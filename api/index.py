"""
Vercel Serverless Entry Point for PESO Masbate Django App.
This file bridges Vercel's Python runtime with Django's WSGI application.
"""
import os
import sys

# Add project root to Python path so Django can find settings and apps
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'peso_project.settings')

from django.core.wsgi import get_wsgi_application

# This 'app' variable is what Vercel looks for
app = get_wsgi_application()
