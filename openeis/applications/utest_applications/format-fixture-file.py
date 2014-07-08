#!/usr/bin/env  bash
"""
Reformat a JSON fixture file, making it easier to view in a text editor.

This is cosmetic only.  It puts one JSON object on each line, and squeezes out
some of the extra spaces, but it doesn't/shouldn't change content.

Usage:
> python  <name-of-this-script>  name-of-fixture-file  >  name-of-formatted-fixture-file
"""


import json
import sys


#--- Read the fixture file into a Python data structure.
#
#   This maps:
# - JSON array to Python list
# - JSON object to Python dict
# - JSON string to Python str
# - JSON true to Python True
# - etc.
with open(sys.argv[1]) as fixtureFile:
    fixtureDat = json.load(fixtureFile)

# The fixture should be a JSON array of objects (so a Python list of dictionaries).
assert( type(fixtureDat) == list )


#--- Write the JSON back out.

# Start the JSON array.
sys.stdout.write('[\n')

# Write every Python dictionary as a JSON object, one per line.
endPrevLine = False
for item in fixtureDat:
    assert( type(item) == dict )

    jsonStr = json.dumps(item, separators=(', ', ':'))
    assert( jsonStr[0] == '{' )

    # Put "model" keyword first, if it occurs as a keyword in {item}.
    #   Note "model" may appear as a keyword in a sub-dictionary of {item},
    # so it's dangerous to just pull it out using a grep search of {jsonStr}.
    if 'model' in item:
        modelType = item['model']
        modelStr = ', "model":"' + modelType + '"'
        leftIdx = jsonStr.find(modelStr)
        if( leftIdx>1  and  jsonStr.rfind(modelStr)==leftIdx ):
            # Here, <<, "model":"{modelType}">> appears exactly once in {jsonStr}.
            # Move the "model":"{modelType}" part to beginning of {jsonStr}.
            parts = jsonStr[1:].split(modelStr)
            jsonStr = ''.join([
                '{"model":"',
                modelType,
                '", ',
                ''.join(parts)
                ])

    # Write the JSON object.
    if( endPrevLine ):
        sys.stdout.write(',\n')
    else:
        endPrevLine = True
    sys.stdout.write(jsonStr)

# End the JSON array.
sys.stdout.write('\n]')
