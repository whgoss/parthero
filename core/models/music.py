from django.db.models import (
    CharField,
    DurationField,
    ForeignKey,
    BooleanField,
    IntegerField,
    UniqueConstraint,
    CASCADE,
)
from core.models.base import UUIDPrimaryKeyModel
from core.models.organizations import Organization
from core.enum.instruments import Instrument, InstrumentFamily


class Instrument(UUIDPrimaryKeyModel):
    name = CharField(max_length=255, choices=Instrument.choices())
    family = CharField(max_length=255, choices=InstrumentFamily.choices())

    def __str__(self):
        return f"{self.name} ({self.family})"


class Section(UUIDPrimaryKeyModel):
    instrument = ForeignKey(Instrument, on_delete=CASCADE)
    number = IntegerField(null=True)
    organization = ForeignKey(Organization, on_delete=CASCADE)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["instrument", "number", "organization"],
                name="unique_instrument_section_per_organization",
            ),
        ]

    def __str__(self):
        return f"{self.name}"


class Piece(UUIDPrimaryKeyModel):
    title = CharField(max_length=255)
    composer = CharField(max_length=255)
    arranger = CharField(max_length=255, blank=True, null=True)
    duration = DurationField(blank=True, null=True)
    organization = ForeignKey(Organization, on_delete=CASCADE)

    def __str__(self):
        return f"{self.title} by {self.composer}"


class Part(UUIDPrimaryKeyModel):
    piece = ForeignKey(Piece, on_delete=CASCADE)
    section = ForeignKey(Section, on_delete=CASCADE)
    file = CharField(max_length=255)

    def __str__(self):
        return f"{self.piece.title} ({self.section})"


class Musician(UUIDPrimaryKeyModel):
    first_name = CharField(max_length=255)
    last_name = CharField(max_length=255)
    email = CharField(max_length=255)
    phone_number = CharField(max_length=20, blank=True, null=True)
    address = CharField(max_length=255, blank=True, null=True)
    organization = ForeignKey(Organization, on_delete=CASCADE)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class MusicianSection(UUIDPrimaryKeyModel):
    musician = ForeignKey(Musician, on_delete=CASCADE)
    section = ForeignKey(Section, on_delete=CASCADE)
    principal = BooleanField(default=False)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["musician", "section"],
                name="unique_musician_section",
            ),
        ]

    def __str__(self):
        return f"{self.musician} ({self.section})"
