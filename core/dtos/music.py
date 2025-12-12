from typing import Optional, List
from core.dtos.base import BaseDTO
from core.dtos.organizations import MusicianDTO
from core.models.music import (
    Piece,
    Part,
    InstrumentSection,
    Edition,
    PartInstrument,
    MusicianInstrument,
)
from core.enum.status import UploadStatus
from core.enum.instruments import InstrumentSectionEnum


class InstrumentSectionDTO(BaseDTO):
    name: InstrumentSectionEnum

    @classmethod
    def from_model(cls, model: InstrumentSection):
        return cls(
            id=str(model.id),
            name=InstrumentSectionEnum(model.name),
        )


class MusicianInstrumentDTO(BaseDTO):
    musician: MusicianDTO
    instrument_section: InstrumentSectionDTO

    @classmethod
    def from_model(cls, model: MusicianInstrument):
        return cls(
            id=str(model.id),
            musician=MusicianDTO.from_model(model.musician),
            instrument_section=InstrumentSectionDTO.from_model(
                model.instrument_section
            ),
        )


class PieceDTO(BaseDTO):
    title: str
    composer: str
    organization_id: str
    editions_count: int
    arranger: Optional[str] = None

    @classmethod
    def from_model(cls, model: Piece, editions_count: Optional[int] = None):
        if editions_count is None:
            editions_count = getattr(model, "editions_count", None)

        if editions_count is None:
            editions_count = model.editions.count()

        return cls(
            id=str(model.id),
            title=model.title,
            composer=model.composer,
            organization_id=str(model.organization.id),
            arranger=model.arranger,
            editions_count=editions_count,
        )


class EditionDTO(BaseDTO):
    name: str
    piece: PieceDTO
    instrumentation: str
    parts_count: int
    duration: Optional[int] = None

    @classmethod
    def from_model(cls, model: Edition, parts_count: Optional[int] = None):
        if parts_count is None:
            parts_count = getattr(model, "parts_count", None)

        if parts_count is None:
            parts_count = model.parts.count()

        return cls(
            id=str(model.id),
            name=model.name,
            piece=PieceDTO.from_model(model.piece),
            instrumentation=model.instrumentation,
            parts_count=parts_count,
            duration=model.duration,
        )


class PartDTO(BaseDTO):
    edition_id: str
    status: UploadStatus
    part_instruments: List["PartInstrumentDTO"] = []
    upload_url: Optional[str] = None
    upload_filename: Optional[str] = None
    file_key: Optional[str] = None

    @classmethod
    def from_model(cls, model: Part):
        return cls(
            id=str(model.id),
            edition_id=str(model.edition.id),
            status=UploadStatus(model.status),
            part_instruments=PartInstrumentDTO.from_models(
                model.part_instruments.all()
            ),
            upload_url=model.upload_url,
            upload_filename=model.upload_filename,
            file_key=model.file_key,
        )


class PartInstrumentDTO(BaseDTO):
    part_id: str
    instrument_section: InstrumentSectionDTO
    chair_number: int

    @classmethod
    def from_model(cls, model: PartInstrument):
        return cls(
            id=str(model.id),
            part_id=str(model.part.id),
            instrument_section=InstrumentSectionDTO.from_model(
                model.instrument_section
            ),
            chair_number=model.chair_number,
        )
