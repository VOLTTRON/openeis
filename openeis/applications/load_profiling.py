"""
Load profile: show building loads over time.

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
from .utils import conversion_utils as cu
import datetime as dt
import logging


class Application(DriverApplicationBaseClass):

    def __init__(self, *args, building_name=None, **kwargs):
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


    @classmethod
    def get_config_parameters(cls):
        #Called by UI
        return {
            "building_name": ConfigDescriptor(str, "Building Name", optional=True)
            }


    @classmethod
    def required_input(cls):
        #Called by UI
        return {
            'load':InputDescriptor('WholeBuildingElectricity','Building Load'),
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

        # Work with topics["OAT"][0] to get building topic
        output_needs = {
            'Load_Profiling': {
                'timestamp':OutputDescriptor('datetime', time_topic),
                'load':OutputDescriptor('float', load_topic)
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
        
        report = reports.Report('Building Load Profile Report')

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

        report_list = [report]

        return report_list

    def execute(self):
        #Called after User hits GO
        "Outputs values for line graph."
        self.out.log("Starting analysis", logging.INFO)

        # Get the units and the conversion factor. 
        self.out.log("Find the conversion factor.", logging.INFO)
        base_topic = self.inp.get_topics()
        meta_topics = self.inp.get_topics_meta()
        load_unit = meta_topics['load'][base_topic['load'][0]]['unit']
        #
        load_convertfactor = cu.conversiontoKWH(load_unit)
        
        load_by_hour = self.inp.get_query_sets('load', 
                                                exclude={'value': None},
                                                group_by='hour')

        for x in load_by_hour[0]:
            self.out.insert_row("Load_Profiling", {
                'timestamp': dt.datetime.strptime(x[0],'%Y-%m-%d %H'),
                'load': x[1]*load_convertfactor 
                })
