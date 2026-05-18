from django.contrib import admin
from .models import LabOrder


@admin.register(LabOrder)
class LabOrderAdmin(admin.ModelAdmin):
    list_display = ['patient', 'test_name', 'status', 'doctor', 'assigned_lab', 'created_at', 'completed_at']
    list_filter = ['status', 'test_type', 'assigned_lab', 'created_at']
    search_fields = ['patient__name', 'patient__token_id', 'doctor__username', 'assigned_lab__username']
    date_hierarchy = 'created_at'
