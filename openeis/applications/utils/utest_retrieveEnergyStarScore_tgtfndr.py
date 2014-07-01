"""Unit test :mod:`retrieveEnergyStarScore_targetFinder`"""


#--- Provide accesss
#
import os
import gen_xml_tgtfndr as gxml
import retrieveEnergyStarScore_tgtfndr as rtgf

#--- Assemble payload.
#
bldgMetaData = dict()
#
bldgMetaData['bldg-name'] = 'BLDG 90'
bldgMetaData['zipcode'] = str(10001)
bldgMetaData['function'] = 'Office'
bldgMetaData['floor-area'] = str(123456)
bldgMetaData['year-built'] = str(2000)
#
energyUseList = [['Natural Gas','kBtu (thousand Btu)',str(121300)],
                 ['Electric','kWh (thousand Watt-hours)',str(156000)]]

filepath = os.path.join(os.getcwd(),'z_targetFinder_xml')
targetFinder_xml = gxml.gen_xml_targetFinder(bldgMetaData,energyUseList,filepath)
PMMetrics = rtgf.retrieveScore(targetFinder_xml)

assert ('designScore' in PMMetrics.keys())
assert (PMMetrics['designScore'][0].isdigit()) 