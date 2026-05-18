"""
WSGI config for smart_hospital project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_hospital.settings')

application = get_wsgi_application()
app = application
