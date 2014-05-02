'''
Created on Apr 22, 2014

@author: openeis team
'''
from django.test import TestCase
from django.core.exceptions import ValidationError
from projects import models    

class TestModelsValidate(TestCase):
    fixtures = ['all.json'] #, 'initial_data.json']
    
    def test_site_requires_site_name(self):
        
        site = models.Site()
        self.assertTrue(site.validate, "Validations were not setup correctly for site.")
        
        
        
    