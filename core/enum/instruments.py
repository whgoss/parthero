from enum import Enum


class InstrumentFamily(Enum):
    STRING = "String"
    PERCUSSION = "Percussion"
    BRASS = "Brass"
    WIND = "Wind"
    VOCAL = "Vocal"

    def choices():
        return [(family.value, family.value) for family in InstrumentFamily]


class Instrument(Enum):
    HARP = "Harp"
    VIOLIN = "Violin"
    VIOLA = "Viola"
    CELLO = "Cello"
    BASS = "Bass"
    PIANO = "Piano"
    TIMPANI = "Timpani"
    BASS_DRUM = "Bass Drum"
    SNARE_DRUM = "Snare Drum"
    PERCUSSION = "Percussion"
    TRUMPET = "Trumpet"
    FRENCH_HORN = "French Horn"
    TROMBONE = "Trombone"
    TUBA = "Tuba"
    FLUTE = "Flute"
    OBOE = "Oboe"
    CLARINET = "Clarinet"
    BASSOON = "Bassoon"
    SAXOPHONE = "Saxophone"
    SOPRANO = "Soprano"
    ALTO = "Alto"
    TENOR = "Tenor"

    def choices():
        return [(instrument.value, instrument.value) for instrument in Instrument]
