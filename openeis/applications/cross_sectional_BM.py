"""
Cross-sectional benchmarking: retrieve an ENERGY STAR score from EPA's Target Finder.

Shows the building performance relative to a comparable peer group.


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


from openeis.applications import DriverApplicationBaseClass, InputDescriptor,  \
    OutputDescriptor, ConfigDescriptor
from openeis.applications import reports
import logging
from django.db.models import Sum
from openeis.applications.utils.gen_xml_tgtfndr import gen_xml_targetFinder
from openeis.applications.utils.retrieveEnergyStarScore_tgtfndr import retrieveScore
from openeis.applications.utils import conversion_utils as cu


class Application(DriverApplicationBaseClass):

    def __init__(self, *args,
                    building_sq_ft=-1,
                    building_year_constructed=-1,
                    building_name=None,
                    building_function='Office',
                    building_zipcode=None,
                    **kwargs):
        #Called after app has been staged
        """
        When applications extend this base class, they need to make
        use of any kwargs that were setup in config_param
        """
        super().__init__(*args,**kwargs)

        self.default_building_name_used = False

        if building_sq_ft <= 0:
            raise Exception("Building floor area must be positive")
        if building_year_constructed < 0:
            raise Exception("Invalid input for building_year_constructed")
        if building_name is None:
            building_name = "None supplied"
            self.default_building_name_used = True
        if len(building_zipcode) < 5:
            raise Exception("Invalid input for building_zipcode")

        self.sq_ft = building_sq_ft
        self.building_year = building_year_constructed
        self.building_name = building_name
        #TODO: Provide list of Portfolio Manager valid building types.
        self.building_function = building_function
        self.building_zipcode = building_zipcode

    @classmethod
    def get_app_descriptor(cls):    
        name = 'Cross-Sectional Benchmarking'
        desc = 'Cross-sectional benchmarking is used to compare a building’s\
                energy efficiency relative to a peer group. It is the first step\
                in determining if performance is good or poor, and it shows\
                how much potential there is to improve the building’s efficiency. '
        return ApplicationDescriptor(app_name=name, description=desc)

    @classmethod
    def get_config_parameters(cls):
        #Called by UI.

        buildingTypeList = ('Bank Branch',
                    'Bank or Financial Institution',
                    'Barracks',
                    'Courthouse',
                    'Distribution Center',
                    'Hospital (General Medical and Surgical)',
                    'Hotel',
                    'House of Worship',
                    'K-12 School',
                    'Medical Office',
                    'Non-Refrigerated Warehouse',
                    'Office',
                    'Refrigerated Warehouse',
                    'Residence Hall/Dormitory',
                    'Retail Store',
                    'Senior Care Community',
                    'Supermarket/Grocery Store',
                    'Wholesale Club/Supercenter')


        return {
            "building_sq_ft": ConfigDescriptor(float, "Square footage", value_min=5000),
            "building_year_constructed": ConfigDescriptor(int, "Construction Year", value_min=1800, value_max=2014),
            "building_name": ConfigDescriptor(str, "Building Name", optional=True),
            "building_function": ConfigDescriptor(str, "Building Function", value_list=buildingTypeList),
            "building_zipcode": ConfigDescriptor(str, "Building Zipcode")
            }


    @classmethod
    def required_input(cls):
        #Called by UI
        return {
            'load':InputDescriptor('WholeBuildingElectricity','Building Load'),
            'natgas':InputDescriptor('WholeBuildingGas', 'Natural Gas usage')
            }


    @classmethod
    def output_format(cls, input_object):
        # Called when app is staged
        """
        Output is the year with its respective load and natural gas amounts
        aggregated over the year.
        """
        topics = input_object.get_topics()
        print (topics)
        load_topic = topics['load'][0]
        load_topic_parts = load_topic.split('/')
        output_topic_base = load_topic_parts[:-1]
        metric_name_topic = '/'.join(output_topic_base+['crossection', 'metric_name'])
        value_topic = '/'.join(output_topic_base+['crossection', 'value'])

        output_needs = {
            'CrossSectional_BM': {
                'Metric Name':OutputDescriptor('string', metric_name_topic),
                'Value':OutputDescriptor('string', value_topic)
                }
            }
        return output_needs


    def reports(self):
        #Called by UI to create Viz
        """Describe how to present output to user
        Display this viz with these columns from this table


        display_elements is a list of display objects specifying viz and columns
        for that viz
        """
        report = reports.Report('Cross Sectional Benchmarking, \
                                 ENERGY STAR Portfolio Manager')

        text_blurb = reports.TextBlurb(text="Determine the performance of your \
                                            building relative to a comparable \
                                            peer group using Portfolio Manager .")
        report.add_element(text_blurb)


        column_info = (('Value', 'ENERGY STAR Score'),)

        espmscore_table = reports.Table('CrossSectional_BM',
                                      column_info,
                                      title='Cross-Sectional Benchmarking')

        report.add_element(espmscore_table)

        text_guide = reports.TextBlurb(text="Scores of 75 or higher qualify for ENERGY STAR Label.\
                                             Scores of 50 indicate average energy performance.")
        report.add_element(text_guide)

        report_list = [report]

        return report_list


    def execute(self):
        #Called after User hits GO
        """Outputs the ENERGY Star Score from Target Finder API"""
        #NOTE: Connection check happens after data is formatted into XML and
        # sent into the web service request.
        self.out.log("Starting application: cross-sectional benchmarking.", logging.INFO)

        self.out.log("Querying the database for model parameters.", logging.INFO)
        bldgMetaData = dict()
        bldgMetaData['floor-area']  = self.sq_ft
        bldgMetaData['year-built']  = self.building_year
        bldgMetaData['bldg-name']   = self.building_name
        bldgMetaData['function']    = self.building_function
        bldgMetaData['zipcode']     = self.building_zipcode

        self.out.log("Querying the database for most recent year of energy load.", logging.INFO)
        # NOTE: Hourly values are preferred to make calculations easier.
        # TODO: The caveat above must be made stronger.  Aggregating by summing
        #   only converts, e.g., [kW] to [kWh] for hourly observations.
        #   Similar problem for gas data.
        # TODO: The query here presumably groups by calendar year.  Need to check
        #   whether application actually wants a year's worth of data, looking
        #   backward from most recent observation.
        load_by_year = self.inp.get_query_sets('load', group_by='year',
                                               group_by_aggregation=Sum,
                                               exclude={'value':None},
                                               wrap_for_merge=True)
        gas_by_year = self.inp.get_query_sets('natgas', group_by='year',
                                              group_by_aggregation=Sum,
                                              exclude={'value':None},
                                              wrap_for_merge=True)

        merge_load_gas = self.inp.merge(load_by_year, gas_by_year)

        # Convert the generator to a list that can be indexed.
        merge_data_list = []
        for item in merge_load_gas:
            merge_data_list.append((item['time'], item['load'][0], item['natgas'][0]))

        recent_record = merge_data_list[len(merge_data_list)-1]

        self.out.log("Getting unit conversions.", logging.INFO)
        base_topic = self.inp.get_topics()
        meta_topics = self.inp.get_topics_meta()

        load_unit = meta_topics['load'][base_topic['load'][0]]['unit']
        self.out.log(
            "Convert loads from [{}] to [kW]; integration will take to [kWh].".format(load_unit),
            logging.INFO
            )
        load_convertfactor = cu.getFactor_powertoKW(load_unit)

        natgas_unit = meta_topics['natgas'][base_topic['natgas'][0]]['unit']
        self.out.log(
            "Convert natgas from [{}] to [kBtu/hr]; integration will take to [kBtu].".format(natgas_unit),
            logging.INFO
            )
        natgas_convertfactor = cu.getFactor_powertoKBtu_hr(natgas_unit)

        #TODO: Convert values to units that are PM Manager valid values.
        energyUseList = [['Electric','kWh (thousand Watt-hours)',int(recent_record[1]*load_convertfactor)],
                         ['Natural Gas','kBtu (thousand Btu)',int(recent_record[2]*natgas_convertfactor)]]

        self.out.log("Generate XML-formatted data to pass data to the webservice.", logging.INFO)
        targetFinder_xml = gen_xml_targetFinder(bldgMetaData,energyUseList,'z_targetFinder_xml')

        self.out.log("Function that sends a URL Request with ENERGY STAR web server.", logging.INFO)
        PMMetrics = retrieveScore(targetFinder_xml)

        self.out.log("Compile report table.", logging.INFO)
        if PMMetrics['status'] == 'success':
            self.out.log('Analysis successful', logging.INFO)
            self.out.insert_row('CrossSectional_BM', {
                'Metric Name': 'Target Finder Score',
                'Value': str(PMMetrics['designScore'][0])
                })
        else:
            self.out.log(str(PMMetrics['status'])+'\nReason:\t'+str(PMMetrics['reason']), logging.WARNING)
            self.out.insert_row('CrossSectional_BM', {
                'Metric Name': 'Target Finder Score',
                'Value': 'Check log for error.'
                })
