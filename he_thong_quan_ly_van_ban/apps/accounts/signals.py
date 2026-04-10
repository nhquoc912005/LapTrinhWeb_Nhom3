from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Customer


@receiver(post_save, sender=Customer)
def sync_customer_core_profile(sender, instance, raw, **kwargs):
    if raw:
        return
    instance.sync_access_context()
