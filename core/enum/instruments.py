from core.enum.base import BaseEnum


class InstrumentEnum(BaseEnum):
    ACCORDION = "Accordion"
    ALTO = "Alto"
    ALTO_SAXOPHONE = "Alto Saxophone"
    ALTO_FLUTE = "Alto Flute"
    ARPEGGIONE = "Arpeggione"
    BAGPIPE = "Bagpipe"
    BARITONE = "Baritone"
    BASS = "Bass"
    BASS_BARITONE = "Bass baritone"
    BASS_CLARINET = "Bass Clarinet"
    BASS_DRUM = "Bass Drum"
    BASS_FLUTE = "Bass Flute"
    BASS_GUITAR = "Bass Guitar"
    BASS_TROMBONE = "Bass Trombone"
    BANJO = "Banjo"
    BASSOON = "Bassoon"
    BASS_OBOE = "Bass oboe"
    BARYTON = "Baryton"
    BASSET_CLARINET = "Basset clarinet"
    BASSET_HORN = "Basset Horn"
    BELL = "Bell"
    BUGLE = "Bugle"
    CELLO = "Cello"
    CELESTA = "Celesta"
    CHILDRENS_CHORUS = "Children's chorus"
    CIMBALOM = "Cimbalom"
    CITTERN = "Cittern"
    CLARINET = "Clarinet"
    CLAVICHORD = "Clavichord"
    CHALUMEAU = "Chalumeau"
    CHILDS_VOICE = "Child's voice"
    CONCERTINA = "Concertina"
    CRUMHORN = "Crumhorn"
    CORNET = "Cornet"
    CORNETT = "Cornett"
    CONTRABASSOON = "Contrabassoon"
    CONTRABASS_CLARINET = "Contrabass clarinet"
    COUNTER_TENOR = "Counter-tenor"
    CYMBAL = "Cymbal"
    DOMRA = "Domra"
    DOUBLE_BASS = "Double Bass"
    DRUM_KIT = "Drum Kit"
    DULCIAN = "Dulcian"
    DULCIMER = "Dulcimer"
    ELECTRIC_GUITAR = "Electric Guitar"
    ELECTRONICA = "Electronica"
    ELECTRONIC_INSTRUMENTS = "Electronic Instruments"
    ELECTRIC_PIANO = "Electric piano"
    ENGLISH_HORN = "English Horn"
    ERHU = "Erhu"
    EUPHONIUM = "Euphonium"
    FEMALE_CHORUS = "Female chorus"
    FLUTE_DAMORE = "Flute d'amore"
    FLUGELHORN = "Flugelhorn"
    FIFE = "Fife"
    FLUTE = "Flute"
    FLAGEOLET = "Flageolet"
    FRENCH_HORN = "French Horn"
    GLASS_HARMONIC = "Glass harmonica"
    GLOCKENSPIEL = "Glockenspiel"
    GUITAR = "Guitar"
    HARP = "Harp"
    HARPSICHORD = "Harpsichord"
    HARMONIUM = "Harmonium"
    HARMONICA = "Harmonica"
    HECKELPHONE = "Heckelphone"
    LUTE = "Lute"
    LYRE = "Lyre"
    MANDOLIN = "Mandolin"
    MARIMBA = "Marimba"
    MALE_CHORUS = "Male chorus"
    MEZZO_SOPRANO = "Mezzo-soprano"
    MIXED_CHORUS = "Mixed chorus"
    MUSETTE = "Musette"
    NARRATOR = "Narrator"
    OBOE = "Oboe"
    OCARINA = "Ocarina"
    OBOE_DAMORE = "Oboe d'amore"
    ONDES_MARTENOT = "Ondes Martenot"
    OPHICLEIDE = "Ophicleide"
    ORGAN = "Organ"
    OUD = "Oud"
    PAN_FLUTE = "Pan flute"
    PEDAL_PIANO = "Pedal Piano"
    PERCUSSION = "Percussion"
    PIANO = "Piano"
    PICCOLO = "Piccolo"
    PICCOLO_TRUMPET = "Piccolo Trumpet"
    PIPA = "Pipa"
    REBEC = "Rebec"
    RECORDER = "Recorder"
    SACKBUT = "Sackbut"
    SARRUSOPHONE = "Sarrusophone"
    SAXHORN = "Saxhorn"
    SAXOPONE = "Saxophone"
    SERPENT = "Serpent"
    SHAWM = "Shawm"
    SHENG = "Sheng"
    SITAR = "Sitar"
    SLIDE_TRUMPET = "Slide Trumpet"
    SNARE_DRUM = "Snare Drum"
    SOPRANO = "Soprano"
    SOPRANO_SAXOPHONE = "Soprano Saxophone"
    SYNTHESIZER = "Synthesizer"
    TAM_TAM = "Tam-Tam"
    TENOR = "Tenor"
    TENOR_SAXOPHONE = "Tenor Saxophone"
    THEREMIN = "Theremin"
    TIMPANI = "Timpani"
    TOMS = "Toms"
    TROMBONE = "Trombone"
    TRIANGLE = "Triangle"
    TRUMPET = "Trumpet"
    TUBA = "Tuba"
    UKELELE = "Ukelele"
    VIBRAPHONE = "Vibraphone"
    VIELLE = "Vielle"
    VIOL = "Viol"
    VIOLA = "Viola"
    VIOLA_DAMORE = "Viola d'amore"
    VIOLA_POMPOSA = "Viola pomposa"
    VIOLIN_1 = "Violin 1"
    VIOLIN_2 = "Violin 2"
    VIOLONE = "Violone"
    VUVUZELA = "Vuvuzela"
    WAGNER_TUBA = "Wagner Tuba"
    XIAO = "Xiao"
    XYLOPHONE = "Xylophone"
    ZITHER = "Zither"


