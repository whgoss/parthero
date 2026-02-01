import os
from rest_framework import serializers
from email_validator import validate_email, EmailNotValidError


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
