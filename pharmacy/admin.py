from django.contrib import admin
from .models import PharmacyOrder


@admin.register(PharmacyOrder)
class PharmacyOrderAdmin(admin.ModelAdmin):
    list_display = ['patient', 'status', 'created_at', 'dispensed_at']
    list_filter = ['status', 'created_at']
    search_fields = ['patient__name', 'patient__token_id']
