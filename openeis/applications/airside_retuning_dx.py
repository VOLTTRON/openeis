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
import logging
import re
from openeis.applications import (DrivenApplicationBaseClass,
                                  OutputDescriptor,
                                  ConfigDescriptor,
                                  InputDescriptor,
                                  Results,
                                  ApplicationDescriptor)

duct_stc_dx = 'Duct Static Pressure Diagnostics'
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
    Air-side HVAC Auto-Retuning to identify problems
    related to static pressure contrl of AHU/RTU
    '''
    fan_status_name = 'fan_status'
    zone_reheat_name = 'zone_reheat'
    zone_damper_name = 'zone_damper'
    fan_speedcmd_name = 'fan_speedcmd'
    duct_stp_name = 'duct_stp'
    sa_temp_name = 'sa_temp'
    sat_stpt_name = 'sat_stpt'
    duct_stp_stpt_name = 'duct_stp_stpt'

    fan_speedcmd_priority = ''
    duct_stp_stpt_priority = ''
    ahu_ccoil_priority = ''
    sat_stpt_priority = ''

    time_format = '%m/%d/%Y %H:%M'

    def __init__(self, *args,
                 override_state=None, no_required_data=None,
                 data_window=None, number_of_zones=None, auto_correctflag=None,
                 data_sample_rate=None, warm_up_time=None,
                 duct_stc_retuning=None, max_duct_stp_stpt=None,
                 high_supply_fan_threshold=None,
                 zone_high_damper_threshold=None,
                 zone_low_damper_threshold=None,
                 min_duct_stp_stpt=None, hdzone_damper_threshold=None,
                 low_supply_fan_threshold=None,
                 setpoint_allowable_deviation=None,

                 stpr_diff_threshold=None,

                 percent_reheat_threshold=None, rht_on_threshold=None,
                 satemp_diff_threshold=None,

                 sat_high_damper_threshold=None, percent_damper_threshold=None,
                 minimum_sat_stpt=None, sat_reduction=None,

                 reheat_valve_threshold=None,
                 maximum_sat_stpt=None, sat_increase=None,

                 unocc_time_threshold=None, unocc_stp_threshold=None,
                 monday_sch=None, tuesday_sch=None, wednesday_sch=None,
                 thursday_sch=None, friday_sch=None, saturday_sch=None,
                 sunday_sch=None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        Application.pre_requiste_messages = []
        Application.pre_msg_time = []

        no_required_data = int(no_required_data)
        self.total_reheat = 0
        self.total_damper = 0

        '''Pre-requisite messages'''
        self.pre_msg0 = ('Fan Status is not available, '
                         'could not verify system is ON.')
        self.pre_msg1 = ('Supply fan is off, current data will '
                         'not be used for diagnostics.')
        self.pre_msg2 = ('Missing required data for diagnostic:  '
                         'duct static pressure.')
        self.pre_msg3 = ('Missing required data for diagnostic:  '
                         'duct static pressure set point')
        self.pre_msg4 = ('Missing required data for diagnostic:  '
                         'terminal-box damper-position (all zones).')
        self.pre_msg5 = ('Missing required data for diagnostic: SAT.')
        self.pre_msg6 = ('Missing required data for diagnostic: '
                         'terminal-box reheat-valve-positions (all zones).')
        self.pre_msg7 = ('Missing required data for diagnostic: '
                         'SAT set point.')

        '''Point names (Configurable)'''
        self.fan_status_name = Application.fan_status_name
        self.zone_reheat_name = Application.zone_reheat_name
        self.zone_damper_name = Application.zone_damper_name
        self.fan_speedcmd_name = Application.fan_speedcmd_name
        self.duct_stp_name = Application.duct_stp_name
        self.sa_temp_name = Application.sa_temp_name
        Application.sat_stpt_cname = Application.sat_stpt_name
        Application.duct_stp_stpt_cname = Application.duct_stp_stpt_name

        '''optional points'''
        self.override_state = override_state
        if Application.fan_speedcmd_name is not None:
            Application.fan_speedcmd_name = \
                Application.fan_speedcmd_name.lower()
        else:
            Application.fan_speedcmd_name = None

        Application.fan_speedcmd_priority = \
            Application.fan_speedcmd_priority.lower()
        Application.duct_stp_stpt_priority = \
            Application.duct_stp_stpt_priority.lower()
        Application.ahu_ccoil_priority = Application.ahu_ccoil_priority.lower()
        Application.sat_stpt_priority = Application.sat_stpt_priority.lower()

        '''Zone Parameters'''
        Application.zone_damper_name = Application.zone_damper_name.lower()
        Application.zone_reheat_name = Application.zone_reheat_name.lower()

        '''Application thresholds (Configurable)'''
        self.data_window = float(data_window)
        self.low_supply_fan_threshold = float(low_supply_fan_threshold)
        self.high_supply_fan_threshold = float(high_supply_fan_threshold)
        self.warm_up_flag = None
        self.warm_up_time = int(warm_up_time)
        self.warm_up_start = None

        self.static_dx = duct_static_dx(max_duct_stp_stpt, duct_stc_retuning,
                                        data_window, no_required_data,
                                        number_of_zones,
                                        zone_high_damper_threshold,
                                        zone_low_damper_threshold,
                                        setpoint_allowable_deviation,
                                        auto_correctflag,
                                        hdzone_damper_threshold,
                                        min_duct_stp_stpt)

        self.sat_dx = supply_air_temp_dx(data_window, no_required_data,
                                         data_sample_rate,
                                         number_of_zones,
                                         auto_correctflag, rht_on_threshold,
                                         sat_high_damper_threshold,
                                         percent_damper_threshold,
                                         percent_reheat_threshold,
                                         setpoint_allowable_deviation,
                                         minimum_sat_stpt, sat_reduction,
                                         reheat_valve_threshold,
                                         maximum_sat_stpt, sat_increase)

        self.sched_occ_dx = schedule_reset_dx(unocc_time_threshold,
                                              unocc_stp_threshold,
                                              monday_sch, tuesday_sch,
                                              wednesday_sch, thursday_sch,
                                              friday_sch, saturday_sch,
                                              sunday_sch, data_window,
                                              no_required_data,
                                              stpr_diff_threshold,
                                              satemp_diff_threshold)

    @classmethod
    def get_config_parameters(cls):
        '''
        Generate required configuration
        parameters with description for user
        '''
        return {
            'data_window': ConfigDescriptor(float, 'Minimum Elapsed time for '
                                            'analysis (15) minutes'),

            'no_required_data': ConfigDescriptor(int,
                                                 'Number of required '
                                                 'data measurements to '
                                                 'perform diagnostic (10)'),

            'data_sample_rate':
            ConfigDescriptor(float,
                             'Data sampling rate (minutes/sample)'),

            'warm_up_time':
            ConfigDescriptor(float,
                             'When the system starts this much '
                             'time will be allowed to elapse before adding '
                             'using data for analysis (10) minutes'),

            'auto_correctflag':
            ConfigDescriptor(bool,
                             'Takes an appropriate diagnostic '
                             'action to address the faults, such as '
                             'adjusting the set-points (True)'),

            'number_of_zones':
            ConfigDescriptor(float,
                             'Number of zones served by AHU'),

            'zone_high_damper_threshold':
            ConfigDescriptor(float,
                             'Number of zones served by AHU'),

            'zone_low_damper_threshold':
            ConfigDescriptor(float,
                             'Number of zones served by AHU'),

            'override_state':
            ConfigDescriptor(bool,
                             'Override state (only for implementation '
                             'with live devices)'),

            'max_duct_stp_stpt':
            ConfigDescriptor(float,
                             'Maximum duct static set point (in. w.c.) '
                             'allowed, when auto-correction diagnostic is '
                             'active, i.e., the set point chosen by the '
                             'diagnostic will never exceed this value'),

            'high_supply_fan_threshold':
            ConfigDescriptor(float,
                             'Value (%) above which the supply fan will '
                             'be considered running at its maximum speed. '
                             'If fan is running at its maximum speed, no '
                             'static pressure retuning application '
                             'will be active'),

            'duct_stc_retuning':
            ConfigDescriptor(float,
                             'Increment/decrement of static pressure '
                             'set-point (in. w.c.) in one time step. '
                             'This is used while taking an appropriate '
                             'diagnostic action to clear the static '
                             'pressure faults.'),

            'min_duct_stp_stpt':
            ConfigDescriptor(float, 'Minimum static set point allowed '
                             'when auto-correction diagnostic is active, '
                             'i.e., the set point chosen by the diagnostic'
                             ' will always be greater than this value'),

            'hdzone_damper_threshold':
            ConfigDescriptor(float,
                             'Threshold for zone damper (30  (%)). If the '
                             'averaged value of the zone dampers is less '
                             'than this threshold the fan is '
                             'supplying too much air.'),

            'low_supply_fan_threshold':
            ConfigDescriptor(float,
                             'Value above which the supply fan will be '
                             'considered at its minimum speed (20  (%))'),

            'setpoint_allowable_deviation':
            ConfigDescriptor(float,
                             '% allowable deviation from set points '
                             '(10 (%)). A message will be generated if '
                             'the different between the set point and '
                             'actual value of a variable exceeds '
                             'this value.'),

            'stpr_diff_threshold':
            ConfigDescriptor(float,
                             'Required difference between minimum and '
                             'maximum duct-static pressure for static '
                             'pressure reset diagnostic (0.1 in. w.c.). '
                             'This is used to detect whether there is a '
                             'reset for the duct static pressure '
                             'set-point'),

            'reheat_valve_threshold':
            ConfigDescriptor(float,
                             'Zone reheat valve threshold for SAT '
                             'Dx (50 (%))'),

            'percent_reheat_threshold':
            ConfigDescriptor(float,
                             'SAT Dx threshold for % of zone with '
                             'reheat ON (25 (%))'),

            'maximum_sat_stpt':
            ConfigDescriptor(float,
                             'Maximum SAT set point allowed when '
                             'auto-correction diagnostic is active, '
                             'i.e., the set point chosen by the '
                             'diagnostic will never exceed this value'),

            'rht_on_threshold':
            ConfigDescriptor(float,
                             'Value above which zone reheat is '
                             'considered ON (10 (%))'),

            'sat_reduction':
            ConfigDescriptor(float,
                             'Decrement of  SA temperature '
                             'set-point (in. w.c.) in one time step. '
                             'This is used while taking an appropriate '
                             'diagnostic action to address SA temperature '
                             'related  faults.(0.5 F)'),
            'sat_increase':
            ConfigDescriptor(float,
                             'Increment of SA temperature '
                             'set-point (in. w.c.) in one time step. '
                             'This is used while taking an appropriate '
                             'diagnostic action to address SA temperature '
                             'related  faults.(0.5 F)'),

            'sat_high_damper_threshold':
            ConfigDescriptor(float,
                             'High zone damper threshold for SAT '
                             'Dx (80  (%))'),

            'percent_damper_threshold':
            ConfigDescriptor(float,
                             'SAT Dx threshold for % of zone dampers '
                             'above high damper threshold (50  (%))'),

            'minimum_sat_stpt':
            ConfigDescriptor(float,
                             'Minimum SAT set point allowed when '
                             'auto-correction diagnostic is active, '
                             'I.E., the set point chosen by the '
                             'diagnostic will always be greaten than '
                             'this value'),

            'satemp_diff_threshold':
            ConfigDescriptor(float,
                             'Threshold for supply-air temperature '
                             'difference for SAT Reset Dx (3.0 (F)). '
                             'Used in No reset of SA temperature '
                             'set-point application. Detects if there '
                             'is sufficient variation in the SA '
                             'temperature.'),

            'unocc_time_threshold':
            ConfigDescriptor(float,
                             'Time threshold used for AHU schedule Dx '
                             '(80 (%)). Used by the 24-hr fan operation '
                             'diagnostic. Used to detect whether the '
                             'fan is on during unoccupied time period.'),

            'unocc_stp_threshold':
            ConfigDescriptor(float,
                             'AHU off static pressure deadband '
                             '(0.2 (in w.c.)). Used by the 24-hr '
                             'fan operation diagnostic. Detects whether '
                             'the duct static pressure exceeds this '
                             'value during non-working scheduled hours.'),

            'monday_sch':
            ConfigDescriptor(str,
                             'Monday AHU occupied schedule (6:30;18:30). '
                             'Used to detect the time when fan should be '
                             'operational.'),

            'tuesday_sch':
            ConfigDescriptor(str,
                             'Tuesday AHU occupied schedule (6:30;18:30). '
                             'Used to detect the time when fan should be '
                             'operational.'),

            'wednesday_sch':
            ConfigDescriptor(str,
                             'Wednesday AHU occupied schedule '
                             '(6:30;18:30). Used to detect the '
                             'time when fan should be operational.'),

            'thursday_sch':
            ConfigDescriptor(float,
                             'Thursday AHU occupied schedule '
                             '(6:30;18:30). Used to detect the time '
                             'when fan should be operational.'),
            'friday_sch':
            ConfigDescriptor(str,
                             'Friday AHU occupied schedule '
                             '(6:30;18:30). Used to detect the '
                             'time when fan should be operational.'),

            'saturday_sch':
            ConfigDescriptor(str,
                             'Saturday AHU occupied schedule '
                             '(6:30;18:30). Used to detect the '
                             'time when fan should be operational.'),

            'sunday_sch':
            ConfigDescriptor(str,
                             'Sunday AHU occupied schedule '
                             '(6:30;18:30). Used to detect the '
                             'time when fan should be operational.')
                }

    @classmethod
    def get_app_descriptor(cls):
        name = 'airside_returning_dx'
        desc = 'airside_returning_dx'
        return ApplicationDescriptor(app_name=name, description=desc)

    @classmethod
    def required_input(cls):
        '''
        Generate required inputs with description for
        user.
        '''
        return {
            cls.fan_status_name:
            InputDescriptor('SupplyFanStatus',
                            'AHU Supply Fan Status', count_min=1),

            cls.fan_speedcmd_name:
            InputDescriptor('SupplyFanSpeed',
                            'AHU supply fan speed', count_min=1),

            cls.zone_reheat_name:
            InputDescriptor('TeminalBoxReheat', 'All terminal-box '
                            'reheat valve commands', count_min=1),

            cls.zone_damper_name:
            InputDescriptor('TerminalBoxDamper',
                            'All terminal-box damper commands', count_min=1),

            cls.duct_stp_name:
            InputDescriptor('DuctStaticSp', 'AHU duct static pressure',
                            count_min=1),

            cls.duct_stp_stpt_name:
            InputDescriptor('DuctStaticPrSp', 'Duct static pressure set point',
                            count_min=1),

            cls.sa_temp_name:
            InputDescriptor('SupplyAirTemp', 'AHU supply-air '
                            '(discharge-air) temperature', count_min=1),

            cls.sat_stpt_name:
            InputDescriptor('SupplyAirTempSp',
                            'Supply-air temperature set-point', count_min=1)
            }

    def reports(self):
        '''
        Called by UI to create Viz.
        Describe how to present output to user
        Display this viz with these columns from this table

        display_elements is a list of display
        objects specifying viz and columns
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
        datetime_topic = '/'.join(output_topic_base+['airside_dx', 'date'])
        message_topic = '/'.join(output_topic_base+['airside_dx', 'message'])
        diagnostic_name = '/'.join(output_topic_base+['airside_dx',
                                                      'diagnostic_name'])
        energy_impact = '/'.join(output_topic_base+['airside_dx',
                                                    'energy_impact'])
        color_code = '/'.join(output_topic_base+['airside_dx', 'color_code'])

        output_needs = {
            'Airside_dx': {
                'datetime': OutputDescriptor('datetime', datetime_topic),
                'diagnostic_name': OutputDescriptor('string', diagnostic_name),

                'diagnostic_message':
                OutputDescriptor('string', message_topic),

                'energy_impact': OutputDescriptor('float', energy_impact),
                'color_code': OutputDescriptor('string', color_code)
                }
            }
        result.update(output_needs)
        return result

    def run(self, current_time, points):
        '''
        Check application pre-quisites and assemble analysis data set.
        '''
        device_dict = {}
        diagnostic_result = Results()

        for key, value in points.iteritems():
            device_dict[key.lower()] = value

        Application.pre_msg_time.append(current_time)
        message_check = datetime.timedelta(minutes=(self.data_window))
        pre_check = Application.pre_msg_time[-1] - Application.pre_msg_time[0]
        if pre_check >= message_check:
            msg_lst = [self.pre_msg0, self.pre_msg1, self.pre_msg2,
                       self.pre_msg3, self.pre_msg4, self.pre_msg5,
                       self.pre_msg6, self.pre_msg7]
            for item in msg_lst:
                if (Application.pre_requiste_messages.count(item) >
                        (0.25) * len(Application.pre_msg_time)):
                    diagnostic_result.log(item, logging.DEBUG)
            Application.pre_requiste_messages = []
            Application.pre_msg_time = []

        fan_stat_data = []
        fan_stat_check = False
        for key, value in device_dict.items():
            if key.startswith(self.fan_status_name):
                fan_stat_check = True
                fan_stat_data.append(value)
                if int(value) == 0:
                    self.warm_up_flag = True
                    Application.pre_requiste_messages.append(self.pre_msg1)
                    return diagnostic_result

        if not fan_stat_check and self.fan_speedcmd_name is not None:
            for key, value in device_dict.iteritems():
                if key.startswith(self.fan_speedcmd_name):
                    fan_stat_check = True
                    if value < self.low_supply_fan_threshold:
                        self.warm_up_flag = True
                        Application.pre_requiste_messages.append(self.pre_msg1)
                        return diagnostic_result
                    fan_stat_data.append(1)
        if not fan_stat_check:
            Application.pre_requiste_messages.append(self.pre_msg0)
            return diagnostic_result

        low_dx_condition = False
        high_dx_condition = False
        static_override_check = False
        sat_override_check = False

        if self.warm_up_flag:
            self.warm_up_flag = False
            self.warm_up_start = current_time
            return diagnostic_result

        time_check = datetime.timedelta(minutes=self.warm_up_time - 1)
        if (self.warm_up_start is not None and
           (current_time - self.warm_up_start) < time_check):
            return diagnostic_result

        for key, value in device_dict.items():
            if (self.fan_speedcmd_name is not None and
               self.fan_speedcmd_name in key):
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
                    sat_override_check = True
            if self.sat_stpt_priority in key:
                if value == self.override_state:
                    sat_override_check = True

        stc_pr_data = []
        stc_pr_sp_data = []
        zone_damper_data = []
        satemp_data = []
        rht_data = []
        sat_stpt_data = []

        for key, value in device_dict.items():

            if (key.startswith(self.duct_stp_stpt_name) and
               value is not None):
                stc_pr_sp_data.append(value)

            elif (key.startswith(self.duct_stp_name) and
                  value is not None):
                stc_pr_data.append(value)

            elif (key.startswith(self.zone_damper_name) and
                  value is not None):
                zone_damper_data.append(value)

            elif (key.startswith(self.sat_stpt_name) and
                  value is not None):
                sat_stpt_data.append(value)

            elif (key.startswith(self.sa_temp_name) and
                  value is not None):
                satemp_data.append(value)

            elif (key.startswith(self.zone_reheat_name) and
                  value is not None):
                rht_data.append(value)

        if not stc_pr_data:
            Application.pre_requiste_messages.append(self.pre_msg2)
        if not stc_pr_sp_data:
            Application.pre_requiste_messages.append(self.pre_msg3)
        if not zone_damper_data:
            Application.pre_requiste_messages.append(self.pre_msg4)
        if not (stc_pr_data and zone_damper_data and stc_pr_sp_data):
            return diagnostic_result

        if not satemp_data:
            Application.pre_requiste_messages.append(self.pre_msg5)
        if not rht_data:
            Application.pre_requiste_messages.append(self.pre_msg6)
        if not sat_stpt_data:
            Application.pre_requiste_messages.append(self.pre_msg7)
        if (not satemp_data or not rht_data or not sat_stpt_data):
            return diagnostic_result

        diagnostic_result = self.static_dx.duct_static(
            current_time, stc_pr_sp_data, stc_pr_data, zone_damper_data,
            static_override_check, low_dx_condition,
            high_dx_condition, diagnostic_result)

        diagnostic_result = self.sat_dx.sat_diagnostics(
            current_time, satemp_data, sat_stpt_data, rht_data,
            zone_damper_data,
            diagnostic_result, sat_override_check)

        diagnostic_result = self.sched_occ_dx.sched_dx_alg(
            current_time, stc_pr_data, stc_pr_sp_data,
            sat_stpt_data, fan_stat_data, diagnostic_result)

        return diagnostic_result


