from openeis.server._settings import *

# Import database-specific configuration
try:
    from .database import *
except ImportError:
    pass

# Import webserver-specific configuration
try:
    from .webserver import *
except ImportError:
    pass

# Don't share this key with another Django installation or save it to VCS.
with open('/etc/openeis/secret.key') as file:
    SECRET_KEY = file.readline()

# Set DEBUG to False on production servers.
DEBUG = False
TEMPLATE_DEBUG = False

# Enable these options if HTTPS is enabled, disable otherwise.
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
