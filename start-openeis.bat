:: Assumes the current directory is the root of openeis

:: Set the port we want openeis to run under.
SET OPENEIS_PORT=54620

::echo off
start env\scripts\openeis.exe runserver %OPENEIS_PORT%

:: timeout command waits for n seconds before continuing
:: a hack to make sure the server might have a chance to
:: start before opening iexplore
timeout /T 3

start iexplore.exe http://localhost:%OPENEIS_PORT%
