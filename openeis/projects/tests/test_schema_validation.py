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
from schema.schema import (BUILDING_NAME, BUILDINGS, DATA_TYPE, SENSOR_NAME, SENSOR_TYPE, SENSOR_UNIT_TYPE, SITE_NAME, SITES, SENSORS, 
                SYSTEM_NAME, SYSTEM_TYPE, SYSTEMS, SENSOR_DATA_FILE, SCHEMA_FILE, UNIT_DATA_FILE)

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

        self.good_building_sensor = copy.deepcopy(self.good_building)
        self.good_building_sensor[SITES][0][BUILDINGS][0][SENSORS] = [{SENSOR_NAME: "Building Sensor", DATA_TYPE: "float", SENSOR_UNIT_TYPE: "temperature", SENSOR_TYPE:"FirstStageCooling"}]
        
        self.good_sensor = copy.deepcopy(self.good_site)
        self.good_sensor[SITES][0][SENSORS] = [{SENSOR_NAME: "Test One", DATA_TYPE: "float", SENSOR_UNIT_TYPE: "acceleration", SENSOR_TYPE:"OutdoorAirTemperature"}]
        
        self.good_system = copy.deepcopy(self.good_building)
        self.good_system[SITES][0][BUILDINGS][0][SYSTEMS] = [{SYSTEM_NAME: "HVAC_1", SYSTEM_TYPE: "Chiller" }]
        
        self.good_system_sensor = copy.deepcopy(self.good_system)
        self.good_system_sensor[SITES][0][BUILDINGS][0][SYSTEMS][0][SENSORS] = [{SENSOR_NAME: "Some other name", DATA_TYPE: "integer", SENSOR_UNIT_TYPE: "temperature", SENSOR_TYPE:"FirstStageCooling"}]
        
        self.good_rtu = copy.deepcopy(self.good_building)
        self.good_rtu[SITES][0][BUILDINGS][0][SYSTEMS] = [{SYSTEM_NAME: "RTU_1", SYSTEM_TYPE: "rtu" }]
        
        self.good_rtu_sensor = copy.deepcopy(self.good_rtu)
        self.good_rtu_sensor[SITES][0][BUILDINGS][0][SYSTEMS][0][SENSORS] = [{SENSOR_NAME: "An RTU Sensor", DATA_TYPE: "float", SENSOR_UNIT_TYPE: "temperature", SENSOR_TYPE:"MixedAirTemperature"}]
        
        self.full_schema = json.load(open(SCHEMA_FILE))
        
    def test_cant_add_properties_to_any_object(self):
        """
        Tests the ability to include random stuff in the object that are defined in the schema.
        
        The "additionalProperties": false is the property that is being tested on all of the elements.
        """
        instance = copy.deepcopy(self.good_site)
        instance['bogus_property'] = 'hello world'
        self.assertRaises(jsonschema.exceptions.ValidationError, lambda: validate(instance, self.full_schema))
        
        instance = copy.deepcopy(self.good_building)
        instance['bogus_property'] = 'hello world'
        self.assertRaises(jsonschema.exceptions.ValidationError, lambda: validate(instance, self.full_schema))
        
        instance = copy.deepcopy(self.good_sensor)
        instance['bogus_property'] = 'hello world'
        self.assertRaises(jsonschema.exceptions.ValidationError, lambda: validate(instance, self.full_schema))
        
        instance = copy.deepcopy(self.good_system)
        instance['bogus_property'] = 'hello world'
        self.assertRaises(jsonschema.exceptions.ValidationError, lambda: validate(instance, self.full_schema))
                
        
        
        
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
        
    def test_system_must_have_name_and_type(self):
        instance = self.good_system
        # Fully valid sensor type
        self.assertIsNone(validate(instance, self.full_schema))
        
        #Test with no SYSTEM_TYPE specified
        instance[SITES][0][BUILDINGS][0][SYSTEMS][0].pop(SYSTEM_TYPE)
        self.assertRaises(jsonschema.exceptions.ValidationError, lambda: validate(instance, self.full_schema))
        
        #Test with no SENSOR_TYPE specified
        instance = copy.deepcopy(self.good_system_sensor)
        instance[SITES][0][BUILDINGS][0][SYSTEMS][0][SENSORS][0].pop(SENSOR_TYPE)
        self.assertRaises(jsonschema.exceptions.ValidationError, lambda: validate(instance, self.full_schema))
        
    def test_system_can_have_no_sensors(self):
        instance = self.good_system
        # Fully valid sensor type
        self.assertIsNone(validate(instance, self.full_schema))
        
        
        #Test a system with no sensors attached
        instance = copy.deepcopy(self.good_system_sensor)
        instance[SITES][0][BUILDINGS][0][SYSTEMS][0].pop(SENSORS)
        self.assertIsNone(validate(instance, self.full_schema))
    
    def test_system_cant_have_random_child(self):
        instance = self.good_system
        # Fully valid sensor type
        self.assertIsNone(validate(instance, self.full_schema))
        
        
        #Test a system with no sensors attached
        instance = copy.deepcopy(self.good_system_sensor)
        instance[SITES][0][BUILDINGS][0][SYSTEMS][0]["blah"] =  {"hello": "barf"}
        self.assertRaises(jsonschema.exceptions.ValidationError, lambda: validate(instance, self.full_schema))
        
    def test_rtu_has_allowed_sensor_types(self):
        instance = self.good_rtu_sensor
        # Fully valid sensor type
        self.assertIsNone(validate(instance, self.full_schema))
        
        #Test with no SENSOR_TYPE specified
        instance[SITES][0][BUILDINGS][0][SYSTEMS][0][SENSORS][0].pop(SENSOR_TYPE)
