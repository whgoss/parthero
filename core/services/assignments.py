from collections import defaultdict

from django.db import transaction

from core.dtos.music import PartDTO
from core.dtos.programs import (
    ProgramAssignmentAssignedMusicianDTO,
    ProgramAssignmentDTO,
    ProgramAssignmentEligibleMusicianDTO,
    ProgramAssignmentPartDTO,
    ProgramAssignmentPieceDTO,
    ProgramAssignmentPrincipalPartsDTO,
    ProgramAssignmentPrincipalStatusDTO,
    ProgramAssignmentStatusDTO,
    ProgramAssignmentSummaryDTO,
)
from core.enum.notifications import MagicLinkType
from core.enum.instruments import (
    INSTRUMENT_PRIMARIES,
    INSTRUMENT_SECTIONS,
    InstrumentEnum,
    InstrumentSectionEnum,
)
from core.models.notifications import MagicLink
from core.models.music import Part
from core.models.programs import (
    ProgramChecklist,
    ProgramMusician,
    ProgramPartMusician,
    ProgramPiece,
)


def _canonical_instrument(instrument_name: str) -> InstrumentEnum:
    instrument = InstrumentEnum(instrument_name)
    return INSTRUMENT_PRIMARIES.get(instrument, instrument)


def _program_musician_instruments(
    program_musician: ProgramMusician,
) -> set[InstrumentEnum]:
    instruments = set()
    for musician_instrument in program_musician.instruments.all():
        instruments.add(_canonical_instrument(musician_instrument.instrument.name))
    return instruments


def _expand_principal_instruments(
    principal_instruments: set[InstrumentEnum],
) -> set[InstrumentEnum]:
    expanded = set(principal_instruments)
    percussion_section = set(INSTRUMENT_SECTIONS[InstrumentSectionEnum.PERCUSSION])
    if principal_instruments.intersection(percussion_section):
        expanded.update(percussion_section)
    return expanded


def _part_instruments(part: Part) -> set[InstrumentEnum]:
    instruments = set()
    for part_instrument in part.instruments.all():
        instruments.add(_canonical_instrument(part_instrument.instrument.name))
    return instruments


def get_assignment_payload(
    program_id: str, principal_musician_id: str
) -> ProgramAssignmentDTO:
    principal_program_musician = (
        ProgramMusician.objects.filter(
            program_id=program_id,
            musician_id=principal_musician_id,
        )
        .prefetch_related("instruments__instrument", "musician")
        .first()
    )
    if not principal_program_musician:
        raise ProgramMusician.DoesNotExist
    if not principal_program_musician.musician.principal:
        raise PermissionError("Only principals can assign parts.")

    principal_instruments = _expand_principal_instruments(
        _program_musician_instruments(principal_program_musician)
    )
    string_instruments = set(INSTRUMENT_SECTIONS[InstrumentSectionEnum.STRINGS])
    # String principals do not assign parts in this workflow.
    if principal_instruments and principal_instruments.issubset(string_instruments):
        return ProgramAssignmentDTO(
            pieces=[],
            eligible_musicians=[],
            eligible_musician_ids=[],
            all_assigned=True,
        )

    program_musicians = ProgramMusician.objects.filter(
        program_id=program_id
    ).prefetch_related("instruments__instrument", "musician")
    eligible_musicians = []
    eligible_musician_ids = set()
    for program_musician in program_musicians:
        musician_instruments = _program_musician_instruments(program_musician)
        if principal_instruments.intersection(musician_instruments):
            eligible_musician_ids.add(str(program_musician.musician_id))
            eligible_musicians.append(
                ProgramAssignmentEligibleMusicianDTO(
                    id=str(program_musician.musician_id),
                    first_name=program_musician.musician.first_name,
                    last_name=program_musician.musician.last_name,
                    email=program_musician.musician.email,
                    instruments=[
                        instrument.instrument.name
                        for instrument in program_musician.instruments.all()
                    ],
                )
            )

    program_piece_ids = list(
        ProgramPiece.objects.filter(program_id=program_id).values_list(
            "piece_id", flat=True
        )
    )
    parts = (
        Part.objects.filter(piece_id__in=program_piece_ids)
        .select_related("piece")
        .prefetch_related("instruments__instrument")
    )

    filtered_parts = []
    for part in parts:
        if principal_instruments.intersection(_part_instruments(part)):
            filtered_parts.append(part)

    part_assignments = {
        str(assignment.part_id): str(assignment.musician_id)
        for assignment in ProgramPartMusician.objects.filter(
            program_id=program_id, part_id__in=[part.id for part in filtered_parts]
        )
    }

    pieces_map: defaultdict[str, list[ProgramAssignmentPartDTO]] = defaultdict(list)
    for part in filtered_parts:
        part_dto = PartDTO.from_model(part)
        pieces_map[str(part.piece_id)].append(
            ProgramAssignmentPartDTO(
                id=str(part.id),
                display_name=part_dto.display_name,
                assigned_musician_id=part_assignments.get(str(part.id)),
            )
        )

    pieces: list[ProgramAssignmentPieceDTO] = []
    for piece_id in program_piece_ids:
        piece_parts = pieces_map.get(str(piece_id), [])
        if not piece_parts:
            continue
        piece = piece_parts and next(
            (p for p in filtered_parts if str(p.piece_id) == str(piece_id)), None
        )
        if not piece:
            continue
        pieces.append(
            ProgramAssignmentPieceDTO(
                id=str(piece.piece_id),
                title=piece.piece.title,
                composer=piece.piece.composer,
                parts=piece_parts,
            )
        )

    all_assigned = True
    for piece in pieces:
        for part in piece.parts:
            if not part.assigned_musician_id:
                all_assigned = False
                break

    return ProgramAssignmentDTO(
        pieces=pieces,
        eligible_musicians=eligible_musicians,
        eligible_musician_ids=list(eligible_musician_ids),
        all_assigned=all_assigned,
    )


