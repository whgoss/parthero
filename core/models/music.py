from django.db.models import (
    CharField,
    DurationField,
    ForeignKey,
    TextField,
    IntegerField,
    CASCADE,
)
from core.models.base import UUIDPrimaryKeyModel
from core.models.organizations import Musician, Organization
from core.enum.status import UploadStatus


class InstrumentSection(UUIDPrimaryKeyModel):
    name = CharField(max_length=255)

    def __str__(self):
        return f"{self.name}"


class MusicianInstrument(UUIDPrimaryKeyModel):
    musician = ForeignKey(
        Musician, related_name="instrument_sections", on_delete=CASCADE
    )
    instrument_section = ForeignKey(InstrumentSection, on_delete=CASCADE)


class Piece(UUIDPrimaryKeyModel):
    title = CharField(max_length=255)
    composer = CharField(max_length=255)
    arranger = CharField(max_length=255, blank=True, null=True)
    duration = DurationField(blank=True, null=True)
    organization = ForeignKey(Organization, on_delete=CASCADE)

    def __str__(self):
        return f"{self.title} by {self.composer}"


class Edition(UUIDPrimaryKeyModel):
    name = CharField(max_length=255, default="Standard")
    piece = ForeignKey(Piece, on_delete=CASCADE)
    instrumentation = TextField()

    def __str__(self):
        return f"{self.name} Edition"


class Part(UUIDPrimaryKeyModel):
    edition = ForeignKey(Edition, related_name="editions", on_delete=CASCADE)
    status = CharField(
        max_length=50,
        default=UploadStatus.PENDING.value,
        choices=UploadStatus.choices(),
    )
    upload_url = CharField(max_length=511, null=True)
    upload_filename = CharField(max_length=255, null=True)
    file_key = CharField(max_length=255, null=True)


class PartInstrument(UUIDPrimaryKeyModel):
    part = ForeignKey(Part, related_name="part_instruments", on_delete=CASCADE)
    instrument_section = ForeignKey(InstrumentSection, on_delete=CASCADE)
    chair_number = IntegerField()
