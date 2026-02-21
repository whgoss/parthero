import pytest
from faker import Faker
from core.models.music import PartAsset, Piece
from core.models.programs import Program
from core.models.organizations import Musician
from core.enum.instruments import InstrumentEnum
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
from core.services.programs import (
    create_program,
    get_program,
    get_programs,
    get_pieces_for_program,
    add_piece_to_program,
    remove_piece_from_program,
    get_musicians_for_program,
    add_musician_to_program,
    remove_musician_from_program,
    add_program_musician_instrument,
    remove_program_musician_instrument,
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


def _create_program_for_org(organization_id: str):
    return create_program(
        organization_id=organization_id,
        name=faker.sentence(nb_words=2),
        performance_dates=[],
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
        primary_instrument=InstrumentEnum.VIOLIN_1,
        secondary_instruments=[],
    )

    with pytest.raises(Musician.DoesNotExist):
        get_musician(str(org_b.id), str(musician.id))


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
        primary_instrument=InstrumentEnum.VIOLIN_1,
        secondary_instruments=[],
    )

    result = update_musician(
        organization_id=str(org_b.id),
        musician_id=str(musician.id),
        first_name=musician.first_name,
        last_name=musician.last_name,
        email=faker.email(),
        principal=False,
        core_member=True,
        primary_instrument=InstrumentEnum.VIOLIN_1,
        secondary_instruments=[],
    )
    assert result is None

    unchanged = get_musician(str(org_a.id), str(musician.id))
    assert unchanged is not None
    assert unchanged.email == email


def test_get_program_blocks_cross_tenant_access():
    org_a = create_organization()
    org_b = create_organization()
    program = _create_program_for_org(str(org_a.id))

    with pytest.raises(Program.DoesNotExist):
        get_program(str(org_b.id), str(program.id))


def test_get_programs_is_scoped_to_organization():
    org_a = create_organization()
    org_b = create_organization()
    _create_program_for_org(str(org_a.id))
    _create_program_for_org(str(org_b.id))

    programs = get_programs(str(org_a.id))
    assert len(programs) == 1
    assert programs[0].organization_id == str(org_a.id)


def test_program_piece_mutations_block_cross_tenant_access():
    org_a = create_organization()
    org_b = create_organization()
    program = _create_program_for_org(str(org_a.id))
    piece = _create_piece_for_org(str(org_a.id))

    with pytest.raises(Program.DoesNotExist):
        add_piece_to_program(str(org_b.id), str(program.id), str(piece.id))

    with pytest.raises(Program.DoesNotExist):
        remove_piece_from_program(str(org_b.id), str(program.id), str(piece.id))

    pieces = get_pieces_for_program(str(org_b.id), str(program.id))
    assert pieces == []


def test_program_musician_mutations_block_cross_tenant_access():
    org_a = create_organization()
    org_b = create_organization()
    program = _create_program_for_org(str(org_a.id))
    musician = create_musician(
        organization_id=str(org_a.id),
        first_name=faker.first_name(),
        last_name=faker.last_name(),
        email=faker.email(),
        principal=False,
        core_member=True,
        primary_instrument=InstrumentEnum.VIOLIN_1,
        secondary_instruments=[],
    )

    with pytest.raises(Program.DoesNotExist):
        add_musician_to_program(str(org_b.id), str(program.id), str(musician.id))

    roster = add_musician_to_program(str(org_a.id), str(program.id), str(musician.id))
    assert len(roster) == 1
    program_musician_id = roster[0].id

    with pytest.raises(Program.DoesNotExist):
        remove_musician_from_program(
            str(org_b.id), str(program.id), str(program_musician_id)
        )

    with pytest.raises(Program.DoesNotExist):
        add_program_musician_instrument(
            str(org_b.id),
            str(program.id),
            str(program_musician_id),
            InstrumentEnum.VIOLIN_1,
        )

    with pytest.raises(Program.DoesNotExist):
        remove_program_musician_instrument(
            str(org_b.id),
            str(program.id),
            str(program_musician_id),
            InstrumentEnum.VIOLIN_1,
        )

    cross_tenant_roster = get_musicians_for_program(str(org_b.id), str(program.id))
    assert cross_tenant_roster == []
