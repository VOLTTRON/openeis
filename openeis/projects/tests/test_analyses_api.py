'''Tests for RESTful Analyses API.
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


class TestAnalysesApi(OpenEISTestBase):
    fixtures = ['db_dump_test_userPWtest_project.json','analyses_test_data.json']

    def test_daily_summary_run(self):
        # TODO Add test for running an application
        from openeis.applications import (_applicationDict)

        app_name = 'daily_summary'
        self.assertIn(app_name, _applicationDict, app_name + " not in application list")



        client = APIClient()
        response = client.get('/api/analyses')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        client = self.get_authenticated_client()

        #Make sure the applicatin we're looking for exists

        response = client.get('/api/analyses')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        post_data = json.dumps({

            "name": "Unit_Test",
            "dataset": 1,
            "application": "daily_summary",
            "configuration": {
                              "parameters": {
                                             "building_sq_ft": 3000
                                             },
                              "inputs": {
                                         "load": [
                                                  "lbnl/bldg90/WholeBuildingElectricity"
                                                  ]
                                         }
                              }
                })

        response = client.post('/api/analyses', post_data, content_type='application/json', Accept='application/json')
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        analysis_id = response.data['id']
        self.assertIsNotNone(analysis_id)
        self.assertTrue(analysis_id > 0)


#        time.sleep(30)
#        response = client.get('/api/analyses')
#        self.assertEqual(status.HTTP_200_OK, response.status_code)
#        self.assertEqual(response.data[0]['status'], "completed")

    def test_energy_signature_run(self):
        # TODO Add test for running an application
        from openeis.applications import (_applicationDict)

        app_name = 'energy_signature'
        self.assertIn(app_name, _applicationDict, app_name + " not in application list")



        client = APIClient()
        response = client.get('/api/analyses')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        client = self.get_authenticated_client()

        #Make sure the applicatin we're looking for exists

        response = client.get('/api/analyses')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        post_data = json.dumps(    {
            "name": "EnergySignature - Unit Test",
            "dataset": 1,
            "application": "energy_signature",
            "configuration": {
                "inputs": {
                    "oat": [
                        "lbnl/bldg90/OutdoorAirTemperature"
                    ],
                    "load": [
                        "lbnl/bldg90/WholeBuildingElectricity"
                    ]
                },
                "parameters": {}
            }
        })
        response = client.post('/api/analyses', post_data, content_type='application/json', Accept='application/json')
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        analysis_id = response.data['id']
        self.assertIsNotNone(analysis_id)
        self.assertTrue(analysis_id > 0)

#        time.sleep(30)
#        response = client.get('/api/analyses')
#        self.assertEqual(status.HTTP_200_OK, response.status_code)
#        self.assertEqual(response.data[0]['status'], "completed")


