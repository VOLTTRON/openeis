# Never commit this file to revision control; it contains sensitive
# information. General settings should be written to _settings.py.
# Sites may override general settings by including them below the
# following import statements. Optionally, sites may implement the
# openeis.local package and include site-specific settings in that
# packages settings module, which are preferred over _settings. That
# module may also import _settings before the site-specific settings.

try:
    from openeis.local.settings import *
except ImportError:
    from ._settings import *

# Include site-specific settings below this line or in
# openeis.local.settings (which must be on the PYTHONPATH).


