import pytz
import pgbulk
from datetime import datetime
from typing import Optional, List
from django.db import transaction
from django.db.models import Min, F, Count, Q
from django.utils import timezone
from core.dtos.music import PieceDTO
from core.dtos.programs import ProgramDTO, ProgramMusicianDTO, ProgramChecklistDTO
from core.enum.music import PartAssetType
from core.enum.status import UploadStatus
from core.models.music import Piece, MusicianInstrument, Instrument
from core.models.organizations import Organization, Musician, SetupChecklist
from core.models.users import User
from core.models.programs import (
    Program,
    ProgramPerformance,
    ProgramPiece,
    ProgramMusician,
    ProgramMusicianInstrument,
    ProgramChecklist,
)
from core.enum.instruments import InstrumentEnum


@transaction.atomic
def create_program(
    organization_id: str,
    name: str,
    performance_dates: Optional[List[datetime]] = None,
) -> ProgramDTO:
    organization = Organization.objects.get(id=organization_id)
    program = Program(
        organization_id=organization.id,
        name=name,
    )
    program.save()

    for performance_date in performance_dates or []:
        # Convert from the organization's time zone to UTC
        # TODO: Consider different timezones per performance?
        target_timezone = pytz.timezone(organization.timezone)
        if timezone.is_naive(performance_date):
            performance_date = target_timezone.localize(performance_date)
        performance_date = performance_date.astimezone(pytz.UTC)
        program_performance = ProgramPerformance(
            program_id=program.id, date=performance_date
        )
        program_performance.save()

    # Create a program checklist
    program_checklist = ProgramChecklist(program=program)
    program_checklist.save()

    # Modify the setup checklist if necessary
    setup_checklist = SetupChecklist.objects.get(organization_id=organization_id)
    if not setup_checklist.completed:
        setup_checklist.program_created = True
        setup_checklist.save()

    return ProgramDTO.from_model(program)


def get_program(organization_id: str, program_id: str) -> ProgramDTO:
    program = Program.objects.get(id=program_id, organization_id=organization_id)
    return ProgramDTO.from_model(program)


def get_program_checklist(organization_id: str, program_id: str) -> ProgramChecklistDTO:
    program_checklist = ProgramChecklist.objects.get(
        program_id=program_id, program__organization_id=organization_id
    )
    return ProgramChecklistDTO.from_model(program_checklist)


def get_programs(organization_id: str) -> List[ProgramDTO]:
    programs = (
        Program.objects.filter(organization_id=organization_id)
        .annotate(first_performance=Min("performances__date"))
        .order_by(F("first_performance").asc(nulls_last=True))
    )
    return ProgramDTO.from_models(programs)


def get_pieces_for_program(organization_id: str, program_id: str) -> List[PieceDTO]:
    program_pieces = ProgramPiece.objects.filter(
        program_id=program_id, program__organization_id=organization_id
    )
    piece_ids = []
    for program_piece in program_pieces:
        piece_ids.append(program_piece.piece_id)
    piece_models = Piece.objects.filter(id__in=piece_ids).annotate(
        parts_count=Count("parts", distinct=True),
        completed_parts=Count(
            "parts",
            filter=Q(
                parts__assets__status=UploadStatus.UPLOADED.value,
                parts__assets__asset_type=PartAssetType.CLEAN.value,
            ),
            distinct=True,
        ),
    )
    return PieceDTO.from_models(piece_models)


def add_piece_to_program(
    organization_id: str,
    program_id: str,
    piece_id: str,
) -> List[PieceDTO]:
    program = Program.objects.get(id=program_id, organization_id=organization_id)
    piece = Piece.objects.get(id=piece_id, organization=program.organization)
    program_piece = ProgramPiece.objects.filter(program=program, piece=piece).first()
    if not program_piece:
        program_piece = ProgramPiece(program=program, piece=piece)
        program_piece.save()
    return get_pieces_for_program(
        organization_id=organization_id, program_id=program.id
    )


