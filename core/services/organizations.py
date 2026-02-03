from typing import List, Optional
from django.db.models import Q
from core.dtos.users import UserOrganizationDTO
from core.enum.instruments import InstrumentEnum
from core.models.users import UserOrganization
from core.models.organizations import Organization, Musician, SetupChecklist
from core.services.music import update_musician_instruments
from core.dtos.organizations import OrganizationDTO, MusicianDTO, SetupChecklistDTO


def create_organization(name: str) -> OrganizationDTO:
    organization = Organization(name=name)
    organization.save()
    setup_checklist = SetupChecklist(organization=organization)
    setup_checklist.save()
    return OrganizationDTO.from_model(organization)


def get_organization(organization_id: str) -> OrganizationDTO:
    organization = Organization.objects.get(id=organization_id)
    return OrganizationDTO.from_model(organization)


def get_organizations_for_user(user_id: str) -> UserOrganizationDTO:
    user_organizations = UserOrganization.objects.filter(user__id=user_id)
    return UserOrganizationDTO.from_models(user_organizations)


def get_setup_checklist(organization_id: str) -> SetupChecklistDTO:
    setup_checklist, _ = SetupChecklist.objects.get_or_create(
        organization_id=organization_id
    )
    return SetupChecklistDTO.from_model(setup_checklist)


def get_roster(organization_id: str) -> List[MusicianDTO]:
    musicians = Musician.objects.filter(organization__id=organization_id).order_by(
        "last_name"
    )
    return MusicianDTO.from_models(musicians)


def create_musician(
    organization_id: str,
    first_name: str,
    last_name: str,
    email: str,
    principal: bool,
    core_member: bool,
    instruments: Optional[List[InstrumentEnum]],
) -> MusicianDTO | None:
    musician = Musician.objects.filter(
        organization__id=organization_id, email=email
    ).first()
    if musician:
        return musician

    musician = Musician(
        first_name=first_name,
        last_name=last_name,
        email=email,
        principal=principal,
        core_member=core_member,
        organization_id=organization_id,
    )
    musician.save()

    if instruments:
        update_musician_instruments(musician.id, instruments)

    return MusicianDTO.from_model(musician)


def get_musician(organization_id: str, musician_id: str) -> MusicianDTO | None:
    musician = Musician.objects.filter(
        organization__id=organization_id, id=musician_id
    ).first()
    return MusicianDTO.from_model(musician)


def get_musician_by_email(organization_id: str, email: str) -> MusicianDTO | None:
    musician = Musician.objects.filter(
        organization__id=organization_id, email=email
    ).first()
    return MusicianDTO.from_model(musician)


def musician_exists_by_email(email, organization_id: str) -> bool:
    return Musician.objects.filter(
        email=email, organization__id=organization_id
    ).exists()


def update_musician(
    organization_id: str,
    musician_id: str,
    first_name: str,
    last_name: str,
    email: str,
    principal: bool,
    core_member: bool,
    instruments: Optional[List[InstrumentEnum]],
) -> MusicianDTO | None:
    musician = Musician.objects.filter(
        organization__id=organization_id, id=musician_id
    ).first()
    if not musician:
        return None

    musician.first_name = first_name
    musician.last_name = last_name
    musician.email = email
    musician.principal = principal
    musician.core_member = core_member

    if instruments:
        update_musician_instruments(musician.id, instruments)

    musician.save()
    return MusicianDTO.from_model(musician)


def search_for_musician(
    organization_id: str,
    name: Optional[str] = None,
    instrument: Optional[str] = None,
) -> List[MusicianDTO]:
    search_query = Q(organization_id=organization_id)
    if name:
        search_query &= Q(Q(first_name__icontains=name) | Q(last_name__icontains=name))
    if instrument:
        search_query &= Q(instruments__instrument__name__icontains=instrument)

    musicians = Musician.objects.filter(search_query).distinct()
    return MusicianDTO.from_models(musicians)
