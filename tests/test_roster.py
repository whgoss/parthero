import pytest
from faker import Faker
from moto import mock_aws
from tests.mocks import create_organization
from core.services.files import upload_roster
from core.enum.instruments import InstrumentEnum
from core.services.organizations import create_musician, update_musician
from parthero.settings_test import BASE_DIR

faker = Faker()
pytestmark = pytest.mark.django_db


@mock_aws
def test_roster_upload():
    organization = create_organization()
    filename = BASE_DIR / "tests" / "data" / "Test Roster.csv"
    with open(filename, "r") as file:
        musicians = upload_roster(file=file, organization_id=organization.id)
    assert len(musicians) == 12


def test_create_musician():
    organization = create_organization()
    first_name = faker.first_name()
    last_name = faker.last_name()
    email = faker.email()
    musician = create_musician(
        organization.id,
        first_name,
        last_name,
        email,
        True,
        instrument_sections=[
            InstrumentEnum.VIOLIN_1,
            InstrumentEnum.VIOLIN_2,
        ],
    )

    assert musician.first_name == first_name
    assert musician.last_name == last_name
    assert musician.email == email
    assert musician.organization == organization

    instrument_sections = [
        instrument_section.instrument_section
        for instrument_section in musician.instrument_sections
    ]
    assert InstrumentEnum.VIOLIN_1 in instrument_sections
    assert InstrumentEnum.VIOLIN_2 in instrument_sections


def test_update_musician():
    organization = create_organization()
    first_name = faker.first_name()
    last_name = faker.last_name()
    email = faker.email()
    musician = create_musician(
        organization.id,
        first_name,
        last_name,
        email,
        True,
        instrument_sections=[
            InstrumentEnum.VIOLIN_1,
            InstrumentEnum.VIOLIN_2,
        ],
    )

    musician = update_musician(
        organization.id,
        musician.id,
        first_name,
        last_name,
        faker.email(),
        True,
        instrument_sections=[InstrumentEnum.TIMPANI],
    )

    assert musician.first_name == first_name
    assert musician.last_name == last_name
    assert musician.email != email
    assert musician.organization == organization

    instrument_sections = [
        instrument_section.instrument_section
        for instrument_section in musician.instrument_sections
    ]
    assert InstrumentEnum.TIMPANI in instrument_sections
    assert InstrumentEnum.VIOLIN_1 not in instrument_sections
    assert InstrumentEnum.VIOLIN_2 not in instrument_sections
