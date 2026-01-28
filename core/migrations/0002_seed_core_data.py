from core.enum.instruments import InstrumentEnum, get_instrument_family
from django.db import migrations
from django.contrib.auth.hashers import make_password


def create_instrument_metadata(apps, schema_editor):
    Instrument = apps.get_model("core", "Instrument")
    for instrument_section in InstrumentEnum:
        instrument_family = get_instrument_family(instrument_section)
        instrument_section_model = Instrument(
            name=instrument_section.value, family=instrument_family.value
        )
        instrument_section_model.save()


def create_organizations_and_users(apps, schema_editor):
    User = apps.get_model("core", "User")
    Organization = apps.get_model("core", "Organization")
    UserOrganization = apps.get_model("core", "UserOrganization")
    summerville_orchestra = Organization(
        name="Summerville Orchestra", enabled=True, timezone="America/New_York"
    )
    summerville_orchestra.save()

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

    # Add users to Summerville organization
    UserOrganization(
        user_id=will_user.id, organization_id=summerville_orchestra.id
    ).save()
    UserOrganization(
        user_id=wojciech_user.id, organization_id=summerville_orchestra.id
    ).save()


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            code=create_instrument_metadata, reverse_code=migrations.RunPython.noop
        ),
        migrations.RunPython(
            code=create_organizations_and_users, reverse_code=migrations.RunPython.noop
        ),
    ]
