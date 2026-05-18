from django.urls import path
from . import views

app_name = 'doctors'

urlpatterns = [
    path('dashboard/', views.DoctorDashboardView.as_view(), name='dashboard'),
    path('queue/', views.DoctorQueueView.as_view(), name='queue'),
    path('consultation/<int:patient_id>/', views.DoctorConsultationView.as_view(), name='consultation'),
    path('consultation/<int:patient_id>/prescription/', views.CreatePrescriptionView.as_view(), name='create_prescription'),
    path('consultation/<int:patient_id>/lab-order/', views.CreateLabOrderView.as_view(), name='create_lab_order'),
    path('consultation/<int:patient_id>/note/', views.SaveConsultationNoteView.as_view(), name='save_note'),
    path('consultation/<int:patient_id>/generate-soap/', views.GenerateSOAPNoteView.as_view(), name='generate_soap'),
    path('toggle-availability/', views.ToggleAvailabilityView.as_view(), name='toggle_availability'),
    path('lab-results/', views.DoctorLabResultsView.as_view(), name='lab_results'),
]
