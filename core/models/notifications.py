import secrets

from django.utils import timezone
from django.db.models import (
    BooleanField,
    CharField,
    DateTimeField,
    SET_NULL,
    ForeignKey,
    TextField,
)
from core.enum.notifications import (
    MagicLinkType,
    NotificationMethod,
    NotificationStatus,
    NotificationType,
)
from core.models.base import UUIDPrimaryKeyModel
from core.models.programs import Program
from core.models.organizations import Musician


def generate_magic_link_token():
    return secrets.token_urlsafe(32)


class MagicLink(UUIDPrimaryKeyModel):
    created = DateTimeField(default=timezone.now)
    token = CharField(max_length=255, unique=True, default=generate_magic_link_token)
    type = CharField(
        max_length=255,
        default=MagicLinkType.ASSIGNMENT.value,
        choices=MagicLinkType.choices(),
    )
    program = ForeignKey(Program, null=True, blank=True, on_delete=SET_NULL)
    musician = ForeignKey(Musician, null=True, blank=True, on_delete=SET_NULL)
    expires_on = DateTimeField()
    revoked = BooleanField(default=False)
    last_accessed_on = DateTimeField(null=True, blank=True)
    completed_on = DateTimeField(null=True, blank=True)


class Notification(UUIDPrimaryKeyModel):
    created = DateTimeField(null=True, blank=True)
    method = CharField(
        max_length=255,
        default=NotificationMethod.EMAIL.value,
        choices=NotificationMethod.choices(),
    )
    type = CharField(
        max_length=255,
        choices=NotificationType.choices(),
    )
    program = ForeignKey(Program, null=True, blank=True, on_delete=SET_NULL)
    status = CharField(
        max_length=255,
        default=NotificationStatus.CREATED.value,
        choices=NotificationStatus.choices(),
    )
    recipient_email = CharField(max_length=255)
    recipient_first_name = CharField(max_length=255)
    recipient_last_name = CharField(max_length=255)
    recipient = ForeignKey(Musician, null=True, blank=True, on_delete=SET_NULL)
    magic_link = ForeignKey(MagicLink, null=True, blank=True, on_delete=SET_NULL)
    subject = CharField(max_length=255)
    body = TextField()
    body_html = TextField()