def remove_piece_from_program(
    organization_id: str,
    program_id: str,
    piece_id: str,
) -> List[PieceDTO]:
    program = Program.objects.get(id=program_id, organization_id=organization_id)
    piece = Piece.objects.get(id=piece_id, organization=program.organization)
    program_piece = ProgramPiece.objects.filter(program=program, piece=piece).first()
    if program_piece:
        program_piece.delete()
    return get_pieces_for_program(
        organization_id=organization_id, program_id=program.id
    )


def get_musicians_for_program(
    organization_id: str, program_id: str
) -> List[ProgramMusicianDTO]:
    program_musicians = ProgramMusician.objects.filter(
        program_id=program_id, program__organization_id=organization_id
    ).select_related("program", "musician", "musician__organization")
    return ProgramMusicianDTO.from_models(program_musicians)


def get_musician_for_program(
    organization_id: str, program_id: str, musician_id: str
) -> ProgramMusicianDTO:
    program_musician = ProgramMusician.objects.get(
        program_id=program_id,
        musician_id=musician_id,
        program__organization_id=organization_id,
    )
    return ProgramMusicianDTO.from_model(program_musician)


def get_program_musician_instruments(
    program_musician: ProgramMusician,
) -> set[InstrumentEnum]:
    instruments = set()
    for musician_instrument in program_musician.instruments.all():
        instruments.add(InstrumentEnum(musician_instrument.instrument.name))
    return instruments


def add_musician_to_program(
    organization_id: str,
    program_id: str,
    musician_id: str,
) -> List[ProgramMusicianDTO]:
    program = Program.objects.get(id=program_id, organization_id=organization_id)
    musician = Musician.objects.get(id=musician_id, organization_id=organization_id)
    program_musician = ProgramMusician.objects.filter(
        program=program, musician=musician
    ).first()
    if not program_musician:
        program_musician = ProgramMusician(program=program, musician=musician)
        program_musician.save()

    musician_instrument = (
        MusicianInstrument.objects.filter(musician=musician)
        .select_related("instrument")
        .first()
    )
    if musician_instrument and musician_instrument.instrument:
        ProgramMusicianInstrument.objects.get_or_create(
            program_musician=program_musician,
            instrument=musician_instrument.instrument,
        )
    return get_musicians_for_program(
        organization_id=organization_id, program_id=program.id
    )


def remove_musician_from_program(
    organization_id: str,
    program_id: str,
    program_musician_id: str,
) -> List[ProgramMusicianDTO]:
    program = Program.objects.get(id=program_id, organization_id=organization_id)
    program_musician = ProgramMusician.objects.filter(
        id=program_musician_id, program=program
    ).first()
    if program_musician:
        ProgramMusicianInstrument.objects.filter(
            program_musician=program_musician
        ).delete()
        program_musician.delete()
    return get_musicians_for_program(
        organization_id=organization_id, program_id=program.id
    )


def add_program_musician_instrument(
    organization_id: str,
    program_id: str,
    program_musician_id: str,
    instrument: InstrumentEnum,
) -> List[ProgramMusicianDTO]:
    program = Program.objects.get(id=program_id, organization_id=organization_id)
    program_musician = ProgramMusician.objects.filter(
        id=program_musician_id, program=program
    ).first()
    if not program_musician:
        return get_musicians_for_program(
            organization_id=organization_id, program_id=program.id
        )
    instrument_model = Instrument.objects.filter(name=instrument.value).first()
    if instrument_model:
        ProgramMusicianInstrument.objects.get_or_create(
            program_musician=program_musician,
            instrument=instrument_model,
        )
    return get_musicians_for_program(
        organization_id=organization_id, program_id=program.id
    )


def remove_program_musician_instrument(
    organization_id: str,
    program_id: str,
    program_musician_id: str,
    instrument: InstrumentEnum,
) -> List[ProgramMusicianDTO]:
    program = Program.objects.get(id=program_id, organization_id=organization_id)
    program_musician = ProgramMusician.objects.filter(
        id=program_musician_id, program=program
    ).first()
    if not program_musician:
        return get_musicians_for_program(
            organization_id=organization_id, program_id=program.id
        )
    instrument_model = Instrument.objects.filter(name=instrument.value).first()
    if instrument_model:
        ProgramMusicianInstrument.objects.filter(
            program_musician=program_musician,
            instrument=instrument_model,
        ).delete()
    return get_musicians_for_program(
        organization_id=organization_id, program_id=program.id
    )


