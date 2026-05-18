from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('dashboard/', views.PatientDashboardView.as_view(), name='dashboard'),
    path('join-queue/', views.PatientJoinQueueView.as_view(), name='join_queue'),
    path('prescriptions/', views.PatientPrescriptionsView.as_view(), name='prescriptions'),
    path('lab-results/', views.PatientLabResultsView.as_view(), name='lab_results'),
    path('queue-status/', views.PatientQueueStatusView.as_view(), name='queue_status'),
    path('department-availability/', views.DepartmentAvailabilityView.as_view(), name='department_availability'),
]
