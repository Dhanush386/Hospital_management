from django.urls import path
from . import views

app_name = 'pharmacy'

urlpatterns = [
    path('dashboard/', views.PharmacyDashboardView.as_view(), name='dashboard'),
    path('prescriptions/', views.PrescriptionListView.as_view(), name='prescription_list'),
    path('prescriptions/<int:prescription_id>/', views.PrescriptionDetailView.as_view(), name='prescription_detail'),
]
