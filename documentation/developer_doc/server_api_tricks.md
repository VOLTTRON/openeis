# OpenEIS Server API Tricks


## Introduction

This section lists some useful API pages available under the OpenEIS server.
After [starting the server](command_line_basics.md), log in to enable the API pages.

The API pages offers a way to make HTTP [`POST` and `GET` requests](http://en.wikipedia.org/wiki/POST_\(HTTP\)) without going through the user interface.
`POST` requests allows you to put information on the server and database, while `GET` allows you to obtain information.

*TODO: Clarify: do the API pages allow you to make the requests without going through the interface, or do they allow you to form and see the requests?
After all, the pages are still accessed via the GUI.*

*TODO: Consider renaming this file to `server_api_pages.md`.


## Overview of use

Most API pages have "OPTIONS" and "GET" buttons near the top.

The "OPTIONS" button displays a JSON object describing the API (for example, its name,
what it can parse, what data needs to be input, etc).

The "GET" button displays a [JSON](http://en.wikipedia.org/wiki/JSON) object showing the relevant information from the database.
At the top of the field there is a header showing:

+ HTTP [request code](http://en.wikipedia.org/wiki/List_of_HTTP_status_codes).
    The request code will tell if the request was a success or not.
+ Content-Type.
    *TODO: explain content type*
+ Allow.
    Shows the supported [HTTP request methods](http://en.wikipedia.org/wiki/Hypertext_Transfer_Protocol#Request_methods).
+ vary *TODO: what is "vary"*.

*TODO Consider deleting the bullet list above, as taking up a lot of space for largely self-explanatory information.*

The results of `GET` requests can be displayed as formatted or unformatted JSON.
To view the unformatted version, select "json" from the pull-down menu on the side of the "GET" button (selecting "api" gives the default, formatted version).


*TODO: Fill in useful/helpful tips for each page, where appropriate.*


## API Root

[http://localhost:8000/api/](http://localhost:8000/api/)

This is the root of the API.
This is where you may access all of the available API pages.


## Projects page

[http://localhost:8000/api/projects](http://localhost:8000/api/projects)

This page lists all projects in the database.

To create a new project, enter a name in the `HTML form` and click "POST".
You can also put the name of your project under "Raw data" in the "name" field.
Now you should see a JSON that has an id associated with your project and the name you had given it.


## Files page

[http://localhost:8000/api/files](http://localhost:8000/api/files)

This page lists the files uploaded to the server.
You may only GET with this page, so you must upload files through the user interface.

*TODO: Files uploaded to server, or to the database?
Or is this distinction meaningless?*


## Sensor maps page

[http://localhost:8000/api/sensormaps](http://localhost:8000/api/sensormaps)

This page lists all the sensor maps.
You may POST your own sensor map in "map" field of the "HTML form" as well as the "Raw data".
The sensor map you post must be in JSON format.
It is easiest to first input a sensor map with the user interface and then copy the JSON format for input.


## Datasets page

[http://localhost:8000/api/datasets](http://localhost:8000/api/datasets)

*TODO: Describe datasets page*


## Authentication page

[http://localhost:8000/api/auth](http://localhost:8000/api/auth)

This page lists all of the usernames on the database right now.
You may only GET from this page, so new users must be added through the user interface.


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
