"""
    Creates the units.json file from the haystack_units.txt input file.
"""
import json

OUTPUT_FILE = 'static/projects/json/units.json'

with open('haystack_units.txt') as builder:
    groups = {}
    current_group = None
    for line in builder:
        line = line.strip()
        if len(line) == 0:
            continue
        #print(line)
        
        if line[:2] == '--':
            current_group = line[2:-2].strip()
            groups[current_group] = {}
        else:
            fields = line.split(',')
            
            if len(fields) == 1:
                groups[current_group][fields[0]]={'key': fields[0],
                                              'value': fields[0]}
            else:
                groups[current_group][fields[0]]={'key': fields[0],
                                                  'value': fields[1]}
                if len(fields) > 2:
                    groups[current_group][fields[0]]['other'] = ','.join(fields[2:])
                
    json.dump(groups, open(OUTPUT_FILE, 'w'), sort_keys=True, indent=4, separators=(',', ':'))