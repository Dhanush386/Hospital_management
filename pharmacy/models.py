from django.db import models
from patients.models import Patient
from lab.models import LabOrder
from django.conf import settings


class PharmacyOrder(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PREPARING', 'Preparing'),
        ('READY', 'Ready'),
        ('DISPENSED', 'Dispensed'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='pharmacy_orders')
    prescription = models.ForeignKey(
        'patients.Prescription',
        on_delete=models.CASCADE,
        related_name='pharmacy_orders',
        null=True,
        blank=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    prepared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders_prepared'
    )
    dispensed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders_dispensed'
    )
    dispensed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'pharmacy_orders'
        ordering = ['-created_at']

    def __str__(self):
        return f"Pharmacy Order for {self.patient.name} - {self.status}"
