from django.db.models import (
    CharField,
    ForeignKey,
    TextField,
    IntegerField,
    ManyToManyField,
    UniqueConstraint,
    BooleanField,
    CASCADE,
)
from core.models.base import UUIDPrimaryKeyModel
from core.models.organizations import Musician, Organization
from core.enum.music import PartAssetType
from core.enum.status import UploadStatus


class Instrument(UUIDPrimaryKeyModel):
    name = CharField(max_length=255)

    def __str__(self):
        return f"{self.name}"


class InstrumentSection(UUIDPrimaryKeyModel):
    name = CharField(max_length=255)

    def __str__(self):
        return f"{self.name}"


class MusicianInstrument(UUIDPrimaryKeyModel):
    musician = ForeignKey(Musician, related_name="instruments", on_delete=CASCADE)
    instrument = ForeignKey(Instrument, on_delete=CASCADE)


class Piece(UUIDPrimaryKeyModel):
    title = CharField(max_length=255)
    composer = CharField(max_length=255)
    domo_id = CharField(null=True, blank=True)
    composer_domo_id = CharField(null=True, blank=True)
    instrumentation = TextField()
    duration = IntegerField(null=True)
    organization = ForeignKey(Organization, on_delete=CASCADE)

    def __str__(self):
        return f"{self.title} by {self.composer}"


class Part(UUIDPrimaryKeyModel):
    piece = ForeignKey(Piece, related_name="parts", on_delete=CASCADE)
    number = IntegerField(null=True)


class PartAsset(UUIDPrimaryKeyModel):
    parts = ManyToManyField(Part, related_name="assets", blank=True)
    piece = ForeignKey(Piece, related_name="assets", on_delete=CASCADE)
    upload_url = CharField(max_length=511, null=True, blank=True)
    upload_filename = CharField(max_length=255, null=True, blank=True)
    file_key = CharField(max_length=255, null=True, blank=True)
    asset_type = CharField(
        max_length=255,
        default=PartAssetType.CLEAN.value,
        choices=PartAssetType.choices(),
    )
    status = CharField(
        max_length=255,
        default=UploadStatus.NONE.value,
        choices=UploadStatus.choices(),
    )


class PartInstrument(UUIDPrimaryKeyModel):
    part = ForeignKey(Part, related_name="instruments", on_delete=CASCADE)
    primary = BooleanField(default=False)
    instrument = ForeignKey(Instrument, on_delete=CASCADE, null=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["part", "instrument"], name="unique_part_instrument"
            )
        ]
