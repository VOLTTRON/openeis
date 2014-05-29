'''Tests for RESTful API.
'''

import io
import json
import os
import tempfile
import time

from django.contrib.auth.models import User
from django.test.utils import override_settings
from rest_framework import status
from rest_framework.test import APIClient

from openeis.projects.tests.openeistest import OpenEISTestBase


class TestRestApi(OpenEISTestBase):
    fixtures = ['db_dump_test_userPWtest_project.json']

    def test_eis157_timestamp_parsing_endpoint(self):
        '''
        This function tests the timestamp parsing endpoint for correctness.  The test uses
        the temp upload file loaded from the base class.  The only timestamp column is
        in the 0th column of the data.  
        
        The test will test the parsing ability of the -1 column, the 0th column and the 30th column.
        Of these we expect that the -1 and 30th column will return a 400 bad request as they are out of bounds
        or non-timestep columns In addition we test the default behaviour which is to assume the first column
        is a timestamp.
        '''
        expected = ['9/29/2009 15:00', '2009-09-29T15:00:00+00:00']

        # Upload a file
        response = self.upload_temp_file_data(1)
        file_id = response.data['id']
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        client = self.get_authenticated_client()

        # Tests known valid
        response = client.get('/api/files/{}/timestamps'.format(file_id), {'columns': 0})
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(expected, response.data[0], 'Invalid data returned')

        # Test no column specified
        response = client.get('/api/files/{}/timestamps'.format(file_id))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        # Should default to the first column of data.
        self.assertEqual(expected, response.data[0], 'Invalid data returned')

        # Test negative column
        response = client.get('/api/files/{}/timestamps'.format(file_id), {'columns': -1})
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        # Test out of bounds
        response = client.get('/api/files/{}/timestamps'.format(file_id), {'columns': 30})
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_eis157_timestamp_parsing_endpoint_multi_column_timestamp(self):
        '''
        Tests the timestamp parsing endpoint with multiple column timestamp data.
        '''
        raw_data = '''Date,Time,Hillside OAT [F],Main Meter [kW],Boiler Gas [kBtu/hr]
9/29/2009,15:00,74.72,280.08,186.52
9/29/2009,16:00,75.52,259.67,169.82
9/29/2009,17:00,75.78,221.92,113.88
9/29/2009,18:00,76.19,145.24,54.74
9/29/2009,19:00,76.72,121.85,11.58
9/29/2009,20:00,76.3,113.72,11.17
9/29/2009,21:00,76.88,111.22,21.41'''
        response = self.upload_temp_file_data(1, raw_data)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        file_id = response.data['id']
        client = self.get_authenticated_client()

        # Tests known valid
        response = client.get('/api/files/{}/timestamps'.format(file_id), {'columns': '0,1'})
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual('9/29/2009 15:00', response.data[0][0], 'Invalid data returned')

    def test_can_get_default_project(self):
        client = self.get_authenticated_client()
        response = client.get("/api/projects")
        self.assertIsNotNone(response)
        self.assertEqual(response.data[0]['id'], 1)

    @override_settings(DEBUG=True)
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

#     def test_can_retrieve_status_change_with_large_ingest(self):
#         client = self.get_authenticated_client()
#         # Upload the file
#         expected_id = 1
#         with open(os.path.join(os.path.dirname(__file__), '../fixtures/test_4year.csv'), 'r+b') as upload_file:
#             response = client.post('/api/projects/1/add_file', {'file':upload_file})
#             self.assertEqual(expected_id, response.data['id'])

    @override_settings(DEBUG=True)
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

    @override_settings(DEBUG=True)
    def test_can_add_files(self):
        client = self.get_authenticated_client()
        response = client.get('/api/files', {'project': 1})
        original_num_files = len(response.data)

        response= self.upload_temp_file_data(1)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(1, response.data['id'])
        self.assertEqual(1, response.data['project'])
        self.assertEqual(original_num_files+1, response.data['id'])

    def test_eis176_can_add_sensormap_with_OAT_site_sensors(self):
        '''
        Creates a sensormap, uploads default file and creates an ingestion using the file.
        '''
        # upload file
        response = self.upload_temp_file_data(1)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        file_id = response.data['id']
        
        sensor_map = '''{"version":1,"sensors":{"pnnl/OutdoorAirTemperature":{"type":"OutdoorAirTemperature","column":"Hillside OAT [F]","file":"0","unit":"fahrenheit"},"pnnl":{"level":"site"}},"files":{"0":{"timestamp":{"columns":[0]},"signature":{"headers":["Date","Hillside OAT [F]","Main Meter [kW]","Boiler Gas [kBtu/hr]"]}}}}'''
        client = self.get_authenticated_client()
        response = client.get('/api/sensormaps')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        
        response = client.post('/api/sensormaps', {'project': 1, 'name': 'testmap1', 'map': sensor_map})
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        sensor_map_id = response.data['id']
        self.assertIsNotNone(sensor_map_id)
        self.assertTrue(sensor_map_id > 0)
        
        file_json = '[{"file": 0}]'
        
        response = client.post('/api/datasets', {'files': file_json, 'map': sensor_map_id})
        
        print(response.data)
        
        
        

    def test_can_authenticate(self):
        """
        Testing of /api/auth
        """
        client = APIClient()
        self.assertTrue(client.login(username='test_user', password='test'))
