from django.db import migrations, models
from django.db.models import Q


def populate_primary_from_existing(apps, schema_editor):
    MusicianInstrument = apps.get_model("core", "MusicianInstrument")
    musician_ids = MusicianInstrument.objects.values_list(
        "musician_id", flat=True
    ).distinct()
    for musician_id in musician_ids:
        rows = list(
            MusicianInstrument.objects.filter(musician_id=musician_id).order_by("id")
        )
        if not rows:
            continue
        rows[0].primary = True
        rows[0].save(update_fields=["primary"])
        for row in rows[1:]:
            row.primary = False
            row.save(update_fields=["primary"])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_programmusician_principal"),
    ]

    operations = [
        migrations.AddField(
            model_name="musicianinstrument",
            name="primary",
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(
            populate_primary_from_existing,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AddConstraint(
            model_name="musicianinstrument",
            constraint=models.UniqueConstraint(
                fields=("musician", "instrument"), name="unique_musician_instrument"
            ),
        ),
        migrations.AddConstraint(
            model_name="musicianinstrument",
            constraint=models.UniqueConstraint(
                condition=Q(primary=True),
                fields=("musician",),
                name="unique_primary_instrument",
            ),
        ),
    ]
