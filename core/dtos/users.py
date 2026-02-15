from core.dtos.base import BaseDTO
from core.models.users import User, UserOrganization


class UserDTO(BaseDTO):
    username: str
    first_name: str
    last_name: str
    email: str

    @classmethod
    def from_model(cls, model: User):
        return cls(
            id=str(model.id),
            username=model.username,
            first_name=model.first_name,
            last_name=model.last_name,
            email=model.email,
        )


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
