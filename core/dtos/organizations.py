from core.dtos.base import BaseDTO
from core.models.organizations import Organization


class OrganizationDTO(BaseDTO):
    name: str

    @classmethod
    def from_model(cls, model: Organization):
        return cls(id=str(model.id), name=model.name)
