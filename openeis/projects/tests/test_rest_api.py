'''
Created on May 2, 2014
'''
import json
import io
import tempfile
import time
import os
  
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from openeistest import OpenEISTestBase
  
TEST_USER = 'test_user'
TEST_PASS = 'test_pass'
      
class TestRestApi(OpenEISTestBase):
    fixtures = ['db_dump_test_userPWtest_project.json']
      
    def test_can_get_default_project(self):        
        client = self.get_authenticated_client()
        response = client.get("/api/projects")
        self.assertIsNotNone(response)
        self.assertEqual(response.data[0]['id'], 1)

    def test_can_add_project(self):
        client = self.get_authenticated_client()
        response = client.get("/api/projects")
        projects_before = len(response.data)
        data = {"name": "New Project"}
        response = client.post("/api/projects", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(data['name'], response.data['name'])
        response = client.get("/api/projects")
        self.assertEqual(projects_before+1, len(response.data))
        
    def test_bad_delim_response(self):
        bad_delim = '''Date,Hillside OAT [F],Main Meter [kW],Boiler Gas [kBtu/hr]
9/29/2009 15:00,74.72,280.08,186.52
9/29/2009 16:00
9/29/2009 17:00,75.78,221.92,113.88'''
        expected_response = {'file': ['Could not determine delimiter']}
        client = self.get_authenticated_client()
        
        # Create a temp file for uploading to the server.        
        tf = tempfile.NamedTemporaryFile(suffix='.cxv')
        tf.write(bytes(bad_delim, 'utf-8'))
        tf.flush()
        tf.seek(0)
        response = client.post('/api/projects/1/add_file', {'file':tf})
        self.assertEqual(expected_response, response.data)
    
    def test_can_add_files(self):
        client = self.get_authenticated_client()
        response = client.get('/api/files?project=1')
        original_num_files = len(response.data)
        
        response= self.upload_temp_file_data(1)
        
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(1, response.data['id'])
        self.assertEqual(1, response.data['project'])
        self.assertEqual(original_num_files+1, response.data['id'])
        
        
    
    def test_can_authenticate(self):
        """
        Testing of /api/auth
        """
        client = APIClient()
        self.assertTrue(client.login(username='test_user', password='test'))
        
        