REM Set the settings module to be used for the openeis instance
REM this should probably be a test server settings but for not
REM use the default settings.

set DJANGO_SETTINGS_MODULE=openeis.server.settings
nosetests --with-xunit