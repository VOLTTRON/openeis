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

'''
Created on May 11, 2014

@author: D3M614
'''
import unittest
from openeis.projects import sensors
from _ctypes import ArgumentError
import os
import json

class TestSensor(unittest.TestCase):

    def test_loading_of_building(self):
        self.assertIsNotNone(sensors.building)


    def test_loading_of_site(self):
        self.assertIsNotNone(sensors.site)

    def test_sensors_are_loaded(self):
        self.assertIsNotNone(sensors.sensors)
        self.assertTrue(len(sensors.sensors) > 0)

#        self.assertIsNotNone(sensors.buildings)
# #         self.assertIsNotNone(sensors.building_sensors)
# #         self.assertTrue(len(sensors.building_sensors) > 0)
# #
# #         self.assertIsNotNone(sensors.site_sensors)
# #         self.assertTrue(len(sensors.site_sensors) > 0)
#
#     def test_buildings_have_address_objects(self):
#         self.assertIsNotNone(sensors.buildings, msg)
#         self.assertIsNotNone(sensors.building_sensors., msg)
#
#     def test_systems_are_loaded(self):
#         self.assertIsNotNone(sensors.systems)
#         self.assertTrue(len(sensors.systems) > 0)
#
#     def test_rtu_system(self):
#         self.assertIsNotNone(sensors.systems['RTU'])
#         rtu = sensors.systems['RTU']
#         self.assertEqual(21, len(rtu.sensors))
#




    def test_json_and_verify_top_level(self):
        data = os.path.dirname(os.path.realpath(__file__))
        sensor_data_path = os.path.join(data, "../static/projects/json/general_definition.json")

        jsonObj = json.load(open(sensor_data_path, 'r'))
        self.assertIsNotNone(jsonObj, "Invalid json object!")
        #self.assertEqual(4, len(jsonObj.keys()), "Invalid keys in json dictionary.")

#         self.assertTrue("sensors" in jsonObj.keys(), "sensors dict is None")
#         self.assertTrue("systems" in jsonObj.keys(), "systems dict is None")
#         self.assertTrue("site_sensors" in jsonObj.keys(), "site_sensors dict is None")
#         self.assertTrue("building_sensors" in jsonObj.keys(), "building_sensors dict is None")




