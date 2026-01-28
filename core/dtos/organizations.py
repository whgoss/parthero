from typing import Optional, List
from uuid import UUID
from core.dtos.base import BaseDTO
from core.enum.instruments import InstrumentEnum
from core.models.music import MusicianInstrument
from core.models.organizations import Organization, Musician


class OrganizationDTO(BaseDTO):
    name: str
    enabled: bool
    timezone: str

    def to_model(self, model: Organization):
        return model(
            id=UUID(self.id),
            name=self.name,
            enabled=self.enabled,
            time=self.timezone,
        )

    @classmethod
    def from_model(cls, model: Organization):
        return cls(
            id=str(model.id),
            name=model.name,
            enabled=model.enabled,
            timezone=model.timezone,
        )


class MusicianDTO(BaseDTO):
    first_name: str
    last_name: str
    email: str
    principal: bool
    core_member: bool
    organization: OrganizationDTO
    instruments: List["MusicianInstrumentDTO"]
    phone_number: Optional[str] = None
    address: Optional[str] = None

    @classmethod
    def from_model(cls, model: Musician):
        if not model:
            return None
        return cls(
            id=str(model.id),
            first_name=model.first_name,
            last_name=model.last_name,
            email=model.email,
            principal=model.principal,
            core_member=model.core_member,
            organization=OrganizationDTO.from_model(model.organization),
            instruments=MusicianInstrumentDTO.from_models(model.instruments.all()),
            phone_number=model.phone_number if model.phone_number else None,
            address=model.address if model.address else None,
        )


class MusicianInstrumentDTO(BaseDTO):
    musician_id: str
    instrument: InstrumentEnum

    @classmethod
    def from_model(cls, model: MusicianInstrument):
        return cls(
            id=str(model.id),
            musician_id=str(model.musician.id),
            instrument=InstrumentEnum(model.instrument.name),
        )
