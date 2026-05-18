from django.urls import path
from . import views

app_name = 'queue'

urlpatterns = [
    path('display/', views.PublicQueueView.as_view(), name='public_display'),
    path('api/status/', views.QueueStatusApiView.as_view(), name='api_status'),
    path('add/', views.AddToQueueView.as_view(), name='add'),
]
