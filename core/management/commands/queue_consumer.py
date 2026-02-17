import logging
import time

from django.core.management.base import BaseCommand
from pydantic import ValidationError

from core.services.notifications import send_notification_email
from core.services.queue import (
    delete_email_message,
    parse_email_payload,
    receive_email_messages,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Consume email queue messages and send notification emails."

    def add_arguments(self, parser):
        parser.add_argument(
            "--wait-time",
            type=int,
            default=20,
            help="SQS long-poll wait time in seconds.",
        )
        parser.add_argument(
            "--max-number",
            type=int,
            default=10,
            help="Maximum number of SQS messages per poll.",
        )
        parser.add_argument(
            "--sleep",
            type=float,
            default=0.0,
            help="Optional sleep between empty polls.",
        )

    def handle(self, *args, **options):
        wait_time = options["wait_time"]
        max_number = options["max_number"]
        sleep_seconds = options["sleep"]

        self.stdout.write(self.style.SUCCESS("Starting email queue consumer..."))

        while True:
            try:
                messages = receive_email_messages(
                    max_number=max_number,
                    wait_time=wait_time,
                )
            except Exception:
                logger.exception("Failed to poll SQS queue")
                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)
                continue

            if not messages:
                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)
                continue

            for message in messages:
                receipt_handle = message.get("ReceiptHandle")
                raw_body = message.get("Body", "{}")

                try:
                    payload = parse_email_payload(raw_body)
                    send_notification_email(
                        organization_id=payload.organization_id,
                        program_id=payload.program_id,
                        musician_id=payload.musician_id,
                        notification_type=payload.notification_type,
                    )
                    if receipt_handle:
                        delete_email_message(receipt_handle)
                except (ValueError, ValidationError):
                    logger.exception("Invalid email payload: %s", raw_body)
                    if receipt_handle:
                        delete_email_message(receipt_handle)
                except Exception:
                    logger.exception("Failed to process email message")