class InstrumentSectionEnum(BaseEnum):
    STRINGS = "Strings"
    BRASS = "Brass"
    WOODWINDS = "Woodwinds"
    PERCUSSION = "Percussion"
    HARP = "Harp"
    KEYBOARD = "Keyboard"
    VOCAL = "Vocal"
    OTHER = "Other"


INSTRUMENT_SECTIONS = {
    InstrumentSectionEnum.WOODWINDS: [
        InstrumentEnum.FLUTE,
        InstrumentEnum.PICCOLO,
        InstrumentEnum.OBOE,
        InstrumentEnum.ENGLISH_HORN,
        InstrumentEnum.CLARINET,
        InstrumentEnum.BASS_CLARINET,
        InstrumentEnum.CONTRABASS_CLARINET,
        InstrumentEnum.BASSOON,
        InstrumentEnum.CONTRABASSOON,
        InstrumentEnum.SOPRANO_SAXOPHONE,
        InstrumentEnum.ALTO_SAXOPHONE,
        InstrumentEnum.TENOR_SAXOPHONE,
    ],
    InstrumentSectionEnum.BRASS: [
        InstrumentEnum.FRENCH_HORN,
        InstrumentEnum.TRUMPET,
        InstrumentEnum.TROMBONE,
        InstrumentEnum.BASS_TROMBONE,
        InstrumentEnum.TUBA,
    ],
    InstrumentSectionEnum.PERCUSSION: [
        InstrumentEnum.BELL,
        InstrumentEnum.TIMPANI,
        InstrumentEnum.BASS_DRUM,
        InstrumentEnum.PERCUSSION,
        InstrumentEnum.DRUM_KIT,
        InstrumentEnum.SNARE_DRUM,
        InstrumentEnum.TAM_TAM,
        InstrumentEnum.TRIANGLE,
        InstrumentEnum.TOMS,
    ],
    InstrumentSectionEnum.HARP: [
        InstrumentEnum.HARP,
    ],
    InstrumentSectionEnum.KEYBOARD: [
        InstrumentEnum.PIANO,
        InstrumentEnum.CELESTA,
        InstrumentEnum.HARPSICHORD,
        InstrumentEnum.ORGAN,
        InstrumentEnum.PEDAL_PIANO,
    ],
    InstrumentSectionEnum.STRINGS: [
        InstrumentEnum.VIOLIN_1,
        InstrumentEnum.VIOLIN_2,
        InstrumentEnum.VIOLA,
        InstrumentEnum.CELLO,
        InstrumentEnum.DOUBLE_BASS,
    ],
    InstrumentSectionEnum.VOCAL: [
        InstrumentEnum.SOPRANO,
        InstrumentEnum.MEZZO_SOPRANO,
        InstrumentEnum.ALTO,
        InstrumentEnum.TENOR,
        InstrumentEnum.BARITONE,
        InstrumentEnum.BASS,
    ],
}


