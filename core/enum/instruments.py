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
    AUXILIARY = "Auxiliary"
    VOICE = "Voice"
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
    InstrumentSectionEnum.AUXILIARY: [
        InstrumentEnum.HARP,
        InstrumentEnum.PIANO,
        InstrumentEnum.CELESTA,
        InstrumentEnum.GUITAR,
        InstrumentEnum.ELECTRIC_GUITAR,
        InstrumentEnum.BASS_GUITAR,
        InstrumentEnum.ELECTRONICA,
    ],
    InstrumentSectionEnum.STRINGS: [
        InstrumentEnum.VIOLIN_1,
        InstrumentEnum.VIOLIN_2,
        InstrumentEnum.VIOLA,
        InstrumentEnum.CELLO,
        InstrumentEnum.DOUBLE_BASS,
    ],
    InstrumentSectionEnum.VOICE: [
        InstrumentEnum.SOPRANO,
        InstrumentEnum.MEZZO_SOPRANO,
        InstrumentEnum.ALTO,
        InstrumentEnum.TENOR,
        InstrumentEnum.BARITONE,
        InstrumentEnum.BASS,
    ],
}


INSTRUMENT_PRIMARIES = {
    InstrumentEnum.PICCOLO: InstrumentEnum.FLUTE,
    InstrumentEnum.ENGLISH_HORN: InstrumentEnum.OBOE,
    InstrumentEnum.BASS_CLARINET: InstrumentEnum.CLARINET,
    InstrumentEnum.CONTRABASS_CLARINET: InstrumentEnum.CLARINET,
    InstrumentEnum.CONTRABASSOON: InstrumentEnum.BASSOON,
}
