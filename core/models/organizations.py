from django.db.models import (
    CharField,
    BooleanField,
    ForeignKey,
    CASCADE,
)
from core.models.base import UUIDPrimaryKeyModel


class Organization(UUIDPrimaryKeyModel):
    name = CharField(max_length=255)
    enabled = BooleanField(default=True)

    def __str__(self):
        return f"{self.name}"


class Musician(UUIDPrimaryKeyModel):
    first_name = CharField(max_length=255)
    last_name = CharField(max_length=255)
    email = CharField(max_length=255)
    core_member = BooleanField(default=True)
    phone_number = CharField(max_length=20, blank=True, null=True)
    address = CharField(max_length=255, blank=True, null=True)
    organization = ForeignKey(Organization, on_delete=CASCADE)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
