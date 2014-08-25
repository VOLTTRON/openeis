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
# from sys import exc_info
# from os import path
import datetime, logging, re
from openeis.applications import (DrivenApplicationBaseClass,
                                  OutputDescriptor, 
                                  ConfigDescriptor,
                                  InputDescriptor,
                                  Results)

duct_stc_dx = 'Duct Static Pressured Diagnostics'
duct_static1 = 'Low Duct Static Pressure Dx'
duct_static2 = 'High Duct Static Pressure Dx'
duct_static3 = 'No Static Pressure Reset Dx'
sa_temp_dx = 'Supply-air temperature Diagnostics'
sa_temp_dx1 = 'Low Supply-air Temperature Dx'
sa_temp_dx2 = 'High Supply-air Temperature Dx'
sa_temp_dx3 = 'Supply-air Temperature Reset Dx'
sched_dx = 'Operational Schedule Dx'

class Application(DrivenApplicationBaseClass):
    '''
    Air-side HVAC Auto-Retuning to identify problems related to static pressure contrl of AHU/RTU
    '''
    fan_status_name = 'fan_status'
    oa_temp_name = 'oa_temp'
    ma_temp_name = 'ma_temp'
    zone_reheat_name = 'zone_reheat'
    zone_damper_name = 'zone_damper'
    cool_call_name = 'cool_call'
    fan_speedcmd_name = 'fan_speedcmd'
    duct_stp_name = 'duct_stp'
    sa_temp_name = 'sa_temp'
    sat_stpt_name = 'sat_stpt'
    duct_stp_stpt_name = 'duct_stp_stpt'
    time_format = '%m/%d/%Y %H:%M'
    def __init__(self,*args,
    
                override_state=None,fan_speedcmd_priority='',fan_speedcmd_name=None, 
                oa_temp_name=None,fan_status_name=None,duct_stp_stpt_priority='',duct_stp_stpt_name=None,
                zone_damper_name=None,duct_stp_name=None,
                
                data_window=None,number_of_zones=None,auto_correctflag=None, duct_stc_retuning=None,
                
                max_duct_stp_stpt=None,
                high_supply_fan_threshold=None,zone_high_damper_threhold=None,
                zone_low_damper_threhold=None,
                
                min_duct_stp_stpt=None,hdzone_damper_threshold=None,
                low_supply_fan_threshold=None,setpoint_allowable_deviation=None,
                
                stpr_diff_threshold=None,oat_threshold=None,
                zonedpr_max_threshold=None,zonedpr_min_threshold=None,no_zones_dpr_max=None,
                no_zones_dpr_min=None, dsgn_stp_high=None, dsgn_stp_low=None,
              
                sa_temp_name=None, ma_temp_name=None,cool_call_name=None,
                sat_stpt_name=None,zone_reheat_name=None,
                ahu_ccoil_priority='',
                
                percent_reheat_threshold=None,rht_on_threshold=None,
                satemp_diff_threshold=None, mat_low_threshold=None,
                ccoil_on_threshold=None,sat_high_threshold=None,oatemp_diff_threshold=None,
    
                high_damper_threshold=None,percent_damper_threshold=None,
                minimum_sat_stpt=None,sat_reduction=None,

                sat_stpt_priority='',
                reheat_valve_threshold=None,
                maximum_sat_stpt=None,sat_increase=None,

                unocc_time_threshold=None,unocc_stp_threshold=None,
                monday_sch=None,tuesday_sch=None,wednesday_sch=None,thursday_sch=None,
                friday_sch=None, saturday_sch=None, sunday_sch=None,
                **kwargs):
        super().__init__(*args, **kwargs)
        Application.pre_requiste_messages = []
        Application.pre_msg_time = []

        '''Pre-requisite messages'''
        self.pre_msg0 = 'Fan Status is not available, could not verify system is ON.'
        self.pre_msg1 = 'Supply fan is off, current data will not be used for diagnostics.'
    
        self.pre_msg2 = 'Missing required data for diagnostic:  Outside-air temperature.'
        self.pre_msg3 = 'Missing required data for diagnostic:  Duct static pressure'
        self.pre_msg4 = 'Missing required data for diagnostic:  Zone damper command.'
         
        self.pre_msg5 = 'Missing required data for diagnostic: Supply-air temperature.'
        self.pre_msg6 = 'Missing required data for diagnostic: terminal box reheat-valve-positions (all zones).'
        self.pre_msg7 = 'Missing required data for diagnostic: Outside-air temperature.'
        self.pre_msg8 = 'Missing required data for diagnostic: Mixed Air Temperature.'
        self.pre_msg9 = 'Missing required data for diagnostic: AHU cooling-coil-position.'
 
        if duct_stp_stpt_name == None:
            duct_stp_stpt_name = ''
 
        '''Point names (Configurable)'''
        self.fan_status_name = Application.fan_status_name
        self.oa_temp_name = Application.oa_temp_name
        self.ma_temp_name = Application.ma_temp_name
        self.zone_reheat_name = Application.zone_reheat_name
        self.zone_damper_name = Application.zone_damper_name
        self.cool_call_name = Application.cool_call_name
        self.fan_speedcmd_name = Application.fan_speedcmd_name
        self.duct_stp_name = Application.duct_stp_name
        self.sa_temp_name = Application.sa_temp_name
        
        self.sat_stpt_name = Application.sat_stpt_name
        self.duct_stp_stpt_name = Application.duct_stp_stpt_name
        duct_stp_stpt_cname = self.duct_stp_stpt_name_name
        
        self.ahu_ccoil_priority = ahu_ccoil_priority.lower()
        self.sat_stpt_priority = sat_stpt_priority.lower()
        self.fan_speedcmd_priority = fan_speedcmd_priority.lower()
        self.duct_stp_stpt_priority = duct_stp_stpt_priority.lower()
        
        '''Application thresholds (Configurable)'''
        self.data_window = float(data_window)
         
        self.low_supply_fan_threshold = float(low_supply_fan_threshold)
        self.high_supply_fan_threshold = float(high_supply_fan_threshold)
        
        self.static_dx = duct_static_dx(max_duct_stp_stpt,duct_stc_retuning, data_window,
                                   number_of_zones, duct_high_damper_threhold, _low_damper_threhold,
                                   setpoint_allowable_deviation, auto_correctflag,
                                   hdzone_damper_threshold, min_duct_stp_stpt, duct_stp_stpt_cname,stpr_diff_threshold,
                                   oat_threshold, zonedpr_max_threshold, zonedpr_min_threshold, no_zones_dpr_max, 
                                   no_zones_dpr_min,dsgn_stp_high, dsgn_stp_low)
         
        self.sat_dx = supply_air_temp_dx(data_window, number_of_zones, auto_correctflag, rht_on_threshold,
                sat_high_damper_threhold, percent_damper_threshold, percent_reheat_threshold,
                setpoint_allowable_deviation, minimum_sat_stpt, sat_retuning, reheat_valve_threshold,
                maximum_sat_stpt,satemp_diff_threshold, mat_low_threshold,ccoil_on_threshold, 
                sat_high_threshold,oatemp_diff_threshold)
        
        self.sched_occ_dx = schedule_dx(unocc_time_threshold, unocc_stp_threshold,
                                         monday_sch,tuesday_sch,wednesday_sch,thursday_sch,
                                         friday_sch, saturday_sch, sunday_sch, data_window)
    @classmethod
    def get_config_parameters(cls):
        '''
        Generate required configuration
        parameters with description for user
        '''
        return {
                'data_window': ConfigDescriptor(float, 'Data Window'),
                'auto_correctflag': ConfigDescriptor(float, 'Simulate auto-correction (True)'),
                'number_of_zones': ConfigDescriptor(float,'Number of zones served by AHU'),
                
                'max_duct_stp_stpt': ConfigDescriptor(float, 'Maximum static set point allowed with auto-correction'),
                'high_supply_fan_threshold': ConfigDescriptor(float,'high supply fan command (100)'),
                'duct_stc_retuning': ConfigDescriptor(float,'Correction step applied to static pressure set point(0.05)'),
                'zone_high_damper_threhold': ConfigDescriptor(float,'High zone damper threshold for static pressure Dx (90)'),
                'zone_low_damper_threhold': ConfigDescriptor(float,'Low zone damper threshold (10)'),
            
                'min_duct_stp_stpt': ConfigDescriptor(float, 'Minimum static set point allowed with auto-correction'),
                'hdzone_damper_threshold': ConfigDescriptor(float, 'Threshold for zone damper (30)'),
                'low_supply_fan_threshold': ConfigDescriptor(float,'Low supply fan command (20)'),
                'setpoint_allowable_deviation': ConfigDescriptor(float,'% allowable deviation from set points (10)'),
                
                'stpr_diff_threshold': ConfigDescriptor(float, 'Duct-static pressure threshold (0.1)'),
                'oat_threshold': ConfigDescriptor(float, 'Outdoor-air temperature threshold (1.0)'),
                'zonedpr_max_threshold': ConfigDescriptor(float, 'Zone damper threshold threshold (80)'),
                'zonedpr_min_threshold': ConfigDescriptor(float, 'Zone damper threshold threshold (20)'),
                'no_zones_dpr_max': ConfigDescriptor(float, 'Number of zones with dampers at maximum'),
                'no_zones_dpr_min': ConfigDescriptor(float, 'Number of zones with dampers at minimum'),
                'dsgn_stp_high': ConfigDescriptor(float, 'Static pressure high limit (3.0'),
                'dsgn_stp_low': ConfigDescriptor(float, 'Static pressure low limit (0.25)'),
    
                'reheat_valve_threshold': ConfigDescriptor(float,'Zone reheat valve threshold for SAT Dx (50)'),
                'percent_reheat_threshold': ConfigDescriptor(float,'SAT Dx threshold for % of zone with reheat ON (25)'),
                'maximum_sat_stpt': ConfigDescriptor(float, 'Maximum SAT set point allowed with auto-correction'),
                'rht_on_threshold': ConfigDescriptor(float,'Value above which zone reheat is considered ON (10)'),
                'sat_retuning': ConfigDescriptor(float,'Correction step applied to SAT set point (0.5)'),
    
                'sat_high_damper_threhold': ConfigDescriptor(float,'High zone damper threshold for SAT Dx (80)'),
                'percent_damper_threshold': ConfigDescriptor(float,'SAT Dx threshold for % of zone dampers above high damper threshold (50)'),
                'minimum_sat_stpt': ConfigDescriptor(float, 'Minimum SAT set point allowed with auto-correction'),
    
                'mat_low_threshold': ConfigDescriptor(float, 'Low MAT threshold used for detecting SAT Reset (54)'),
                'ccoil_on_threshold': ConfigDescriptor(float, 'AHU cooling coil position at which cooling is considered ON (5)'),
                'sat_high_threshold': ConfigDescriptor(float, 'High SAT threshold used to for SAT Reset Dx (70)'),
                'oatemp_diff_threshold': ConfigDescriptor(float, 'OAT variation threshold used to for SAT Reset Dx (5.0)'),
                'satemp_diff_threshold': ConfigDescriptor(float,'Threshold for supply-air temperature difference for SAT Reset Dx (3)'),
    
                'unocc_time_threshold': ConfigDescriptor(float,'Time threshold used for AHU schedule Dx (80)'),
                'unocc_stp_threshold': ConfigDescriptor(float, 'AHU off static pressure deadband (0.2)'),
                'monday_sch': ConfigDescriptor(float, 'Monday AHU occupied schedule (6:30;18:30)'),
                'tuesday_sch': ConfigDescriptor(float, 'Monday AHU occupied schedule (6:30;18:30)'),
                'wednesday_sch': ConfigDescriptor(float,  'Monday AHU occupied schedule (6:30;18:30)'),
                'thursday_sch': ConfigDescriptor(float,  'Monday AHU occupied schedule (6:30;18:30)'),
                'friday_sch': ConfigDescriptor(float,  'Monday AHU occupied schedule (6:30;18:30)'),
                'saturday_sch': ConfigDescriptor(float,  'Monday AHU occupied schedule (6:30;18:30)'),
                'sunday_sch': ConfigDescriptor(float,  'Monday AHU occupied schedule (6:30;18:30)')
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
            cls.zone_reheat_name: InputDescriptor('TeminalBoxReheat','All terminal box reheat',count_min=1),
            cls.zone_damper_name: InputDescriptor('TerminalBoxDamper','All terminal box damper commands', count_min=1),
            cls.cool_call_name: InputDescriptor('CoolingCall', 'AHU cooling coil command or RTU coolcall or compressor command', count_min=1),
            cls.fan_speedcmd_name:  InputDescriptor('SupplyFanSpeed','AHU supply fan speed', count_min=1),
            cls.duct_stp_name: InputDescriptor('DuctStaticSp', 'AHU duct static pressure', count_min=1),
            cls.sa_temp_name:  InputDescriptor('SupplyAirTemp','AHU supply-air temperature', count_min=1),
            cls.cool_call_name:  InputDescriptor('CoolCall', 'AHU cooling coil position', count_min=1),
            cls.sat_stpt_name: InputDescriptor('SupplyAirTempSp','Supply-air temperature set point', count_min=0),
            cls.duct_stp_stpt_name: InputDescriptor('DuctStaticPrSp','Duct static pressure set point', count_min=0)
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
        '''
        Called when application is staged.
        Output will have the date-time and  error-message.
        '''
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
            'Airside_dx': {
                'datetime': OutputDescriptor('datetime', datetime_topic),
                'diagnostic_name': OutputDescriptor('string', diagnostic_name),
                'diagnostic_message': OutputDescriptor('string', message_topic),
                'energy_impact': OutputDescriptor('float', energy_impact),
                'color_code': OutputDescriptor('string', color_code)
                }
            }
        result.update(output_needs)
        return result

    def run(self,current_time, points):
        '''
        Check application pre-quisites and assemble analysis data set.
        '''
        device_dict = {}
        diagnostic_result = Results()

        if None in points.values():
            diagnostic_result.log(''.join(['Missing data for timestamp: ',str(current_time),
                                   '  This row will be dropped from analysis.']))
            return diagnostic_result
            
        for key, value in points.iteritems():
            device_dict[key.lower()] = value

        Application.pre_msg_time.append(current_time)
        message_check =  datetime.timedelta(minutes=(self.data_window))

        if (Application.pre_msg_time[-1]-Application.pre_msg_time[0]) >= message_check:
            msg_lst = [self.pre_msg0, self.pre_msg1, self.pre_msg2, self.pre_msg3, self.pre_msg4, 
                       self.pre_msg5,self.pre_msg6, self.pre_msg7, self.pre_msg8, self.pre_msg9]
            for item in msg_lst:
                if Application.pre_requiste_messages.count(item) > (0.25)*len(Application.pre_msg_time):
                    diagnostic_result.log(item, logging.INFO)
            Application.pre_requiste_messages = []
            Application.pre_msg_time = []

        fan_stat_data = []
        fan_stat_check = False
        for key, value in device_dict.items():
            if key.startswith(self.fan_status_name): 
                fan_stat_check = True
                fan_stat_data.append(value)
                if int(value) == 0:
                    Application.pre_requiste_messages.append(self.pre_msg1)
                    return diagnostic_result
        if not fan_stat_check:
            Application.pre_requiste_messages.append(self.pre_msg0)
            return diagnostic_result
        
        low_dx_condition = False
        high_dx_condition = False
        static_override_check = False
        sat_override_check = False
        
        for key, value in device_dict.iteritems():
            if self.fan_speedcmd_name in key:
                if value > self.high_supply_fan_threshold:
                    low_dx_condition = True
                elif value < self.low_supply_fan_threshold:
                    high_dx_condition = True
            if self.fan_speedcmd_priority in key:
                if value == self.override_state:
                    static_override_check = True
            if self.duct_stp_stpt_priority in key:
                if value == self.override_state:
                    static_override_check = True
            if self.ahu_ccoil_priority in key:
                if value == self.override_state:
                    sat_override_check  = True
            if self.sat_stpt_priority in key:
                if value == self.override_state:
                    sat_override_check  = True

        oatemp_data = []
        stc_pr_data = []
        stc_pr_sp_data = []
        zone_damper_data = []
        satemp_data = []
        rht_data = []
        matemp_data = []
        cooling_data = []
        sat_stpt_data = []

        for key, value in device_dict.iteritems():

            if key.startswith(self.duct_stp_stpt_name):
                stc_pr_sp_data.append(value)

            elif key.startswith(self.duct_stp_name):
                stc_pr_data.append(value)

            elif key.startswith(self.zone_damper_name):
                zone_damper_data.append(value)
            
            elif key.startswith(self.oa_temp_name):
                oatemp_data.append(value)
                
            elif key.startswith(self.sat_stpt_name):
                sat_stpt_data.append(value)

            elif key.startswith(self.sa_temp_name):
                satemp_data.append(value)

            elif key.startswith(self.zone_reheat_name):
                rht_data.append(value)
                
            elif key.startswith(self.oa_temp_name):
                oatemp_data.append(value)
                
            elif key.startswith(self.ma_temp_name):
                matemp_data.append(value)
                
            elif key.startswith(self.cool_call_name):
                cooling_data.append(value)

        if not oatemp_data:
            Application.pre_requiste_messages.append(self.pre_msg2)
        if not stc_pr_data:
            Application.pre_requiste_messages.append(self.pre_msg3)
        if not zone_damper_data:
            Application.pre_requiste_messages.append(self.pre_msg4)
        if not (oatemp_data and stc_pr_data and zone_damper_data):
            return diagnostic_result

        if not satemp_data:
            Application.pre_requiste_messages.append(self.pre_msg5)
        if not rht_data:
            Application.pre_requiste_messages.append(self.pre_msg6)
        if not matemp_data:
            Application.pre_requiste_messages.append(self.pre_msg8)
        if not cooling_data:
            Application.pre_requiste_messages.append(self.pre_msg9)
        if not satemp_data or not rht_data or not cooling_data or not matemp_data:
            return diagnostic_result

        if not low_dx_condition and not high_dx_condition:
            diagnostic_result = self.static_dx.duct_static(current_time, stc_pr_sp_data, stc_pr_data, zone_damper_data, oatemp_data, static_override_check, diagnostic_result)
        elif low_dx_condition:
            diagnostic_result.log('{name}:The supply fan is running at nearly 100% of full speed, data corresponding to {timstamp} '
                                      'will not be used for diagnostic'.format(name = duct_static1, timestamp=str(current_time)), logging.INFO)
        elif high_dx_condition:
            diagnostic_result.log('{name}: The supply fan is running at the minimum speed, data corresponding to {timstamp} '
                                      'will not be used for diagnostic'.format(name =duct_static2, timestamp=str(current_time)), logging.INFO)
 
        diagnostic_result = self.sat_dx.sat_diagnostics(current_time, satemp_data, sat_stpt_data, rht_data, zone_damper_data,
                                                       oatemp_data, matemp_data, cooling_data, diagnostic_result, sat_override_check)
        diagnostic_result = self.sched_occ_dx.sched_dx_alg(current_time, stc_pr_data, fan_stat_data, diagnostic_result)
        return diagnostic_result


