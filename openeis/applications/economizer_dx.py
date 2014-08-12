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
import datetime, logging
from collections import Counter
from openeis.applications import (DrivenApplicationBaseClass,
                                  OutputDescriptor, 
                                  ConfigDescriptor,
                                  InputDescriptor,
                                  Results)

econ1 = 'Temperature Sensor Dx'
econ2 = 'Economizer Correctly ON Dx'
econ3 = 'Economizer Correctly OFF Dx'
econ4 = 'Excess Outdoor-air Intake Dx'
econ5 = 'Insufficient Outdoor-air Intake Dx'
time_format = '%m/%d/%Y %H:%M'

class Application(DrivenApplicationBaseClass):
    '''
    Air-side HVAC diagnostic to check if an AHU/RTU is not economizing when it should.
    '''
    '''Diagnostic Point Names (Must match OpenEIS data-type names)'''
    fan_status_name = 'fan_status'
    oa_temp_name = 'oa_temp'
    ma_temp_name = 'ma_temp'
    ra_temp_name = 'ra_temp'
    damper_signal_name = 'damper_signal'
    cool_call_name = 'cool_call'
    def __init__ (self,*args, economizer_type=None,
                  device_type=None,temp_deadband=None,data_window=None,
                   
                  mat_low_threshold=None,mat_high_threshold=None,oat_low_threshold=None,
                  oat_high_threshold=None,rat_low_threshold=None,rat_high_threshold=None,
                    
                  temp_difference_threshold=None,
                  oat_mat_check=None,open_damper_threshold=None,
                    
                  oaf_economizing_threshold=None,oaf_temperature_threshold=None,cooling_enabled_threshold=None,
                  minimum_damper_signal = None,
                    
                  excess_oaf_threshold=None,
                  desired_oaf=None,
                    
                  ventilation_oaf_threshold=None,
                  insufficient_damper_threshold=None,temp_damper_threshold=None,tonnage=None,eer=None, data_sample_rate=None,
                  **kwargs):
        super().__init__(*args, **kwargs)

        self.fan_status_name = Application.fan_status_name
        self.oa_temp_name = Application.oa_temp_name
        self.ra_temp_name = Application.ra_temp_name
        self.ma_temp_name = Application.ma_temp_name
        self.damper_signal_name = Application.damper_signal_name
        self.cool_call_name = Application.cool_call_name
        
        self.device_type = device_type.lower()
        
        temp = [x.strip() for x in economizer_type.split(',')]
        self.economizer_type = [float(element) if (len(temp) == 2 and (element != 'DDB' and element != 'HL')) else element for element in temp]   #0 for differential dry bulb and 1 for high limit
        self.economizer_type = [element.lower() if isinstance(element,str) else element for element in self.economizer_type]

        Application.pre_requiste_messages = []
        Application.pre_msg_time = []

        '''Algorithm thresholds (Configurable)'''
        self.data_window = float(data_window)
        self.mat_low_threshold = float(mat_low_threshold)
        self.mat_high_threshold = float(mat_high_threshold)
        self.oat_low_threshold = float(oat_low_threshold)
        self.oat_high_threshold = float(oat_high_threshold)
        self.rat_low_threshold = float(rat_low_threshold)
        self.rat_high_threshold = float(rat_high_threshold)
        self.temp_deadband = float(temp_deadband)
        self.cooling_enabled_threshold = float(cooling_enabled_threshold)
        cfm = tonnage*400.0
        
        '''Pre-requisite messages'''
        self.pre_msg0 = 'Air temperature sensor problem detected, economizer diagnostics depend on reliable air temperature sensor readings.'
        self.pre_msg1 = 'Supply fan is off, current data will not be used for diagnostics.'
        self.pre_msg2 = 'Supply fan status data is missing from input(device or csv), could not verify system was ON.'
        self.pre_msg3 = 'Missing required data for diagnostic: Check BACnet configuration or CSV file input for outside-air temperature.'
        self.pre_msg4 = 'Missing required data for diagnostic: Check BACnet configuration or CSV file input for return-air temperature.'
        self.pre_msg5 = 'Missing required data for diagnostic: Check BACnet configuration or CSV file input for mixed-air temperature.'
        self.pre_msg6 = 'Missing required data for diagnostic: Check BACnet configuration or CSV file input for damper signal.'
        self.pre_msg7 = ''.join(['Missing required data for diagnostic: ',
                                'Check BACnet configuration or CSV file input for cooling call',
                                ' (AHU cooling coil, RTU cooling call or compressor command).'])
        self.pre_msg8 = 'Outside-air temperature is outside high/low operating limits, check the functionality of the temperature sensor.'
        self.pre_msg9 = 'Return-air temperature is outside high/low operating limits, check the functionality of the temperature sensor.'
        self.pre_msg10 = 'Mixed-air temperature is outside high/low operating limits, check the functionality of the temperature sensor.'
        self.pre_msg11 = 'Air temperature sensor problem detected, economizer diagnostics depend on reliable air temperature sensor readings.'
        self.pre_msg12 = 'Must verify temperature sensors functionality before running economizer diagnostics.'
        self.pre_msg13= 'Conditions are consistently not favorable for diagnostics, try again later.'

        self.econ1 = temperature_sensor_dx(data_window, temp_difference_threshold,oat_mat_check,temp_damper_threshold)

        self.econ2 = econ_correctly_on(oaf_economizing_threshold, open_damper_threshold,
                                self.economizer_type, oaf_temperature_threshold,data_window, cfm, eer, data_sample_rate)
        self.econ3 = econ_correctly_off(device_type,self.economizer_type,data_window,
                                        minimum_damper_signal,cooling_enabled_threshold,desired_oaf, cfm, eer, data_sample_rate)
        self.econ4 = excess_oa_intake(self.economizer_type, device_type,data_window, excess_oaf_threshold,
                                      minimum_damper_signal, desired_oaf, oaf_temperature_threshold, cfm, eer, data_sample_rate)
        self.econ5 = insufficient_oa_intake(device_type, self.economizer_type, data_window, ventilation_oaf_threshold,minimum_damper_signal,
                                            insufficient_damper_threshold, desired_oaf)
        
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
            'temp_deadband': ConfigDescriptor(float,'Economizer control temperature deadband'),
            'minimum_damper_signal': ConfigDescriptor(float, 'Minimum outdoor-air damper command'),
            'cooling_enabled_threshold': ConfigDescriptor(float, 'Amount cooling coil valve must be open for diagnostic to consider unit in cooling mode'),
            'insufficient_damper_threshold': ConfigDescriptor(float, 'Minimum damper position to ensure proper ventilation'),
            'ventilation_oaf_threshold':  ConfigDescriptor(float, 'Threshold on OAF diagnostics'),
            'desired_oaf':  ConfigDescriptor(float, 'The desired minimum OAF'),
            'excess_oaf_threshold':  ConfigDescriptor(float, 'Value above the desired OAF that the OA intake will be considered excessive'),
            'economizer_type': ConfigDescriptor(string, 'Economizer type:  DDB - differential dry bulb HL - High limit'),
            'open_damper_threshold': ConfigDescriptor(float, 'Threshold below 100% in which damper is considered fully open'),
            'oaf_economizing_threshold': ConfigDescriptor(float,'Amount below 1.0 in which the OAF is considered sufficient to economizer.'),
            'oaf_temperature_threshold': ConfigDescriptor(float,'Required difference between OAT and RAT for accurate diagnostic'),
            'device_type': ConfigDescriptor(string, 'Device type "RTU" or "AHU"'),
            'temp_difference_threshold': ConfigDescriptor(float, 'Threshold for detecting temperature sensor problems'),
            'oat_mat_check': ConfigDescriptor(float, 'Threshold for OAT and MAT consistency check for times when the damper is 100% open'),
            'temp_damper_threshold': ConfigDescriptor(float,'Damper position to check for OAT/MAT consistency'),
            'tonnage': ConfigDescriptor(float, 'AHU/RTU cooling capacity in tons'),
            'eer': ConfigDescriptor(float, 'AHU/RTU rated EER')
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
            cls.damper_signal_name: InputDescriptor('OutdoorDamperSignal','AHU outdoor-air damper signal', count_min=1),
            cls.cool_call_name: InputDescriptor('CoolingCall', 'AHU cooling coil command or RTU coolcall or compressor command', count_min=1)
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
        result = super().output_format(input_object)
        
        topics = input_object.get_topics()
        diagnostic_topic = topics[cls.fan_status_name][0]
        diagnostic_topic_parts = diagnostic_topic.split('/')
        output_topic_base = diagnostic_topic_parts[:-1]
        datetime_topic = '/'.join(output_topic_base+['economizer_dx', 'date'])
        message_topic = '/'.join(output_topic_base+['economizer_dx', 'message'])
        diagnostic_name = '/'.join(output_topic_base+['economizer_dx', 'diagnostic_name'])
        energy_impact = '/'.join(output_topic_base+['economizer_dx', 'energy_impact'])
        color_code = '/'.join(output_topic_base+['economizer_dx', 'color_code'])
        
        output_needs = {
            'Economizer_dx': {
                'datetime': OutputDescriptor('datetime', datetime_topic),
                'diagnostic_name': OutputDescriptor('string', diagnostic_name),
                'diagnostic_message': OutputDescriptor('string', message_topic),
                'energy_impact': OutputDescriptor('float', energy_impact),
                'color_code': OutputDescriptor('string', color_code)
                }
            }
        result.update(output_needs)
        return result

    def run(self,current_time,points):
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

        Application.pre_msg_time.append(current_time)
        message_check =  datetime.timedelta(minutes=(self.data_window))
 
        if (Application.pre_msg_time[-1]-Application.pre_msg_time[0]) >= message_check:
            msg_lst = [self.pre_msg0, self.pre_msg1, self.pre_msg2, self.pre_msg3, self.pre_msg4, 
                       self.pre_msg5,self.pre_msg6, self.pre_msg7, self.pre_msg8, self.pre_msg9, self.pre_msg10,
                       self.pre_msg11, self.pre_msg12, self.pre_msg13]
            for item in msg_lst:
                if Application.pre_requiste_messages.count(item) > (0.25)*len(Application.pre_msg_time):
                    diagnostic_result.log(item, logging.INFO)
            Application.pre_requiste_messages = []
            Application.pre_msg_time = []

        fan_stat_check = False
        for key, value in device_dict.items():
            if key.startswith(self.fan_status_name): 
                fan_stat_check = True
                if int(value) == 0:
                    self.pre_requiste_messages.append(self.pre_msg1)
                    return diagnostic_result
        if not fan_stat_check:
            Application.pre_requiste_messages.append(self.pre_msg2)
            return diagnostic_result

        damper_data, oatemp_data, matemp_data = [], [], []
        ratemp_data, cooling_data = [], [] 

        for key, value in device_dict.items():
            if key.startswith(self.damper_signal_name): 
                damper_data.append(value)

            elif key.startswith(self.oa_temp_name):
                oatemp_data.append(value)
                
            elif key.startswith(self.ma_temp_name):
                matemp_data.append(value)

            elif key.startswith(self.ra_temp_name):
                ratemp_data.append(value)
            
            elif key.startswith(self.cool_call_name):
                cooling_data.append(value)
        
        if not oatemp_data:
            Application.pre_requiste_messages.append(self.pre_msg3)
 
        if not ratemp_data:
            Application.pre_requiste_messages.append(self.pre_msg4)
           
        if not matemp_data:
            Application.pre_requiste_messages.append(self.pre_msg5)
 
        if not damper_data:
            Application.pre_requiste_messages.append(self.pre_msg6)
           
        if not cooling_data:
            Application.pre_requiste_messages.append(self.pre_msg7)

        if not (oatemp_data and ratemp_data and matemp_data and
            damper_data and cooling_data):
            return diagnostic_result
        
        oatemp = (sum(oatemp_data)/len(oatemp_data))
        ratemp = (sum(ratemp_data)/len(ratemp_data))
        matemp = (sum(matemp_data)/len(matemp_data))
        damper_signal = (sum(damper_data)/len(damper_data))

        limit_check = False
        if oatemp < self.oat_low_threshold or oatemp > self.oat_high_threshold:
            Application.pre_requiste_messages.append(self.pre_msg8)
            limit_check = True
        if ratemp < self.rat_low_threshold or ratemp > self.rat_high_threshold:
            Application.pre_requiste_messages.append(self.pre_msg9)
            limit_check = True
        if matemp < self.mat_low_threshold or matemp > self.mat_high_threshold:
            Application.pre_requiste_messages.append(self.pre_msg10)
            limit_check = True

        if limit_check:
            return diagnostic_result
        
        device_type_error = False
        if self.device_type == 'ahu':
            cooling_valve = sum(cooling_data)/len(cooling_data)
            if cooling_valve > self.cooling_enabled_threshold: 
                cooling_call = True
            else:
                cooling_call = False
        elif self.device_type == 'rtu':
            cooling_call = int(max(cooling_data))
        else:
            device_type_error = True
            diagnostic_result.log('device_type must be specified as "AHU" or "RTU" Check Configuration input.', logging.INFO)
            
        if device_type_error:
            return diagnostic_result
        
        if self.economizer_type[0] == 'ddb':
            if abs(oatemp - ratemp) <= self.temp_deadband:
                Application.pre_requiste_messages.append(self.pre_msg13)
                return diagnostic_result
            economizer_conditon = (oatemp < (ratemp - self.temp_deadband))
        else:
            if abs(oatemp - self.economizer_type[1]) <= self.temp_deadband:
                Application.pre_requiste_messages.append(self.pre_msg13)
                return diagnostic_result
            economizer_conditon = (oatemp < (self.economizer_type[1] - self.temp_deadband))

        diagnostic_result = self.econ1.econ_alg1(diagnostic_result,cooling_call, oatemp, ratemp, 
                                                                    matemp, damper_signal,current_time)

        try:
            if temperature_sensor_dx.temp_sensor_problem == None:
                Application.pre_requiste_messages.append(self.pre_msg12)
                return diagnostic_result
            elif temperature_sensor_dx.temp_sensor_problem != None and self.pre_msg12 in Application.pre_requiste_messages:
                Application.pre_requiste_messages = [x for x in Application.pre_requiste_messages if x != self.pre_msg12]
            if temperature_sensor_dx.temp_sensor_problem == True:
                Application.pre_requiste_messages.append(self.pre_msg11)
                return diagnostic_result
        except:
            pass
        diagnostic_result = self.econ2.econ_alg2(diagnostic_result,cooling_call, oatemp, ratemp, 
                                                                    matemp, damper_signal,economizer_conditon,current_time)
        diagnostic_result = self.econ3.econ_alg3(diagnostic_result,cooling_call, oatemp, ratemp, 
                                                                    matemp, damper_signal,economizer_conditon,current_time)
        diagnostic_result = self.econ4.econ_alg4(diagnostic_result,cooling_call, oatemp, ratemp, 
                                                                    matemp, damper_signal,economizer_conditon,current_time)
        diagnostic_result = self.econ5.econ_alg5(diagnostic_result,cooling_call, oatemp, ratemp, 
                                                                    matemp, damper_signal,economizer_conditon,current_time)
        return diagnostic_result
    
    
