'''
Copyright (c) 2014, Battelle Memorial Institute
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met: 

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer. 
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution. 

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those
of the authors and should not be interpreted as representing official policies, 
either expressed or implied, of the FreeBSD Project.
'''
'''
This material was prepared as an account of work sponsored by an 
agency of the United States Government.  Neither the United States 
Government nor the United States Department of Energy, nor Battelle,
nor any of their employees, nor any jurisdiction or organization 
that has cooperated in the development of these materials, makes 
any warranty, express or implied, or assumes any legal liability 
or responsibility for the accuracy, completeness, or usefulness or 
any information, apparatus, product, software, or process disclosed,
or represents that its use would not infringe privately owned rights.

Reference herein to any specific commercial product, process, or 
service by trade name, trademark, manufacturer, or otherwise does 
not necessarily constitute or imply its endorsement, recommendation, 
r favoring by the United States Government or any agency thereof, 
or Battelle Memorial Institute. The views and opinions of authors 
expressed herein do not necessarily state or reflect those of the 
United States Government or any agency thereof.

PACIFIC NORTHWEST NATIONAL LABORATORY
operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
under Contract DE-AC05-76RL01830
'''
from math import fabs as abs
import datetime
from openeis.applications import (DrivenApplicationBaseClass,
                                  OutputDescriptor, 
                                  ConfigDescriptor,
                                  InputDescriptor,
                                  Results)
import logging

