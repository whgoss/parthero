import pytest
from moto import mock_aws

from core.enum.instruments import InstrumentEnum
from core.services.music import create_part_asset, create_piece, get_parts
from tests.mocks import create_organization

pytestmark = pytest.mark.django_db


def _part_has_instrument(part, instrument_enum: InstrumentEnum) -> bool:
    return any(
        part_instrument.instrument.name == instrument_enum
        for part_instrument in part.instruments
    )


def _numbers_for_instrument(parts, instrument_enum: InstrumentEnum) -> set[int]:
    return {
        part.number for part in parts if _part_has_instrument(part, instrument_enum)
    }


def _parts_for_primary_instrument(parts, instrument_enum: InstrumentEnum):
    return [
        part
        for part in parts
        if any(
            part_instrument.primary
            and part_instrument.instrument.name == instrument_enum
            for part_instrument in part.instruments
        )
    ]


def _numbers_for_primary_instrument(parts, instrument_enum: InstrumentEnum) -> set[int]:
    return {
        part.number for part in _parts_for_primary_instrument(parts, instrument_enum)
    }


def _has_primary_with_doubling(
    parts, primary: InstrumentEnum, doubling: InstrumentEnum, number: int
) -> bool:
    for part in parts:
        if part.number != number:
            continue
        if not any(
            part_instrument.primary and part_instrument.instrument.name == primary
            for part_instrument in part.instruments
        ):
            continue
        if any(
            (not part_instrument.primary)
            and part_instrument.instrument.name == doubling
            for part_instrument in part.instruments
        ):
            return True
    return False


@mock_aws
def test_numbered_horn_and_english_horn_detection():
    organization = create_organization()
    instrumentation = "3[1.2/pic.pic] 2[1.2/Eh] 2 2 — 4 2 3 1 — tmp+5 — hp — str"
    piece = create_piece(
        organization_id=str(organization.id),
        title="Scheherazade",
        composer="Nikolai Rimsky-Korsakov",
        instrumentation=instrumentation,
        duration=None,
        domo_id=None,
        composer_domo_id=None,
    )

    parts = get_parts(piece.id)

    assert len(parts) == 31
    assert _numbers_for_primary_instrument(parts, InstrumentEnum.FLUTE) == {1, 2}
    assert _numbers_for_primary_instrument(parts, InstrumentEnum.PICCOLO) == {3}
    assert _numbers_for_primary_instrument(parts, InstrumentEnum.OBOE) == {1, 2}
    assert _numbers_for_primary_instrument(parts, InstrumentEnum.CLARINET) == {1, 2}
    assert _numbers_for_primary_instrument(parts, InstrumentEnum.BASSOON) == {1, 2}
    assert _numbers_for_primary_instrument(parts, InstrumentEnum.FRENCH_HORN) == {
        1,
        2,
        3,
        4,
    }
    assert _numbers_for_primary_instrument(parts, InstrumentEnum.TRUMPET) == {1, 2}
    assert _numbers_for_primary_instrument(parts, InstrumentEnum.TROMBONE) == {1, 2, 3}
    assert _numbers_for_primary_instrument(parts, InstrumentEnum.TUBA) == {1}
    assert _numbers_for_primary_instrument(parts, InstrumentEnum.TIMPANI) == {1}
    assert _numbers_for_primary_instrument(parts, InstrumentEnum.PERCUSSION) == {
        1,
        2,
        3,
        4,
        5,
    }
    assert _numbers_for_primary_instrument(parts, InstrumentEnum.ENGLISH_HORN) == set()

    harp_parts = _parts_for_primary_instrument(parts, InstrumentEnum.HARP)
    assert len(harp_parts) == 1
    assert harp_parts[0].number is None

    assert _has_primary_with_doubling(
        parts, InstrumentEnum.FLUTE, InstrumentEnum.PICCOLO, 2
    )
    assert _has_primary_with_doubling(
        parts, InstrumentEnum.OBOE, InstrumentEnum.ENGLISH_HORN, 2
    )

    string_primary = {
        InstrumentEnum.VIOLIN_1,
        InstrumentEnum.VIOLIN_2,
        InstrumentEnum.VIOLA,
        InstrumentEnum.CELLO,
        InstrumentEnum.DOUBLE_BASS,
    }
    for instrument_enum in string_primary:
        string_parts = _parts_for_primary_instrument(parts, instrument_enum)
        assert len(string_parts) == 1
        assert string_parts[0].number is None

    horn_asset = create_part_asset(
        piece_id=str(piece.id),
        filename="IMSLP40972-PMLP04406-Rimsky-Op35.Horn12.pdf",
    )
    horn_numbers = _numbers_for_instrument(horn_asset.parts, InstrumentEnum.FRENCH_HORN)
    assert horn_numbers == {1, 2}
    assert len(horn_asset.parts) == 2

    english_horn_asset = create_part_asset(
        piece_id=str(piece.id),
        filename="IMSLP40972-PMLP04406-Rimsky-Op35.EnglishHorn12.pdf",
    )
    english_horn_numbers = _numbers_for_instrument(
        english_horn_asset.parts, InstrumentEnum.ENGLISH_HORN
    )
    assert english_horn_numbers == {2}
    assert len(english_horn_asset.parts) == 1
    assert all(
        not _part_has_instrument(part, InstrumentEnum.FRENCH_HORN)
        for part in english_horn_asset.parts
    )


