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

from collections import OrderedDict
import itertools
import json
import os.path
import sys


def load_json(filename):
    path = os.path.join(os.path.dirname(__file__), '..', 'static',
                        'projects', 'json', filename + '.json')
    with open(path) as file:
         return json.load(file)

def load_schema():
    path = os.path.join(os.path.dirname(__file__), 'sensormap-schema.json')
    with open(path) as file:
        schema = json.load(file, object_pairs_hook=OrderedDict)
    return schema


def generate_schema():
    gendef = load_json('general_definition')
    unit_types = set()
    sensor_types = []
    keyfunc = lambda s: '' if s['data_type'] == 'boolean' else s['unit_type']
    sensors = sorted(gendef['sensors'].values(), key=keyfunc)
    for unit_type, it in itertools.groupby(sensors, key=keyfunc):
        unit_types.add(unit_type)
        unit = ({'$ref': '#/definitions/units/{}'.format(unit_type)}
                if unit_type else {'not': {}})
        names = sorted(s['sensor_name'] for s in it)
        props = OrderedDict([('type', {'enum': names}), ('unit', unit)])
        obj = OrderedDict([('required', ['unit']),
                           ('properties', props)][int(not unit_type):])
        sensor_types.append(obj)
    all_units = load_json('units')
    units = OrderedDict((k, {'enum': sorted(all_units[k])})
                        for k in sorted(all_units) if k in unit_types)
    schema = load_schema()
    units['title'] = schema['definitions']['units']['title']
    units.move_to_end('title', last=False)
    schema['definitions']['units'] = units
    schema['definitions']['sensor']['oneOf'] = sensor_types
    return schema


def main():
    schema = generate_schema()
    json.dump(schema, sys.stdout, indent=4)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
