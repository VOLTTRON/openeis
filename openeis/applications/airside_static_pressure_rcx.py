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
import math
from openeis.applications import (DrivenApplicationBaseClass,
                                  OutputDescriptor,
                                  ConfigDescriptor,
                                  InputDescriptor,
                                  Results,
                                  Descriptor,
                                  reports)

DUCT_STC_RCx = 'Duct Static Pressure Control Loop Diagnostics'
DUCT_STC_RCx1 = 'Low Duct Static Pressure Dx'
DUCT_STC_RCx2 = 'High Duct Static Pressure Dx'
DUCT_STC_RCx3 = 'No Static Pressure Reset Dx'
SA_TEMP_RCx = 'Supply-air temperature Control Loop Dx'
SA_TEMP_RCx1 = 'Low Supply-air Temperature Dx'
SA_TEMP_RCx2 = 'High Supply-air Temperature Dx'
SA_TEMP_RCx3 = 'No Supply-air Temperature Reset Dx'
SCHED_RCx = 'Operational Schedule Dx'


class Application(DrivenApplicationBaseClass):
    '''
    Air-side HVAC Auto-Retuning Diagnostics
    for AHUs
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

    def __init__(self, *args, no_required_data=1, data_window=1,
                 warm_up_time=0, duct_stc_retuning=0.15,
                 max_duct_stp_stpt=2.5, high_supply_fan_threshold=100.0,
                 zone_high_damper_threshold=90.0,
                 zone_low_damper_threshold=10.0, min_duct_stp_stpt=0.5,
                 hdzone_damper_threshold=30.0, low_supply_fan_threshold=20.0,
                 setpoint_allowable_deviation=10.0, stpr_reset_threshold=0.25,
                 percent_reheat_threshold=25.0, rht_on_threshold=10.0,
                 sat_reset_threshold=5.0, sat_high_damper_threshold=80.0,
                 percent_damper_threshold=50.0,
                 minimum_sat_stpt=50.0, sat_retuning=1.0,
                 reheat_valve_threshold=50.0, maximum_sat_stpt=75.0,
                 unocc_time_threshold=30.0, unocc_stp_threshold=0.2,
                 monday_sch='6:30;18:30', tuesday_sch='6:30;18:30',
                 wednesday_sch='6:30;18:30', thursday_sch='6:30;18:30',
                 friday_sch='6:30;18:30', saturday_sch='0:00;0:00',
                 sunday_sch='0:00;0:00',sensitivity = 1.0, **kwargs):
        super().__init__(*args, **kwargs)
        Application.pre_requiste_messages = []
        Application.pre_msg_time = []
        no_required_data = int(no_required_data)
        # Pre-requisite messages
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

        if sensitivity == 0.0:
            # low sensitivity
            zone_high_damper_threshold = float(zone_high_damper_threshold) * 1.5
            zone_low_damper_threshold = float(zone_low_damper_threshold) * 1.5
            stcpr_reset_threshold = float(stpr_reset_threshold) * 1.5

            sat_reset_threshold = float(sat_reset_threshold) * 1.5
            sat_high_damper_threshold= float(sat_high_damper_threshold) * 1.5
            percent_damper_threshold = float(percent_damper_threshold) * 1.5
            percent_reheat_threshold= float(percent_reheat_threshold) * 1.5
            reheat_valve_threshold = float(reheat_valve_threshold) * 1.5

            unocc_stp_threshold= float(unocc_stp_threshold) * 1.5
            unocc_time_threshold= float(unocc_time_threshold) * 1.5

        elif sensitivity == 2.0:
            # high sensitivity
            zone_high_damper_threshold = float(zone_high_damper_threshold) * 0.5
            zone_low_damper_threshold = float(zone_low_damper_threshold) * 0.5
            stcpr_reset_threshold = float(stpr_reset_threshold) * 0.5

            sat_reset_threshold = float(sat_reset_threshold) * 0.5
            sat_high_damper_threshold= float(sat_high_damper_threshold) * 0.5
            percent_damper_threshold = float(percent_damper_threshold) * 0.5
            percent_reheat_threshold= float(percent_reheat_threshold) * 0.5
            reheat_valve_threshold = float(reheat_valve_threshold) * 0.5

            unocc_stp_threshold= float(unocc_stp_threshold) * 0.5
            unocc_time_threshold= float(unocc_time_threshold) * 0.5
        else:
            # Normal sensitivtyy
            zone_high_damper_threshold = float(zone_high_damper_threshold)
            zone_low_damper_threshold = float(zone_low_damper_threshold)
            stcpr_reset_threshold = float(stpr_reset_threshold)

            sat_reset_threshold = float(sat_reset_threshold)
            sat_high_damper_threshold = float(sat_high_damper_threshold)
            percent_damper_threshold = float(percent_damper_threshold)
            percent_reheat_threshold = float(percent_reheat_threshold)
            reheat_valve_threshold = float(reheat_valve_threshold)

            unocc_stp_threshold= float(unocc_stp_threshold)
            unocc_time_threshold= float(unocc_time_threshold)

        # Point names (Configurable)
        self.fan_status_name = Application.fan_status_name
        self.duct_stp_stpt_name = Application.duct_stp_stpt_name
        self.duct_stp_name = Application.duct_stp_name
        self.sa_temp_name = Application.sa_temp_name
        self.sat_stpt_name = Application.sat_stpt_name
        Application.sat_stpt_cname = Application.sat_stpt_name
        Application.duct_stp_stpt_cname = Application.duct_stp_stpt_name
        # Optional points
        self.override_state = 'AUTO'
        if Application.fan_speedcmd_name is not None:
            self.fan_speedcmd_name = Application.fan_speedcmd_name.lower()
        else:
            self.fan_speedcmd_name = None
        self.fan_speedcmd_priority = Application.fan_speedcmd_priority.lower()
        self.duct_stp_stpt_priority = Application.duct_stp_stpt_priority.lower()
        self.ahu_ccoil_priority = Application.ahu_ccoil_priority.lower()
        self.sat_stpt_priority = Application.sat_stpt_priority.lower()
        # Zone Parameters
        self.zone_damper_name = Application.zone_damper_name.lower()
        self.zone_reheat_name = Application.zone_reheat_name.lower()
        # Application thresholds (Configurable)
        self.data_window = float(data_window)
        self.low_supply_fan_threshold = float(low_supply_fan_threshold)
        self.high_supply_fan_threshold = float(high_supply_fan_threshold)
        self.warm_up_flag = None
        self.warm_up_time = int(warm_up_time)
        self.warm_up_start = None
        auto_correctflag = True
        self.static_dx = DuctStaticRcx(data_window, no_required_data,
                                       auto_correctflag,
                                       setpoint_allowable_deviation,
                                       max_duct_stp_stpt,
                                       duct_stc_retuning,
                                       zone_high_damper_threshold,
                                       zone_low_damper_threshold,
                                       hdzone_damper_threshold,
                                       min_duct_stp_stpt,
                                       stpr_reset_threshold)


    @classmethod
    def get_config_parameters(cls):
        '''
        Generate required configuration
        parameters with description for user
        '''
        dgr_sym = u'\N{DEGREE SIGN}'
        return {
            'data_window':
            ConfigDescriptor(int,
                             'Minimum Elapsed time for '
                             'analysis (minutes)',
                             value_default=15),
            'no_required_data':
            ConfigDescriptor(int,
                             'Number of required data measurements to '
                             'perform diagnostic',
                             value_default=10),
            'low_supply_fan_threshold':
                ConfigDescriptor(float,
                                 'Value above which the supply fan will be '
                                 'considered at its minimum speed (%)',
                                 value_default=20.0),
            'warm_up_time':
            ConfigDescriptor(int,
                             'When the system starts this much '
                             'time will be allowed to elapse before adding '
                             'using data for analysis (minutes)',
                             value_default=30),
            'zone_high_damper_threshold':
            ConfigDescriptor(float,
                             ('Zone high damper threshold '
                              'used for detection of duct static '
                              'pressure problems (%)'),
                             value_default=90.0),
            'zone_low_damper_threshold':
            ConfigDescriptor(float,
                             ('Zone low damper threshold '
                              'used for detection of duct static '
                              'pressure problems (%)'),
                             value_default=10.0),
            'max_duct_stp_stpt':
            ConfigDescriptor(float,
                             'Maximum duct static pressure set point '
                             'allowed, when auto-correction is '
                             'enabled, i.e., the set point chosen by the '
                             'diagnostic will never exceed this value '
                             '(inch w.g.)', value_default=2.5),
            'duct_stc_retuning':
            ConfigDescriptor(float,
                             ('Increment/decrement of static pressure '
                              'set point during auto-correction '
                              '(inch w.g.)'),
                             value_default=0.15),
            'min_duct_stp_stpt':
            ConfigDescriptor(float,
                             'Minimum duct static pressure set point '
                             'allowed, when auto-correction is '
                             'enabled, i.e., the set point chosen by the '
                             'diagnostic will never exceed this value '
                             '(inch w.g.)', value_default=0.25),
            'hdzone_damper_threshold':
            ConfigDescriptor(float,
                             'Threshold for zone damper. If the '
                             'average value of the zone dampers is less '
                             'than this threshold the fan is '
                             'supplying too much air (%)',
                             value_default=30.0),

            'setpoint_allowable_deviation':
            ConfigDescriptor(float,
                             'Allowable deviation from set points '
                             'before a fault message is generated '
                             '(%)', value_default=10.0),
            'stpr_reset_threshold':
            ConfigDescriptor(float,
                             ('Required difference between minimum and '
                              'maximum duct static pressure set point '
                              'detecting a duct static pressure '
                              'set point reset (inch w.g.)'),
                             value_default=0.25),
            'sensitivity':
                ConfigDescriptor(float,
                                 'Sensitivity: values can be 0.0 (low sensitivity), '
                                 '1.0 (normal sensitivity), 2.0 (high sensitivity) ',
                                 value_default=1.0)

            }

    @classmethod
    def get_self_descriptor(cls):
        name = 'Auto-RCx AHU: Static Pressure'
        desc = 'Auto-RCx AHU: Static Pressure'
        return Descriptor(name=name, description=desc)

    @classmethod
    def required_input(cls):
        '''
        Generate required inputs with description for
        user.
        '''
        return {
            cls.fan_status_name:
            InputDescriptor('SupplyFanStatus',
                            'AHU Supply fan status', count_min=1),
            cls.fan_speedcmd_name:
            InputDescriptor('SupplyFanSpeed',
                            'AHU supply fan speed', count_min=0),
            cls.zone_damper_name:
            InputDescriptor('TerminalBoxDamperCommand',
                            'All terminal-box damper commands', count_min=1),
            cls.duct_stp_name:
            InputDescriptor('DuctStaticPressure', 'AHU duct static pressure',
                            count_min=1),
            cls.duct_stp_stpt_name:
            InputDescriptor('DuctStaticPressureSetPoint',
                            'Duct static pressure set point',
                            count_min=1)
            }

    def reports(self):
        '''Called by UI to assemble information for creation of the diagnostic
        visualization.
        '''
        report = reports.Report('Retuning Report')
        # report.add_element(reports.RetroCommissioningOAED(
        #     table_name='Airside_RCx'))
        report.add_element(reports.RxStaticPressure(
            table_name='Airside_RCx'))
        return [report]

    @classmethod
    def output_format(cls, input_object):
        '''Describes how the output or results will be formatted
        Output will have the date-time, error-message, color-code,
        and energy impact.
        '''
        result = super().output_format(input_object)
        topics = input_object.get_topics()
        diagnostic_topic = topics[cls.fan_status_name][0]
        diagnostic_topic_parts = diagnostic_topic.split('/')
        output_topic_base = diagnostic_topic_parts[:-1]
        datetime_topic = '/'.join(output_topic_base + ['Airside_RCx',
                                                       'date'])
        message_topic = '/'.join(output_topic_base + ['Airside_RCx',
                                                      'message'])
        diagnostic_name = '/'.join(output_topic_base + ['Airside_RCx',
                                                        ' diagnostic_name'])
        energy_impact = '/'.join(output_topic_base + ['Airside_RCx',
                                                      'energy_impact'])
        color_code = '/'.join(output_topic_base + ['Airside_RCx',
                                                   'color_code'])

        output_needs = {
            'Airside_RCx': {
                'datetime': OutputDescriptor('string', datetime_topic),
                'diagnostic_name': OutputDescriptor('string', diagnostic_name),
                'diagnostic_message': OutputDescriptor('string',
                                                       message_topic),
                'energy_impact': OutputDescriptor('float', energy_impact),
                'color_code': OutputDescriptor('string', color_code)
                }
            }
        result.update(output_needs)
        return result

    def run(self, current_time, points):
        '''Check application pre-quisites and assemble analysis data set.
        Receives mapped data from the DrivenBaseClass.  Filters non-relevent
        data and assembles analysis data set for diagnostics.
        '''
        device_dict = {}
        diagnostic_result = Results()
        topics = self.inp.get_topics()
        diagnostic_topic = topics[self.fan_status_name][0]
        current_time = self.inp.localize_sensor_time(diagnostic_topic,
                                                     current_time)
        for key, value in points.items():
            device_dict[key.lower()] = value
        supply_fan_off = False
        fan_stat_data = []
        fan_stat_check = False
        for key, value in device_dict.items():
            if key.startswith(self.fan_status_name) and value is not None:
                fan_stat_check = True
                fan_stat_data.append(value)
                if not value:
                    self.warm_up_flag = True
                    Application.pre_requiste_messages.append(self.pre_msg1)
                    diagnostic_result = self.pre_message(diagnostic_result,
                                                         current_time)
                    supply_fan_off = True
        if not fan_stat_check and self.fan_speedcmd_name is not None:
            for key, value in device_dict.items():
                if (key.startswith(self.fan_speedcmd_name) and
                        value is not None):
                    fan_stat_check = True
                    if value < self.low_supply_fan_threshold:
                        self.warm_up_flag = True
                        Application.pre_requiste_messages.append(self.pre_msg1)
                        diagnostic_result = self.pre_message(diagnostic_result,
                                                             current_time)
                        return diagnostic_result
                    fan_stat_data.append(1)
                    supply_fan_off = False
        if not fan_stat_check:
            Application.pre_requiste_messages.append(self.pre_msg0)
            diagnostic_result = self.pre_message(diagnostic_result,
                                                 current_time)
            return diagnostic_result
        low_dx_condition = False
        high_dx_condition = False
        static_override_check = False


        for key, value in device_dict.items():
            if (self.fan_speedcmd_name is not None and
                    self.fan_speedcmd_name in key):
                if (value is not None and
                        value > self.high_supply_fan_threshold):
                    low_dx_condition = True
                elif (value is not None and
                      value < self.low_supply_fan_threshold):
                    high_dx_condition = True
            if self.fan_speedcmd_priority in key:
                if value == self.override_state:
                    static_override_check = True
            if self.duct_stp_stpt_priority in key:
                if value == self.override_state:
                    static_override_check = True

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

        if not stc_pr_data:
            Application.pre_requiste_messages.append(self.pre_msg2)
        if not stc_pr_sp_data:
            Application.pre_requiste_messages.append(self.pre_msg3)
        if not zone_damper_data:
            Application.pre_requiste_messages.append(self.pre_msg4)
        if not (stc_pr_data and zone_damper_data and stc_pr_sp_data):
            return diagnostic_result

        # diagnostic_result = self.sched_occ_dx.sched_rcx_alg(
        #     current_time, stc_pr_data, stc_pr_sp_data,
        #     sat_stpt_data, fan_stat_data, diagnostic_result)

        if supply_fan_off:
            return diagnostic_result

        if self.warm_up_flag:
            self.warm_up_flag = False
            self.warm_up_start = current_time
            diagnostic_result = self.pre_message(diagnostic_result,
                                                 current_time)
            return diagnostic_result

        time_check = datetime.timedelta(minutes=self.warm_up_time)
        if (self.warm_up_start is not None and
                (current_time - self.warm_up_start) < time_check):
            diagnostic_result = self.pre_message(diagnostic_result,
                                                 current_time)
            return diagnostic_result
        diagnostic_result = self.static_dx.duct_static(
            current_time, stc_pr_sp_data, stc_pr_data, zone_damper_data,
            static_override_check, low_dx_condition,
            high_dx_condition, diagnostic_result)


        return diagnostic_result

    def pre_message(self, result, current_time):
        '''Add meaningful output based to results table if analysis
        cannot be run.
        '''
        Application.pre_msg_time.append(current_time)
        pre_check = ((Application.pre_msg_time[-1] -
                      Application.pre_msg_time[0])
                     .total_seconds()/60)
        pre_check = pre_check if pre_check > 0.0 else 1.0
        if pre_check >= self.data_window:
            msg_lst = [self.pre_msg0, self.pre_msg1, self.pre_msg2,
                       self.pre_msg3, self.pre_msg4, self.pre_msg5,
                       self.pre_msg6, self.pre_msg7]
            for item in msg_lst:
                if (Application.pre_requiste_messages.count(item) >
                        (0.25) * len(Application.pre_msg_time)):
                    result.log(item, logging.DEBUG)
            Application.pre_requiste_messages = []
            Application.pre_msg_time = []
        return result


class DuctStaticRcx(object):
    '''Air-side HVAC Self-Correcting Diagnostic: Detect and correct
    duct static pressure problems.
    '''
    def __init__(self, data_window, no_required_data, auto_correctflag,
                 setpoint_allowable_deviation,
                 max_duct_stp_stpt, duct_stc_retuning,
                 zone_high_damper_threshold,
                 zone_low_damper_threshold,
                 hdzone_damper_threshold, min_duct_stp_stpt,
                 stpr_reset_threshold):
        self.zone_damper_values = []
        self.duct_stp_stpt_values = []
        self.duct_stp_values = []
        self.timestamp = []
        self.data_window = float(data_window)
        self.no_required_data = no_required_data
        self.setpoint_allowable_deviation = float(setpoint_allowable_deviation)
        self.max_duct_stp_stpt = float(max_duct_stp_stpt)
        self.duct_stc_retuning = float(duct_stc_retuning)
        self.zone_high_damper_threshold = float(zone_high_damper_threshold)
        self.zone_low_damper_threshold = float(zone_low_damper_threshold)
        self.setpoint_allowable_deviation = float(setpoint_allowable_deviation)
        self.auto_correctflag = auto_correctflag
        self.min_duct_stp_stpt = float(min_duct_stp_stpt)
        self.hdzone_damper_threshold = float(hdzone_damper_threshold)
        self.stpr_reset_threshold = float(stpr_reset_threshold)

    def duct_static(self, current_time, stc_pr_sp_data, stc_pr_data,
                    zone_dmpr_data, static_override_check, low_dx_condition,
                    high_dx_condition, diagnostic_result):
        '''Check duct static pressure RCx pre-requisites
        and assemble the duct static pressure analysis data set.
        '''
        if low_dx_condition:
            diagnostic_result.log(('The supply fan is running at '
                                   'nearly 100% of full speed, data '
                                   'corresponding to {timestamp} will not be '
                                   'used for diagnostic'.
                                   format(timestamp=str(current_time)),
                                   logging.DEBUG))
            return diagnostic_result
        if high_dx_condition:
            diagnostic_result.log(('The supply fan is running at '
                                   ' the minimum speed, data corresponding '
                                   'to {timestamp} will not be used for '
                                   'diagnostic'.
                                   format(timestamp=str(current_time)),
                                   logging.DEBUG))
            return diagnostic_result
        self.duct_stp_values.append(sum(stc_pr_data)/len(stc_pr_data))
        self.zone_damper_values.append(sum(zone_dmpr_data)/len(zone_dmpr_data))
        self.timestamp.append(current_time)

        self.duct_stp_stpt_values.append(
            sum(stc_pr_sp_data) / len(stc_pr_sp_data))
        elapsed_time = ((self.timestamp[-1] - self.timestamp[0])
                        .total_seconds()/60)
        elapsed_time = elapsed_time if elapsed_time > 0.0 else 1.0

        if (elapsed_time >= self.data_window and
                len(self.timestamp) >= self.no_required_data):
            avg_duct_stpr_stpt = (sum(
                self.duct_stp_stpt_values) / len(self.duct_stp_stpt_values))

            if avg_duct_stpr_stpt > 0 and avg_duct_stpr_stpt < 10.0:
                set_point_tracking = [abs(x - y) for
                                      x, y in zip(self.duct_stp_values,
                                                  self.duct_stp_stpt_values)]

                set_point_tracking = (sum(set_point_tracking) /
                                      (len(set_point_tracking)
                                       * avg_duct_stpr_stpt)*100)
                if set_point_tracking > self.setpoint_allowable_deviation:
                    diagnostic_message = ('The duct static '
                                          'pressure is deviating from its '
                                          'set point significantly.')
                    color_code = 'RED'
                    energy_impact = None
                    dx_table = {
                        'datetime': str(self.timestamp[-1]),
                        'diagnostic_name': DUCT_STC_RCx,
                        'diagnostic_message': diagnostic_message,
                        'energy_impact': energy_impact,
                        'color_code': color_code
                    }
                    diagnostic_result.insert_table_row('Airside_RCx', dx_table)
                    diagnostic_result.log(diagnostic_message, logging.INFO)

            diagnostic_result = self.no_static_pr_reset(diagnostic_result)
            diagnostic_result = self.low_ductstatic_pr(diagnostic_result,
                                                       static_override_check)
            diagnostic_result = self.high_ductstatic_pr(diagnostic_result,
                                                        static_override_check)

        return diagnostic_result

    def low_ductstatic_pr(self, result, static_override_check):
        '''Diagnostic to identify and correct low duct static pressure
        (correction by modifying duct static pressure set point).
        '''
        zone_damper_temp = self.zone_damper_values
        zone_damper_temp.sort(reverse=False)
        zone_damper_lowtemp = zone_damper_temp[
            :int(math.ceil(len(self.zone_damper_values)*0.5))
            if len(self.zone_damper_values) != 1 else 1]
        zone_damper_lowavg = (
            sum(zone_damper_lowtemp) / len(zone_damper_lowtemp))

        zone_damper_hightemp = (
            zone_damper_temp[
                int(math.ceil(len(self.zone_damper_values)*0.5)) - 1
                if len(self.zone_damper_values) != 1 else 0:])

        zone_damper_highavg = (
            sum(zone_damper_hightemp) / len(zone_damper_hightemp))
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
                    duct_stpr_stpt = (avg_duct_stpr_stpt +
                                      self.duct_stc_retuning)
                    if duct_stpr_stpt <= self.max_duct_stp_stpt:
                        result.command(
                            Application.duct_stp_stpt_cname, duct_stpr_stpt)
                        duct_stpr_stpt = '%s' % float('%.2g' % duct_stpr_stpt)
                        duct_stpr_stpt = str(duct_stpr_stpt)
                        duct_stpr_stpt = ''.join([duct_stpr_stpt,
                                                  ' in. w.g.'])
                        diagnostic_message = ('The duct static '
                                              'pressure was detected to be '
                                              'too low. The duct static '
                                              'pressure has been increased '
                                              'to: {val}'
                                              .format(val=duct_stpr_stpt))
                    else:
                        result.command(Application.duct_stp_stpt_cname,
                                       self.max_duct_stp_stpt)
                        duct_stpr_stpt = '%s' % float('%.2g' % self.max_duct_stp_stpt)
                        duct_stpr_stpt = str(duct_stpr_stpt)
                        duct_stpr_stpt = ''.join([duct_stpr_stpt,
                                                  ' in. w.g.'])
                        diagnostic_message = ('The duct static pressure set '
                                              'point is at the maximum '
                                              'value configured by the '
                                              'building operator: {val})'
                                              .format(val=duct_stpr_stpt))
                else:
                    diagnostic_message = ('The duct static pressure set '
                                          'point was detected to be too low '
                                          'but auto-correction '
                                          'is not enabled.')

            elif not static_override_check:
                diagnostic_message = ('The duct static pressure was '
                                      'detected to be too low.')
            else:
                diagnostic_message = ('The duct static pressure was '
                                      'detected to be too low but an operator '
                                      'override was detected. Auto-correction '
                                      'can not be performed when the static '
                                      'pressure set point or fan speed '
                                      'command is in override.')
        else:
            diagnostic_message = ('No re-tuning opportunity was '
                                  'detected during the low duct static '
                                  'pressure diagnostic.')
            color_code = 'GREEN'

        dx_table = {
            'datetime': str(self.timestamp[-1]),
            'diagnostic_name': DUCT_STC_RCx1,
            'diagnostic_message': diagnostic_message,
            'energy_impact': energy_impact,
            'color_code': color_code
        }

        result.insert_table_row('Airside_RCx', dx_table)
        result.log(diagnostic_message, logging.INFO)
        return result

    def high_ductstatic_pr(self, result, static_override_check):
        '''Diagnostic to identify and correct high duct static pressure
        (correction by modifying duct static pressure set point)
        '''
        zone_damper_temp = self.zone_damper_values
        zone_damper_temp.sort(reverse=True)
        zone_damper_temp = zone_damper_temp[
            :int(math.ceil(len(self.zone_damper_values)*0.5))
            if len(self.zone_damper_values) != 1 else 1]
        avg_zone_damper = sum(zone_damper_temp) / len(zone_damper_temp)
        energy_impact = None
        avg_duct_stpr_stpt = None
        if self.duct_stp_stpt_values:
            avg_duct_stpr_stpt = sum(
                self.duct_stp_stpt_values) / len(self.duct_stp_stpt_values)
        if avg_zone_damper <= self.hdzone_damper_threshold:
            color_code = 'RED'
            if avg_duct_stpr_stpt is not None and not static_override_check:
                if self.auto_correctflag:
                    duct_stpr_stpt = (avg_duct_stpr_stpt -
                                      self.duct_stc_retuning)
                    if duct_stpr_stpt >= self.min_duct_stp_stpt:
                        result.command(
                            Application.duct_stp_stpt_cname, duct_stpr_stpt)
                        duct_stpr_stpt = '%s' % float('%.2g' % duct_stpr_stpt)
                        duct_stpr_stpt = str(duct_stpr_stpt)
                        duct_stpr_stpt = ''.join([duct_stpr_stpt,
                                                  ' in. w.g.'])
                        diagnostic_message = ('The duct static '
                                              'pressure was detected to be '
                                              'too high. The duct static '
                                              'pressure set point has been '
                                              'reduced to: {val}'
                                              .format(val=duct_stpr_stpt))
                    else:
                        result.command(
                            Application.duct_stp_stpt_cname,
                            self.min_duct_stp_stpt)
                        duct_stpr_stpt = '%s' % float('%.2g' % self.min_duct_stp_stpt)
                        duct_stpr_stpt = str(duct_stpr_stpt)
                        duct_stpr_stpt = ''.join([duct_stpr_stpt,
                                                  ' in. w.g.'])
                        diagnostic_message = ('The duct static pressure set '
                                              'point is at the minimum value '
                                              'configured by the building '
                                              'operator: {val})'
                                              .format(val=duct_stpr_stpt))
                else:
                    diagnostic_message = ('Duct static pressure set '
                                          'point was detected to be too high '
                                          'but auto-correction '
                                          'is not enabled.')
            elif not static_override_check:
                diagnostic_message = ('The duct static pressure was '
                                      'detected to be too high.')
            else:
                diagnostic_message = ('The duct static pressure was '
                                      'detected to be too high but an '
                                      'operator override was detected. '
                                      'Auto-correction can not be performed '
                                      'when the static pressure set point '
                                      'or fan speed command is in override.')
        else:
            diagnostic_message = ('No re-tuning opportunity was '
                                  'detected during the low duct static '
                                  'pressure diagnostic.')
            color_code = 'GREEN'

        dx_table = {
            'datetime': str(self.timestamp[-1]),
            'diagnostic_name': DUCT_STC_RCx2,
            'diagnostic_message': diagnostic_message,
            'energy_impact': energy_impact,
            'color_code': color_code
        }

        result.insert_table_row('Airside_RCx', dx_table)
        result.log(diagnostic_message, logging.INFO)
        self.duct_stp_stpt_values = []
        self.duct_stp_values = []
        self.zone_damper_values = []
        self.timestamp = []
        return result

    def no_static_pr_reset(self, result):
        '''Auto-RCx  to detect whether a static pressure set point
        reset is implemented.
        '''
        if not self.duct_stp_stpt_values:
            return result
        stp_diff = (max(self.duct_stp_stpt_values) -
                    min(self.duct_stp_stpt_values))
        energy_impact = None

        if stp_diff < self.stpr_reset_threshold:
            diagnostic_message = ('No duct static pressure '
                                  'reset detected. A duct static '
                                  'pressure set point reset can save '
                                  'significant amounts of energy.')
            color_code = 'RED'
        else:
            diagnostic_message = 'No problem detected.'
            color_code = 'GREEN'

        dx_table = {
            'datetime': str(self.timestamp[-1]),
            'diagnostic_name': DUCT_STC_RCx3,
            'diagnostic_message': diagnostic_message,
            'energy_impact': energy_impact,
            'color_code': color_code
        }

        result.insert_table_row('Airside_RCx', dx_table)
        result.log(diagnostic_message, logging.INFO)
        return result

