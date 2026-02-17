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
from core.models.programs import Program, ProgramMusician
from core.services.magic_links import create_magic_link, get_magic_link_url
from core.services.programs import get_pieces_for_program
from core.services.queue import enqueue_email_payload


def _is_string_principal(program_musician: ProgramMusician) -> bool:
    string_instruments = set(INSTRUMENT_SECTIONS[InstrumentSectionEnum.STRINGS])
    musician_instruments = {
        InstrumentEnum(instrument.instrument.name)
        for instrument in program_musician.instruments.all()
    }
    return bool(musician_instruments) and musician_instruments.issubset(
        string_instruments
    )


def send_part_assignment_emails(organization_id: str, program_id: str):
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
        payload = EmailQueuePayloadDTO(
            organization_id=organization_id,
            program_id=program_id,
            musician_id=str(principal.musician.id),
            notification_type=NotificationType.ASSIGNMENT,
        )
        enqueue_email_payload(payload)


def send_assignment_email(
    organization_id: str, program_id: str, musician_id: str
) -> None:
    program = Program.objects.get(id=program_id, organization_id=organization_id)
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

    # Only principals can assign parts
    if not program_musician or not program_musician.musician.principal:
        return None
    if _is_string_principal(program_musician):
        return None

    # Has a notification already been sent for this musician on this program?
    notification = Notification.objects.filter(
        program_id=program_id,
        recipient_id=musician_id,
        type=NotificationType.ASSIGNMENT.value,
    ).first()
    if notification:
        return None

    magic_link = create_magic_link(
        program_id=program_id,
        musician_id=musician_id,
        link_type=MagicLinkType.ASSIGNMENT,
    )

    pieces = get_pieces_for_program(
        organization_id=organization_id,
        program_id=program_id,
    )

    context = {
        "musician": musician,
        "program": program,
        "pieces": pieces,
        "url": get_magic_link_url(magic_link.token),
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
    # Reserved for part-delivery email implementation.
    return None


def send_notification_email(
    *,
    organization_id: str,
    program_id: str,
    musician_id: str,
    notification_type: NotificationType,
) -> None:
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
