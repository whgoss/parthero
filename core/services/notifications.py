from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from core.dtos.queue import EmailQueuePayloadDTO
from core.enum.instruments import (
    INSTRUMENT_SECTIONS,
    InstrumentEnum,
    InstrumentSectionEnum,
)
from core.enum.notifications import (
    MagicLinkType,
    NotificationMethod,
    NotificationStatus,
    NotificationType,
)
from core.models.notifications import Notification
from core.models.organizations import Musician
from core.models.programs import Program, ProgramMusician, ProgramPartMusician
from core.services.assignments import (
    auto_assign_harp_keyboard_principal_parts_if_unambiguous,
    get_assignment_payload,
)
from core.services.magic_links import create_magic_link, get_magic_link_url
from core.services.programs import get_pieces_for_program
from core.services.queue import enqueue_email_payload


def _is_string_principal(program_musician: ProgramMusician) -> bool:
    """Return True when a principal only belongs to the strings section.

    String principals are excluded from principal assignment emails in the
    current workflow.
    """
    string_instruments = set(INSTRUMENT_SECTIONS[InstrumentSectionEnum.STRINGS])
    musician_instruments = {
        InstrumentEnum(instrument.instrument.name)
        for instrument in program_musician.instruments.all()
    }
    return bool(musician_instruments) and musician_instruments.issubset(
        string_instruments
    )


def send_part_assignment_emails(organization_id: str, program_id: str):
    """Queue assignment notifications for principals who actually need to assign.

    Skips:
    - string principals
    - principals auto-assigned by unambiguous harp/keyboard rules
    - principals with no assignable parts in scope
    """
    principals = (
        ProgramMusician.objects.filter(
            program_id=program_id,
            musician__organization_id=organization_id,
            musician__principal=True,
        )
        .select_related("musician")
        .prefetch_related("instruments__instrument")
    )

    for principal in principals:
        if _is_string_principal(principal):
            continue
        if auto_assign_harp_keyboard_principal_parts_if_unambiguous(
            program_id=program_id,
            principal_musician_id=str(principal.musician.id),
        ):
            continue
        assignment_payload = get_assignment_payload(
            program_id=program_id,
            principal_musician_id=str(principal.musician.id),
        )
        if not assignment_payload.pieces:
            continue
        payload = EmailQueuePayloadDTO(
            organization_id=organization_id,
            program_id=program_id,
            musician_id=str(principal.musician.id),
            notification_type=NotificationType.ASSIGNMENT,
        )
        enqueue_email_payload(payload)


def send_part_delivery_emails(organization_id: str, program_id: str):
    """Queue delivery notifications for every musician on the program roster."""
    roster_musicians = ProgramMusician.objects.filter(
        program_id=program_id,
        musician__organization_id=organization_id,
    ).select_related("musician")

    for program_musician in roster_musicians:
        payload = EmailQueuePayloadDTO(
            organization_id=organization_id,
            program_id=program_id,
            musician_id=str(program_musician.musician_id),
            notification_type=NotificationType.PART_DELIVERY,
        )
        enqueue_email_payload(payload)


def send_assignment_email(
    organization_id: str, program_id: str, musician_id: str
) -> None:
    """Render and send one principal assignment email with magic link.

    A Notification row is persisted before send; status transitions to SENT/FAILED.
    Duplicate ASSIGNMENT notifications for the same program+musician are ignored.
    """
    program = (
        Program.objects.filter(id=program_id, organization_id=organization_id)
        .prefetch_related("organization")
        .first()
    )
    if not program:
        return None

    musician = Musician.objects.get(id=musician_id, organization_id=organization_id)
    program_musician = (
        ProgramMusician.objects.filter(
            program_id=program_id,
            musician_id=musician_id,
            musician__organization_id=organization_id,
        )
        .select_related("musician")
        .prefetch_related("instruments__instrument")
        .first()
    )

    # String principals don't need to assign parts
    if _is_string_principal(program_musician):
        return None

    # Must be assigned to the program and a principal
    if not program_musician or not program_musician.musician.principal:
        return None

    assignment_payload = get_assignment_payload(
        program_id=program_id,
        principal_musician_id=musician_id,
    )
    if not assignment_payload.pieces:
        return None

    # Dedupe on (program, recipient, type) so queue retries are safe
    notification = Notification.objects.filter(
        program_id=program_id,
        recipient_id=musician_id,
        type=NotificationType.ASSIGNMENT.value,
    ).first()
    if notification:
        return None

    # Create the magic link
    magic_link = create_magic_link(
        program_id=program_id,
        musician_id=musician_id,
        link_type=MagicLinkType.ASSIGNMENT,
    )

    # Create the email context and send the email
    pieces = get_pieces_for_program(
        organization_id=organization_id,
        program_id=program_id,
    )

    context = {
        "organization": program.organization,
        "musician": musician,
        "program": program,
        "pieces": pieces,
        "url": get_magic_link_url(magic_link.token, link_type=MagicLinkType.ASSIGNMENT),
    }
    subject = f"Assign Parts for {program.name}"
    text_body = render_to_string("emails/assignment.txt", context)
    html_body = render_to_string("emails/assignment.html", context)
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        to=[musician.email],
    )
    msg.attach_alternative(html_body, "text/html")

    notification = Notification(
        created=timezone.now(),
        method=NotificationMethod.EMAIL.value,
        type=NotificationType.ASSIGNMENT.value,
        program=program,
        status=NotificationStatus.CREATED.value,
        recipient_email=musician.email,
        recipient_first_name=musician.first_name,
        recipient_last_name=musician.last_name,
        recipient=musician,
        magic_link=magic_link,
        subject=subject,
        body=text_body,
        body_html=html_body,
    )
    notification.save()

    try:
        success = msg.send()
    except Exception:
        success = False

    if success:
        notification.status = NotificationStatus.SENT.value
        notification.save(update_fields=["status"])
    else:
        notification.status = NotificationStatus.FAILED.value
        notification.save(update_fields=["status"])


