from uuid import UUID
from django.forms import (
    Form,
    CharField,
    TextInput,
    IntegerField,
    NumberInput,
    HiddenInput,
)
from core.services.domo import fetch_piece


class PieceForm(Form):
    organization_id: UUID = None
    class_attribute = "block w-full rounded-xl border border-slate-200 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"

    title = CharField(
        max_length=255,
        widget=TextInput(attrs={"class": class_attribute}),
        required=True,
    )
    instrumentation = CharField(
        widget=TextInput(attrs={"class": class_attribute}),
        required=True,
    )
    composer = CharField(
        max_length=255,
        widget=TextInput(attrs={"class": class_attribute}),
    )
    duration = IntegerField(
        widget=NumberInput(attrs={"class": class_attribute}),
        required=False,
    )
    domo_id = CharField(required=False, widget=HiddenInput())
    composer_domo_id = CharField(required=False, widget=HiddenInput())

    def __init__(self, *args, organization_id=None, domo_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization_id = organization_id

        # If we have a DOMO ID, use that preopulate the piece's metadata
        if domo_id:
            self.domo_id = domo_id
            domo_work = fetch_piece(domo_id)
            if domo_work:
                self.composer_domo_id = domo_work.composer.domo_uid
                self.initial.update(
                    {
                        "title": domo_work.title,
                        "composer": domo_work.composer.full_name,
                        "instrumentation": domo_work.formula,
                        "duration": int(domo_work.duration),
                        "domo_id": domo_id,
                        "composer_domo_id": domo_work.composer.domo_uid,
                    }
                )

    def clean(self):
        cleaned = super().clean()
        return cleaned
