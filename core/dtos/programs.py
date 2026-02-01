from datetime import datetime
from typing import Optional, List
from core.dtos.base import BaseDTO
from core.enum.instruments import InstrumentEnum
from core.enum.status import ProgramStatus
from core.models.programs import (
    Program,
    ProgramPerformance,
    ProgramMusician,
    ProgramMusicianInstrument,
)


class ProgramDTO(BaseDTO):
    organization_id: str
    name: str
    status: ProgramStatus = ProgramStatus.CREATED
    piece_count: int
    performances: Optional[List["ProgramPerformanceDTO"]] = None

    @classmethod
    def from_model(
        cls,
        model: Program,
        piece_count: Optional[int] = None,
    ):
        if piece_count is None:
            piece_count = getattr(model, "piece_count", None)

        if piece_count is None:
            piece_count = model.pieces.count()

        return cls(
            id=str(model.id),
            organization_id=str(model.organization.id),
            name=model.name,
            status=ProgramStatus(model.status),
            performances=ProgramPerformanceDTO.from_models(model.performances.all()),
            piece_count=piece_count,
        )


class ProgramPerformanceDTO(BaseDTO):
    program_id: str
    date: datetime
    timezone: str

    @classmethod
    def from_model(cls, model: ProgramPerformance):
        return cls(
            id=str(model.id),
            program_id=str(model.program.id),
            date=model.date,
            timezone=model.timezone,
        )


class ProgramMusicianDTO(BaseDTO):
    program_id: str
    musician_id: str
    organization_id: str
    first_name: str
    last_name: str
    email: str
    principal: bool
    core_member: bool
    instruments: List["ProgramMusicianInstrumentDTO"]
    phone_number: Optional[str] = None
    address: Optional[str] = None

    @classmethod
    def from_model(cls, model: ProgramMusician):
        if not model:
            return None
        return cls(
            id=str(model.id),
            program_id=str(model.program.id),
            musician_id=str(model.musician.id),
            organization_id=str(model.musician.organization.id),
            first_name=model.musician.first_name,
            last_name=model.musician.last_name,
            email=model.musician.email,
            principal=model.musician.principal,
            core_member=model.musician.core_member,
            instruments=ProgramMusicianInstrumentDTO.from_models(
                model.instruments.all()
            ),
            phone_number=model.musician.phone_number
            if model.musician.phone_number
            else None,
            address=model.musician.address if model.musician.address else None,
        )


class ProgramMusicianInstrumentDTO(BaseDTO):
    program_id: str
    musician_id: str
    instrument: InstrumentEnum

    @classmethod
    def from_model(cls, model: ProgramMusicianInstrument):
        return cls(
            id=str(model.id),
            program_id=str(model.program_musician.program.id),
            musician_id=str(model.program_musician.musician.id),
            instrument=InstrumentEnum(model.instrument.name),
        )
