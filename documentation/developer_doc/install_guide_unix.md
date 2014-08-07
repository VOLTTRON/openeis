# OpenEIS Installation Guide (Unix)


## Introduction

This section describes how to install OpenEIS, under a Unix-like shell.


## Requirements

Requires:

+ Python 3

*TODO: Describe getting files, or add pointer to documentation on getting and updating the files.*


## Create a virtual environment

OpenEIS generally should be run through a virtual environment.

Create and run the virtual environment from the root directory that contains the OpenEIS project files.
This directory can have any name.
The examples here assume this directory is called `openeis_root`:

    > cd  openeis_root
    > ls bootstrap.py

Create the virtual environment:

    > python3  bootstrap.py

This will also install Python's package manager, `pip`, as well as [Django](https://www.djangoproject.com/).
Django is the web framework used in OpenEIS.
It provides a development server to work on, and an easy database to work with.

Next [activate the virtual environment](command_line_basics_unix.md):

    > source  env/bin/activate


## Finish the installation

From the command prompt established by the virtual environment, finish the installation:

    > python  bootstrap.py


## Create a database

To create a database and set up a superuser:

    > openeis  syncdb

You will be prompted for a superuser name and password.

This only needs to be done once, unless there is a change to the schema in the database.


## Re-creating the database

On occasion, it may be necessary to delete and then re-create the database.
This may happen when, for example, a new table is added to the database.

To re-create the database, first delete the entire `data` directory, then run through the installation procedure again:

    > rm -r  data/
    > source  env/bin/activate
    > python  bootstrap.py
    > openeis  syncdb
