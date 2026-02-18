from datetime import timedelta

from django.utils import timezone

from core.enum.notifications import MagicLinkType
from core.models.notifications import MagicLink
from core.models.programs import Program, ProgramPerformance
from parthero.settings import (
    DEBUG,
    MAGIC_LINK_DEFAULT_EXPIRATION_DAYS,
)


def get_magic_link_expiration(
    program_id: str, link_type: MagicLinkType = MagicLinkType.ASSIGNMENT
):
    """Return expiration datetime for a program-scoped magic link.

    Policy:
    - If the program has performances, use the latest performance date.
    - Otherwise, fall back to the configured default window.
    """
    latest_performance = (
        ProgramPerformance.objects.filter(program_id=program_id)
        .order_by("-date")
        .first()
    )
    if latest_performance:
        return latest_performance.date
    if link_type == MagicLinkType.DELIVERY:
        return timezone.now() + timedelta(days=MAGIC_LINK_DEFAULT_EXPIRATION_DAYS)
    return timezone.now() + timedelta(days=MAGIC_LINK_DEFAULT_EXPIRATION_DAYS)


def create_magic_link(
    program_id: str,
    musician_id: str,
    link_type: MagicLinkType = MagicLinkType.ASSIGNMENT,
) -> MagicLink:
    """Create a magic link token tied to one program, musician, and link type."""
    Program.objects.get(id=program_id)
    expires_on = get_magic_link_expiration(program_id, link_type=link_type)
    return MagicLink.objects.create(
        program_id=program_id,
        musician_id=musician_id,
        type=link_type.value,
        expires_on=expires_on,
    )


def get_valid_magic_link(token: str, link_type: MagicLinkType) -> MagicLink:
    """Fetch an active magic link by token/type and enforce not revoked/expired."""
    magic_link = MagicLink.objects.get(
        token=token,
        type=link_type.value,
        revoked=False,
    )
    if magic_link.expires_on <= timezone.now() or magic_link.revoked:
        raise MagicLink.DoesNotExist
    return magic_link


def mark_magic_link_accessed(magic_link: MagicLink) -> MagicLink:
    """Stamp last access time for analytics/status visibility."""
    magic_link.last_accessed_on = timezone.now()
    magic_link.save(update_fields=["last_accessed_on"])
    return magic_link


def mark_magic_link_completed(magic_link: MagicLink) -> MagicLink:
    """Stamp completion time for flows that include an explicit confirm action."""
    magic_link.completed_on = timezone.now()
    magic_link.save(update_fields=["completed_on"])
    return magic_link


def get_magic_link_url(
    token: str, link_type: MagicLinkType = MagicLinkType.ASSIGNMENT
) -> str:
    """Build absolute UI URL for assignment or delivery magic-link landing page."""
    base = "http://localhost:8000" if DEBUG else "https://app.parthero.net"
    if link_type == MagicLinkType.DELIVERY:
        return f"{base}/magic/{token}/delivery/"
    return f"{base}/magic/{token}/assignments/"
