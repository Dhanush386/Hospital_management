from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_out
from .models import User, DoctorProfile, LabProfile


@receiver(post_save, sender=User)
def create_doctor_profile(sender, instance, created, **kwargs):
    if kwargs.get('raw'):
        return
    if instance.role == 'DOCTOR':
        DoctorProfile.objects.get_or_create(user=instance)
    elif instance.role == 'LAB':
        LabProfile.objects.get_or_create(user=instance)


@receiver(user_logged_out)
def set_doctor_offline_on_logout(sender, request, user, **kwargs):
    if user and hasattr(user, 'role') and user.role == 'DOCTOR':
        from doctors.models import DoctorAvailability
        DoctorAvailability.objects.filter(doctor=user).update(is_online=False)
