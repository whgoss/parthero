from django.db.models import (
    CharField,
    DateTimeField,
    ForeignKey,
    TextField,
    IntegerField,
    BooleanField,
    CASCADE,
    SET_NULL,
)
from core.models.base import UUIDPrimaryKeyModel
from core.models.music import Piece, Instrument
from core.models.organizations import Musician


class Program(UUIDPrimaryKeyModel):
    name = CharField(max_length=255)
    date = DateTimeField()


class ProgramMusician(UUIDPrimaryKeyModel):
    instrument = ForeignKey(Instrument, on_delete=CASCADE)
    chair_number = IntegerField()


class ProgramPiece(UUIDPrimaryKeyModel):
    program = ForeignKey(Program, on_delete=CASCADE)
    piece = ForeignKey(Piece, on_delete=CASCADE)
    instrumentation_override = TextField(null=True, blank=True)


class ProgramPieceSlot(UUIDPrimaryKeyModel):
    program_piece = ForeignKey(ProgramPiece, on_delete=CASCADE)
    musician = ForeignKey(Musician, on_delete=SET_NULL, null=True, blank=True)


class ProgramPieceSlotInstrument(UUIDPrimaryKeyModel):
    program_piece_slot = ForeignKey(
        ProgramPieceSlot, related_name="instruments", on_delete=CASCADE
    )
    instrument = ForeignKey(Instrument, on_delete=CASCADE)
    chair_number = IntegerField()
    principal = BooleanField(default=False)
    musician = ForeignKey(Musician, on_delete=SET_NULL, null=True, blank=True)
