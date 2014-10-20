"""
Retrieves the Portfolio Manager Energy Star score using targetFinder.


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

    metrics = dict()
    try:
        response = opener.open(request)
        xmlRoot = ET.fromstring(response.read())
        metrics['status'] = 'success'
        for val in xmlRoot.iter('metric'):
            metrics[val.get('name')] = (val.findtext('value'),val.get('uom'))
    except urllib.request.HTTPError as err:
        print ('http error')
        print ('code is ', err.code)
        print ('reason is', err.reason)
        print (str(err))
        print (err.read())
        metrics['status'] = 'HTTP Error'
        metrics['reason'] = err.reason
    except urllib.request.URLError as err:
        print ('url error')
        print (err.args)
        print (err.reason)
        metrics['status'] = 'URL Error'
        metrics['reason'] = err.reason
    return (metrics)

    #
    # End :func:`retrieveEnergyStarScore_targetFinder`.