#         self.assertRaises(jsonschema.exceptions.ValidationError, lambda: validate(instance, self.full_schema))
        
        #Test with no SENSOR_TYPE specified
        instance = copy.deepcopy(self.good_rtu_sensor)
        instance[SITES][0][BUILDINGS][0][SYSTEMS][0][SENSOR_TYPE] = 'junk_sensor'
#         self.assertRaises(jsonschema.exceptions.ValidationError, lambda: validate(instance, self.full_schema))

    def test_rtu_catch_valid_non_rtu_sensor(self):
        instance = self.good_rtu_sensor
        # Fully valid sensor type
        self.assertIsNone(validate(instance, self.full_schema))
        
        #Test with no SENSOR_TYPE specified
        instance[SITES][0][BUILDINGS][0][SYSTEMS][0][SENSORS][0][SENSOR_TYPE] = "WholeBuildingGas"
#         self.assertRaises(jsonschema.exceptions.ValidationError, lambda: validate(instance, self.full_schema))
        
#Test with no SENSOR_TYPE specified
        instance[SITES][0][BUILDINGS][0][SYSTEMS][0][SENSORS][0].pop(SENSOR_TYPE)
        self.assertRaises(jsonschema.exceptions.ValidationError, lambda: validate(instance, self.full_schema))


    def test_building_sensor_has_type(self):
        instance = self.good_building_sensor
        # Fully valid sensor type
        print (instance)
        self.assertIsNone(validate(instance, self.full_schema))
        
        #Test with no SENSOR_TYPE specified 
        
        instance[SITES][0][BUILDINGS][0][SENSORS][0].pop(SENSOR_TYPE)
        self.assertRaises(jsonschema.exceptions.ValidationError, lambda: validate(instance, self.full_schema))
        
        #Test with no bad type specified
        instance = copy.deepcopy(self.good_building_sensor)
        instance[SITES][0][BUILDINGS][0][SENSOR_TYPE] = 'junk_sensor'
        self.assertRaises(jsonschema.exceptions.ValidationError, lambda: validate(instance, self.full_schema))
    
        
          
      