from django.db.models import (
    CharField,
    DateTimeField,
    ForeignKey,
    IntegerField,
    CASCADE,
)
from core.models.base import UUIDPrimaryKeyModel
from core.models.music import Piece, Part, Instrument
from core.models.organizations import Organization, Musician
from core.enum.status import ProgramStatus


class Program(UUIDPrimaryKeyModel):
    name = CharField(max_length=255)
    status = CharField(
        max_length=255,
        default=ProgramStatus.CREATED.value,
        choices=ProgramStatus.choices(),
    )
    organization = ForeignKey(Organization, on_delete=CASCADE)

    def __str__(self):
        return f"{self.name}"


class ProgramPiece(UUIDPrimaryKeyModel):
    program = ForeignKey(Program, related_name="pieces", on_delete=CASCADE)
    piece = ForeignKey(Piece, on_delete=CASCADE)
    concert_order = IntegerField(null=True, blank=True)


class ProgramMusician(UUIDPrimaryKeyModel):
    program = ForeignKey(Program, related_name="musicians", on_delete=CASCADE)
    musician = ForeignKey(Musician, on_delete=CASCADE)


class ProgramMusicianInstrument(UUIDPrimaryKeyModel):
    program_musician = ForeignKey(
        ProgramMusician, related_name="instruments", on_delete=CASCADE
    )
    instrument = ForeignKey(Instrument, on_delete=CASCADE)


class ProgramPartMusician(UUIDPrimaryKeyModel):
    part = ForeignKey(Part, on_delete=CASCADE)
    musician = ForeignKey(Musician, on_delete=CASCADE)


class ProgramPerformance(UUIDPrimaryKeyModel):
    program = ForeignKey(Program, related_name="performances", on_delete=CASCADE)
    date = DateTimeField()
    timezone = CharField(default="America/New_York")


class ProgramRehearsal(UUIDPrimaryKeyModel):
    program = ForeignKey(Program, related_name="rehearsals", on_delete=CASCADE)
    date = DateTimeField()
    timezone = CharField(default="America/New_York")
