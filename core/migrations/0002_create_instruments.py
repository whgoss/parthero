from core.enum.instruments import InstrumentEnum
from django.db import migrations


def create_instruments(apps, schema_editor):
    Instrument = apps.get_model("core", "Instrument")
    for instrument in InstrumentEnum:
        instrument_model = Instrument(name=instrument.value)
        instrument_model.save()


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
