"""
URL configuration for smart_hospital project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from accounts.views import HomeView, RoleRedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', HomeView.as_view(), name='home'),
    path('auth/', include('accounts.urls')),
    path('patient/', include('patients.urls')),
    path('doctor/', include('doctors.urls')),
    path('lab/', include('lab.urls')),
    path('pharmacy/', include('pharmacy.urls')),
    path('queue/', include('queues.urls')),
    path('redirect/', RoleRedirectView.as_view(), name='role_redirect'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
