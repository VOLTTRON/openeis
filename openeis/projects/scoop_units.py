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
        
        print(line.strip())
        fields = line.strip().split(',')
        
        if len(fields) == 1:
            key = value = fields[0]
        else:
            key = fields[0]
            value = fields[1]
                    
        other = fields[2:]
        if len(other) == 0:
            other = None
        else:
            if len(other) == 1:
                other = other[0]
        
        # Only include other keyword if there are other items in the list  
        if other:
            units['units'][current_unit].append({"key": key,
                                                 "value": value,
                                                 "other": other
                                                 })
        else:
            units['units'][current_unit].append({"key": key,
                                                 "value": value
                                                 })
        

with open("units.json", 'w') as writeJson:
    json.dump(units, writeJson, sort_keys=True, indent=4)
    
