from django.db.models import (
    CharField,
    BooleanField,
    OneToOneField,
    DateTimeField,
    ForeignKey,
    IntegerField,
    UniqueConstraint,
    CASCADE,
    SET_NULL,
)
from core.models.base import UUIDPrimaryKeyModel
from core.models.music import Piece, Part, Instrument
from core.models.organizations import Organization, Musician
from core.models.users import User


class Program(UUIDPrimaryKeyModel):
    name = CharField(max_length=255)
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
    principal = BooleanField(default=False)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["program", "musician"], name="unique_program_musician"
            )
        ]


class ProgramMusicianInstrument(UUIDPrimaryKeyModel):
    program_musician = ForeignKey(
        ProgramMusician, related_name="instruments", on_delete=CASCADE
    )
    instrument = ForeignKey(Instrument, on_delete=CASCADE)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["program_musician", "instrument"],
                name="unique_program_musician_instrument",
            )
        ]


class ProgramPartMusician(UUIDPrimaryKeyModel):
    program = ForeignKey(Program, on_delete=CASCADE, null=True, blank=True)
    part = ForeignKey(Part, on_delete=CASCADE)
    musician = ForeignKey(Musician, on_delete=CASCADE)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["program", "part"], name="unique_program_part_assignment"
            )
        ]


class ProgramPerformance(UUIDPrimaryKeyModel):
    program = ForeignKey(Program, related_name="performances", on_delete=CASCADE)
    date = DateTimeField()
    timezone = CharField(default="America/New_York")


class ProgramRehearsal(UUIDPrimaryKeyModel):
    program = ForeignKey(Program, related_name="rehearsals", on_delete=CASCADE)
    date = DateTimeField()
    timezone = CharField(default="America/New_York")


class ProgramChecklist(UUIDPrimaryKeyModel):
    program = OneToOneField(Program, related_name="checklist", on_delete=CASCADE)
    pieces_completed_on = DateTimeField(null=True, blank=True)
    pieces_completed_by = ForeignKey(
        User, related_name="+", null=True, blank=True, on_delete=SET_NULL
    )
    roster_completed_on = DateTimeField(null=True, blank=True)
    roster_completed_by = ForeignKey(
        User, related_name="+", null=True, blank=True, on_delete=SET_NULL
    )
    overrides_completed_on = DateTimeField(null=True, blank=True)
    overrides_completed_by = ForeignKey(
        User, related_name="+", null=True, blank=True, on_delete=SET_NULL
    )
    bowings_completed_on = DateTimeField(null=True, blank=True)
    bowings_completed_by = ForeignKey(
        User, related_name="+", null=True, blank=True, on_delete=SET_NULL
    )
    assignments_sent_on = DateTimeField(null=True, blank=True)
    assignments_sent_by = ForeignKey(
        User, related_name="+", null=True, blank=True, on_delete=SET_NULL
    )
    assignments_completed_on = DateTimeField(null=True, blank=True)
    assignments_completed_by = ForeignKey(
        User, related_name="+", null=True, blank=True, on_delete=SET_NULL
    )
    delivery_sent_on = DateTimeField(null=True, blank=True)
    delivery_sent_by = ForeignKey(
        User, related_name="+", null=True, blank=True, on_delete=SET_NULL
    )
    delivery_completed_on = DateTimeField(null=True, blank=True)
