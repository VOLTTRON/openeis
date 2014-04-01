'''
Created on Mar 31, 2014

@author: Craig Allwardt
'''
import json
from jsonschema import validate

with open('schema.json') as jsonFile:
    schema = json.load(jsonFile)

#print(schema)
# site = {
#     "name": "PNNL",
#     "street_address": "902 Battelle Blvd."
# }    
# 
# print(validate(site, schema))

with open("schema_test.json") as loader:
    test = json.load(loader)

print("Test Data")
print(json.dumps(test,  sort_keys=True, indent=4))
#print(test)
# sensor = {
#     "sensor":{
#     #"name": "OutdoorAirTemperature",
#     "data-type": "float",
#     "units": "bogus"
#     }
# }

print(validate(test, schema))

# schema = {
#     "$schema": "http://openeis.pnnl.gov/01/schema#"
#     "type": "object",
#     "properties": {
#         "object_type": {
#             "type": "string"
#         },
#     },
#     "required": []
#     
# }
# 
# units_schema = {
#     
# }
