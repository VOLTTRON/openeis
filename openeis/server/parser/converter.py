# -*- coding: utf-8 -*- {{{
# vim: set fenc=utf-8 ft=python sw=4 ts=4 sts=4 et:
#
# Copyright (c) 2014, Battelle Memorial Institute
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.
#
#
# This material was prepared as an account of work sponsored by an
# agency of the United States Government.  Neither the United States
# Government nor the United States Department of Energy, nor Battelle,
# nor any of their employees, nor any jurisdiction or organization
# that has cooperated in the development of these materials, makes
# any warranty, express or implied, or assumes any legal liability
# or responsibility for the accuracy, completeness, or usefulness or
# any information, apparatus, product, software, or process disclosed,
# or represents that its use would not infringe privately owned rights.
#
# Reference herein to any specific commercial product, process, or
# service by trade name, trademark, manufacturer, or otherwise does
# not necessarily constitute or imply its endorsement, recommendation,
# or favoring by the United States Government or any agency thereof,
# or Battelle Memorial Institute. The views and opinions of authors
# expressed herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY
# operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830
#
#}}}

# Convert GreenButton xml to csv
import csv
import sys
from datetime import date
from datetime import datetime
from time import strftime
from xml.etree.ElementTree import parse
from xml.etree.ElementTree import iterparse
# import xml.etree.cElementTree as ET
# from xml.etree import ElementTree
# from xml.etree.ElementTree import register_namespace
#
# The difference is this:
# from elementtree import ElementTree
# Versus this:
# import xml.etree.ElementTree as ET
# note that there is also a C implementation, which is more efficient:
# import xml.etree.cElementTree as ET
    
def Convert(input_file, output_file):
    """
    input_file: a file object from which the xml data is parsed
    outpt_file: a file object to which the parsed rows will be written
    """
    
    # Note: 'lineterminator' defaults to '\r\n', which injects extra newlines into excel
    csv.register_dialect('csvdialect', delimiter=',', lineterminator='\n', quoting=csv.QUOTE_NONNUMERIC)
    # writer = csv.writer(output_type, 'csvdialect')
    
    # Set up a namespace for the various xml namespaces in the document.
    # The namespace is used in calls to find and findall, in order to avoid
    # prepending every search for a given node with that node's full xml namespace. 
    ns = {
        'Atom': "http://www.w3.org/2005/Atom", 
        'espi': "http://naesb.org/espi", 
        'xsi:schemaLocation': "http://naesb.org/espi espiDerived.xsd",
        'xmlns:xsi': "http://www.w3.org/2001/XMLSchema-instance"
    }
    
    headerDict = {
        'start' : 'Start Timestamp',
        'duration' : 'Duration (Seconds)',
        'end': 'End Timestamp',
        'cost': "Cost",
        'value' : 'Value',
        'ReadingQuality': 'Reading Quality'
    }
    
    prefixes = {
        '0': None,        #x10^0  ('0': 'None',)
        '1': 'deca',    #=x10^1',
        '2': 'hecto',   #=x100',
        '-3': 'mili',   #=x10-3',
        '3': 'kilo',    #=x1000',
        '6': 'Mega',    #=x106',
        '-6': 'micro',  #=x10-6',
        '9': 'Giga'     #=x109'
    }
    
    # Parse the xml tree and get the timezone offset node.
    # This timezone offset was necessary because I discovered that the converted time was
    # different from the time in a comment field of each node. 
    # I later found that the inherent offset plus the timezone offset was exactly 8 hours, 
    # which meant the time is UTC - a much simpler conversion.
    tree = parse(input_file)
    root = tree.getroot()
    tzOffset = get_child_node_text(root, ns, 'tzOffset')
    powerOfTenMultiplier = get_child_node_text(root, ns, "powerOfTenMultiplier")
    
    currencyType = get_currency_type(root, ns)
    prefix = None
    if powerOfTenMultiplier in prefixes:
        prefix = prefixes[powerOfTenMultiplier]
    uomType = get_uom_type(root, ns, prefix)
    
    count = 0
    startDateHeader = 'Start Timestamp'
    durationHeader = 'Duration (Seconds)'
    endDateHeader = 'End Timestamp'
    costHeader = 'Cost - {0}'.format(currencyType)
    valueHeader = 'Value - {0}'.format(uomType)
    readingQualityHeader = 'Reading Quality'
    
    headerDict['cost'] = '{0} - {1}'.format(headerDict['cost'], currencyType)
    headerDict['value'] = '{0} - {1}'.format(headerDict['value'], uomType)
    
    headers_found = build_header_list(root, ns)
    headers_used = []
    for header in headers_found:
        if header in headerDict:
            print("\'{0}\', \'{1}\'".format(header, headerDict[header]))
            headers_used.append(headerDict[header])
        else:
            print(header)
            headers_used.append(header)
    
    headers_used.append(endDateHeader)
    
    header_row = [startDateHeader, durationHeader, endDateHeader, costHeader, valueHeader, readingQualityHeader]
    writer = csv.writer(output_file, 'csvdialect')
    writer.writerow(header_row)
    # writer.writerow(headers_used)
            
    # loop through every node in the input file
    # for (event, node) in iterparse(input_file, events=['end']):
    for node in root.iter():
        node_tag = node.tag.split('}', 1)[1]
        node_attributes = node.attrib
        node_text = node.text
        if node_tag == 'entry':
                print(node_tag, ', ', node_attributes, ', ', node_text)
                
                for child in node.iter(): 
                    child_tag = split_namespace(child.tag)
                    
                    # Get the retail customer
                    if child_tag == 'link' and 'rel' in child.attrib and child.attrib['rel'] == 'self':
                        link_string = child.attrib['href']
                        retailCustomer = link_string.split('/', 6)[1]  #This won't work if RetailCustomer isn't the first part of the string-need to improve the split
                        # print("retailCustomer: \"{0}\"".format(retailCustomer))
                        
                    # Error, but do not break out of the loop or change retail customer
                    elif child_tag == 'link' and 'rel' not in child.attrib:
                        print(child_tag, child.attrib, child.text)
                    
                    # Process row data for IntervalReading nodes
                    elif child_tag == 'IntervalReading':
                        process_row(child, writer, ns)
                        
                count += 1
                print('\n\ncount: ',count)
    
    print(strftime("%Y-%m-%d %H:%M:%S"))  #use this in the filename later
    

