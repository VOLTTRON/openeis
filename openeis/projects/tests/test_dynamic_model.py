'''
Created on May 15, 2014

'''
from django.test import TestCase
from django.db import models
from openeis.projects.storage.dynamictables import create_model
from django.test.utils import setup_test_environment
from django.conf import settings
from django.core.management import call_command
from openeis.projects.models import User


class TestDynamicModelCreation(TestCase):
    
    def setUp(self):
        setup_test_environment()
        
    
    def test_create_models(self):
        print(dir(User.Meta))
        Person = create_model("Person", {'name':models.CharField(max_length=10)}, app_label='openeis.projects', module= 'dynamicmodels')
        print(dir(Person))
        
        p = Person(name='doah')
        self.assertEqual('doah', p.name)
        
        
        p.save()
        
        p2 = Person.objects.get(pk=1)
        self.assertEqual(1, p2.id)
        self.assertEqual("doah", p2.name)
    