@transaction.atomic
def assign_program_part(
    program_id: str,
    principal_musician_id: str,
    part_id: str,
    musician_id: str | None,
) -> ProgramAssignmentDTO:
    payload = get_assignment_payload(
        program_id=program_id, principal_musician_id=principal_musician_id
    )
    if part_id not in {part.id for piece in payload.pieces for part in piece.parts}:
        raise ValueError("This part is not assignable by this principal.")

    if musician_id and musician_id not in payload.eligible_musician_ids:
        raise ValueError("Selected musician is not eligible for this section.")

    if not musician_id:
        ProgramPartMusician.objects.filter(
            program_id=program_id, part_id=part_id
        ).delete()
    else:
        ProgramPartMusician.objects.update_or_create(
            program_id=program_id,
            part_id=part_id,
            defaults={"musician_id": musician_id},
        )

    return get_assignment_payload(
        program_id=program_id, principal_musician_id=principal_musician_id
    )


def get_program_assignments_status(
    organization_id: str, program_id: str
) -> ProgramAssignmentStatusDTO:
    program_piece_ids = list(
        ProgramPiece.objects.filter(
            program_id=program_id,
            program__organization_id=organization_id,
        ).values_list("piece_id", flat=True)
    )

    all_parts = (
        Part.objects.filter(piece_id__in=program_piece_ids)
        .select_related("piece")
        .prefetch_related("instruments__instrument")
    )
    string_instruments = set(INSTRUMENT_SECTIONS[InstrumentSectionEnum.STRINGS])
    parts = []
    for part in all_parts:
        part_instruments = _part_instruments(part)
        # String-only parts are not part of assignment workflow.
        if part_instruments and part_instruments.issubset(string_instruments):
            continue
        parts.append(part)
    assignments = ProgramPartMusician.objects.filter(
        program_id=program_id,
        part_id__in=[part.id for part in parts],
    ).select_related("musician")
    assignments_by_part = {
        str(assignment.part_id): assignment for assignment in assignments
    }

    pieces_map: defaultdict[str, list[ProgramAssignmentPartDTO]] = defaultdict(list)
    for part in parts:
        assignment = assignments_by_part.get(str(part.id))
        assigned_musician = assignment.musician if assignment else None
        part_dto = PartDTO.from_model(part)
        pieces_map[str(part.piece_id)].append(
            ProgramAssignmentPartDTO(
                id=str(part.id),
                display_name=part_dto.display_name,
                status="Assigned" if assignment else "Unassigned",
                assigned_musician=ProgramAssignmentAssignedMusicianDTO(
                    id=str(assigned_musician.id),
                    first_name=assigned_musician.first_name,
                    last_name=assigned_musician.last_name,
                    profile_url=f"/musicians/{assigned_musician.id}/",
                )
                if assigned_musician
                else None,
            )
        )

    pieces: list[ProgramAssignmentPieceDTO] = []
    for piece_id in program_piece_ids:
        piece_parts = pieces_map.get(str(piece_id), [])
        if not piece_parts:
            continue
        piece = next(
            (part for part in parts if str(part.piece_id) == str(piece_id)), None
        )
        if not piece:
            continue
        pieces.append(
            ProgramAssignmentPieceDTO(
                id=str(piece.piece_id),
                title=piece.piece.title,
                composer=piece.piece.composer,
                all_assigned=all(part.assigned_musician for part in piece_parts),
                parts=piece_parts,
            )
        )

    checklist = ProgramChecklist.objects.get(
        program_id=program_id,
        program__organization_id=organization_id,
    )
    assignments_sent_on = checklist.assignments_sent_on

    principals = (
        ProgramMusician.objects.filter(
            program_id=program_id,
            program__organization_id=organization_id,
            musician__principal=True,
        )
        .select_related("musician")
        .prefetch_related("instruments__instrument")
    )

    principal_statuses = []
    for principal in principals:
        principal_payload = get_assignment_payload(
            program_id=program_id,
            principal_musician_id=str(principal.musician_id),
        )
        # String principals and any principals with no applicable subsection work are excluded.
        if not principal_payload.pieces:
            continue

        magic_link = (
            MagicLink.objects.filter(
                program_id=program_id,
                musician_id=principal.musician_id,
                type=MagicLinkType.ASSIGNMENT.value,
            )
            .order_by("-expires_on")
            .first()
        )

        principal_total_parts = sum(
            len(piece.parts) for piece in principal_payload.pieces
        )
        principal_assigned_parts = sum(
            1
            for piece in principal_payload.pieces
            for part in piece.parts
            if part.assigned_musician_id
        )

        principal_all_assigned = (
            principal_total_parts > 0
            and principal_assigned_parts == principal_total_parts
        )
        link_accessed = (
            principal_all_assigned
            or (magic_link is not None and magic_link.last_accessed_on is not None)
            or (magic_link is not None and magic_link.completed_on is not None)
        )
        if not assignments_sent_on:
            status = "Not Sent"
        elif principal_all_assigned or (magic_link and magic_link.completed_on):
            status = "Completed"
        elif magic_link and magic_link.last_accessed_on:
            status = "Accessed"
        else:
            status = "Sent"

        principal_statuses.append(
            ProgramAssignmentPrincipalStatusDTO(
                id=str(principal.musician_id),
                first_name=principal.musician.first_name,
                last_name=principal.musician.last_name,
                profile_url=f"/musicians/{principal.musician_id}/",
                status=status,
                link_accessed=link_accessed,
                assigned_parts=ProgramAssignmentPrincipalPartsDTO(
                    assigned=principal_assigned_parts,
                    total=principal_total_parts,
                ),
                last_accessed_on=magic_link.last_accessed_on if magic_link else None,
                completed_on=magic_link.completed_on if magic_link else None,
            )
        )

    total_parts = sum(len(piece.parts) for piece in pieces)
    assigned_parts = sum(
        1
        for piece in pieces
        for part in piece.parts
        if part.assigned_musician is not None
    )

    return ProgramAssignmentStatusDTO(
        pieces=pieces,
        principals=principal_statuses,
        summary=ProgramAssignmentSummaryDTO(
            total_parts=total_parts,
            assigned_parts=assigned_parts,
            all_assigned=total_parts > 0 and assigned_parts == total_parts,
        ),
    )
