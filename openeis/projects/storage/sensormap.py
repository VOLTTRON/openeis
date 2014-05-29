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
