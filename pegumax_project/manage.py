#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path


def main():
    """Run administrative tasks."""
    # Determine the absolute path to the directory containing this manage.py file
    MANAGE_PY_DIR = Path(__file__).resolve().parent
    # The overall project root (containing 'core' and 'pegumax_project' Django app) is one level up
    PROJECT_ROOT = MANAGE_PY_DIR.parent

    # Add the project root to sys.path if it's not already there
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    # For debugging, you can temporarily print the path:
    # print(f"MANAGE.PY - Added to sys.path: {str(PROJECT_ROOT)}")
    # print(f"MANAGE.PY - Current sys.path: {sys.path}")

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
