from django.db import models
from django.conf import settings
import uuid


class Patient(models.Model):
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]

    token_id = models.CharField(max_length=10, unique=True, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_profile',
        null=True,
        blank=True
    )
    name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    visit_date = models.DateTimeField(auto_now_add=True)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=15, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'patients'
        ordering = ['-visit_date']

    def __str__(self):
        return f"{self.name} ({self.token_id})"

    def save(self, *args, **kwargs):
        if not self.token_id:
            self.token_id = self.generate_token()
        
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            self.age = today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
            
        super().save(*args, **kwargs)

    def generate_token(self):
        return f"P{uuid.uuid4().hex[:6].upper()}"


class Prescription(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('READY', 'Ready'),
        ('DISPENSED', 'Dispensed'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='prescriptions')
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='prescriptions_given'
    )
    medicines_json = models.JSONField(default=dict)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    dispensed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prescriptions_dispensed'
    )
    dispensed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'prescriptions'
        ordering = ['-created_at']

    def __str__(self):
        return f"Prescription for {self.patient.name} - {self.status}"

    @property
    def medicines_list(self):
        return self.medicines_json.get('medicines', [])


class ConsultationNote(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='consultation_notes')
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='consultation_notes'
    )
    transcript = models.TextField(blank=True)
    structured_note = models.JSONField(default=dict)
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'consultation_notes'
        ordering = ['-created_at']

    def __str__(self):
        return f"Consultation for {self.patient.name} - {self.created_at.date()}"
