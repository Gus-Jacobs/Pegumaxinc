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

# Add the parent directory of the Django project ('pegumax_project') to sys.path.
# This directory is the root of your overall project and contains the 'core' module.
# wsgi.py is in /path/to/FreelanceBot/pegumax_project/pegumax_project/wsgi.py
# Path(__file__).resolve().parent is /path/to/FreelanceBot/pegumax_project/pegumax_project/
# Path(__file__).resolve().parent.parent is /path/to/FreelanceBot/pegumax_project/
# Path(__file__).resolve().parent.parent.parent is /path/to/FreelanceBot/
PROJECT_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT_DIR))


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pegumax_project.settings')

application = get_wsgi_application()
