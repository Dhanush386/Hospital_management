from django.db import models
from patients.models import Patient
from queues.models import QueueSlot
from lab.models import LabOrder
from patients.models import Prescription
from django.conf import settings


class DoctorAvailability(models.Model):
    doctor = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='availability'
    )
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    current_patient = models.ForeignKey(
        Patient,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_doctor'
    )
    max_daily_patients = models.PositiveIntegerField(default=20)
    patients_seen_today = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'doctor_availability'

    def __str__(self):
        return f"Dr. {self.doctor.get_full_name()} - {'Online' if self.is_online else 'Offline'}"
