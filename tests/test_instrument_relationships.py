from core.enum.instruments import (
    InstrumentEnum,
    get_assignment_scope_for_instruments,
    get_assignment_subsection_instruments,
    get_chair_parent_instrument,
)


def test_get_chair_parent_instrument_for_piccolo():
    assert get_chair_parent_instrument(InstrumentEnum.PICCOLO) == InstrumentEnum.FLUTE


def test_get_chair_parent_instrument_for_primary_is_none():
    assert get_chair_parent_instrument(InstrumentEnum.FLUTE) is None


def test_get_assignment_subsection_instruments_for_flute_family():
    assert get_assignment_subsection_instruments(InstrumentEnum.PICCOLO) == {
        InstrumentEnum.FLUTE,
        InstrumentEnum.PICCOLO,
        InstrumentEnum.ALTO_FLUTE,
        InstrumentEnum.BASS_FLUTE,
    }


def test_get_assignment_subsection_instruments_for_percussion_family():
    subsection = get_assignment_subsection_instruments(InstrumentEnum.TIMPANI)
    assert InstrumentEnum.PERCUSSION in subsection
    assert InstrumentEnum.TIMPANI in subsection
    assert InstrumentEnum.SNARE_DRUM in subsection


def test_get_assignment_subsection_instruments_for_unmapped_instrument():
    assert get_assignment_subsection_instruments(InstrumentEnum.EUPHONIUM) == set()


def test_get_assignment_scope_for_instruments_unions_subsections():
    assert get_assignment_scope_for_instruments(
        {InstrumentEnum.FLUTE, InstrumentEnum.OBOE}
    ) == {
        InstrumentEnum.FLUTE,
        InstrumentEnum.PICCOLO,
        InstrumentEnum.ALTO_FLUTE,
        InstrumentEnum.BASS_FLUTE,
        InstrumentEnum.OBOE,
        InstrumentEnum.ENGLISH_HORN,
        InstrumentEnum.OBOE_DAMORE,
        InstrumentEnum.BASS_OBOE,
        InstrumentEnum.HECKELPHONE,
    }
