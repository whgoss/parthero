from uuid import UUID
from django.forms import (
    Form,
    CharField,
    TextInput,
    EmailField,
    EmailInput,
    BooleanField,
    ValidationError,
)
from core.enum.instruments import InstrumentSectionEnum
from core.services.organizations import get_musician_by_email
from core.utils import is_valid_email


def email_validator(email: str):
    return is_valid_email(email)


class MusicianForm(Form):
    organization_id: UUID = None
    original_email: str = None

    class_attribute = "block w-full rounded-xl border border-slate-200 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"

    first_name = CharField(
        max_length=64, widget=TextInput(attrs={"class": class_attribute}), required=True
    )
    last_name = CharField(
        max_length=64, widget=TextInput(attrs={"class": class_attribute}), required=True
    )
    email = EmailField(
        validators=[email_validator],
        max_length=256,
        widget=EmailInput(attrs={"class": class_attribute}),
        required=True,
    )
    core_member = BooleanField(required=False)
    sections = CharField(
        required=False,
        widget=TextInput(
            attrs={
                "id": "instrument-sections",
                "class": "block w-full rounded-xl border border-slate-200 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100",
            }
        ),
    )

    def __init__(self, *args, original_email=None, organization_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_email = (original_email or "").strip().lower()
        self.organization_id = organization_id

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if self.original_email and email == self.original_email:
            return email

        user = get_musician_by_email(self.organization_id, email)
        if user:
            raise ValidationError("A musician with this email already exists.")
        return email

    def clean_sections(self):
        """
        Tagify will submit something like: "Violin 1,Violin 2,Cello"
        Turn that into a Python list: ["Violin 1", "Violin 2", "Cello"]
        """
        raw = self.cleaned_data.get("sections", "") or ""
        raw_sections = [
            raw_section.strip() for raw_section in raw.split(",") if raw_section.strip()
        ]
        sections = []
        for raw_section in raw_sections:
            if raw_section not in InstrumentSectionEnum.values():
                raise ValidationError("Invalid instrument section.")
            else:
                sections.append(InstrumentSectionEnum(raw_section))
        return sections

    def clean(self):
        cleaned = super().clean()
        return cleaned
