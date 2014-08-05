# OpenEIS Installation Guide (Unix)


## Introduction

This section describes how to install OpenEIS, under a Unix-like shell.


## Requirements

Requires:

+ Python 3


## Create a virtual environment

OpenEIS generally should be run through a virtual environment.

Create and run the virtual environment from the root directory that contains the OpenEIS project files.
This directory can have any name.
The examples here assume this directory is called `openeis_root`:

    > cd  openeis_root
    > ls bootstrap.py

Create the virtual environment:

    > python3  bootstrap.py

This will also install Python's package manager, pip, as well as Django.  Django is the web framework used in OpenEIS.  It provides a development server to work on and an easy database to work with.  For more information, please refer to to [their website](https://www.djangoproject.com/).

Then [activate the virtual environment](command_line_basics_unix.md):

    > source  env/bin/activate


## Finish the installation

From the command prompt established by the virtual environment, finish the installation:

    > python  bootstrap.py
    > pip install  openeis_ui.whl
    > python  bootstrap.py

*TODO: It's not clear the step above is needed anymore.
If it is, need to say where to find the `whl` file.*


## Create a database

To create a database and set up a superuser:

    > openeis  syncdb

You will be prompted for a superuser name and password.

This only needs to be done once, unless there is a change to the schema in the database.