class temperature_sensor_dx(object):
    """
    Air-side HVAC diagnostic to check the functionality of the air temperature sensors in an AHU/RTU.
    """
    def __init__(self, data_window,temp_difference_threshold,oat_mat_check,temp_damper_threshold):
        self.oa_temp_values = []
        self.ra_temp_values = []
        self.ma_temp_values = []
        self.timestamp = []
        self.open_damper_oat = []
        self.open_damper_mat = []

        temperature_sensor_dx.temp_sensor_problem = None

        '''Algorithm thresholds (Configurable)'''
        self.data_window = float(data_window)
        self.temp_difference_threshold = float(temp_difference_threshold)
        self.oat_mat_check = float(oat_mat_check)
        self.temp_damper_threshold  = float(temp_damper_threshold)
 
    def econ_alg1(self, diagnostic_result,cooling_call, oatemp, ratemp, matemp, damper_signal, current_time):
        '''
        Check algorithm pre-quisites and assemble data set for analysis.
        '''
        if (damper_signal) > self.temp_damper_threshold :
            self.open_damper_oat.append(oatemp)
            self.open_damper_mat.append(matemp)
 
        self.oa_temp_values.append(oatemp)
        self.ma_temp_values.append(matemp)
        self.ra_temp_values.append(ratemp)
        self.timestamp.append(current_time)
        
        time_check =  datetime.timedelta(minutes=(self.data_window))

        if ((self.timestamp[-1]-self.timestamp[0]) >= time_check and
            len(self.timestamp) > 10):
            diagnostic_result = self.temperature_sensor_dx(diagnostic_result, current_time)
        return diagnostic_result
   
    def temperature_sensor_dx(self, result, current_time):
        """
        If the detected problems(s) are consistent then generate a fault message(s).
        """
        avg_oa_temp = sum(self.oa_temp_values)/len(self.oa_temp_values)
        avg_ra_temp = sum(self.ra_temp_values)/len(self.ra_temp_values)
        avg_ma_temp = sum(self.ma_temp_values)/len(self.ma_temp_values)
        color_code = 'GREEN'
        self.oa_temp_values = []
        self.ra_temp_values = []
        self.ma_temp_values = []
        Application.pre_requiste_messages = []
        Application.pre_msg_time = [] 
        self.timestamp = []
        dx_table = {}
        
        if len(self.open_damper_oat) > 50:
            mat_oat_diff_list = [abs(x-y)for x,y in zip(self.open_damper_oat,self.open_damper_mat)]
            open_damper_check = sum(mat_oat_diff_list)/len(mat_oat_diff_list)

            if open_damper_check > self.oat_mat_check:
                temperature_sensor_dx.temp_sensor_problem = True
                diagnostic_message = '{name}: OAT and MAT and sensor readings are not consistent \
                                      when the outdoor-air damper is fully open'.format(name=econ1)
                color_code = 'RED'
                dx_table = {
                    'datetime': str(current_time), 
                    'diagnostic_name': econ1, 
                    'diagnostic_message': diagnostic_message, 
                    'energy_impact': 0.0,
                    'color_code': color_code
                    }
                result.insert_table_row('Economizer_dx', dx_table)
            self.open_damper_oat = []
            self.open_damper_mat = []
 
        if ((avg_oa_temp - avg_ma_temp) > self.temp_difference_threshold and 
            (avg_ra_temp - avg_ma_temp) > self.temp_difference_threshold):
            diagnostic_message = ('{name}: Temperature sensor problem detected.' 
                                 'Mixed-air temperature is less than outdoor-air and return-air temperature'.format(name=econ1))
            color_code = 'RED'
            dx_table = {
                    'datetime': str(current_time), 
                    'diagnostic_name': econ1, 
                    'diagnostic_message': diagnostic_message, 
                    'energy_impact': 0.0,
                    'color_code': color_code
                    }
            temperature_sensor_dx.temp_sensor_problem = True
 
        elif((avg_ma_temp - avg_oa_temp) > self.temp_difference_threshold and 
             (avg_ma_temp - avg_ra_temp) > self.temp_difference_threshold):
            diagnostic_message = ('{name}: Temperature sensor problem detected. '  
                                 'Mixed-air temperature is greater than outdoor-air and return-air temperature'.format(name=econ1))
            temperature_sensor_dx.temp_sensor_problem = True
            color_code = 'RED'
            dx_table = {
                    'datetime': str(current_time), 
                    'diagnostic_name': econ1, 
                    'diagnostic_message': diagnostic_message, 
                    'energy_impact': 0.0,
                    'color_code': color_code
                    }
 
        elif temperature_sensor_dx.temp_sensor_problem == None or not temperature_sensor_dx.temp_sensor_problem:
            diagnostic_message = '{name}: No problems were detected'.format(name=econ1)
            temperature_sensor_dx.temp_sensor_problem = False
            color_code = 'GREEN'
            dx_table = {
                    'datetime': str(current_time), 
                    'diagnostic_name': econ1, 
                    'diagnostic_message': diagnostic_message, 
                    'energy_impact': 0.0,
                    'color_code': color_code
                    }
        result.insert_table_row('Economizer_dx', dx_table)
        result.log(diagnostic_message, logging.INFO)
        return result
    

