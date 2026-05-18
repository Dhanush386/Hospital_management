from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, DoctorProfile, LabProfile


class DoctorProfileInline(admin.StackedInline):
    model = DoctorProfile
    can_delete = False
    extra = 0
    max_num = 1
    fields = ['department', 'specialization', 'license_number', 'is_available']


class LabProfileInline(admin.StackedInline):
    model = LabProfile
    can_delete = False
    extra = 0
    max_num = 1
    fields = ['department']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_verified', 'is_staff']
    list_filter = ['role', 'is_verified', 'is_staff', 'is_superuser', 'is_active']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Hospital Info', {'fields': ('role', 'phone_number', 'is_verified')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Hospital Info', {'fields': ('role', 'phone_number')}),
    )
    search_fields = ['username', 'first_name', 'last_name', 'email', 'phone_number']
    inlines = [DoctorProfileInline, LabProfileInline]

    def get_inline_instances(self, request, obj=None):
        if obj is None:
            return []

        inline_instances = []
        for inline_class in self.inlines:
            if obj.role == 'DOCTOR' and inline_class is DoctorProfileInline:
                inline_instances.append(inline_class(self.model, self.admin_site))
            elif obj.role == 'LAB' and inline_class is LabProfileInline:
                inline_instances.append(inline_class(self.model, self.admin_site))
        return inline_instances


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'department', 'specialization', 'is_available']
    list_filter = ['is_available', 'department']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'license_number']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'user':
            kwargs['queryset'] = User.objects.filter(role='DOCTOR')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(LabProfile)
class LabProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'department']
    list_filter = ['department']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'user':
            kwargs['queryset'] = User.objects.filter(role='LAB')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
