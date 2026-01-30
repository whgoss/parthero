import os
import re
from rest_framework import serializers
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


class EnumChoiceField(serializers.ChoiceField):
    def __init__(self, enum_cls, **kwargs):
        self.enum_cls = enum_cls
        super().__init__(choices=[e.value for e in enum_cls], **kwargs)

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        return self.enum_cls(value)


def is_integer(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def precise_string_match(needle: str, haystack: str):
    """Match whole word/phrase boundaries, so "horn" won't match inside "english horn"""
    return re.search(rf"\b{re.escape(needle)}\b", haystack) is not None
