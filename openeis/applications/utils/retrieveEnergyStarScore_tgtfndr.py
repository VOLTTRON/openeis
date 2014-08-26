"""
Retrieves the Portfolio Manager Energy Star score using targetFinder.

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


#--- Provide access.
#
import urllib.request
import xml.dom.minidom
import xml.etree.ElementTree as ET


def retrieveScore(targetFinderData):
    """
    Given property characteristics in XML format access Portfolio Manager
    targetFinder webservices and retrieve the PM designScore.


    **Args:**

    - *targetFinderData*, XML-format string of the characteristics of a
       property or building.

    **Returns:**

    - *PMMetrics*, dictionary of PM metrics retrieved from targetFinder
       web services. The values returned is a list with the calculated value
       and the unit of measurement.

    **Notes:**

    - The purpose of targetFinder is having to do a single PUSH call instead of
      multiple calls with different XML files. This web service does not save
      property data.
    - targetFinder does not require login information.
    - Missing values in `propertyUses` tag are filled with ENERGY STAR default values.
      The only propertyUse information in this code is the `totalGrossFloorArea`.
    """
    #
    assert ( type(targetFinderData) == str)
	# NOTE: When testing new features in OpenEIS or in Energy Star use the
    # URL for the test environment. Production versions of the code
    # should use live environment.
    url = 'https://portfoliomanager.energystar.gov/wstest/targetFinder' # Test Environment
    # url = 'https://portfoliomanager.energystar.gov/ws/targetFinder' # Live Environment

    #--- Assemble opener.
    #
    debugHandler = urllib.request.HTTPSHandler(debuglevel=0)

    #--- Assemble request.
    #
    opener = urllib.request.build_opener(debugHandler)
    targetFinderData_bin = targetFinderData.encode('utf-8')
    request = urllib.request.Request(url, targetFinderData_bin, headers={'Content-Type': 'application/xml'})
    assert ( request.get_method() == 'POST' )

    try:
        response = opener.open(request)
        xmlRoot = ET.fromstring(response.read())
        metrics = dict()
        for val in xmlRoot.iter('metric'):
            metrics[val.get('name')] = (val.findtext('value'),val.get('uom'))
        return (metrics)
    except urllib.request.HTTPError as err:
        print ('http error')
        print ('code is ', err.code)
        print ('reason is', err.reason)
        print (str(err))
        print (err.read())
    except urllib.request.URLError as err:
        print ('url error')
        print (err.args)
        print (err.reason)
        return (None)

    #
    # End :func:`retrieveEnergyStarScore_targetFinder`.
