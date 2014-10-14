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
# import xml.etree.cElementTree as ET
# from xml.etree import ElementTree
from xml.etree.ElementTree import parse
from xml.etree.ElementTree import iterparse
# from xml.etree.ElementTree import register_namespace

# The difference is this:
# from elementtree import ElementTree
# Versus this:
# import xml.etree.ElementTree as ET
# note that there is also a C implementation, which is more efficient:
# import xml.etree.cElementTree as ET
    
def Convert(input_file, output):
    # Note: 'lineterminator' defaults to '\r\n', which injects extra newlines into excel
    csv.register_dialect('csvdialect', delimiter=',', lineterminator='\n', quoting=csv.QUOTE_NONNUMERIC)
    # writer = csv.writer(output_type, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
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
    
    prefixes = {
        '0': "",
        '1': "deca",
        '2': "hecto",
        
        '0': 'None',
        '1': 'deca=x10',
        '2': 'hecto=x100',
        '-3': 'mili=x10-3',
        '3': 'kilo=x1000',
        '6': 'Mega=x106',
        '-6': 'micro=x10-6',
        '9': 'Giga=x109'
    }
    
    for item in ns:
        print(item, ns[item])
        
    for prefix in prefixes:
        print(prefix, prefixes[prefix])
    # raise RuntimeError("Hulloo Zeeba Neighba!")
    
    # Parse the xml tree and get the timezone offset node.
    # This timezone offset was necessary because I discovered that the converted time was
    # different from the time in a comment field of each node. 
    # I later found that the inherent offset plus the timezone offset was exactly 8 hours, 
    # which meant the time is UTC - a much simpler conversion.
    tree = parse(input_file)
    root = tree.getroot()
    tzOffset = root.find('.//espi:tzOffset', namespaces=ns).text
    tzOffset = int(tzOffset)
    powerOfTenMultiplier = root.find('.//espi:ReadingType/espi:powerOfTenMultiplier', namespaces=ns).text
    powerOfTenMultiplier = int(powerOfTenMultiplier)
    
    currencyType = get_currency_type(root, ns)
    uomType = get_uom_type(root, ns)
    print('currencyType',currencyType, sep="")
    print('uomType',uomType)
    # raise ValueError("Something, something, Dark Side.")
    
    print("Power of Ten Multiplier: ",powerOfTenMultiplier)
    print(root.tag)
    print('tzOffset: ', tzOffset)
    
    # We use today's date and also append the count of the current entry to the output file name
    today = date.today()
    count = 0
    startDateHeader = 'Start Date'
    durationHeader = 'Duration (Seconds)'
    endDateHeader = 'End Date'
    costHeader = 'Cost - {0}'.format(currencyType)
    valueHeader = 'Value - {0}'.format(uomType)
    header_row = [startDateHeader, durationHeader, endDateHeader, costHeader, valueHeader]
    writer = csv.writer(output, 'csvdialect')
    writer.writerow(header_row)
            
    # loop through every node in the input file
    for (event, node) in iterparse(input_file, events=['end']):
        # Output file name: 'output-<date>-<count>.csv
        # Example: 'output-2014-08-29-0.csv'
        output_file_name = 'entry-output-{0}-{1}.csv'.format(today, count)
        
        node_tag = node.tag.split('}', 1)[1]
        node_attributes = node.attrib
        node_text = node.text
        if node_tag == 'entry':
            # with open(output_file_name, 'w') as output: 
                # writer = csv.writer(output, 'csvdialect')
                # writer.writerow(header_row)
                print(node_tag, ', ', node_attributes, ', ', node_text)
                
                for child in node.iter(): 
                    # print(child)
                    # child_tag = child.tag.split('}', 1)[1]
                    child_tag = split_namespace(child.tag)
                    
                    # Get the retail customer
                    if child_tag == 'link' and 'rel' in child.attrib and child.attrib['rel'] == 'self':
                        link_string = child.attrib['href']
                        retailCustomer = link_string.split('/', 6)[1]  #This won't work if RetailCustomer isn't the first part of the string-need to improve the split
                        print("retailCustomer: \"{0}\"".format(retailCustomer))
                        
                    # Error, but do not break out of the loop or change retail customer
                    elif child_tag == 'link' and 'rel' not in child.attrib:
                        print(child_tag, child.attrib, child.text)
                    
                    # Process row data for IntervalReading nodes
                    elif child_tag == 'IntervalReading':
                        process_row(child, writer, ns)
                        
                count += 1
                print('\n\ncount: ',count)
    
    print(today)
    print(strftime("%Y-%m-%d %H:%M:%S"))  #use this in the filename later
    

