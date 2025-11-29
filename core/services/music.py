import uuid
from typing import List
from datetime import timedelta
from core.dtos.music import PieceDTO, PartDTO, SectionDTO
from core.enum.status import UploadStatus
from core.models import Piece, Part, Section
from core.services.s3 import create_upload_url, create_bucket_for_organization
from core.utils import get_file_extension


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


def create_part(piece_id: str, filename: str) -> PartDTO:
    piece = Piece.objects.get(id=piece_id)

    # Create the part
    part_id = uuid.uuid4()

    part = Part(
        id=part_id,
        piece_id=piece_id,
        upload_filename=filename,
    )
    part.save()

    # Ensure the org bucket exists
    create_bucket_for_organization(str(piece.organization.id))

    # Generate a pre-signed URL for upload
    file_key = str(piece.id) + "/" + str(part_id) + get_file_extension(filename)
    presigned_url = create_upload_url(
        organization_id=str(piece.organization.id),
        file_key=file_key,
        expiration=3600,
    )
    part.file_key = file_key
    part.upload_url = presigned_url
    part.upload_filename = filename
    part.status = UploadStatus.PENDING.value
    part.save()

    # Upload the file to the organization storage bucket
    # organization_id = str(piece.organization.id)
    # create_bucket_for_organization(organization_id)
    # upload_file(file_buffer, organization_id, file_key)

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


def get_piece_by_id(piece_id: str, organization_id: str) -> PieceDTO:
    piece = Piece.objects.get(id=piece_id, organization__id=organization_id)
    return PieceDTO.from_model(piece)


def get_pieces_for_organization(organization_id: str) -> List[PieceDTO]:
    pieces = Piece.objects.filter(organization__id__in=[organization_id])
    return [PieceDTO.from_model(piece) for piece in pieces]


def get_pieces_count_for_organization(organization_id: str) -> int:
    return Piece.objects.filter(organization__id__in=[organization_id]).count()