class duct_static_dx(object):

    '''
    Air-side HVAC Auto-Retuning diagnostic to check if the
    duct static pressure is too low.
    '''

    def __init__(self, max_duct_stp_stpt, duct_stc_retuning, data_window,
                 no_required_data, number_of_zones, zone_high_damper_threshold,
                 zone_low_damper_threshold, setpoint_allowable_deviation,
                 auto_correctflag, hdzone_damper_threshold, min_duct_stp_stpt):
        self.zone_damper_values = []
        self.duct_stp_stpt_values = []
        self.duct_stp_values = []
        self.timestamp = []

        self.data_window = float(data_window)
        self.no_required_data = no_required_data
        self.number_of_zones = float(number_of_zones)
        self.setpoint_allowable_deviation = float(setpoint_allowable_deviation)

        self.max_duct_stp_stpt = float(max_duct_stp_stpt)
        self.duct_stc_retuning = float(duct_stc_retuning)

        self.zone_high_damper_threshold = float(zone_high_damper_threshold)
        self.zone_low_damper_threshold = float(zone_low_damper_threshold)
        self.setpoint_allowable_deviation = float(setpoint_allowable_deviation)
        self.auto_correctflag = bool(auto_correctflag)

        self.min_duct_stp_stpt = float(min_duct_stp_stpt)
        self.hdzone_damper_threshold = float(hdzone_damper_threshold)

    def duct_static(self, current_time, stc_pr_sp_data, stc_pr_data,
                    zone_dmpr_data, static_override_check, low_dx_condition,
                    high_dx_condition, diagnostic_result):
        '''
        Check duct static pressure RCx pre-requisites
        and assemble duct static pressure analysis data set
        execute RCx
        '''
        if low_dx_condition:
            diagnostic_result.log(('{name}:The supply fan is running at '
                                   'nearly 100% of full speed, data '
                                   'corresponding to {timestamp} will not be '
                                   'used for diagnostic'.
                                   format(name=duct_stc_dx,
                                          timestamp=str(current_time)),
                                   logging.DEBUG))
            return diagnostic_result
        if high_dx_condition:
            diagnostic_result.log(('{name}: The supply fan is running at '
                                   ' the minimum speed, data corresponding '
                                   'to {timestamp} will not be used for '
                                   'diagnostic'.
                                   format(name=duct_stc_dx,
                                          timestamp=str(current_time)),
                                   logging.DEBUG))
            return diagnostic_result
        self.duct_stp_values.append(sum(stc_pr_data)/len(stc_pr_data))
        self.zone_damper_values.append(sum(zone_dmpr_data)/len(zone_dmpr_data))
        self.timestamp.append(current_time)

        self.duct_stp_stpt_values.append(
            sum(stc_pr_sp_data) / len(stc_pr_sp_data))

        time_check = datetime.timedelta(minutes=self.data_window)

        if ((self.timestamp[-1] - self.timestamp[0]) >= time_check and
                len(self.timestamp) >= self.no_required_data):

            avg_duct_stpr_stpt = sum(
                self.duct_stp_stpt_values) / len(self.duct_stp_stpt_values)

            if avg_duct_stpr_stpt > 0 and avg_duct_stpr_stpt < 5:
                set_point_tracking = [abs(x - y) for
                                      x, y in zip(self.duct_stp_values,
                                                  self.duct_stp_stpt_values)]

                set_point_tracking = (sum(set_point_tracking) /
                                      (len(set_point_tracking)
                                       * avg_duct_stpr_stpt)*100)
                if set_point_tracking > self.setpoint_allowable_deviation:
                    diagnostic_message = ('{name}: The duct static '
                                          'pressure is deviating from its '
                                          'set point significantly.'.
                                          format(name=duct_stc_dx))
                    color_code = 'RED'
                    energy_impact = None
                    dx_table = {
                        'datetime': str(self.timestamp[-1]),
                        'diagnostic_name': duct_stc_dx,
                        'diagnostic_message': diagnostic_message,
                        'energy_impact': energy_impact,
                        'color_code': color_code
                    }
                diagnostic_result.insert_table_row('Airside_Dx', dx_table)
                diagnostic_result.log(diagnostic_message, logging.INFO)

            diagnostic_result = self.low_ductstatic_pr(diagnostic_result,
                                                       static_override_check)
            diagnostic_result = self.high_ductstatic_pr(diagnostic_result,
                                                        static_override_check)
        return diagnostic_result

    def low_ductstatic_sp(self, result, static_override_check):
        '''
        Diagnostic to identify and correct low duct static pressure
        (correction by modifying duct static pressure set point)
        '''
        zone_damper_temp = self.zone_damper_values
        zone_damper_temp.sort(reverse=False)
        zone_damper_lowtemp = zone_damper_temp[
            0:int(len(zone_damper_temp) / 2)]
        zone_damper_lowavg = sum(
            zone_damper_lowtemp) / len(zone_damper_lowtemp)
        zone_damper_hightemp = zone_damper_temp[
            int(len(zone_damper_temp) / 2 + 1):-1]
        zone_damper_highavg = sum(
            zone_damper_hightemp) / len(zone_damper_hightemp)
        energy_impact = None

        avg_duct_stpr_stpt = None
        if self.duct_stp_stpt_values:
            avg_duct_stpr_stpt = (sum(self.duct_stp_stpt_values) /
                                  len(self.duct_stp_stpt_values))

        if (zone_damper_highavg > self.zone_high_damper_threshold
                and zone_damper_lowavg > self.zone_low_damper_threshold):
            color_code = 'RED'
            if (avg_duct_stpr_stpt is not None and
                    not static_override_check):

                if self.auto_correctflag:
                    duct_stpr_stpt = avg_duct_stpr_stpt + \
                        self.duct_stc_retuning
                    if duct_stpr_stpt <= self.max_duct_stp_stpt:
                        result.command(
                            Application.duct_stp_stpt_cname, duct_stpr_stpt)
                        diagnostic_message = ('{name}: The duct static '
                                              'pressure was detected to be '
                                              'too low. The duct static '
                                              'pressure has been increased '
                                              'to: '.format(name=duct_static1))
                        diagnostic_message += str(duct_stpr_stpt) + ' in. w.c.'
                    else:
                        result.command(
                            Application.duct_stp_stpt_cname,
                            self.max_duct_stp_stpt)
                        diagnostic_message = ('{name}: Duct static pressure '
                                              'set point is at maximum value '
                                              'specified in configuration '
                                              'file'.format(name=duct_static1))

                else:
                    diagnostic_message = ('{name}: Duct static pressure set '
                                          'point was detected to be too low '
                                          'but auto-correction is not enabled'
                                          .format(name=duct_static1))

            elif not static_override_check:
                diagnostic_message = ('{name}: The duct static pressure was '
                                      'detected to be too low'.
                                      format(name=duct_static1))
            else:
                diagnostic_message = ('{name}: The duct static pressure was '
                                      'detected to be too low but an operator '
                                      'override was detected. Auto-correction '
                                      'can not be performed when the static '
                                      'pressure set point or fan speed '
                                      'command is in overrride'.
                                      format(name=duct_static1))
        else:
            diagnostic_message = ('{name}: No re-tuning opportunity was '
                                  'detected during the low duct static '
                                  'pressure diagnostic'.
                                  format(name=duct_static1))
            color_code = 'GREEN'

        dx_table = {
            'datetime': str(self.timestamp[-1]),
            'diagnostic_name': duct_static1,
            'diagnostic_message': diagnostic_message,
            'energy_impact': energy_impact,
            'color_code': color_code
        }

        result.insert_table_row('Airside_Dx', dx_table)
        result.log(diagnostic_message, logging.INFO)
        return result

    def high_ductstatic_pr(self, result, static_override_check):
        '''
        Diagnostic to identify and correct high duct static pressure
        (correction by modifying duct static pressure set point)
        '''
        zone_damper_temp = self.zone_damper_values
        zone_damper_temp.sort(reverse=True)
        zone_damper_temp = zone_damper_temp[0:int(len(zone_damper_temp) / 2)]
        avg_zone_damper = sum(zone_damper_temp) / len(zone_damper_temp)
        energy_impact = None
        avg_duct_stpr_stpt = None

        if self.duct_stp_stpt_values:
            avg_duct_stpr_stpt = sum(
                self.duct_stp_stpt_values) / len(self.duct_stp_stpt_values)

        if avg_zone_damper <= self.hdzone_damper_threshold:
            color_code = 'RED'
            if (avg_duct_stpr_stpt is not None and
                    not static_override_check):
                if self.auto_correctflag:
                    duct_stpr_stpt = (avg_duct_stpr_stpt -
                                      self.duct_stc_retuning)
                    if duct_stpr_stpt >= self.min_duct_stp_stpt:
                        result.command(
                            Application.duct_stp_stpt_cname, duct_stpr_stpt)
                        diagnostic_message = ('{name}: The duct static '
                                              'pressure was detected to be '
                                              'too high. The duct static '
                                              'pressure has been reduced to: '
                                              .format(name=duct_static2))
                        diagnostic_message += str(duct_stpr_stpt) + ' in. w.c.'
                    else:
                        result.command(
                            Application.duct_stp_stpt_cname,
                            self.min_duct_stp_stpt)
                        diagnostic_message = ('{name}: Duct static pressure  '
                                              'set point is at minimum value '
                                              'specified in configuration file'
                                              .format(name=duct_static2))
                else:
                    diagnostic_message = ('{name}: Duct static pressure set '
                                          'point was detected to be too high '
                                          'but auto-correction is not enabled'
                                          .format(name=duct_static2))

            elif not static_override_check:
                diagnostic_message = ('{name}: The duct static pressure was '
                                      'detected to be too high'
                                      .format(name=duct_static2))
            else:
                diagnostic_message = ('{name}: The duct static pressure was '
                                      'detected to be too high but an '
                                      'operator override was detected. '
                                      'Auto-correction can not be performed '
                                      'when the static pressure set point '
                                      'or fan speed command is in overrride'
                                      .format(name=duct_static2))
        else:
            diagnostic_message = ('{name}: No re-tuning opportunity was '
                                  'detected during the low duct static '
                                  'pressure diagnostic'
                                  .format(name=duct_static2))
            color_code = 'GREEN'

        dx_table = {
            'datetime': str(self.timestamp[-1]),
            'diagnostic_name': duct_static1,
            'diagnostic_message': diagnostic_message,
            'energy_impact': energy_impact,
            'color_code': color_code
        }

        result.insert_table_row('Airside_Dx', dx_table)
        result.log(diagnostic_message, logging.INFO)
        self.duct_stp_stpt_values = []
        self.duct_stp_values = []
        self.zone_damper_values = []
        self.timestamp = []
        return result
        return result