def process_row(node, writer, ns):
    """
    method to process an xml IntervalReading node and write an individual row
    parameters: the IntervalReading node, the csv writer, and a list of namespaces
    returns: nothing 
    """
    
    intervalDate = get_child_node_text(node, ns, 'start')
    intervalAdjusted = int(intervalDate)
    formattedDate = datetime.utcfromtimestamp(intervalAdjusted)
    
    intervalDuration = get_child_node_text(node, ns, "duration")
    
    if intervalDuration == "":
        endDate = formattedDate
    else:
        endDate = datetime.utcfromtimestamp(intervalAdjusted + int(intervalDuration))
    
    intervalCost = get_child_node_text(node, ns, "cost")
    
    # An examination of the espi schema shows IntervalCost is in hundred-thousandths of the given currency type.
    # Ex: Assuming USD, if IntervalCost == 2585 this actually means 0.02585 USD, because 2585/100000 = 0.02585
    if intervalCost != None and intervalCost != '' and int(intervalCost) != 0:
        intervalCost = int(intervalCost) / 100000   
    
    intervalReadingQuality = get_child_node_text(node, ns, "ReadingQuality")
    
    # intervalValue = node.find('./{http://naesb.org/espi}value').text  # the url way
    intervalValue = get_child_node_text(node, ns, "value", './{http://naesb.org/espi}')    # The url way
                        
    print("Interval Date: {0}\nFormatted Date: {1}".format(intervalDate, formattedDate))
    print("Interval Duration: {0}\nInterval Cost: {1}".format(intervalDuration, intervalCost))
    print("Interval Reading Quality: {0}\nIntervalValue: {1}".format(intervalReadingQuality, intervalValue))
                        
    row = [formattedDate, intervalDuration, endDate, intervalCost, intervalValue, intervalReadingQuality]
    writer.writerow(row)
    
    
def build_header_list(root, ns):
    """
    Method to build a list of column headers for the csv file from the xml nodes.
    Nodes of any name within an IntervalReading node should be accepted
    Parameters: the root node, the list of namespaces
    Returns: A list of strings, each string is a column header
    """
    columnHeaders = []
    intervalReadings = root.findall('.//espi:IntervalReading', namespaces=ns)
    for intervalReading in intervalReadings:
        for child in intervalReading.iter():
            stripped_tag = split_namespace(child.tag)
            text = (child.text.strip() if (child.text != None) else child.text)
            if (stripped_tag not in columnHeaders) and (text != "") and (text != None):
                print(text)
                columnHeaders.append(stripped_tag)

    print(columnHeaders)
    
    return columnHeaders


def get_child_node_text(node, ns, node_tag, node_ns=None):
    """
    method to look up an arbitrary child node of a parent node
    parameters: the parent node, the list of namespaces, the node tag (name)
    optional parameter: node_ns, an optional namespace which is appended to node_tag
    returns: the text of the child node (not attributes), or an empty string ("")
    """
    lookupStr = node_ns+node_tag if (node_ns != None) else './/espi:{0}'.format(node_tag)
    special_tags = ['start', 'tzOffset', 'powerOfTenMultiplier']    # These tags must return an integer
    retVal = ""
    
    childNode = node.find(lookupStr, namespaces=ns)
    if childNode != None:
        retVal = childNode.text
    elif childNode == None and node_tag in special_tags:
        retVal = 0
    
    return retVal

