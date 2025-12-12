from uuid import UUID
from django.forms import (
    Form,
    CharField,
    TextInput,
    IntegerField,
    NumberInput,
)


class PieceForm(Form):
    organization_id: UUID = None
    class_attribute = "block w-full rounded-xl border border-slate-200 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"

    title = CharField(
        max_length=255,
        widget=TextInput(attrs={"class": class_attribute}),
        required=True,
    )
    edition_name = CharField(
        max_length=255,
        widget=TextInput(attrs={"class": class_attribute}),
        required=False,
    )
    instrumentation = CharField(
        widget=TextInput(attrs={"class": class_attribute}),
        required=True,
    )
    composer = CharField(
        max_length=255,
        widget=TextInput(attrs={"class": class_attribute}),
    )
    arranger = CharField(
        max_length=255,
        widget=TextInput(attrs={"class": class_attribute}),
        required=False,
    )
    duration = IntegerField(
        widget=NumberInput(attrs={"class": class_attribute}), required=False
    )

    def __init__(self, *args, organization_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization_id = organization_id

    def clean(self):
        cleaned = super().clean()
        return cleaned