@transaction.atomic
def update_program_checklist(
    organization_id: str,
    program_id: str,
    user_id: str,
    pieces_completed: Optional[bool] = None,
    roster_completed: Optional[bool] = None,
    overrides_completed: Optional[bool] = None,
    bowings_completed: Optional[bool] = None,
    assignments_sent: Optional[bool] = None,
    assignments_completed: Optional[bool] = None,
    delivery_sent: Optional[bool] = None,
    delivery_completed: Optional[bool] = None,
) -> ProgramChecklistDTO:
    program_checklist = ProgramChecklist.objects.get(
        program_id=program_id, program__organization_id=organization_id
    )

    user = User.objects.get(id=user_id)

    current_pieces_completed = program_checklist.pieces_completed_on is not None
    current_roster_completed = program_checklist.roster_completed_on is not None
    current_bowings_completed = program_checklist.bowings_completed_on is not None
    current_overrides_completed = program_checklist.overrides_completed_on is not None
    current_assignments_sent = program_checklist.assignments_sent_on is not None
    current_assignments_completed = (
        program_checklist.assignments_completed_on is not None
    )

    pieces_will_be_completed = (
        pieces_completed if pieces_completed is not None else current_pieces_completed
    )
    roster_will_be_completed = (
        roster_completed if roster_completed is not None else current_roster_completed
    )
    bowings_will_be_completed = (
        bowings_completed
        if bowings_completed is not None
        else current_bowings_completed
    )
    overrides_will_be_completed = (
        overrides_completed
        if overrides_completed is not None
        else current_overrides_completed
    )
    assignments_will_be_sent = (
        assignments_sent if assignments_sent is not None else current_assignments_sent
    )
    assignments_will_be_completed = (
        assignments_completed
        if assignments_completed is not None
        else current_assignments_completed
    )

    if bowings_completed:
        if not pieces_will_be_completed:
            raise ValueError("Bowings cannot be completed before pieces are complete.")

    if overrides_completed:
        if not pieces_will_be_completed:
            raise ValueError(
                "Overrides cannot be completed before pieces are complete."
            )

    if assignments_completed:
        if not all(
            [
                pieces_will_be_completed,
                roster_will_be_completed,
                bowings_will_be_completed,
                overrides_will_be_completed,
                assignments_will_be_sent,
            ]
        ):
            raise ValueError(
                "Assignments cannot be completed until pieces, roster, bowings, "
                "overrides, and sending to principals are complete."
            )

    if assignments_sent:
        if not all(
            [
                pieces_will_be_completed,
                roster_will_be_completed,
                bowings_will_be_completed,
                overrides_will_be_completed,
            ]
        ):
            raise ValueError(
                "Assignments cannot be sent until pieces, roster, bowings, and overrides are complete."
            )

    if delivery_sent:
        if not assignments_will_be_completed:
            raise ValueError("Delivery cannot be sent until assignments are complete.")
    if delivery_sent is False:
        raise ValueError("Delivery cannot be undone once sent.")

    if pieces_completed is not None:
        if pieces_completed:
            program_checklist.pieces_completed_on = timezone.now()
            program_checklist.pieces_completed_by = user
        else:
            program_checklist.pieces_completed_on = None
            program_checklist.pieces_completed_by = None
            program_checklist.bowings_completed_on = None
            program_checklist.bowings_completed_by = None
            program_checklist.overrides_completed_on = None
            program_checklist.overrides_completed_by = None
            program_checklist.assignments_sent_on = None
            program_checklist.assignments_sent_by = None
            program_checklist.assignments_completed_on = None
            program_checklist.assignments_completed_by = None
    if roster_completed is not None:
        if roster_completed:
            program_checklist.roster_completed_on = timezone.now()
            program_checklist.roster_completed_by = user
        else:
            program_checklist.roster_completed_on = None
            program_checklist.roster_completed_by = None
            program_checklist.assignments_sent_on = None
            program_checklist.assignments_sent_by = None
            program_checklist.assignments_completed_on = None
            program_checklist.assignments_completed_by = None
    if overrides_completed is not None:
        if overrides_completed:
            program_checklist.overrides_completed_on = timezone.now()
            program_checklist.overrides_completed_by = user
        else:
            program_checklist.overrides_completed_on = None
            program_checklist.overrides_completed_by = None
            program_checklist.assignments_sent_on = None
            program_checklist.assignments_sent_by = None
            program_checklist.assignments_completed_on = None
            program_checklist.assignments_completed_by = None
    if bowings_completed is not None:
        if bowings_completed:
            program_checklist.bowings_completed_on = timezone.now()
            program_checklist.bowings_completed_by = user
        else:
            program_checklist.bowings_completed_on = None
            program_checklist.bowings_completed_by = None
            program_checklist.assignments_sent_on = None
            program_checklist.assignments_sent_by = None
            program_checklist.assignments_completed_on = None
            program_checklist.assignments_completed_by = None
    if assignments_sent is not None:
        if assignments_sent:
            if program_checklist.assignments_sent_on is None:
                program_checklist.assignments_sent_on = timezone.now()
                program_checklist.assignments_sent_by = user

                # Nested import prevents circular dependency
                from core.services.notifications import send_part_assignment_emails

                send_part_assignment_emails(
                    organization_id=organization_id,
                    program_id=program_id,
                )
        else:
            program_checklist.assignments_sent_on = None
            program_checklist.assignments_sent_by = None
            program_checklist.assignments_completed_on = None
            program_checklist.assignments_completed_by = None
    if assignments_completed is not None:
        if assignments_completed:
            program_checklist.assignments_completed_on = timezone.now()
            program_checklist.assignments_completed_by = user
        else:
            program_checklist.assignments_completed_on = None
            program_checklist.assignments_completed_by = None
    if delivery_sent is not None and delivery_sent:
        if program_checklist.delivery_sent_on is None:
            program_checklist.delivery_sent_on = timezone.now()
            program_checklist.delivery_sent_by = user
            # Nested import prevents circular dependency
            from core.services.notifications import send_part_delivery_emails

            send_part_delivery_emails(
                organization_id=organization_id,
                program_id=program_id,
            )
    program_checklist.save()
    return ProgramChecklistDTO.from_model(program_checklist)


