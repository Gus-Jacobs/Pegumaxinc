# settings.py

from pathlib import Path
import dj_database_url
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ... (rest of your existing settings) ...

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles' # Directory where collectstatic will gather files

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Additional locations of static files
STATICFILES_DIRS = [
    BASE_DIR / "assets", # Assuming this is correct
    # CHANGE THIS LINE to match your actual directory structure:
    BASE_DIR / "frontend" / "student-suite-web", # Changed from "student-suite" to "student-suite-web"
]

# ... (rest of your settings) ...
