"""
Reformat a JSON fixture file, making it easier to view in a text editor.

This is cosmetic only.  It puts one JSON object on each line, and squeezes out
some of the extra spaces, but it doesn't/shouldn't change content.

Usage:
> python  <name-of-this-script>  name-of-fixture-file  >  name-of-formatted-fixture-file


Copyright
=========

OpenEIS Algorithms Phase 2 Copyright (c) 2014,
The Regents of the University of California, through Lawrence Berkeley National
Laboratory (subject to receipt of any required approvals from the U.S.
Department of Energy). All rights reserved.

If you have questions about your rights to use or distribute this software,
please contact Berkeley Lab's Technology Transfer Department at TTD@lbl.gov
referring to "OpenEIS Algorithms Phase 2 (LBNL Ref 2014-168)".

NOTICE:  This software was produced by The Regents of the University of
California under Contract No. DE-AC02-05CH11231 with the Department of Energy.
For 5 years from November 1, 2012, the Government is granted for itself and
others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide
license in this data to reproduce, prepare derivative works, and perform
publicly and display publicly, by or on behalf of the Government. There is
provision for the possible extension of the term of this license. Subsequent to
that period or any extension granted, the Government is granted for itself and
others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide
license in this data to reproduce, prepare derivative works, distribute copies
to the public, perform publicly and display publicly, and to permit others to
do so. The specific term of the license can be identified by inquiry made to
Lawrence Berkeley National Laboratory or DOE. Neither the United States nor the
United States Department of Energy, nor any of their employees, makes any
warranty, express or implied, or assumes any legal liability or responsibility
for the accuracy, completeness, or usefulness of any data, apparatus, product,
or process disclosed, or represents that its use would not infringe privately
owned rights.


License
=======

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


#--- Utility fcns.

def pythonObjAsJson(theObj, toFile):
    """
    Write out a Python object to a file, formatted as JSON.
    """
    theType = type(theObj)
    if( theType == dict ):
        pythonDictAsJson(theObj, toFile)
    elif( theType == list ):
        pythonListAsJson(theObj, toFile)
    else:
        toFile.write(json.dumps(theObj, separators=(', ', ':')))


def pythonListAsJson(theList, toFile):
    """
    Write out a Python list to a file, formatted as JSON.
    """
    assert( type(theList) == list )
    toFile.write('[')
    endPrevItem = False
    for item in theList:
        if( endPrevItem ):
            toFile.write(', ')
        else:
            endPrevItem = True
        pythonObjAsJson(item, toFile)
    toFile.write(']')


def pythonDictAsJson(theDict, toFile):
    """
    Write out a Python dictionary to a file, formatted as JSON.
    Assume keys are always strings.
    """
    assert( type(theDict) == dict )

    # Start writing dictionary.
    toFile.write('{')
    endPrevItem = False

    # Get dictionary keys, as a list.
    #   Method keys() returns list in Python 2, iterable view in Python 3.
    theKeys = theDict.keys()
    if( type(theKeys) != list ):
        theKeys = list(theKeys)

    # Run through keys for which have preferred order.
    for prefKey in ['model', 'pk', 'codename', 'name', 'time', 'value']:
        if prefKey in theKeys:
            theKeys.remove(prefKey)
            if( endPrevItem ):
                toFile.write(', ')
            else:
                endPrevItem = True
            toFile.write('"')
            toFile.write(prefKey)
            toFile.write('":')
            pythonObjAsJson(theDict[prefKey], toFile)

    # Run through remaining keys.
    for otherKey in theKeys:
        if( endPrevItem ):
            toFile.write(', ')
        else:
            endPrevItem = True
        assert( type(otherKey) == str )
        toFile.write('"')
        toFile.write(otherKey)
        toFile.write('":')
        pythonObjAsJson(theDict[otherKey], toFile)

    # Finish writing dictionary.
    toFile.write('}')


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
endPrevItem = False
for item in fixtureDat:
    # Finish off the last item if necessary.
    if( endPrevItem ):
        sys.stdout.write(',\n')
    else:
        endPrevItem = True
    # Print this item.
    pythonDictAsJson(item, sys.stdout)

# End the JSON array.
sys.stdout.write('\n]')
