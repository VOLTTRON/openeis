'''
Created on Apr 22, 2014

@author: openeis team
'''
from django.test import TestCase
from django.core.exceptions import ValidationError
from projects import models    

class TestModelsValidate(TestCase):
    #fixtures = ['all.json'] #, 'initial_data.json']
    
    def test_building_requrires_site_and_building_name(self):
        site = models.Site(site_name="PNNL")
    
    
    def test_site_requires_site_name(self):
        """
        Test that validate method returns a list of things that are wrong.
        Tests that validate returns an empty set (False) when the 
        """
        
        with self.assertRaises(ValidationError):
            models.Site().save()
        
        saved_site = models.Site(site_name="PNNL").save()
        print(saved_site)
        site = models.Site.objects.get(site_name="PNNL")
        #self.assertTrue(site.validate(), "Validations were not setup correctly for site.")
        
        #site.site_name = "PNNL"
        #self.assertFalse(site.validate())
               
    