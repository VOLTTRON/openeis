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

# So that we get the database set up the way that we need it
# before running the tests.
from django.test import TestCase
from rest_framework.test import APIClient
from django.core.urlresolvers import reverse


import json
import codecs

from test_utils import get_authenticated_client


class TestSilentIngest(TestCase):
    # This fixture contains the following attributes
    #    - a 'test' project
    #    - an uploaded csv file test_alpha_nwmSyFS.csv with the timestamp configured.
    #    - a datamap called 'ready-map' that has the following
    #         - an "other" object of type SupplyFanSpeed Sensor with the selected file
    #         - a Unit of DCIE    
    fixtures = ['silent_ingest_fixture.json']
    
    def setUp(self):
        self.client = get_authenticated_client()
    
    def verify_fixture_loaded_properly(self):
#         url = '/api/projects'
#         client = APIClient()
#         assert client.login(username='test_user', password='test')
#         response = client.get(url)
#         assert response.data[0]['id'] == 1
#         assert response.data[0]['name'] == 'test'
        url = '/api/sensormaps'
        response = self.client.get(url)
        assert response.data[0]['id'] == 1
        assert response.data[0]['name'] == 'ready-map'
        assert response.data[0]['project'] == 1
        
        url = '/api/files'
        response = self.client.get(url)
        assert response.data[0]['file'] == 'test_alpha_nwmSyFS.csv'
        assert response.data[0]['time_zone'] == 'America/Los_Angeles'
        
    
    def test_silent_ingest_failure(self):
        self.verify_fixture_loaded_properly()
        # Create the ingest request
        
        
        
