import pytest

from core.enum.notifications import NotificationType
from core.enum.instruments import InstrumentEnum
from core.models.music import Instrument, Part, PartInstrument, Piece
from core.models.programs import ProgramPartMusician, ProgramPiece
from core.services.notifications import (
    send_notification_email,
    send_part_assignment_emails,
)
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


def test_send_part_assignment_emails_enqueues_principals_only(monkeypatch):
    organization = create_organization()
    program = create_program(
        organization_id=str(organization.id),
        name="Queue Program",
        performance_dates=[],
    )
    principal = create_musician(
        organization_id=str(organization.id),
        first_name="Pat",
        last_name="Principal",
        email="principal-queue@example.com",
        principal=True,
        core_member=True,
        instruments=[InstrumentEnum.TRUMPET],
    )
    string_principal = create_musician(
        organization_id=str(organization.id),
        first_name="Vi",
        last_name="Principal",
        email="violin-principal-queue@example.com",
        principal=True,
        core_member=True,
        instruments=[InstrumentEnum.VIOLIN_1],
    )
    section = create_musician(
        organization_id=str(organization.id),
        first_name="Sam",
        last_name="Section",
        email="section-queue@example.com",
        principal=False,
        core_member=True,
        instruments=[InstrumentEnum.TRUMPET],
    )

    add_musician_to_program(
        organization_id=str(organization.id),
        program_id=str(program.id),
        musician_id=str(principal.id),
    )
    add_musician_to_program(
        organization_id=str(organization.id),
        program_id=str(program.id),
        musician_id=str(string_principal.id),
    )
    add_musician_to_program(
        organization_id=str(organization.id),
        program_id=str(program.id),
        musician_id=str(section.id),
    )
    piece = Piece.objects.create(
        organization_id=organization.id,
        title="Queue Piece",
        composer="Composer",
        instrumentation="",
        duration=None,
    )
    ProgramPiece.objects.create(program_id=program.id, piece_id=piece.id)
    _create_part(str(piece.id), InstrumentEnum.TRUMPET)

    payloads = []

    def _enqueue_email_payload(payload):
        payloads.append(payload)
        return "msg-1"

    monkeypatch.setattr(
        "core.services.notifications.enqueue_email_payload",
        _enqueue_email_payload,
    )

    send_part_assignment_emails(
        organization_id=str(organization.id),
        program_id=str(program.id),
    )

    assert [payload.model_dump() for payload in payloads] == [
        {
            "organization_id": str(organization.id),
            "program_id": str(program.id),
            "musician_id": str(principal.id),
            "notification_type": NotificationType.ASSIGNMENT,
        },
    ]


def test_send_part_assignment_emails_skips_principals_without_assignable_parts(
    monkeypatch,
):
    organization = create_organization()
    program = create_program(
        organization_id=str(organization.id),
        name="No Assignable Parts Program",
        performance_dates=[],
    )
    principal_euphonium = create_musician(
        organization_id=str(organization.id),
        first_name="Eddie",
        last_name="Euphonium",
        email="euphonium-principal@example.com",
        principal=True,
        core_member=True,
        instruments=[InstrumentEnum.EUPHONIUM],
    )
    add_musician_to_program(
        organization_id=str(organization.id),
        program_id=str(program.id),
        musician_id=str(principal_euphonium.id),
    )

    piece = Piece.objects.create(
        organization_id=organization.id,
        title="Brass Piece",
        composer="Composer",
        instrumentation="",
        duration=None,
    )
    ProgramPiece.objects.create(program_id=program.id, piece_id=piece.id)
    _create_part(str(piece.id), InstrumentEnum.TROMBONE)

    payloads = []

    def _enqueue_email_payload(payload):
        payloads.append(payload)
        return "msg-1"

    monkeypatch.setattr(
        "core.services.notifications.enqueue_email_payload",
        _enqueue_email_payload,
    )

    send_part_assignment_emails(
        organization_id=str(organization.id),
        program_id=str(program.id),
    )

    assert payloads == []


