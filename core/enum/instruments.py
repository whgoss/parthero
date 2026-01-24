from enum import Enum


# This really represents an instrument or instrument section (Harp v. Violin 1)
# But we're calling it an instrument for simplicity
class InstrumentEnum(Enum):
    HARP = "Harp"
    VIOLIN_1 = "Violin 1"
    VIOLIN_2 = "Violin 2"
    VIOLA = "Viola"
    CELLO = "Cello"
    DOUBLE_BASS = "Double Bass"
    PIANO = "Piano"
    CELESTA = "Celesta"
    ORGAN = "Organ"
    SYNTH = "Synth"
    TIMPANI = "Timpani"
    BASS_DRUM = "Bass Drum"
    PERCUSSION = "Percussion"
    DRUM_KIT = "Drum Kit"
    TRUMPET = "Trumpet"
    HORN = "Horn"
    TROMBONE = "Trombone"
    BASS_TROMBONE = "Bass Trombone"
    TUBA = "Tuba"
    FLUTE = "Flute"
    PICCOLO = "Piccolo"
    OBOE = "Oboe"
    ENGLISH_HORN = "English Horn"
    CLARINET = "Clarinet"
    BASS_CLARINET = "Bass Clarinet"
    BASSOON = "Bassoon"
    CONTRABASSOON = "Contrabassoon"
    SOPRANO_SAXOPHONE = "Soprano Saxophone"
    ALTO_SAXOPHONE = "Alto Saxophone"
    TENOR_SAXOPHONE = "Tenor Saxophone"
    SOPRANO = "Soprano"
    ALTO = "Alto"
    TENOR = "Tenor"
    BASS = "Bass"
    GUITAR = "Guitar"
    ELECTRIC_GUITAR = "Electric Guitar"
    BASS_GUITAR = "Bass Guitar"
    ELECTRONICA = "Electronica"

    def choices():
        return [(instrument.value, instrument.value) for instrument in InstrumentEnum]

    def values():
        return [instrument.value for instrument in InstrumentEnum]


class InstrumentFamily(Enum):
    STRINGS = "Strings"
    BRASS = "Brass"
    WOODWINDS = "Woodwinds"
    PERCUSSION = "Percussion"
    AUXILIARY = "Auxiliary"
    VOICE = "Voice"
    OTHER = "Other"


INSTRUMENT_FAMILIES = {
    InstrumentFamily.WOODWINDS: [
        InstrumentEnum.FLUTE,
        InstrumentEnum.PICCOLO,
        InstrumentEnum.OBOE,
        InstrumentEnum.ENGLISH_HORN,
        InstrumentEnum.CLARINET,
        InstrumentEnum.BASS_CLARINET,
        InstrumentEnum.BASSOON,
        InstrumentEnum.CONTRABASSOON,
        InstrumentEnum.SOPRANO_SAXOPHONE,
        InstrumentEnum.ALTO_SAXOPHONE,
        InstrumentEnum.TENOR_SAXOPHONE,
    ],
    InstrumentFamily.BRASS: [
        InstrumentEnum.HORN,
        InstrumentEnum.TRUMPET,
        InstrumentEnum.TROMBONE,
        InstrumentEnum.BASS_TROMBONE,
        InstrumentEnum.TUBA,
    ],
    InstrumentFamily.PERCUSSION: [
        InstrumentEnum.TIMPANI,
        InstrumentEnum.BASS_DRUM,
        InstrumentEnum.PERCUSSION,
        InstrumentEnum.DRUM_KIT,
        InstrumentEnum.TUBA,
    ],
    InstrumentFamily.AUXILIARY: [
        InstrumentEnum.HARP,
        InstrumentEnum.PIANO,
        InstrumentEnum.CELESTA,
        InstrumentEnum.GUITAR,
        InstrumentEnum.ELECTRIC_GUITAR,
        InstrumentEnum.BASS_GUITAR,
        InstrumentEnum.ELECTRONICA,
    ],
    InstrumentFamily.STRINGS: [
        InstrumentEnum.VIOLIN_1,
        InstrumentEnum.VIOLIN_2,
        InstrumentEnum.VIOLA,
        InstrumentEnum.CELLO,
        InstrumentEnum.DOUBLE_BASS,
    ],
    InstrumentFamily.VOICE: [
        InstrumentEnum.SOPRANO,
        InstrumentEnum.ALTO,
        InstrumentEnum.TENOR,
        InstrumentEnum.BASS,
    ],
}


def get_instrument_family(
    instrument_section: InstrumentEnum,
) -> InstrumentFamily:
    instrument_family = None
    if instrument_section in INSTRUMENT_FAMILIES[InstrumentFamily.WOODWINDS]:
        instrument_family = InstrumentFamily.WOODWINDS
    elif instrument_section in INSTRUMENT_FAMILIES[InstrumentFamily.BRASS]:
        instrument_family = InstrumentFamily.BRASS
    elif instrument_section in INSTRUMENT_FAMILIES[InstrumentFamily.PERCUSSION]:
        instrument_family = InstrumentFamily.PERCUSSION
    elif instrument_section in INSTRUMENT_FAMILIES[InstrumentFamily.AUXILIARY]:
        instrument_family = InstrumentFamily.AUXILIARY
    elif instrument_section in INSTRUMENT_FAMILIES[InstrumentFamily.STRINGS]:
        instrument_family = InstrumentFamily.STRINGS
    elif instrument_section in INSTRUMENT_FAMILIES[InstrumentFamily.VOICE]:
        instrument_family = InstrumentFamily.VOICE
    else:
        instrument_family = InstrumentFamily.OTHER

    return instrument_family
