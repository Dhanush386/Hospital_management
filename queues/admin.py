from django.contrib import admin
from .models import QueueSlot


@admin.register(QueueSlot)
class QueueSlotAdmin(admin.ModelAdmin):
    list_display = ['token_number', 'token_date', 'patient', 'department', 'status', 'priority', 'slot_time']
    list_filter = ['status', 'department', 'token_date', 'slot_time']
    search_fields = ['=token_number', 'patient__name', 'patient__token_id']
    date_hierarchy = 'slot_time'
