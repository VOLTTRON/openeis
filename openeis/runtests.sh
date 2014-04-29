# Set the settings module to be used for the openeis instance
# this should probably be a test server settings but for not
# use the default settings.

export DJANGO_SETTINGS_MODULE=openeis.server.settings
nosetests --with-xunit