class econ_correctly_on(object):
    '''
    Air-side HVAC diagnostic to check if an AHU/RTU is not economizing when it should.
    '''
    def __init__(self,oaf_economizing_threshold, open_damper_threshold,economizer_type, 
                oaf_temperature_threshold,data_window, cfm, eer, data_sample_rate):
        
        self.oa_temp_values = []
        self.ra_temp_values = []
        self.ma_temp_values = []
        self.damper_signal_values = []
        self.timestamp = []
        self.data_sample_rate = data_sample_rate
        self.economizer_type = economizer_type
        self.oaf_temperature_threshold = float(oaf_temperature_threshold)
        self.open_damper_threshold = float(open_damper_threshold)
        self.oaf_economizing_threshold = float(oaf_economizing_threshold)
        self.data_window = float(data_window)
        self.cfm = cfm
        self.eer = float(eer)
        '''Algorithm result messages'''
        self.alg_result_messages =['{name}: Conditions are favorable for economizing but the damper is frequently below 100% open'.format(name=econ2),
                                   '{name}: No problems detected'.format(name=econ2),
                                   '{name}: Conditions are favorable for economizing and the damper is 100% '
                                   'open but the OAF indicates the unit is not brining in near 100% OA'.format(name=econ2)]
        
    def econ_alg2(self, diagnostic_result, cooling_call, oatemp, ratemp, matemp, damper_signal, economizer_conditon,current_time):
        if not cooling_call:
            diagnostic_result.log('The unit is not cooling, data corresponding to {timestamp} will '
                                  'not be used for {name} diagnostic.'.format(timestamp=str(current_time),name=econ2))
            return diagnostic_result
        
        if not economizer_conditon:
            diagnostic_result.log('{name}: Conditions are not favorable for economizing, data ' 
                                  'corresponding to {timestamp} will not be used'.format(timestamp=str(current_time),name=econ2))
            return diagnostic_result
    
        if abs(oatemp - ratemp) < self.oaf_temperature_threshold:
            diagnostic_result.log('{name}: Conditions are not favorable for OAF calculation, data ' 
                                  'corresponding to {timestamp} will not be used'.format(timestamp=str(current_time),name=econ2))
            return diagnostic_result

        self.oa_temp_values.append(oatemp)
        self.ma_temp_values.append(matemp) 
        self.ra_temp_values.append(ratemp)
        self.timestamp.append(current_time)
        self.ra_temp_values.append(damper_signal)

        time_check =  datetime.timedelta(minutes=(self.data_window))

        if ((self.timestamp[-1]-self.timestamp[0]) >= time_check and
            len(self.timestamp) >= 10):
            diagnostic_result = self.not_economizing_when_needed(diagnostic_result, current_time)
        return diagnostic_result
       
    def not_economizing_when_needed(self, result, current_time):
        '''
        If the detected problems(s) are consistent then generate a fault message(s).
        '''
        oaf = [(m-r)/(o-r) for o,r,m in zip(self.oa_temp_values,self.ra_temp_values,self.ma_temp_values)]
        avg_oaf = sum(oaf)/len(oaf)*100.0
        avg_damper_signal = sum(self.damper_signal_values)/len(self.damper_signal_values)
        color_code = 'GREEN'
        energy_impact = 0

        if  avg_damper_signal < self.open_damper_threshold:
            diagnostic_message = (self.alg_result_messages[0])
            color_code = 'RED'
        else:
            if (100.0 - avg_oaf) <= self.oaf_economizing_threshold:
                diagnostic_message = (self.alg_result_messages[1])
                color_code = 'GREEN'
            else:
                diagnostic_message = (self.alg_result_messages[2])
                color_code = 'RED'

        energy_calc = [(1.08*self.cfm*(ma - oa)/(1000.0*self.eer)) for
                       ma, oa in zip(self.ma_temp_values, self.oa_temp_values) 
                       if ((ma - oa) > 0 and color_code == 'RED')]
        
        if energy_calc:
            dx_time = (len(energy_calc) - 1)*self.data_sample_rate if len(energy_calc) > 1 else 1.0
            energy_impact = (sum(energy_calc)*60.0)/(len(energy_calc)*dx_time)

        dx_table = {
                    'datetime': str(current_time), 
                    'diagnostic_name': econ2, 'diagnostic_message': diagnostic_message, 
                    'energy_impact': energy_impact,
                    'color_code': color_code
                    }
        result.insert_table_row('Economizer_dx', dx_table)
        result.log(diagnostic_message, logging.INFO)

        Application.pre_msg_time = []
        Application.pre_requiste_messages = []
        self.timestamp = []
        self.oa_temp_values = []
        self.ra_temp_values = []
        self.ma_temp_values = []
        diagnostic_message = []
        return result

   
