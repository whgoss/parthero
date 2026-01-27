from django.db.models import (
    CharField,
    DateTimeField,
    ForeignKey,
    IntegerField,
    CASCADE,
    SET_NULL,
)
from core.models.base import UUIDPrimaryKeyModel
from core.models.music import Piece, Part
from core.models.organizations import Organization, Musician
from core.enum.status import ProgramStatus


class Program(UUIDPrimaryKeyModel):
    title = CharField(max_length=255)
    status = CharField(
        max_length=50,
        default=ProgramStatus.DRAFT.value,
        choices=ProgramStatus.choices(),
    )
    organization = ForeignKey(Organization, on_delete=CASCADE)


class ProgramPiece(UUIDPrimaryKeyModel):
    program = ForeignKey(Program, related_name="pieces", on_delete=CASCADE)
    piece = ForeignKey(Piece, on_delete=CASCADE)
    concert_order = IntegerField()


class ProgramPartMusicianSlot(UUIDPrimaryKeyModel):
    part = ForeignKey(Part, on_delete=CASCADE)
    musician = ForeignKey(
        Musician, related_name="musicians", on_delete=SET_NULL, null=True
    )


class ProgramPerformance(UUIDPrimaryKeyModel):
    program = ForeignKey(Program, related_name="performances", on_delete=CASCADE)
    date = DateTimeField()
    timezone = CharField(default="America/New_York")


class ProgramRehearsal(UUIDPrimaryKeyModel):
    program = ForeignKey(Program, related_name="rehearsals", on_delete=CASCADE)
    date = DateTimeField()
    timezone = CharField(default="America/New_York")
