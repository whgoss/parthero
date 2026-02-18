from datetime import timedelta

import pytest
from django.utils import timezone

from core.enum.notifications import MagicLinkType
from core.models.notifications import MagicLink
from core.models.programs import ProgramPerformance
from core.services.magic_links import (
    create_magic_link,
    get_magic_link_expiration,
    get_valid_magic_link,
)
from core.services.organizations import create_musician
from core.services.programs import create_program
from tests.mocks import create_organization

pytestmark = pytest.mark.django_db


def _create_program_and_musician():
    organization = create_organization()
    program = create_program(
        organization_id=str(organization.id),
        name="Magic Link Program",
        performance_dates=[],
    )
    musician = create_musician(
        organization_id=str(organization.id),
        first_name="Taylor",
        last_name="Principal",
        email=f"principal-{timezone.now().timestamp()}@example.com",
        principal=True,
        core_member=True,
        instruments=[],
    )
    return organization, program, musician


def test_magic_link_expiration_defaults_to_90_days_without_performances():
    _, program, _ = _create_program_and_musician()

    expires_on = get_magic_link_expiration(program_id=str(program.id))
    delta = expires_on - timezone.now()
    assert timedelta(days=89) <= delta <= timedelta(days=91)


def test_magic_link_expiration_uses_latest_program_performance():
    _, program, _ = _create_program_and_musician()
    expected = timezone.now() + timedelta(days=30)
    ProgramPerformance.objects.create(program_id=program.id, date=expected)

    expires_on = get_magic_link_expiration(program_id=str(program.id))
    assert abs((expires_on - expected).total_seconds()) < 1


def test_get_valid_magic_link_rejects_expired_links():
    _, program, musician = _create_program_and_musician()
    magic_link = create_magic_link(
        program_id=str(program.id),
        musician_id=str(musician.id),
        link_type=MagicLinkType.ASSIGNMENT,
    )
    MagicLink.objects.filter(id=magic_link.id).update(
        expires_on=timezone.now() - timedelta(minutes=1)
    )

    with pytest.raises(MagicLink.DoesNotExist):
        get_valid_magic_link(token=magic_link.token, link_type=MagicLinkType.ASSIGNMENT)


def test_get_valid_magic_link_rejects_revoked_links():
    _, program, musician = _create_program_and_musician()
    magic_link = create_magic_link(
        program_id=str(program.id),
        musician_id=str(musician.id),
        link_type=MagicLinkType.ASSIGNMENT,
    )
    MagicLink.objects.filter(id=magic_link.id).update(revoked=True)

    with pytest.raises(MagicLink.DoesNotExist):
        get_valid_magic_link(token=magic_link.token, link_type=MagicLinkType.ASSIGNMENT)
