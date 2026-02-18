from django.db import migrations


def add_harp_keyboard_sections(apps, schema_editor):
    InstrumentSection = apps.get_model("core", "InstrumentSection")
    InstrumentSection.objects.get_or_create(name="Harp")
    InstrumentSection.objects.get_or_create(name="Keyboard")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0011_magiclink_created_revoked"),
    ]

    operations = [
        migrations.RunPython(
            code=add_harp_keyboard_sections,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
