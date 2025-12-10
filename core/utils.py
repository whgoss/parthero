import os
from email_validator import validate_email, EmailNotValidError


def get_bucket_name(name: str) -> str:
    """Generate an S3 bucket name based on the organization name."""
    return name.title().replace(" ", "_")


def sanitize_filename(filename: str) -> str:
    """Sanitize the filename to prevent security issues."""
    name, ext = os.path.splitext(filename)
    sanitized_name = name.replace(" ", "_").title()
    return f"{sanitized_name}{ext.lower()}"


def get_file_extension(filename: str) -> str:
    """Get the file extension from a filename."""
    _, ext = os.path.splitext(filename)
    return ext.lower()


def is_valid_email(email: str) -> bool:
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False