class econ_correctly_off(object):
    '''
    Air-side HVAC diagnostic to check if an AHU/RTU is economizing when it should not.
    '''
    def __init__(self,device_type,economizer_type,data_window,
                minimum_damper_signal,cooling_enabled_threshold, desired_oaf, cfm, eer, data_sample_rate):
        self.oa_temp_values = []
        self.ra_temp_values = []
        self.ma_temp_values = []
        self.damper_signal_values = []
        self.cool_call_values = []
        self.cfm = cfm
        self.eer = float(eer)
        self.timestamp = []
        self.economizer_diagnostic2_result = []
 
        '''Algorithm result messages'''
        self.alg_result_messages =['{name}: Unit should be economizing, no problem detected'.format(name=econ3),
                                   '{name}: The outdoor-air damper should be at the minimum position but is significantly above that value'.format(name=econ3),
                                   '{name}: No problems detected'.format(name=econ3),
                                   '{name}: The diagnostic led to inconclusive results'.format(name=econ3)]
        self.data_sample_rate = data_sample_rate
        self.device_type = device_type
        self.data_window = float(data_window)
        self.economizer_type = economizer_type
        self.minimum_damper_signal = float(minimum_damper_signal)
        self.cooling_enabled_threshold = float(cooling_enabled_threshold)
        self.desired_oaf = float(desired_oaf)
    
    def econ_alg3(self, diagnostic_result,cooling_call, oatemp, ratemp, matemp, damper_signal, economizer_conditon, current_time):
        '''
        Check algorithm pre-quisites and economizer conditions (Problem or No Problem).
        '''
        if economizer_conditon and cooling_call:
            self.economizer_diagnostic2_result.append(1.0)
        elif economizer_conditon:
            self.economizer_diagnostic2_result.append(4.0)
        else:
            if damper_signal <= self.minimum_damper_signal:
                self.economizer_diagnostic2_result.append(3.0)
            else:
                self.economizer_diagnostic2_result.append(2.0)

        self.oa_temp_values.append(oatemp)
        self.ma_temp_values.append(matemp) 
        self.ra_temp_values.append(ratemp)
        self.timestamp.append(current_time)
        self.ra_temp_values.append(damper_signal)
        
        time_check =  datetime.timedelta(minutes=(self.data_window))
        self.timestamp.append(current_time)
 
        if ((self.timestamp[-1]-self.timestamp[0]) >= time_check and
            len(self.timestamp) >= 30):
            diagnostic_result = self.economizing_when_not_needed(diagnostic_result, current_time)
        return diagnostic_result
  
    def economizing_when_not_needed(self, result, current_time):
        '''
        If the detected problems(s) are consistent then generate a fault message(s).
        '''
        desired_oaf = self.desired_oaf/100.0
        alg_message_count = Counter(self.economizer_diagnostic2_result)
        alg_message_count = alg_message_count.most_common(1)
        color_code = 'GREEN'
        energy_impact = 0

        if alg_message_count[0][1] > len(self.timestamp)*(0.35):
            diagnostic_message = self.alg_result_messages[int(alg_message_count[0][0]-1)]
            if alg_message_count[0][0] == 1.0 or alg_message_count[0][0] == 3.0:
                color_code = 'GREEN'
            elif alg_message_count[0][0] == 2.0:
                color_code = 'RED'
            else:
                color_code = 'GREY'
        else:
            color_code = 'GREY'
            diagnostic_message = 'This diagnostic was inconclusive.'

        energy_calc = [(1.08*self.cfm*(ma - (oa*desired_oaf + (ra*(1.0-desired_oaf))))/(1000.0*self.eer)) for
                       ma, oa, ra in zip(self.ma_temp_values, self.oa_temp_values, self.ra_temp_values) 
                       if (ma - (oa*desired_oaf + (ra*(1.0-desired_oaf))) > 0 and color_code == 'RED')]

        if energy_calc:
            dx_time = (len(energy_calc) - 1)*self.data_sample_rate if len(energy_calc) > 1 else 1.0
            energy_impact = (sum(energy_calc)*60.0)/(len(energy_calc)*dx_time)

        dx_table = {'datetime': str(current_time), 
                    'diagnostic_name': econ3, 'diagnostic_message': diagnostic_message, 
                    'energy_impact': energy_impact,
                    'color_code': color_code
                    }

        result.insert_table_row('Economizer_dx', dx_table)
        result.log(diagnostic_message, logging.INFO)
        Application.pre_msg_time = []
        Application.pre_requiste_messages = []
        self.timestamp = []
        self.economizer_diagnostic2_result = []
        return result
    

