from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('PATIENT', 'Patient'),
        ('DOCTOR', 'Doctor'),
        ('LAB', 'Lab Technician'),
        ('PHARMACY', 'Pharmacist'),
        ('ADMIN', 'Administrator'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='PATIENT',
        help_text='User role in the hospital system'
    )
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_patient(self):
        return self.role == 'PATIENT'

    @property
    def is_doctor(self):
        return self.role == 'DOCTOR'

    @property
    def is_lab(self):
        return self.role == 'LAB'

    @property
    def is_pharmacy(self):
        return self.role == 'PHARMACY'

    @property
    def is_admin_role(self):
        return self.role == 'ADMIN'

    def get_dashboard_url(self):
        from django.conf import settings
        return settings.ROLE_DASHBOARD_URLS.get(self.role, '/')


class DoctorProfile(models.Model):
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

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES, blank=True)
    specialization = models.CharField(max_length=100, blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    is_available = models.BooleanField(default=True)

    class Meta:
        db_table = 'doctor_profiles'

    def __str__(self):
        return f"Dr. {self.user.get_full_name()}"


class LabProfile(models.Model):
    LAB_DEPARTMENT_CHOICES = [
        ('BLOOD', 'Blood Test'),
        ('URINE', 'Urine Test'),
        ('XRAY', 'X-Ray'),
        ('CT', 'CT Scan'),
        ('MRI', 'MRI'),
        ('ECG', 'ECG'),
        ('USG', 'Ultrasound'),
        ('OTHER', 'Other Lab Tests'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lab_profile')
    department = models.CharField(
        max_length=20,
        choices=LAB_DEPARTMENT_CHOICES,
        blank=True,
        help_text='Leave blank for central lab access to all lab test types.'
    )

    class Meta:
        db_table = 'lab_profiles'

    def __str__(self):
        department = self.get_department_display() if self.department else 'All Departments'
        return f"{self.user.get_full_name() or self.user.username} - {department}"
