'''
Created on Apr 22, 2014

@author: openeis team
'''
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db.models.fields import FieldDoesNotExist
from projects import models    


class TestModelsValidate(TestCase):
    
    def test_can_save_site_sensor(self):
        site = models.Site.objects.create(site_name="PNNL")
        site.save()
    
    def test_can_save_building_sensor(self):
        pass
    
    
    
    def test_building_requires_site_and_building_name(self):
        site = models.Site.objects.create(site_name="PNNL")
        site.save()
        
        building = models.Building(building_name="ISB1")
                 
        with self.assertRaises(ValidationError):
            building.save()
    
        self.assertFalse(building.is_valid())
        
        building.site = site
        building.save()
        self.assertEqual(building.pk, 1, "Invalid building primary key")
                
        
    
    def test_site_requires_site_name(self):
        """
        Test that validate method returns a list of things that are wrong.
        Tests that validate returns an empty set (False) when the 
        """        
        with self.assertRaises(ValidationError):
            models.Site().save()
                
        site = models.Site(site_name="PNNL")
        site.save()
        self.assertEqual(site.pk, 1, "Invalid primary key")
        self.assertEqual(site.site_name, "PNNL", "Invalid site name.")
               
    