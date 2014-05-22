'''
Created on May 2, 2014
'''
 
from rest_framework.test import APIClient
from django.test import TestCase
from django.http.response import HttpResponseForbidden
from django.contrib.auth.models import User
import json
 
TEST_USER = 'test_user'
TEST_PASS = 'test_pass'
     
class TestRestApi(TestCase):
    fixtures = ['db_dump_test_userPWtest_project.json']
     
    def test_can_get_default_project(self):
        client = APIClient()
        self.assertTrue(client.login(username='test_user', password='test'))
        
        response = client.get("/api/projects")
        self.assertIsNotNone(response)
        self.assertEqual(response.data[0]['id'], 1)
        
         
    def test_can_authenticate(self):
        """
        Testing of /api/auth
        """
        # Simulate the login of test_user
        #user = User.objects.get(username="test_user")
        client = APIClient()
        self.assertTrue(client.login(username='test_user', password='test'))
        
        response = client.get("/api/projects")
        #response.render()
        print(response.data)
         
#         response = self.client.get("/api/auth")
#         self.assertTrue(isinstance(response, HttpResponseForbidden))
        #user = User.objects.get(username="test_user")
        #self.client.
        #auth_params = {"username":"test_user","password":"test_pass"}
        #response = self.client.post("/api-token-auth/",auth_params, 'application/json')
        #print(response.streaming_content)
        #print(response.status_code)
        #response = self.client.post("/api/auth", auth_params)
                        
         