import pytest
from faker import Faker
from core.models.music import PartAsset, Piece
from core.enum.music import PartAssetType
from core.enum.status import UploadStatus
from core.services.music import (
    create_piece,
    get_piece,
    get_parts,
    get_part_assets,
    get_part_asset,
    update_part_asset,
    delete_part_asset,
)
from core.services.organizations import (
    create_musician,
    get_musician,
    update_musician,
)
from tests.mocks import create_organization

faker = Faker()
pytestmark = pytest.mark.django_db


def _create_piece_for_org(organization_id: str):
    return create_piece(
        organization_id=organization_id,
        title=faker.sentence(nb_words=3),
        composer=faker.name(),
        instrumentation="2 2 2 2 — 4 2 3 1 — tmp+1 — hp — str",
        duration=None,
        domo_id=None,
        composer_domo_id=None,
    )


def test_get_piece_blocks_cross_tenant_access():
    org_a = create_organization()
    org_b = create_organization()
    piece = _create_piece_for_org(str(org_a.id))

    with pytest.raises(Piece.DoesNotExist):
        get_piece(str(org_b.id), str(piece.id))


def test_get_part_assets_blocks_cross_tenant_access():
    org_a = create_organization()
    org_b = create_organization()
    piece = _create_piece_for_org(str(org_a.id))

    with pytest.raises(Piece.DoesNotExist):
        get_part_assets(str(org_b.id), str(piece.id), PartAssetType.CLEAN)


def test_get_parts_returns_empty_for_cross_tenant_piece():
    org_a = create_organization()
    org_b = create_organization()
    piece = _create_piece_for_org(str(org_a.id))

    parts = get_parts(str(org_b.id), str(piece.id))
    assert parts == []


def test_part_asset_mutations_block_cross_tenant_access():
    org_a = create_organization()
    org_b = create_organization()
    piece = _create_piece_for_org(str(org_a.id))
    parts = get_parts(str(org_a.id), str(piece.id))

    part_asset = PartAsset.objects.create(
        piece_id=str(piece.id),
        upload_filename="Violin 1.pdf",
        asset_type=PartAssetType.CLEAN.value,
        status=UploadStatus.UPLOADED.value,
    )
    part_asset.parts.add(parts[0].id)

    with pytest.raises(PartAsset.DoesNotExist):
        get_part_asset(str(org_b.id), str(part_asset.id))

    with pytest.raises(PartAsset.DoesNotExist):
        update_part_asset(str(org_b.id), str(part_asset.id), [parts[0].id], None)

    with pytest.raises(PartAsset.DoesNotExist):
        delete_part_asset(str(org_b.id), str(part_asset.id))

    assert PartAsset.objects.filter(id=part_asset.id).exists()


def test_get_musician_blocks_cross_tenant_access():
    org_a = create_organization()
    org_b = create_organization()
    musician = create_musician(
        organization_id=str(org_a.id),
        first_name=faker.first_name(),
        last_name=faker.last_name(),
        email=faker.email(),
        principal=False,
        core_member=True,
        instruments=[],
    )

    result = get_musician(str(org_b.id), str(musician.id))
    assert result is None


def test_update_musician_blocks_cross_tenant_access():
    org_a = create_organization()
    org_b = create_organization()
    email = faker.email()
    musician = create_musician(
        organization_id=str(org_a.id),
        first_name=faker.first_name(),
        last_name=faker.last_name(),
        email=email,
        principal=False,
        core_member=True,
        instruments=[],
    )

    result = update_musician(
        organization_id=str(org_b.id),
        musician_id=str(musician.id),
        first_name=musician.first_name,
        last_name=musician.last_name,
        email=faker.email(),
        principal=False,
        core_member=True,
        instruments=[],
    )
    assert result is None

    unchanged = get_musician(str(org_a.id), str(musician.id))
    assert unchanged is not None
    assert unchanged.email == email
