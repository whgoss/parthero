import pytz
from datetime import datetime
from typing import Optional, List
from django.db import transaction
from django.db.models import Min, F, Count
from django.utils import timezone
from core.dtos.music import PieceDTO
from core.dtos.programs import ProgramDTO, ProgramMusicianDTO
from core.enum.status import ProgramStatus
from core.models.music import Piece, MusicianInstrument, Instrument
from core.models.organizations import Organization, Musician, SetupChecklist
from core.models.programs import (
    Program,
    ProgramPerformance,
    ProgramPiece,
    ProgramMusician,
    ProgramMusicianInstrument,
)
from core.enum.instruments import InstrumentEnum


@transaction.atomic
def create_program(
    organization_id: str,
    name: str,
    status: Optional[ProgramStatus] = ProgramStatus.CREATED,
    performance_dates: Optional[List[datetime]] = None,
) -> ProgramDTO:
    organization = Organization.objects.get(id=organization_id)
    program = Program(
        organization_id=organization.id,
        name=name,
        status=status.value,
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

    setup_checklist = SetupChecklist.objects.get(organization_id=organization_id)
    if not setup_checklist.completed:
        setup_checklist.program_created = True
        setup_checklist.save()

    return ProgramDTO.from_model(program)


def get_program(piece_id: str) -> ProgramDTO:
    program = Program.objects.get(id=piece_id)
    return ProgramDTO.from_model(program)


def get_programs(organization_id: str) -> List[ProgramDTO]:
    programs = (
        Program.objects.filter(organization_id=organization_id)
        .annotate(first_performance=Min("performances__date"))
        .order_by(F("first_performance").asc(nulls_last=True))
    )
    return ProgramDTO.from_models(programs)


def get_pieces_for_program(program_id: str) -> List[PieceDTO]:
    program_pieces = ProgramPiece.objects.filter(program_id=program_id)
    piece_ids = []
    for program_piece in program_pieces:
        piece_ids.append(program_piece.piece_id)
    piece_models = Piece.objects.filter(id__in=piece_ids).annotate(
        parts_count=Count("parts", distinct=True),
    )
    return PieceDTO.from_models(piece_models)


def add_piece_to_program(
    program_id: str,
    piece_id: str,
) -> List[PieceDTO]:
    program = Program.objects.get(id=program_id)
    piece = Piece.objects.get(id=piece_id, organization=program.organization)
    program_piece = ProgramPiece.objects.filter(program=program, piece=piece).first()
    if not program_piece:
        program_piece = ProgramPiece(program=program, piece=piece)
        program_piece.save()
    return get_pieces_for_program(program.id)


def remove_piece_from_program(
    program_id: str,
    piece_id: str,
) -> List[PieceDTO]:
    program = Program.objects.get(id=program_id)
    piece = Piece.objects.get(id=piece_id, organization=program.organization)
    program_piece = ProgramPiece.objects.filter(program=program, piece=piece).first()
    if program_piece:
        program_piece.delete()
    return get_pieces_for_program(program.id)


def get_musicians_for_program(program_id: str) -> List[ProgramMusicianDTO]:
    program_musicians = ProgramMusician.objects.filter(
        program_id=program_id
    ).select_related("program", "musician", "musician__organization")
    return ProgramMusicianDTO.from_models(program_musicians)


def add_musician_to_program(
    program_id: str,
    musician_id: str,
) -> List[ProgramMusicianDTO]:
    program = Program.objects.get(id=program_id)
    musician = Musician.objects.get(id=musician_id)
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
    return get_musicians_for_program(program.id)


def remove_musician_from_program(
    program_id: str,
    program_musician_id: str,
) -> List[ProgramMusicianDTO]:
    program = Program.objects.get(id=program_id)
    program_musician = ProgramMusician.objects.filter(
        id=program_musician_id, program=program
    ).first()
    if program_musician:
        ProgramMusicianInstrument.objects.filter(
            program_musician=program_musician
        ).delete()
        program_musician.delete()
    return get_musicians_for_program(program.id)


def add_program_musician_instrument(
    program_id: str,
    program_musician_id: str,
    instrument: InstrumentEnum,
) -> List[ProgramMusicianDTO]:
    program = Program.objects.get(id=program_id)
    program_musician = ProgramMusician.objects.filter(
        id=program_musician_id, program=program
    ).first()
    if not program_musician:
        return get_musicians_for_program(program.id)
    instrument_model = Instrument.objects.filter(name=instrument.value).first()
    if instrument_model:
        ProgramMusicianInstrument.objects.get_or_create(
            program_musician=program_musician,
            instrument=instrument_model,
        )
    return get_musicians_for_program(program.id)


def remove_program_musician_instrument(
    program_id: str,
    program_musician_id: str,
    instrument: InstrumentEnum,
) -> List[ProgramMusicianDTO]:
    program = Program.objects.get(id=program_id)
    program_musician = ProgramMusician.objects.filter(
        id=program_musician_id, program=program
    ).first()
    if not program_musician:
        return get_musicians_for_program(program.id)
    instrument_model = Instrument.objects.filter(name=instrument.value).first()
    if instrument_model:
        ProgramMusicianInstrument.objects.filter(
            program_musician=program_musician,
            instrument=instrument_model,
        ).delete()
    return get_musicians_for_program(program.id)
