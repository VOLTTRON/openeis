'''
Created on Apr 17, 2014

Unit tests to test the methods for looking up data from the
associated schema data files.

@author: D3M614
'''
import unittest
import schema.schema as schema
import os

class SchemaLookupTestCase(unittest.TestCase):
    '''
    classdocs
    '''

    def test_temp_lookup_has_correct_3_results(self):
        testUnitType = "temperature"
        results = schema.getUnitSelectionType(testUnitType)
        
        self.assertEqual(3, len(results), "Number of results not correct")
        
        kelvin = [x for x in results if x["key"] == 'kelvin']        
        self.assertTrue(len(kelvin) == 1, "kelvin not found in set")
        
        fahrenheit = [x for x in results if x["key"] == 'fahrenheit']        
        self.assertTrue(len(fahrenheit) == 1, "fahrenheit not found in set")
        
        celsius = [x for x in results if x["key"] == 'celsius']
        self.assertTrue(len(celsius) == 1, "celsius not found in set")