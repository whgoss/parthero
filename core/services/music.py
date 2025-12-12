import uuid
from typing import List, Optional
from django.db import transaction
from django.db.models import Count
from core.dtos.music import PieceDTO, PartDTO, InstrumentSectionDTO, EditionDTO
from core.enum.instruments import InstrumentSectionEnum
from core.enum.status import UploadStatus
from core.models.organizations import Musician
from core.models.music import (
    Piece,
    Part,
    InstrumentSection,
    MusicianInstrument,
    Edition,
)
from core.services.s3 import create_upload_url
from core.utils import get_file_extension


def create_piece(
    organization_id: str,
    title: str,
    composer: str,
    arranger: str = None,
) -> PieceDTO:
    piece = Piece(
        organization_id=organization_id,
        title=title,
        composer=composer,
        arranger=arranger,
    )
    piece.save()
    return PieceDTO.from_model(piece)


def get_piece_by_id(organization_id: str, piece_id: str) -> PieceDTO:
    piece = Piece.objects.get(id=piece_id, organization__id=organization_id)
    return PieceDTO.from_model(piece)


def get_pieces(organization_id: str) -> List[PieceDTO]:
    piece_models = Piece.objects.filter(organization__id=organization_id).annotate(
        editions_count=Count("editions")
    )
    return PieceDTO.from_models(piece_models)


def get_pieces_count(organization_id: str) -> int:
    return Piece.objects.filter(organization__id=organization_id).count()


def create_edition(
    piece_id: str,
    name: str,
    instrumentation: str,
    duration: Optional[int] = None,
) -> EditionDTO:
    piece = Piece.objects.get(id=piece_id)
    edition = Edition(
        name=name, piece_id=piece.id, instrumentation=instrumentation, duration=duration
    )
    edition.save()
    return EditionDTO.from_model(edition)


def create_part(edition_id: str, filename: str) -> PartDTO:
    edition = Edition.objects.get(id=edition_id)

    # Create the part
    part_id = uuid.uuid4()

    part = Part(
        id=part_id,
        edition_id=str(edition.id),
        upload_filename=filename,
    )
    part.save()

    # Generate a pre-signed URL for upload
    file_key = str(edition.id) + "/" + str(part.id) + get_file_extension(filename)
    presigned_url = create_upload_url(
        organization_id=str(edition.piece.organization.id),
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


def get_parts(edition_id: str) -> List[PartDTO]:
    parts = Part.objects.filter(edition_id=edition_id)
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
    instrument_section_strings = [
        instrument_section.value for instrument_section in instrument_sections
    ]

    instrument_sections = list(
        InstrumentSection.objects.filter(name__in=instrument_section_strings)
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
