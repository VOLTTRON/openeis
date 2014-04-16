{% autoescape off %}
from openeis.server._settings import *

# Don't share this key with another Django installation or save it to VCS.
SECRET_KEY = {{ secret_key }}

# Set DEBUG to False on production servers.
DEBUG = {{ debug }}
TEMPLATE_DEBUG = {{ debug }}

ALLOWED_HOSTS = {{ hosts }}

# Set server-specific databases. Don't save this to VCS.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'openeis',
        'USER': 'openeis',
        'PASSWORD': 'changeme',
        #'HOST': '127.0.0.1',
        #'PORT': '5432',
    }
}

# Enable these options if HTTPS is enabled, disable otherwise.
{% if no_https %}#{% endif %}CSRF_COOKIE_SECURE = True
{% if no_https %}#{% endif %}SESSION_COOKIE_SECURE = True

# Select protected media method:
#   direct: Serve files directly through Django. Avoid this if possible.
#   X-Sendfile: Instructs Apache (and similar) web servers to serve
#               files after Django authorizes access.
#   X-Accel-Redirect: Instruct Nginx (and similar) web servers to serve
#                     files after Django authorizes access.
PROTECTED_MEDIA_METHOD = {{ pm_method }}
#PROTECTED_MEDIA_ROOT = os.path.join(DATA_DIR, 'files')
#PROTECTED_MEDIA_URL = '/files/'

# Set these if needed
#STATIC_URL = '/static/'
#STATIC_ROOT = '/var/www/openeis/static'
{% endautoescape %}
