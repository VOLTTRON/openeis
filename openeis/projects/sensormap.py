import json
import sys

from jsonschema import exceptions, Draft4Validator


# This is the official version 1 schema for sensor map definitions
schema_text = '''
{
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "Schema for input data to sensor map definition.",
    "type": "object",
    "required": ["version", "files", "sensors"],
    "properties": {
        "version": {
            "type": "integer",
            "enum": [1]
        },
        "files": {
            "type": "object",
            "minProperties": 1,
            "additionalProperties": {
                "type": "object",
                "required": ["signature", "timestamp"],
                "properties": {
                    "signature": {
                        "type": "object",
                        "required": ["headers"],
                        "properties": {
                            "headers": {
                                "type": "array",
                                "items": {"type": ["string", "null"]},
                                "minItems": 2
                            }
                        },
                        "additionalProperties": false
                    },
                    "timestamp": {
                        "type": "object",
                        "required": ["columns", "format"],
                        "properties": {
                            "columns": {
                                "type": "array",
                                "items": {
                                    "oneOf": [
                                        {"type": "string"},
                                        {"type": "integer", "minimum": 0}
                                    ]
                                },
                                "minItems": 1,
                                "uniqueItems": true
                            },
                            "format": {"type": "string"}
                        },
                        "additionalProperties": false
                    },
                    "extra": {"type": "object"}
                },
                "additionalProperties": false
            }
        },
        "sensors": {
            "type": "object",
            "patternProperties": {
                "^([^/]+)(/[^/]+)*$": {
                    "oneOf": [
                        {
                            "type": "object",
                            "required": ["level"],
                            "properties": {
                                "level": {"type": "string"},
                                "attributes": {"type": "object"},
                                "extra": {"type": "object"}
                            },
                            "additionalProperties": false
                        },
                        {
                            "type": "object",
                            "required": ["type", "unit", "file", "column"],
                            "properties": {
                                "type": {"type": "string"},
                                "unit": {"type": ["string", "null"]},
                                "file": {"type": "string"},
                                "column": {
                                    "oneOf": [
                                        {"type": "string"},
                                        {"type": "integer", "minimum": 0}
                                    ]
                                },
                                "extra": {"type": "object"}
                            },
                            "additionalProperties": false
                        }
                    ]
                }
            },
            "minProperties": 1,
            "additionalProperties": false
        },
        "extra": {"type": "object"}
    },
    "additionalProperties": false
}
'''

schema = json.loads(schema_text)


def validate(obj):
    '''Validate obj against the schema and check reference constraints.

    Returns a dictionary where each key is a tuple to the path of the
    error and each value is a list of errors which occurred at that
    path. An empty dictionary indicates that the object validated
    successfully.
    '''
    errors = {}
    def append_error(path, msg):
        err_list = errors.get(path)
        if err_list is None:
            errors[path] = err_list = []
        err_list.append(msg)

    # Validate object against schema
    validator = Draft4Validator(schema)
    try:
        validator.validate(obj)
    except exceptions.ValidationError as e:
        append_error(tuple(e.path), e.message)
        return errors

    files = obj['files']
    # Check timestamp columns of each file against the headers
    for filename, file in files.items():
        headers = file['signature']['headers']
        ts = file['timestamp']
        for i, col in enumerate(ts['columns']):
            if ((col not in headers)
                    if isinstance(col, str) else col >= len(headers)):
                append_error(('files', filename, 'timestamp', 'columns', i),
                        'References undefined column: {!r}'.format(col))

    used_files = set()
    for name, sensor in obj['sensors'].items():
        # Check sensor for valid file and column
        if 'type' in sensor:
            filename = sensor['file']
            try:
                file = files[filename]
            except KeyError:
                append_error(('sensors', name, 'file'),
                        'References undefined file: {!r}'.format(filename))
            else:
                used_files.add(filename)
                headers = file['signature']['headers']
                col = sensor['column']
                if ((col not in headers)
                        if isinstance(col, str) else col >= len(headers)):
                    append_error(('sensors', name, 'column'),
                            'References undefined column: {!r}'.format(col))
            #XXX: Check type and unit against possible values
        else:
            #XXX: Check level against possible values
            pass

    # Check for defined but unused files
    for filename in set(files) - used_files:
        append_error(('files',), 'Defines unused file: {!r}'.format(filename))
    return errors




if __name__ == '__main__':
    Draft4Validator.check_schema(schema)
    obj = json.load(open(sys.argv[1]))
    for path, msg in validate(obj).items():
        print('{}: {}'.format(''.join('[{!r}]'.format(n) for n in path), msg))
