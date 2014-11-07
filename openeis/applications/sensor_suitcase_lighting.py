"""
Analyze a location's lighting data and checks whether lights are switched on
for more than 50% of the operational hours.


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


from openeis.applications import DriverApplicationBaseClass, InputDescriptor, \
    OutputDescriptor, ConfigDescriptor, Descriptor
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
                              operating_hours,
                              operating_days,
                              holidays=[],
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

        operating_days_list = []
        for daysint in operating_days.split(','):
            operating_days_list.append(int(daysint))

        holiday_list = []
        if holidays != []:
            for dates in holidays.split(','):
                holiday_list.append(dt.datetime.strptime(dates.strip(),'%Y-%m-%d').date())
        hour_int = []
        for hour in operating_hours.split(','):
            hour_int.append(int(hour))

        self.operating_sched = [hour_int,
                                operating_days_list,
                                holiday_list]
        
        self.building_area = building_area
        self.electricity_cost = electricity_cost
        
    @classmethod
    def get_app_descriptor(cls):    
        name = 'Sensor Suitcase: Lighting'
        desc = 'RCx sensor suitcase diagnostics is used to identify problems in\
                the operation and performance of lighting systems in small\
                commercial buildings. This diagnostic suite targets problems\
                that are common to this class of buildings, specifically,\
                excessive lighting during the day-time and after-hours periods. '
        return ApplicationDescriptor(app_name=name, description=desc)
        
    @classmethod
    def get_config_parameters(cls):
        # Called by UI
        #FIXME: Change the operating hours param to match the HVAC system, operating schedule.
        return {
            "building_name": ConfigDescriptor(str, "Building Name", optional=True),
            "building_area": ConfigDescriptor(float, "Building Area"),
            "electricity_cost": ConfigDescriptor(float, "Electricity Cost"),
            "operating_hours": ConfigDescriptor(str, "Operating Schedule: 'begin, end' (e.g. 8,17)'"),
            "operating_days": ConfigDescriptor(str, "List the weekdays when building is operated: \n (1 = Monday, 7 = Sunday), separated by commas"),
            "holidays": ConfigDescriptor(str, "List the holidays (YYYY-MM-DD) in the dataset, separated by commas.", optional=True),
            }

    @classmethod
    def get_self_descriptor(cls):
        name = 'sensor_suitcase_lighting'
        desc = 'sensor_suitcase_lighting'
        return Descriptor(name=name, description=desc)
    
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
        self.out.log("Starting application: Sensor Suitcase excessive lighting.", logging.INFO)

        # FIXME: Modify logging message.
        self.out.log('@building_area'+str(self.building_area), logging.INFO)
        self.out.log('@electricity_cost'+str(self.electricity_cost), logging.INFO)
        self.out.log('@operating_sched'+str(self.operating_sched), logging.INFO)

        # Get lighting status from database
        lighting_query = self.inp.get_query_sets('lightingstatus',
                                                 exclude={'value':None} )
        datetime_lightmode = []
        for x in lighting_query[0]:
            datetime_lightmode.append((x[0],x[1]))

        daylight_flag = edl.excessive_daylight(datetime_lightmode,
                                               self.operating_sched,
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
                                                 self.operating_sched,
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
