from core.enum.instruments import InstrumentEnum, get_instrument_family
from django.db import migrations


def create_instruments(apps, schema_editor):
    Instrument = apps.get_model("core", "Instrument")
    for instrument_section in InstrumentEnum:
        instrument_family = get_instrument_family(instrument_section)
        instrument_section_model = Instrument(
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
            code=create_instruments, reverse_code=migrations.RunPython.noop
        ),
    ]
