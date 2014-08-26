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
# r favoring by the United States Government or any agency thereof,
# or Battelle Memorial Institute. The views and opinions of authors
# expressed herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY
# operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830

#}}}

import json
import os.path
import re
import sys

from jsonschema import exceptions, Draft4Validator


def pull_headers(file):
    '''Try to access the signature headers of a file.
    
    Return the list of headers or an empty list on failure.
    '''
    try:
        headers = file['signature']['headers']
    except (KeyError, TypeError):
        return []
    return headers if isinstance(headers, list) else []


def add_instance_constraints(schema, obj):
    '''Examine obj and add constraints to check for valid references.

    Checked references include file names and column names and indexes.
    '''
    # Check that dictionaries occur where expected
    if not (isinstance(obj, dict) and isinstance(obj.get('files'), dict) and
            isinstance(obj.get('sensors'), dict)):
        return
    used_files = {sensor['file'] for sensor in obj['sensors'].values()
        if isinstance(sensor, dict) and isinstance(sensor.get('file'), str)}
    if not used_files:
        return
    files = [i for i in obj['files'].items() if i[0] in used_files]
    defs = schema['definitions']
    # Limit the files named under 'files' to those used by sensors and
    # ensure the timestamp columns are valid for that file.
    defs['file_reqs'].update({
        "properties": {
            name: {
                "properties":{
                    "timestamp": {
                        "properties": {
                            "columns": {
                                "oneOf": [
                                    {
                                        "type": "array",
                                        "items": {
                                "$ref": "#/definitions/header_reqs/{}".format(i)
                                        }
                                    },
                                    {
                                "$ref": "#/definitions/header_reqs/{}".format(i)
                                    }
                                ]
                            }
                        }
                    }
                },
            }
            for i, (name, file) in enumerate(files)
        },
        "additionalProperties": False
    })
    # Limit the files available to sensors and ensure they reference
    # valid columns.
    defs['sensor_columns'].update({
        "additionalProperties": {
            "anyOf": [
                {
                    "properties": {
                        "file": {"enum": [name]},
                        "column": {"$ref": "#/definitions/header_reqs/{}".format(i)}
                    }
                }
                for i, (name, file) in enumerate(files)
            ]
        }
    })
    # Set name and index constraints for file columns.
    defs['header_reqs'] = {
        str(i): {
            "anyOf": [
                {
                    "type": "string",
                    "enum": [name for name in headers
                             if name and isinstance(name, str)]
                },
                {
                    "type": "integer",
                     "maximum": len(headers) - 1
                }
            ]
        }
        for i, (name, file) in enumerate(files)
            for headers in [pull_headers(file)]
    }
    # Force levels to be properly parented.
    levels = ['site', 'building', 'system']
    defs['sensor_levels'].update({
        "patternProperties": {
            r'^{}/.*$'.format(re.escape(name)): {
                "properties": {
                    "level": {
                        "not": {
                            "enum": levels[:levels.index(sensor['level'])+1]
                        }
                    }
                }
            }
            for name, sensor in obj['sensors'].items()
                if isinstance(name, str) and isinstance(sensor, dict) and
                    'type' not in sensor and sensor.get('level') in levels
        }
    })


class Schema:
    @property
    def schema(self):
        '''Return a copy of schema with its own copy of 'definitions'.
        '''
        try:
            schema = Schema._sensormap_schema
        except AttributeError:
            path = os.path.join(os.path.dirname(__file__),
                                'sensormap-schema.json')
            with open(path) as file:
                Schema._sensormap_schema = schema = json.load(file)
        copy = schema.copy()
        copy['definitions'] = schema['definitions'].copy()
        return copy

    def validate(self, obj, check_schema=False):
        '''Validate obj against the schema and check reference constraints.

        Returns a dictionary where each key is a tuple to the path of the
        error and each value is a list of errors which occurred at that
        path. On successful validation, None is returned. 
        '''
        # Validate object against schema
        schema = self.schema
        add_instance_constraints(schema, obj)
        if check_schema:
            Draft4Validator.check_schema(schema)
        validator = Draft4Validator(schema)
        try:
            validator.validate(obj)
        except exceptions.ValidationError as e:
            return {tuple(e.path): [e.message]}



if __name__ == '__main__':
    schema = Schema()
    obj = json.load(open(sys.argv[1]))
    errors = schema.validate(obj, check_schema=True)
    if errors:
        for path, msg in errors.items():
            print('{}: {}'.format(''.join('[{!r}]'.format(n) for n in path), msg))
