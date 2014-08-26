#!/usr/bin/env  bash
"""
Reformat a JSON fixture file, making it easier to view in a text editor.

This is cosmetic only.  It puts one JSON object on each line, and squeezes out
some of the extra spaces, but it doesn't/shouldn't change content.

Usage:
> python  <name-of-this-script>  name-of-fixture-file  >  name-of-formatted-fixture-file

Copyright (c) 2014, The Regents of the University of California, Department
of Energy contract-operators of the Lawrence Berkeley National Laboratory.
All rights reserved.

1. Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions are met:

   (a) Redistributions of source code must retain the copyright notice, this
   list of conditions and the following disclaimer.

   (b) Redistributions in binary form must reproduce the copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

   (c) Neither the name of the University of California, Lawrence Berkeley
   National Laboratory, U.S. Dept. of Energy nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

2. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
   AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
   DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
   ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
   (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
   LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
   ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
   (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
   THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

3. You are under no obligation whatsoever to provide any bug fixes, patches,
   or upgrades to the features, functionality or performance of the source code
   ("Enhancements") to anyone; however, if you choose to make your Enhancements
   available either publicly, or directly to Lawrence Berkeley National
   Laboratory, without imposing a separate written license agreement for such
   Enhancements, then you hereby grant the following license: a non-exclusive,
   royalty-free perpetual license to install, use, modify, prepare derivative
   works, incorporate into other computer software, distribute, and sublicense
   such enhancements or derivative works thereof, in binary and source code
   form.

NOTE: This license corresponds to the "revised BSD" or "3-clause BSD" license
and includes the following modification: Paragraph 3. has been added.
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
