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

'''
This python module loads sensor definitions from a json file for use within the openeis context.
'''
import json
import os
from _ctypes import ArgumentError

sensors = {}
building = {}
site = {}
system = {}

DATA_FILE = "general_definition.json"
# Path to the sensor_data.json file.
sensor_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "static/projects/json/{}".format(DATA_FILE))

def load_types():
    """
    Loads json sensor data into python type objects for use on the backend.
    """
    sensors.clear()
    building.clear()
    site.clear()
    system.clear()

    jsonObj = json.load(open(sensor_data_path, 'r'))

    # First populate the sensors so that they can be referenced in the
    # building and system objects.
    for child in jsonObj['sensors']:
        sensors[child] = type(child, (object,), jsonObj['sensors'][child])

    # building_sensors refrence only the types that are available for the
    # building.
    for child in jsonObj['building']:
        if child == 'building_sensors':
            sensor_list = {}
            for sensor in jsonObj['building'][child]:
                sensor_list[sensor] = sensors[sensor]
            building.building_sensors = sensor_list
        else:
            building[child] = jsonObj['building'][child]


#     # site sensors reference only the types that are available at the site level.
#     for child in jsonObj['site_sensors']['sensor_list']:
#         site_sensors[child] = sensors[child]
#
#     # build the systems so that tehy can be referenced by other systems
#     for child in jsonObj['systems']:
#         systems[child] = type(child, (object,), {'sensors':{}})
#         sensor_list = {}
#         for sensor_type_name in jsonObj['systems'][child]['sensor_list']:
#             sensor_list[sensor_type_name] = sensors[sensor_type_name]
#
#         systems[child].sensors = sensor_list #['sensors'].sensor_type_name = sensors[sensor_type_name]


load_types()




