#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path


def main():
    """Run administrative tasks."""
    # Add the parent directory of 'pegumax_project' (which contains 'core') to sys.path
    # This script (manage.py) is in /path/to/FreelanceBot/pegumax_project/
    # Path(__file__).resolve().parent is /path/to/FreelanceBot/pegumax_project/
    # Path(__file__).resolve().parent.parent is /path/to/FreelanceBot/
    PROJECT_ROOT_DIR = Path(__file__).resolve().parent.parent
    if str(PROJECT_ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT_DIR))

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pegumax_project.settings') # pegumax_project.settings refers to the inner settings.py
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
