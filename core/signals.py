from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from core.models.organizations import Organization
from core.models.music import PartAsset
from core.services.s3 import create_bucket_for_organization, delete_file


@receiver(post_save, sender=Organization)
def ensure_org_bucket(sender, instance: Organization, created, **kwargs):
    if kwargs.get("raw"):
        return

    # Safe to call on both create + update since it's an upsert
    create_bucket_for_organization(str(instance.id))


@receiver(post_delete, sender=PartAsset)
def delete_part_asset(sender, instance: PartAsset, **kwargs):
    if kwargs.get("raw"):
        return

    delete_file(str(instance.piece.organization.id), instance.file_key)
