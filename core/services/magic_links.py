from datetime import timedelta

from django.utils import timezone

from core.enum.notifications import MagicLinkType
from core.models.notifications import MagicLink
from core.models.programs import Program, ProgramPerformance
from parthero.settings import DEBUG


def get_magic_link_expiration(program_id: str):
    latest_performance = (
        ProgramPerformance.objects.filter(program_id=program_id)
        .order_by("-date")
        .first()
    )
    if latest_performance:
        return latest_performance.date
    return timezone.now() + timedelta(days=90)


def create_magic_link(
    program_id: str,
    musician_id: str,
    link_type: MagicLinkType = MagicLinkType.ASSIGNMENT,
) -> MagicLink:
    Program.objects.get(id=program_id)
    expires_on = get_magic_link_expiration(program_id)
    return MagicLink.objects.create(
        program_id=program_id,
        musician_id=musician_id,
        type=link_type.value,
        expires_on=expires_on,
    )


def get_valid_magic_link(token: str, link_type: MagicLinkType) -> MagicLink:
    magic_link = MagicLink.objects.get(
        token=token,
        type=link_type.value,
        revoked=False,
    )
    if magic_link.expires_on <= timezone.now() or magic_link.revoked:
        raise MagicLink.DoesNotExist
    return magic_link


def mark_magic_link_accessed(magic_link: MagicLink) -> MagicLink:
    magic_link.last_accessed_on = timezone.now()
    magic_link.save(update_fields=["last_accessed_on"])
    return magic_link


def mark_magic_link_completed(magic_link: MagicLink) -> MagicLink:
    magic_link.completed_on = timezone.now()
    magic_link.save(update_fields=["completed_on"])
    return magic_link


def get_magic_link_url(token: str) -> str:
    base = "http://localhost:8000" if DEBUG else "https://app.parthero.net"
    return f"{base}/magic/{token}/assignments/"
