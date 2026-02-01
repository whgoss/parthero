from core.enum.instruments import InstrumentEnum, InstrumentSectionEnum
from django.db import migrations
from django.contrib.auth.hashers import make_password


def create_instrument_metadata(apps, schema_editor):
    Instrument = apps.get_model("core", "Instrument")
    for instrument in InstrumentEnum:
        instrument_model = Instrument(
            name=instrument.value,
        )
        instrument_model.save()

    InstrumentSection = apps.get_model("core", "InstrumentSection")
    for instrument_section in InstrumentSectionEnum:
        instrument_section_model = InstrumentSection(
            name=instrument_section.value,
        )
        instrument_section_model.save()


def create_users(apps, schema_editor):
    User = apps.get_model("core", "User")

    will_user, created = User.objects.get_or_create(
        username="will",
        defaults={
            "email": "will@parthero.net",
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        },
    )
    wojciech_user, created = User.objects.get_or_create(
        username="wojciech",
        defaults={
            "email": "wojciech@parthero.net",
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        },
    )

    # This makes it impossible to log in until both users set a password
    User.objects.filter(pk=will_user.pk).update(password=make_password(None))
    User.objects.filter(pk=wojciech_user.pk).update(password=make_password(None))


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            code=create_instrument_metadata, reverse_code=migrations.RunPython.noop
        ),
        migrations.RunPython(code=create_users, reverse_code=migrations.RunPython.noop),
    ]
