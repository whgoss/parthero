from collections import defaultdict

from django.db import transaction

from core.dtos.organizations import MusicianDTO, OrganizationDTO
from core.dtos.music import PartDTO
from core.dtos.programs import (
    ProgramAssignmentAssignedMusicianDTO,
    ProgramAssignmentDTO,
    ProgramAssignmentPartDTO,
    ProgramAssignmentPieceDTO,
    ProgramAssignmentPrincipalPartsDTO,
    ProgramAssignmentPrincipalStatusDTO,
    ProgramAssignmentStatusDTO,
    ProgramAssignmentSummaryDTO,
)
from core.enum.notifications import MagicLinkType
from core.enum.instruments import (
    INSTRUMENT_SECTIONS,
    get_assignment_scope_for_instruments,
    InstrumentSectionEnum,
)
from core.models.notifications import MagicLink
from core.models.music import Part
from core.models.programs import (
    Program,
    ProgramChecklist,
    ProgramMusician,
    ProgramPartMusician,
    ProgramPiece,
)
from core.services.music import get_part_instruments
from core.services.programs import get_program_musician_instruments


def auto_assign_harp_keyboard_principal_parts_if_unambiguous(
    program_id: str, principal_musician_id: str
) -> bool:
    """Auto-assign harp/keyboard principals when no assignment decision is needed.

    Rules (harp/keyboard-only for now):
    - If the principal's assignment scope is not harp/keyboard, do nothing.
    - If there is exactly one eligible musician and exactly one assignable part
      on every in-scope piece, auto-assign all those parts to that musician.
    - If any piece has more than one assignable part, or there is more than one
      eligible musician, do nothing.

    Returns:
        True when auto-assignment was performed and assignment email can be skipped.
    """
    principal_program_musician = (
        ProgramMusician.objects.filter(
            program_id=program_id,
            musician_id=principal_musician_id,
        )
        .prefetch_related("instruments__instrument", "musician")
        .first()
    )
    if not principal_program_musician or not principal_program_musician.principal:
        return False

    principal_scope = get_assignment_scope_for_instruments(
        get_program_musician_instruments(principal_program_musician)
    )
    auto_assignable_instruments = set(INSTRUMENT_SECTIONS[InstrumentSectionEnum.HARP])
    auto_assignable_instruments.update(
        INSTRUMENT_SECTIONS[InstrumentSectionEnum.KEYBOARD]
    )
    if not principal_scope or not principal_scope.issubset(auto_assignable_instruments):
        return False

    payload = get_assignment_payload(
        program_id=program_id,
        principal_musician_id=principal_musician_id,
    )
    if not payload.pieces:
        return False
    if len(payload.eligible_musician_ids) != 1:
        return False
    if any(len(piece.parts) != 1 for piece in payload.pieces):
        return False

    musician_id = payload.eligible_musician_ids[0]
    for piece in payload.pieces:
        part = piece.parts[0]
        set_program_part_assignment(
            program_id=program_id,
            part_id=part.id,
            musician_id=musician_id,
        )
    return True


def get_assignment_payload(
    program_id: str, principal_musician_id: str
) -> ProgramAssignmentDTO:
    """Build the assignment workspace payload for a single principal.

    This is the source of truth for what a principal can assign on a program:
    which pieces/parts they own, which musicians they can assign to those parts,
    and whether all parts in scope are currently assigned.

    Raises:
        ProgramMusician.DoesNotExist: If the musician is not on the program roster.
        PermissionError: If the musician is on the roster but is not a principal.
    """
    program = Program.objects.get(id=program_id)
    organization = OrganizationDTO.from_model(program.organization)
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

    if not principal_program_musician.principal:
        raise PermissionError("Only principals can assign parts.")

    principal_instruments = get_assignment_scope_for_instruments(
        get_program_musician_instruments(principal_program_musician)
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

    # Eligible musicians are only those in the same assignment subsection as this principal.
    program_musicians = (
        ProgramMusician.objects.filter(program_id=program_id)
        .select_related("musician", "musician__organization")
        .prefetch_related(
            "instruments__instrument", "musician__instruments__instrument"
        )
    )
    eligible_musicians = []
    eligible_musician_ids = set()
    for program_musician in program_musicians:
        musician_instruments = get_program_musician_instruments(program_musician)
        if principal_instruments.intersection(musician_instruments):
            eligible_musician_ids.add(str(program_musician.musician_id))
            eligible_musicians.append(MusicianDTO.from_model(program_musician.musician))

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

    # Only include parts owned by this principal's assignment scope.
    filtered_parts = []
    for part in parts:
        if principal_instruments.intersection(get_part_instruments(part)):
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
        organization=organization,
        pieces=pieces,
        eligible_musicians=eligible_musicians,
        eligible_musician_ids=list(eligible_musician_ids),
        all_assigned=all_assigned,
    )


