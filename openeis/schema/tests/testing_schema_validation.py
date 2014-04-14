'''
Created on Apr 1, 2014

The tests contained within this file are meant to validate our schema against
the types of errors that our users could produce when adding systems, sensors,
buildings, and sites to a project.

@author: Craig Allwardt
'''
import unittest
import json
import jsonschema
from jsonschema import validate, RefResolver, Draft4Validator
import sys
import os
import copy
SITES = 'sites'
SITE_NAME = 'site_name'
SENSORS = 'sensors'
SENSOR_NAME = 'sensor_name'
SENSOR_TYPE = 'sensor_type'
SENSOR_UNIT_TYPE = 'unit_type'
BUILDINGS = 'buildings'
BUILDING_NAME = 'building_name'
DATA_TYPE = "data_type"

class SchemaTestCase(unittest.TestCase):

    # good_* are instances that pass the schema
    good_site = None
    good_building = None
    
    def setUp(self):
        # Provide different levels to test schema validation.  The below example shows
        # how to do a deep copy if necessary to extend.
        self.good_site = {SITES:[{SITE_NAME:"PNNL"}]}
        self.good_building = copy.deepcopy(self.good_site)
        self.good_building[SITES][0][BUILDINGS] = [{BUILDING_NAME:"ISB1"}]
        self.good_sensor = copy.deepcopy(self.good_site)
        self.good_sensor[SITES][0][SENSORS] = [{SENSOR_NAME: "Test One", DATA_TYPE: "float", SENSOR_UNIT_TYPE: "acceleration", SENSOR_TYPE:"OutdoorAirTemperature"}]
        
        # Path relative to the tests directory.
        full_schema_file = "../schema.json"
        
        self.full_schema = json.load(open(full_schema_file))
        
    def test_sensor_must_have_valid_sensor_type(self):
        
        # Fully valid sensor type
        instance = copy.deepcopy(self.good_sensor)
        self.assertIsNone(validate(instance, self.full_schema))
        
        #Test with no SENSOR_TYPE specified
        instance[SITES][0][SENSORS][0].pop(SENSOR_TYPE)
        self.assertRaises(jsonschema.exceptions.ValidationError, lambda: validate(instance, self.full_schema))
        
        #Test with no SENSOR_TYPE specified
        instance = copy.deepcopy(self.good_sensor)
        instance[SITES][0][SENSORS][0][SENSOR_TYPE] = 'junk_sensor'
        self.assertRaises(jsonschema.exceptions.ValidationError, lambda: validate(instance, self.full_schema))
        
        
     
    def test_sensor_must_have_valid_data_type(self):
        instance = copy.deepcopy(self.good_sensor)
        
        # Remove data_type
        instance[SITES][0][SENSORS][0].pop(DATA_TYPE)
        self.assertRaises(jsonschema.exceptions.ValidationError, lambda: validate(instance, self.full_schema))
                
        # Apply a sensor with an invalid data type.
        instance[SITES][0][SENSORS][0][DATA_TYPE] = "junk_data_type"
        self.assertRaises(jsonschema.exceptions.ValidationError, lambda: validate(instance, self.full_schema))
                
        # Apply a sensor with an valid data type.
        instance = copy.deepcopy(self.good_sensor)        
        self.assertIsNone(validate(instance, self.full_schema))
                    
    def test_sensor_must_have_valid_unit_type(self):
        
        instance = copy.deepcopy(self.good_sensor)
        
        # No sensor_unit_type specified at all.
        instance[SITES][0][SENSORS][0].pop(SENSOR_UNIT_TYPE)
        self.assertRaises(jsonschema.exceptions.ValidationError, lambda: validate(instance, self.full_schema))
        
        # Apply a sensor with invalid unit type.
        instance = copy.deepcopy(self.good_sensor)
        instance[SITES][0][SENSORS][0][SENSOR_UNIT_TYPE] = "junk_unit_type"        
        self.assertRaises(jsonschema.exceptions.ValidationError, lambda: validate(instance, self.full_schema))
         
        instance = copy.deepcopy(self.good_sensor)
        self.assertIsNone(validate(instance, self.full_schema))
     
    def test_building_must_have_name(self):
        instance = self.good_site
        # Adding one building with no properties.
        instance[SITES][0][BUILDINGS] = [{}]
        self.assertRaises(jsonschema.exceptions.ValidationError, lambda: validate(instance, self.full_schema))
          
        instance[SITES][0][BUILDINGS] = [{BUILDING_NAME:"ISB1"}]
        # Should return None if valid data.
        self.assertIsNone(validate(instance, self.full_schema))
      
    def test_must_have_at_least_one_site(self):
        # Test for no objects listed
        instance = {}
        self.assertRaises(jsonschema.exceptions.ValidationError, lambda: validate(instance, self.full_schema))
          
        # Test empty sites specification
        instance = {SITES:[]}
        self.assertRaises(jsonschema.exceptions.ValidationError, lambda:validate(instance, self.full_schema))
          
        # One site named PNNL (name is required on a site.
        instance = self.good_site
          
        # Should return None if valid data.
        self.assertIsNone(validate(instance, self.full_schema))
          
      