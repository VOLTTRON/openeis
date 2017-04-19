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
import logging
import math
from datetime import timedelta as td
from copy import deepcopy
import dateutil.tz
from numpy import mean
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
    """
    Check current timestamp with previous timestamp
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
    """
    The diagnostics run at a regular interval (some minimum elapsed amount of time) and have a
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
                           dx_name, dx_tag, token, token_offset, current_time):
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
            color_code = 'RED'
            # dx_table = {dx_name + dx_tag: dx_msg}
        else:
            # color_code = 'green'
            msg = 'No problem detected.'
            dx_msg = 0.0 + token_offset
            color_code = 'GREEN'
            # dx_table = {dx_name + dx_tag: dx_msg}
    else:
        # color_code = 'grey'
        msg = ('{} set point data is not available. '
               'The Set Point Control Loop Diagnostic'
               'requires set point '
               'data.'.format(token))
        dx_msg = 2.2 + token_offset
        color_code = 'GREY'
        # dx_table = {dx_name + dx_tag: dx_msg}

    dx_table = {
        'datetime': str(current_time),
        'diagnostic_name': DUCT_STC_RCX,
        'diagnostic_message': msg,
        'energy_impact': None,
        'color_code': color_code
    }

    return average_setpoint, dx_table


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

    def __init__(self, *args, no_required_data=1, data_window=1, local_tz=1,
                 warm_up_time=0, duct_stc_retuning=0.15,
                 max_duct_stp_stpt=2.5, high_supply_fan_threshold=100.0,
                 zone_high_damper_threshold=90.0,
                 zone_low_damper_threshold=10.0, min_duct_stp_stpt=0.5,
                 hdzone_damper_threshold=30.0, low_supply_fan_threshold=20.0,
                 setpoint_allowable_deviation=10.0, sensitivity=1,
                 stpr_reset_threshold=0.25, **kwargs):
        super().__init__(*args, **kwargs)
        if sensitivity == 0:
            # low sensitivity
            setpoint_allowable_deviation = 15
            zone_high_damper_threshold = 100
            zone_low_damper_threshold = 5
            stpr_reset_threshold = 0.38
        elif sensitivity == 1:
            # normal sensitivity
            setpoint_allowable_deviation = 10
            zone_high_damper_threshold = 90
            zone_low_damper_threshold = 10
            stpr_reset_threshold = 0.25
        elif sensitivity == 2:
            # high sensitivity
            setpoint_allowable_deviation = 5
            zone_high_damper_threshold = 80
            zone_low_damper_threshold = 15
            stpr_reset_threshold = 0.17

        try:
            self.cur_tz = available_tz[local_tz]
        except:
            self.cur_tz = 'UTC'

        # Point names (Configurable)
        self.fan_status_name = Application.fan_status_name
        self.duct_stp_stpt_name = Application.duct_stp_stpt_name
        self.duct_stp_name = Application.duct_stp_name
        self.sa_temp_name = Application.sa_temp_name
        self.sat_stpt_name = Application.sat_stpt_name

        duct_stp_stpt_cname = Application.duct_stp_stpt_name
        if Application.fan_speedcmd_name is not None:
            self.fan_speedcmd_name = Application.fan_speedcmd_name.lower()
        else:
            self.fan_speedcmd_name = None

        # Zone Points
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
        analysis = "Airside_RCx"
        self.static_dx = DuctStaticRcx(no_required_data, auto_correctflag, setpoint_allowable_deviation,
                                       max_duct_stp_stpt, duct_stc_retuning, zone_high_damper_threshold,
                                       zone_low_damper_threshold, hdzone_damper_threshold,
                                       min_duct_stp_stpt, stpr_reset_threshold, analysis,
                                       duct_stp_stpt_cname)

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
            'sensitivity':
            ConfigDescriptor(int,
                             'Sensitivity: values can be 0 (low), '
                             '1 (normal), 2 (high), 3 (custom). Setting sensitivity to 3 (custom) '
                             'allows you to enter your own values for all threshold values',
                             value_default=1),
            'stpr_reset_threshold':
            ConfigDescriptor(float,
                             ('Required difference between minimum and '
                              'maximum duct static pressure set point '
                              'detecting a duct static pressure '
                              'set point reset (inch w.g.)'),
                             value_default=0.25),
            'local_tz':
            ConfigDescriptor(int,
                             "Integer corresponding to local timezone: [1: 'US/Pacific', 2: 'US/Mountain', 3: 'US/Central', 4: 'US/Eastern']",
                             value_default=1)
            }

    @classmethod
    def get_self_descriptor(cls):
        name = 'Auto-RCx AHU: Static Pressure'
        desc = 'Auto-RCx AHU: Static Pressure'
        return Descriptor(name=name, description=desc)

    @classmethod
    def required_input(cls):
        """
        Generate required inputs with description for
        user.
        """
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
        """
        Called by UI to assemble information for creation of the diagnostic
        visualization.
        """
        report = reports.Report('Retuning Report')
        # report.add_element(reports.RetroCommissioningOAED(
        #     table_name='Airside_RCx'))
        report.add_element(reports.RxStaticPressure(
            table_name='Airside_RCx'))
        return [report]

    @classmethod
    def output_format(cls, input_object):
        """
        Describes how the output or results will be formatted
        Output will have the date-time, error-message, color-code,
        and energy impact.
        """
        result = super().output_format(input_object)
        topics = input_object.get_topics()
        diagnostic_topic = topics[cls.fan_status_name][0]
        diagnostic_topic_parts = diagnostic_topic.split('/')
        output_topic_base = diagnostic_topic_parts[:-1]
        datetime_topic = '/'.join(output_topic_base + ['Airside_RCx', 'date'])
        message_topic = '/'.join(output_topic_base + ['Airside_RCx', 'message'])
        diagnostic_name = '/'.join(output_topic_base + ['Airside_RCx', ' diagnostic_name'])
        energy_impact = '/'.join(output_topic_base + ['Airside_RCx', 'energy_impact'])
        color_code = '/'.join(output_topic_base + ['Airside_RCx', 'color_code'])

        output_needs = {
            'Airside_RCx': {
                'datetime': OutputDescriptor('string', datetime_topic),
                'diagnostic_name': OutputDescriptor('string', diagnostic_name),
                'diagnostic_message': OutputDescriptor('string', message_topic),
                'energy_impact': OutputDescriptor('float', energy_impact),
                'color_code': OutputDescriptor('string', color_code)
                }
            }
        result.update(output_needs)
        return result

    def run(self, current_time, points):
        """
        Check application pre-quisites and assemble analysis data set.
        Receives mapped data from the DrivenBaseClass.  Filters non-relevent
        data and assembles analysis data set for diagnostics.
        """
        # topics = self.inp.get_topics()
        # diagnostic_topic = topics[self.fan_status_name][0]
        # cur_time = self.inp.localize_sensor_time(diagnostic_topic, current_time)
        to_zone = dateutil.tz.gettz(self.cur_tz)
        cur_time = current_time.astimezone(to_zone)
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

        if self.fan_speedcmd_name in device_dict:
            fan_speed = device_dict[self.fan_speedcmd_name]
            fan_speed = mean([point[1] for point in fan_speed])
            if self.fan_status_name is None:
                if not int(fan_speed):
                    supply_fan_off = True
                    self.warm_up_flag = True
                fan_status_data.append(bool(int(fan_speed)))

            if fan_speed > self.high_supply_fan_threshold:
                low_dx_cond = True
            elif fan_speed < self.low_supply_fan_threshold:
                high_dx_cond = True

        stc_pr_data = []
        stcpr_sp_data = []
        zn_dmpr_data = []

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
            elif data_name == self.duct_stp_name:
                stc_pr_data = data_builder(value, data_name)
            elif data_name == self.zone_damper_name:
                zn_dmpr_data = data_builder(value, data_name)
        missing_data = []

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
                                                                  zn_dmpr_data, low_dx_cond, high_dx_cond,
                                                                  diagnostic_result)
        return diagnostic_result