@transaction.atomic
def set_program_part_assignment(
    *,
    program_id: str,
    part_id: str,
    musician_id: str | None,
) -> None:
    """Persist a single part assignment mutation.

    This is the shared write path used by both interactive magic-link assignment
    actions and server-side auto-assignment behavior.
    """
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


@transaction.atomic
def assign_program_part(
    program_id: str,
    principal_musician_id: str,
    part_id: str,
    musician_id: str | None,
) -> ProgramAssignmentDTO:
    """Assign or unassign a single part within a principal's scope.

    Authorization is enforced by reusing `get_assignment_payload()`, so a principal
    can only mutate parts in their subsection and only assign eligible musicians.

    Args:
        musician_id: Target musician ID, or `None` to clear the assignment.

    Returns:
        Fresh `ProgramAssignmentDTO` after the mutation.
    """
    payload = get_assignment_payload(
        program_id=program_id, principal_musician_id=principal_musician_id
    )

    # Guardrail: principals may only assign parts present in their payload.
    if part_id not in {part.id for piece in payload.pieces for part in piece.parts}:
        raise ValueError("This part is not assignable by this principal.")

    # Guardrail: only musicians from the principal's subsection are assignable.
    if musician_id and musician_id not in payload.eligible_musician_ids:
        raise ValueError("Selected musician is not eligible for this section.")

    set_program_part_assignment(
        program_id=program_id,
        part_id=part_id,
        musician_id=musician_id,
    )

    return get_assignment_payload(
        program_id=program_id, principal_musician_id=principal_musician_id
    )


@transaction.atomic
def assign_program_part_by_librarian(
    organization_id: str,
    program_id: str,
    part_id: str,
    musician_id: str | None,
) -> ProgramAssignmentStatusDTO:
    """Assign or unassign a program part from the librarian workflow."""
    part_exists = Part.objects.filter(
        id=part_id,
        piece__programpiece__program_id=program_id,
        piece__programpiece__program__organization_id=organization_id,
    ).exists()
    if not part_exists:
        raise ValueError("Part is not on this program.")

    if musician_id:
        musician_on_program = ProgramMusician.objects.filter(
            program_id=program_id,
            musician_id=musician_id,
            program__organization_id=organization_id,
        ).exists()
        if not musician_on_program:
            raise ValueError("Selected musician is not on this program roster.")

    set_program_part_assignment(
        program_id=program_id,
        part_id=part_id,
        musician_id=musician_id,
    )
    return get_program_assignments_status(
        organization_id=organization_id,
        program_id=program_id,
    )


def get_program_assignments_status(
    organization_id: str, program_id: str
) -> ProgramAssignmentStatusDTO:
    """Build the read-only assignments status payload for the program page.

    This summarizes:
    - piece/part assignment progress across the program, and
    - per-principal assignment/link-access status for principals who have
      assignment work in scope.
    """
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
        part_instruments = get_part_instruments(part)
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

    program_musicians = (
        ProgramMusician.objects.filter(
            program_id=program_id,
            program__organization_id=organization_id,
        )
        .select_related("musician", "musician__organization")
        .prefetch_related(
            "musician__instruments__instrument", "instruments__instrument"
        )
    )
    roster_musicians = [MusicianDTO.from_model(pm.musician) for pm in program_musicians]

    principals = (
        ProgramMusician.objects.filter(
            program_id=program_id,
            program__organization_id=organization_id,
            principal=True,
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
        # String principals and any principals with no applicable section work are excluded.
        if not principal_payload.pieces:
            continue

        # Look up most recent non-revoked assignment links for access/completion state.
        magic_links = MagicLink.objects.filter(
            program_id=program_id,
            musician_id=principal.musician_id,
            type=MagicLinkType.ASSIGNMENT.value,
            revoked=False,
        )
        latest_magic_link = magic_links.order_by("-created").first()
        completed_magic_link = (
            magic_links.filter(completed_on__isnull=False)
            .order_by("-completed_on")
            .first()
        )
        accessed_magic_link = (
            magic_links.filter(last_accessed_on__isnull=False)
            .order_by("-last_accessed_on")
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
        link_completed = completed_magic_link is not None
        link_accessed = (
            principal_all_assigned or accessed_magic_link is not None or link_completed
        )
        if not assignments_sent_on:
            status = "Not Sent"
        elif principal_all_assigned or link_completed:
            status = "Completed"
        elif link_accessed:
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
                last_accessed_on=(
                    accessed_magic_link.last_accessed_on
                    if accessed_magic_link
                    else latest_magic_link.last_accessed_on
                    if latest_magic_link
                    else None
                ),
                completed_on=(
                    completed_magic_link.completed_on
                    if completed_magic_link
                    else latest_magic_link.completed_on
                    if latest_magic_link
                    else None
                ),
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
        roster_musicians=roster_musicians,
        summary=ProgramAssignmentSummaryDTO(
            total_parts=total_parts,
            assigned_parts=assigned_parts,
            all_assigned=total_parts > 0 and assigned_parts == total_parts,
        ),
    )