#
# Instrument relationships used for score/part presentation.
# Example: a standalone Piccolo 3 part should render as "Piccolo (Flute 3)".
#
INSTRUMENT_CHAIR_PARENTS = {
    InstrumentEnum.ALTO_FLUTE: InstrumentEnum.FLUTE,
    InstrumentEnum.BASS_FLUTE: InstrumentEnum.FLUTE,
    InstrumentEnum.PICCOLO: InstrumentEnum.FLUTE,
    InstrumentEnum.OBOE_DAMORE: InstrumentEnum.OBOE,
    InstrumentEnum.ENGLISH_HORN: InstrumentEnum.OBOE,
    InstrumentEnum.BASS_OBOE: InstrumentEnum.OBOE,
    InstrumentEnum.HECKELPHONE: InstrumentEnum.OBOE,
    InstrumentEnum.BASS_CLARINET: InstrumentEnum.CLARINET,
    InstrumentEnum.CONTRABASS_CLARINET: InstrumentEnum.CLARINET,
    InstrumentEnum.CONTRABASSOON: InstrumentEnum.BASSOON,
    InstrumentEnum.BASS_TROMBONE: InstrumentEnum.TROMBONE,
    InstrumentEnum.PICCOLO_TRUMPET: InstrumentEnum.TRUMPET,
}


#
# Principal assignment subsections.
# Key = "lead" instrument (principal ownership bucket).
# Value = instruments that principal can assign in that subsection.
#
INSTRUMENT_ASSIGNMENT_SUBSECTIONS = {
    InstrumentEnum.FLUTE: {
        InstrumentEnum.FLUTE,
        InstrumentEnum.PICCOLO,
        InstrumentEnum.ALTO_FLUTE,
        InstrumentEnum.BASS_FLUTE,
    },
    InstrumentEnum.OBOE: {
        InstrumentEnum.OBOE,
        InstrumentEnum.ENGLISH_HORN,
        InstrumentEnum.OBOE_DAMORE,
        InstrumentEnum.BASS_OBOE,
        InstrumentEnum.HECKELPHONE,
    },
    InstrumentEnum.CLARINET: {
        InstrumentEnum.CLARINET,
        InstrumentEnum.BASS_CLARINET,
        InstrumentEnum.CONTRABASS_CLARINET,
    },
    InstrumentEnum.BASSOON: {
        InstrumentEnum.BASSOON,
        InstrumentEnum.CONTRABASSOON,
    },
    InstrumentEnum.TRUMPET: {
        InstrumentEnum.TRUMPET,
        InstrumentEnum.PICCOLO_TRUMPET,
    },
    InstrumentEnum.FRENCH_HORN: {
        InstrumentEnum.FRENCH_HORN,
    },
    InstrumentEnum.TROMBONE: {
        InstrumentEnum.TROMBONE,
        InstrumentEnum.BASS_TROMBONE,
    },
    InstrumentEnum.TUBA: {
        InstrumentEnum.TUBA,
    },
    InstrumentEnum.PERCUSSION: set(
        INSTRUMENT_SECTIONS[InstrumentSectionEnum.PERCUSSION]
    ),
    InstrumentEnum.HARP: set(INSTRUMENT_SECTIONS[InstrumentSectionEnum.HARP]),
    InstrumentEnum.PIANO: set(INSTRUMENT_SECTIONS[InstrumentSectionEnum.KEYBOARD]),
}


INSTRUMENT_ASSIGNMENT_LEADS = {
    subsection_instrument: lead_instrument
    for lead_instrument, subsection in INSTRUMENT_ASSIGNMENT_SUBSECTIONS.items()
    for subsection_instrument in subsection
}


def get_chair_parent_instrument(instrument: InstrumentEnum) -> InstrumentEnum | None:
    return INSTRUMENT_CHAIR_PARENTS.get(instrument)


def get_assignment_lead_instrument(instrument: InstrumentEnum) -> InstrumentEnum:
    return INSTRUMENT_ASSIGNMENT_LEADS.get(instrument, instrument)


def get_assignment_subsection_instruments(
    instrument: InstrumentEnum,
) -> set[InstrumentEnum]:
    lead_instrument = get_assignment_lead_instrument(instrument)
    return set(INSTRUMENT_ASSIGNMENT_SUBSECTIONS.get(lead_instrument, set()))


def get_assignment_scope_for_instruments(
    instruments: set[InstrumentEnum],
) -> set[InstrumentEnum]:
    scope: set[InstrumentEnum] = set()
    for instrument in instruments:
        scope.update(get_assignment_subsection_instruments(instrument))
    return scope
