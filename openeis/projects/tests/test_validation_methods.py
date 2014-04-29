'''
Created on Apr 29, 2014


'''
import unittest
from projects import validation

class SchemaLookupTestCase(unittest.TestCase):
    def test_name_validation(self):
        self.assertFalse(validation.is_valid_name(None),  "None objects should return False")
        self.assertFalse(validation.is_valid_name("  "), "Name with just spaces should return False")
        self.assertFalse(validation.is_valid_name("\t\t"), "Name with whitspace characters should return False")
        self.assertTrue(validation.is_valid_name("heloWorld"), "helloWorld should be a valid name!")