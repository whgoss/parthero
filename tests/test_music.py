import pytest
from faker import Faker
from moto import mock_aws
from tests.mocks import create_organization
from core.enum.status import UploadStatus
from core.services.music import create_piece, create_edition, create_part
from core.utils import get_file_extension

faker = Faker()
pytestmark = pytest.mark.django_db


@mock_aws
def test_create_piece():
    organization = create_organization()
    piece = create_piece(
        organization_id=str(organization.id),
        title="Firebird Suite",
        composer="Igor Stravinsky",
    )
    edition = create_edition(
        piece.id,
        name="1919 Version",
        instrumentation="2[1.2/pic] 2[1.2/Eh] 2[1.2] 2[1.2] — 4 2 3 1 — tmp+1 — hp — cel — pf — str",
    )

    assert piece is not None
    assert piece.title == "Firebird Suite"
    assert piece.composer == "Igor Stravinsky"
    assert piece.organization_id == organization.id
    assert edition.piece == piece
    assert edition.name == "1919 Version"
    assert (
        edition.instrumentation
        == "2[1.2/pic] 2[1.2/Eh] 2[1.2] 2[1.2] — 4 2 3 1 — tmp+1 — hp — cel — pf — str"
    )


@mock_aws
def test_create_part():
    organization = create_organization()
    organization = create_organization()
    piece = create_piece(
        organization_id=str(organization.id),
        title="Firebird Suite",
        composer="Igor Stravinsky",
    )
    edition = create_edition(
        piece.id,
        name="1919 Version",
        instrumentation="2[1.2/pic] 2[1.2/Eh] 2[1.2] 2[1.2] — 4 2 3 1 — tmp+1 — hp — cel — pf — str",
    )

    filename = "NOMIA Menu Theme (Full Score).pdf"
    part = create_part(
        edition_id=edition.id,
        filename=filename,
    )

    assert part is not None
    assert part.edition_id == edition.id
    assert part.status == UploadStatus.PENDING
    assert part.upload_url is not None
    assert part.upload_filename == filename
    assert part.file_key == str(edition.id) + "/" + str(part.id) + get_file_extension(
        filename
    )
