from enum import Enum


class InstrumentSectionEnum(Enum):
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
    FRENCH_HORN = "French Horn"
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
        return [
            (instrument.value, instrument.value) for instrument in InstrumentSectionEnum
        ]

    def values():
        return [instrument.value for instrument in InstrumentSectionEnum]


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
        InstrumentSectionEnum.FLUTE,
        InstrumentSectionEnum.PICCOLO,
        InstrumentSectionEnum.OBOE,
        InstrumentSectionEnum.ENGLISH_HORN,
        InstrumentSectionEnum.CLARINET,
        InstrumentSectionEnum.BASS_CLARINET,
        InstrumentSectionEnum.BASSOON,
        InstrumentSectionEnum.CONTRABASSOON,
        InstrumentSectionEnum.SOPRANO_SAXOPHONE,
        InstrumentSectionEnum.ALTO_SAXOPHONE,
        InstrumentSectionEnum.TENOR_SAXOPHONE,
    ],
    InstrumentFamily.BRASS: [
        InstrumentSectionEnum.FRENCH_HORN,
        InstrumentSectionEnum.TRUMPET,
        InstrumentSectionEnum.TROMBONE,
        InstrumentSectionEnum.BASS_TROMBONE,
        InstrumentSectionEnum.TUBA,
    ],
    InstrumentFamily.PERCUSSION: [
        InstrumentSectionEnum.TIMPANI,
        InstrumentSectionEnum.BASS_DRUM,
        InstrumentSectionEnum.PERCUSSION,
        InstrumentSectionEnum.DRUM_KIT,
        InstrumentSectionEnum.TUBA,
    ],
    InstrumentFamily.AUXILIARY: [
        InstrumentSectionEnum.HARP,
        InstrumentSectionEnum.PIANO,
        InstrumentSectionEnum.CELESTA,
        InstrumentSectionEnum.GUITAR,
        InstrumentSectionEnum.ELECTRIC_GUITAR,
        InstrumentSectionEnum.BASS_GUITAR,
        InstrumentSectionEnum.ELECTRONICA,
    ],
    InstrumentFamily.STRINGS: [
        InstrumentSectionEnum.VIOLIN_1,
        InstrumentSectionEnum.VIOLIN_2,
        InstrumentSectionEnum.VIOLA,
        InstrumentSectionEnum.CELLO,
        InstrumentSectionEnum.DOUBLE_BASS,
    ],
    InstrumentFamily.VOICE: [
        InstrumentSectionEnum.SOPRANO,
        InstrumentSectionEnum.ALTO,
        InstrumentSectionEnum.TENOR,
        InstrumentSectionEnum.BASS,
    ],
}


def get_instrument_family(
    instrument_section: InstrumentSectionEnum,
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
