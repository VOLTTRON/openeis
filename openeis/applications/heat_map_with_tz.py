"""
Heat map: show electricity use by time-of-day, across many days.

Shows extent of daily, weekly, and seasonal load profiles.

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

from openeis.applications import reports
from openeis.applications import DriverApplicationBaseClass, InputDescriptor,  \
    OutputDescriptor, ConfigDescriptor
from openeis.applications import reports
from .utils import conversion_utils as cu
import datetime as dt
import logging
import pytz

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
        # Called by UI
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
        Output will have the date, hour, and respective load.
        To be graphed in a heat map later.
        """
        topics = input_object.get_topics()
        load_topic = topics['load'][0]
        load_topic_parts = load_topic.split('/')
        output_topic_base = load_topic_parts[:-1]
        date_topic = '/'.join(output_topic_base+['heatmap', 'date'])
        hour_topic = '/'.join(output_topic_base+['heatmap', 'time'])
        load_topic = '/'.join(output_topic_base+['heatmap', 'load'])
        output_needs = {
            'Heat_Map': {
                'date': OutputDescriptor('string', date_topic),
                'hour': OutputDescriptor('integer', hour_topic),
                'load': OutputDescriptor('float', load_topic)
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

        report = reports.Report('Heat Map for Building Energy Load')

        text_blurb = reports.TextBlurb(text="Analysis of the extent of a building's daily, weekly, and seasonal shut off.")
        report.add_element(text_blurb)

        heat_map = reports.HeatMap(table_name='Heat_Map',
                                   x_column='hour',
                                   y_column='date',
                                   z_column='load',
                                   x_label='Hour of the Day',
                                   y_label='Date',
                                   z_label='Building Energy [kWh]')
        report.add_element(heat_map)

        text_guide1 = reports.TextBlurb(text="Horizontal banding indicates shut off during\
                                              periodic days (e.g. weekends).")
        report.add_element(text_guide1)

        text_guide2 = reports.TextBlurb(text="Unusual or unexplainable \"hot spots\"\
                                              may indicate poor equipment control.")
        report.add_element(text_guide2)

        text_guide3 = reports.TextBlurb(text="Vertical banding indicates consistent\
                                              daily scheduling of usage.")
        report.add_element(text_guide3)

        report_list = [report]

        return report_list

    def execute(self):
        #Called after User hits GO
        """
        Output values for Heat Map.
        """
        self.out.log("Starting analysis", logging.INFO)

        loads = self.inp.get_query_sets('load', group_by='hour', exclude={'value':None})

        # Get conversion factor
        base_topic = self.inp.get_topics()
        meta_topics = self.inp.get_topics_meta()
        load_unit = meta_topics['load'][base_topic['load'][0]]['unit']
#        load_tz = meta_topics['load'][base_topic['load'][0]]['timezone']

        load_convertfactor = cu.conversiontoKWH(load_unit)
        print (load_convertfactor)

        self.out.log("@length of a month"+str(len(loads[0])), logging.INFO)



        

        for x in loads[0]:
            print(x)

            datevalue = dt.datetime.strptime(x[0], '%Y-%m-%d %H')
            datevalue = self.inp.localize_sensor_time('load', base_topic['load'][0], datevalue)
            
            print(datevalue)
#            tz.localize(datevalue)
            self.out.insert_row("Heat_Map", {
                'date': datevalue.date(),
                'hour': datevalue.hour,
                'load': x[1]*load_convertfactor
                }
            )
