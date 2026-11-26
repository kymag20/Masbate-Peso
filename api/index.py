"""
Vercel Serverless Entry Point for PESO Masbate Django App.
This file bridges Vercel's Python runtime with Django's WSGI application.
"""
import os
import sys

# Add project root to Python path so Django can find settings and apps
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'peso_project.settings')

from django.core.wsgi import get_wsgi_application

# Expose both 'app' and 'application' for Vercel Python runtime compatibility
application = get_wsgi_application()
app = application
