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
    ProgramChecklist,
)
from core.dtos.users import UserDTO


class ProgramDTO(BaseDTO):
    organization_id: str
    name: str
    status: ProgramStatus = ProgramStatus.CREATED
    piece_count: int
    checklist: "ProgramChecklistDTO"
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
            checklist=ProgramChecklistDTO.from_model(model.checklist),
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


class ProgramChecklistDTO(BaseDTO):
    program_id: str
    pieces_completed_on: Optional[datetime] = None
    pieces_completed_by: Optional[UserDTO] = None
    roster_completed_on: Optional[datetime] = None
    roster_completed_by: Optional[UserDTO] = None
    overrides_completed_on: Optional[datetime] = None
    overrides_completed_by: Optional[UserDTO] = None
    bowings_completed_on: Optional[datetime] = None
    bowings_completed_by: Optional[UserDTO] = None
    assignments_sent_on: Optional[datetime] = None
    assignments_sent_by: Optional[UserDTO] = None
    assignments_completed_on: Optional[datetime] = None
    assignments_completed_by: Optional[UserDTO] = None
    delivery_sent_on: Optional[datetime] = None
    delivery_sent_by: Optional[UserDTO] = None
    delivery_completed_on: Optional[datetime] = None

    @property
    def pieces_completed(self) -> bool:
        return self.pieces_completed_on is not None

    @property
    def roster_completed(self) -> bool:
        return self.roster_completed_on is not None

    @property
    def overrides_completed(self) -> bool:
        return self.overrides_completed_on is not None

    @property
    def bowings_completed(self) -> bool:
        return self.bowings_completed_on is not None

    @property
    def assignments_completed(self) -> bool:
        return self.assignments_completed_on is not None

    @property
    def delivery_sent(self) -> bool:
        return self.delivery_sent_on is not None

    @property
    def completed(self) -> bool:
        return (
            self.pieces_completed
            and self.roster_completed
            and self.overrides_completed
            and self.bowings_completed
            and self.assignments_completed
            and self.delivery_sent
        )

    @classmethod
    def from_model(cls, model: ProgramChecklist):
        return cls(
            id=str(model.id),
            program_id=str(model.program.id),
            pieces_completed_on=model.pieces_completed_on,
            pieces_completed_by=UserDTO.from_model(model.pieces_completed_by)
            if model.pieces_completed_by
            else None,
            roster_completed_on=model.roster_completed_on,
            roster_completed_by=UserDTO.from_model(model.roster_completed_by)
            if model.roster_completed_by
            else None,
            overrides_completed_on=model.overrides_completed_on,
            overrides_completed_by=UserDTO.from_model(model.overrides_completed_by)
            if model.overrides_completed_by
            else None,
            bowings_completed_on=model.bowings_completed_on,
            bowings_completed_by=UserDTO.from_model(model.bowings_completed_by)
            if model.bowings_completed_by
            else None,
            assignments_sent_on=model.assignments_sent_on,
            assignments_sent_by=UserDTO.from_model(model.assignments_sent_by)
            if model.assignments_sent_by
            else None,
            assignments_completed_on=model.assignments_completed_on,
            assignments_completed_by=UserDTO.from_model(model.assignments_completed_by)
            if model.assignments_completed_by
            else None,
            delivery_sent_on=model.delivery_sent_on,
            delivery_sent_by=UserDTO.from_model(model.delivery_sent_by)
            if model.delivery_sent_by
            else None,
            delivery_completed_on=model.delivery_completed_on,
        )
