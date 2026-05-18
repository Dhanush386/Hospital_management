from django.contrib import admin
from .models import DoctorAvailability


@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'is_online', 'last_seen', 'patients_seen_today']
    list_filter = ['is_online']
