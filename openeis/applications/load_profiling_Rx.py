"""
Load profile: show building loads over time.


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
    OutputDescriptor, ConfigDescriptor, Descriptor
from openeis.applications import reports
from openeis.applications.utils import conversion_utils as cu
from dateutil import parser
import logging
import workalendar.usa

class Application(DriverApplicationBaseClass):

    def __init__(self, *args,
                 building_name=None,
                 pre_start=None,
                 pre_end=None,
                 post_start=None,
                 post_end=None,
                 **kwargs):
        #Called after app has been staged
        """
        When applications extend this base class, they need to make
        use of any kwargs that were setup in config_param
        """
        super().__init__(*args,**kwargs)

        self.default_building_name_used = False

        if building_name is None:
            building_name = "None supplied"
            self.default_building_name_used = True

        self.building_name = building_name
        self.pre_start = parser.parse(pre_start)
        self.pre_end = parser.parse(pre_end)
        self.post_start = parser.parse(post_start)
        self.post_end = parser.parse(post_end)

    @classmethod
    def get_self_descriptor(cls):    
        name = 'Time Series Load Profiling Rx'
        desc = 'Time series load profiling is used to understand the relationship\
                between energy use and time of day. \
                This app compares load profile for pre- and post- retrocommissioning periods.'
        return Descriptor(name=name, description=desc)

    @classmethod
    def get_config_parameters(cls):
        #Called by UI
        return {
            'building_name': ConfigDescriptor(str, "Building Name", optional=True),
            'pre_start': ConfigDescriptor(str, 'Pre-Rx start date (yyyy-mm-dd) (including)'),
            'pre_end': ConfigDescriptor(str, 'Pre-Rx end date (yyyy-mm-dd) (excluding)'),
            'post_start': ConfigDescriptor(str, 'Post-Rx start date (yyyy-mm-dd) (including)'),
            'post_end': ConfigDescriptor(str, 'Post-Rx end date (yyyy-mm-dd) (excluding)'),
        }
    
    @classmethod
    def required_input(cls):
        #Called by UI
        return {
            'load':InputDescriptor('WholeBuildingPower','Building Load'),
            }


    @classmethod
    def output_format(cls, input_object):
        # Called when app is staged
        """
        Output is hour with respective load, to be put in a line graph later.
        """
        topics = input_object.get_topics()
        load_topic = topics['load'][0]
        load_topic_parts = load_topic.split('/')
        output_topic_base = load_topic_parts[: -1]
        time_topic = '/'.join(output_topic_base+['timeseries', 'time'])
        load_topic = '/'.join(output_topic_base+['timeseries', 'load'])
        daytype_topic = '/'.join(output_topic_base+['timeseries', 'daytype'])
        rx_topic = '/'.join(output_topic_base + ['timeseries', 'rx'])

        # Work with topics["OAT"][0] to get building topic
        output_needs = {
            'Load_Profiling': {
                'datetime':OutputDescriptor('string', time_topic),
                'load':OutputDescriptor('float', load_topic),
                'daytype': OutputDescriptor('string', daytype_topic),
                'rxtype': OutputDescriptor('string', rx_topic)
                }
            }
        return output_needs

    def reports(self):
        report = reports.Report('Load Profile Rx Report')
        report.add_element(reports.LoadProfileRx(
            table_name='Load_Profiling'))
        return [report]

    def reports1(self):
        #Called by UI to create Viz
        """Describe how to present output to user
        Display this viz with these columns from this table

        display_elements is a list of display objects specifying viz and columns
        for that viz
        """

        report = reports.Report('Building Load Profile Rx Report')

        text_blurb = reports.TextBlurb(text="A plot showing building energy consumption over a time period.")
        report.add_element(text_blurb)

        xy_dataset_list = []
        xy_dataset_list.append(reports.XYDataSet('Load_Profiling', 'timestamp', 'load'))

        scatter_plot = reports.DatetimeScatterPlot(xy_dataset_list,
                                           title='Time Series Load Profile',
                                           x_label='Timestamp',
                                           y_label='Energy [kWh]'
                                           )
        report.add_element(scatter_plot)

        text_guide1 = reports.TextBlurb(text="Do loads decrease during lower occupancy periods\
                                              (e.g. weekends or overnight)?")
        report.add_element(text_guide1)

        text_guide2 = reports.TextBlurb(text="Does the width of similar load profiles correspond\
                                              to occupancy schedule?")
        report.add_element(text_guide2)

        text_guide3 = reports.TextBlurb(text="Minima should occur during unoccupied hours\
                                              and be as close to zero as possible.")
        report.add_element(text_guide3)

        text_guide4 = reports.TextBlurb(text="Does the weekly profile correspond to occupancy\
                                              and use for each day for a typical week?")
        report.add_element(text_guide4)

        report_list = [report]

        return report_list

    def execute(self):
        """Outputs values for line graph."""
        self.out.log("Starting application: load profile.", logging.INFO)

        self.out.log("Getting unit conversions.", logging.INFO)
        base_topic = self.inp.get_topics()
        meta_topics = self.inp.get_topics_meta()

        load_unit = meta_topics['load'][base_topic['load'][0]]['unit']
        self.out.log(
            "Convert loads from [{}] to [kW].".format(load_unit),
            logging.INFO
            )
        load_convertfactor = cu.getFactor_powertoKW(load_unit)

        self.out.log("Querying database.", logging.INFO)
        load_by_hour = self.inp.get_query_sets('load',
                                                exclude={'value': None},
                                                group_by='hour')[0]

        self.out.log("Reducing the records to two weeks.", logging.INFO)
        # Note: Limit the number of datapoints, have 2 weeks worth of data.
        # 24 hours x 14 days = 336.
        # if len(load_by_hour) > 336:
        #     start = len(load_by_hour) - 336
        #     end = len(load_by_hour) - 1
        # else:
        #     start = 0
        #     end = len(load_by_hour)

        self.out.log("Compiling the report table.", logging.INFO)
        #for x in load_by_hour[start:end]:
        cal = workalendar.usa.UnitedStates()
        values = []
        prev_local_time = None
        pre_start_local = self.inp.localize_sensor_time(base_topic['load'][0], self.pre_start)
        pre_end_local = self.inp.localize_sensor_time(base_topic['load'][0], self.pre_end)
        post_start_local = self.inp.localize_sensor_time(base_topic['load'][0], self.post_start)
        post_end_local = self.inp.localize_sensor_time(base_topic['load'][0], self.post_end)
        for i, x in enumerate(load_by_hour):
            local_time = self.inp.localize_sensor_time(base_topic['load'][0], x[0])
            #Rx type
            rx_type = None
            if (pre_start_local <= local_time <= pre_end_local):
                rx_type = "pre"
            elif (post_start_local <= local_time <= post_end_local):
                rx_type = "post"
            if rx_type is None:
                prev_local_time = None
                values = []
                continue
            #Add 1st record or subsequent records having the same timestamp
            if (local_time == pre_start_local) or (local_time == post_start_local) or (local_time == prev_local_time):
                values.append(x[1])
                prev_local_time = local_time

            if (local_time == pre_end_local) or (local_time == post_end_local) or (local_time != prev_local_time):
                daytype = 'W' #weekdays: [0,4]
                if prev_local_time.weekday() == 5:
                    daytype = 'Sat'
                if prev_local_time.weekday() == 6:
                    daytype = 'Sun'
                if cal.is_holiday(prev_local_time):
                    daytype = 'H'
                value = sum(values)/len(values)
                #print(prev_local_time.strftime('%m/%d/%Y %H:%M:%S') + "   " + daytype + "      " + str(value))
                self.out.insert_row("Load_Profiling", {
                    'datetime': prev_local_time,
                    'load': value*load_convertfactor,
                    'daytype': daytype,
                    'rxtype': rx_type
                })
                values = [x[1]]
                prev_local_time = local_time
