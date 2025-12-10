from typing import Optional, List
from datetime import timedelta
from core.dtos.base import BaseDTO
from core.dtos.organizations import MusicianDTO, OrganizationDTO
from core.models.music import (
    Piece,
    Part,
    Instrument,
    Edition,
    PartInstrument,
    MusicianInstrument,
)
from core.enum.status import UploadStatus
from core.enum.instruments import InstrumentEnum


class InstrumentDTO(BaseDTO):
    name: InstrumentEnum

    @classmethod
    def from_model(cls, model: Instrument):
        return cls(
            id=str(model.id),
            name=InstrumentEnum(model.name),
        )


class MusicianInstrument(BaseDTO):
    musician: MusicianDTO
    instrument: InstrumentDTO

    @classmethod
    def from_model(cls, model: MusicianInstrument):
        return cls(
            id=str(model.id),
            musician=MusicianDTO.from_model(model.musician),
            instrument=InstrumentDTO.from_model(model.instrument),
        )


class PieceDTO(BaseDTO):
    title: str
    composer: str
    editions: List["EditionDTO"]
    organization: OrganizationDTO
    arranger: Optional[str] = None
    duration: Optional[timedelta] = None

    @classmethod
    def from_model(cls, model: Piece):
        return cls(
            id=str(model.id),
            title=model.title,
            composer=model.composer,
            organization=OrganizationDTO.from_model(model.organization),
            arranger=model.arranger,
            duration=model.duration,
        )


class EditionDTO(BaseDTO):
    name: str
    piece: PieceDTO
    instrumentation: str
    parts: List["PartDTO"]
    parts_count: int

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
        )


class PartDTO(BaseDTO):
    edition: EditionDTO
    status: UploadStatus
    part_instruments: List["PartInstrumentDTO"]
    upload_url: Optional[str] = None
    upload_filename: Optional[str] = None
    file_key: Optional[str] = None

    @classmethod
    def from_model(cls, model: Part):
        return cls(
            id=str(model.id),
            edition=PieceDTO.from_model(model.edition),
            status=UploadStatus(model.status),
            part_instruments=PartInstrumentDTO.from_models(
                model.part_instruments.all()
            ),
            upload_url=model.upload_url,
            upload_filename=model.upload_filename,
            file_key=model.file_key,
        )


class PartInstrumentDTO(BaseDTO):
    part: PartDTO
    instrument: InstrumentDTO
    chair_number: int

    @classmethod
    def from_model(cls, model: PartInstrument):
        return cls(
            id=str(model.id),
            part=PieceDTO.from_model(model.part),
            instrument=InstrumentDTO.from_model(model.instrument),
            chair_number=model.chair_number,
        )
