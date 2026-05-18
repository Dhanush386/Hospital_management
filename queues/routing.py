from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/queue/$', consumers.QueueConsumer.as_asgi()),
    re_path(r'ws/lab/$', consumers.LabOrderConsumer.as_asgi()),
    re_path(r'ws/pharmacy/$', consumers.PharmacyConsumer.as_asgi()),
    re_path(r'ws/notifications/$', consumers.PatientNotificationConsumer.as_asgi()),
]
