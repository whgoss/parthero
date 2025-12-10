from typing import Optional, List
from uuid import UUID
from core.dtos.base import BaseDTO
from core.models.music import MusicianInstrument
from core.models.organizations import Organization, Musician


class OrganizationDTO(BaseDTO):
    name: str
    enabled: bool

    def to_model(self, model: Organization):
        return model(
            id=UUID(self.id),
            name=self.name,
            enabled=self.enabled,
        )

    @classmethod
    def from_model(cls, model: Organization):
        return cls(id=str(model.id), name=model.name, enabled=model.enabled)


class MusicianDTO(BaseDTO):
    first_name: str
    last_name: str
    email: str
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
            core_member=model.core_member,
            organization=OrganizationDTO.from_model(model.organization),
            instruments=MusicianInstrumentDTO.from_models(model.instruments.all()),
            phone_number=model.phone_number if model.phone_number else None,
            address=model.address if model.address else None,
        )


class MusicianInstrumentDTO(BaseDTO):
    instrument: str

    @classmethod
    def from_model(cls, model: MusicianInstrument):
        return cls(
            id=str(model.id),
            instrument=model.instrument.name,
        )
