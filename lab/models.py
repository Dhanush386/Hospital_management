from django.db import models
from patients.models import Patient
from django.conf import settings


class LabOrder(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    TEST_TYPE_CHOICES = [
        ('BLOOD', 'Blood Test'),
        ('URINE', 'Urine Test'),
        ('XRAY', 'X-Ray'),
        ('CT', 'CT Scan'),
        ('MRI', 'MRI'),
        ('ECG', 'ECG'),
        ('USG', 'Ultrasound'),
        ('OTHER', 'Other'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='lab_orders')
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lab_orders_ordered'
    )
    assigned_lab = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lab_orders_assigned'
    )
    test_type = models.CharField(max_length=20, choices=TEST_TYPE_CHOICES, default='BLOOD')
    custom_test_name = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True)
    result_file = models.FileField(upload_to='lab_results/%Y/%m/%d/', blank=True, null=True)
    result_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lab_orders_completed'
    )

    class Meta:
        db_table = 'lab_orders'
        ordering = ['-created_at']

    def __str__(self):
        test_name = self.custom_test_name if self.test_type == 'OTHER' else self.get_test_type_display()
        return f"{test_name} for {self.patient.name} - {self.status}"

    @property
    def test_name(self):
        if self.test_type == 'OTHER' and self.custom_test_name:
            return self.custom_test_name
        return self.get_test_type_display()
