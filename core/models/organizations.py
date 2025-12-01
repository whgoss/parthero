from django.db.models import (
    CharField,
    BooleanField,
    ForeignKey,
    UniqueConstraint,
    IntegerField,
    CASCADE,
)
from core.models.base import UUIDPrimaryKeyModel
from core.enum.instruments import Instrument, InstrumentFamily


class Organization(UUIDPrimaryKeyModel):
    name = CharField(max_length=255)
    enabled = BooleanField(default=True)

    def __str__(self):
        return f"{self.name}"


class Musician(UUIDPrimaryKeyModel):
    first_name = CharField(max_length=255)
    last_name = CharField(max_length=255)
    email = CharField(max_length=255)
    phone_number = CharField(max_length=20, blank=True, null=True)
    address = CharField(max_length=255, blank=True, null=True)
    organization = ForeignKey(Organization, on_delete=CASCADE)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Section(UUIDPrimaryKeyModel):
    instrument = CharField(max_length=255, choices=Instrument.choices())
    family = CharField(max_length=255, choices=InstrumentFamily.choices())
    number = IntegerField(null=True)
    organization = ForeignKey(Organization, on_delete=CASCADE)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["instrument", "family", "number", "organization"],
                name="unique_instrument_section_per_organization",
            ),
        ]

    def __str__(self):
        return f"{self.instrument} {self.number} ({self.family})"


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
