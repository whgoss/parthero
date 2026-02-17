import pytest

from core.enum.instruments import InstrumentEnum
from core.enum.notifications import NotificationType
from core.models.notifications import Notification
from core.services.notifications import send_assignment_email
from core.services.organizations import create_musician
from core.services.programs import add_musician_to_program, create_program
from tests.mocks import create_organization

pytestmark = pytest.mark.django_db


def test_send_assignment_email_deduplicates_by_notification_type(monkeypatch):
    organization = create_organization()
    program = create_program(
        organization_id=str(organization.id),
        name="Notify Program",
        performance_dates=[],
    )
    principal = create_musician(
        organization_id=str(organization.id),
        first_name="Nora",
        last_name="Principal",
        email="nora-principal@example.com",
        principal=True,
        core_member=True,
        instruments=[InstrumentEnum.TRUMPET],
    )
    add_musician_to_program(
        organization_id=str(organization.id),
        program_id=str(program.id),
        musician_id=str(principal.id),
    )

    sends = {"count": 0}

    def _mock_send(_self):
        sends["count"] += 1
        return 1

    monkeypatch.setattr(
        "core.services.notifications.EmailMultiAlternatives.send",
        _mock_send,
    )

    send_assignment_email(
        organization_id=str(organization.id),
        program_id=str(program.id),
        musician_id=str(principal.id),
    )
    send_assignment_email(
        organization_id=str(organization.id),
        program_id=str(program.id),
        musician_id=str(principal.id),
    )

    notifications = Notification.objects.filter(
        program_id=program.id,
        recipient_id=principal.id,
        type=NotificationType.ASSIGNMENT.value,
    )

    assert notifications.count() == 1
    assert notifications.first().type == NotificationType.ASSIGNMENT.value
    assert sends["count"] == 1
