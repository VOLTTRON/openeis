"""
Analyze a location's lighting data and checks whether lights are switched on
for more than 50% of the operational hours.

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


from openeis.applications import DriverApplicationBaseClass, InputDescriptor, \
    OutputDescriptor, ConfigDescriptor
from openeis.applications import reports
import logging
import datetime as dt
from django.db.models import Avg
from openeis.applications.utils.sensor_suitcase import excessive_daylight_lighting as edl
from openeis.applications.utils.sensor_suitcase import excessive_night_lighting as enl


class Application(DriverApplicationBaseClass):

    def __init__(self, *args, building_name=None, 
                              building_area,
                              electricity_cost,
                              operation_hours,
                              **kwargs):
        # Called after app has been staged
        """
        When applications extend this base class, they need to make
        use of any kwargs that were setup in config_param
        """
        super().__init__(*args, **kwargs)

        self.default_building_name_used = False

        if building_name is None:
            building_name = "None supplied"
            self.default_building_name_used = True

        self.building_name = building_name
        
        self.building_area = building_area
        self.electricity_cost = electricity_cost
        self.operation_hours = operation_hours

    @classmethod
    def get_config_parameters(cls):
        # Called by UI
        return {
            "building_name": ConfigDescriptor(str, "Building Name", optional=True),
            "building_area": ConfigDescriptor(float, "Building Area"),
            "electricity_cost": ConfigDescriptor(float, "Electricity Cost"),
            "operation_hours": ConfigDescriptor(float, "Number of hours buildings is operational")
            }


    @classmethod
    def required_input(cls):
        # Called by UI
        # Sort out units.
        return {
            'lightingstatus':InputDescriptor('LightingStatus', 'Building Lighting Mode')
            }

    @classmethod
    def output_format(cls, input_object):
        # Called when app is staged
        """
        Output:
            measuredValues: values directly measured from the building
        """
        topics = input_object.get_topics()
        base_topic = topics['lightingstatus'][0]
        topic_parts = base_topic.split('/')
        output_topic_base = topic_parts[:-1]
        
        stat_analysis_topic = '/'.join(output_topic_base + ['sensorsuitcaseLight', 'analysis'])        
        stat_problem_topic = '/'.join(output_topic_base + ['sensorsuitcaseLight', 'problem'])
        stat_diagnostic_topic = '/'.join(output_topic_base + ['sensorsuitcaseLight', 'diagnostic'])
        stat_recommendation_topic = '/'.join(output_topic_base + ['sensorsuitcaseLight', 'recommendation'])
        stat_savings_topic = '/'.join(output_topic_base + ['sensorsuitcaseLight', 'savings'])

        output_needs = {
            'SensorSuitcaseLight': {
                'analysis': OutputDescriptor('string', stat_analysis_topic),
                'problem': OutputDescriptor('string', stat_problem_topic),
                'diagnostic': OutputDescriptor('string', stat_diagnostic_topic),
                'recommendation': OutputDescriptor('string', stat_recommendation_topic),
                'savings': OutputDescriptor('string', stat_savings_topic)
                }
            }
        return output_needs


    @classmethod
    def reports(cls, output_object):
        # Called by UI to create Viz
        """Describe how to present output to user
        Display this viz with these columns from this table

        display_elements is a list of display objects specifying viz and columns
        for that viz
        """

        report = reports.Report('Sensor Suitcase (Lighting Diagnostics)')

        text_blurb = reports.TextBlurb(text="Sensor Suitcase analysis showing Lighting Diagnostics.")
        report.add_element(text_blurb)

        column_info = (('problem', 'Problem'), 
                       ('diagnostic', 'Diagnostic'),
                       ('recommendation','Recommendations'),
                       ('savings','Savings'))

        summary_table = reports.Table('SensorSuitcaseLight',
                                      column_info,
                                      title='Sensor Suitcase Lighting Diagnostics',
                                      description='A table showing diagnostics for your building.')

        report.add_element(summary_table)

        report_list = [report]

        return report_list

    def execute(self):
        # Called after User hits GO
        """
        Accepts lighting status and operational hours to determine if there 
        is excessive lighting during daytime.        
        """
        self.out.log("Starting ExcessiveLighting Analysis", logging.INFO)
        
        self.out.log('@building_area'+str(self.building_area), logging.INFO)
        self.out.log('@electricity_cost'+str(self.electricity_cost), logging.INFO)
        self.out.log('@operation_hours'+str(self.operation_hours), logging.INFO)

        # Get lighting status from database
        lighting_query = self.inp.get_query_sets('lightingstatus', 
                                                 exclude={'value':None} )
        datetime_lightmode = []
        for x in lighting_query[0]:
            datetime_lightmode.append((x[0],x[1]))
            
        daylight_flag = edl.excessive_daylight(datetime_lightmode, 
                                               self.operation_hours, 
                                               self.building_area, 
                                               self.electricity_cost)
        if daylight_flag != {}:
            self.out.insert_row('SensorSuitcaseLight', { 
                                'analysis': 'Excessive Daylighting',
                                'problem': daylight_flag['Problem'],
                                'diagnostic': daylight_flag['Diagnostic'],
                                'recommendation': daylight_flag['Recommendation'],
                                'savings': '${:.2f}'.format(daylight_flag['Savings'])
                                })
                            
        nighttime_flag = enl.excessive_nighttime(datetime_lightmode, 
                                                 self.operation_hours, 
                                                 self.building_area, 
                                                 self.electricity_cost)
        if nighttime_flag != {}:
            self.out.insert_row('SensorSuitcaseLight', { 
                                'analysis': 'Excessive Daylighting',
                                'problem': nighttime_flag['Problem'],
                                'diagnostic': nighttime_flag['Diagnostic'],
                                'recommendation': nighttime_flag['Recommendation'],
                                'savings': '${:.2f}'.format(nighttime_flag['Savings'])
                                })