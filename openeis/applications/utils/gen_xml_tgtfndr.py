"""
Fill for Target Finder XML template replacement.


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
import os
import sys
import io
import datetime as dto
import numpy as np
#
sys.path.append(os.path.dirname(__file__))
#
import copy_file as fw_copy
import fill_template as fw_fill
#


def gen_xml_targetFinder(bldgMetaData, energyUseList,
                     xmlDirName):
    """
    Fills in the XML template required for Target Finder.

    **Args:**

    - *bldgMetaData*, dictionary of building properties.
    - *energyUseList*, list of calculated yearly building energy use.
    - *xmlDirName*, string where xml files are written.

    **Returns:**

    - *xmlStrings*, list of strings that are XML-formatted that contains
      ``propertyData``, ``propertyUseData``, ``meterData``, and
      ``meterConsumptionData``.

    **Notes:**

    - Energy use is an annual total for each fuel type.
    - This fcn also creates separate XML files that the user can upload
      to the Portfolio Manager web-based GUI.
    """
    #
    # Check inputs
    assert ( type(bldgMetaData) == dict )
    assert ( type(energyUseList) == list )
    #
    xmlTemplateDirName = os.path.abspath(os.path.join(os.path.dirname(__file__), 'xml_template'))
    if( not os.path.isdir(xmlTemplateDirName) ):
        raise Exception('Expecting to find XML template directory at {' +xmlTemplateDirName +'}')
    #
    # Initialize xml replacements
    #
    xml_replacements = dict()
    xml_replacements['{:property-name:}'] = bldgMetaData['bldg-name']
    xml_replacements['{:property-zipcode:}'] = bldgMetaData['zipcode']
    xml_replacements['{:property-floor-area:}'] = bldgMetaData['floor-area']
    xml_replacements['{:property-year-built:}'] = bldgMetaData['year-built']

    if 'type' not in bldgMetaData.keys():
        converted_types = translateBldgType(bldgMetaData['function'])
        xml_replacements['{:property-function:}'] = converted_types[0]
        xml_replacements['{:property-type:}'] = converted_types[1]
    else:
        xml_replacements['{:property-function:}'] = bldgMetaData['function']
        xml_replacements['{:property-type:}'] = bldgMetaData['type']
    #
    fw_copy.ensureDir(xmlDirName)
    outFileFullName = os.path.join(xmlDirName, 'targetFinder.xml')
    outFile = open(outFileFullName, 'w')
    #
    #
    # Generate designEntry replacement. The XML template is separated from main template to allow
    # for multiple energy uses.
    xml_replacements['{:design-entry-text:}'] = __write_estimatedEnergyTag(energyUseList,xmlTemplateDirName)
    #
    # Generate targetFinder XML
    outDataStr = io.StringIO()
    __fill_xml(xmlTemplateDirName, 'targetFinder.xml', xml_replacements, outDataStr)
    xmlDataStrings = outDataStr.getvalue()
    #
    outFile.write(xmlDataStrings)
    outFile.close()
    #
    return ( xmlDataStrings )
	#
	# End :func:`gen_portmngr_xml`.

def __write_estimatedEnergyTag(energyUseList,xmlTemplateDirName):
    """Generate the estimatedEnergyList tag of the XML file."""

    assert (len(energyUseList) > 0)
    #
    outDataStr = io.StringIO()
    designEntry_text = ''
    design_replacements = dict()
    #
    for energyUse in energyUseList:
        design_replacements['{:energy-type:}'] = energyUse[0]
        design_replacements['{:energy-unit:}'] = energyUse[1]
        design_replacements['{:energy-usage:}'] = energyUse[2]
        __fill_xml(xmlTemplateDirName, 'designEntry.xml', design_replacements, outDataStr)
    designEntry_text = outDataStr.getvalue()

    return (designEntry_text)
    #
    # End :func:`write_estimatedEnergyList`.
	
def __fill_xml(templateDirName, templateFileName, replacements,
    outFile):
    """
    Fill an XML template file.
    """
    #
    # TODO: Figure out a more elegant way to flag unmatched replacement strings,
    # than just printing.  Don't particularly want to raise an exception-- that
    # seems kind of drastic in this context.
    #
    with open(os.path.join(templateDirName, templateFileName)) as templateFile:
        unmatched = fw_fill.fillTemplate_strKey(templateFile,
            fw_fill.PATTERN_BRACE_COLON, replacements,
            outFile)
        if( unmatched is not None ):
            print ('Template file',templateFileName, 'requires replacement values for the following patterns:')
            for pattern, lineNo in unmatched.iteritems():
                print ('-- Pattern:',pattern, '(found on line', lineNo, 'of template file)')
    #
    # End :func:`_fill_xml`.

def translateBldgType(buildingTypeMenu):
        """Translates the building type from options to XML formatted."""
        #
        if buildingTypeMenu == 'Bank Branch':
            buildingFcnXML = 'Bank Branch'
            buildingTypeXML = 'bankBranch'
        elif buildingTypeMenu == 'Barracks':
            buildingFcnXML = 'Barracks'
            buildingTypeXML = 'barracks'
        elif buildingTypeMenu == 'Bank or Financial Institution':
            buildingFcnXML = 'Financial Office'
            buildingTypeXML = 'financialOffice'
        elif buildingTypeMenu == 'K-12 School':
            buildingFcnXML = 'K-12 School'
            buildingTypeXML = 'k12School'
        elif buildingTypeMenu == 'College/University':
            buildingFcnXML = 'College/University'
            buildingTypeXML = 'collegeUniversity'
        elif buildingTypeMenu == 'Supermarket/Grocery Store':
            buildingFcnXML = 'Supermarket/Grocery Store'
            buildingTypeXML = 'supermarket'
        elif buildingTypeMenu == 'Wholesale Club/Supercenter':
            buildingFcnXML = 'Wholesale Club/Supercenter'
            buildingTypeXML = 'wholesaleClubSupercenter'
        elif buildingTypeMenu == 'Hospital (General Medical and Surgical)':
            buildingFcnXML = 'Hospital (General Medical &amp; Surgical)'
            buildingTypeXML = 'hospital'
        elif buildingTypeMenu == 'Medical Office':
            buildingFcnXML = 'Medical Office'
            buildingTypeXML = 'medicalOffice'
        elif buildingTypeMenu == 'Senior Care Community':
            buildingFcnXML = 'Senior Care Community'
            buildingTypeXML = 'seniorCareCommunity'
        elif buildingTypeMenu == 'Hotel':
            buildingFcnXML = 'Hotel'
            buildingTypeXML = 'hotel'
        elif buildingTypeMenu == 'Residence Hall/Dormitory':
            buildingFcnXML = 'Residence Hall/Dormitory'
            buildingTypeXML = 'residenceHallDormitory'
        elif buildingTypeMenu == 'Courthouse':
            buildingFcnXML = 'Courthouse'
            buildingTypeXML = 'courthouse'
        elif buildingTypeMenu == 'House of Worship':
            buildingFcnXML = 'Worship Facility'
            buildingTypeXML = 'worshipFacility'
        elif buildingTypeMenu == 'Retail':
            buildingFcnXML = 'Retail Store'
            buildingTypeXML = 'retail'
        elif buildingTypeMenu == 'Distribution Center':
            buildingFcnXML = 'Distribution Center'
            buildingTypeXML = 'distributionCenter'
        elif buildingTypeMenu == 'Non-Refrigerated Warehouse':
            buildingFcnXML = 'Non-Refrigerated Warehouse'
            buildingTypeXML = 'nonRefrigeratedWarehouse'
        elif buildingTypeMenu == 'Refrigerated Warehouse':
            buildingFcnXML = 'Refrigerated Warehouse'
            buildingTypeXML = 'refrigeratedWarehouse'
        else:
            # Default value
            buildingFcnXML = 'Office'
            buildingTypeXML = 'office'
        #
        return (buildingFcnXML,buildingTypeXML)
        #
        # End :meth:`setMenubuttonText`.
