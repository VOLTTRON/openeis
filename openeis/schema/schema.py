'''
Created on Mar 31, 2014

@author: Craig Allwardt
'''
import json
from jsonschema import validate

with open('schema.json') as jsonFile:
    schema = json.load(jsonFile)
    
with open('sensor_data.json') as sensordatafile:
    sensordata = json.load(sensordatafile)
    
with open('unit_data.json') as unitdatafile:
    unitdata = json.load(unitdatafile)
    

for k in sensordata.keys():
    verify = validate(sensordata[k], schema['definitions']['sensor']) 
    if verify != None:
        raise Exception("Invalid sensor:\n"+verify)
    
# for k in unitdata.keys():
#     verify = validate(sensordata[k], schema['definitions']['unit']) 
#     if verify != None:
#         raise Exception("Invalid unit:\n"+verify)

