from enum import Enum


class InstrumentEnum(Enum):
    HARP = "Harp"
    VIOLIN_1 = "Violin 1"
    VIOLIN_2 = "Violin 2"
    VIOLA = "Viola"
    CELLO = "Cello"
    DOUBLE_BASS = "Double Bass"
    PIANO = "Piano"
    ORGAN = "Organ"
    SYNTH = "Synth"
    TIMPANI = "Timpani"
    BASS_DRUM = "Bass Drum"
    PERCUSSION = "Percussion"
    DRUM_KIT = "Drum Kit"
    TRUMPET = "Trumpet"
    FRENCH_HORN = "French Horn"
    TROMBONE = "Trombone"
    TUBA = "Tuba"
    FLUTE = "Flute"
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

    def choices():
        return [(instrument.value, instrument.value) for instrument in InstrumentEnum]

    def values():
        return [instrument.value for instrument in InstrumentEnum]
