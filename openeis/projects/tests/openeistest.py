'''
Created on May 22, 2014
'''
from django.test import TestCase
from rest_framework.test import APIClient

class OpenEISTestBase(TestCase):
    
    def get_authenticated_client(self):
        client = APIClient()
        self.assertTrue(client.login(username='test_user', password='test'))
        return client