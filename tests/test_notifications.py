import pytest

from core.enum.instruments import InstrumentEnum
from core.enum.notifications import NotificationType
from core.models.music import Instrument, Part, PartInstrument, Piece
from core.models.notifications import Notification
from core.models.programs import ProgramPiece, ProgramPartMusician
from core.services.notifications import send_assignment_email, send_part_delivery_email
from core.services.organizations import create_musician
from core.services.programs import add_musician_to_program, create_program
from tests.mocks import create_organization

pytestmark = pytest.mark.django_db


def _create_part(piece_id: str, instrument: InstrumentEnum) -> str:
    part = Part.objects.create(piece_id=piece_id)
    instrument_model = Instrument.objects.get(name=instrument.value)
    PartInstrument.objects.create(
        part=part,
        instrument=instrument_model,
        primary=True,
    )
    return str(part.id)


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
    piece = Piece.objects.create(
        organization_id=organization.id,
        title="Notify Piece",
        composer="Composer",
        instrumentation="",
        duration=None,
    )
    ProgramPiece.objects.create(program_id=program.id, piece_id=piece.id)
    _create_part(str(piece.id), InstrumentEnum.TRUMPET)

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


def test_send_assignment_email_skips_principal_without_assignable_parts(monkeypatch):
    organization = create_organization()
    program = create_program(
        organization_id=str(organization.id),
        name="No Assignable Parts",
        performance_dates=[],
    )
    principal = create_musician(
        organization_id=str(organization.id),
        first_name="Eddie",
        last_name="Euphonium",
        email="eddie-euphonium@example.com",
        principal=True,
        core_member=True,
        instruments=[InstrumentEnum.EUPHONIUM],
    )
    add_musician_to_program(
        organization_id=str(organization.id),
        program_id=str(program.id),
        musician_id=str(principal.id),
    )
    piece = Piece.objects.create(
        organization_id=organization.id,
        title="No Euphonium",
        composer="Composer",
        instrumentation="",
        duration=None,
    )
    ProgramPiece.objects.create(program_id=program.id, piece_id=piece.id)
    _create_part(str(piece.id), InstrumentEnum.TROMBONE)

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

    notifications = Notification.objects.filter(
        program_id=program.id,
        recipient_id=principal.id,
        type=NotificationType.ASSIGNMENT.value,
    )
    assert notifications.count() == 0
    assert sends["count"] == 0


def test_send_part_delivery_email_deduplicates_by_notification_type(monkeypatch):
    organization = create_organization()
    program = create_program(
        organization_id=str(organization.id),
        name="Delivery Program",
        performance_dates=[],
    )
    musician = create_musician(
        organization_id=str(organization.id),
        first_name="Del",
        last_name="Ivery",
        email="delivery@example.com",
        principal=False,
        core_member=True,
        instruments=[InstrumentEnum.TRUMPET],
    )
    piece = Piece.objects.create(
        organization_id=organization.id,
        title="Notify Piece",
        composer="Composer",
        instrumentation="",
        duration=None,
    )
    add_musician_to_program(
        organization_id=str(organization.id),
        program_id=str(program.id),
        musician_id=str(musician.id),
    )
    ProgramPiece.objects.create(program_id=program.id, piece_id=piece.id)
    part_id = _create_part(str(piece.id), InstrumentEnum.TRUMPET)
    ProgramPartMusician.objects.create(
        program_id=program.id,
        part_id=part_id,
        musician_id=musician.id,
    )

    sends = {"count": 0}

    def _mock_send(_self):
        sends["count"] += 1
        return 1

    monkeypatch.setattr(
        "core.services.notifications.EmailMultiAlternatives.send",
        _mock_send,
    )

    send_part_delivery_email(
        organization_id=str(organization.id),
        program_id=str(program.id),
        musician_id=str(musician.id),
    )
    send_part_delivery_email(
        organization_id=str(organization.id),
        program_id=str(program.id),
        musician_id=str(musician.id),
    )

    notifications = Notification.objects.filter(
        program_id=program.id,
        recipient_id=musician.id,
        type=NotificationType.PART_DELIVERY.value,
    )
    assert notifications.count() == 1
    assert notifications.first().type == NotificationType.PART_DELIVERY.value
    assert sends["count"] == 1
