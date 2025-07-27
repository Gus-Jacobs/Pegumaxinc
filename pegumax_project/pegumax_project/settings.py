# settings.py

from pathlib import Path
import dj_database_url
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ... (rest of your existing settings: SECRET_KEY, DEBUG, ALLOWED_HOSTS_STRING, etc.) ...

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main_site.apps.MainSiteConfig',
    'django.contrib.humanize',
    'rest_framework',
    'bot_monitor',
    'whitenoise.runserver_nostatic', # Keep this for dev if you want.
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # This must be high up, after SecurityMiddleware
    # 'bot_monitor.middleware.CsrfExemptAPIMiddleware', # Uncomment if you're using this
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Note: STATICFILES_STORAGE is defined below in the static files section, which is cleaner.
# You can remove the duplicate line from here: STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

ROOT_URLCONF = 'pegumax_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], # Using Pathlib here
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'pegumax_project.wsgi.application'

# ... (rest of your database, password validation, internationalization settings) ...

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles' # Directory where collectstatic will gather files

# This setting must be here for WhiteNoise to compress and manifest static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Additional locations of static files
STATICFILES_DIRS = [
    # If you have a 'static' folder directly under your project root for general static files:
    # BASE_DIR / "static",
    
    # Path to your project-level 'assets' directory (if it contains static files to be collected)
    BASE_DIR / "assets",

    # THIS IS THE CRUCIAL ONE FOR YOUR FLUTTER APP
    BASE_DIR / "frontend" / "student-suite", # Use Pathlib's / operator for joining paths
]

# ... (rest of your settings: LOGIN_URL, EMAIL, DEFAULT_AUTO_FIELD, BOT_REMOTE_LOG_API_KEY, Security settings) ...