class duct_static_dx(object):
    '''
    Air-side HVAC Auto-Retuning diagnostic to check if the duct static pressure is too low.
    '''
    def __init__(self, max_duct_stp_stpt,duct_stc_retuning, data_window, number_of_zones,
                 zone_high_damper_threhold, zone_low_damper_threhold, setpoint_allowable_deviation, 
                 auto_correctflag, hdzone_damper_threshold, min_duct_stp_stpt, duct_stp_stpt_cname,
                 stpr_diff_threshold, oat_threshold, zonedpr_max_threshold, zonedpr_min_threshold, 
                 no_zones_dpr_max, no_zones_dpr_min, dsgn_stp_high, dsgn_stp_low):
        self.zone_damper_values = []
        self.duct_stp_stpt_values = []
        self.duct_stp_values = []
        self.oa_temp_values = []
        self.timestamp = []

        self.data_window = float(data_window)
        self.number_of_zones = float(number_of_zones)
        self.setpoint_allowable_deviation = float(setpoint_allowable_deviation)
        
        self.duct_stp_stpt_cname = duct_stp_stpt_cname
        self.max_duct_stp_stpt = float(max_duct_stp_stpt)
        self.duct_stc_retuning = float(duct_stc_retuning)
        
        self.zone_high_damper_threhold = float(zone_high_damper_threhold)
        self.zone_low_damper_threhold = float(zone_low_damper_threhold)
        self.setpoint_allowable_deviation = float(setpoint_allowable_deviation)
        self.auto_correctflag = bool(auto_correctflag)
        
        self.min_duct_stp_stpt = float(min_duct_stp_stpt)
        self.hdzone_damper_threshold = float(hdzone_damper_threshold)
        
        self.stpr_diff_threshold = float(stpr_diff_threshold)
        self.oat_threshold = float(oat_threshold)
        self.zonedpr_max_threshold = float(zonedpr_max_threshold)
        self.zonedpr_min_threshold = float(zonedpr_min_threshold)
        self.no_zones_dpr_max = float(no_zones_dpr_max)
        self.no_zones_dpr_min = float(no_zones_dpr_min)
        self.dsgn_stp_high = float(dsgn_stp_high)
        self.dsgn_stp_low = float(dsgn_stp_low)
        
    def duct_static(self, current_time, stc_pr_sp_data, stc_pr_data, zone_dmpr_data, oatemp_data, 
                    static_override_check, diagnostic_result):
        '''
        Check duct static pressure dx pre-requisites and assemble analysis data set
        '''
        self.duct_stp_values.append(sum(stc_pr_data)/len(stc_pr_data))
        self.zone_damper_values.append(sum(zone_dmpr_data)/len(zone_dmpr_data))
        self.oa_temp_values.append(sum(oatemp_data)/len(oatemp_data))
        self.timestamp.append(current_time)

        if stc_pr_sp_data:
            self.duct_stp_stpt_values.append(sum(stc_pr_sp_data)/len(stc_pr_sp_data))

        time_check =  datetime.timedelta(minutes=self.data_window)

        if ((self.timestamp[-1]-self.timestamp[0]) >= time_check and
            len(self.timestamp) > 20):

            avg_duct_stpr_stpt = None
            if self.duct_stp_stpt_values:
                avg_duct_stpr_stpt = sum(self.duct_stp_stpt_values)/len(self.duct_stp_stpt_values)
                if avg_duct_stpr_stpt > 0 and avg_duct_stpr_stpt < 5:
                    set_point_tracking = [abs(x-y) for x,y in zip(self.duct_stp_values, self.duct_stp_stpt_values)]
                    set_point_tracking = sum(set_point_tracking)/(len(set_point_tracking)*avg_duct_stpr_stpt)*100
                    if set_point_tracking > self.setpoint_allowable_deviation:
                        diagnostic_message = ('{name}: The duct static pressure is deviating from its '
                                              'set point significantly.'.format(name = duct_stc_dx))
                    color_code = 'RED'
                    energy_impact = None
                    dx_table = {
                                'datetime': str(self.timestamp[-1]), 
                                'diagnostic_name': duct_stc_dx, 'diagnostic_message': diagnostic_message, 
                                'energy_impact': energy_impact,
                                'color_code': color_code
                                }
                    diagnostic_result.insert_table_row('Economizer_dx', dx_table)
                    diagnostic_result.log(diagnostic_message, logging.INFO)
            diagnostic_result = self.low_ductstatic_sp(diagnostic_result, static_override_check)
            diagnostic_result = self.high_ductstatic_sp(diagnostic_result, static_override_check)
            diagnostic_result = self.no_static_pr_reset(diagnostic_result)

        return diagnostic_result
        
    def low_ductstatic_sp(self, result, static_override_check):
        '''
        Diagnostic to identify and correct low duct static pressure
        setpoint
        '''
        zone_damper_temp = self.zone_damper_values                       
        zone_damper_temp.sort(reverse=False)
        zone_damper_lowtemp = zone_damper_temp[0:len(zone_damper_temp)/2]
        zone_damper_lowavg = sum(zone_damper_lowtemp)/len(zone_damper_lowtemp)
        zone_damper_hightemp = zone_damper_temp[len(zone_damper_temp)/2 +1:-1]
        zone_damper_highavg = sum(zone_damper_hightemp)/len(zone_damper_hightemp)
        energy_impact = None
        
        avg_duct_stpr_stpt = None
        if self.duct_stp_stpt_values:
            avg_duct_stpr_stpt = sum(self.duct_stp_stpt_values)/len(self.duct_stp_stpt_values)

        if (zone_damper_highavg > self.zone_high_damper_threhold 
            and zone_damper_lowavg > self.zone_low_damper_threhold):
            color_code = 'RED'
            if avg_duct_stpr_stpt != None and not static_override_check: 
            
                if self.auto_correctflag:
                    duct_stpr_stpt = avg_duct_stpr_stpt + self.duct_stc_retuning
                    if duct_stpr_stpt <= self.max_duct_stp_stpt:
                        result.command(self.duct_stp_stpt_cname, duct_stpr_stpt)
                        diagnostic_message = ('{name}: The duct static pressure was detected to be too low. The duct static pressure' 
                                             'has been increased to: '.format(name=duct_static2))
                        diagnostic_message += str(duct_stpr_stpt) + ' in. w.c.'
                    else:
                        result.command(self.duct_stp_stpt_cname, self.max_duct_stp_stpt)
                        diagnostic_message = ('{name}: Duct static pressure set point is at maximum value '
                                             'specified in configuration file'.format(name=duct_static1))
                                             
                else:                                
                    diagnostic_message =( '{name}: Duct static pressure set point was detected to be too low '
                                      'but auto-correction is not enabled'.format(name=duct_static1))  
        
            elif not static_override_check:
                diagnostic_message = '{name}: The duct static pressure was detected to be too low'.format(name=duct_static1)
            else:
                diagnostic_message = ('{name}: The duct static pressure was detected to be too low but an operator override '
                                      'was detected. Auto-correction can not be performed when the static pressure set point '
                                      'or fan speed command is in overrride'.format(name=duct_static1)) 
        else:
            diagnostic_message = '{name}: No re-tuning opportunity was detected during the low duct static pressure diagnostic'.format(name=duct_static1)
            color_code = 'GREEN'
            
        dx_table = {
                    'datetime': str(self.timestamp[-1]), 
                    'diagnostic_name': duct_static1, 'diagnostic_message': diagnostic_message, 
                    'energy_impact': energy_impact,
                    'color_code': color_code
                    }

        result.insert_table_row('Economizer_dx', dx_table)
        result.log(diagnostic_message,logging.INFO) 
        return result

    def high_ductstatic_sp(self, result, static_override_check):
        '''
        Diagnostic to identify and correct high duct static pressure
        setpoint
        '''
        zone_damper_temp = self.zone_damper_values                       
        zone_damper_temp.sort(reverse=True)
        zone_damper_temp = zone_damper_temp[0:len(zone_damper_temp)/2]
        avg_zone_damper = sum(zone_damper_temp)/len(zone_damper_temp)
        energy_impact = None
        avg_duct_stpr_stpt = None

        if self.duct_stp_stpt_values:
            avg_duct_stpr_stpt = sum(self.duct_stp_stpt_values)/len(self.duct_stp_stpt_values)

        if avg_zone_damper <= self.hdzone_damper_threshold:
            color_code = 'RED'
            if avg_duct_stpr_stpt != None and not static_override_check: 
            
                if self.auto_correctflag:
                    duct_stpr_stpt = avg_duct_stpr_stpt - self.duct_stc_retuning
                    if duct_stpr_stpt >= self.min_duct_stp_stpt:
                        result.command(self.duct_stp_stpt_cname, duct_stpr_stpt)
                        diagnostic_message = ('{name}: The duct static pressure was detected to be too high. ' 
                        'The duct static pressure has been reduced to: '.format(name=duct_static2))
                        diagnostic_message += str(duct_stpr_stpt) + ' in. w.c.'
                    else:
                        result.command(self.duct_stp_stpt_cname, self.min_duct_stp_stpt)
                        diagnostic_message = ('{name}: Duct static pressure set point is at minimum value '
                                             'specified in configuration file'.format(name=duct_static2))
                else:       
                    diagnostic_message =( '{name}: Duct static pressure set point was detected to be too high '
                                      'but auto-correction is not enabled'.format(name=duct_static2))  
        
            elif not static_override_check:
                diagnostic_message = '{name}: The duct static pressure was detected to be too high'.format(name=duct_static2)
            else:
                diagnostic_message = ('{name}: The duct static pressure was detected to be too high but an operator override '
                                      'was detected. Auto-correction can not be performed when the static pressure set point '
                                      'or fan speed command is in overrride'.format(name=duct_static2)) 
        else:
            diagnostic_message = ('{name}: No re-tuning opportunity was detected during the '
                                  'low duct static pressure diagnostic'.format(name=duct_static2))
            color_code = 'GREEN'

        dx_table = {
                    'datetime': str(self.timestamp[-1]), 
                    'diagnostic_name': duct_static1, 'diagnostic_message': diagnostic_message, 
                    'energy_impact': energy_impact,
                    'color_code': color_code
                    }
        
        result.insert_table_row('Economizer_dx', dx_table)
        result.log(diagnostic_message, logging.INFO)
        return result
        
    def no_static_pr_reset(self, result):
        '''
        Auto-retuning diagnostic to detect whether a static
        pressure reset is implemented
        '''
        no_zones_avg_dpr_max = [i for i in self.zone_damper_values if i >= self.zonedpr_max_threshold]
        no_zones_avg_dpr_min = [i for i in self.zone_damper_values if i <= self.zonedpr_min_threshold]
        per_no_zones_avg_dpr_max = len(no_zones_avg_dpr_max)/len(self.zone_damper_values)
        per_no_zones_avg_dpr_min = len(no_zones_avg_dpr_min)/len(self.zone_damper_values)
        
        stp_diff = max(self.duct_stp_values) - min(self.duct_stp_values)
        avg_stp = sum(self.duct_stp_values)/len(self.duct_stp_values)
        oat_diff = max(self.oa_temp_values) - min(self.oa_temp_values)
        energy_impact = None

        if stp_diff < self.stpr_diff_threshold:
            if oat_diff > self.oat_threshold:
                if ((avg_stp < self.dsgn_stp_high and  per_no_zones_avg_dpr_max > self.no_zones_dpr_max/100) or
                    (avg_stp > self.dsgn_stp_low and  per_no_zones_avg_dpr_min > self.no_zones_dpr_min/100)):                
                    diagnostic_message =('{name}: No duct static pressure reset detected. '
                                        'A duct static pressure set point reset can save '
                                        'significant amounts of energy'.format(name=duct_static3))
                    color_code = 'RED'
                else:
                    diagnostic_message = '{name}: Inconclusive diagnostic'.format(name=duct_static3)
                    color_code = 'GREY'
            else:                       
                diagnostic_message = ('{name}: Inconclusive diagnostic, very little variation in outdoor-'
                                     'air temperature conditions'.format(name=duct_static3))
                color_code = 'GREY'
        else:
            diagnostic_message = '{name}: No problem detected'.format(name=duct_static3)
            color_code = 'GREEN'
        
        dx_table = {
                    'datetime': str(self.timestamp[-1]), 
                    'diagnostic_name': duct_static3, 'diagnostic_message': diagnostic_message, 
                    'energy_impact': energy_impact,
                    'color_code': color_code
                    }
        
        result.insert_table_row('Economizer_dx', dx_table)
        result.log(diagnostic_message, logging.INFO)
        self.duct_stp_stpt_values = []
        self.duct_stp_values = []
        self.zone_damper_values = []
        self.timestamp = []
        return result
    
