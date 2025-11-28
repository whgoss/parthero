import uuid
from django.contrib.auth.models import AbstractUser
from django.db.models import ForeignKey, CharField, CASCADE, UUIDField
from core.models.base import UUIDPrimaryKeyModel
from core.models.organizations import Organization


class User(AbstractUser):
    id = UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    # Optional: any PartHero-specific fields later
    # e.g. preferred_instrument, etc.
    pass


class UserOrganization(UUIDPrimaryKeyModel):
    user = ForeignKey(User, on_delete=CASCADE)
    organization = ForeignKey(Organization, on_delete=CASCADE)
    role = CharField(max_length=100, default="Member")

    def __str__(self):
        return f"{self.user.username} - {self.organization.name} ({self.role})"
