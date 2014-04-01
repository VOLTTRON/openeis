'''
Created on Mar 31, 2014

@author: D3M614
'''
import json

with open("hastack_units.txt") as parser:
    units = {'units': {}}
    current_unit = None
    
    for line in parser:
        # blank line between each of the units
        if line.strip() == "":
            current_unit = None
            continue
        
        if current_unit == None:
            current_unit = line.strip()[2:-2].strip()
            #units['units'][current_unit] = {}
            units['units'][current_unit] = []
            continue
        
        units['units'][current_unit].append(line.strip())
        

with open("units.json", 'w') as writeJson:
    json.dump(units, writeJson, sort_keys=True, indent=4)
    
