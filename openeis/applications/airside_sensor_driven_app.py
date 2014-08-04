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
    """
    Air-side HVAC diagnostic to check the functionality of the air temperature sensors in an AHU/RTU.
    """
    
    '''Diagnostic Point Names (Must match Openeis data-type names)'''
    fan_status_name = "fan_status"
    oa_temp_name = "oa_temp"
    ma_temp_name = "ma_temp"
    ra_temp_name = "ra_temp"
    damper_signal_name = "damper_signal"
        
    def __init__(self,*args,data_window=None,mat_low_threshold=None,mat_high_threshold=None,
                rat_low_threshold=None,rat_high_threshold=None,oat_low_threshold=None,
                oat_high_threshold=None,temp_difference_threshold=None,
                oat_mat_check=None,open_damper_threshold=None,**kwargs):
        super().__init__(*args,**kwargs)
        
        self.oa_temp_values = []
        self.ra_temp_values = []
        self.ma_temp_values = []
        self.timestamp = []
        self.pre_requiste_messages = []
        self.pre_msg_time = []
        self.open_damper_oat = []
        self.open_damper_mat = []
        
        '''Pre-requistes not-met messages'''
        self.pre_msg1 = 'Supply fan is off, current data will not be used for diagnostics.'
        self.pre_msg2 = 'Outside-air temperature is outside high/low operating limits, check the functionality of the temperature sensor.'
        self.pre_msg3 = 'Mixed-air temperature is outside high/low operating limits, check the functionality of the temperature sensor.'
        self.pre_msg4 = 'Return-air temperature is outside high/low operating limits, check the functionality of the temperature sensor.'
        Application.temp_sensor_problem = None

        '''Point names (Configurable)'''
        self.fan_status_name = Application.fan_status_name
        self.oa_temp_name =  Application.oa_temp_name
        self.ra_temp_name =  Application.ra_temp_name
        self.ma_temp_name =  Application.ma_temp_name
        self.damper_signal_name = Application.damper_signal_name

        '''Algorithm thresholds (Configurable)'''
        self.data_window = float(data_window)
        self.mat_low_threshold = float(mat_low_threshold)
        self.mat_high_threshold = float(mat_high_threshold)
        self.oat_low_threshold = float(oat_low_threshold)
        self.oat_high_threshold = float(oat_high_threshold)
        self.rat_low_threshold = float(rat_low_threshold)
        self.rat_high_threshold = float(rat_high_threshold)
        self.temp_difference_threshold = float(temp_difference_threshold)
        self.oat_mat_check = float(oat_mat_check)
        self.open_damper_threshold  = float(open_damper_threshold)

    @classmethod
    def get_config_parameters(cls):
        '''
        Generate required configuration
        parameters with description for user
        '''
        return {
            'data_window': ConfigDescriptor(float, 'Data Window'),
            'mat_low_threshold': ConfigDescriptor(float, 'Mixed-air sensor low limit'),
            'mat_high_threshold': ConfigDescriptor(float, 'Mixed-air sensor high limit'),
            'rat_low_threshold': ConfigDescriptor(float, 'Return-air sensor low limit'),
            'rat_high_threshold': ConfigDescriptor(float, 'Return-air sensor high limit'),
            'oat_low_threshold': ConfigDescriptor(float, 'Outdoor-air sensor low limit'),
            'oat_high_threshold': ConfigDescriptor(float, 'Outdoor-air sensor high limit'),
            'temp_difference_threshold': ConfigDescriptor(float,'Air temperature consistency check threshold'),
            'oat_mat_check': ConfigDescriptor(float,'Consistency check for OAT and MAT when outdoor-air damper is 100% open'),
            'open_damper_threshold': ConfigDescriptor(float, 'Threshold below 100% in which damper is considered fully open')
           }

    @classmethod
    def required_input(cls):
        '''
        Generate required inputs with description for
        user.
        '''
        return {
            cls.fan_status_name: InputDescriptor('SupplyFanStatus', 'AHU Supply Fan Status', count_min=1),
            cls.oa_temp_name: InputDescriptor('OutdoorAirTemperature','AHU or building outdoor-air temperature', count_min=1),
            cls.ma_temp_name: InputDescriptor('MixedAirTemperature','AHU mixed-air temperature', count_min=1),
            cls.ra_temp_name: InputDescriptor('ReturnAirTemperature','AHU return-air temperature',count_min=1),
            cls.damper_signal_name: InputDescriptor('OutdoorDamperSignal','AHU outdoor-air damper signal', count_min=1)
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
        diagnostic_topic = topics[cls.oa_temp_name][0]
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
            msg_lst = [self.pre_msg1, self.pre_msg2, self.pre_msg3, self.pre_msg4]
            for item in msg_lst:
                if self.pre_requiste_messages.count(item) > (0.25)*(len(self.pre_msg_time)+len(self.timestamp)):
                    diagnostic_result.log(item, logging.INFO)
            self.pre_requiste_messages = []
            self.pre_msg_time = [] 

        limit_check = False
        for key, value in device_dict.items():
            if key.startswith(self.fan_status_name): 
                if int(value) == 0:
                    self.pre_requiste_messages.append(self.pre_msg1)
                    return diagnostic_result

        damper_data, oatemp_data, matemp_data = [], [], []
        ratemp_data = [] 

        for key, value in device_dict.items():
            if key.startswith(self.damper_signal_name): 
                damper_data.append(value)

            elif key.startswith(self.oa_temp_name):
                oatemp_data.append(value)
                
            elif key.startswith(self.ma_temp_name):
                matemp_data.append(value)

            elif key.startswith(self.ra_temp_name):
                ratemp_data.append(value)

        oatemp = (sum(oatemp_data)/len(oatemp_data))
        ratemp = (sum(ratemp_data)/len(ratemp_data))
        matemp = (sum(matemp_data)/len(matemp_data))
        damper_signal = (sum(damper_data)/len(damper_data))

        if oatemp > self.oat_high_threshold or oatemp < self.oat_low_threshold:
            limit_check = True
            self.pre_requiste_messages.append(self.pre_msg2)
        if matemp > self.mat_high_threshold or matemp < self.mat_low_threshold:
            limit_check = True
            self.pre_requiste_messages.append(self.pre_msg3)
        if ratemp > self.rat_high_threshold or ratemp < self.rat_low_threshold:
            limit_check = True
            self.pre_requiste_messages.append(self.pre_msg4)

        if limit_check:
            return diagnostic_result

        if (damper_signal) > self.open_damper_threshold :
            self.open_damper_oat.append(oatemp), self.open_damper_mat.append(matemp)

        self.oa_temp_values.append(oatemp), self.ma_temp_values.append(matemp),
        self.ra_temp_values.append(ratemp), self.timestamp.append(current_time)

        time_check =  datetime.timedelta(minutes=(self.data_window))

        if ((self.timestamp[-1]-self.timestamp[0]) >= time_check and
            len(self.timestamp) > 10):
            diagnostic_result = self.air_temp_sensor_diagnostic(diagnostic_result)
        return diagnostic_result
  
    def air_temp_sensor_diagnostic(self, result):
        """
        If the detected problems(s) are consistent then generate a fault message(s).
        """
        avg_oa_temp = sum(self.oa_temp_values)/len(self.oa_temp_values)
        avg_ra_temp = sum(self.ra_temp_values)/len(self.ra_temp_values)
        avg_ma_temp = sum(self.ma_temp_values)/len(self.ma_temp_values)

        self.oa_temp_values = []
        self.ra_temp_values = []
        self.ma_temp_values = []
        self.pre_requiste_messages = []
        self.pre_msg_time = [] 
        self.timestamp = []
        
        if len(self.open_damper_oat) > 50:
            mat_oat_diff_list = [abs(x-y)for x,y in zip(self.open_damper_oat,self.open_damper_mat)]
            open_damper_check = sum(mat_oat_diff_list)/len(mat_oat_diff_list)
            if open_damper_check > self.oat_mat_check:
                Application.temp_sensor_problem = True
                diagnostic_message = 'OAT and MAT and sensor readings are not consistent \
                                      when the outdoor-air damper is fully open'
            self.open_damper_oat = []
            self.open_damper_mat = []

        if ((avg_oa_temp - avg_ma_temp) > self.temp_difference_threshold and 
            (avg_ra_temp - avg_ma_temp) > self.temp_difference_threshold):
            diagnostic_message = 'Temperature sensor problem detected.  Mixed-air temperature is less than outdoor-air and return-air temperature.'
            Application.temp_sensor_problem = True

        elif((avg_ma_temp - avg_oa_temp) > self.temp_difference_threshold and 
             (avg_ma_temp - avg_ra_temp) > self.temp_difference_threshold):
            diagnostic_message = 'Temperature sensor problem detected.  Mixed-air temperature is greater than outdoor-air and return-air temperature.'
            Application.temp_sensor_problem = True

        elif Application.temp_sensor_problem == None or not Application.temp_sensor_problem:
            diagnostic_message = 'No Temperature sensor problems were detected.'
            Application.temp_sensor_problem = False

        result.log(diagnostic_message, logging.INFO)
        return result