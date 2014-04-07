from optparse import make_option
import os
import string
import random

from django.core.management.base import NoArgsCommand


_wsgi_py = '''\
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", __package__ + '.settings')
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
'''


_settings_py = '''\
from openeis.server._settings import *

# Don't share this key with another Django installation or save it to VCS.
SECRET_KEY = {secret_key!r}

# Set DEBUG to False on production servers.
DEBUG = {debug!r}
TEMPLATE_DEBUG = {debug!r}

ALLOWED_HOSTS = {hosts!r}

# Set server-specific databases. Don't save this to VCS.
DATABASES = {{
    'default': {{
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'openeis',
        'USER': 'openeis',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }}
}}

# Enable these options if HTTPS is enabled, disable otherwise.
{no_https}CSRF_COOKIE_SECURE = True
{no_https}SESSION_COOKIE_SECURE = True

# Select protected media method:
#   direct: Serve files directly through Django. Avoid this if possible.
#   X-Sendfile: Instructs Apache (and similar) web servers to serve
#               files after Django authorizes access.
#   X-Accel-Redirect: Instruct Nginx (and similar) web servers to serve
#                     files after Django authorizes access.
PROTECTED_MEDIA_METHOD = {pm_method!r}
#PROTECTED_MEDIA_ROOT = os.path.join(DATA_DIR, 'files')
#PROTECTED_MEDIA_URL = '/files/'

# Set these if needed
#STATIC_URL = '/static/'
#STATIC_ROOT = '/var/www/openeis/static'
'''


class Command(NoArgsCommand):
    help = 'Create openeis.local package with skeleton settings.'
    requires_model_validation = False
    option_list = NoArgsCommand.option_list + (
        make_option('--base-dir', default=None,
                    help='Install local settings package into given directory.'),
        make_option('--debug', action='store_true', default=False,
                    help='Set DEBUG variables to True'),
        make_option('--host', dest='hosts', action='append', default=[],
                    help='Append host to ALLOWED_HOSTS'),
        make_option('--no-https', default='', action='store_const', const='#',
                    help='Disable HTTPS security settings.'),
        make_option('--server', default='generic', type='choice',
                    choices=('generic', 'apache', 'nginx'),
                    help='Server type: generic (default), apache, or nginx'),
    )

    def handle_noargs(self, base_dir=None, **options):
        if base_dir is None:
            base_dir = os.path.dirname(__file__)
            for i in range(__package__.count('.') + 1):
                base_dir = os.path.dirname(base_dir)
        mod_dir = os.path.join(base_dir, 'openeis', 'local')
        if not os.path.exists(mod_dir):
            os.makedirs(mod_dir)
        path = os.path.join(mod_dir, '__init__.py')
        if not os.path.exists(path):
            open(path, 'w').close()
        path = os.path.join(mod_dir, 'wsgi.py')
        if not os.path.exists(path):
            with open(path, 'w') as file:
                file.write(_wsgi_py)
        path = os.path.join(mod_dir, 'settings.py')
        if not os.path.exists(path):
            chars = ''.join(getattr(string, name) for name in
                            ['ascii_letters', 'digits', 'punctuation'])
            options['secret_key'] = ''.join(random.choice(chars)
                                            for i in range(50))
            options['pm_method'] = {'generic': 'direct',
                                    'apache': 'X-Sendfile',
                                    'nginx': 'X-Accel-Redirect'}[options['server']]
            with open(path, 'w') as file:
                file.write(_settings_py.format(**options))
        self.stdout.write("Edit `{}' to your liking.".format(path))