class excess_oa_intake(object):
    '''
    Air-side HVAC diagnostic to check if an AHU/RTU bringing in excess outdoor air.
    '''
    def __init__(self,economizer_type,device_type,data_window,excess_oaf_threshold,
                minimum_damper_signal,desired_oaf, oaf_temperature_threshold, cfm, eer, data_sample_rate):

        self.oa_temp_values = []
        self.ra_temp_values = []
        self.ma_temp_values = []
        self.damper_signal_values = []
        self.cool_call_values = []
        self.cfm = cfm
        self.eer = float(eer)
        self.timestamp = []
        
        '''Algorithm thresholds (Configurable)'''
        self.data_sample_rate = data_sample_rate
        self.economizer_type = economizer_type
        self.data_window = float(data_window)
        self.excess_oaf_threshold = float(excess_oaf_threshold)
        self.minimum_damper_signal = float(minimum_damper_signal)
        self.desired_oaf = float(desired_oaf)
        self.oaf_temperature_threshold = float(oaf_temperature_threshold)
            
    def econ_alg4(self, diagnostic_result,cooling_call, oatemp, ratemp, matemp, damper_signal, economizer_conditon, current_time):
        '''
        Check algorithm pre-quisites and assemble data set for analysis.
        '''
        if abs(oatemp - ratemp) < self.oaf_temperature_threshold:
            diagnostic_result.log('{name}: Conditions are not favorable for OAF calculation, data' 
                                  'corresponding to {timestamp} will not be used'.format(str(current_time),name=econ4))
            return diagnostic_result
        
        if economizer_conditon:
            diagnostic_result.log('{name}: The unit may be economizing, data corresponding to {timestamp}'
                                  'will not be used'.format(timestamp=str(current_time),name=econ4))
            return diagnostic_result

        self.damper_signal_values.append(damper_signal)
        self.oa_temp_values.append(oatemp)
        self.ra_temp_values.append(ratemp)
        self.ma_temp_values.append(matemp)
        self.timestamp.append(current_time)

        time_check =  datetime.timedelta(minutes=(self.data_window))

        if ((self.timestamp[-1]-self.timestamp[0]) >= time_check and
            len(self.timestamp) >= 30):
            diagnostic_result = self.excess_oa(diagnostic_result, current_time)
        return diagnostic_result
 
    def excess_oa(self, result, current_time):
        '''
        If the detected problems(s) are consistent then generate a fault message(s).
        '''
        oaf = [(m-r)/(o-r) for o,r,m in zip(self.oa_temp_values,self.ra_temp_values,self.ma_temp_values)]

        avg_oaf = sum(oaf)/len(oaf)*100
        avg_damper = sum(self.damper_signal_values)/len(self.damper_signal_values)
        desired_oaf = self.desired_oaf/100.0
        
        energy_calc = [(1.08*self.cfm*(ma - (oa*desired_oaf + (ra*(1.0-desired_oaf))))/(1000.0*self.eer)) for
                       ma, oa, ra in zip(self.ma_temp_values, self.oa_temp_values, self.ra_temp_values) 
                       if (ma - (oa*desired_oaf + (ra*(1.0-desired_oaf)))) > 0]
        
        color_code = 'GREEN'
        energy_impact = 0
        self.oa_temp_values = []
        self.ra_temp_values = []
        self.ma_temp_values = []
        self.damper_signal_values = []
        Application.pre_msg_time = []
        Application.pre_requiste_messages = []
        
        if avg_oaf < 0 or avg_oaf > 125.0:
            diagnostic_message = '{name}: Inconclusive result, the OAF calculation led to an unexpected value'.format(name=econ4)
            color_code = 'GREY'
            result.log(diagnostic_message)
            dx_table = {
                    'datetime': str(current_time), 
                    'diagnostic_name': econ4, 
                    'diagnostic_message': diagnostic_message, 
                    'energy_impact': 0.0,
                    'color_code': color_code
                    }
            result.insert_table_row('Economizer_dx', dx_table)
            return result

        if avg_damper > self.minimum_damper_signal:
            diagnostic_message = ('{name}: The damper should be at the minimum position '
                                      'for ventilation but is significantly higher than this value'.format(name=econ4))
            color_code = 'RED'
            
            if energy_calc:
                dx_time = (len(energy_calc) - 1)*self.data_sample_rate if len(energy_calc) > 1 else 1.0
                energy_impact = (sum(energy_calc)*60.0)/(len(energy_calc)*dx_time)
                
            dx_table = {
                    'datetime': str(current_time), 
                    'diagnostic_name': econ4, 
                    'diagnostic_message': diagnostic_message, 
                    'energy_impact': energy_impact,
                    'color_code': color_code
                    }
            result.insert_table_row('Economizer_dx', dx_table)
            return result

        if avg_oaf - self.desired_oaf > self.excess_oaf_threshold:
            diagnostic_message = ('{name}: Excess outdoor-air is being provided, this could increase '
                                      'heating and cooling energy consumption'.format(name=econ4))
            color_code = 'RED'
            
            if energy_calc:
                dx_time = (len(energy_calc) - 1)*self.data_sample_rate if len(energy_calc) > 1 else 1.0
                energy_impact = (sum(energy_calc)*60.0)/(len(energy_calc)*dx_time)
                
            dx_table = {
                    'datetime': str(current_time), 
                    'diagnostic_name': econ4, 
                    'diagnostic_message': diagnostic_message, 
                    'energy_impact': energy_impact,
                    'color_code': color_code
                    }
        else:
            diagnostic_message = ('{name}: The calculated outdoor-air fraction is within configured '
                                  'limits'.format(name=econ4))
            color_code = 'GREEN'
            dx_table = {
                    'datetime': str(current_time), 
                    'diagnostic_name': econ4, 
                    'diagnostic_message': diagnostic_message, 
                    'energy_impact': 0.0,
                    'color_code': color_code
                    }

        result.insert_table_row('Economizer_dx', dx_table)
        result.log(diagnostic_message, logging.INFO)

        self.timestamp = []
        return result
    
    
