from typing import Optional
from datetime import timedelta
from core.dtos.base import BaseDTO
from core.models.music import Piece, Part
from core.models.organizations import Section
from core.enum.status import UploadStatus
from core.enum.instruments import Instrument, InstrumentFamily


class PieceDTO(BaseDTO):
    title: str
    composer: str
    organization_id: str
    arranger: Optional[str] = None
    duration: Optional[timedelta] = None

    @classmethod
    def from_model(cls, model: Piece):
        return cls(
            id=str(model.id),
            title=model.title,
            composer=model.composer,
            organization_id=str(model.organization.id),
            arranger=model.arranger,
            duration=model.duration,
        )


class PartDTO(BaseDTO):
    piece_id: str
    status: UploadStatus
    section_id: Optional[str] = None
    upload_url: Optional[str] = None
    upload_filename: Optional[str] = None
    file_key: Optional[str] = None

    @classmethod
    def from_model(cls, model: Part):
        return cls(
            id=str(model.id),
            piece_id=str(model.piece.id),
            status=UploadStatus(model.status),
            section_id=str(model.section.id) if model.section else None,
            upload_url=model.upload_url,
            upload_filename=model.upload_filename,
            file_key=model.file_key,
        )


class SectionDTO(BaseDTO):
    instrument: Instrument
    family: InstrumentFamily
    organization_id: str
    number: Optional[int] = None

    @classmethod
    def from_model(cls, model: Section):
        return cls(
            id=str(model.id),
            instrument=Instrument(model.instrument),
            family=InstrumentFamily(model.family),
            organization_id=str(model.organization.id),
            number=model.number,
        )
