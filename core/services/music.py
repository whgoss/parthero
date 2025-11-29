import uuid
from io import BytesIO
from typing import List
from datetime import timedelta
from core.dtos.music import PieceDTO, PartDTO, SectionDTO
from core.models import Piece, Part, Section
from core.services.s3 import create_bucket_for_organization, upload_file
from core.utils import get_file_extension
from django.db import transaction


def create_piece(
    title: str,
    composer: str,
    organization_id: str,
    arranger: str = None,
    duration: timedelta = None,
) -> PieceDTO:
    piece = Piece(
        title=title,
        composer=composer,
        organization_id=organization_id,
        arranger=arranger,
        duration=duration,
    )
    piece.save()
    return PieceDTO.from_model(piece)


@transaction.atomic
def create_part(
    piece_id: str, section_id: str, file_buffer: BytesIO, filename: str
) -> PieceDTO:
    piece = Piece.objects.get(id=piece_id)
    section = Section.objects.get(id=section_id)

    # Create the part
    part_id = uuid.uuid4()
    file_key = str(piece.id) + "/" + str(part_id) + get_file_extension(filename)
    part = Part(
        id=part_id,
        piece_id=piece_id,
        section_id=section_id,
        file_key=file_key,
    )
    part.save()

    # Upload the file to the organization storage bucket
    organization_id = str(piece.organization.id)
    create_bucket_for_organization(organization_id)
    upload_file(file_buffer, organization_id, file_key)

    return PartDTO.from_model(part)


def create_section(
    instrument: str,
    family: str,
    number: int,
    organization_id: str,
) -> SectionDTO:
    section = Section(
        instrument=instrument,
        family=family,
        number=number,
        organization_id=organization_id,
    )
    section.save()
    return SectionDTO.from_model(section)


def get_pieces_for_organization(organization_id: str) -> List[PieceDTO]:
    pieces = Piece.objects.filter(organization__id__in=[organization_id])
    return [PieceDTO.from_model(piece) for piece in pieces]


def get_pieces_count_for_organization(organization_id: str) -> int:
    return Piece.objects.filter(organization__id__in=[organization_id]).count()
