from datetime import time, timedelta

from django.db import models, transaction
from django.db.models import Max
from django.utils import timezone
from patients.models import Patient
from django.conf import settings


QUEUE_DAY_START = time(4, 0)


def get_queue_token_date(at_time=None):
    local_time = timezone.localtime(at_time or timezone.now())
    token_date = local_time.date()
    if local_time.time() < QUEUE_DAY_START:
        token_date -= timedelta(days=1)
    return token_date


class QueueSlot(models.Model):
    STATUS_CHOICES = [
        ('WAITING', 'Waiting'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    DEPARTMENT_CHOICES = [
        ('GENERAL', 'General Medicine'),
        ('CARDIOLOGY', 'Cardiology'),
        ('ORTHOPEDICS', 'Orthopedics'),
        ('PEDIATRICS', 'Pediatrics'),
        ('DERMATOLOGY', 'Dermatology'),
        ('ENT', 'ENT'),
        ('OPHTHALMOLOGY', 'Ophthalmology'),
        ('NEUROLOGY', 'Neurology'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='queue_slots')
    token_number = models.PositiveIntegerField(editable=False)
    token_date = models.DateField(editable=False)
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES, default='GENERAL')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='WAITING')
    slot_time = models.DateTimeField(auto_now_add=True)
    estimated_wait_time = models.PositiveIntegerField(default=15)
    priority = models.PositiveIntegerField(default=0)
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_patients'
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ML Tracking fields
    predicted_wait_time = models.PositiveIntegerField(null=True, blank=True, help_text="Wait time predicted by ML model")
    actual_wait_time_mins = models.IntegerField(null=True, blank=True, help_text="Actual wait time recorded")
    prediction_error_mins = models.IntegerField(null=True, blank=True, help_text="Actual minus Predicted")

    class Meta:
        db_table = 'queue_slots'
        ordering = ['priority', 'slot_time']
        constraints = [
            models.UniqueConstraint(
                fields=['token_date', 'department', 'token_number'],
                name='unique_daily_department_queue_token'
            ),
        ]

    def __str__(self):
        return f"Token {self.token_number} - {self.patient.name} - {self.department} - {self.status}"

    def save(self, *args, **kwargs):
        if not self.token_date:
            self.token_date = get_queue_token_date()

        if not self.token_number:
            with transaction.atomic():
                list(
                    QueueSlot.objects.select_for_update()
                    .filter(token_date=self.token_date, department=self.department)
                    .values_list('id', flat=True)
                )
                max_token = QueueSlot.objects.filter(
                    token_date=self.token_date,
                    department=self.department
                ).aggregate(Max('token_number'))['token_number__max'] or 0
                self.token_number = max_token + 1
                return super().save(*args, **kwargs)

        return super().save(*args, **kwargs)

    @property
    def position_in_queue(self):
        if self.status != 'WAITING':
            return None
        return QueueSlot.objects.filter(
            department=self.department,
            status='WAITING',
            priority__gte=self.priority,
            slot_time__lte=self.slot_time
        ).count()

    @property
    def waiting_time_display(self):
        position = self.position_in_queue
        if position is None:
            return "Not in queue"
        return f"~{position * self.estimated_wait_time} mins"
