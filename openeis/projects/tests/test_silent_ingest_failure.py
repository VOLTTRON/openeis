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
from django.core.urlresolvers import reverse
from django.test import TestCase
from rest_framework.test import APIClient

import codecs
import json
import os
import pytest
import shutil
import time

from openeis.projects.models import SensorIngestLog
from test_utils import get_authenticated_client, create_project, upload_temp_file_data

# The following general definiation text does not work in our current system.  We use it because this is what
# was initially discovered to be the culprit in the silent error.
BAD_GENERAL_DEF_TEXT = """
{"site": {"attribute_list": ["address"],"sensor_list": ["OutdoorAirTemperature"],"child_list": ["building","other"]},
"building": {"attribute_list": ["address"],"sensor_list": ["OutdoorAirTemperature","OutdoorAirRelativeHumidity","WholeBuildingElectricity","WholeBuildingGas"],"child_list": ["RTU","Chiller","other"]},
"RTU": {"sensor_list": ["OutdoorAirTemperature","OutdoorAirRelativeHumidity","MixedAirTemperature","MixedAirRelativeHumidity","ReturnAirTemperature","ReturnAirRelativeHumidity","DischargeAirTemperature","DischargeAirRelativeHumidity","FirstStageCooling","SecondStageCooling","FirstStageHeating","SecondStageHeating","TotalPower","SupplyFanPower","CondenserFanPower","OutdoorDamperSignal","EconomizerMode","OccupancyMode","ZoneSetpoint","ZoneTemperature","SupplyFanSpeed"]},
"Chiller": {"sensor_list": [],"child_list": ["Pump"]},
"Pump": {"sensor_list": []},"other": {"sensor_list": "*","child_list": ["other"]},"attributes": {"address": {"address": { "data_type": "string"},"city": { "data_type": "string"},"state": { "data_type": "string"},"zip_code": { "data_type": "string"}}},
"sensors": {"CondenserFanPower": {"data_type": "float","sensor_name": "CondenserFanPower","sensor_type": "CondenserFanPower","unit_type": "energy"},"DischargeAirRelativeHumidity": {"data_type": "float","sensor_name": "DischargeAirRelativeHumidity","sensor_type": "DischargeAirRelativeHumidity","unit_type": "dimensionless"},"DischargeAirTemperature": {"data_type": "float","sensor_name": "DischargeAirTemperature","sensor_type": "DischargeAirTemperature","unit_type": "temperature"},"EconomizerMode": {"data_type": "boolean","sensor_name": "EconomizerMode","sensor_type": "EconomizerMode","unit_type": "dimensionless"},"FirstStageCooling": {"data_type": "boolean","sensor_name": "FirstStageCooling","sensor_type": "FirstStageCooling","unit_type": "dimensionless"},"FirstStageHeating": {"data_type": "boolean","sensor_name": "FirstStageHeating","sensor_type": "FirstStageHeating","unit_type": "dimensionless"},"MixedAirRelativeHumidity": {"data_type": "float","sensor_name": "MixedAirRelativeHumidity","sensor_type": "MixedAirRelativeHumidity","unit_type": "dimensionless"},"MixedAirTemperature": {"data_type": "float","sensor_name": "MixedAirTemperature","sensor_type": "MixedAirTemperature","unit_type": "temperature"},"OccupancyMode": {"data_type": "boolean","sensor_name": "OccupancyMode","sensor_type": "OccupancyMode","unit_type": "dimensionless"},"OutdoorAirRelativeHumidity": {"data_type": "float","sensor_name": "OutdoorAirRelativeHumidity","sensor_type": "OutdoorAirRelativeHumidity","unit_type": "dimensionless"},"OutdoorAirTemperature": {"data_type": "float","sensor_name": "OutdoorAirTemperature","sensor_type": "OutdoorAirTemperature","unit_type": "temperature"},"OutdoorDamperSignal": {"data_type": "float","sensor_name": "OutdoorDamperSignal","sensor_type": "OutdoorDamperSignal","unit_type": "dimensionless"},"ReturnAirRelativeHumidity": {"data_type": "float","sensor_name": "ReturnAirRelativeHumidity","sensor_type": "ReturnAirRelativeHumidity","unit_type": "dimensionless"},"ReturnAirTemperature": {"data_type": "float","sensor_name": "ReturnAirTemperature","sensor_type": "ReturnAirTemperature","unit_type": "temperature"},"SecondStageCooling": {"data_type": "boolean","sensor_name": "SecondStageCooling","sensor_type": "SecondStageCooling","unit_type": "temperature"},"SecondStageHeating": {"data_type": "boolean","sensor_name": "SecondStageHeating","sensor_type": "SecondStageHeating","unit_type": "temperature"},"SupplyFanPower": {"data_type": "float","sensor_name": "SupplyFanPower","sensor_type": "SupplyFanPower","unit_type": "energy"},"SupplyFanSpeed": {"maximum": "100","minimum": "0","data_type": "float","sensor_name": "SupplyFanSpeed","sensor_type": "SupplyFanSpeed","unit_type": "dimensionless"},"TotalPower": {"data_type": "float","sensor_name": "TotalPower","sensor_type": "TotalPower","unit_type": "energy"},   "WholeBuildingElectricity":{"data_type": "float","sensor_name": "WholeBuildingElectricity","sensor_type": "WholeBuildingElectricity","unit_type": "power"},"WholeBuildingGas":{"data_type": "float","sensor_name": "WholeBuildingGas","sensor_type": "WholeBuildingGas","unit_type": "power"},"ZoneSetpoint": {"data_type": "float","sensor_name": "ZoneSetpoint","sensor_type": "ZoneSetpoint","unit_type": "temperature"},"ZoneTemperature": {"data_type": "float","sensor_name": "ZoneTemperature","sensor_type": "ZoneTemperature","unit_type": "temperature"}}}"""

