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
from core.enum.instruments import InstrumentEnum
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
        max_length=255,
        widget=EmailInput(attrs={"class": class_attribute}),
        required=True,
    )
    principal = BooleanField(required=False)
    core_member = BooleanField(required=False)
    primary_instrument = CharField(
        required=True,
        widget=TextInput(
            attrs={
                "id": "primary_instrument",
                "class": "block w-full rounded-xl border border-slate-200 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100",
            }
        ),
    )
    secondary_instruments = CharField(
        required=False,
        widget=TextInput(
            attrs={
                "id": "secondary_instruments",
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

    def clean_primary_instrument(self):
        """
        Tagify will submit something like: "Violin 1"
        Turn that into our InstrumentEnum
        """
        # Clean primary instrument
        raw_primary = self.cleaned_data.get("primary_instrument", "") or ""
        raw_primary_instrument = raw_primary.strip()
        if not raw_primary_instrument:
            raise ValidationError("Primary instrument is required.")
        if raw_primary_instrument not in InstrumentEnum.values():
            raise ValidationError("Invalid primary instrument.")

        return InstrumentEnum(raw_primary_instrument)

    def clean_secondary_instruments(self):
        """
        Tagify will submit something like: "Violin 1,Violin 2,Cello"
        Turn that into a Python list: ["Violin 1", "Violin 2", "Cello"]
        """
        # Clean secondary instruments
        raw = self.cleaned_data.get("secondary_instruments", "") or ""
        raw_secondary_instruments = [
            raw_instrument.strip()
            for raw_instrument in raw.split(",")
            if raw_instrument.strip()
        ]
        instruments = []
        for raw_secondary_instrument in raw_secondary_instruments:
            if raw_secondary_instrument not in InstrumentEnum.values():
                raise ValidationError("Invalid secondary instrument.")
            else:
                instruments.append(InstrumentEnum(raw_secondary_instrument))
        return instruments

    def clean(self):
        cleaned = super().clean()
        return cleaned