@mock_aws
def test_hyphenated_numbered_part_detection():
    organization = create_organization()
    instrumentation = (
        "2[1.2/pic] 2[1.2/Eh] 2 2 — 4 2 3 1 — tmp+3 — hp — pf/opt cel — str"
    )
    piece = create_piece(
        organization_id=str(organization.id),
        title="Firebird Suite",
        composer="Igor Stravinsky",
        instrumentation=instrumentation,
        duration=None,
        domo_id=None,
        composer_domo_id=None,
    )

    parts = get_parts(piece.id)
    assert len(parts) == 29
    assert _numbers_for_primary_instrument(parts, InstrumentEnum.FLUTE) == {1, 2}
    assert _numbers_for_primary_instrument(parts, InstrumentEnum.OBOE) == {1, 2}
    assert _numbers_for_primary_instrument(parts, InstrumentEnum.CLARINET) == {1, 2}
    assert _numbers_for_primary_instrument(parts, InstrumentEnum.BASSOON) == {1, 2}
    assert _numbers_for_primary_instrument(parts, InstrumentEnum.FRENCH_HORN) == {
        1,
        2,
        3,
        4,
    }
    assert _numbers_for_primary_instrument(parts, InstrumentEnum.TRUMPET) == {1, 2}
    assert _numbers_for_primary_instrument(parts, InstrumentEnum.TROMBONE) == {1, 2, 3}
    assert _numbers_for_primary_instrument(parts, InstrumentEnum.TUBA) == {1}
    assert _numbers_for_primary_instrument(parts, InstrumentEnum.TIMPANI) == {1}
    assert _numbers_for_primary_instrument(parts, InstrumentEnum.PERCUSSION) == {
        1,
        2,
        3,
    }
    assert _numbers_for_primary_instrument(parts, InstrumentEnum.PICCOLO) == set()
    assert _numbers_for_primary_instrument(parts, InstrumentEnum.ENGLISH_HORN) == set()

    harp_parts = _parts_for_primary_instrument(parts, InstrumentEnum.HARP)
    assert len(harp_parts) == 1
    assert harp_parts[0].number is None

    piano_parts = _parts_for_primary_instrument(parts, InstrumentEnum.PIANO)
    assert len(piano_parts) == 1
    assert piano_parts[0].number is None
    assert _has_primary_with_doubling(
        parts, InstrumentEnum.PIANO, InstrumentEnum.CELESTA, None
    )

    assert _has_primary_with_doubling(
        parts, InstrumentEnum.FLUTE, InstrumentEnum.PICCOLO, 2
    )
    assert _has_primary_with_doubling(
        parts, InstrumentEnum.OBOE, InstrumentEnum.ENGLISH_HORN, 2
    )

    string_primary = {
        InstrumentEnum.VIOLIN_1,
        InstrumentEnum.VIOLIN_2,
        InstrumentEnum.VIOLA,
        InstrumentEnum.CELLO,
        InstrumentEnum.DOUBLE_BASS,
    }
    for instrument_enum in string_primary:
        string_parts = _parts_for_primary_instrument(parts, instrument_enum)
        assert len(string_parts) == 1
        assert string_parts[0].number is None

    horn_asset = create_part_asset(
        piece_id=str(piece.id),
        filename="Firebird.Horn-1.pdf",
    )
    horn_numbers = _numbers_for_instrument(horn_asset.parts, InstrumentEnum.FRENCH_HORN)
    assert horn_numbers == {1}
    assert len(horn_asset.parts) == 1
