from django.db import migrations, models


def set_program_principal_from_musician(apps, schema_editor):
    ProgramMusician = apps.get_model("core", "ProgramMusician")
    for program_musician in ProgramMusician.objects.select_related("musician").all():
        program_musician.principal = bool(program_musician.musician.principal)
        program_musician.save(update_fields=["principal"])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_seed_core_data"),
    ]

    operations = [
        migrations.AddField(
            model_name="programmusician",
            name="principal",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(
            set_program_principal_from_musician,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