class supply_air_temp_dx(object):
    def __init__(self, data_window, no_required_data,
                 data_sample_rate, number_of_zones,
                 auto_correctflag, rht_on_threshold, high_damper_threshold,
                 percent_damper_threshold, percent_reheat_threshold,
                 setpoint_allowable_deviation, minimum_sat_stpt, sat_reduction,
                 reheat_valve_threshold, maximum_sat_stpt, sat_increase):

        self.timestamp = []
        self.sat_stpt_values = []
        self.sa_temp_values = []
        self.rht_values = []
        self.total_reheat = 0
        self.total_damper = 0
        self.pre_requiste_messages = []
        self.pre_msg_time = []
        self.timestamp = []
        self.reheat = []

        '''Common RCx parameters'''
        self.data_sample_rate = int(data_sample_rate)
        self.data_window = float(data_window)
        self.no_required_data = no_required_data
        self.number_of_zones = float(number_of_zones)
        self.auto_correctflag = bool(auto_correctflag)
        self.setpoint_allowable_deviation = float(setpoint_allowable_deviation)
        self.rht_on_threshold = float(rht_on_threshold)
        self.percent_reheat_threshold = float(percent_reheat_threshold)

        '''Low SAT RCx thresholds'''
        self.reheat_valve_threshold = float(reheat_valve_threshold)
        self.maximum_sat_stpt = float(maximum_sat_stpt)
        self.sat_increase = float(sat_increase)

        '''High SAT RCx thresholds'''
        self.high_damper_threshold = float(high_damper_threshold)
        self.percent_damper_threshold = float(percent_damper_threshold)
        self.minimum_sat_stpt = float(minimum_sat_stpt)
        self.sat_reduction = float(sat_reduction)

    def sat_diagnostics(self, current_time, satemp_data, sat_stpt_data,
                        rht_data, zone_damper_data,
                        diagnostic_result, sat_override_check):
        '''
        Check supply-air temperature dx
        pre-requisites and assemble analysis data set
        '''
        self.sa_temp_values.append(sum(satemp_data) / len(satemp_data))
        self.rht_values.append(sum(rht_data) / len(rht_data))
        self.sat_stpt_values.append(sum(sat_stpt_data) / len(sat_stpt_data))

        for value in rht_data:
            if value > self.rht_on_threshold:
                self.total_reheat += 1
        for value in zone_damper_data:
            if value > self.high_damper_threshold:
                self.total_damper += 1

        self.timestamp.append(current_time)
        time_check = datetime.timedelta(minutes=self.data_window - 1)

        if ((self.timestamp[-1] - self.timestamp[0]) >= time_check and
                len(self.sat_stpt_values) >= self.no_required_data):

            avg_sat_stpt = (sum(self.sat_stpt_values) /
                            len(self.sat_stpt_values))

            set_point_tracking = [abs(x - y) for x, y in
                                  zip(self.sat_stpt_values,
                                      self.sa_temp_values)]

            set_point_tracking = (sum(set_point_tracking) /
                                  len(set_point_tracking)
                                  * avg_sat_stpt) * 100
            if set_point_tracking > self.setpoint_allowable_deviation:
                diagnostic_message = ('{name}: Supply-air temperature is '
                                      'deviating significantly '
                                      'from the supply-air temperature '
                                      'set point'.format(name=sa_temp_dx))
                color_code = 'RED'
                energy_impact = None
                dx_table = {
                    'datetime': str(self.timestamp[-1]),
                    'diagnostic_name': sa_temp_dx,
                    'diagnostic_message': diagnostic_message,
                    'energy_impact': energy_impact,
                    'color_code': color_code
                }
                diagnostic_result.insert_table_row('Airside_Dx', dx_table)
                diagnostic_result.log(diagnostic_message, logging.INFO)
            diagnostic_result = self.low_sat(diagnostic_result,
                                             avg_sat_stpt,
                                             sat_override_check)
            diagnostic_result = self.high_sat(diagnostic_result,
                                              avg_sat_stpt,
                                              sat_override_check)
        return diagnostic_result

    def low_sat(self, result, avg_sat_stpt, sat_override_check):
        '''
        Diagnostic to identify and correct low supply-air temperature
        (correction by modifying SAT set point)
        '''
        time_d = self.timestamp[-1] - self.timestamp[0]
        time_d = int(time_d.total_seconds() / 60) + 1

        avg_zones_reheat = (self.total_reheat /
                            (time_d/self.data_sample_rate
                             * self.number_of_zones)) * 100
        reheat_coil_average = (sum(self.rht_values)) / (len(self.rht_values))
        energy_impact = None

        if (reheat_coil_average > self.reheat_valve_threshold and
                avg_zones_reheat > self.percent_reheat_threshold):
            color_code = 'RED'
            if (avg_sat_stpt is not None and
                    not sat_override_check):
                if self.auto_correctflag:

                    sat_stpt = avg_sat_stpt + self.sat_increase
                    '''
                    Create diagnostic message for fault
                    condition with auto-correction
                    '''
                    if sat_stpt <= self.maximum_sat_stpt:
                        result.command(Application.sat_stpt_cname, sat_stpt)
                        diagnostic_message = ('{name}: The SAT has been '
                                              'detected to be too low. '
                                              'The SAT has been increased to: '
                                              .format(name=sa_temp_dx1))
                        diagnostic_message += str(sat_stpt) + ' deg.'
                    else:
                        '''
                        Create diagnostic message
                        for fault condition where
                        the maximum SAT has been reached
                        '''
                        result.command(Application.sat_stpt_cname,
                                       self.maximum_sat_stpt)
                        diagnostic_message = ('{name}: The SAT was detected '
                                              'to be too low, Auto-correction '
                                              'has increased the SAT to the '
                                              'maximum configured SAT: '
                                              .format(name=sa_temp_dx1))

                        diagnostic_message += (str(self.maximum_sat_stpt)
                                               + ' deg. F')
                else:
                    '''
                    Create diagnostic message for fault
                    condition without auto-correction
                    '''
                    diagnostic_message = ('{name}: The SAT has been detected '
                                          'to be too low but auto-correction '
                                          'is not enabled'
                                          .format(name=sa_temp_dx1))

            elif not sat_override_check:
                diagnostic_message = ('{name}: The SAT has been detected to '
                                      'be too low'.format(name=sa_temp_dx1))
            else:
                diagnostic_message = ('{name}: The SAT has been detected to '
                                      'be too low but auto-correction cannot '
                                      'be performed because the SAT set-point '
                                      'is in an override state'
                                      .format(name=sa_temp_dx1))
        else:
            diagnostic_message = ('{name}: No problem detected'
                                  .format(name=sa_temp_dx1))
            color_code = 'GREEN'

        dx_table = {
            'datetime': str(self.timestamp[-1]),
            'diagnostic_name': sa_temp_dx1,
            'diagnostic_message': diagnostic_message,
            'energy_impact': energy_impact,
            'color_code': color_code
        }

        result.insert_table_row('Airside_Dx', dx_table)
        result.log(diagnostic_message, logging.INFO)
        return result

    def high_sat_sp(self, result, avg_sat_stpt, sat_override_check):
        '''
        Diagnostic to identify and correct high supply-air temperature
        (correction by modifying SAT set point)
        '''
        time_d = self.timestamp[-1] - self.timestamp[0]
        time_d = int(time_d.total_seconds() / 60)

        avg_zones_reheat = (self.total_reheat /
                            (time_d/self.data_sample_rate
                             * self.number_of_zones)) * 100

        avg_zone_damper = (self.total_damper /
                           (time_d/self.data_sample_rate
                            * self.number_of_zones)) * 100

        energy_impact = None

        if (avg_zone_damper > self.percent_damper_threshold and
                avg_zones_reheat < self.percent_reheat_threshold):
            color_code = 'RED'
            if (avg_sat_stpt is not None and
                    not sat_override_check):
                if self.auto_correctflag:
                    sat_stpt = avg_sat_stpt - self.sat_reduction
                    '''
                    Create diagnostic message for fault condition
                    with auto-correction
                    '''
                    if sat_stpt >= self.minimum_sat_stpt:
                        result.command(Application.sat_stpt_cname, sat_stpt)
                        diagnostic_message = ('{name}: The SAT has been '
                                              'detected to be too high. The '
                                              'SAT has been increased to: '
                                              .format(name=sa_temp_dx2))
                        diagnostic_message += str(sat_stpt)
                    else:
                        '''
                        Create diagnostic message for fault condition
                        where the maximum SAT has been reached
                        '''
                        result.command(
                            Application.sat_stpt_cname, self.minimum_sat_stpt)
                        diagnostic_message = ('{name}: The SAT was detected '
                                              'to be too high, '
                                              'Auto-correction has increased '
                                              'the SAT to the minimum '
                                              'configured SAT: '
                                              .format(name=sa_temp_dx2))
                        diagnostic_message += str(self.minimum_sat_stpt)
                else:
                    '''
                    Create diagnostic message for fault condition
                    without auto-correction
                    '''
                    diagnostic_message = ('{name}: The SAT has been detected '
                                          'to be too high but auto-correction '
                                          'is not enabled'
                                          .format(name=sa_temp_dx2))
            if not sat_override_check:
                diagnostic_message = ('{name}: The SAT has been detected to '
                                      'be too high'.format(name=sa_temp_dx2))
            else:
                diagnostic_message = ('{name}: The SAT has been detected to '
                                      'be too high but auto-correction cannot '
                                      'be performed because the SAT set point '
                                      'is in an override state'
                                      .format(name=sa_temp_dx2))
        else:
            diagnostic_message = ('{name}: No problem detected'
                                  .format(name=sa_temp_dx2))
            color_code = 'GREEN'

        dx_table = {
            'datetime': str(self.timestamp[-1]),
            'diagnostic_name': sa_temp_dx2,
            'diagnostic_message': diagnostic_message,
            'energy_impact': energy_impact,
            'color_code': color_code
        }
        result.insert_table_row('Airside_Dx', dx_table)
        result.log(diagnostic_message, logging.INFO)
        self.sat_stpt_values = []
        self.sa_temp_values = []
        self.timestamp = []

        temp1 = []
        temp2 = []
        for x in range(0, len(Application.pre_requiste_messages) - 1):
            if sched_dx in Application.pre_requiste_messages[x]:
                temp1.append(Application.pre_requiste_messages[x])
                temp2.append(Application.pre_msg_time[x])

        Application.pre_requiste_messages = temp1
        Application.pre_msg_time = temp2

        self.rht_values = []
        self.total_reheat = 0
        self.total_damper = 0
        return result


