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
from numpy import mean
import dateutil.tz
from datetime import timedelta as td, datetime
from copy import deepcopy
from dateutil.parser import parse
from openeis.applications import (DrivenApplicationBaseClass,
                                  OutputDescriptor,
                                  ConfigDescriptor,
                                  InputDescriptor,
                                  Results,
                                  Descriptor,
                                  reports)

available_tz = {1: 'US/Pacific', 2: 'US/Mountain', 3: 'US/Central', 4: 'US/Eastern'}
DUCT_STC_RCX = 'Duct Static Pressure Set Point Control Loop Dx'
DUCT_STC_RCX1 = 'Low Duct Static Pressure Dx'
DUCT_STC_RCX2 = 'High Duct Static Pressure Dx'
DUCT_STC_RCX3 = 'No Static Pressure Reset Dx'

SA_TEMP_RCX = 'Supply-air Temperature Set Point Control Loop Dx'
SA_TEMP_RCX1 = 'Low Supply-air Temperature Dx'
SA_TEMP_RCX2 = 'High Supply-air Temperature Dx'
SA_TEMP_RCX3 = 'No Supply-air Temperature Reset Dx'

SCHED_RCX = 'Operational Schedule Dx'
DX = '/diagnostic message'

STCPR_NAME = 'StcPr_ACCx_State'
SATEMP_NAME = 'Satemp_ACCx_State'
SCHED_NAME = 'Sched_ACCx_State'
ST = 'state'
DATA = '/data/'

CORRECT_STC_PR = 'suggested duct static pressure set point'
STCPR_VALIDATE = 'Duct Static Pressure ACCx'
STCPR_VAL_FILE_TOKEN = 'stcpr-rcx'
SATEMP_VAL_FILE_TOKEN = 'satemp-rcx'
RESET_VAL_FILE_TOKEN = 'reset-schedule'

STCPR_POINT_NAME = 'duct static pressure'
SAT_POINT_NAME = 'supply-air temperature'

SA_VALIDATE = 'Supply-air Temperature ACCx'

RESET_FILE_TOKEN = 'reset'
SCHEDULE_FILE_TOKEN = 'schedule'

"""Common functions used across multiple algorithms."""

def create_table_key(table_name, timestamp):
    return '&'.join([table_name, timestamp.isoformat()])

def check_date(current_time, timestamp_array):
    """Check current timestamp with previous timestamp
    to verify that there are no large missing data gaps.
    """
    if not timestamp_array:
        return False
    if current_time.date() != timestamp_array[-1].date():
        if (timestamp_array[-1].date() + td(days=1) != current_time.date() or
                (timestamp_array[-1].hour != 23 and current_time.hour == 0)):
            return True
        return False


def validation_builder(validate, dx_name, data_tag):
    data = {}
    for key, value in validate.items():
        tag = dx_name + data_tag + key
        data.update({tag: value})
    return data


def check_run_status(timestamp_array, current_time, no_required_data, minimum_diagnostic_time=None):
    """The diagnostics run at a regular interval (some minimum elapsed amount of time) and have a
       minimum data count requirement (each time series of data must contain some minimum number
       of points).
       ARGS:
            timestamp_array(list(datetime)): ordered array of timestamps associated with building
                data.
            no_required_data(integer):  The minimum number of measurements for each time series used
                in the analysis.
    """
    def minimum_data():
        if len(timestamp_array) < no_required_data:
            return None
        return True
    if minimum_diagnostic_time is not None:
        sampling_interval = (timestamp_array[-1] - timestamp_array[0])/len(timestamp_array)
        required_time = (timestamp_array[-1] - timestamp_array[0]) + sampling_interval
        if required_time >= minimum_diagnostic_time:
            return minimum_data()
        return False
    if timestamp_array and timestamp_array[-1].hour != current_time.hour:
        return minimum_data()
    return False


def setpoint_control_check(setpoint_array, point_array, allowable_deviation,
                           dx_name, dx_tag, token, token_offset):
    """Verify that point is tracking well with set point.
        ARGS:
            setpoint_array (list(floats):
    """
    average_setpoint = None
    setpoint_array = [float(pt) for pt in setpoint_array if pt != 0]
    if setpoint_array:
        average_setpoint = sum(setpoint_array)/len(setpoint_array)
        zipper = (setpoint_array, point_array)
        stpt_tracking = [abs(x - y) for x, y in zip(*zipper)]
        stpt_tracking = (sum(stpt_tracking)/len(stpt_tracking))/average_setpoint*100

        if stpt_tracking > allowable_deviation:
            # color_code = 'red'
            msg = ('{pt} is deviating significantly '
                   'from the {pt} set point.'.format(pt=token))
            dx_msg = 1.1 + token_offset
            dx_table = {dx_name + dx_tag: dx_msg}
        else:
            # color_code = 'green'
            msg = 'No problem detected.'
            dx_msg = 0.0 + token_offset
            dx_table = {dx_name + dx_tag: dx_msg}
    else:
        # color_code = 'grey'
        msg = ('{} set point data is not available. '
               'The Set Point Control Loop Diagnostic'
               'requires set point '
               'data.'.format(token))
        dx_msg = 2.2 + token_offset
        dx_table = {dx_name + dx_tag: dx_msg}
    return average_setpoint, dx_table


