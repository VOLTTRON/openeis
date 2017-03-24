:: export PIP_DOWNLOAD_CACHE=/tmp/pip/cache
:: set PATH=C:\Program Files (x86)\Git\bin;%PATH%

C:\Python34\python.exe bootstrap.py

SET ENVPYTHON=env\Scripts\python.exe
SET ENVPIP=env\Scripts\pip.exe
SET OPENEIS=env\Scripts\openeis.exe

:: Upgrade pip to the lastes version
%ENVPYTHON% -m pip install --upgrade pip

:: These are extra things that we want to be installed and either are
:: available from PyPi or we have in our windows support folder.

%ENVPIP% install wheel
%ENVPIP% install workalendar
%ENVPIP% install pytest-django
%ENVPIP% install dist/windows-support/pre-built-wheels/numpy-1.11.3+mkl-cp34-cp34m-win_amd64.whl
%ENVPIP% install dist/windows-support/pre-built-wheels/scipy-0.19.0-cp34-cp34m-win_amd64.whl
:: %ENVPIP% install pandas

%ENVPIP% install pytest-django

:: Required export so that tests can be run
set DJANGO_SETTINGS_MODULE=openeis.server.settings

:: Setup the database
%OPENEIS% syncdb --noinput --no-initial-data

:: Load the exported data
:: %OPENEIS% loaddata projects_test_auth.json

::env\Scripts\py.test openeis\projects --junitxml=xunit-output.xml --ds=openeis.server.settings

