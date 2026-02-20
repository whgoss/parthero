import boto3
import logging
from botocore.config import Config
from botocore.exceptions import ClientError
from parthero.settings import DEBUG

s3_client = None
logger = logging.getLogger()


def get_s3_client():
    global s3_client
    if s3_client is None:
        if not DEBUG:
            s3_client = boto3.client("s3")
        else:
            s3_client = boto3.client(
                "s3",
                endpoint_url="http://localhost:4566",
                aws_access_key_id="test",
                aws_secret_access_key="test",
                region_name="us-east-1",
                config=Config(
                    signature_version="s3v4",
                    s3={"addressing_style": "path"},
                ),
            )
    return s3_client


def upsert_bucket_for_organization(organization_id: str):
    try:
        s3_client = get_s3_client()
        s3_client.head_bucket(Bucket=organization_id)
    except ClientError as error:
        error_code = error.response["Error"]["Code"]
        if error_code == "404":
            s3_client.create_bucket(Bucket=organization_id)
        else:
            raise error


def delete_file(organization_id: str, file_key: str):
    s3_client = get_s3_client()
    s3_client.delete_object(
        Bucket=organization_id,
        Key=file_key,
    )


def create_upload_url(
    organization_id: str, file_key: str, expiration: int = 3600
) -> str:
    s3_client = get_s3_client()
    try:
        presigned_url = s3_client.generate_presigned_url(
            "put_object",
            Params={"Bucket": organization_id, "Key": file_key},
            ExpiresIn=expiration,
        )
    except ClientError as error:
        logger.error(f"Error generating presigned URL: {error}")
        return None
    return presigned_url


def create_download_url(
    organization_id: str,
    file_key: str,
    expiration: int = 3600,
    download_filename: str | None = None,
) -> str:
    s3_client = get_s3_client()
    try:
        params = {"Bucket": organization_id, "Key": file_key}
        if download_filename:
            params["ResponseContentDisposition"] = (
                f'attachment; filename="{download_filename}"'
            )
        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=expiration,
        )
    except ClientError as error:
        print(f"Error generating presigned URL: {error}")
        return None
    return presigned_url
