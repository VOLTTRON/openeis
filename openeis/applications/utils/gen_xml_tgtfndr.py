"""Fill for Target Finder XML template replacement."""


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
