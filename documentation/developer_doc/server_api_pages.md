# OpenEIS Server API


## Introduction

This section lists some useful API pages available under the OpenEIS server.
After [starting the server](command_line_basics.md#startServer), log in to enable the API pages.

The API pages offers a way to make HTTP [`POST` and `GET` requests](http://en.wikipedia.org/wiki/POST_\(HTTP\)) without going through the user interface.
Additionally, you may also see past requests made through the GUI.
`POST` requests allows you to put information on the server and database, while `GET` allows you to obtain information.

Contents:

+ [Overview](#apiOverview)
+ [API root](#apiRoot)
+ Pages:
    + [Projects](#pageProjects)
    + [Files](#pageFiles)
    + [Sensor maps](#pageSensorMaps)
    + [Datasets](#pageDatasets)
    + [Authentication](#pageAuthentication)
    + [Analyses](#pageAnalyses)


<a name="apiOverview"/>
## Overview

Most API pages have "OPTIONS" and "GET" buttons near the top.

The "OPTIONS" button displays a JSON object describing the API (for example, its name,
what it can parse, what data needs to be input, etc).

The "GET" button displays a [JSON](http://en.wikipedia.org/wiki/JSON) object showing the relevant information from the database.
At the top of the field there is a header showing:
HTTP [request code](http://en.wikipedia.org/wiki/List_of_HTTP_status_codes), content-type, the allowed [HTTP request methods](http://en.wikipedia.org/wiki/Hypertext_Transfer_Protocol#Request_methods), if the POSTed data can vary. *TODO: what is "vary"*.

The results of `GET` requests can be displayed as formatted or unformatted JSON.
To view the unformatted version, select "json" from the pull-down menu on the side of the "GET" button (selecting "api" gives the default, formatted version).


<a name="apiRoot"/>
## API root

[http://localhost:8000/api/](http://localhost:8000/api/)

This is the root of the API.
This is where you may access all of the available API pages.


<a name="pageProjects"/>
## Projects page

[http://localhost:8000/api/projects](http://localhost:8000/api/projects)

This page lists all projects in the database.

To create a new project, enter a name in the `HTML form` and click "POST".
You can also put the name of your project under "Raw data" in the "name" field.
Now you should see a JSON that has an id associated with your project and the name you had given it.


<a name="pageFiles"/>
## Files page

[http://localhost:8000/api/files](http://localhost:8000/api/files)

This page lists the files uploaded to the database.
You may only GET with this page, so you must upload files through the user interface.


<a name="pageSensorMaps"/>
## Sensor maps page

[http://localhost:8000/api/sensormaps](http://localhost:8000/api/sensormaps)

This page lists all the sensor maps.
You may POST your own sensor map in "map" field of the "HTML form" as well as the "Raw data".
The sensor map you post must be in JSON format.
It is easiest to first input a sensor map with the user interface and then copy the JSON format for input.


<a name="pageDatasets"/>
## Datasets page

[http://localhost:8000/api/datasets](http://localhost:8000/api/datasets)

*TODO: Describe datasets page*


<a name="pageAuthentication"/>
## Authentication page

[http://localhost:8000/api/auth](http://localhost:8000/api/auth)

This page lists all of the usernames on the database right now.
You may only GET from this page, so new users must be added through the user interface.


<a name="pageAnalyses"/>
## Analyses page

[http://localhost:8000/api/analyses](http://localhost:8000/api/analyses)

This page can be used to test an application.

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
