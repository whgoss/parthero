from uuid import UUID
from django.forms import (
    Form,
    CharField,
    TextInput,
)


class ProgramForm(Form):
    organization_id: UUID = None
    class_attribute = "block w-full rounded-xl border border-slate-200 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"

    title = CharField(
        max_length=255,
        widget=TextInput(attrs={"class": class_attribute}),
        required=True,
    )
    status = CharField(
        widget=TextInput(attrs={"class": class_attribute}),
        required=True,
    )

    def __init__(self, *args, organization_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization_id = organization_id

    def clean(self):
        cleaned = super().clean()
        return cleaned
