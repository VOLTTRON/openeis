'''
Created on Mar 31, 2014

@author: Craig Allwardt
'''
import json
from jsonschema import validate

with open('schema.json') as jsonFile:
    schema = json.load(jsonFile)


site = {
    "name": "PNNL",
    "address": {"street_address": "902 Battelle Blvd."},
}    

print(validate(site, schema))

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