class Application(DrivenApplicationBaseClass):
    '''
    Air-side HVAC Auto-Retuning diagnostic to check if a duct static pressure reset is implemented.
    '''
    '''Diagnostic Point Names (Must match Openeis data-type names)'''
    fan_status_name = "fan_status"
    fan_speedcmd_name = "fan_speedcmd"
    oa_temp_name = "oa_temp"
    duct_stp_name = "duct_stp"
    zone_damper_name = "zone_damper"
    
    def __init__(self,*args,data_window=None,number_of_zones=None,
                low_supply_fan_threshold=None,stpr_diff_threshold=None,oat_threshold=None,
                zonedpr_max_threshold=None,zonedpr_min_threshold=None,no_zones_dpr_max=None,
                no_zones_dpr_min=None, dsgn_stp_high=None, dsgn_stp_low=None,
                device_type=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.zone_damper_values = []
        self.duct_stp_values = []
        self.timestamp =[]
        self.pre_requiste_messages = []
        self.pre_msg_time = []
        self.oa_temp_values = []

        '''Pre-requisite messages'''
        self.pre_msg0 = 'Supply fan is off, current data will not be used for diagnostics.'
        self.pre_msg1 = 'The supply fan is at the minimum allowable speed.'
        self.pre_msg2  = 'Verify that point names in diagnostic match OpenEIS data-type names.'

        '''Point names (Configurable)'''
        self.fan_speedcmd_name = Application.fan_speedcmd_name
        self.fan_status_name = Application.fan_status_name
        self.duct_stp_name = Application.duct_stp_name
        self.oa_temp_name = Application.oa_temp_name

        '''Zone Parameters'''
        self.zone_damper_name = Application.zone_damper_name

        '''Algorithm thresholds (Configurable)'''
        self.device_type = device_type
        self.data_window = float(data_window)
        self.number_of_zones = float(number_of_zones)
        self.low_supply_fan_threshold = float(low_supply_fan_threshold)
        self.stpr_diff_threshold = float(stpr_diff_threshold)
        self.oat_threshold = float(oat_threshold)
        self.zonedpr_max_threshold = float(zonedpr_max_threshold)
        self.zonedpr_min_threshold = float(zonedpr_min_threshold)
        self.no_zones_dpr_max = float(no_zones_dpr_max)
        self.no_zones_dpr_min = float(no_zones_dpr_min)
        self.dsgn_stp_high = float(dsgn_stp_high)
        self.dsgn_stp_low = float(dsgn_stp_low)

    @classmethod
    def get_config_parameters(cls):
        '''
        Generate required configuration
        parameters with description for user
        '''
        return {
                
            'device_type ': ConfigDescriptor(str, 'AHU or RTU'),
            'data_window ': ConfigDescriptor(float, 'Data window'),
            'number_of_zones ': ConfigDescriptor(float, 'Number of zones'),
            'low_supply_fan_threshold ': ConfigDescriptor(float, 'Minimum allowable supply fan speed (typically ~ 20%)'),
            'stpr_diff_threshold ': ConfigDescriptor(float, 'Threshold to detect static pressure reset'),
            'oat_threshold ': ConfigDescriptor(float, 'Required OAT difference for detecting static pressure reset'),
            'zonedpr_max_threshold ': ConfigDescriptor(float, 'High zone damper threshold'),
            'zonedpr_min_threshold ': ConfigDescriptor(float, 'Low zone damper threshold'),
            'no_zones_dpr_max ': ConfigDescriptor(float, 'Number of zones where the damper is greater than the high damper threshold'),
            'no_zones_dpr_min ': ConfigDescriptor(float, 'Number of zones where the damper is less than the low damper threshold'),
            'dsgn_stp_high ': ConfigDescriptor(float, 'Max allowable or desired static pressure'),
            'dsgn_stp_low ': ConfigDescriptor(float, 'Minimum allowable or desired static pressure')
           }

    @classmethod
    def required_input(cls):
        '''
        Generate required inputs with description for
        user.
        '''
        return {
            cls.fan_status_name: InputDescriptor('fan_status', 'AHU Supply Fan Status', count_min=1),
            cls.oa_temp_name: InputDescriptor('oa_temp','AHU or building outdoor-air temperature', count_min=0, count_max=1),
            cls.duct_stp_name: InputDescriptor('duct_stp','AHU duct static pressure', count_min=1),
            cls.zone_damper_name: InputDescriptor('zone_damper','For accurate results this diagnostic requires'
                                                    ' terminal box data for all zones for a particular AHU: terminal box damper command', count_min=2),
            cls.fan_speedcmd_name: InputDescriptor('fan_speedcmd', 'Supply fan VFD command for AHU', count_min=1)
            }

    def reports(self):
        '''
        Called by UI to create Viz.
        Describe how to present output to user
        Display this viz with these columns from this table
    
        display_elements is a list of display objects specifying viz and columns
        for that viz
        '''
        return []

    @classmethod
    def output_format(cls, input_object):
        """
        Called when application is staged.
        Output will have the date-time and  error-message.
        """
        topics = input_object.get_topics()
        diagnostic_topic = topics[cls.fan_status_name][0]
        diagnostic_topic_parts = diagnostic_topic.split('/')
        output_topic_base = diagnostic_topic_parts[:-1]
        datetime_topic = '/'.join(output_topic_base+['airside_low_dat_diagnostic', 'date'])
        message_topic = '/'.join(output_topic_base+['airside_low_dat_diagnostic', 'message'])
        output_needs = {
            'Diagnostic_Message': {
                'date-time': OutputDescriptor('datetime', datetime_topic),
                'diagnostic-message': OutputDescriptor('string', message_topic)
                }
            }
        return output_needs

    def drop_partial_lines (self): 
        '''
        drop rows with missing data.
        '''
        return True

    def run(self,current_time, points):
        """
        Check algorithm pre-quisites and assemble data set for analysis.
        """
        device_dict = {}
        diagnostic_result = Results()

        if None in points.values():
            diagnostic_result.log(''.join(['Missing data for timestamp: ',str(current_time),
                                   '  This row will be dropped from analysis.']))
            return diagnostic_result

        for key, value in points.items():
            device_dict[key.lower()] = value

        self.pre_msg_time.append(current_time)
        message_check =  datetime.timedelta(minutes=(self.data_window))
       
        if (self.pre_msg_time[-1]-self.pre_msg_time[0]) >= message_check:
            msg_lst = [self.pre_msg0,self.pre_msg1, self.pre_msg2]
            for item in msg_lst:
                if self.pre_requiste_messages.count(item) > (0.25)*len(self.pre_msg_time):
                    diagnostic_result.log(item, logging.INFO)
            self.pre_requiste_messages = []
            self.pre_msg_time = [] 

        for key, value in device_dict.items():
            if self.fan_status_name in key:
                if int(value) == 0:
                    self.pre_requiste_messages.append(sef.pre_msg0)
                    return diagnostic_result

        for key, value in device_dict.items():
            if self.fan_speedcmd_name in key:
                if value < self.low_supply_fan_threshold:
                    self.pre_requiste_messages.append(self.pre_msg1)
                    return diagnostic_result

        oatemp_data, stc_pr_data, zone_damper_data = [], [], []

        for key, value in device_dict.items():

            if key.startswith(self.duct_stp_name):
                stc_pr_data.append(value)
                
            elif key.startswith(self.oa_temp_name):
                oatemp_data.append(value)
                
            elif key.startswith(self.zone_damper_name):
                zone_damper_data.append(value)

        if not (oatemp_data and stc_pr_data and zone_damper_data):
            self.pre_requiste_messages.append(self.pre_msg2)
            return diagnostic_result
        
        self.timestamp.append(current_time)
        self.duct_stp_values.extend(stc_pr_data)
        self.zone_damper_values.extend(zone_damper_data)
        self.oa_temp_values.extend(oatemp_data)

        time_check =  datetime.timedelta(minutes=self.data_window)

        if ((self.timestamp[-1]-self.timestamp[0]) >= time_check and
            len(self.timestamp) > 25):
            diagnostic_result = self.high_ductstatic_sp(diagnostic_result)
        return diagnostic_result

    def high_ductstatic_sp(self, result):
        """
        If the detected problems(s) are consistent then generate a fault message(s).
        """
        no_zones_avg_dpr_max = [i for i in self.zone_damper_values if i >= self.zonedpr_max_threshold]
        no_zones_avg_dpr_min = [i for i in self.zone_damper_values if i <= self.zonedpr_min_threshold]
        per_no_zones_avg_dpr_max = len(no_zones_avg_dpr_max)/len(self.zone_damper_values)
        per_no_zones_avg_dpr_min = len(no_zones_avg_dpr_min)/len(self.zone_damper_values)

        avg_duct_stpr = sum(self.duct_stp_values)/len(self.duct_stp_values)
        stp_diff = max(self.duct_stp_values)-min(self.duct_stp_values)
        avg_stp = sum(self.duct_stp_values)/len(self.duct_stp_values)
        oat_diff = max(self.oa_temp_values)-min(self.oa_temp_values)

        if stp_diff<self.stpr_diff_threshold:
            if oat_diff>self.oat_threshold:
                if (
                    (avg_stp<self.dsgn_stp_high and  per_no_zones_avg_dpr_max>self.no_zones_dpr_max/100) or
                    (avg_stp>self.dsgn_stp_low and  per_no_zones_avg_dpr_min>self.no_zones_dpr_min/100)
                    ):                
                    result.log('No duct static pressure reset detected.  A duct static pressure set point reset '
                               'can save significant amounts of energy', logging.INFO)
                else:
                    result.log('No conclusion drawn.', logging.INFO)
                
            else:                       
                result.log('No conclusion drawn since outside temperature is not varying.', logging.INFO)
        else:
            result.log('A duct static pressure reset was detected', logging.INFO)
        
        self.zone_damper_values = []
        self.duct_stp_values = []
        self.oa_temp_values = []
        self.pre_requiste_messages = []
        self.pre_msg_time = []
        self.timestamp = []

        return result
