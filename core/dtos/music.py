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
    InstrumentSection,
    PartInstrument,
    MusicianInstrument,
)
from core.enum.music import PartAssetType
from core.enum.status import UploadStatus
from core.enum.instruments import (
    InstrumentEnum,
    InstrumentSectionEnum,
    INSTRUMENT_PRIMARIES,
)


class InstrumentDTO(BaseDTO):
    name: InstrumentEnum

    @classmethod
    def from_model(cls, model: Instrument):
        return cls(
            id=str(model.id),
            name=InstrumentEnum(model.name),
        )


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
                PartAsset.objects.filter(
                    piece_id=str(model.id),
                    asset_type=PartAssetType.CLEAN.value,
                    status=UploadStatus.UPLOADED.value,
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

        # Determine the primary instrument
        primary = None
        primary_name = None
        for part_instrument in self.instruments:
            if part_instrument.primary:
                primary = part_instrument
                primary_name = primary.instrument.name.value

        # If there's only 1 instrument
        if len(names) == 1:
            # Is this a part for non-primary woodwind instrument?
            if primary.instrument.name in INSTRUMENT_PRIMARIES.keys():
                return f"{primary_name} ({INSTRUMENT_PRIMARIES[primary.instrument.name].value} {self.number})"
            # Is there a chair number?
            if self.number:
                return f"{names[0]} {self.number}"
            else:
                return f"{names[0]}"

        # If there's multiple instruments it's a doubled part and we need to display all instruments
        if self.number and primary:
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
    asset_type: PartAssetType
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
            asset_type=PartAssetType(model.asset_type),
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
    id: str


class PartAssetsPayloadDTO(BaseDTO):
    part_assets: List[PartAssetDTO]
    missing_parts: List[PartDTO]
    part_options: List[PartOptionDTO]
