from faker import Faker
from core.services.organizations import (
    create_organization as service_create_organization,
)
from core.dtos.organizations import OrganizationDTO

faker = Faker()


def create_organization():
    organization = service_create_organization(name=faker.company())
    return OrganizationDTO.from_model(organization)
