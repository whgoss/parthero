from django.db.models import CharField
from core.models.base import UUIDPrimaryKeyModel


class Organization(UUIDPrimaryKeyModel):
    name = CharField(max_length=255)

    def __str__(self):
        return f"{self.name}"
