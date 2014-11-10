"""
Longitudinal benchmarking: aggregate electric load and gas usage on a yearly basis.

Shows trends in building performance over time.


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


from openeis.applications import DriverApplicationBaseClass, InputDescriptor, OutputDescriptor, ConfigDescriptor, Descriptor
from openeis.applications import reports
import logging
from django.db.models import Sum
from openeis.applications.utils import conversion_utils as cu

class Application(DriverApplicationBaseClass):

    def __init__(self, *args, building_name=None, **kwargs):
        #Called after app has been staged
        """
        When applications extend this base class, they need to make
        use of any kwargs that were setup in config_param
        """
        super().__init__(*args,**kwargs)

        self.default_building_name_used = False

        #match parameters
        if building_name is None:
            building_name = "None supplied"
            self.default_building_name_used = True

        self.building_name = building_name

    @classmethod
    def get_self_descriptor(cls):    
        name = 'Longitudinal Benchmarking'
        desc = 'Longitudinal benchmarking compares the energy usage\
                in a fixed period for a building, system, or component\
                to a comparable "baseline" or "base" period of the same length,\
                to determine if performance has deteriorated or improved,\
                to set goals for a building or system,\
                or to monitor for unexpectedly high usage.'
        return Descriptor(name=name, description=desc)

    @classmethod
    def get_config_parameters(cls):
        #Called by UI
        #also matches parameters
        return {
            "building_name": ConfigDescriptor(str, "Building Name", optional=True)
            }

    @classmethod
    def required_input(cls):
        #Called by UI
        return {
            'load':InputDescriptor('WholeBuildingElectricity','Building Electicity Load'),
            'natgas':InputDescriptor('WholeBuildingGas', 'Natural Gas Usage')
            }

    @classmethod
    def output_format(cls, input_object):
        # Called when app is staged
        """
        Output is the year with its respective load and natural gas amounts
        aggregated over the year.
        """
        topics = input_object.get_topics()
        base_topic = topics['load'][0]
        load_topic_parts = base_topic.split('/')
        output_topic_base = load_topic_parts[:-1]

        year_topic = '/'.join(output_topic_base+['longitudinalbm', 'time'])
        load_topic = '/'.join(output_topic_base+['longitudinalbm', 'load'])
        gas_topic = '/'.join(output_topic_base+['longitudinalbm', 'natgas'])

        #stuff needed to put inside output, will output by row, each new item
        #is a new file, title must match title in execute when writing to out
        output_needs = {
            'Longitudinal_BM': {
                'year':OutputDescriptor('integer', year_topic),
                'load':OutputDescriptor('float', load_topic),
                'natgas':OutputDescriptor('float', gas_topic)
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
        # topics = input_object.get_topics()
        # meta_topics = input_object.get_topics_meta()
        # load_units = meta_topics['load'][base_topic]['unit']

        report = reports.Report('Longitudinal Benchmarking Report')

        text_blurb = reports.TextBlurb(text="The plots show total building energy consumption compared over time.")
        report.add_element(text_blurb)

        xy_dataset_list = []
        xy_dataset_list.append(reports.XYDataSet('Longitudinal_BM', 'year', 'load'))
        elec_bar_chart = reports.BarChart(xy_dataset_list,
                                     title='Annual Building Consumption (Electricity)',
                                     x_label='Year',
                                     y_label='Electric Energy [kWh]')
        report.add_element(elec_bar_chart)

        xy_dataset_list = []
        xy_dataset_list.append(reports.XYDataSet('Longitudinal_BM', 'year', 'natgas'))
        natgas_bar_chart = reports.BarChart(xy_dataset_list,
                                     title='Annual Building Consumption (Natural Gas)',
                                     x_label='Year',
                                     y_label='Natural Gas Energy [kBTU]')
        report.add_element(natgas_bar_chart)

        text_guide1 = reports.TextBlurb(text="Compare energy use in the base year to that in the later years.")
        report.add_element(text_guide1)

        text_guide2 = reports.TextBlurb(text="A persistent or large increase in bar height\
                                              reflects growing annual energy use and possible\
                                              efficiency opportunities.")
        report.add_element(text_guide2)

        text_guide3 = reports.TextBlurb(text="A significant efficiency improvement would result\
                                              in a downward trend of decreasing bar height.")
        report.add_element(text_guide3)

        report_list = [report]

        return report_list


    def execute(self):
        #Called after User hits GO
        """
        Will output the following: year, aggregated load amounts,
        and aggregated gas amounts.
        """
        self.out.log("Starting application: longitudinal benchmarking.", logging.INFO)

        self.out.log("Querying database.", logging.INFO)
        # Note: Assumes all of the energy data are in a per hour basis.
        # TODO: The caveat above must be made stronger.  Aggregating by summing
        #   only converts, e.g., [kW] to [kWh] for hourly observations.
        #   Similar problem for gas data.
        # TODO: The query here presumably groups by calendar year.  Need to check
        #   whether application actually wants a year's worth of data, looking
        #   backward from most recent observation.
        # Valid calculation to sum the data by 'year'.
        load_by_year = self.inp.get_query_sets('load', group_by='year',
                                               group_by_aggregation=Sum,
                                               exclude={'value':None},
                                               wrap_for_merge=True)

        gas_by_year = self.inp.get_query_sets('natgas', group_by='year',
                                              group_by_aggregation=Sum,
                                              exclude={'value':None},
                                              wrap_for_merge=True)

        merge_load_gas = self.inp.merge(load_by_year, gas_by_year)

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

        self.out.log("Compiling the report table.", logging.INFO)
        for x in merge_load_gas:
            self.out.insert_row('Longitudinal_BM', {
                'year': x['time'].year,
                'load': x['load'][0]*load_convertfactor,
                'natgas': x['natgas'][0]*natgas_convertfactor
                })
