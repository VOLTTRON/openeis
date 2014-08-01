# OpenEIS Server API Tricks


## Introduction

This section lists some useful API pages available under the OpenEIS server.
After [starting the server](command_line_basics.md), log in to enable the API pages.

*TODO: Fill in useful/helpful tips for each page, where appropriate.*


## Projects page

[http://localhost:8000/api/projects](http://localhost:8000/api/projects)


## Files page

[http://localhost:8000/api/files](http://localhost:8000/api/files)


## Sensor maps page

[http://localhost:8000/api/sensormaps](http://localhost:8000/api/sensormaps)


## Datasets page

[http://localhost:8000/api/datasets](http://localhost:8000/api/datasets)


## Authentication page

[http://localhost:8000/api/auth](http://localhost:8000/api/auth)


## Analyses page

This page can be used to test an application.

[http://localhost:8000/api/analyses](http://localhost:8000/api/analyses)

Fill in the HTML form:

+ Name: anything.
+ Dataset: Using the dropdown menu, pick the dataset appropriate to the application.
+ application: The name of the Python file that defines the application, but without ".py" (this should be the same entry as in the `.ini` file).
+ configuration: A JSON version of the application_config and inputs portions of the `.ini` file.
See example below.

Hit `POST`.
You should see output on the console, as well as new tables in the database.

Sample configuration file:

```json
{
  "inputs": {
    "oat": ["lbnl/bldg90/OutdoorAirTemperature"],
    "load": ["lbnl/bldg90/WholeBuildingElectricity"]
  }, 
  "parameters": {
    "building_name": "bldg90"
  }
}
```
