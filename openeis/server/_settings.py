"""
Django settings for openeis project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

import os
import posixpath

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(__file__)
POSIX_BASE_DIR = os.path.abspath(BASE_DIR)
if os.path.sep != posixpath.sep:
    POSIX_BASE_DIR = posixpath.join(*POSIX_BASE_DIR.split(os.path.sep))

DATA_DIR = os.path.abspath(
    os.path.join(*([BASE_DIR] + ['..']*len(__package__.split('.')) + ['data'])))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'a9sdeeed&m&^8=yt=(res$+-z7kn@pixcia+pi6^!=jk1*e*3r'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

# Append to the INSTALLED_APPS imported from openeis.projects.settngs.
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'openeis.projects',
    'rest_framework',
    'rest_framework_swagger',
    'django_nose',
    'openeis.ui',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'openeis.server.urls'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(DATA_DIR, 'openeis-db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Los_Angeles'
USE_I18N = False
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(DATA_DIR, 'static')

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    posixpath.join(POSIX_BASE_DIR, "templates"),
)

# Setup of django_nose based upon readme at https://github.com/django-nose/django-nose
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

PROTECTED_MEDIA_URL = '/files/'
PROTECTED_MEDIA_ROOT = os.path.join(DATA_DIR, 'files')
PROTECTED_MEDIA_METHOD = 'direct' # 'X-Sendfile', 'X-Accel-Redirect', 'direct'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
