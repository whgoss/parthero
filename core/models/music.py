from django.db.models import (
    CharField,
    DurationField,
    ForeignKey,
    CASCADE,
)
from core.models.base import UUIDPrimaryKeyModel
from core.models.organizations import Organization, Section
from core.enum.status import UploadStatus


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
    status = CharField(
        max_length=50,
        default=UploadStatus.PENDING.value,
        choices=UploadStatus.choices(),
    )
    section = ForeignKey(Section, on_delete=CASCADE, null=True)
    upload_url = CharField(max_length=511, null=True)
    upload_filename = CharField(max_length=255, null=True)
    file_key = CharField(max_length=255, null=True)

    def __str__(self):
        return f"{self.piece.title} ({self.section})"