VALID_CSV_DATA='''TIME_STAMP,SupplyFanStatus,SupplyAirTempStPt,SupplyAirTemp,ZoneReheat1,ZoneReheat2,ZoneDamperCommand1,ZoneDamperCommand2,SupplyFanCommand Priority,AHUCoolingCoil Priority,DuctStaticPressureStPt,SupplyFanSpeedCommand,HotWaterLoopDp,HotWaterLoopDpSetPoint,OutdoorAirTemperature,HotWaterSupplyTemperatureSetPoint,HotWaterPumpStatus1,BoilerStatus,HotWaterPumpStatus2,HotWaterPumpVFD1 Command,HotWaterPumpVFD2 Command,ReturnAirTemperature,MixedAirTemperature,CoolCall,DamperSignal,DuctStaticPressure,HotWaterSupplyTemperature1,HotWaterSupplyTemperature2,HotWaterReturnTemperature,CoolingCoilValvePosition,RTUCoolCall
4/1/2014 8:05,1,57,67,0,0,100,100,0,0,1.5,75,12.5,20,60,180,1,1,1,100,100,70,65,1,0,1,150,100,125,30,1
4/1/2014 8:06,1,57,67,0,0,100,100,0,0,1.5,75,12.5,20,60,180,1,1,1,100,100,70,65,1,0,1,150,100,125,30,1
4/1/2014 8:07,1,57,67,0,0,100,100,0,0,1.5,75,12.5,20,60,180,1,1,1,100,100,70,65,1,0,1,150,100,125,30,1
4/1/2014 8:08,1,57,67,0,0,100,100,0,0,1.5,75,12.5,20,60,180,1,1,1,100,100,70,65,1,0,1,150,100,125,30,1
4/1/2014 8:09,1,57,67,0,0,100,100,0,0,1.5,75,12.5,20,60,180,1,1,1,100,100,70,65,1,0,1,150,100,125,30,1
4/1/2014 8:10,1,57,67,0,0,100,100,0,0,1.5,75,12.5,20,60,180,1,1,1,100,100,70,65,1,0,1,150,100,125,30,1
4/1/2014 8:11,1,57,67,0,0,100,100,0,0,1.5,75,12.5,20,60,180,1,1,1,100,100,70,65,1,0,1,150,100,125,30,1
4/1/2014 8:12,1,57,67,0,0,100,100,0,0,1.5,75,12.5,20,60,180,1,1,1,100,100,70,65,1,0,1,150,100,125,30,1
4/1/2014 8:13,1,57,67,0,0,100,100,0,0,1.5,75,12.5,20,60,180,1,1,1,100,100,70,65,1,0,1,150,100,125,30,1
4/1/2014 8:14,1,57,67,0,0,100,100,0,0,1.5,75,12.5,20,60,180,1,1,1,100,100,70,65,1,0,1,150,100,125,30,1
4/1/2014 8:15,1,57,67,0,0,100,100,0,0,1.5,75,12.5,20,60,180,1,1,1,100,100,70,65,1,0,1,150,100,125,30,1
4/1/2014 8:16,1,57,67,0,0,100,100,0,0,1.5,75,12.5,20,60,180,1,1,1,100,100,70,65,1,0,1,150,100,125,30,1
'''