@transaction.atomic
def add_musicians_to_program(
    organization_id: str,
    program_id: str,
    principals: bool = False,
    core_members: bool = True,
) -> List[ProgramMusicianDTO]:
    program = Program.objects.get(id=program_id, organization_id=organization_id)
    musicians = Musician.objects.filter(principal=principals, core_member=core_members)
    program_musicians = []

    # Add musicians to the program
    for musician in musicians:
        program_musician = ProgramMusician(program=program, musician=musician)
        program_musicians.append(program_musician)
    pgbulk.upsert(
        ProgramMusician, program_musicians, unique_fields=["program_id", "musician_id"]
    )
    saved_program_musicians = ProgramMusician.objects.filter(program_id=program_id)

    # Designate each musicians' primary instrument on the program
    program_musician_instruments = []
    for program_musician in saved_program_musicians:
        musician_instrument = (
            MusicianInstrument.objects.filter(musician=program_musician.musician)
            .select_related("instrument")
            .first()
        )

        if musician_instrument and musician_instrument.instrument:
            program_musician_instrument = ProgramMusicianInstrument(
                program_musician=program_musician,
                instrument=musician_instrument.instrument,
            )
            program_musician_instruments.append(program_musician_instrument)
    pgbulk.upsert(
        ProgramMusicianInstrument,
        program_musician_instruments,
        unique_fields=["program_musician_id", "instrument_id"],
    )

    return ProgramMusicianDTO.from_models(saved_program_musicians)