def get_currency_type(root, ns):
    """
    Helper function to get the human-readable currency type
    Parameters: Root node, namespaces
    Returns: A string containing the currency type
    TODO: This list of currencies is a subset of possible world currencies. See full list at http://www.currency-iso.org/dam/downloads/table_a1.xml 
    """
    currencies = {
        '0': 'Not Applicable',
        '36': 'Australian Dollar',
        '124': 'Canadian Dollar',
        '840': 'US Dollar',
        '978': 'Euro'
    }
    
    currencyID = ""
    currencyType = ""
    currencyNode = root.find('.//espi:currency', namespaces=ns)
    if currencyNode != None:
        currencyID = currencyNode.text
    
    if currencyID in currencies:
        currencyType = currencies[currencyID]
    
    return currencyType


def get_retail_customer(node, ns):
    """
    Helper function to get the retail customer
    Parameters: the entry node
    Returns: A string containing the retail customer
    """
    link = node.find('./Atom:link', namespaces=ns)
    retail_customer = link.attrib[1]
    return retail_customer
    
def get_uom_type(root, ns, prefix = None):
    """
    Helper function to get unit of measure (uom)
    Parameters: Root node, namespaces, prefix (a string containing a scientific notation prefix)
    Returns: A string containing the uom
    """
    uomTypes = {
        '0' :'Not Applicable',
        '5' :'A (Current)',
        '29' :'Voltage',
        '31' :'J (Energy joule)',
        '33' :'Hz (Frequency)',
        '38' :'Real power (Watts)',
        '42' :'m3 (Cubic Meter)',
        '61' :'VA (Apparent power)',
        '63' :'VAr (Reactive power)',
        '65' :'Cos? (Power factor)',
        '67' :'V2 (Volts squared)',
        '69' :'A2 (Amp squared)',
        '71' :'VAh (Apparent energy)',
        '72' :'Real energy (Watt-hours)',
        '73' :'VArh (Reactive energy)',
        '106' :'Ah (Ampere-hours / Available Charge)',
        '119' :'ft3 (Cubic Feet)',
        '122' :'ft3/h (Cubic Feet per Hour)',
        '125' :'m3/h (Cubic Meter per Hour)',
        '128' :'US gl (US Gallons)',
        '129' :'US gl/h (US Gallons per Hour)',
        '130' :'IMP gl (Imperial Gallons)',
        '131' :'IMP gl/h (Imperial Gallons per Hour)',
        '132' :'BTU',
        '133' :'BTU/h',
        '134' :'Liter',
        '137' :'L/h (Liters per Hour)',
        '140' :'PA(gauge)',
        '155' :'PA(absolute)',
        '169' :'Therm'
    }
    
    uomType = ""
    uomVal = get_child_node_text(root, ns, './/espi:ReadingType/espi:uom', "")
        
    if uomVal in uomTypes:
        uomType = uomTypes[uomVal]
        # If we have a prefix, prepend it to the unit type, and also prepend it inside 1st open parenthesis, if present.
        if prefix != None:
            uomType = '{0}-{1}'.format(prefix, uomType)
            if uomType.find('(') != -1:
                uomType = uomType.replace('(', '({0}-'.format(prefix), 1)
    
    return uomType


def split_namespace(name):
    '''
    My custom split function, splits name based on trailing brace '}' to remove xml namespace from tag.
    If no trailing brace is found, returns the original string.
    parameter: a single string containing the name to split
    returns: a string containing the tag without the namespace
    '''
    retVal = name
    
    # if name[0] == "{" may not be necessary, however it is nice to check for the opening brace, as it will not be a valid namespace otherwise. The opening brace SHOULD be at the beginning...
    if name[0] == "{":
        temp = name[1:].split('}', 1)
        
        # Check to make sure the name was split, this guards against potentially empty strings
        # previously: child_tag = child.tag.split('}', 1)[1]
        if len(temp) > 1:
            retVal = temp[1]
    
    #return name.split('}', 1)[1]
    return retVal


if __name__ == "__main__":
    '''
    # 
    # Problem: the xml tag comes prepended with {foo}
    # where 'foo' is the full url of the xml namespace.
    # 
    # Example: 
    #   We have: "{http://www.w3.org/2005/Atom}updated"
    #   We want: "updated"
    #
    #   We have: "{http://naesb.org/espi}IntervalReading"
    #   We want: "IntervalReading"
    #
    # Solution: http://bugs.python.org/issue18304
    #
    # Summary: To split xml namespaces, use: 
    # node.tag.split('}', 1)[1]
    # 
    '''
    
    currentTime = datetime.now()
    output_file_name = 'entry-output-{0}_{1}-{2}-{3}.csv'.format(date.today(), currentTime.hour, currentTime.minute, currentTime.second)
    
    if len(sys.argv) < 2:
        filename = 'TestGBDataoneMonthBinnedDailyWCost.xml'
        print("No files passed. Attempting to open test file '{0}'...".format(filename))
        with open(output_file_name, 'w') as output:
            Convert(filename, output)
    
    for input_file in sys.argv[1:]:
        with open(output_file_name, 'w') as output: 
            Convert(input_file, output)