def process_row(node, writer, ns):
    intervalDate = node.find('./espi:timePeriod/espi:start', namespaces=ns).text
    intervalAdjusted = int(intervalDate)
    formattedDate = datetime.utcfromtimestamp(intervalAdjusted)
                        
    intervalDuration = node.find('./espi:timePeriod/espi:duration', namespaces=ns).text
    endDate = datetime.utcfromtimestamp(intervalAdjusted + int(intervalDuration))
                        
    intervalCost = ""
    costNode = node.find('./espi:cost', namespaces=ns)  # the namespace way
    if costNode != None:
        intervalCost = costNode.text
        
        
    intervalValue = node.find('./{http://naesb.org/espi}value').text  # the url way
                        
    print("Interval Date: ", intervalDate)
    print("Formatted Date: ", formattedDate)
    print("Interval Duration: ", intervalDuration)
    print("Interval Cost: ", intervalCost)  #The new test file was missing the interval cost nodes entirely - error handling code corrects this
    print("Interval Value: ", intervalValue)
                        
    row = [formattedDate, intervalDuration, endDate, intervalCost, intervalValue]
    writer.writerow(row)
    
    

def get_currency_type(root, ns):
    """
    Helper function to get the currency type
    Parameters: Root node, namespaces
    Returns: A string containing the currency type
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
    
def get_uom_type(root, ns):
    """
    Helper function to get unit of measure (uom)
    Parameters: Root node, namespaces
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
        '67' :'V� (Volts squared)',
        '69' :'A� (Amp squared)',
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
    
    uomVal = ""
    uomType = ""
    uomNode = root.find('.//espi:ReadingType/espi:uom', namespaces=ns)
    if uomNode != None:
        uomVal = uomNode.text
        
    if uomVal in uomTypes:
        uomType = uomTypes[uomVal]
        
    print(uomType)
    
    return uomType


# My custom split function
# Split name based on trailing brace '}' to remove xml namespace from tag
# Takes a single string parameter and returns a string.
# If no trailing brace is found, returns the original string.
def split_namespace(name):
    retVal = name
    
    # if name[0] == "{" may not be necessary, however it is nice to check for the opening brace, as it will not be a valid namespace otherwise. The opening brace SHOULD be at the beginning...
    if name[0] == "{":
        temp = name[1:].split('}', 1)
        
        # Check to make sure the name was split
        if len(temp) > 1:
            retVal = temp[1]
    
    #return name.split('}', 1)[1]
    return retVal


if __name__ == "__main__":
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
    
    if len(sys.argv) < 2:
        filename = 'TestGBDataoneMonthBinnedDailyWCost.xml'
        print("No files passed. Attempting to open test file '{0}'...".format(filename))
        Convert(filename)
    
    output_file_name = 'entry-output-{0}.csv'.format(date.today())
    for input_file in sys.argv[1:]:
    
        # writer = csv.writer(sys.stdout, quoting=csv.QUOTE_NONNUMERIC)
        # writer = csv.writer(output_type, quoting=csv.QUOTE_NONNUMERIC)
    
        # for (event, node) in iterparse(input_file, events=['start']):
        #     writer.writerow( (node.tag.split('}', 1)[1], node.attrib, node.text) )
        with open(output_file_name, 'w') as output: 
            Convert(input_file, output)