class TestSilentIngest(TestCase):
    # This fixture contains the following attributes
    #    - a 'test' project
    #    - an uploaded csv file test_alpha.csv with the timestamp configured.
    #    - a datamap called 'test-map' that has the following
    #         - an "other" object of type SupplyFanSpeed Sensor with the selected file
    #         - a Unit of DCIE    
    #fixtures = ['silent_ingest_fixture.json']
    
    def setUp(self):
        self.client = get_authenticated_client()
        static_json_folder = os.path.join(os.path.dirname(__file__), '..', 'static', 'projects', 'json')
        self.original_def_file = os.path.join(static_json_folder, 'general_definition.json')
        self.bak_def_file = os.path.join(static_json_folder, 'general_definition.json.bak')
        
        shutil.move(self.original_def_file, self.bak_def_file)
        # Write the bad file.
        open(self.original_def_file, 'w').write(BAD_GENERAL_DEF_TEXT)
        
        
        
    def tearDown(self):
        # remove the "faked" data from the original file location
        os.remove(self.original_def_file)
        shutil.move(self.bak_def_file, self.original_def_file)
               
        
    
    def verify_fixture_loaded_properly(self):
#         url = '/api/projects'
#         client = APIClient()
#         assert client.login(username='test_user', password='test')
#         response = client.get(url)
#         assert response.data[0]['id'] == 1
#         assert response.data[0]['name'] == 'test'
        url = '/api/datamaps'
        response = self.client.get(url)
        assert response.data[0]['id'] == 1
        assert response.data[0]['name'] == 'test-map'
        assert response.data[0]['project'] == 1
        
        url = '/api/files'
        response = self.client.get(url)
        assert response.data[0]['name'] == 'test_alpha.csv'
        assert response.data[0]['time_zone'] == 'America/Los_Angeles'
    
    @pytest.mark.skipif(True)    
    def test_create_silent_state(self):
        project_id = create_project('test')
        upload_file_id = upload_temp_file_data(project_id, VALID_CSV_DATA)
        
        # Copied directly from firebug.  The map has to be wrapped around """ in order
            # for the mechanisim to upload properly.  In addition the uplodate_file_id
            # is search and replaced so that it can reference the correct file in the database.
        params = {"project":project_id,
                  "map":"""{"version":1,"sensors":{"abcdef":{"level":"other"},"abcdef/SupplyFanSpeed":{"column":"SupplyFanSpeedCommand","file":"0","unit":"data_center_infrastructure_efficiency","type":"SupplyFanSpeed"}},
                  "files":{"0":{"signature":{"headers":["TIME_STAMP","SupplyFanStatus","SupplyAirTempStPt","SupplyAirTemp","ZoneReheat1","ZoneReheat2","ZoneDamperCommand1","ZoneDamperCommand2","SupplyFanCommand Priority","AHUCoolingCoil Priority","DuctStaticPressureStPt","SupplyFanSpeedCommand","HotWaterLoopDp","HotWaterLoopDpSetPoint","OutdoorAirTemperature","HotWaterSupplyTemperatureSetPoint","HotWaterPumpStatus1","BoilerStatus","HotWaterPumpStatus2","HotWaterPumpVFD1 Command","HotWaterPumpVFD2 Command","ReturnAirTemperature","MixedAirTemperature","CoolCall","DamperSignal","DuctStaticPressure","HotWaterSupplyTemperature1","HotWaterSupplyTemperature2","HotWaterReturnTemperature","CoolingCoilValvePosition","RTUCoolCall"]},"timestamp":{"columns":[0]}}}}""",
                  "valid":"true",
                  "name":"hello"}
        #params['map'] = params['map'].replace("{{upload_file_id}}", str(upload_file_id))
        response = self.client.post('/api/datamaps', params)
        assert response.status_code == 201, 'status code was: {}'.format(response.status_code)
        datamap_id = response.data['id']
        
        # now that we have the datamap uploaded we can attempt to use it in the dataset
        params = {"name":"hello - 10/6/14 6:09 PM","map":datamap_id,"files":[{"name":"0","file":upload_file_id}]}        
        response = self.client.post('/api/datasets', params)
        # Assert that the error code was indeed incorrectly returned
        assert response.status_code == 400, 'The error was not propegated'
        
        
        time.sleep(5)
        # because there was an error there should be something in the log table about the ingestion error.
        for a in SensorIngestLog.objects.all():
            print("Message in log:", a.message)
        assert len(SensorIngestLog.objects.all()) > 0
    
#     def test_silent_ingest_failure(self):
#         self.verify_fixture_loaded_properly()
#         # Create the ingest request
#         url = '/api/datasets'
#         parameters = {"map":1, 'name':'test_alpha_value', "files":[{"name":"0","file":1}]}
#         response = self.client.post(url, parameters)
#         print(response.data)
#         assert response.status_code == '200', 'status code was: {}'.format(response.status_code)
        
        