class supply_air_temp_dx(object):
    def __init__(self, data_window, number_of_zones, auto_correctflag, rht_on_threshold,
                high_damper_threshold, percent_damper_threshold, percent_reheat_threshold,
                setpoint_allowable_deviation, minimum_sat_stpt, sat_reduction, reheat_valve_threshold,
                maximum_sat_stpt,satemp_diff_threshold, mat_low_threshold,ccoil_on_threshold, 
                sat_high_threshold,oatemp_diff_threshold):
        sat_increase = sat_reduction   
        self.timestamp = []
        self.sat_stpt_values = []
        self.sa_temp_values = [] 
        self.ma_temp_values = []
        self.rht_values = []
        self.oa_temp_values = []
        self.clg_coil_values = []
        self.total_reheat = 0
        self.total_damper = 0
        self.pre_requiste_messages = []
        self.pre_msg_time = []
        self.timestamp = []
        self.reheat = []
        
        self.data_window = float(data_window)
        self.number_of_zones = float(number_of_zones)
        self.auto_correctflag = bool(auto_correctflag)
        self.reheat_valve_threshold = float(reheat_valve_threshold)
        self.percent_reheat_threshold = float(percent_reheat_threshold)
        self.setpoint_allowable_deviation = float(setpoint_allowable_deviation)
        self.maximum_sat = float(maximum_sat_stpt)
        self.sat_increase = float(sat_increase)
        self.rht_on_threshold = float(rht_on_threshold)
        
        self.high_damper_threshold = float(high_damper_threshold)
        self.percent_damper_threshold = float(percent_damper_threshold)
        self.minimum_sat_stpt = float(minimum_sat_stpt)
        self.sat_reduction = float(sat_reduction) 
        
        self.satemp_diff_threshold = float(satemp_diff_threshold)
        self.mat_low_threshold = float(mat_low_threshold)
        self.ccoil_on_threshold = float(ccoil_on_threshold)
        self.sat_high_threshold = float(sat_high_threshold)
        self.oatemp_diff_threshold = float(oatemp_diff_threshold)
        
        
             
    def sat_diagnostics(self, current_time, satemp_data, sat_stpt_data,rht_data, zone_damper_data,
                        oatemp_data, matemp_data, cooling_data, diagnostic_result, sat_override_check):
        '''
        Check supply-air temperature dx pre-requisites and assemble analysis data set
        '''
        self.sa_temp_values.append(sum(satemp_data)/len(satemp_data))
        self.ma_temp_values.append(sum(matemp_data)/len(matemp_data))
        self.rht_values.append(sum(rht_data)/len(rht_data))

        if sat_stpt_data:
            self.sat_stpt_values.append(sum(sat_stpt_data)/len(sat_stpt_data))

        self.clg_coil_values.append(sum(cooling_data)/len(cooling_data))
        self.oa_temp_values.append(sum(oatemp_data)/len(oatemp_data))

        for value in rht_data:
            if value > self.rht_on_threshold:
                self.total_reheat += 1
        for value in zone_damper_data:        
            if value > self.high_damper_threshold:
                self.total_damper += 1
     
        self.timestamp.append(current_time)       
        time_check =  datetime.timedelta(minutes=self.data_window)

        if ((self.timestamp[-1]-self.timestamp[0]) >= time_check and
            len(self.sat_stpt_values) > 20):
            avg_sat_stpt = None
            if self.sat_stpt_values:
                avg_sat_stpt = (sum(self.sat_stpt_values))/(len(self.sat_stpt_values))
                set_point_tracking = [abs(x-y) for x,y in zip(self.sat_stpt_values, self.sa_temp_values)]
                set_point_tracking = sum(set_point_tracking)/(len(set_point_tracking)*avg_sat_stpt)*100
                if set_point_tracking > self.setpoint_allowable_deviation:
                    diagnostic_message = ('{name}: Supply-air temperature is deviating significantly '
                                          'from the supply-air temperature set point'.format(name=sa_temp_dx))
                    color_code = 'RED'
                    energy_impact = None
                    dx_table = {
                                'datetime': str(self.timestamp[-1]), 
                                'diagnostic_name': sa_temp_dx, 'diagnostic_message': diagnostic_message, 
                                'energy_impact': energy_impact,
                                'color_code': color_code
                                }
                    diagnostic_result.insert_table_row('Economizer_dx', dx_table)
                    diagnostic_result.log(diagnostic_message, logging.INFO)
                diagnostic_result = self.low_sat_sp(diagnostic_result, avg_sat_stpt, sat_override_check)
                diagnostic_result = self.high_sat_sp(diagnostic_result, avg_sat_stpt, sat_override_check)
                diagnostic_result = self.no_sat_sp_reset(diagnostic_result)
        return diagnostic_result

    def low_sat_sp(self, result, avg_sat_stpt, sat_override_check):
        '''
        Diagnostic to identify and correct low supply-air temperature
        setpoint
        '''
        time_d = self.timestamp[-1]-self.timestamp[0]
        time_d = int(time_d.total_seconds()/60) + 1

        avg_zones_reheat = self.total_reheat/(time_d*self.number_of_zones)*100
        reheat_coil_average = (sum(self.rht_values))/(len(self.rht_values))
        energy_impact = None

        if (reheat_coil_average > self.reheat_valve_threshold and
            avg_zones_reheat > self.percent_reheat_threshold):
            color_code = 'RED'
            if avg_sat_stpt != None and not sat_override_check:
            
                if self.auto_correctflag:
                
                    sat_stpt = avg_sat_stpt + self.sat_increase
                    '''Create diagnostic message for fault condition with auto-correction'''
                    if sat_stpt <= self.maximum_sat:
                        result.command(self.sat_stpt_cname, sat_stpt)
                        diagnostic_message = ('{name}: The SAT has been detected to be too low. The SAT has been '
                                             'increased to: '.format(name=sa_temp_dx1))
                        diagnostic_message += str(sat_stpt) + ' deg.'
                    else:
                        '''Create diagnostic message for fault condition where the maximum SAT has been reached'''
                        result.command(self.sat_stpt_cname,self.maximum_sat)
                        diagnostic_message = ('{name}: The SAT was detected to be too low, Auto-correction has '
                                             'increased the SAT to the maximum configured SAT: '.format(name=sa_temp_dx1))
                        diagnostic_message += str(self.maximum_sat) + ' deg.'
                else:
                    '''Create diagnostic message for fault condition without auto-correction'''
                    diagnostic_message = ('{name}: The SAT has been detected to be too low but auto-correction '
                                          'is not enabled'.format(name=sa_temp_dx1))
            
            elif not sat_override_check:
                diagnostic_message = '{name}: The SAT has been detected to be too low'.format(name=sa_temp_dx1)
            else:
                diagnostic_message = ('{name}: The SAT has been detected to be too low '
                                      'but auto-correction cannot be performed because the SAT set-point is in an '
                                      'override state'.format(name=sa_temp_dx1))
        else:   
            diagnostic_message = '{name}: No problem detected'.format(name=sa_temp_dx1)
            color_code = 'GREEN'

        dx_table = {
                    'datetime': str(self.timestamp[-1]), 
                    'diagnostic_name': sa_temp_dx1, 'diagnostic_message': diagnostic_message, 
                    'energy_impact': energy_impact,
                    'color_code': color_code
                    }
        
        result.insert_table_row('Economizer_dx', dx_table)
        result.log(diagnostic_message,logging.INFO)
        return result 
    
    def high_sat_sp(self, result, avg_sat_stpt, sat_override_check):
        '''
        Diagnostic to identify and correct high supply-air temperature
        setpoint
        '''
        time_d = self.timestamp[-1]-self.timestamp[0]
        time_d = int(time_d.total_seconds()/60) 

        avg_zones_reheat = self.total_reheat/(time_d*self.number_of_zones)
        avg_zones_reheat = avg_zones_reheat * 100

        avg_zone_damper = self.total_damper/(time_d*self.number_of_zones)
        avg_zone_damper = avg_zone_damper * 100
        energy_impact = None

        if (avg_zone_damper > self.percent_damper_threshold and
            avg_zones_reheat < self.percent_reheat_threshold):
            color_code ='RED'
            if avg_sat_stpt != None and not sat_override_check:
            
                if self.auto_correctflag:
                
                    sat_stpt = avg_sat_stpt - self.sat_reduction
                    '''Create diagnostic message for fault condition with auto-correction'''
                    if sat_stpt >= self.minimum_sat_stpt:
                        result.command(self.sat_stpt_cname, sat_stpt)
                        diagnostic_message = ('{name}: The SAT has been detected to be too high. The SAT has been '
                                              'increased to: '.format(name=sa_temp_dx2))
                        diagnostic_message += str(sat_stpt)
                    else:
                        '''Create diagnostic message for fault condition where the maximum SAT has been reached'''
                        result.command(self.sat_stpt_cname,self.minimum_sat_stpt)
                        diagnostic_message = ('{name}: The SAT was detected to be too high, Auto-correction has '
                                             'increased the SAT to the minimum configured SAT: '.format(name=sa_temp_dx2))
                        diagnostic_message += str(self.minimum_sat_stpt) 
                else:  
                    '''Create diagnostic message for fault condition without auto-correction'''
                    diagnostic_message = ('{name}: The SAT has been detected to be too high but auto-correction '
                                          'is not enabled'.format(name=sa_temp_dx2))
            if not sat_override_check:
                diagnostic_message = '{name}: The SAT has been detected to be too high'.format(name=sa_temp_dx2)
            else:
                diagnostic_message = ('{name}: The SAT has been detected to be too high '
                                      'but auto-correction cannot be performed because the SAT set point is in an '
                                      'override state'.format(name=sa_temp_dx2))
        else:      
            diagnostic_message = '{name}: No problem detected'.format(name=sa_temp_dx2)
            color_code = 'GREEN'

        dx_table = {
                    'datetime': str(self.timestamp[-1]), 
                    'diagnostic_name': sa_temp_dx2, 'diagnostic_message': diagnostic_message, 
                    'energy_impact': energy_impact,
                    'color_code': color_code
                    }
        result.insert_table_row('Economizer_dx', dx_table)
        result.log(diagnostic_message,logging.INFO)
        return result
    
    def no_sat_sp_reset(self, result):
        '''
        If the detected problems(s) are consistent then generate a fault message(s).
        '''
        time_d = self.timestamp[-1]-self.timestamp[0]
        time_d = int(time_d.total_seconds()/60) + 1

        avg_zones_reheat = self.total_reheat/(time_d*self.number_of_zones)
        avg_zones_reheat = avg_zones_reheat * 100
        avg_clg_coil = sum(self.clg_coil_values)/len(self.clg_coil_values)
        avg_sat = sum(self.sa_temp_values)/len(self.sa_temp_values)
     
        satemp_diff = max(self.sa_temp_values) - min(self.sa_temp_values)
        oatemp_diff = max(self.oa_temp_values) - min(self.oa_temp_values)
        energy_impact = None

        if satemp_diff <= self.satemp_diff_threshold:
            if self.ma_temp_values:
                if(oatemp_diff > self.oatemp_diff_threshold and max(self.ma_temp_values) > self.mat_low_threshold and 
                avg_zones_reheat > self.percent_reheat_threshold and avg_clg_coil > self.ccoil_on_threshold and 
                avg_sat < self.sat_high_threshold):
                    diagnostic_message = ('{name}: A supply-air temperature reset was not detected. '
                                         'This can result in excess energy consumption.'.fomat(name=sa_temp_dx3))
                    color_code = 'RED'
                else:
                    diagnostic_message = '{name}: Inconclusive diagnostic.'.format(name=sa_temp_dx3)
                    color_code = 'GREY'
            else:
                if(oatemp_diff > self.oatemp_diff_threshold and avg_zones_reheat > self.percent_reheat_threshold 
                and avg_clg_coil > self.ccoil_on_threshold and avg_sat < self.sat_high_threshold):
                    diagnostic_message = ('{name}: A supply-air temperature reset was not detected. ' 
                                          'This can result in excess energy consumption'.format(name=sa_temp_dx3))
                    color_code = 'RED'
                else:
                    diagnostic_message = '{name}: Inconclusive diagnostic.'.format(name=sa_temp_dx3)
        else:
            diagnostic_message = '{name}: No problems detected for this diagnostic.'.format(name=sa_temp_dx3)
            color_code = 'GREEN'

        dx_table = {
                    'datetime': str(self.timestamp[-1]), 
                    'diagnostic_name': sa_temp_dx2, 'diagnostic_message': diagnostic_message, 
                    'energy_impact': energy_impact,
                    'color_code': color_code
                    }
        result.insert_table_row('Economizer_dx', dx_table)

        result.log(diagnostic_message, logging.INFO)
        self.sat_stpt_values = []
        self.sa_temp_values = []
        self.timestamp = []
        
        temp1 = []
        temp2 = []
        for x in range(0,len(Application.pre_requiste_messages)-1):
            if sched_dx in Application.pre_requiste_messages[x]:
                temp1.append(Application.pre_requiste_messages[x])
                temp2.append(Application.pre_msg_time[x])
                
        Application.pre_requiste_messages = temp1
        Application.pre_msg_time = temp2

        self.oa_temp_values = []
        self.ma_temp_values = []
        self.clg_coil_values = []
        self.rht_values = []
        self.total_reheat = 0
        self.total_damper = 0
        return result

