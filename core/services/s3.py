import boto3
from botocore.exceptions import ClientError
from parthero.settings import DEBUG

s3_client = None


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
            )
    return s3_client


def create_bucket_for_organization(organization_id: str):
    try:
        s3_client = get_s3_client()
        s3_client.head_bucket(Bucket=organization_id)
    except ClientError as error:
        error_code = error.response["Error"]["Code"]
        if error_code == "404":
            s3_client.create_bucket(Bucket=organization_id)
        else:
            raise error


def upload_file(file_buffer, organization_id: str, file_key: str):
    s3_client = get_s3_client()
    s3_client.upload_fileobj(file_buffer, Bucket=organization_id, Key=file_key)