class Application(DrivenApplicationBaseClass):
    """
    Air-side HVAC Auto-Retuning Diagnostics
    for AHUs.
    Note:
        All configurable threshold have default threshold that work well with most equipment/configurations.
    Args:
        no_required_data (int): minimum number of measurements required for
            conclusive analysis.
        warm_up_time (int): Number of minutes after equipment startup prior
            to beginning data collection for analysis.
        duct_stcpr_retuning (float): Amount to increment or decrement the duct
            static pressure set point high/low duct static pressure set point
            problem is detected (assumed to be in inches water column (gauge)).
        max_duct_stcpr_stpt (float): Maximum value for the duct static pressure set
            point when applying auto-correction.
        high_sf_threshold (float): Auto-correction for low duct static pressure set point
            will not be effective if the supply fan for the AHU is operating at or near 100%
            of full speed. Auto-correction will not be applied if this condition exists.
        zone_high_damper_threshold (float):
        zone_low_damper_threshold (float):
        min_duct_stcpr_stpt (float): Minimum value for the duct static pressure set
            point when applying auto-correction.
        low_sf_threshold (float): Auto-correction for high duct static pressure set point
            will not be effective if the supply fan for the AHU is operating at or near its
            minimum SupplyFanSpeed. Auto-correction will not be applied if this condition exists.
            If the SupplyFanStatus is not available, the supply fan speed can be used
            to determine if the supply fan is operating. The supply fan will be considered
            ON when operating at speeds above the minimum SupplyFanSpeed.
        setpoint_allowable_deviation (float): Maximum acceptable deviation set point for the supply-air
            temperature and the duct static pressure (averaged over an analysis period, typically one hour).
        stcpr_reset_threshold (float):
        percent_reheat_threshold (float):
        rht_on_threshold (float):
        sat_reset_threshold (float):
        sat_high_damper_threshold (float):
        percent_damper_threshold (float):
        min_sat_stpt (float):
        sat_retuning (float):
        reheat_valve_threshold (float):
        max_sat_stpt (float):
    """
    fan_status_name = 'fan_status'
    zone_reheat_name = 'zone_reheat'
    zone_damper_name = 'zone_damper'
    fan_speedcmd_name = 'fan_speedcmd'
    duct_stp_name = 'duct_stp'
    sa_temp_name = 'sa_temp'
    sat_stpt_name = 'sat_stpt'
    duct_stp_stpt_name = 'duct_stp_stpt'

    def __init__(
            self, *args, data_window=1, no_required_data=10, warm_up_time=15,
            duct_stcpr_retuning=0.15, max_duct_stcpr_stpt=2.5, local_tz=1,
            high_sf_threshold=100.0, zone_high_damper_threshold=90.0,
            zone_low_damper_threshold=10.0, min_duct_stcpr_stpt=0.5,
            hdzone_damper_threshold=30.0, low_sf_threshold=20.0,
            setpoint_allowable_deviation=10.0, stcpr_reset_threshold=0.25,

            percent_reheat_threshold=25.0, rht_on_threshold=10.0,
            sat_reset_threshold=5.0, sat_high_damper_threshold=80.0,
            percent_damper_threshold=50.0, min_sat_stpt=50.0,
            sat_retuning=1.0, reheat_valve_threshold=50.0,
            max_sat_stpt=75.0,

            unocc_time_threshold=30.0, unocc_stp_threshold=0.2,
            monday_sch=['5:30', '18:30'], tuesday_sch=['5:30', '18:30'],
            wednesday_sch=['5:30', '18:30'], thursday_sch=['5:30', '18:30'],
            friday_sch=['5:30', '18:30'], saturday_sch=['0:00', '0:00'],
            sunday_sch=['0:00', '0:00'], auto_correct_flag=False,
            analysis_name='', **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.cur_tz = available_tz[local_tz]
        except:
            self.cur_tz = 'UTC'

        self.warm_up_start = None
        self.warm_up_flag = True
        analysis = analysis_name

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
            self.fansp_name = Application.fan_speedcmd_name.lower()
        else:
            self.fansp_name = None


        sat_stpt_cname = self.sat_stpt_name
        duct_stp_stpt_cname = self.duct_stp_stpt_name
        # Zone Parameters
        self.zone_damper_name = Application.zone_damper_name.lower()
        self.zone_reheat_name = Application.zone_reheat_name.lower()

        no_required_data = int(no_required_data)
        self.low_sf_threshold = float(low_sf_threshold)
        self.high_sf_threshold = float(high_sf_threshold)
        self.warm_up_time = int(warm_up_time)
        self.static_dx = (
            DuctStaticRcx(no_required_data, auto_correct_flag,
                          setpoint_allowable_deviation, max_duct_stcpr_stpt,
                          duct_stcpr_retuning, zone_high_damper_threshold,
                          zone_low_damper_threshold, hdzone_damper_threshold,
                          min_duct_stcpr_stpt, analysis, duct_stp_stpt_cname))
        self.sat_dx = (
            SupplyTempRcx(no_required_data, auto_correct_flag,
                           setpoint_allowable_deviation, rht_on_threshold,
                          sat_high_damper_threshold, percent_damper_threshold,
                          percent_reheat_threshold, min_sat_stpt, sat_retuning,
                           reheat_valve_threshold, max_sat_stpt, analysis, sat_stpt_cname))
        self.sched_occ_dx = (
             SchedResetRcx(unocc_time_threshold, unocc_stp_threshold,
                           monday_sch, tuesday_sch, wednesday_sch, thursday_sch,
                           friday_sch, saturday_sch, sunday_sch,
                           no_required_data, stcpr_reset_threshold,
                           sat_reset_threshold, analysis))

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
            'warm_up_time':
            ConfigDescriptor(int,
                             'When the system starts this much '
                             'time will be allowed to elapse before adding '
                             'using data for analysis (minutes)',
                             value_default=15),
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
            'max_duct_stcpr_stpt':
            ConfigDescriptor(float,
                             'Maximum duct static pressure set point '
                             'allowed, when auto-correction is '
                             'enabled, i.e., the set point chosen by the '
                             'diagnostic will never exceed this value '
                             '(inch w.g.)', value_default=2.5),
            'duct_stcpr_retuning':
            ConfigDescriptor(float,
                             ('Increment/decrement of static pressure '
                              'set point during auto-correction '
                              '(inch w.g.)'),
                             value_default=0.15),
            'min_duct_stcpr_stpt':
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
            'low_sf_threshold':
            ConfigDescriptor(float,
                             'Value above which the supply fan will be '
                             'considered at its minimum speed (%)',
                             value_default=20.0),
            'high_sf_threshold':
            ConfigDescriptor(float,
                             ('Value above which the supply fan will '
                              'be considered running at its maximum speed. '
                              'If fan is running at its '
                              'maximum speed (%)'),
                             value_default=95.0),
            'setpoint_allowable_deviation':
            ConfigDescriptor(float,
                             'Allowable deviation from set points '
                             'before a fault message is generated '
                             '(%)', value_default=10.0),
            'stcpr_reset_threshold':
            ConfigDescriptor(float,
                             ('Required difference between minimum and '
                              'maximum duct static pressure set point '
                              'detecting a duct static pressure '
                              'set point reset (inch w.g.)'),
                             value_default=0.25),
            'reheat_valve_threshold':
            ConfigDescriptor(float,
                             'Zone re-heat valve threshold for SAT '
                             'RCx, compared to average zone '
                             're-heat valve (%)',
                             value_default=50.0),
            'percent_reheat_threshold':
            ConfigDescriptor(float,
                             ('Threshold for average percent of zones '
                              'where terminal box re-heat is ON (%)'),
                             value_default=25.0),
            'max_sat_stpt':
            ConfigDescriptor(float,
                             'Maximum SAT set point allowed when '
                             'auto-correction  is enabled, '
                             'i.e., the set point chosen by the '
                             'diagnostic will never exceed '
                             'this value ({drg}F)'
                             .format(drg=dgr_sym),
                             value_default=75.0),
            'rht_on_threshold':
            ConfigDescriptor(float,
                             'Value above which zone re-heat is '
                             'considered ON (%)',
                             value_default=10.0),
            'sat_retuning':
            ConfigDescriptor(float,
                             'Decrement of supply-air temperature set '
                             'point during auto-correction ({drg}F)'
                             .format(drg=dgr_sym),
                             value_default=1.0),
            'sat_high_damper_threshold':
            ConfigDescriptor(float,
                             'High zone damper threshold for '
                             'high supply-air temperature '
                             'auto-correct RCx (%)',
                             value_default=30),
            'percent_damper_threshold':
            ConfigDescriptor(float,
                             'Threshold for the average % of zone '
                             'dampers above high damper threshold '
                             '(%)',
                             value_default=50.0),
            'min_sat_stpt':
            ConfigDescriptor(float,
                             'Maximum supply-air temperature '
                             'set point allowed, when auto-correction '
                             'is enabled, i.e., '
                             'the set point chosen by the '
                             'diagnostic will never exceed this value '
                             '({drg}F)'.format(drg=dgr_sym),
                             value_default=50.0),
            'sat_reset_threshold':
            ConfigDescriptor(float,
                             'Threshold difference required '
                             'to detect a supply-air temperature '
                             'set point reset ({drg}F)'.format(drg=dgr_sym),
                             value_default=3.0),

            'unocc_time_threshold':
            ConfigDescriptor(float,
                             'Time threshold used for AHU schedule Dx. '
                             '(%)', value_default=30.0),
            'unocc_stp_threshold':
            ConfigDescriptor(float,
                             'AHU off static pressure dead-band '
                             'Detects whether the duct static '
                             'pressure exceeds this '
                             'value during non-working scheduled '
                             'hours (inch w.g.)',
                             value_default=0.2),
            'monday_sch':
            ConfigDescriptor(str,
                             'Thursday AHU occupied schedule, '
                             'Used to detect the '
                             'time when the supply fan should '
                             'be operational)',
                             value_default=['6:30','18:30']),
            'tuesday_sch':
            ConfigDescriptor(str,
                             'Tuesday AHU occupied schedule, '
                             'Used to detect the '
                             'time when the supply fan should '
                             'be operational',
                             value_default=['6:30','18:30']),
            'wednesday_sch':
            ConfigDescriptor(str,
                             'Wednesday AHU occupied schedule, '
                             'Used to detect the '
                             'time when the supply fan should '
                             'be operational',
                             value_default=['6:30','18:30']),
            'thursday_sch':
            ConfigDescriptor(str,
                             'Thursday AHU occupied schedule, '
                             'Used to detect the '
                             'time when the supply fan should '
                             'be operational',
                             value_default=['6:30','18:30']),
            'friday_sch':
            ConfigDescriptor(str,
                             'Friday AHU occupied schedule, '
                             'Used to detect the '
                             'time when the supply fan should '
                             'be operational',
                             value_default=['6:30','18:30']),
            'saturday_sch':
            ConfigDescriptor(str,
                             'Saturday AHU occupied schedule, '
                             'Used to detect the '
                             'time when the supply fan should '
                             'be operational (unoccupied)',
                             value_default=['0:00','0:00']),
            'sunday_sch':
            ConfigDescriptor(str,
                             'Sunday AHU occupied schedule, '
                             'Used to detect the '
                             'time when the supply fan should '
                             'be operational (unoccupied)',
                             value_default=['0:00','0:00']),
            'local_tz':
            ConfigDescriptor(int,
                             "Integer corresponding to local timezone: [1: 'US/Pacific', 2: 'US/Mountain', 3: 'US/Central', 4: 'US/Eastern']",
                             value_default=1)
            }

    @classmethod
    def get_self_descriptor(cls):
        name = 'Auto-RCx for Air Handling HVAC Systems'
        desc = 'Automated Retro-commisioning for AHUs'
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
            cls.zone_reheat_name:
            InputDescriptor('TerminalBoxReheatValvePosition',
                            'All terminal-box re-heat valve commands',
                            count_min=1),
            cls.zone_damper_name:
            InputDescriptor('TerminalBoxDamperCommand',
                            'All terminal-box damper commands', count_min=1),
            cls.duct_stp_name:
            InputDescriptor('DuctStaticPressure', 'AHU duct static pressure',
                            count_min=1),
            cls.duct_stp_stpt_name:
            InputDescriptor('DuctStaticPressureSetPoint',
                            'Duct static pressure set point',
                            count_min=1),
            cls.sa_temp_name:
            InputDescriptor('DischargeAirTemperature', 'AHU supply-air '
                            '(discharge-air) temperature', count_min=1),
            cls.sat_stpt_name:
            InputDescriptor('DischargeAirTemperatureSetPoint',
                            'Supply-air temperature set-point', count_min=1)
            }

    def reports(self):
        '''Called by UI to assemble information for creation of the diagnostic
        visualization.
        '''
        report = reports.Report('Retuning Report')
        report.add_element(reports.RetroCommissioningOAED(
            table_name='Airside_RCx'))
        report.add_element(reports.RetroCommissioningAFDD(
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
        # topics = self.inp.get_topics()
        # diagnostic_topic = topics[self.fan_status_name][0]
        # cur_time = self.inp.localize_sensor_time(diagnostic_topic, current_time)
        # validate_topic = create_table_key('validate', cur_time)
        # validate_data = {SATEMP_NAME: 0, STCPR_NAME: 0, SCHED_NAME: 0}
        to_zone = dateutil.tz.gettz(self.cur_tz)
        cur_time = current_time.astimezone(to_zone)

        try:
            device_dict = {}
            diagnostic_result = Results()
            fan_status_data = []
            supply_fan_off = False
            low_dx_cond = False
            high_dx_cond = False

            for key, value in points.items():
                point_device = [_name.lower() for _name in key.split('&&&')]
                if point_device[0] not in device_dict:
                    device_dict[point_device[0]] = [(point_device[1], value)]
                else:
                    device_dict[point_device[0]].append((point_device[1], value))

            if self.fan_status_name in device_dict:
                fan_status = device_dict[self.fan_status_name]
                fan_status = [point[1] for point in fan_status]
                fan_status = [status for status in fan_status if status is not None]
                if fan_status:
                    fan_status_data.append(min(fan_status))
                    if not int(fan_status_data[0]):
                        supply_fan_off = True
                        self.warm_up_flag = True

            if self.fansp_name in device_dict:
                fan_speed = device_dict[self.fansp_name]
                fan_speed = mean([point[1] for point in fan_speed])
                if self.fan_status_name is None:
                    if not int(fan_speed):
                        supply_fan_off = True
                        self.warm_up_flag = True
                    fan_status_data.append(bool(int(fan_speed)))

                if fan_speed > self.high_sf_threshold:
                    low_dx_cond = True
                elif fan_speed < self.low_sf_threshold:
                    high_dx_cond = True

            stc_pr_data = []
            stcpr_sp_data = []
            zn_dmpr_data = []
            satemp_data = []
            rht_data = []
            sat_stpt_data = []
            # validate = {}
            # sched_val = {}

            def data_builder(value_tuple, point_name):
                value_list = []
                for item in value_tuple:
                    value_list.append(item[1])
                return value_list

            for key, value in device_dict.items():
                data_name = key
                if value is None:
                    continue
                if data_name == self.duct_stp_stpt_name:
                    stcpr_sp_data = data_builder(value, data_name)
                elif data_name == self.sat_stpt_name:
                    sat_stpt_data = data_builder(value, data_name)
                elif data_name == self.duct_stp_name:
                    stc_pr_data = data_builder(value, data_name)
                elif data_name == self.sa_temp_name:
                    satemp_data = data_builder(value, data_name)
                elif data_name == self.zone_reheat_name:
                    rht_data = data_builder(value, data_name)
                elif data_name == self.zone_damper_name:
                    zn_dmpr_data = data_builder(value, data_name)

            missing_data = []
            if not satemp_data:
                missing_data.append(self.sa_temp_name)
            if not rht_data:
                missing_data.append(self.zone_reheat_name)
            if not sat_stpt_data:
                diagnostic_result.log('Supply-air temperature set point data is '
                                      'missing. This will limit the effectiveness of '
                                      'the supply-air temperature diagnostics.')
            if not stc_pr_data:
                missing_data.append(self.duct_stp_name)
            if not stcpr_sp_data:
                diagnostic_result.log('Duct static pressure set point data is '
                                      'missing. This will limit the effectiveness of '
                                      'the duct static pressure diagnostics.')
            if not zn_dmpr_data:
                missing_data.append(self.zone_damper_name)
            if not fan_status:
                missing_data.append(self.fan_status_name)
            if missing_data:
                raise Exception('Missing required data: {}'.format(missing_data))
                return diagnostic_result
            dx_status, diagnostic_result = (
                self.sched_occ_dx.sched_rcx_alg(cur_time, stc_pr_data,
                                                stcpr_sp_data, sat_stpt_data,
                                               fan_status, diagnostic_result))
            # validate_data.update({SCHED_NAME: dx_status})

            if supply_fan_off:
                diagnostic_result.log('Supply fan is off. Data will not be used for '
                              'retuning diagnostics.')
                return diagnostic_result
            if self.warm_up_flag:
                self.warm_up_flag = False
                self.warm_up_start = cur_time
                return diagnostic_result
            time_check = td(minutes=self.warm_up_time)
            if self.warm_up_start is not None and (cur_time - self.warm_up_start) < time_check:
                diagnostic_result.log('Unit may be in warm-up. Data will not be analyzed.')
                return diagnostic_result
            dx_status, diagnostic_result = self.static_dx.duct_static(cur_time, stcpr_sp_data, stc_pr_data,
                                                              zn_dmpr_data, low_dx_cond, high_dx_cond, diagnostic_result)
            # validate_data.update({STCPR_NAME: dx_status})
            dx_status, diagnostic_result = self.sat_dx.sat_rcx(cur_time, satemp_data, sat_stpt_data, rht_data, zn_dmpr_data,
                                                               diagnostic_result)
            # validate_data.update({SATEMP_NAME: dx_status})
            return diagnostic_result
        finally:
            pass
            # diagnostic_result.insert_table_row(validate_topic, validate_data)


class DuctStaticRcx(object):
    """Air-side HVAC Self-Correcting Diagnostic: Detect and correct
    duct static pressure problems.
    """
    def __init__(self, no_req_data, auto_correct_flag, stpt_allowable_dev,
                 max_stcpr_stpt, stcpr_retuning, zone_high_dmpr_threshold,
                 zone_low_dmpr_threshold, hdzn_dmpr_thr, min_stcpr_stpt,
                 analysis, stcpr_stpt_cname):
        # Initialize data arrays
        self.table_key = None
        self.file_key = None
        self.zn_dmpr_arr = []
        self.stcpr_stpt_arr = []
        self.stcpr_arr = []
        self.timestamp_arr = []
        self.data = {}
        self.dx_table = {}

        # Initialize configurable thresholds
        self.analysis = analysis + '-' + STCPR_VAL_FILE_TOKEN
        self.file_name_id = analysis + '-' + STCPR_VAL_FILE_TOKEN
        self.stcpr_stpt_cname = stcpr_stpt_cname
        self.no_req_data = no_req_data
        self.stpt_allowable_dev = float(stpt_allowable_dev)
        self.max_stcpr_stpt = float(max_stcpr_stpt)
        self.stcpr_retuning = float(stcpr_retuning)
        self.zone_high_dmpr_threshold = float(zone_high_dmpr_threshold)
        self.zone_low_dmpr_threshold = float(zone_low_dmpr_threshold)
        self.sp_allowable_dev = float(stpt_allowable_dev)
        self.auto_correct_flag = auto_correct_flag
        self.min_stcpr_stpt = float(min_stcpr_stpt)
        self.hdzn_dmpr_thr = float(hdzn_dmpr_thr)
        self.token_offset = 0.0

        self.low_msg = ('The supply fan is running at nearly 100% of full '
                        'speed, data corresponding to {} will not be used.')
        self.high_msg = ('The supply fan is running at the minimum speed, '
                         'data corresponding to {} will not be used.')

    def reinitialize(self):
        """Reinitialize data arrays"""
        self.table_key = None
        self.file_key = None
        self.zn_dmpr_arr = []
        self.stcpr_stpt_arr = []
        self.stcpr_arr = []
        self.timestamp_arr = []
        self.data = {}
        self.dx_table = {}

    def duct_static(self, current_time, stcpr_stpt_data, stcpr_data,
                    zn_dmpr_data, low_dx_cond, high_dx_cond, dx_result):
        """Check duct static pressure RCx pre-requisites and assemble the
        duct static pressure analysis data set.
        """
        dx_status = 0
        if check_date(current_time, self.timestamp_arr):
            dx_status = 0
            self.reinitialize()
            return dx_status, dx_result

        if low_dx_cond:
            dx_result.log(self.low_msg.format(current_time), logging.DEBUG)
            return dx_status, dx_result
        if high_dx_cond:
            dx_result.log(self.high_msg.format(current_time), logging.DEBUG)
            return dx_status, dx_result

        run_status = check_run_status(self.timestamp_arr, current_time, self.no_req_data)

        if run_status is None:
            dx_result.log('{}: Current analysis data set has insufficient data '
                          'to produce a valid diagnostic result.'.format(STCPR_VALIDATE, logging.DEBUG))
            self.reinitialize()
            return dx_status, dx_result
        dx_status = 1
        if run_status:
            self.table_key = create_table_key(self.analysis, self.timestamp_arr[-1])
            avg_stcpr_stpt, dx_table = setpoint_control_check(self.stcpr_stpt_arr,
                                                              self.stcpr_arr,
                                                              self.stpt_allowable_dev,
                                                              DUCT_STC_RCX, DX,
                                                              STCPR_POINT_NAME, self.token_offset)

            self.dx_table.update(dx_table)
            dx_result = self.low_stcpr_dx(dx_result, avg_stcpr_stpt)
            dx_result = self.high_stcpr_dx(dx_result, avg_stcpr_stpt)
            #dx_result.insert_table_row(self.table_key, self.dx_table)
            dx_result.log('{}: Running diagnostics.'.format(STCPR_VALIDATE, logging.DEBUG))
            dx_status = 2
            self.reinitialize()
        dx_result.log('{}: Collecting and aggregating data.'.format(STCPR_VALIDATE, logging.DEBUG))
        self.stcpr_stpt_arr.append(mean(stcpr_data))
        self.stcpr_arr.append(mean(stcpr_stpt_data))
        self.zn_dmpr_arr.append(mean(zn_dmpr_data))
        self.timestamp_arr.append(current_time)

        return dx_status, dx_result

    def low_stcpr_dx(self, dx_result, avg_stcpr_stpt):
        """Diagnostic to identify and correct low duct static pressure
        (correction by modifying duct static pressure set point).
        """
        zn_dmpr = deepcopy(self.zn_dmpr_arr)
        zn_dmpr.sort(reverse=False)
        zone_dmpr_lowtemp = zn_dmpr[:int(math.ceil(len(self.zn_dmpr_arr)*0.5)) if len(self.zn_dmpr_arr) != 1 else 1]
        zn_dmpr_low_avg = mean(zone_dmpr_lowtemp)

        zone_dmpr_hightemp = zn_dmpr[int(math.ceil(len(self.zn_dmpr_arr)*0.5)) - 1 if len(self.zn_dmpr_arr) != 1 else 0:]
        zn_dmpr_high_avg = mean(zone_dmpr_hightemp)
        if zn_dmpr_high_avg > self.zone_high_dmpr_threshold and zn_dmpr_low_avg > self.zone_low_dmpr_threshold:
            color_code = 'RED'
            if avg_stcpr_stpt is None:
                # Create diagnostic message for fault
                # when duct static pressure set point
                # is not available.
                msg = ('{}: The duct static pressure set point has been '
                       'detected to be too low but but supply-air'
                       'temperature set point data is not available.'.format(DUCT_STC_RCX1))
                dx_msg = 14.1
            elif self.auto_correct_flag:
                auto_correct_stcpr_stpt = avg_stcpr_stpt + self.stcpr_retuning
                if auto_correct_stcpr_stpt <= self.max_stcpr_stpt:
                    dx_result.command(self.stcpr_stpt_cname, auto_correct_stcpr_stpt)
                    new_stcpr_stpt = '%s' % float('%.2g' % auto_correct_stcpr_stpt)
                    new_stcpr_stpt = new_stcpr_stpt + ' in. w.g.'
                    msg = ('{}: The duct static pressure was detected to be '
                           'too low. The duct static pressure has been '
                           'increased to: {}'
                           .format(DUCT_STC_RCX1, new_stcpr_stpt))
                    dx_msg = 11.1
                else:
                    dx_result.command(self.stcpr_stpt_cname, self.max_stcpr_stpt)
                    new_stcpr_stpt = '%s' % float('%.2g' % self.max_stcpr_stpt)
                    new_stcpr_stpt = new_stcpr_stpt + ' in. w.g.'
                    msg = ('{}: The duct static pressure set point is at the '
                           'maximum value configured by the building operator: {}'
                           .format(DUCT_STC_RCX1, new_stcpr_stpt))
                    dx_msg = 12.1
            else:
                msg = ('{}: The duct static pressure set point was detected '
                       'to be too low but auto-correction is not enabled.'.format(DUCT_STC_RCX1))
                dx_msg = 13.1
        else:
            msg = ('{}: No re-tuning opportunity was detected during the low duct '
                   'static pressure diagnostic.'.format(DUCT_STC_RCX1))
            color_code = 'GREEN'
            dx_msg = 10.0

        dx_table = {
            'datetime': str(self.timestamp_arr[-1]),
            'diagnostic_name': DUCT_STC_RCX1,
            'diagnostic_message': msg,
            'energy_impact': None,
            'color_code': color_code
        }

        dx_result.insert_table_row('Airside_RCx', dx_table)
        dx_result.log(msg, logging.INFO)
        return dx_result

    def high_stcpr_dx(self, dx_result, avg_stcpr_stpt):
        """Diagnostic to identify and correct high duct static pressure
        (correction by modifying duct static pressure set point)
        """
        zn_dmpr = deepcopy(self.zn_dmpr_arr)
        zn_dmpr.sort(reverse=True)
        zn_dmpr = zn_dmpr[:int(math.ceil(len(self.zn_dmpr_arr)*0.5))if len(self.zn_dmpr_arr) != 1 else 1]
        avg_zone_damper = mean(zn_dmpr)

        if avg_zone_damper <= self.hdzn_dmpr_thr:
            color_code = 'RED'
            if avg_stcpr_stpt is None:
                # Create diagnostic message for fault
                # when duct static pressure set point
                # is not available.
                msg = ('{}: The duct static pressure set point has been '
                       'detected to be too high but but duct static '
                       'pressure set point data is not available.'
                       'temperature set point data is not available.'.format(DUCT_STC_RCX2))
                dx_msg = 24.1
            elif self.auto_correct_flag:
                auto_correct_stcpr_stpt = avg_stcpr_stpt - self.stcpr_retuning
                if auto_correct_stcpr_stpt >= self.min_stcpr_stpt:
                    dx_result.command(self.stcpr_stpt_cname, auto_correct_stcpr_stpt)
                    new_stcpr_stpt = '%s' % float('%.2g' % auto_correct_stcpr_stpt)
                    new_stcpr_stpt = new_stcpr_stpt + ' in. w.g.'
                    msg = ('{}: The duct static pressure was detected to be '
                           'too high. The duct static pressure set point '
                           'has been reduced to: {}'.format(DUCT_STC_RCX2, new_stcpr_stpt))
                    dx_msg = 21.1
                else:
                    dx_result.command(self.stcpr_stpt_cname, self.min_stcpr_stpt)
                    new_stcpr_stpt = '%s' % float('%.2g' % self.min_stcpr_stpt)
                    new_stcpr_stpt = new_stcpr_stpt + ' in. w.g.'
                    msg = ('{}: The duct static pressure set point is at the '
                           'minimum value configured by the building '
                           'operator: {})'.format(DUCT_STC_RCX2, new_stcpr_stpt))
                    dx_msg = 22.1
            else:
                msg = ('{}: Duct static pressure set point was detected to be '
                       'too high but auto-correction is not enabled.'.format(DUCT_STC_RCX2))
                dx_msg = 23.1
        else:
            msg = ('{}: No re-tuning opportunity was detected during the high duct '
                   'static pressure diagnostic.'.format(DUCT_STC_RCX2))
            color_code = 'GREEN'
            dx_msg = 20.0

        dx_table = {
            'datetime': str(self.timestamp_arr[-1]),
            'diagnostic_name': DUCT_STC_RCX2,
            'diagnostic_message': msg,
            'energy_impact': None,
            'color_code': color_code
        }

        dx_result.insert_table_row('Airside_RCx', dx_table)
        dx_result.log(msg, logging.INFO)
        return dx_result


class SupplyTempRcx(object):
    """Air-side HVAC Self-Correcting Diagnostic: Detect and correct supply-air
    temperature problems.
    Args:
        timestamp_arr (List[datetime]): timestamps for analysis period.
        sat_stpt_arr (List[float]): supply-air temperature set point
            for analysis period.
        satemp_arr (List[float]): supply-air temperature for analysis period.
        rht_arr (List[float]): terminal box reheat command for analysis period.
    """
    def __init__(self, no_req_data, auto_correct_flag, stpt_allowable_dev,
                 rht_on_thr, high_dmpr_thr, percent_dmpr_thr, percent_rht_thr,
                 min_sat_stpt, sat_retuning, rht_valve_thr, max_sat_stpt,
                 analysis, sat_stpt_cname):
        self.timestamp_arr = []
        self.sat_stpt_arr = []
        self.satemp_arr = []
        self.rht_arr = []
        self.percent_rht = []
        self.percent_dmpr = []
        self.table_key = None
        self.file_key = None
        self.data = {}
        self.dx_table = {}

        # Common RCx parameters
        self.analysis = analysis + '-' + SATEMP_VAL_FILE_TOKEN
        self.sat_stpt_cname = sat_stpt_cname
        self.no_req_data = no_req_data
        self.auto_correct_flag = bool(auto_correct_flag)
        self.stpt_allowable_dev = float(stpt_allowable_dev)
        self.rht_on_thr = float(rht_on_thr)
        self.percent_rht_thr = float(percent_rht_thr)
        self.dgr_sym = u'\N{DEGREE SIGN}'

        # Low SAT RCx thresholds
        self.rht_valve_thr = float(rht_valve_thr)
        self.max_sat_stpt = float(max_sat_stpt)

        # High SAT RCx thresholds
        self.high_dmpr_thr = float(high_dmpr_thr)
        self.percent_dmpr_thr = float(percent_dmpr_thr)
        self.min_sat_stpt = float(min_sat_stpt)
        self.sat_retuning = float(sat_retuning)
        self.token_offset = 30.0

    def reinitialize(self):
        """Reinitialize data arrays."""
        self.table_key = None
        self.file_key = None
        self.timestamp_arr = []
        self.sat_stpt_arr = []
        self.satemp_arr = []
        self.rht_arr = []
        self.percent_rht = []
        self.percent_dmpr = []
        self.data = {}
        self.dx_table = {}

    def sat_rcx(self, current_time, sat_data, sat_stpt_data,
                zone_rht_data, zone_dmpr_data, dx_result):
        """Manages supply-air diagnostic data sets.
        Args:
            current_time (datetime): current timestamp for trend data.
            sat_data (lst of floats): supply-air temperature measurement for
                AHU.
            sat_stpt_data (List[floats]): supply-air temperature set point
                data for AHU.
            zone_rht_data (List[floats]): reheat command for terminal boxes
                served by AHU.
            zone_dmpr_data (List[floats]): damper command for terminal boxes
                served by AHU.
            dx_result (Object): Object for interacting with platform and devices.
        Returns:
            Results object (dx_result) to Application.
            Status of diagnostic (dx_status)
        """
        dx_status = 1
        if check_date(current_time, self.timestamp_arr):
            self.reinitialize()
            dx_status = 0
            return dx_status, dx_result

        tot_rht = sum(1 if val > self.rht_on_thr else 0 for val in zone_rht_data)
        count_rht = len(zone_rht_data)
        tot_dmpr = sum(1 if val > self.high_dmpr_thr else 0 for val in zone_dmpr_data)
        count_damper = len(zone_dmpr_data)

        run_status = check_run_status(self.timestamp_arr, current_time, self.no_req_data)

        if run_status is None:
            dx_result.log('{}: Current analysis data set has insufficient data '
                          'to produce a valid diagnostic result.'.format(SA_VALIDATE, logging.DEBUG))
            self.reinitialize()
            dx_status = 0
            return dx_status, dx_result

        if run_status:
            self.table_key = create_table_key(self.analysis, self.timestamp_arr[-1])
            avg_sat_stpt, dx_table = setpoint_control_check(self.sat_stpt_arr,
                                                            self.satemp_arr,
                                                            self.stpt_allowable_dev,
                                                            SA_TEMP_RCX,
                                                            DX, SAT_POINT_NAME,
                                                            self.token_offset)
            self.dx_table.update(dx_table)
            dx_result = self.low_sat(dx_result, avg_sat_stpt)
            dx_result = self.high_sat(dx_result, avg_sat_stpt)
            #dx_result.insert_table_row(self.table_key, self.dx_table)
            dx_result.log('{}: Running diagnostics.'.format(SA_VALIDATE, logging.DEBUG))
            dx_status = 2
            self.reinitialize()
        dx_result.log('{}: Collecting and aggregating data.'.format(SA_VALIDATE, logging.DEBUG))
        self.satemp_arr.append(mean(sat_data))
        self.rht_arr.append(mean(zone_rht_data))
        self.sat_stpt_arr.append(mean(sat_stpt_data))
        self.percent_rht.append(tot_rht/count_rht)
        self.percent_dmpr.append(tot_dmpr/count_damper)
        self.timestamp_arr.append(current_time)

        return dx_status, dx_result

    def low_sat(self, dx_result, avg_sat_stpt):
        """Diagnostic to identify and correct low supply-air temperature
        (correction by modifying SAT set point)
        """
        avg_zones_rht = mean(self.percent_rht)*100
        rht_avg = mean(self.rht_arr)
        if rht_avg > self.rht_valve_thr and avg_zones_rht > self.percent_rht_thr:
            color_code = 'RED'
            if avg_sat_stpt is None:
                # Create diagnostic message for fault
                # when supply-air temperature set point
                # is not available.
                msg = ('{}: The SAT has been detected to be too low but '
                       'but supply-air temperature set point data '
                       'is not available.'.format(SA_TEMP_RCX1))
                dx_msg = 43.1
            elif self.auto_correct_flag:
                autocorrect_sat_stpt = avg_sat_stpt + self.sat_retuning
                if autocorrect_sat_stpt <= self.max_sat_stpt:
                    dx_result.command(self.sat_stpt_cname, autocorrect_sat_stpt)
                    sat_stpt = '%s' % float('%.2g' % autocorrect_sat_stpt)
                    msg = ('{}: The SAT has been detected to be too low. '
                           'The SAT set point has been increased to: '
                           '{}{}F'.format(SA_TEMP_RCX1, self.dgr_sym, sat_stpt))
                    dx_msg = 41.1
                else:
                    dx_result.command(self.sat_stpt_cname, self.max_sat_stpt)
                    sat_stpt = '%s' % float('%.2g' % self.max_sat_stpt)
                    sat_stpt = str(sat_stpt)
                    msg = (
                        '{}: The supply-air temperautre was detected to be '
                        'too low. Auto-correction has increased the '
                        'supply-air temperature set point to the maximum '
                        'configured supply-air tempeature set point: '
                        '{}{}F)'.format(SA_TEMP_RCX1, self.dgr_sym, sat_stpt))
                    dx_msg = 42.1
            else:
                msg = ('{}: The SAT has been detected to be too low but'
                       'auto-correction is not enabled.'.format(SA_TEMP_RCX1))
                dx_msg = 44.1
        else:
            msg = ('{}: No problem detected.')
            color_code = 'GREEN'
            dx_msg = 40.0

        dx_table = {
            'datetime': str(self.timestamp_arr[-1]),
            'diagnostic_name': SA_TEMP_RCX1,
            'diagnostic_message': msg,
            'energy_impact': None,
            'color_code': color_code
        }
        dx_result.insert_table_row('Airside_RCx', dx_table)
        dx_result.log(msg, logging.INFO)
        return dx_result

    def high_sat(self, dx_result, avg_sat_stpt):
        """Diagnostic to identify and correct high supply-air temperature
        (correction by modifying SAT set point)
        """
        avg_zones_rht = mean(self.percent_rht)*100
        avg_zone_dmpr_data = mean(self.percent_dmpr)*100

        if avg_zone_dmpr_data > self.percent_dmpr_thr and avg_zones_rht < self.percent_rht_thr:
            color_code = 'RED'
            if avg_sat_stpt is None:
                # Create diagnostic message for fault
                # when supply-air temperature set point
                # is not available.
                msg = ('{}: The SAT has been detected to be too high but '
                       'but supply-air temperature set point data '
                       'is not available.'.format(SA_TEMP_RCX2))
                dx_msg = 54.1
            elif self.auto_correct_flag:
                autocorrect_sat_stpt = avg_sat_stpt - self.sat_retuning
                # Create diagnostic message for fault condition
                # with auto-correction
                if autocorrect_sat_stpt >= self.min_sat_stpt:
                    dx_result.command(self.sat_stpt_cname, autocorrect_sat_stpt)
                    sat_stpt = '%s' % float('%.2g' % autocorrect_sat_stpt)
                    msg = ('{}: The SAT has been detected to be too high. The '
                           'SAT set point has been increased to: '
                           '{}{}F'.format(SA_TEMP_RCX2, self.dgr_sym, sat_stpt))
                    dx_msg = 51.1
                else:
                    # Create diagnostic message for fault condition
                    # where the maximum SAT has been reached
                    dx_result.command(self.sat_stpt_cname, self.min_sat_stpt)
                    sat_stpt = '%s' % float('%.2g' % self.min_sat_stpt)
                    msg = ('{}: The SAT was detected to be too high, '
                           'auto-correction has increased the SAT to the '
                           'minimum configured SAT: {}{}F'
                           .format(SA_TEMP_RCX2, self.dgr_sym, sat_stpt))
                    dx_msg = 52.1
            else:
                # Create diagnostic message for fault condition
                # without auto-correction
                msg = ('{}: The SAT has been detected to be too high but '
                       'auto-correction is not enabled.'.format(SA_TEMP_RCX2))
                dx_msg = 53.1
        else:
            msg = ('{}: No problem detected for High Supply-air '
                   'Temperature diagnostic.'.format(SA_TEMP_RCX2))
            color_code = 'GREEN'
            dx_msg = 50.0

        dx_table = {
            'datetime': str(self.timestamp_arr[-1]),
            'diagnostic_name': SA_TEMP_RCX2,
            'diagnostic_message': msg,
            'energy_impact': None,
            'color_code': color_code
        }
        dx_result.insert_table_row('Airside_RCx', dx_table)
        dx_result.log(msg, logging.INFO)
        return dx_result

class SchedResetRcx(object):
    """Schedule, supply-air temperature, and duct static pressure auto-detect
    diagnostics for AHUs or RTUs.
    """

    def __init__(self, unocc_time_threshold, unocc_stp_threshold,
                 monday_sch, tuesday_sch, wednesday_sch, thursday_sch,
                 friday_sch, saturday_sch, sunday_sch,
                 no_req_data, stpr_reset_threshold, sat_reset_threshold,
                 analysis):
        self.fanstat_values = []
        self.schedule = {}
        self.stcpr_arr = []
        self.stcpr_stpt_arr = []
        self.sat_stpt_arr = []
        self.timestamp = []
        self.sched_time = []
        self.dx_table = {}
        self.dx_time = None

        def date_parse(dates):
            return [parse(timestamp).time() for timestamp in dates]

        self.analysis = analysis
        self.sched_file_name_id = analysis + '-' + SCHEDULE_FILE_TOKEN
        self.reset_file_name_id = analysis + '-' + RESET_FILE_TOKEN
        self.monday_sch = date_parse(monday_sch)
        self.tuesday_sch = date_parse(tuesday_sch)
        self.wednesday_sch = date_parse(wednesday_sch)
        self.thursday_sch = date_parse(thursday_sch)
        self.friday_sch = date_parse(friday_sch)
        self.saturday_sch = date_parse(saturday_sch)
        self.sunday_sch = date_parse(sunday_sch)

        self.schedule = {0: self.monday_sch, 1: self.tuesday_sch,
                         2: self.wednesday_sch, 3: self.thursday_sch,
                         4: self.friday_sch, 5: self.saturday_sch,
                         6: self.sunday_sch}
        self.pre_msg = ('Current time is in the scheduled hours '
                        'unit is operating correctly.')

        # Application thresholds (Configurable)
        self.no_req_data = no_req_data
        self.unocc_time_threshold = float(unocc_time_threshold)
        self.unocc_stp_threshold = float(unocc_stp_threshold)
        self.stpr_reset_threshold = float(stpr_reset_threshold)
        self.sat_reset_threshold = float(sat_reset_threshold)

    def reinitialize(self, start_new_analysis_time, start_new_analysis_sat_stpt,
                     start_new_analysis_stcpr_stpt, stcpr_data, fan_status):
        """Reinitialize data arrays"""
        self.sat_stpt_arr = []
        self.stcpr_arr = []
        self.stcpr_stpt_arr = []
        self.fanstat_values = []
        self.sched_time = []
        self.dx_table = {}
        if start_new_analysis_stcpr_stpt is not None:
            self.sat_stpt_arr.append(start_new_analysis_sat_stpt)
            self.stcpr_stpt_arr.append(start_new_analysis_stcpr_stpt)
        if fan_status is not None:
            self.fanstat_values.append((start_new_analysis_time, fan_status))
            self.stcpr_arr.extend(stcpr_data)
        self.timestamp = [start_new_analysis_time]

    def sched_rcx_alg(self, current_time, stcpr_data, stcpr_stpt_data,
                      sat_stpt_data, fan_stat_data, dx_result):
        """Check schedule status and unit operational status."""
        dx_status = 1
        fan_status = None
        schedule = self.schedule[current_time.weekday()]
        run_diagnostic = False
        start_new_analysis_sat_stpt = None
        start_new_analysis_stcpr_stpt = None

        if self.timestamp and self.timestamp[-1].date() != current_time.date():
            start_new_analysis_time = current_time
            run_diagnostic = True

        if not run_diagnostic:
            if current_time.time() < schedule[0] or current_time.time() > schedule[1]:
                self.stcpr_arr.extend(stcpr_data)
                self.fanstat_values.append((current_time, int(max(fan_stat_data))))
                self.sched_time.append(current_time)
            if int(max(fan_stat_data)):
                self.stcpr_stpt_arr.append(mean(stcpr_stpt_data))
                self.sat_stpt_arr.append(mean(sat_stpt_data))
        fan_status = int(max(fan_stat_data))
        start_new_analysis_sat_stpt = mean(stcpr_stpt_data)
        start_new_analysis_stcpr_stpt = mean(sat_stpt_data)
        self.timestamp.append(current_time)

        reset_key = create_table_key(self.reset_file_name_id, self.timestamp[0])
        schedule_key = create_table_key(self.sched_file_name_id, self.timestamp[0])
        file_key = create_table_key(RESET_VAL_FILE_TOKEN, current_time)
        if run_diagnostic and len(self.timestamp) >= self.no_req_data:
            self.dx_time = self.timestamp[-1].date()
            dx_result = self.unocc_fan_operation(dx_result)
            if len(self.stcpr_stpt_arr) >= self.no_req_data:
                dx_result = self.no_static_pr_reset(dx_result)
                dx_status += 1
            if len(self.sat_stpt_arr) >= self.no_req_data:
                dx_result = self.no_sat_stpt_reset(dx_result)
                dx_status += 2
            if self.dx_table:
                dx_result.insert_table_row(reset_key, self.dx_table)

            self.reinitialize(start_new_analysis_time, start_new_analysis_sat_stpt,
                              start_new_analysis_stcpr_stpt, stcpr_data, fan_status)
        elif run_diagnostic:
            dx_msg = 61.2
            dx_table = {SCHED_RCX + DX: dx_msg}
            dx_result.insert_table_row(schedule_key, dx_table)

            self.reinitialize(start_new_analysis_time, start_new_analysis_sat_stpt,
                              start_new_analysis_stcpr_stpt, stcpr_data, fan_status)
            dx_status = 0

        return dx_status, dx_result

    def unocc_fan_operation(self, dx_result):
        """If the AHU/RTU is operating during unoccupied periods inform the
        building operator.
        """
        avg_duct_stcpr = 0
        percent_on = 0
        fanstat_on = [(fan[0].hour, fan[1]) for fan in self.fanstat_values if int(fan[1]) == 1]
        fanstat = [(fan[0].hour, fan[1]) for fan in self.fanstat_values]
        hourly_counter = []

        for counter in range(24):
            fan_on_count = [fan_status_time[1] for fan_status_time in fanstat_on if fan_status_time[0] == counter]
            fan_count = [fan_status_time[1] for fan_status_time in fanstat if fan_status_time[0] == counter]
            if len(fan_count):
                hourly_counter.append(fan_on_count.count(1) / len(fan_count) * 100)
            else:
                hourly_counter.append(0)

        if self.sched_time:
            if self.fanstat_values:
                percent_on = (len(fanstat_on) / len(self.fanstat_values)) * 100.0
            if self.stcpr_arr:
                avg_duct_stcpr = mean(self.stcpr_arr)

            if percent_on > self.unocc_time_threshold:
                msg = 'Supply fan is on during unoccupied times.'
                color_code = 'RED'
                dx_msg = 63.1
            else:
                if avg_duct_stcpr < self.unocc_stp_threshold:
                    msg = 'No problems detected for schedule diagnostic.'
                    color_code = 'GREEN'
                    dx_msg = 60.0
                else:
                    msg = ('Fan status show the fan is off but the duct static '
                           'pressure is high, check the functionality of the '
                           'pressure sensor.')
                    color_code = 'RED'
                    dx_msg = 64.2
        else:
            msg = 'No problems detected for schedule diagnostic.'
            color_code = 'GREEN'
            dx_msg = 60.0

        if dx_msg != 64.2:
            for _hour in range(24):
                push_time = self.timestamp[0].date()
                push_time = datetime.combine(push_time, datetime.min.time())
                push_time = push_time.replace(hour=_hour)
                #dx_table = {SCHED_RCX + DX: 60.0}
                if hourly_counter[_hour] > self.unocc_time_threshold:
                    dx_table = {
                        'datetime': str(push_time),
                        'diagnostic_name': SCHED_RCX,
                        'diagnostic_message': msg,
                        'energy_impact': None,
                        'color_code': color_code
                    }
                    table_key = create_table_key(self.sched_file_name_id, push_time)
                    dx_result.insert_table_row('Airside_RCx', dx_table)
        else:
            push_time = self.timestamp[0].date()
            table_key = create_table_key(self.sched_file_name_id, push_time)
            dx_table = {
                'datetime': str(push_time),
                'diagnostic_name': SCHED_RCX,
                'diagnostic_message': msg,
                'energy_impact': None,
                'color_code': color_code
            }
            dx_result.insert_table_row('Airside_RCx', dx_table)
        dx_result.log(msg, logging.INFO)
        return dx_result

    def no_static_pr_reset(self, dx_result):
        """Auto-RCx  to detect whether a static pressure set point
        reset is implemented.
        """
        if not self.stcpr_stpt_arr:
            return dx_result

        stcpr_daily_range = (max(self.stcpr_stpt_arr) - min(self.stcpr_stpt_arr))

        if stcpr_daily_range < self.stpr_reset_threshold:
            color_code = 'RED'
            msg = ('No duct static pressure reset detected. A duct static '
                   'pressure set point reset can save significant energy.')
            dx_msg = 71.1
        else:
            msg = ('No problems detected for duct static pressure set point '
                   'reset diagnostic.')
            color_code = 'GREEN'
            dx_msg = 70.0

        dx_table = {
            'datetime': str(self.dx_time),
            'diagnostic_name': DUCT_STC_RCX3,
            'diagnostic_message': msg,
            'energy_impact': None,
            'color_code': color_code
        }

        dx_result.insert_table_row('Airside_RCx', dx_table)
        dx_result.log(msg, logging.INFO)
        return dx_result

    def no_sat_stpt_reset(self, dx_result):
        """Auto-RCx  to detect whether a supply-air temperature set point
        reset is implemented.
        """
        if not self.sat_stpt_arr:
            return dx_result

        satemp_daily_range = max(self.sat_stpt_arr) - min(self.sat_stpt_arr)
        if satemp_daily_range <= self.sat_reset_threshold:
            msg = ('A supply-air temperature reset was not detected. '
                   'This can result in excess energy consumption.')
            color_code = 'RED'
            dx_msg = 81.1
        else:
            msg = ('No problems detected for supply-air temperature set point '
                   'reset diagnostic.')
            color_code = 'GREEN'
            dx_msg = 80.0

        dx_table = {
            'datetime': str(self.dx_time),
            'diagnostic_name': DUCT_STC_RCX3,
            'diagnostic_message': msg,
            'energy_impact': None,
            'color_code': color_code
        }

        dx_result.insert_table_row('Airside_RCx', dx_table)
        dx_result.log(msg, logging.INFO)
        return dx_result
