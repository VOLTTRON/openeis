:: export PIP_DOWNLOAD_CACHE=/tmp/pip/cache
:: set PATH=C:\Program Files (x86)\Git\bin;%PATH%

C:\Python34\python.exe bootstrap.py

:: Install dependencies for running extra things.
:: env\Scripts\pip.exe install pyflakes
:: env\Scripts\pip.exe install pylint
env\Scripts\pip.exe install pytest-django

:: Required export so that tests can be run
set DJANGO_SETTINGS_MODULE=openeis.server.settings

:: Setup the database
env\Scripts\openeis.exe syncdb --noinput --no-initial-data

:: Load the exported data
env\Scripts\openeis.exe loaddata projects_test_auth.json

:: Install numpy for some of the applications to work properly.
xcopy ..\openeis-setup-support\numpy1.8.2 env\Lib\site-packages /F/E/Y

::env\Scripts\py.test openeis\projects --junitxml=xunit-output.xml --ds=openeis.server.settings

