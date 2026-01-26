from django.db.models import (
    CharField,
    BooleanField,
    ForeignKey,
    DateTimeField,
    CASCADE,
)
from core.models.base import UUIDPrimaryKeyModel
from core.enum.status import ProgramStatus


class Organization(UUIDPrimaryKeyModel):
    name = CharField(max_length=255)
    enabled = BooleanField(default=True)

    def __str__(self):
        return f"{self.name}"


class Musician(UUIDPrimaryKeyModel):
    first_name = CharField(max_length=255)
    last_name = CharField(max_length=255)
    email = CharField(max_length=255)
    principal = BooleanField(default=False)
    core_member = BooleanField(default=False)
    phone_number = CharField(max_length=20, blank=True, null=True)
    address = CharField(max_length=255, blank=True, null=True)
    organization = ForeignKey(Organization, on_delete=CASCADE)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Program(UUIDPrimaryKeyModel):
    first_name = CharField(max_length=255)
    status = CharField(
        max_length=50,
        default=ProgramStatus.DRAFT.value,
        choices=ProgramStatus.choices(),
    )
    organization = ForeignKey(Organization, on_delete=CASCADE)


class ProgramPerformances(UUIDPrimaryKeyModel):
    program = ForeignKey(Program, related_name="performances", on_delete=CASCADE)
    date = DateTimeField()


class ProgramRehearsals(UUIDPrimaryKeyModel):
    program = ForeignKey(Program, related_name="rehearsals", on_delete=CASCADE)
    date = DateTimeField()
