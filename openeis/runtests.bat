REM Set the settings module to be used for the openeis instance
REM this should probably be a test server settings but for not
REM use the default settings.

set DJANGO_SETTINGS_MODULE=openeis.server.settings
rem mv projects\fixtures\initial_data.json projects\fixtures\initial_data.json.bak
nosetests --with-xunit -v
rem mv projects\fixtures\initial_data.json.bak projects\fixtures\initial_data.json