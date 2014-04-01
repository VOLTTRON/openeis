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
from jsonschema import validate
import sys
import os

class SchemaTestCase(unittest.TestCase):
    
    full_schema = None
    __full_schema_file = "../schema.json"
    
    def setUp(self):
        print(os.getcwd())
        full_schema = json.load(open(self.__full_schema_file))
    
    def test_must_have_at_least_one_site(self):
        # Test for no objects listed
        instance = {}
        self.assertRaises(jsonschema.exceptions.ValidationError, validate(self.full_schema, instance))
        
        # Test empty sites specification
        instance = {"sites":[]}
        self.assertRaises(jsonschema.exceptions.ValidationError, validate(self.full_schema, instance))
        
        # One site named PNNL (name is required on a site.
        instance = {"sites":[
                             {
                              "name":"PNNL"
                              }]}
        self.assertIsNone(validate(self.full_schema, instance))