class schedule_dx(object):
    def __init__(self,unocc_time_threshold,unocc_stp_threshold,
                monday_sch,tuesday_sch,wednesday_sch,thursday_sch,
                friday_sch, saturday_sch, sunday_sch, data_window):
                                  
        self.active_sch=[]
        self.fan_status_values=[]
        self.schedule = {}
        self.duct_stp_values = []
        self.timestamp =[]
        self.monday_sch = re.sub('[:;]',',',monday_sch)
        self.monday_sch = [int(item) for item in (x.strip() for x in self.monday_sch.split(','))]          

        self.tuesday_sch = re.sub('[:;]',',',tuesday_sch)   
        self.tuesday_sch = [int(item) for item in (x.strip() for x in self.tuesday_sch.split(','))]          
        
        self.wednesday_sch = re.sub('[:;]',',',wednesday_sch)  
        self.wednesday_sch = [int(item) for item in (x.strip() for x in self.wednesday_sch.split(','))]          

        self.thursday_sch = re.sub('[:;]',',',thursday_sch)   
        self.thursday_sch = [int(item) for item in (x.strip() for x in self.thursday_sch.split(','))]          

        self.friday_sch = re.sub('[:;]',',',friday_sch)    
        self.friday_sch = [int(item) for item in (x.strip() for x in self.friday_sch.split(','))]          

        self.saturday_sch = re.sub('[:;]',',',saturday_sch)   
        self.saturday_sch = [int(item) for item in (x.strip() for x in self.saturday_sch.split(','))]          

        self.sunday_sch = re.sub('[:;]',',',sunday_sch)   
        self.sunday_sch = [int(item) for item in (x.strip() for x in self.sunday_sch.split(','))]         

        self.schedule = {0:self.monday_sch, 1:self.tuesday_sch, 2:self.wednesday_sch,
                         3:self.thursday_sch, 4:self.friday_sch, 5:self.saturday_sch,
                         6:self.sunday_sch}
        
        self.pre_msg = ('{name}: Current time is in the scheduled hours '
                        'unit is operating correctly.'.format(name=sched_dx))
        
        '''Application thresholds (Configurable)'''
        self.data_window = float(data_window)

        self.unocc_time_threshold = float(unocc_time_threshold)
        self.unocc_stp_threshold = float(unocc_stp_threshold)

    def sched_dx_alg(self, current_time, stc_pr_data, fan_stat_data, diagnostic_result):
        #Checking whether current time is in scheduled hours
        active_sch = self.schedule[current_time.weekday()]

        if(
           (current_time.hour < active_sch[0] or (current_time.hour == active_sch[0] and current_time.min < active_sch[1] ))
           or 
           (current_time.hour > active_sch[2] or (current_time.hour == active_sch[2] and current_time.min < active_sch[3] ))
           ):
            self.timestamp.append(current_time)
        else:
            Application.pre_requiste_messages.append(self.pre_msg)
            return diagnostic_result

        self.duct_stp_values.extend(stc_pr_data)
        self.fan_status_values.append(int(max(fan_stat_data)))

        time_check =  datetime.timedelta(minutes=self.data_window)

        if ((self.timestamp[-1]-self.timestamp[0]) >= time_check and
            len(self.timestamp) > 30):
            diagnostic_result = self.unocc_fan_operation(diagnostic_result)
        return diagnostic_result

    def unocc_fan_operation(self, result):
        """
        If the detected problems(s) are consistent then generate a fault message(s).
        """
        no_times_fan_status_on = [i for i in self.fan_status_values if int(i) == 1]
        per_times_fan_status_on = (len(no_times_fan_status_on)/len(self.fan_status_values))*100.0
        avg_duct_stpr = sum(self.duct_stp_values)/len(self.duct_stp_values)
        energy_impact = None

        if per_times_fan_status_on > self.unocc_time_threshold:
            diagnostic_message = '{name}: Supply fan is on during unoccupied hours.'.format(name=sched_dx)
            color_code = 'RED'
        else:
            if avg_duct_stpr < self.unocc_stp_threshold:
                diagnostic_message = '{name}: No problems detected.'.format(name=sched_dx)
                color_code = 'GREEN'
            else:
                diagnostic_message = ('{name}: Fan status show the fan is off '
                                      'but the duct static pressure is high, '
                                     'check the functionality of the pressure sensor.'.format(name=sched_dx))
                color_code = 'GREY'
                
        dx_table = {
                    'datetime': str(self.timestamp[-1]), 
                    'diagnostic_name': sched_dx, 'diagnostic_message': diagnostic_message, 
                    'energy_impact': energy_impact,
                    'color_code': color_code
                    }
        result.insert_table_row('Economizer_dx', dx_table)
        result.log(diagnostic_message, logging.INFO)
        self.duct_stp_values = []
        self.fan_status_values=[]
        self.timestamp = []
        Application.pre_requiste_messages = []
        Application.pre_msg_time = []
        return result
        

        