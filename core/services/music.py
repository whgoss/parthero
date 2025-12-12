import uuid
from typing import List
from django.db import transaction
from django.db.models import Count
from datetime import timedelta
from core.dtos.music import PieceDTO, PartDTO, InstrumentSectionDTO
from core.enum.instruments import InstrumentSectionEnum
from core.enum.status import UploadStatus
from core.models.organizations import Musician
from core.models.music import Piece, Part, InstrumentSection, MusicianInstrument
from core.services.s3 import create_upload_url
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


def get_piece_by_id(piece_id: str, organization_id: str) -> PieceDTO:
    piece = Piece.objects.get(id=piece_id, organization__id=organization_id)
    return PieceDTO.from_model(piece)


def get_pieces(organization_id: str) -> List[PieceDTO]:
    piece_models = Piece.objects.filter(organization__id=organization_id).annotate(
        parts_count=Count("parts")
    )
    return PieceDTO.from_models(piece_models)


def get_pieces_count(organization_id: str) -> int:
    return Piece.objects.filter(organization__id=organization_id).count()


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

    return PartDTO.from_model(part)


def update_part(dto: PartDTO) -> PartDTO:
    part = Part.objects.get(id=dto.id)

    part.file_key = dto.file_key
    part.upload_url = dto.upload_url
    part.upload_filename = dto.upload_filename
    part.status = dto.status.value

    part.save()
    return PartDTO.from_model(part)


def get_parts(piece_id: str) -> List[PartDTO]:
    parts = Part.objects.filter(piece_id=piece_id)
    return PartDTO.from_models(parts)


def get_instrument_section(
    instrument: InstrumentSectionEnum,
) -> InstrumentSectionDTO | None:
    instrument_section = InstrumentSection.objects.filter(name=instrument.value).first()
    if instrument_section:
        return InstrumentSectionDTO.from_model(instrument_section)
    else:
        return None


@transaction.atomic
def update_musician_instrument_sections(
    musician_id: str, instrument_sections: List[InstrumentSectionEnum]
):
    musician = Musician.objects.get(id=musician_id)
    instrument_names = [s.value for s in instrument_sections]

    instrument_sections = list(
        InstrumentSection.objects.filter(name__in=instrument_names)
    )

    # 1) Clear existing links
    MusicianInstrument.objects.filter(musician=musician).delete()

    # 2) Recreate
    MusicianInstrument.objects.bulk_create(
        [
            MusicianInstrument(musician=musician, instrument_section=instrument_section)
            for instrument_section in instrument_sections
        ]
    )
