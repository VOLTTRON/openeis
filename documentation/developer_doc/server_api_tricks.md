# OpenEIS Server API Tricks


## Introduction

This section lists some useful API pages available under the OpenEIS server.
After [starting the server](command_line_basics.md), log in to enable the API pages.
API pages offer a way to POST and GET information without going through the user interface,
with the exception of the authentification page, which only allows you to GET.
You may GET information in [JSON](http://en.wikipedia.org/wiki/JSON) format. 
POST and GET are both HTTP requests.
POST allows you to put information on the server and database,
while GET allows you to obtain information in a JSON file.
For more information on HTTP requests refer to [this](http://en.wikipedia.org/wiki/POST_(HTTP)).

The top of most API pages have an "OPTIONS" button and a "GET" button.
When you click on "OPTIONS", a JSON describing this API shows up with information on the name,
what it can parse, what data needs to be inputed, etc.
When you click on the "GET" option, a JSON of all of the previously inputted data should show up in the field below it.
At the top of the field there is a header with the 
+ [HTTP request code](http://en.wikipedia.org/wiki/List_of_HTTP_status_codes):
    The request code will tell if the request was a success or not.
+ content type: The content type will tell the content type.  
    *TODO: explain content type
+ allowed methods:
    The allowed method are allowed [HTTP request methods](http://en.wikipedia.org/wiki/Hypertext_Transfer_Protocol#Request_methods).
+ vary *TODO: what is "vary".

*TODO: Fill in useful/helpful tips for each page, where appropriate.*

## API Root
[http://localhost:8000/api/

This is the root of the API.
This is where you may access all of the available API pages.

## Projects page
[http://localhost:8000/api/projects](http://localhost:8000/api/projects)

This page will contain all of the projects the user has previously inputted.
At the bottom of the page you should see a field "name" under "HTML form".
This is where you input the name of your new project, and click "POST".
You can also put the name of your project under "Raw data" in the "name" field.
Now you should see a JSON that has an id associated with your project and the name you had given it.


## Files page

[http://localhost:8000/api/files](http://localhost:8000/api/files)

This page will have a list of files uploaded to the server.
You may only GET with this page, so you must upload files through the user interface.

## Sensor maps page

[http://localhost:8000/api/sensormaps](http://localhost:8000/api/sensormaps)

This page will have all of the sensor maps in JSON format listed.
You may post your own sensor map in "map" field of the "HTML form" as well as the "Raw data".
The sensor map you post must be in JSON format.
It is best to first input a sensor map with the user interface and then
copy the JSON format for input.

## Datasets page

[http://localhost:8000/api/datasets](http://localhost:8000/api/datasets)
*TODO: Describe datasets page

## Authentication page

[http://localhost:8000/api/auth](http://localhost:8000/api/auth)

This page lists all of the usernames on the database right now.
You may only GET from this page, so new users must be done through the user interface.

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
