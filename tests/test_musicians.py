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
        organization_id=organization.id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        principal=False,
        core_member=True,
        instruments=[
            InstrumentEnum.VIOLIN_1,
            InstrumentEnum.VIOLIN_2,
        ],
    )

    assert musician.first_name == first_name
    assert musician.last_name == last_name
    assert musician.email == email
    assert musician.organization == organization

    instruments = [instrument.instrument for instrument in musician.instruments]
    assert InstrumentEnum.VIOLIN_1 in instruments
    assert InstrumentEnum.VIOLIN_2 in instruments


def test_update_musician():
    organization = create_organization()
    first_name = faker.first_name()
    last_name = faker.last_name()
    email = faker.email()
    musician = create_musician(
        organization_id=organization.id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        principal=False,
        core_member=True,
        instruments=[
            InstrumentEnum.VIOLIN_1,
            InstrumentEnum.VIOLIN_2,
        ],
    )

    new_email = faker.email()
    musician = update_musician(
        organization_id=organization.id,
        musician_id=musician.id,
        first_name=first_name,
        last_name=last_name,
        email=new_email,
        principal=False,
        core_member=True,
        instruments=[
            InstrumentEnum.TIMPANI,
        ],
    )

    assert musician.first_name == first_name
    assert musician.last_name == last_name
    assert musician.email != email
    assert musician.email == new_email
    assert musician.organization == organization

    instruments = [instrument.instrument for instrument in musician.instruments]
    assert InstrumentEnum.TIMPANI in instruments
    assert InstrumentEnum.VIOLIN_1 not in instruments
    assert InstrumentEnum.VIOLIN_2 not in instruments
