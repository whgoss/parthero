import pytz
from datetime import datetime
from typing import Optional, List
from django.db import transaction
from django.db.models import Min, F, Count
from django.utils import timezone
from core.dtos.music import PieceDTO
from core.dtos.programs import ProgramDTO
from core.enum.status import ProgramStatus
from core.models.music import Piece
from core.models.organizations import Organization
from core.models.programs import Program, ProgramPerformance, ProgramPiece


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
