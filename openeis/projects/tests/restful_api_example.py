import requests
import json

# Setup server URL
LOCALHOST = 'http://localhost:8000'
HIGHROAD = 'https://highroad.pnl.gov'
host = HIGHROAD

# Setup user and password.  This user account must exist
# on ther server chosen as host above.
username = 'DevGuide'
password = 'DevPass'
auth = (username, password)

# Path to data file.
filename = 'C:/path/to/1Month_hourly.csv'

# Create a new project for our user,
# equivalent of using the Create button on the Projects screen
project_payload = {'name': 'resttest'}
response = requests.post('{host}/api/projects'.format(host=host),
                         auth=auth, data=project_payload, verify=False)

# Retrieve the project id from the response
project_id = response.json()['id']

# Setup the file we will upload and include some metadata
file_meta = {'file': open(filename, 'rb'),
             'name': filename,
             'format': 'csv'}

# Post the file to the add_file endpoint. Equivalent of using the
# Upload File button in the UI.
filepost_response = requests.post('{host}/api/projects/{proj}/add_file'.
                                  format(host=host, proj=project_id),
                                  files=file_meta, auth=auth, verify=False)

# Retrieve the file id from the response
file_id = filepost_response.json()['id']

# Set the timestamp column and timezone for the file. Uses an http PATCH
# Equivalent of Configure Timestamp on file
ts = {'timestamp': {'columns': [0]}, 'time_zone': 'US/Pacific'}

# Set content-type
headers = {'content-type': 'application/json'}
patch_response = requests.patch('{host}/api/files/{id}'
                                .format(host=host, id=file_id),
                                json.dumps(ts), auth=auth, headers=headers,
                                verify=False)

# Send datamap to RESTful endpoint instead of creating it in UI
# requires project id, retrieved above
datamap = {
    'project': project_id,
    'name': 'restmap',
    'map': {
        'version': 1,
        'sensors': {
            'New building/WholeBuildingPower': {
                'file': '0',
                'column': 'Main Meter [kW]',
                'unit': 'kilowatt',
                'type': 'WholeBuildingPower'
                },
            'New building/OutdoorAirTemperature': {
                'file': '0',
                'column': 'Hillside OAT [F]',
                'unit': 'fahrenheit',
                'type': 'OutdoorAirTemperature'
                },
            'New building': {
                'level': 'building',
                'attributes': {
                    'timezone': 'US/Pacific'
                    }
                }
            },
        'files': {
            '0': {
                'timestamp': {
                    'columns': [
                        0
                    ]
                },
                'signature': {
                    'headers': [
                        'Date',
                        'Hillside OAT [F]',
                        'Main Meter [kW]',
                        'Boiler Gas [kBtu/hr]'
                        ]
                }
            }
        }
    }
}

# Post datamap to the server. Equivalent of 'Create new data map' in UI
map_response = requests.post('{host}/api/datamaps'
                             .format(host=host), json.dumps(datamap),
                             auth=auth, headers=headers, verify=False)

# Retrieve map id from response
map_id = map_response.json()['id']

# Create request for making a dataset using the map we just created
# and the file uploaded above
dataset_request = {'files': [{'name': '0', 'file': file_id}],
                   'map': map_id,
                   'name': 'rest_dataset'}

# Post dataset creation to the server,
# Equivalent of 'Create new data set'
dataset_response = requests.post('{host}/api/datasets'
                                 .format(host=host),
                                 json.dumps(dataset_request),
                                 auth=auth, headers=headers, verify=False)

# Retrieve dataset id from response
dataset_id = dataset_response.json()['id']

# Now we will use the dataset as input to an application
# This replaces Run Analysis. All the information that would be input
# in the analysis GUI must be replicated here

application_setup = {'application': 'heat_map',
                     'configuration': {
                         'parameters': {'building_name': 'MyBuilding'},
                         'inputs': {'load': [
                                    'New building/WholeBuildingPower'
                                    ]
                                    }},
                         'dataset': dataset_id, 'debug': 'false',
                         'name': 'rest_dataset - Heat Map'}

# Post the application setup and the result
# should appear on the server for viewing.
application_response = requests.post('{host}/api/analyses'
                                     .format(host=host),
                                     json.dumps(application_setup),
                                     auth=auth, headers=headers, verify=False)