class schedule_reset_dx(object):

    def __init__(self, unocc_time_threshold, unocc_stp_threshold,
                 monday_sch, tuesday_sch, wednesday_sch, thursday_sch,
                 friday_sch, saturday_sch, sunday_sch, data_window,
                 no_required_data, stpr_diff_threshold, satemp_diff_threshold):

        self.active_sch = []
        self.fan_status_values = []
        self.schedule = {}
        self.duct_stp_values = []
        self.duct_stp_stpt_values = []
        self.sat_stpt_values = []
        self.timestamp = []
        self.monday_sch = re.sub('[:;]', ',', monday_sch)
        self.monday_sch = [int(item) for item in (x.strip()
                                                  for x in
                                                  self.monday_sch.split(','))]

        self.tuesday_sch = re.sub('[:;]', ',', tuesday_sch)
        self.tuesday_sch = [int(item) for item
                            in (x.strip() for x in
                                self.tuesday_sch.split(','))]

        self.wednesday_sch = re.sub('[:;]', ',', wednesday_sch)
        self.wednesday_sch = [int(item) for item
                              in(x.strip()for x in
                                 self.wednesday_sch.split(','))]

        self.thursday_sch = re.sub('[:;]', ',', thursday_sch)
        self.thursday_sch = [int(item) for item
                             in (x.strip() for x in
                                 self.thursday_sch.split(','))]

        self.friday_sch = re.sub('[:;]', ',', friday_sch)
        self.friday_sch = [int(item) for item
                           in (x.strip() for x in
                               self.friday_sch.split(','))]

        self.saturday_sch = re.sub('[:;]', ',', saturday_sch)
        self.saturday_sch = [int(item) for item
                             in (x.strip() for x in
                                 self.saturday_sch.split(','))]

        self.sunday_sch = re.sub('[:;]', ',', sunday_sch)
        self.sunday_sch = [int(item) for item
                           in (x.strip() for x in
                               self.sunday_sch.split(','))]

        self.schedule = {0: self.monday_sch, 1: self.tuesday_sch,
                         2: self.wednesday_sch, 3: self.thursday_sch,
                         4: self.friday_sch, 5: self.saturday_sch,
                         6: self.sunday_sch}

        self.pre_msg = ('{name}: Current time is in the scheduled hours '
                        'unit is operating correctly.'.format(name=sched_dx))

        '''Application thresholds (Configurable)'''
        self.data_window = float(data_window)
        self.no_required_data = no_required_data
        self.unocc_time_threshold = float(unocc_time_threshold)
        self.unocc_stp_threshold = float(unocc_stp_threshold)
        self.stpr_diff_threshold = float(stpr_diff_threshold)
        self.satemp_diff_threshold = float(satemp_diff_threshold)

    def sched_dx_alg(self, current_time, stc_pr_data, stc_pr_sp_data,
                     sat_stpt_data,
                     fan_stat_data, diagnostic_result):
        '''
        Check schedule status and unit operational status
        '''
        fan_stat = None
        duct_stp_stpt_values = None
        active_sch = self.schedule[current_time.weekday()]

        if((current_time.hour < active_sch[0] or
            (current_time.hour == active_sch[0] and
                current_time.minute < active_sch[1]))
           or
           (current_time.hour > active_sch[2] or
            (current_time.hour == active_sch[2] and
               current_time.minute < active_sch[3]))):
            self.duct_stp_values.extend(stc_pr_data)
            self.fan_status_values.append(int(max(fan_stat_data)))
            fan_stat = self.fan_status_values[-1]
            duct_stp = self.duct_stp_values[-1]
        else:
            self.duct_stp_stpt_values.append(sum(stc_pr_sp_data) /
                                             len(stc_pr_sp_data))

            duct_stp_stpt_values = self.duct_stp_stpt_values[-1]

            self.sat_stpt_values.append(sum(sat_stpt_data) /
                                        len(sat_stpt_data))

            sat_stpt_values = self.sat_stpt_values[-1]

        run = False
        if self.timestamp and self.timestamp[-1].date() != current_time.date():
            run = True

        self.timestamp.append(current_time)

        if run and len(self.timestamp) >= self.no_required_data:
            diagnostic_result = self.unocc_fan_operation(diagnostic_result)
            diagnostic_result = self.no_static_pr_reset(diagnostic_result)
            diagnostic_result = self.no_sat_sp_reset(diagnostic_result)
            self.sat_stpt_values = []
            self.duct_stp_stpt_values = []
            self.duct_stp_values = []
            self.fan_status_values = []
            if duct_stp_stpt_values is not None:
                self.sat_stpt_values.append(sat_stpt_values)
                self.duct_stp_stpt_values.append(duct_stp_stpt_values)
            if fan_stat is not None:
                self.fan_status_values.append(fan_stat)
                self.duct_stp_values.append(duct_stp)
            self.timestamp = [self.timestamp[-1]]
        return diagnostic_result

    def unocc_fan_operation(self, result):
        '''
        If the detected problems(s) are consistent
        then generate a fault message(s).
        '''
        no_times_fan_status_on = [i for i in self.fan_status_values
                                  if int(i) == 1]

        if self.fan_status_values:
            per_times_fan_status_on = (len(no_times_fan_status_on) /
                                       len(self.fan_status_values)) * 100.0
        else:
            per_times_fan_status_on = 0

        if self.duct_stp_values:
            avg_duct_stpr = (sum(self.duct_stp_values) /
                             len(self.duct_stp_values))
        else:
            avg_duct_stpr = 0
        energy_impact = None

        if per_times_fan_status_on > self.unocc_time_threshold:
            diagnostic_message = ('{name}: Supply fan is on during unoccupied '
                                  'times.'.format(name=sched_dx))
            color_code = 'RED'
        else:
            if avg_duct_stpr < self.unocc_stp_threshold:
                diagnostic_message = '{name}: No problems detected.'.format(
                    name=sched_dx)
                color_code = 'GREEN'
            else:
                diagnostic_message = ('{name}: Fan status show the fan is off '
                                      'but the duct static pressure is high, '
                                      'check the functionality of the '
                                      'pressure sensor.'.format(name=sched_dx))
                color_code = 'GREY'

        dx_table = {
            'datetime': str(self.timestamp[-1]),
            'diagnostic_name': sched_dx,
            'diagnostic_message': diagnostic_message,
            'energy_impact': energy_impact,
            'color_code': color_code
        }
        result.insert_table_row('Airside_Dx', dx_table)
        result.log(diagnostic_message, logging.INFO)
        self.duct_stp_values = []
        self.fan_status_values = []
        Application.pre_requiste_messages = []
        Application.pre_msg_time = []
        return result

    def no_static_pr_reset(self, result):
        '''
        Auto-RCx  to detect whether a static pressure set point
        reset is implemented
        '''
        stp_diff = max(self.duct_stp_stpt_values) - min(self.duct_stp_stpt_values)

        energy_impact = None

        if stp_diff < self.stpr_diff_threshold:

                    diagnostic_message = ('{name}: No duct static pressure '
                                          'reset detected. A duct static '
                                          'pressure set point reset can save '
                                          'significant amounts of energy'
                                          .format(name=duct_static3))
                    color_code = 'RED'
        else:
            diagnostic_message = '{name}: No problem detected'.format(
                name=duct_static3)
            color_code = 'GREEN'

        dx_table = {
            'datetime': str(self.timestamp[-1]),
            'diagnostic_name': duct_static3,
            'diagnostic_message': diagnostic_message,
            'energy_impact': energy_impact,
            'color_code': color_code
            }

        result.insert_table_row('Airside_Dx', dx_table)
        result.log(diagnostic_message, logging.INFO)
        self.duct_stp_stpt_values = []
        return result

    def no_sat_sp_reset(self, result):
        '''
        If the detected problems(s) are consistent
        then generate a fault message(s).
        '''
        satemp_diff = max(self.sat_stpt_values) - min(self.sat_stpt_values)
        energy_impact = None

        if satemp_diff <= self.satemp_diff_threshold:
            diagnostic_message = ('{name}: A supply-air temperature '
                                  'reset was not detected. This can '
                                  'result in excess energy '
                                  'consumption.'
                                  .format(name=sa_temp_dx3))
            color_code = 'RED'
        else:
            diagnostic_message = ('{name}: No problems detected for this '
                                  'diagnostic.'.format(name=sa_temp_dx3))
            color_code = 'GREEN'

        dx_table = {
            'datetime': str(self.timestamp[-1]),
            'diagnostic_name': sa_temp_dx2,
            'diagnostic_message': diagnostic_message,
            'energy_impact': energy_impact,
            'color_code': color_code
        }
        result.insert_table_row('Airside_Dx', dx_table)
        result.log(diagnostic_message, logging.INFO)
        return result
