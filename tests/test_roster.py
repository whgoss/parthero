import pytest
from faker import Faker
from moto import mock_aws
from tests.mocks import create_organization
from core.services.files import upload_roster
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
