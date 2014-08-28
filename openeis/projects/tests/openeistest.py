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
Created on May 22, 2014
'''
import tempfile

from django.test import TestCase
from rest_framework.test import APIClient

UPLOAD_DATA = '''Date,Hillside OAT [F],Main Meter [kW],Boiler Gas [kBtu/hr]
9/29/2009 15:00,74.72,280.08,186.52
9/29/2009 16:00,75.52,259.67,169.82
9/29/2009 17:00,75.78,221.92,113.88
9/29/2009 18:00,76.19,145.24,54.74
9/29/2009 19:00,76.72,121.85,11.58
9/29/2009 20:00,76.3,113.72,11.17
9/29/2009 21:00,76.88,111.22,21.41
9/29/2009 22:00,77.16,107.01,29.2
9/29/2009 23:00,76.44,108.45,81.02
9/30/2009 0:00,76.9,116.66,170.73
9/30/2009 1:00,77.29,119.1,246.17
9/30/2009 2:00,76.99,117.57,213.78
9/30/2009 3:00,,121.98,215.91
9/30/2009 4:00,,139.2,385.73
9/30/2009 5:00,,151.42,477.32
9/30/2009 6:00,,162.47,701.29
9/30/2009 7:00,,189.76,691.95
9/30/2009 8:00,,221.91,624.79
9/30/2009 9:00,,228.19,454.43
9/30/2009 10:00,,236.93,468.05
9/30/2009 11:00,,239.53,308.18
9/30/2009 12:00,,246.81,268.58
9/30/2009 13:00,,249.38,229.05
9/30/2009 14:00,71.81,258.76,205.13
9/30/2009 15:00,71.14,261.77,204.11'''

class OpenEISTestBase(TestCase):


    def get_authenticated_client(self):
        client = APIClient()
        self.assertTrue(client.login(username='test_user', password='test'))
        return client

    def upload_temp_file_data(self, project, data=None):
        '''
        Uploads a filestream that is created from a known stream of valid data.
        '''
        # Create a temp file for uploading to the server.
        tf = tempfile.NamedTemporaryFile(suffix='.cxv')
        if data:
            tf.write(bytes(data, 'utf-8'))
        else:
            tf.write(bytes(UPLOAD_DATA, 'utf-8'))
        tf.flush()
        tf.seek(0)

        client = self.get_authenticated_client()
        return client.post('/api/projects/{}/add_file'.format(project), {'file':tf})

