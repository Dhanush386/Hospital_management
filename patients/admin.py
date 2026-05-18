from django.contrib import admin
from .models import Patient, Prescription, ConsultationNote


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['token_id', 'name', 'age', 'phone', 'visit_date', 'is_active']
    list_filter = ['is_active', 'visit_date']
    search_fields = ['token_id', 'name', 'phone']
    date_hierarchy = 'visit_date'


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'status', 'created_at', 'dispensed_at']
    list_filter = ['status', 'created_at']
    search_fields = ['patient__name', 'patient__token_id', 'doctor__username']


@admin.register(ConsultationNote)
class ConsultationNoteAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'approved', 'created_at']
    list_filter = ['approved', 'created_at']
    search_fields = ['patient__name', 'doctor__username', 'transcript']
