from typing import List, Optional
from django.db.models import Q
from core.enum.instruments import InstrumentEnum
from core.models.organizations import Organization, Musician, SetupChecklist
from core.services.music import update_musician_instruments
from core.dtos.organizations import (
    OrganizationDTO,
    MusicianDTO,
    MusicianSearchResultDTO,
    SetupChecklistDTO,
)


def create_organization(name: str) -> OrganizationDTO:
    organization = Organization(name=name)
    organization.save()
    setup_checklist = SetupChecklist(organization=organization)
    setup_checklist.save()
    return OrganizationDTO.from_model(organization)


def get_organization(organization_id: str) -> OrganizationDTO:
    organization = Organization.objects.get(id=organization_id)
    return OrganizationDTO.from_model(organization)


def get_setup_checklist(organization_id: str) -> SetupChecklistDTO:
    setup_checklist, _ = SetupChecklist.objects.get_or_create(
        organization_id=organization_id
    )
    return SetupChecklistDTO.from_model(setup_checklist)


def create_musician(
    organization_id: str,
    first_name: str,
    last_name: str,
    email: str,
    principal: bool,
    core_member: bool,
    primary_instrument: InstrumentEnum,
    secondary_instruments: Optional[List[InstrumentEnum]] = None,
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

    update_musician_instruments(
        musician.id,
        primary_instrument=primary_instrument,
        secondary_instruments=secondary_instruments or [],
    )

    return MusicianDTO.from_model(musician)


def get_musician(organization_id: str, musician_id: str) -> MusicianDTO:
    musician = Musician.objects.get(organization__id=organization_id, id=musician_id)
    return MusicianDTO.from_model(musician)


def get_musician_by_email(organization_id: str, email: str) -> MusicianDTO | None:
    musician = Musician.objects.filter(
        organization__id=organization_id, email=email
    ).first()
    return MusicianDTO.from_model(musician) if musician else None


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
    primary_instrument: InstrumentEnum,
    secondary_instruments: Optional[List[InstrumentEnum]] = None,
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

    update_musician_instruments(
        musician.id,
        primary_instrument=primary_instrument,
        secondary_instruments=secondary_instruments or [],
    )

    musician.save()
    return MusicianDTO.from_model(musician)


def search_for_musician(
    organization_id: str,
    name: Optional[str] = None,
    instrument: Optional[str] = None,
    limit: int = 25,
    offset: int = 0,
    sort: Optional[str] = None,
) -> MusicianSearchResultDTO:
    search_query = Q(organization_id=organization_id)
    if name:
        search_query &= (
            Q(first_name__icontains=name)
            | Q(last_name__icontains=name)
            | Q(email__icontains=name)
        )
    if instrument:
        search_query &= Q(instruments__instrument__name__icontains=instrument)

    musicians = Musician.objects.filter(search_query).prefetch_related(
        "instruments__instrument"
    )
    sort_field = "last_name"
    sort_direction = "asc"
    if sort and ":" in sort:
        field, direction = sort.split(":", 1)
        sort_field = (field or "").strip()
        sort_direction = (direction or "").strip().lower()
    allowed_sort_fields = {
        "first_name",
        "last_name",
        "email",
        "principal",
        "core_member",
    }
    if sort_field not in allowed_sort_fields:
        sort_field = "last_name"
    sort_prefix = "-" if sort_direction == "dsc" else ""
    musicians = musicians.order_by(f"{sort_prefix}{sort_field}", "first_name", "email")

    limit = min(max(limit, 1), 100)
    offset = max(offset, 0)
    total = musicians.count()
    page = musicians[offset : offset + limit]
    return MusicianSearchResultDTO(total=total, data=MusicianDTO.from_models(page))
