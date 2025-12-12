from core.enum.instruments import InstrumentSectionEnum, get_instrument_family
from django.db import migrations


def create_instrument_sections(apps, schema_editor):
    InstrumentSection = apps.get_model("core", "InstrumentSection")
    for instrument_section in InstrumentSectionEnum:
        instrument_family = get_instrument_family(instrument_section)
        instrument_section_model = InstrumentSection(
            name=instrument_section.value, family=instrument_family.value
        )
        instrument_section_model.save()


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            code=create_instrument_sections, reverse_code=migrations.RunPython.noop
        ),
    ]
