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
import datetime
from openeis.applications import (DrivenApplicationBaseClass,
                                  OutputDescriptor, 
                                  ConfigDescriptor,
                                  InputDescriptor,
                                  Results)
import logging


class Application(DrivenApplicationBaseClass):
    '''
    Air-side HVAC Auto-Retuning diagnostic to check if the supply-air
    temperature is too high.
    '''
    
    '''Diagnostic Point Names (Must match Openeis data-type names)'''
    fan_status_name = "fan_status"
    zone_reheat_name = "zone_rht_vlv"
    da_temp_name = "da_temp"
    da_temp_stpt_name = "da_temp_stpt"
    zone_damper_name = "zone_damper"
    
    def __init__(self,*args,data_window=None,number_of_zones=None,
                high_damper_threshold=None,percent_damper_threshold=None,percent_reheat_threshold=None,
                minimum_dat_stpt=None,dat_reduction=None,rht_on_threshold=None,
                setpoint_allowable_deviation=None,**kwargs):
        super().__init__(*args, **kwargs)
        self.timestamp = []
        self.dat_stpt_values = []
        self.dat_values = []
        self.total_reheat = 0
        self.total_damper = 0
        self.pre_requiste_messages = []
        self.pre_msg_time = []

        '''Pre-requisite messages'''
        self.pre_msg0 = 'Supply fan is off, current data will not be used for diagnostics.'
        self.pre_msg1  = 'Verify that point names in diagnostic match OpenEIS data-type names.'

        '''Point names (Configurable)'''
        self.da_temp_stpt_name = Application.da_temp_stpt_name
        self.da_temp_name = Application.da_temp_name
        self.zone_reheat_name = Application.zone_reheat_name
        self.fan_status_name = Application.fan_status_name
        self.zone_damper_name = Application.zone_damper_name

        '''Algorithm Thresholds(Configurable)'''
        self.data_window = float(data_window)
        self.number_of_zones = float(number_of_zones)
        self.rht_on_threshold = float(rht_on_threshold)
        self.high_damper_threshold = float(high_damper_threshold)
        self.percent_damper_threshold = float(percent_damper_threshold)
        self.percent_reheat_threshold = float(percent_reheat_threshold)
        self.setpoint_allowable_deviation = float(setpoint_allowable_deviation)
        self.minimum_dat_stpt = float(minimum_dat_stpt)
        self.dat_reduction = float(dat_reduction)
    
    @classmethod
    def get_config_parameters(cls):
        '''
        Generate required configuration
        parameters with description for user
        '''
        return {
            'data_window': ConfigDescriptor(float, 'Data Window'),
            'number_of_zones': ConfigDescriptor(int, 'Number of Zones'),
            'high_damper_threshold': ConfigDescriptor(float, 'Value at which damper are considered nearly fully open'),
            'percent_reheat_threshold': ConfigDescriptor(float, 'Excess terminal re-heat Threshold'),
            'percent_damper_threshold': ConfigDescriptor(float, 'Excess terminal box damper threshold'),
            'setpoint_allowable_deviation': ConfigDescriptor(float, 'Supply-air Temperate Deadband'),
            'rht_on_threshold': ConfigDescriptor(float, 'Zone Is Reheating Threshold'),
            'minimum_dat_stpt': ConfigDescriptor(float, 'High DAT limit for auto-correction'),
            'dat_reduction': ConfigDescriptor(float, 'Increment applied to DAT SP when auto-correction is enabled'),
           }

    @classmethod
    def required_input(cls):
        '''
        Generate required inputs with description for
        user.
        '''
        return {
            cls.fan_status_name: InputDescriptor('SupplyFanStatus', 'AHU Supply Fan Status', count_min=1),
            cls.da_temp_stpt_name: InputDescriptor('DischargeAirTemperatureSetPoint','AHU Discharge-air temperature set-point', count_min=0, count_max=1),
            cls.da_temp_name: InputDescriptor('DischargeAirTemperature','AHU Discharge-air Temperature', count_min=1),
            cls.zone_reheat_name: InputDescriptor('ZoneReheatValvePosition','For accurate results this diagnostic requires'
                                                    ' terminal box data for all zones served by an AHU/RTU', count_min=2),
            cls.zone_damper_name: InputDescriptor('ZoneDamperPosition', 'For accurate results this diagnostic requires'
                                                  ' terminal box data for all zones served by an AHU/RTU', count_min=2)
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
        '''
        Check algorithm pre-quisites and assemble data set for analysis.
        '''
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
            msg_lst = [self.pre_msg0, self.pre_msg1]
            for item in msg_lst:
                if self.pre_requiste_messages.count(item) > (1/4)*len(self.pre_msg_time):
                    diagnostic_result.log(item, logging.INFO)
            self.pre_requiste_messages = []
            self.pre_msg_time = []

        for key, value in device_dict.items():
            if self.fan_status_name in key:
                if int(value) == 0:
                    self.pre_requiste_messages.append(sef.pre_msg0)
                    return diagnostic_result

        dat_data, zone_dmpr_data, rht_data = [], [] ,[]
        
        for key, value in device_dict.items():
            if key.startswith(self.da_temp_stpt_name):
                self.dat_stpt_values.append(value)

            elif key.startswith(self.da_temp_name):
                dat_data.append(value)

            elif key.startswith(self.zone_reheat_name):
                rht_data.append(value)

            elif key.startswith(self.zone_damper_name):
                zone_dmpr_data.append(value)
  
        if not dat_data or not rht_data:
            self.pre_requiste_messages.append(self.pre_msg1)
            return diagnostic_result

        datemp = sum(dat_data)/len(dat_data)

        for value in rht_data:
            if value > self.rht_on_threshold:
                self.total_reheat += 1
        for value in zone_dmpr_data:        
            if value > self.high_damper_threshold:
                self.total_damper += 1

        self.dat_values.append(datemp)

        self.timestamp.append(current_time)       
        time_check =  datetime.timedelta(minutes=self.data_window)

        if ((self.timestamp[-1]-self.timestamp[0]) >= time_check and
            len(self.timestamp) > 20):
            diagnostic_result = self.high_dat_sp(diagnostic_result)
        return diagnostic_result
 
    def high_dat_sp(self, result):
        """
        If the detected problems(s) are consistent then generate a fault message(s).
        If auto-correction is enabled and a problem is detected apply correction action.
        """
        time_d = self.timestamp[-1]-self.timestamp[0]
        time_d = int(time_d.total_seconds()/60) 

        avg_zone_reheat = self.total_reheat/(time_d*self.number_of_zones)
        avg_zone_reheat = avg_zone_reheat * 100

        avg_zone_damper = self.total_damper/(time_d*self.number_of_zones)
        avg_zone_damper = avg_zone_damper * 100
       
        avg_dat = (sum(self.dat_values))/(len(self.dat_values))
        avg_dat_stpt = None

        if self.dat_stpt_values:
            avg_dat_stpt = (sum(self.dat_stpt_values))/(len(self.dat_stpt_values))
            set_point_tracking = [abs(x-y) for x,y in zip(self.dat_stpt_values, self.dat_values)]
            set_point_tracking = sum(set_point_tracking)/(len(set_point_tracking)*avg_dat_stpt)*100
            if set_point_tracking > self.setpoint_allowable_deviation:
                result.log('Supply-air temperature is deviating significantly from the supply-air temperature set point.', logging.INFO)

        if  (avg_zone_damper > self.percent_damper_threshold and
            avg_zone_reheat < self.percent_reheat_threshold and self.dat_stpt_values):
            dat_stpt = avg_dat - self.dat_reduction
            '''Create diagnostic message for fault condition with auto-correction'''
            if dat_stpt >= self.minimum_dat_stpt:
                result.command(self.dat_stpt_name, dat_stpt)
                diagnostic_message = "The DAT has been detected to be too high. The DAT has been reduced to: "
                diagnostic_message += str(dat_stpt)
            else:
                '''Create diagnostic message for fault condition where the minimum DAT has been reached'''
                result.command(self.dat_stpt_name,self.minimum_dat_stpt)
                diagnostic_message = 'The supply-air temperature set point is at minimum value specified in configuration file.'
        elif  (avg_zone_damper > self.percent_damper_threshold and
            avg_zone_reheat < self.percent_reheat_threshold):
            '''Create diagnostic message for fault condition without auto-correction'''
            diagnostic_message ='The DAT has been detected to be too high but auto-correction is not enabled'
        else:
            '''Create diagnostic message that no re-tuning opportunity was detected: No Fault condition'''
            diagnostic_message = 'No re-tuning opportunity was detected during the high DAT diagnostic.'

        result.log(diagnostic_message,logging.INFO)

        self.dat_stpt_values = []
        self.dat_values = []
        self.timestamp = []
        self.pre_requiste_messages = []
        self.pre_msg_time = []
        self.total_reheat = 0
        self.total_damper = 0

        return result