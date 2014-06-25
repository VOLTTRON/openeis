"""Retrieves the Portfolio Manager Energy Star score using targetFinder."""

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