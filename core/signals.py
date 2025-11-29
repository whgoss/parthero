from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models.organizations import Organization
from core.services.s3 import create_bucket_for_organization


@receiver(post_save, sender=Organization)
def ensure_org_bucket(sender, instance: Organization, created, **kwargs):
    if kwargs.get("raw"):
        return

    # Safe to call on both create + update since it's an upsert
    create_bucket_for_organization(str(instance.id))
