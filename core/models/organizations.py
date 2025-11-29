from django.db.models import CharField, BooleanField
from core.models.base import UUIDPrimaryKeyModel


class Organization(UUIDPrimaryKeyModel):
    name = CharField(max_length=255)
    enabled = BooleanField(default=True)

    def __str__(self):
        return f"{self.name}"
