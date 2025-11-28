from core.dtos.base import BaseDTO
from core.models.organizations import Organization


class OrganizationDTO(BaseDTO):
    name: str

    @classmethod
    def from_model(self, model: Organization):
        self.id = str(model.id)
        self.name = model.name
