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