def test_auto_assigns_unambiguous_harp_without_enqueue(monkeypatch):
    """Auto-assignment should bypass principal email when there is no decision to make."""
    organization = create_organization()
    program = create_program(
        organization_id=str(organization.id),
        name="Auxiliary Auto Assign Program",
        performance_dates=[],
    )
    principal_harp = create_musician(
        organization_id=str(organization.id),
        first_name="Hannah",
        last_name="Harp",
        email="harp-principal@example.com",
        principal=True,
        core_member=True,
        instruments=[InstrumentEnum.HARP],
    )
    add_musician_to_program(
        organization_id=str(organization.id),
        program_id=str(program.id),
        musician_id=str(principal_harp.id),
    )
    piece = Piece.objects.create(
        organization_id=organization.id,
        title="Harp Piece",
        composer="Composer",
        instrumentation="",
        duration=None,
    )
    ProgramPiece.objects.create(program_id=program.id, piece_id=piece.id)
    part_id = _create_part(str(piece.id), InstrumentEnum.HARP)

    payloads = []

    def _enqueue_email_payload(payload):
        payloads.append(payload)
        return "msg-1"

    monkeypatch.setattr(
        "core.services.notifications.enqueue_email_payload",
        _enqueue_email_payload,
    )

    send_part_assignment_emails(
        organization_id=str(organization.id),
        program_id=str(program.id),
    )

    assignment = ProgramPartMusician.objects.filter(
        program_id=program.id,
        part_id=part_id,
    ).first()
    assert assignment is not None
    assert str(assignment.musician_id) == str(principal_harp.id)
    assert payloads == []


def test_enqueues_harp_principal_when_assignment_is_ambiguous(monkeypatch):
    """When any piece has multiple in-scope parts, principal assignment email should be sent."""
    organization = create_organization()
    program = create_program(
        organization_id=str(organization.id),
        name="Auxiliary Ambiguous Program",
        performance_dates=[],
    )
    principal_harp = create_musician(
        organization_id=str(organization.id),
        first_name="Hannah",
        last_name="Harp",
        email="harp-principal@example.com",
        principal=True,
        core_member=True,
        instruments=[InstrumentEnum.HARP],
    )
    add_musician_to_program(
        organization_id=str(organization.id),
        program_id=str(program.id),
        musician_id=str(principal_harp.id),
    )
    piece = Piece.objects.create(
        organization_id=organization.id,
        title="Double Harp Piece",
        composer="Composer",
        instrumentation="",
        duration=None,
    )
    ProgramPiece.objects.create(program_id=program.id, piece_id=piece.id)
    part_1 = _create_part(str(piece.id), InstrumentEnum.HARP)
    part_2 = _create_part(str(piece.id), InstrumentEnum.HARP)

    payloads = []

    def _enqueue_email_payload(payload):
        payloads.append(payload)
        return "msg-1"

    monkeypatch.setattr(
        "core.services.notifications.enqueue_email_payload",
        _enqueue_email_payload,
    )

    send_part_assignment_emails(
        organization_id=str(organization.id),
        program_id=str(program.id),
    )

    assert [payload.model_dump() for payload in payloads] == [
        {
            "organization_id": str(organization.id),
            "program_id": str(program.id),
            "musician_id": str(principal_harp.id),
            "notification_type": NotificationType.ASSIGNMENT,
        },
    ]
    assignments = ProgramPartMusician.objects.filter(
        program_id=program.id,
        part_id__in=[part_1, part_2],
    )
    assert assignments.count() == 0


def test_send_notification_email_dispatches_assignment(monkeypatch):
    calls = []

    def _send_assignment_email(organization_id: str, program_id: str, musician_id: str):
        calls.append((organization_id, program_id, musician_id))

    monkeypatch.setattr(
        "core.services.notifications.send_assignment_email",
        _send_assignment_email,
    )

    send_notification_email(
        organization_id="org-1",
        program_id="program-1",
        musician_id="musician-1",
        notification_type=NotificationType.ASSIGNMENT,
    )

    assert calls == [("org-1", "program-1", "musician-1")]


def test_send_notification_email_dispatches_part_delivery(monkeypatch):
    calls = []

    def _send_part_delivery_email(
        organization_id: str, program_id: str, musician_id: str
    ):
        calls.append((organization_id, program_id, musician_id))

    monkeypatch.setattr(
        "core.services.notifications.send_part_delivery_email",
        _send_part_delivery_email,
    )

    send_notification_email(
        organization_id="org-1",
        program_id="program-1",
        musician_id="musician-1",
        notification_type=NotificationType.PART_DELIVERY,
    )

    assert calls == [("org-1", "program-1", "musician-1")]
