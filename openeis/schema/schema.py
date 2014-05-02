'''
Created on Mar 31, 2014

@author: Craig Allwardt
'''
import json
import os
from jsonschema import validate

SITES = 'sites'
SITE_NAME = 'site_name'
SENSORS = 'sensors'
SENSOR_NAME = 'sensor_name'
SENSOR_TYPE = 'sensor_type'
SENSOR_UNIT_TYPE = 'unit_type'
BUILDINGS = 'buildings'
BUILDING_NAME = 'building_name'
DATA_TYPE = "data_type"
SYSTEMS = "systems"
SYSTEM_NAME = "system_name"
SYSTEM_TYPE = "system_type"

schema_folder = os.path.abspath(os.path.dirname(__file__))
SCHEMA_FILE = '{0}/schema.json'.format(schema_folder) 
SENSOR_DATA_FILE = '{0}/sensor_data.json'.format(schema_folder)
UNIT_DATA_FILE = '{0}/unit_data.json'.format(schema_folder)
 
with open(SCHEMA_FILE) as jsonFile:
    schema = json.load(jsonFile)
    
with open(SENSOR_DATA_FILE) as sensordatafile:
    sensordata = json.load(sensordatafile)
    
with open(UNIT_DATA_FILE) as unitdatafile:
    unitdata = json.load(unitdatafile)

def getSensors():
    return sensordata

def getUnitSelectionType(unitTyp):
    """
    Gets a unit selection type.  
    
    Returns a list of key-(value,other) parrings that can be used to display and capture
    a users selection.  If the unit type does not exist in the set of data then None
    will be returned.
    """
    return None
    
for k in sensordata.keys():
    verify = validate(sensordata[k], schema['definitions']['sensor']) 
    if verify != None:
        raise Exception("Invalid sensor:\n"+verify)
    
# for k in unitdata.keys():
#     verify = validate(sensordata[k], schema['definitions']['unit']) 
#     if verify != None:
#         raise Exception("Invalid unit:\n"+verify)

