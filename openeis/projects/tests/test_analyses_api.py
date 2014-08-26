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


    def test_sharing_analysis(self):
        auth_client = self.get_authenticated_client()

        # Can share own analyses
        response = auth_client.post('/api/shared-analyses', {'analysis': 1})
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(response.data['analysis'], 1)
        self.assertEqual(response.data['reports'], ['test report'])
        key = response.data['key']

        # Can see all of own shared analyses
        response = auth_client.get('/api/shared-analyses')
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['key'], key)

        # Analysis cannot be shared if already shared
        response = auth_client.post('/api/shared-analyses', {'analysis': 1})
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        # SharedAnalysis cannot be edited
        response = auth_client.post('/api/shared-analyses/1', {'analysis': 2})
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, response.status_code)

        anon_client = APIClient()

        # Cannot list shared analyses
        response = anon_client.get('/api/shared-analyses')
        self.assertEqual(response.data, [])

        # Cannot share analyses
        response = anon_client.post('/api/shared-analyses', {'analysis': 1})
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        # Cannot access shared analysis without key
        response = anon_client.get('/api/shared-analyses/1')
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

        # Can access shared analysis with key
        response = anon_client.get('/api/shared-analyses/1?key=' + key)
        self.assertEqual(response.data['analysis'], 1)
        self.assertEqual(response.data['name'], 'TestAnalysis')
        self.assertEqual(response.data['reports'], ['test report'])

        # Owner can revoke sharing
        response = auth_client.delete('/api/shared-analyses/1')
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)

        # Cannot access revoked shared analysis
        response = anon_client.get('/api/shared-analyses/1?key=' + key)
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)