class DuctStaticRcx(object):
    """
    Air-side HVAC Self-Correcting Diagnostic: Detect and correct
    duct static pressure problems.
    """

    def __init__(self, no_req_data, auto_correct_flag, stpt_allowable_dev,
                 max_stcpr_stpt, stcpr_retuning, zone_high_dmpr_threshold,
                 zone_low_dmpr_threshold, hdzn_dmpr_thr, min_stcpr_stpt,
                 stpr_reset_threshold, analysis, stcpr_stpt_cname):
        # Initialize data arrays
        self.table_key = None
        self.file_key = None
        self.zn_dmpr_arr = []
        self.stcpr_stpt_arr = []
        self.stcpr_stpt_reset = []
        self.stcpr_arr = []
        self.timestamp_arr = []
        self.timestamp_reset = []
        self.data = {}
        self.dx_table = {}
        self.dx_time = None

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
        self.stpr_reset_threshold = float(stpr_reset_threshold)
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
        """
        Check duct static pressure RCx pre-requisites and assemble the
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
            avg_stcpr_stpt, dx_table = setpoint_control_check(self.stcpr_stpt_arr, self.stcpr_arr,
                                                              self.stpt_allowable_dev, DUCT_STC_RCX, DX,
                                                              STCPR_POINT_NAME, self.token_offset,
                                                              self.timestamp_arr[-1])

            dx_result.insert_table_row('Airside_RCx', dx_table)
            dx_result = self.low_stcpr_dx(dx_result, avg_stcpr_stpt)
            dx_result = self.high_stcpr_dx(dx_result, avg_stcpr_stpt)
            # dx_result.insert_table_row(self.table_key, self.dx_table)
            dx_result.log('{}: Running diagnostics.'.format(STCPR_VALIDATE, logging.DEBUG))
            dx_status = 2
            self.reinitialize()

        if self.timestamp_reset and self.timestamp_reset[-1].date() != current_time.date():
            self.dx_time = self.timestamp_reset[-1]
            if len(self.stcpr_stpt_reset) >= self.no_req_data:
                dx_result = self.no_static_pr_reset(dx_result)
            else:
                dx_table = {
                    'datetime': str(self.dx_time),
                    'diagnostic_name': DUCT_STC_RCX3,
                    'diagnostic_message': 'Insufficient data for conclusive diagnostic.',
                    'energy_impact': None,
                    'color_code': 'GREY'
                }
                dx_result.insert_table_row('Airside_RCx', dx_table)
            self.stcpr_stpt_reset = []
            self.timestamp_reset = []

        dx_result.log('{}: Collecting and aggregating data.'.format(STCPR_VALIDATE, logging.DEBUG))
        self.stcpr_stpt_arr.append(mean(stcpr_data))
        self.stcpr_arr.append(mean(stcpr_stpt_data))
        self.stcpr_stpt_reset.append(mean(stcpr_stpt_data))
        self.zn_dmpr_arr.append(mean(zn_dmpr_data))
        self.timestamp_arr.append(current_time)
        self.timestamp_reset.append(current_time)
        return dx_status, dx_result

    def low_stcpr_dx(self, dx_result, avg_stcpr_stpt):
        """
        Diagnostic to identify and correct low duct static pressure
        (correction by modifying duct static pressure set point).
        """
        zn_dmpr = deepcopy(self.zn_dmpr_arr)
        zn_dmpr.sort(reverse=False)
        zone_dmpr_lowtemp = zn_dmpr[:int(math.ceil(len(self.zn_dmpr_arr) * 0.5)) if len(self.zn_dmpr_arr) != 1 else 1]
        zn_dmpr_low_avg = mean(zone_dmpr_lowtemp)

        zone_dmpr_hightemp = zn_dmpr[int(math.ceil(len(self.zn_dmpr_arr) * 0.5)) - 1 if len(self.zn_dmpr_arr) != 1 else 0:]
        zn_dmpr_high_avg = mean(zone_dmpr_hightemp)

        if zn_dmpr_high_avg > self.zone_high_dmpr_threshold and zn_dmpr_low_avg > self.zone_low_dmpr_threshold:
            color_code = 'RED'
            if avg_stcpr_stpt is None:
                # Create diagnostic message for fault
                # when duct static pressure set point
                # is not available.
                msg = ('The duct static pressure set point has been '
                       'detected to be too low but but supply-air'
                       'temperature set point data is not available.')
                # dx_msg = 14.1
            elif self.auto_correct_flag:
                auto_correct_stcpr_stpt = avg_stcpr_stpt + self.stcpr_retuning
                if auto_correct_stcpr_stpt <= self.max_stcpr_stpt:
                    dx_result.command(self.stcpr_stpt_cname, auto_correct_stcpr_stpt)
                    new_stcpr_stpt = '%s' % float('%.2g' % auto_correct_stcpr_stpt)
                    new_stcpr_stpt = new_stcpr_stpt + ' in. w.g.'
                    msg = ('The duct static pressure was detected to be '
                           'too low.')
                    # dx_msg = 11.1
                else:
                    dx_result.command(self.stcpr_stpt_cname, self.max_stcpr_stpt)
                    new_stcpr_stpt = '%s' % float('%.2g' % self.max_stcpr_stpt)
                    new_stcpr_stpt = new_stcpr_stpt + ' in. w.g.'
                    msg = ('The duct static pressure set point is at the '
                           'maximum value configured by the building operator: {}'
                           .format(new_stcpr_stpt))
                    # dx_msg = 12.1
            else:
                msg = ('The duct static pressure set point was detected '
                       'to be too low.')
                # dx_msg = 13.1
        else:
            msg = ('No re-tuning opportunity was detected during the low duct '
                   'static pressure diagnostic.')
            color_code = 'GREEN'
            # dx_msg = 10.0

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
        """
        Diagnostic to identify and correct high duct static pressure
        (correction by modifying duct static pressure set point)
        """
        zn_dmpr = deepcopy(self.zn_dmpr_arr)
        zn_dmpr.sort(reverse=True)
        zn_dmpr = zn_dmpr[:int(math.ceil(len(self.zn_dmpr_arr) * 0.5)) if len(self.zn_dmpr_arr) != 1 else 1]
        avg_zone_damper = mean(zn_dmpr)

        if avg_zone_damper <= self.hdzn_dmpr_thr:
            color_code = 'RED'
            if avg_stcpr_stpt is None:
                # Create diagnostic message for fault
                # when duct static pressure set point
                # is not available.
                msg = ('The duct static pressure set point has been '
                       'detected to be too high but but duct static '
                       'pressure set point data is not available.'
                       'temperature set point data is not available.')
                # dx_msg = 24.1
            elif self.auto_correct_flag:
                auto_correct_stcpr_stpt = avg_stcpr_stpt - self.stcpr_retuning
                if auto_correct_stcpr_stpt >= self.min_stcpr_stpt:
                    dx_result.command(self.stcpr_stpt_cname, auto_correct_stcpr_stpt)
                    new_stcpr_stpt = '%s' % float('%.2g' % auto_correct_stcpr_stpt)
                    new_stcpr_stpt = new_stcpr_stpt + ' in. w.g.'
                    msg = ('The duct static pressure was detected to be '
                           'too high.')
                    # dx_msg = 21.1
                else:
                    dx_result.command(self.stcpr_stpt_cname, self.min_stcpr_stpt)
                    new_stcpr_stpt = '%s' % float('%.2g' % self.min_stcpr_stpt)
                    new_stcpr_stpt = new_stcpr_stpt + ' in. w.g.'
                    msg = ('The duct static pressure set point is at the '
                           'minimum value configured by the building '
                           'operator: {})'.format(new_stcpr_stpt))
                    # dx_msg = 22.1
            else:
                msg = ('Duct static pressure set point was detected to be '
                       'too high.')
                # dx_msg = 23.1
        else:
            msg = ('No re-tuning opportunity was detected during the high duct '
                   'static pressure diagnostic.')
            color_code = 'GREEN'
            # dx_msg = 20.0

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

    def no_static_pr_reset(self, dx_result):
        """
        Auto-RCx  to detect whether a static pressure set point
        reset is implemented.
        """
        if not self.stcpr_stpt_reset:
            return dx_result

        stcpr_daily_range = (max(self.stcpr_stpt_reset) - min(self.stcpr_stpt_reset))

        if stcpr_daily_range < self.stpr_reset_threshold:
            color_code = 'RED'
            msg = ('No duct static pressure reset detected. A duct static '
                   'pressure set point reset can save significant energy.')
            # dx_msg = 71.1
        else:
            msg = ('No problems detected for duct static pressure set point '
                   'reset diagnostic.')
            color_code = 'GREEN'
            # dx_msg = 70.0

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
