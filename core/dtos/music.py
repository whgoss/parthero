import json
from typing import Optional, List
from pydantic import computed_field, Field
from core.dtos.base import BaseDTO
from core.dtos.organizations import MusicianDTO
from core.models.music import (
    Piece,
    Part,
    PartAsset,
    Instrument,
    PartInstrument,
    MusicianInstrument,
)
from core.enum.status import UploadStatus
from core.enum.instruments import InstrumentEnum, InstrumentFamily


class InstrumentDTO(BaseDTO):
    name: InstrumentEnum
    family: InstrumentFamily

    @classmethod
    def from_model(cls, model: Instrument):
        return cls(
            id=str(model.id),
            name=InstrumentEnum(model.name),
            family=InstrumentFamily(model.family),
        )


class MusicianInstrumentDTO(BaseDTO):
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
    organization_id: str
    instrumentation: str
    parts_count: int
    completed_parts: int
    duration: Optional[int] = None

    @classmethod
    def from_model(
        cls,
        model: Piece,
        parts_count: Optional[int] = None,
        completed_parts: Optional[int] = None,
    ):
        if parts_count is None:
            parts_count = getattr(model, "parts_count", None)

        if completed_parts is None:
            completed_parts = getattr(model, "completed_parts", None)

        if parts_count is None:
            parts_count = model.parts.count()

        if completed_parts is None:
            completed_parts = (
                Part.objects.filter(
                    piece_id=str(model.id), assets__status=UploadStatus.UPLOADED.value
                )
                .distinct()
                .count()
            )

        return cls(
            id=str(model.id),
            title=model.title,
            composer=model.composer,
            organization_id=str(model.organization.id),
            instrumentation=model.instrumentation,
            parts_count=parts_count,
            completed_parts=completed_parts,
            duration=model.duration,
        )


class PartDTO(BaseDTO):
    piece_id: str
    instruments: Optional[List["PartInstrumentDTO"]] = None
    number: Optional[int] = None

    @property
    def is_doubling(self) -> bool:
        return len(self.instruments) > 1

    @computed_field
    @property
    def display_name(self) -> str:
        names = [
            part_instrument.instrument.name.value
            for part_instrument in self.instruments
        ]
        if len(names) == 1:
            if self.number:
                return f"{names[0]} {self.number}"
            else:
                return f"{names[0]}"

        primary = None
        for part_instrument in self.instruments:
            if part_instrument.primary:
                primary = part_instrument
        if self.number and primary:
            primary_name = primary.instrument.name.value
            if self.is_doubling:
                extras = [n for n in names if n != primary_name]
                return f"{primary_name} {self.number} / {' + '.join(extras)}"
            else:
                return f"{primary_name} {self.number}"
        return " / ".join(names)

    @property
    def display_name_json(self) -> str:
        return json.dumps([self.display_name])

    @classmethod
    def from_model(cls, model: Part):
        return cls(
            id=str(model.id),
            piece_id=str(model.piece.id),
            instruments=PartInstrumentDTO.from_models(model.instruments.all()),
            number=model.number,
        )


class PartInstrumentDTO(BaseDTO):
    part_id: str
    primary: bool
    instrument: InstrumentDTO

    @classmethod
    def from_model(cls, model: PartInstrument):
        return cls(
            id=str(model.id),
            part_id=str(model.part.id),
            primary=model.primary,
            instrument=InstrumentDTO.from_model(model.instrument),
        )


class PartAssetDTO(BaseDTO):
    piece_id: str
    status: UploadStatus
    parts: Optional[List[PartDTO]] = None
    upload_filename: Optional[str] = None
    upload_url: Optional[str] = Field(default=None, exclude=True)
    file_key: Optional[str] = Field(default=None, exclude=True)

    def display_name(self) -> str:
        return [part.display_name for part in self.parts]

    def display_name_json(self) -> str:
        return json.dumps(self.display_name)

    @classmethod
    def from_model(cls, model: PartAsset):
        return cls(
            id=str(model.id),
            piece_id=str(model.piece.id),
            parts=PartDTO.from_models(model.parts.all()) if model.parts else None,
            status=UploadStatus(model.status),
            upload_url=model.upload_url,
            upload_filename=model.upload_filename,
            file_key=model.file_key,
        )


class PartAssetUploadDTO(PartAssetDTO):
    upload_url: Optional[str] = None
    file_key: Optional[str] = None


class PartOptionDTO(BaseDTO):
    value: str


class PartAssetsPayloadDTO(BaseDTO):
    part_assets: List[PartAssetDTO]
    missing_parts: List[PartDTO]
    part_options: List[PartOptionDTO]
