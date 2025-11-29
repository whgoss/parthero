from core.dtos.organizations import OrganizationDTO
from core.dtos.users import UserOrganizationDTO
from core.models.organizations import Organization
from core.models.users import UserOrganization


def create_organization(name: str) -> OrganizationDTO:
    organization = Organization(name=name)
    organization.save()
    organization
    return OrganizationDTO.from_model(organization)


def get_organizations_for_user(user_id) -> UserOrganizationDTO:
    user_organizations = UserOrganization.objects.filter(user__id=user_id)
    return UserOrganizationDTO.from_models(user_organizations)
