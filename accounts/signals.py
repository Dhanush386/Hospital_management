from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, DoctorProfile, LabProfile


@receiver(post_save, sender=User)
def create_doctor_profile(sender, instance, created, **kwargs):
    if kwargs.get('raw'):
        return
    if instance.role == 'DOCTOR':
        DoctorProfile.objects.get_or_create(user=instance)
    elif instance.role == 'LAB':
        LabProfile.objects.get_or_create(user=instance)
