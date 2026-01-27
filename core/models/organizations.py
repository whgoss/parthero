from django.db.models import (
    CharField,
    BooleanField,
    ForeignKey,
    CASCADE,
    Index,
)
from core.models.base import UUIDPrimaryKeyModel


class Organization(UUIDPrimaryKeyModel):
    name = CharField(max_length=255)
    timezone = CharField(default="America/New_York")
    enabled = BooleanField(default=True)

    def __str__(self):
        return f"{self.name}"


class Musician(UUIDPrimaryKeyModel):
    organization = ForeignKey(Organization, on_delete=CASCADE)
    first_name = CharField(max_length=255)
    last_name = CharField(max_length=255)
    email = CharField(max_length=255)
    principal = BooleanField(default=False)
    core_member = BooleanField(default=False)
    phone_number = CharField(max_length=20, blank=True, null=True)
    address = CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        indexes = [
            Index(
                fields=["organization", "last_name"],
            ),
            Index(fields=["organization", "email"]),
            Index(
                fields=["organization", "principal"],
            ),
            Index(
                fields=["organization", "core_member"],
            ),
        ]
