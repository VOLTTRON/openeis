# -*- coding: utf-8 -*- {{{
# vim: set fenc=utf-8 ft=python sw=4 ts=4 sts=4 et:
#
# Copyright (c) 2014, Battelle Memorial Institute
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.
#
#
# This material was prepared as an account of work sponsored by an
# agency of the United States Government.  Neither the United States
# Government nor the United States Department of Energy, nor Battelle,
# nor any of their employees, nor any jurisdiction or organization
# that has cooperated in the development of these materials, makes
# any warranty, express or implied, or assumes any legal liability
# or responsibility for the accuracy, completeness, or usefulness or
# any information, apparatus, product, software, or process disclosed,
# or represents that its use would not infringe privately owned rights.
#
# Reference herein to any specific commercial product, process, or
# service by trade name, trademark, manufacturer, or otherwise does
# not necessarily constitute or imply its endorsement, recommendation,
# or favoring by the United States Government or any agency thereof,
# or Battelle Memorial Institute. The views and opinions of authors
# expressed herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY
# operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830
#
#}}}

'''Tests for RESTful API.
'''

from datetime import datetime, timezone
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

    def test_timestamp_parsing_endpoint(self):
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

    def test_eis159_store_timestamp_with_file(self):
        response = self.upload_temp_file_data(1)
        file = response.data
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        # Test that timestamp is null.
        self.assertFalse(file.pop('timestamp'))
        client = self.get_authenticated_client()
        # Test patch with known valid value
        ts = {'timestamp': {'columns': [0]}}
        response = client.patch('/api/files/{}'.format(file['id']),
                                json.dumps(ts), content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(ts['timestamp'], response.data.pop('timestamp'))
        self.assertEqual(file, response.data)
        #Test patch with known bad value
        response = client.patch('/api/files/{}'.format(file['id']),
            json.dumps({'timestamp': {'rows': [0]}}), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_eis174_dataset_preview(self):
        sensormap = {
            "version": 1,
            "files": {
                "0": {
                    "signature": {
                        "headers": ["Date", "Hillside OAT [F]", "Main Meter [kW]", "Boiler Gas [kBtu/hr]"]
                    },
                    "timestamp": {"columns": ["Date"]}
                }
            },
            "sensors": {
                "oat": {
                    "type": "OutdoorAirTemperature",
                    "unit": "fahrenheit",
                    "file": "0",
                    "column": "Hillside OAT [F]"
                }
            }
        }
        expected = {
            '0': {
                'errors': [],
                'data': [
                    [datetime(2009, 9, 29, 15, 0, tzinfo=timezone.utc), 74.72],
                    [datetime(2009, 9, 29, 16, 0, tzinfo=timezone.utc), 75.52],
                    [datetime(2009, 9, 29, 17, 0, tzinfo=timezone.utc), 75.78],
                    [datetime(2009, 9, 29, 18, 0, tzinfo=timezone.utc), 76.19],
                    [datetime(2009, 9, 29, 19, 0, tzinfo=timezone.utc), 76.72]
                ]
            }
        }
        # Add data file
        response = self.upload_temp_file_data(1)
        file_id = response.data['id']
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        client = self.get_authenticated_client()
        # Generate preview from explicit sensormap.
        data = json.dumps({'map': sensormap,
                           'files': [{'name': '0', 'file': file_id}],
                           'rows': 5})
        response = client.post('/api/datasets/preview', data,
                content_type='application/json', Accept='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected)
        # Add sensor map for next test
        data = json.dumps({'map': sensormap, 'name': 'test map', 'project': 1})
        response = client.post('/api/sensormaps', data,
                content_type='application/json', Accept='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Test preview with existing sensormap.
        data = json.dumps({'map': {'id': response.data['id']},
                           'files': [{'name': '0', 'file': file_id}],
                           'rows': 5})
        response = client.post('/api/datasets/preview', data,
                content_type='application/json', Accept='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected)
        # Test preview from invalid sensormap.
        data = json.dumps({'map': {'version': 1, 'files': {}, 'sensors': {}},
                           'files': [{'name': '0', 'file': {'filename': file_id, 'time_zone': 'America/Los_Angeles'}}]})
        response = client.post('/api/datasets/preview', data,
                content_type='application/json', Accept='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

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

    def test_application_list(self):
        from openeis.applications import (_applicationDict)

        client = APIClient()
        response = client.get('/api/applications')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        client = self.get_authenticated_client()
        response = client.get('/api/applications')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(len(response.data), len(_applicationDict))

    def test_applications_valid_params_and_inputs(self):
        from openeis.applications import (_applicationDict)

        client = APIClient()
        response = client.get('/api/applications')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        client = self.get_authenticated_client()
        response = client.get('/api/applications')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(len(response.data), len(_applicationDict))
        for app in response.data:
            self.assertTrue(app['name'] in _applicationDict)
            dictApp = _applicationDict[app['name']]
            self.assertEqual(len(app['parameters']),
                             len(dictApp.get_config_parameters()), "Problem with config parameters for: "+app['name'])
            self.assertEqual(len(app['inputs']),
                             len(dictApp.required_input()), "Problem with required inputs: "+app['name'])
