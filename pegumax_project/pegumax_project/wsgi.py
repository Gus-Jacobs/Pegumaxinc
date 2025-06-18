"""
WSGI config for pegumax_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application

# Determine the absolute path to the directory containing this wsgi.py file
WSGI_DIR = Path(__file__).resolve().parent  # Directory containing wsgi.py
DJANGO_APP_DIR = WSGI_DIR.parent  # Django app directory ('pegumax_project')
PROJECT_ROOT = DJANGO_APP_DIR.parent  # Project root (contains 'core' and 'pegumax_project')

# Add the project root to sys.path if it's not already there
# This allows Python to find the 'core' module
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pegumax_project.settings')

application = get_wsgi_application()
