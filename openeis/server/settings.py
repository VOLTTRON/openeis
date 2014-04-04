# WARNING: Never commit this file to revision control; it may contain
# sensitive information.
#
# The preferred method of overriding configuration is to create an
# openeis.local package and override openeis.server._settings in its
# settings.py module. The openeis.local package must be in the
# PYTHONPATH so that this module can find it and include its settings.
#
# If you ignore the warning above and place site-specific configuration
# in this file and it is under git version control, be sure to mark it
# as unchanged using git to help prevent accidentally committing changes:
#
#     git update-index --assume-unchanged settings.py
#

try:
    from openeis.local.settings import *
except ImportError:
    from ._settings import *

