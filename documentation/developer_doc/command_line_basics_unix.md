# OpenEIS Command Line Basics (Unix)


## Introduction

This section describes basic command-line interactions with OpenEIS, under a Unix-like shell:

+ Activating the virtual environment
+ Running the server
+ Killing the server


## Activating the virtual environment

OpenEIS generally should be run through a virtual environment.
See the [installation guide](install_guide_unix.md) for details on creating a virtual environment.

To activate the virtual environment from subdirectory `env`:

    > source  env/bin/activate

The command prompt should change to include `(openeis)` as a prefix.
For brevity, the sample code does not show this prefix.

Another way to verify that the virtual environment is running is to check that the `python` command runs the appropriate interpreter:

    > which python
    openeis_root/env/bin/python

where `openeis_root` is the root directory that contains the OpenEIS project files.


## Running the server

After activating the virtual environment, run the OpenEIS server by:

    > openeis  runserver

It should now be possible to open a web browser to the main entry point, [http://localhost:8000](http://localhost:8000).
The server also supports a number of useful [API](server_api_tricks.md) pages.


## Killing the server

In general, entering `Control-C` in the same terminal used to start the server, will stop the server.

However, it is possible to get into a state where the server is no longer running, but still claims the port.
In this case, trying to run the server gives an error message like "That port is already in use."

To kill the server, first find out the process identifier of the process holding the port.
Try:

    > ps aux  |  grep -i runserver

However, if some other process than `runserver` actually holds the port, this won't work.

It may be possible to identify the process using `lsof`:

    > lsof -P  |  grep localhost:8000

It is also possible to identify the port using `netstat`.
However, not all `netstat` implementations include the process identifier in the output:

    > netstat -an  |  grep 8000

The `fuser` utility can list the process holding the port (however, this doesn't work on a Mac):

    > fuser  8000/tcp

After identifying the process holding the port, kill it:

    > kill -9  <pid-of-interest>