class insufficient_oa_intake(object):
    '''
    Air-side HVAC diagnostic to check if an AHU/RTU bringing in insufficient outdoor air.
    '''
    def __init__(self,device_type,economizer_type,data_window,
                ventilation_oaf_threshold,minimum_damper_signal,
                insufficient_damper_threshold,desired_oaf):

            self.oa_temp_values = []
            self.ra_temp_values = []
            self.ma_temp_values = []
            self.damper_signal_values = []
            self.cool_call_values = []
            self.timestamp = []
    
            '''Algorithm thresholds (Configurable)'''
            self.data_window = float(data_window)
            self.ventilation_oaf_threshold = float(ventilation_oaf_threshold)
            self.insufficient_damper_threshold = float(insufficient_damper_threshold)
            self.minimum_damper_signal = float(minimum_damper_signal)
            self.desired_oaf = float(desired_oaf)

    def econ_alg5(self, diagnostic_result,cooling_call, oatemp, ratemp, matemp, damper_signal, economizer_conditon, current_time): 
        '''
        Check algorithm pre-quisites and assemble data set for analysis.
        '''
        color_code = 'GREEN'
        if economizer_conditon:
            diagnostic_message = ('{name}: The unit may be economizing, data corresponding to {timestamp}'
                                  'will not be'.format(timestamp=str(current_time),name=econ5))
            return diagnostic_result

        self.oa_temp_values.append(oatemp)
        self.ra_temp_values.append(ratemp)
        self.ma_temp_values.append(matemp)
        self.timestamp.append(current_time)
        self.damper_signal_values.append(damper_signal)
        
        time_check =  datetime.timedelta(minutes=(self.data_window))
 
        if ((self.timestamp[-1]-self.timestamp[0]) >= time_check and
            len(self.timestamp) >= 30):
            diagnostic_result = self.insufficient_oa(diagnostic_result, current_time)
        return diagnostic_result
 
    def insufficient_oa(self, result, current_time):
        '''
        If the detected problems(s) are consistent then generate a fault message(s).
        '''
        oaf=[]
        oaf = [(m-r)/(o-r) for o,r,m in zip(self.oa_temp_values,self.ra_temp_values,self.ma_temp_values)]
        avg_oaf = sum(oaf)/len(oaf)*100.0
        avg_damper_signal = sum(self.damper_signal_values)/len(self.damper_signal_values)
        
        self.oa_temp_values = []
        self.ra_temp_values = []
        self.ma_temp_values = []
        Application.pre_msg_time = []
        Application.pre_requiste_messages = []
        self.timestamp = []

        if avg_oaf < 0 or avg_oaf > 125.0:
            diagnostic_message = '{name}: Inconclusive result, the OAF calculation led to an unexpected value'.format(name=econ4)
            color_code = 'GREY'
            result.log(diagnostic_message)
            dx_table = {
                    'datetime': str(current_time), 
                    'diagnostic_name': econ4, 
                    'diagnostic_message': diagnostic_message, 
                    'energy_impact': 0.0,
                    'color_code': color_code
                    }
            result.insert_table_row('Economizer_dx', dx_table)
            return result

        diagnostic_message = []
        if (self.minimum_damper_signal - avg_damper_signal) > self.insufficient_damper_threshold:
            diagnostic_message = ('{name}: Outdoor-air damper is significantly below the minimum '
                                      'configured damper position'.format(name=econ5))
            
            color_code = 'RED'
            dx_table = {
                    'datetime': str(current_time), 
                    'diagnostic_name': econ5, 
                    'diagnostic_message': diagnostic_message, 
                    'energy_impact': 0.0,
                    'color_code': color_code
                    }
            result.insert_table_row('Economizer_dx', dx_table)
            return result

        if (self.desired_oaf - avg_oaf) <= self.ventilation_oaf_threshold:
            diagnostic_message = ('{name}: Insufficient outdoor-air is being provided for ventilation'.format(name=econ5))
            color_code = 'RED'
            dx_table = {
                    'datetime': str(current_time), 
                    'diagnostic_name': econ5, 
                    'diagnostic_message': diagnostic_message, 
                    'energy_impact': 0.0,
                    'color_code': color_code
                    }
        else:
            diagnostic_message = ('{name}: The calculated outdoor-air fraction was within acceptable limits'.format(name=econ5))
            color_code = 'GREEN'
            dx_table = {
                    'datetime': str(current_time), 
                    'diagnostic_name': econ5, 
                    'diagnostic_message': diagnostic_message, 
                    'energy_impact': 0.0,
                    'color_code': color_code
                    }

        result.insert_table_row('Economizer_dx', dx_table)
        result.log(diagnostic_message, logging.INFO)
        return result