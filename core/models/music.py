from django.db.models import CharField, DurationField, ForeignKey, CASCADE
from core.models.base import UUIDPrimaryKeyModel
from core.models.musicians import Section
from core.models.organizations import Organization


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
