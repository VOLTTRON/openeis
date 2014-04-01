'''
Created on Mar 31, 2014

@author: D3M614
'''
import json

with open("hastack_units.txt") as parser:
    units = {}
    current_unit = None
    
    for line in parser:
        # blank line between each of the units
        if line.strip() == "":
            current_unit = None
            continue
        
        if current_unit == None:
            current_unit = line.strip()[2:-2].strip()
            units[current_unit] = {}
            units[current_unit]['name'] = current_unit
            units[current_unit]['values'] = []
            continue
        
        units[current_unit]['values'].append(line.strip())
        

#with open("units.json") as writeJson:

print(json.dumps(units, sort_keys=True, indent=4))
    
