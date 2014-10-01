# OpenEIS Installation Guide (Unix)


## Introduction

This section describes how to install OpenEIS, under a Unix-like shell:

+ [Requirements](#installRequirements)
+ [Creating a virtual environment](#createVirtualEnv)
+ [Finishing the installation](#finishInstallation)
+ [Creating the database](#createDatabase)
+ [Re-creating the database](#createDatabaseAgain)


<a name="installRequirements"/>
## Requirements

Installing OpenEIS requires:

+ Python 3
+ OpenEIS project files

*TODO: Describe getting files, or add pointer to documentation on getting and updating the files.*

The instructions shown here assume the OpenEIS project files reside in a root directory called `openeis_root`.
However, the root directory can have any name.


<a name="createVirtualEnv"/>
## Creating a virtual environment

OpenEIS generally should be run through a virtual environment.

Create and the virtual environment by running `bootstrap.py` from the root directory:

    > cd  openeis_root
    > ls  bootstrap.py
    > python3  bootstrap.py

This will create a virtual environment, housed in directory `openeis_root/env`.

The virtual environment will include Python's package manager, `pip`, as well as [Django](https://www.djangoproject.com/).
Django is the web framework used in OpenEIS.
It provides a development server to work on, and an easy database to work with.

Next [activate the virtual environment](command_line_basics_unix.md#activateVirtualEnv):

    > source  env/bin/activate


<a name="finishInstallation"/>
## Finishing the installation

From the command prompt established by the virtual environment, finish the installation:

    > python  bootstrap.py


<a name="createDatabase"/>
## Creating the database

To create a database and set up a superuser:

    > openeis  syncdb

You will be prompted for a superuser name and password.

This only needs to be done once, unless there is a change to the schema in the database.


<a name="createDatabaseAgain"/>
## Re-creating the database

On occasion, it may be necessary to delete and then re-create the database.
This may happen when, for example, a new table is added to the database.

To re-create the database, first delete the entire `data` directory, then run through the installation procedure again:

    > rm -r  data/
    > source  env/bin/activate
    > python  bootstrap.py
    > openeis  syncdb

*TODO: Not clear the bootstrap is needed above.
I (DML) needed it on the last change, but VTN and CYC did not.
More generally, need to document when bootstrap is needed.*
