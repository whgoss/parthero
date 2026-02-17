import logging

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from core.dtos.queue import EmailQueuePayloadDTO

from parthero.settings import (
    DEBUG,
    EMAIL_QUEUE_NAME,
    EMAIL_QUEUE_URL,
)

logger = logging.getLogger(__name__)
_sqs_client = None
_queue_url = None


def get_sqs_client():
    global _sqs_client
    if _sqs_client is None:
        if DEBUG:
            _sqs_client = boto3.client(
                "sqs",
                endpoint_url="http://localhost:4566",
                aws_access_key_id="test",
                aws_secret_access_key="test",
                region_name="us-east-1",
                config=Config(retries={"max_attempts": 3}),
            )
        else:
            _sqs_client = boto3.client("sqs")
    return _sqs_client


def get_email_queue_url() -> str:
    global _queue_url
    if _queue_url:
        return _queue_url
    if EMAIL_QUEUE_URL:
        _queue_url = EMAIL_QUEUE_URL
        return _queue_url

    client = get_sqs_client()
    try:
        response = client.get_queue_url(QueueName=EMAIL_QUEUE_NAME)
        _queue_url = response["QueueUrl"]
        return _queue_url
    except ClientError:
        response = client.create_queue(QueueName=EMAIL_QUEUE_NAME)
        _queue_url = response["QueueUrl"]
        return _queue_url


def enqueue_email_payload(
    payload: EmailQueuePayloadDTO,
) -> str:
    body = payload.model_dump_json()
    queue_url = get_email_queue_url()
    response = get_sqs_client().send_message(QueueUrl=queue_url, MessageBody=body)
    message_id = response.get("MessageId")
    logger.info("Enqueued email payload message_id=%s", message_id)
    return message_id


def receive_email_messages(max_number: int = 10, wait_time: int = 20):
    queue_url = get_email_queue_url()
    response = get_sqs_client().receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=max_number,
        WaitTimeSeconds=wait_time,
    )
    return response.get("Messages", [])


def delete_email_message(receipt_handle: str):
    queue_url = get_email_queue_url()
    get_sqs_client().delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle,
    )


def parse_email_payload(raw_body: str) -> EmailQueuePayloadDTO:
    return EmailQueuePayloadDTO.model_validate_json(raw_body)
