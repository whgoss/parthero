import pytest
from faker import Faker
from moto import mock_aws
from datetime import timedelta
from tests.mocks import create_organization
from core.services.music import create_piece, create_part
from core.enum.status import UploadStatus
from core.utils import get_file_extension

faker = Faker()
pytestmark = pytest.mark.django_db


@mock_aws
def test_create_piece():
    organization = create_organization()
    piece = create_piece(
        title="Symphony No. 5",
        composer="Ludwig van Beethoven",
        organization_id=str(organization.id),
        arranger="John Doe",
        duration=timedelta(minutes=33),
    )

    assert piece is not None
    assert piece.title == "Symphony No. 5"
    assert piece.composer == "Ludwig van Beethoven"
    assert piece.organization_id == organization.id
    assert piece.arranger == "John Doe"
    assert piece.duration == timedelta(minutes=33)


@mock_aws
def test_create_part():
    organization = create_organization()
    piece = create_piece(
        title="NOMIA Menu Theme",
        composer="Will Goss",
        organization_id=str(organization.id),
        duration=timedelta(minutes=33),
    )

    filename = "NOMIA Menu Theme (Full Score).pdf"
    part = create_part(
        piece_id=piece.id,
        filename=filename,
    )

    assert part is not None
    assert part.piece_id == piece.id
    assert part.section_id is None
    assert part.status == UploadStatus.PENDING
    assert part.upload_url is not None
    assert part.upload_filename == filename
    assert part.file_key == str(piece.id) + "/" + str(part.id) + get_file_extension(
        filename
    )
