'''
Created on May 11, 2014

@author: D3M614
'''
import unittest
from projects import sensors
from _ctypes import ArgumentError
import os
import json

class TestSensor(unittest.TestCase):
    
    def test_loading_of_building(self):
        self.assertIsNotNone(sensors.building)
        
    
    def test_loading_of_site(self):
        self.assertIsNotNone(sensors.site)
    
    def test_sensors_are_loaded(self):
        self.assertIsNotNone(sensors.sensors)
        self.assertTrue(len(sensors.sensors) > 0)
        
#        self.assertIsNotNone(sensors.buildings)
# #         self.assertIsNotNone(sensors.building_sensors)
# #         self.assertTrue(len(sensors.building_sensors) > 0)
# #          
# #         self.assertIsNotNone(sensors.site_sensors)
# #         self.assertTrue(len(sensors.site_sensors) > 0)
#     
#     def test_buildings_have_address_objects(self):
#         self.assertIsNotNone(sensors.buildings, msg)
#         self.assertIsNotNone(sensors.building_sensors., msg)    
#     
#     def test_systems_are_loaded(self):
#         self.assertIsNotNone(sensors.systems)
#         self.assertTrue(len(sensors.systems) > 0)
#     
#     def test_rtu_system(self):
#         self.assertIsNotNone(sensors.systems['RTU'])
#         rtu = sensors.systems['RTU']
#         self.assertEqual(21, len(rtu.sensors))
#         

          
        
    
    def test_json_and_verify_top_level(self):
        data = os.path.dirname(os.path.realpath(__file__))
        sensor_data_path = os.path.join(data, "../static/projects/json/general_definition.json")
        
        jsonObj = json.load(open(sensor_data_path, 'r'))
        self.assertIsNotNone(jsonObj, "Invalid json object!")
        #self.assertEqual(4, len(jsonObj.keys()), "Invalid keys in json dictionary.")
        
#         self.assertTrue("sensors" in jsonObj.keys(), "sensors dict is None")
#         self.assertTrue("systems" in jsonObj.keys(), "systems dict is None")
#         self.assertTrue("site_sensors" in jsonObj.keys(), "site_sensors dict is None")
#         self.assertTrue("building_sensors" in jsonObj.keys(), "building_sensors dict is None")
        
        
        
        
