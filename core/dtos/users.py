from core.dtos.base import BaseDTO
from core.models.users import UserOrganization


class UserOrganizationDTO(BaseDTO):
    user_id: str
    organization_id: str
    name: str
    role: str

    @classmethod
    def from_model(cls, model: UserOrganization):
        return cls(
            id=str(model.id),
            user_id=str(model.user.id),
            organization_id=str(model.organization.id),
            name=model.organization.name,
            role=model.role,
        )
