from typing import List
from core.dtos.organizations import OrganizationDTO, MusicianDTO
from core.dtos.users import UserOrganizationDTO
from core.models.organizations import Organization, Musician
from core.models.users import UserOrganization


def create_organization(name: str) -> OrganizationDTO:
    organization = Organization(name=name)
    organization.save()
    organization
    return OrganizationDTO.from_model(organization)


def get_organization(organization_id: str) -> OrganizationDTO:
    organization = Organization.objects.get(id=organization_id)
    return OrganizationDTO.from_model(organization)


def get_organizations_for_user(user_id) -> UserOrganizationDTO:
    user_organizations = UserOrganization.objects.filter(user__id=user_id)
    return UserOrganizationDTO.from_models(user_organizations)


def get_roster(organization_id: str) -> List[MusicianDTO]:
    musicians = Musician.objects.filter(organization__id=organization_id)
    return MusicianDTO.from_models(musicians)


def musician_exists_by_email(email, organization_id: str) -> bool:
    return Musician.objects.filter(
        email=email, organization__id=organization_id
    ).exists()
