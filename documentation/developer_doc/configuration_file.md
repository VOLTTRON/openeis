# OpenEIS Configuration Files


## Introduction

A configuration file describes parameters needed to run an application from the [command line](command_line_basics_unix.md).
The configuration file provides the application with the same information that would be collected by the graphical user interface.

*TODO: Verify statement above about the GUI is correct.*

*TODO: Add appropriate link to running application through GUI, once available in user documentation.*


## Configuration file structure

A configuration file has the following structure:

    [global_settings]
    application=daily_summary
    fixtures=utest_daily_summary/daily_summary_fixture.json
    dataset_id=4
    sensormap_id=4

    [application_config]
    building_sq_ft=3000
    building_name="bldg90"

    [inputs]
    load=lbnl/bldg90/WholeBuildingElectricity

(This example happens to come from file `openeis/applications/utest_applications/utest_daily_summary/daily_summary_floats.ini`.)


## [global settings]

The `[global settings]` section includes:

+ `application`
  The name of the application to run.
+ `fixtures`
  Optional fixture file.
+ `dataset_id`
  The dataset to use from the database.
+ `sensormap_id`
  The sensor map to use from the database.

The fixture file, provided for [testing purposes](unit_testing_applications.md), causes the database to be flushed and replaced with the contents of the fixture.
In the absence of a fixture file, the current database is used.
*TODO: Verify that this is true.
Possibly fixture file entry is old.
In this case, need to remove from all INI files.*

The `dataset_id` and `sensormap_id` are numbered starting from 1.
To inspect the current database for valid numbers, use the [server API](server_api_tricks.md).


## [application_config]

The `application_config` section lists all configuration parameters needed for an application.
The keys correspond to the keys in the dictionary returned by an application's `get_config_parameters()` method.


## [inputs]

The `inputs` section identifies the data to use when running the application.
The keys correspond to the keys in the dictionary returned by an application's `required_input()` method.


*TODO: Add a section documenting means of forming a valid configuration file based on information that can be extracted from the GUI.*
