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
WSGI_DIR = Path(__file__).resolve().parent
# The 'pegumax_project' Django app directory is one level up from wsgi.py
DJANGO_APP_DIR = WSGI_DIR.parent
# The overall project root (containing 'core' and 'pegumax_project' Django app) is one level up from the Django app dir
PROJECT_ROOT = DJANGO_APP_DIR.parent

# Add the project root to sys.path if it's not already there
# This allows Python to find the 'core' module
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# For debugging on Render, you can temporarily print the path:
# print(f"WSGI - Added to sys.path: {str(PROJECT_ROOT)}")
# print(f"WSGI - Current sys.path: {sys.path}")



os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pegumax_project.settings')

application = get_wsgi_application()