def send_part_delivery_email(
    organization_id: str,
    program_id: str,
    musician_id: str,
) -> None:
    """Render and send one part-delivery email with delivery magic link.

    Only roster musicians are eligible. Duplicate PART_DELIVERY notifications
    for the same program+musician are ignored.
    """
    program = (
        Program.objects.filter(id=program_id, organization_id=organization_id)
        .prefetch_related("organization")
        .first()
    )
    if not program:
        return None

    # Ensure the musician is on the roster and has parts assigned
    musician = Musician.objects.get(id=musician_id, organization_id=organization_id)
    is_on_program_roster = ProgramMusician.objects.filter(
        program_id=program_id,
        musician_id=musician_id,
        musician__organization_id=organization_id,
    ).exists()
    if not is_on_program_roster:
        return None
    has_parts_on_program = ProgramPartMusician.objects.filter(
        program_id=program_id, musician_id=musician_id
    ).exists()
    if not has_parts_on_program:
        return None

    # Dedupe on (program, recipient, type) so queue retries are safe
    notification = Notification.objects.filter(
        program_id=program_id,
        recipient_id=musician_id,
        type=NotificationType.PART_DELIVERY.value,
    ).first()

    if notification:
        return None

    # Create the magic link
    magic_link = create_magic_link(
        program_id=program_id,
        musician_id=musician_id,
        link_type=MagicLinkType.DELIVERY,
    )

    # Create the template context and send the email
    pieces = get_pieces_for_program(
        organization_id=organization_id,
        program_id=program_id,
    )
    context = {
        "organization": program.organization,
        "musician": musician,
        "program": program,
        "pieces": pieces,
        "url": get_magic_link_url(magic_link.token, link_type=MagicLinkType.DELIVERY),
    }
    subject = f"Parts Ready for {program.name}"
    text_body = render_to_string("emails/delivery.txt", context)
    html_body = render_to_string("emails/delivery.html", context)
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        to=[musician.email],
    )
    msg.attach_alternative(html_body, "text/html")

    notification = Notification(
        created=timezone.now(),
        method=NotificationMethod.EMAIL.value,
        type=NotificationType.PART_DELIVERY.value,
        program=program,
        status=NotificationStatus.CREATED.value,
        recipient_email=musician.email,
        recipient_first_name=musician.first_name,
        recipient_last_name=musician.last_name,
        recipient=musician,
        magic_link=magic_link,
        subject=subject,
        body=text_body,
        body_html=html_body,
    )
    notification.save()

    try:
        success = msg.send()
    except Exception:
        success = False

    if success:
        notification.status = NotificationStatus.SENT.value
        notification.save(update_fields=["status"])
    else:
        notification.status = NotificationStatus.FAILED.value
        notification.save(update_fields=["status"])


def send_notification_email(
    *,
    organization_id: str,
    program_id: str,
    musician_id: str,
    notification_type: NotificationType,
) -> None:
    """Dispatch a queued notification payload to the type-specific sender."""
    if notification_type == NotificationType.ASSIGNMENT:
        send_assignment_email(
            organization_id=organization_id,
            program_id=program_id,
            musician_id=musician_id,
        )
        return None

    if notification_type == NotificationType.PART_DELIVERY:
        send_part_delivery_email(
            organization_id=organization_id,
            program_id=program_id,
            musician_id=musician_id,
        )
        return None

    raise ValueError(f"Unsupported notification type: {notification_type}")
