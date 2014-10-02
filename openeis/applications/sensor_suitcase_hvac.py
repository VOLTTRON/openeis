"""
Part of the Sensor Suitcase applications. Analyzes temperature data and checks if 
the building is operating at an optimal comfort level. 

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
import numpy as np
from django.db.models import Avg
from openeis.applications.utils.sensor_suitcase import comfort_and_setpoint as cs 
from openeis.applications.utils.sensor_suitcase import economizer as ecn
from openeis.applications.utils.sensor_suitcase import setback_non_op as sb 
from openeis.applications.utils.sensor_suitcase import short_cycling as shc 
from openeis.applications.utils import conversion_utils as cu

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
    def get_config_parameters(cls):
        # Called by UI
        
        return {
            "building_name": ConfigDescriptor(str, "Building Name", optional=True),
            "building_area": ConfigDescriptor(float, "Building Area"),
            "electricity_cost": ConfigDescriptor(float, "Electricity Cost"),
            "operating_hours": ConfigDescriptor(str, "Operating Schedule: 'begin, end' (e.g. 8,17)'"),
            "operating_days": ConfigDescriptor(str, "List the weekdays when building is operated: \n (1 = Monday, 7 = Sunday), separated by commas"),
            "holidays": ConfigDescriptor(str, "List the holidays (YYYY-MM-DD) in the dataset, separated by commas.", optional=True),
            }


    @classmethod
    def required_input(cls):
        # Called by UI
        # Sort out units.
        return {
            'zat':InputDescriptor('ZoneTemperature', 'Zone/Indoor Temperature'),
            'dat':InputDescriptor('DischargeAirTemperature', 'Discharge Air Temperature'),
            'oat':InputDescriptor('OutdoorAirTemperature', 'Outdoor Air Temperature'),
            'hvacstatus':InputDescriptor('HVACStatus', 'HVAC Equipment Status')
            }

    @classmethod
    def output_format(cls, input_object):
        # Called when app is staged
        """
        Output:
            stat_message: HVAC recommendation based on the model.  
        """
        topics = input_object.get_topics()
        base_topic = topics['zat'][0]
        topic_parts = base_topic.split('/')
        output_topic_base = topic_parts[:-1]
        
        stat_analysis_topic = '/'.join(output_topic_base + ['sensorsuitcaseHVAC', 'analysis'])        
        stat_problem_topic = '/'.join(output_topic_base + ['sensorsuitcaseHVAC', 'problem'])
        stat_diagnostic_topic = '/'.join(output_topic_base + ['sensorsuitcaseHVAC', 'diagnostic'])
        stat_recommendation_topic = '/'.join(output_topic_base + ['sensorsuitcaseHVAC', 'recommendation'])
        stat_savings_topic = '/'.join(output_topic_base + ['sensorsuitcaseHVAC', 'savings'])

        output_needs = {
            'SensorSuitcaseHVAC': {
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

        report = reports.Report('Sensor Suitcase (HVAC Diagnostics)')

        text_blurb = reports.TextBlurb(text="Sensor Suitcase analysis shows HVAC Diagnostics.")
        report.add_element(text_blurb)

        column_info = (('problem', 'Problem'), 
                       ('diagnostic', 'Diagnostic'),
                       ('recommendation','Recommendations'),
                       ('savings','Savings'))

        summary_table = reports.Table('SensorSuitcaseHVAC',
                                      column_info,
                                      title='Sensor Suitcase HVAC Diagnostics',
                                      description='A table showing diagnostics for your building.')

        report.add_element(summary_table)

        report_list = [report]

        return report_list

    def execute(self):
        # Called after User hits GO
        """
        Calculates weather sensitivity using Spearman rank.
        Also, outputs data points for energy signature scatter plot.
        """
        self.out.log("Starting Day Time Temperature Analysis", logging.INFO)

        self.out.log('@operating_sched'+str(self.operating_sched), logging.INFO)
        self.out.log('@building_area'+str(self.building_area), logging.INFO)
        self.out.log('@electricity_cost'+str(self.electricity_cost), logging.INFO)
        
        # Query the database
        zat_query = self.inp.get_query_sets('zat', exclude={'value':None},
                                                   wrap_for_merge=True,
                                                   group_by='minute')
                                                   
        dat_query = self.inp.get_query_sets('dat', exclude={'value':None},
                                                   wrap_for_merge=True,
                                                   group_by='minute')
                                                   
        oat_query = self.inp.get_query_sets('oat', exclude={'value':None},
                                                   wrap_for_merge=True,
                                                   group_by='minute')
                                                   
        status_query = self.inp.get_query_sets('hvacstatus', exclude={'value':None},
                                                   wrap_for_merge=True,
                                                   group_by='minute')
        # Merge temperatures and the HVACStatus
        merged_temperatures_status = self.inp.merge(zat_query, oat_query, dat_query,status_query)
        
        # Get conversion factor
        base_topic = self.inp.get_topics()
        meta_topics = self.inp.get_topics_meta()
        zat_unit = meta_topics['zat'][base_topic['zat'][0]]['unit']
        dat_unit = meta_topics['dat'][base_topic['dat'][0]]['unit']
        oat_unit = meta_topics['oat'][base_topic['oat'][0]]['unit']
        
        #From the merged values make the arrays for the models
        datetime_ZAT = []
        datetime_DAT = []
        datetime_OAT = []
        datetime_HVACStatus = []
        for line in merged_temperatures_status:
            # Convert datetime str to datetime obj
            datetimeObj = dt.datetime.strptime(line['time'],'%Y-%m-%d %H:%M')
            
            # Convert ZAT
            if zat_unit == 'celcius':
                convertedZAT = cu.convertCelciusToFahrenheit(line['zat'][0])
            elif zat_unit == 'kelvin':
                convertedZAT = cu.convertKelvinToCelcius(
                                cu.convertCelciusToFahrenheit(line['zat'][0]))
            else: 
                convertedZAT = line['zat'][0]
            #    
            datetime_ZAT.append((datetimeObj, convertedZAT)) 
        
            # Convert DAT
            if dat_unit == 'celcius':
                convertedDAT = cu.convertCelciusToFahrenheit(line['dat'][0])
            elif dat_unit == 'kelvin':
                convertedDAT = cu.convertKelvinToCelcius(
                                cu.convertCelciusToFahrenheit(line['dat'][0]))
            else: 
                convertedDAT = line['dat'][0]        
            #
            datetime_DAT.append((datetimeObj, convertedDAT)) 
                
            # Convert OAT
            if oat_unit == 'celcius':
                convertedOAT = cu.convertCelciusToFahrenheit(line['oat'][0])
            elif oat_unit == 'kelvin':
                convertedOAT = cu.convertKelvinToCelcius(
                                cu.convertCelciusToFahrenheit(line['oat'][0]))
            else: 
                convertedOAT = line['oat'][0]
            #
            datetime_OAT.append((datetimeObj, convertedOAT)) 
            #
            datetime_HVACStatus.append((datetimeObj, line['hvacstatus'][0])) 
        # Apply the comfort_and_setpoint model.
        comfort_flag, setback_flag = cs.comfort_and_setpoint(datetime_ZAT, 
                                                   datetime_DAT, 
                                                   self.operating_sched, 
                                                   self.building_area, 
                                                   self.electricity_cost, 
                                                   datetime_HVACStatus)
        if comfort_flag != {}:
            self.out.insert_row('SensorSuitcaseHVAC', { 
                                'analysis': 'Comfort Optimization',
                                'problem': comfort_flag['Problem'],
                                'diagnostic': comfort_flag['Diagnostic'],
                                'recommendation': comfort_flag['Recommendation'],
                                'savings': '${:.2f}'.format(comfort_flag['Savings'])
                                })
                                
        if setback_flag != {}:
            self.out.insert_row('SensorSuitcaseHVAC', { 
                                'analysis': 'Comfort Optimization',
                                'problem': setback_flag['Problem'],
                                'diagnostic': setback_flag['Diagnostic'],
                                'recommendation': setback_flag['Recommendation'],
                                'savings': '${:.2f}'.format(setback_flag['Savings'])
                                })
                                
        # Apply the economizer model.
        economizer_flag = ecn.economizer(datetime_DAT, 
                                         datetime_OAT, 
                                         datetime_HVACStatus, 
                                         self.electricity_cost, 
                                         self.building_area)    
        if economizer_flag != {}:
            self.out.insert_row('SensorSuitcaseHVAC', { 
                                'analysis': 'Economizer Diagnostics',
                                'problem': economizer_flag['Problem'],
                                'diagnostic': economizer_flag['Diagnostic'],
                                'recommendation': economizer_flag['Recommendation'],
                                'savings': '${:.2f}'.format(economizer_flag['Savings'])
                                })
        
        # Apply the setback_non_op model.
        setback_nonop_flag = sb.setback_non_op(datetime_ZAT, 
                                         datetime_DAT, 
                                         self.operating_sched, 
                                         self.electricity_cost, 
                                         self.building_area, 
                                         datetime_HVACStatus)
        if setback_nonop_flag != {}:
            self.out.insert_row('SensorSuitcaseHVAC', { 
                                'analysis': 'Setback During Unoccupied Hours',
                                'problem': setback_nonop_flag['Problem'],
                                'diagnostic': setback_nonop_flag['Diagnostic'],
                                'recommendation': setback_nonop_flag['Recommendation'],
                                'savings': '${:.2f}'.format(setback_nonop_flag['Savings'])
                                })
        
        # Apply the short_cycling model.
        shortcycling_flag = shc.short_cycling(datetime_HVACStatus, 
                                              self.electricity_cost)
        if shortcycling_flag != {}:
            self.out.insert_row('SensorSuitcaseHVAC', { 
                                'analysis': 'Shortcycling',
                                'problem': shortcycling_flag['Problem'],
                                'diagnostic': shortcycling_flag['Diagnostic'],
                                'recommendation': shortcycling_flag['Recommendation'],
                                'savings': '${:.2f}'.format(shortcycling_flag['Savings'])
                                })
