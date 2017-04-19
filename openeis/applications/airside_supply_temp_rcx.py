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
from datetime import timedelta as td
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
SA_TEMP_RCX = 'Supply-air Temperature Set Point Control Loop Dx'
SA_TEMP_RCX1 = 'Low Supply-air Temperature Dx'
SA_TEMP_RCX2 = 'High Supply-air Temperature Dx'
SA_TEMP_RCX3 = 'No Supply-air Temperature Reset Dx'

DX = '/diagnostic message'

STCPR_NAME = 'StcPr_ACCx_State'
SATEMP_NAME = 'Satemp_ACCx_State'
SCHED_NAME = 'Sched_ACCx_State'
ST = 'state'
DATA = '/data/'

SATEMP_VAL_FILE_TOKEN = 'satemp-rcx'
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
                           token, token_offset, current_time):
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
            # dx_msg = 1.1 + token_offset
            color_code = 'RED'
            # dx_table = {dx_name + dx_tag: dx_msg}
        else:
            # color_code = 'green'
            msg = 'No problem detected.'
            # dx_msg = 0.0 + token_offset
            color_code = 'GREEN'
            # dx_table = {dx_name + dx_tag: dx_msg}
    else:
        # color_code = 'grey'
        msg = ('{} set point data is not available. '
               'The Set Point Control Loop Diagnostic'
               'requires set point '
               'data.'.format(token))
        # dx_msg = 2.2 + token_offset
        color_code = 'GREY'
        # dx_table = {dx_name + dx_tag: dx_msg}

    dx_table = {
        'datetime': str(current_time),
        'diagnostic_name': SA_TEMP_RCX,
        'diagnostic_message': msg,
        'energy_impact': None,
        'color_code': color_code
    }

    return average_setpoint, dx_table


class Application(DrivenApplicationBaseClass):
    """
    Air-side HVAC Auto-Retuning Diagnostics
    for AHUs
    """
    fan_status_name = 'fan_status'
    zone_reheat_name = 'zone_reheat'
    zone_damper_name = 'zone_damper'
    fan_speedcmd_name = 'fan_speedcmd'
    sa_temp_name = 'sa_temp'
    sat_stpt_name = 'sat_stpt'

    fan_speedcmd_priority = ''
    duct_stp_stpt_priority = ''
    ahu_ccoil_priority = ''
    sat_stpt_priority = ''

    def __init__(self, *args, no_required_data=1, data_window=1, warm_up_time=0, local_tz=1,
                 setpoint_allowable_deviation=10.0, percent_reheat_threshold=25.0,
                 rht_on_threshold=10.0, sat_reset_threshold=5.0, sat_high_damper_threshold=80.0,
                 percent_damper_threshold=50.0, minimum_sat_stpt=50.0, sat_retuning=1.0,
                 reheat_valve_threshold=50.0, maximum_sat_stpt=75.0, sensitivity=1, **kwargs):
        super().__init__(*args, **kwargs)

        if sensitivity == 0:
            # low sensitivity
            setpoint_allowable_deviation = 15.0
            percent_reheat_threshold = 25.0
            percent_damper_threshold = 100.0
            reheat_valve_threshold = 75.0
            sat_reset_threshold = 7.0
            sat_high_damper_threshold = float(sat_high_damper_threshold) * 1.5
        elif sensitivity == 1:
            # normal sensitivity
            setpoint_allowable_deviation = 10.0
            percent_reheat_threshold = 25.0
            percent_damper_threshold = 80.0
            reheat_valve_threshold = 50.0
            sat_reset_threshold = 5.0
            sat_high_damper_threshold = float(sat_high_damper_threshold)
        elif sensitivity == 2:
            # high sensitivity
            setpoint_allowable_deviation = 5.0
            percent_reheat_threshold = 25.0
            percent_damper_threshold = 60.0
            reheat_valve_threshold = 25.0
            sat_reset_threshold = 3.0
            sat_high_damper_threshold = float(sat_high_damper_threshold) * 0.5

        try:
            self.cur_tz = available_tz[local_tz]
        except:
            self.cur_tz = 'UTC'

        self.fan_status_name = Application.fan_status_name
        self.sa_temp_name = Application.sa_temp_name
        self.sat_stpt_name = Application.sat_stpt_name
        Application.sat_stpt_cname = Application.sat_stpt_name
        # Optional points
        if Application.fan_speedcmd_name is not None:
            self.fan_speedcmd_name = Application.fan_speedcmd_name.lower()
        else:
            self.fan_speedcmd_name = None

        # Zone Parameters
        self.zone_damper_name = Application.zone_damper_name.lower()
        self.zone_reheat_name = Application.zone_reheat_name.lower()

        # Application thresholds (Configurable)
        self.data_window = float(data_window)
        self.warm_up_flag = None
        self.warm_up_time = int(warm_up_time)
        self.warm_up_start = None
        auto_correctflag = True
        no_required_data = int(no_required_data)
        analysis = 'Airside_RCx'

        self.sat_dx = SupplyTempRcx(no_required_data, auto_correctflag, setpoint_allowable_deviation,
                                    rht_on_threshold, sat_high_damper_threshold, percent_damper_threshold,
                                    percent_reheat_threshold, minimum_sat_stpt, sat_retuning, reheat_valve_threshold,
                                    maximum_sat_stpt, sat_reset_threshold, analysis, Application.sat_stpt_cname)

    @classmethod
    def get_config_parameters(cls):
        """
        Generate required configuration
        parameters with description for user
        """
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
                             value_default=30),
            'setpoint_allowable_deviation':
            ConfigDescriptor(float,
                             'Allowable deviation from set points '
                             'before a fault message is generated '
                             '(%)', value_default=10.0),

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
            'rht_on_threshold':
            ConfigDescriptor(float,
                             'Value above which zone re-heat is '
                             'considered ON (%)',
                             value_default=10.0),
            'sat_high_damper_threshold':
            ConfigDescriptor(float,
                             'High zone damper threshold for '
                             'high supply-air temperature RCx (%)',
                             value_default=30),
            'percent_damper_threshold':
            ConfigDescriptor(float,
                             'Threshold for the average % of zone '
                             'dampers above high damper threshold '
                             '(%)',
                             value_default=50.0),
            'sat_reset_threshold':
            ConfigDescriptor(float,
                             'Threshold difference required '
                             'to detect a supply-air temperature '
                             'set point reset ({drg}F)'.format(drg=dgr_sym),
                             value_default=3.0),
            'sensitivity':
            ConfigDescriptor(int,
                             'Sensitivity: values can be 0 (low), '
                             '1 (normal), 2 (high), 3 (custom). Setting sensitivity to 3 (custom) '
                             'allows you to enter your own values for all threshold values',
                             value_default=1),
            'local_tz':
            ConfigDescriptor(int,
                             "Integer corresponding to local timezone: [1: 'US/Pacific', 2: 'US/Mountain', 3: 'US/Central', 4: 'US/Eastern']",
                             value_default=1)
            }

    @classmethod
    def get_self_descriptor(cls):
        """Name and description for of application for UI"""
        name = 'Auto-RCx AHU: Supply Temperature'
        desc = 'Auto-RCx AHU: Supply Temperature'
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
            cls.zone_reheat_name:
            InputDescriptor('TerminalBoxReheatValvePosition',
                            'All terminal-box re-heat valve commands',
                            count_min=1),
            cls.zone_damper_name:
            InputDescriptor('TerminalBoxDamperCommand',
                            'All terminal-box damper commands', count_min=1),

            cls.sa_temp_name:
            InputDescriptor('DischargeAirTemperature', 'AHU supply-air '
                            '(discharge-air) temperature', count_min=1),
            cls.sat_stpt_name:
            InputDescriptor('DischargeAirTemperatureSetPoint',
                            'Supply-air temperature set-point', count_min=1)
            }

    def reports(self):
        """Called by UI to assemble information for creation of the diagnostic
        visualization.
        """
        report = reports.Report('Retuning Report')
        # report.add_element(reports.RetroCommissioningOAED(
        #     table_name='Airside_RCx'))
        report.add_element(reports.RxSupplyTemp(
            table_name='Airside_RCx'))
        return [report]

    @classmethod
    def output_format(cls, input_object):
        """Describes how the output or results will be formatted
        Output will have the date-time, error-message, color-code,
        and energy impact.
        """
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
        """
        Check application pre-quisites and assemble analysis data set.
        Receives mapped data from the DrivenBaseClass.  Filters non-relevent
        data and assembles analysis data set for diagnostics.
        """
        # topics = self.inp.get_topics()
        # diagnostic_topic = topics[self.fan_status_name][0])
        # cur_time = self.inp.localize_sensor_time(diagnostic_topic, current_time)
        to_zone = dateutil.tz.gettz(self.cur_tz)
        cur_time = current_time.astimezone(to_zone)
        device_dict = {}
        diagnostic_result = Results()
        fan_status_data = []
        supply_fan_off = False

        for key, value in points.items():
            point_device = [_name.lower() for _name in key.split('&&&')]
            print(point_device)
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


        zn_dmpr_data = []
        satemp_data = []
        rht_data = []
        sat_stpt_data = []

        def data_builder(value_tuple, point_name):
            value_list = []
            for item in value_tuple:
                value_list.append(item[1])
            return value_list

        for key, value in device_dict.items():
            data_name = key
            if value is None:
                continue
            elif data_name == self.sat_stpt_name:
                sat_stpt_data = data_builder(value, data_name)
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
        if not zn_dmpr_data:
            missing_data.append(self.zone_damper_name)
        if not fan_status:
            missing_data.append(self.fan_status_name)
        if missing_data:
            diagnostic_result.log('Missing required data: {}'.format(missing_data))
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
        dx_status, diagnostic_result = self.sat_dx.sat_rcx(cur_time, satemp_data, sat_stpt_data,
                                                           rht_data, zn_dmpr_data, diagnostic_result)
        return diagnostic_result


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
                 min_sat_stpt, sat_retuning, rht_valve_thr, max_sat_stpt, sat_reset_threshold,
                 analysis, sat_stpt_cname):
        self.timestamp_arr = []
        self.timestamp_reset = []
        self.sat_stpt_arr = []
        self.satemp_arr = []
        self.rht_arr = []
        self.percent_rht = []
        self.percent_dmpr = []
        self.satemp_stpt_reset = []
        self.table_key = None
        self.file_key = None
        self.data = {}
        self.dx_table = {}
        self.dx_time = None

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
        self.high_dmpr_thr = high_dmpr_thr
        self.percent_dmpr_thr = percent_dmpr_thr
        self.min_sat_stpt = min_sat_stpt
        self.sat_retuning = sat_retuning
        self.token_offset = 30.0

        # SAT Reset RCx threshold
        self.sat_reset_threshold = sat_reset_threshold

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
            avg_sat_stpt, dx_table = setpoint_control_check(self.sat_stpt_arr, self.satemp_arr,
                                                            self.stpt_allowable_dev, SA_TEMP_RCX,
                                                            self.token_offset, self.timestamp_arr[-1])

            dx_result.insert_table_row('Airside_RCx', dx_table)
            dx_result = self.low_sat(dx_result, avg_sat_stpt)
            dx_result = self.high_sat(dx_result, avg_sat_stpt)
            # dx_result.insert_table_row(self.table_key, self.dx_table)
            dx_result.log('{}: Running diagnostics.'.format(SA_VALIDATE, logging.DEBUG))
            dx_status = 2
            self.reinitialize()

        if self.timestamp_reset and self.timestamp_reset[-1].date() != current_time.date():
            self.dx_time = self.timestamp_reset[-1]
            if len(self.satemp_stpt_reset) >= self.no_req_data:
                dx_result = self.no_sat_stpt_reset(dx_result)
            else:
                dx_table = {
                    'datetime': str(self.dx_time),
                    'diagnostic_name': SA_TEMP_RCX3,
                    'diagnostic_message': 'Insufficient data for conclusive diagnostic.',
                    'energy_impact': None,
                    'color_code': 'GREY'
                }
                dx_result.insert_table_row('Airside_RCx', dx_table)
            self.satemp_stpt_reset = []
            self.timestamp_reset = []

        dx_result.log('{}: Collecting and aggregating data.'.format(SA_VALIDATE, logging.DEBUG))
        self.satemp_arr.append(mean(sat_data))
        self.satemp_stpt_reset.append(mean(sat_data))
        self.rht_arr.append(mean(zone_rht_data))
        self.sat_stpt_arr.append(mean(sat_stpt_data))
        self.percent_rht.append(tot_rht/count_rht)
        self.percent_dmpr.append(tot_dmpr/count_damper)
        self.timestamp_arr.append(current_time)
        self.timestamp_reset.append(current_time)

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
                msg = ('The SAT has been detected to be too low but '
                       'but supply-air temperature set point data '
                       'is not available.')
                # dx_msg = 43.1
            elif self.auto_correct_flag:
                autocorrect_sat_stpt = avg_sat_stpt + self.sat_retuning
                if autocorrect_sat_stpt <= self.max_sat_stpt:
                    dx_result.command(self.sat_stpt_cname, autocorrect_sat_stpt)
                    sat_stpt = '%s' % float('%.2g' % autocorrect_sat_stpt)
                    msg = ('The SAT has been detected to be too low.')
                    # dx_msg = 41.1
                else:
                    dx_result.command(self.sat_stpt_cname, self.max_sat_stpt)
                    sat_stpt = '%s' % float('%.2g' % self.max_sat_stpt)
                    sat_stpt = str(sat_stpt)
                    msg = (
                        'The supply-air temperautre was detected to be '
                        'too low.')
                    # dx_msg = 42.1
            else:
                msg = ('The SAT has been detected to be too low.')
                # dx_msg = 44.1
        else:
            msg = 'No problem detected.'
            color_code = 'GREEN'
            # dx_msg = 40.0

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
                msg = ('The SAT has been detected to be too high but '
                       'but supply-air temperature set point data '
                       'is not available.')
                # dx_msg = 54.1
            elif self.auto_correct_flag:
                autocorrect_sat_stpt = avg_sat_stpt - self.sat_retuning
                # Create diagnostic message for fault condition
                # with auto-correction
                if autocorrect_sat_stpt >= self.min_sat_stpt:
                    dx_result.command(self.sat_stpt_cname, autocorrect_sat_stpt)
                    sat_stpt = '%s' % float('%.2g' % autocorrect_sat_stpt)
                    msg = ('The SAT has been detected to be too high.')
                    # dx_msg = 51.1
                else:
                    # Create diagnostic message for fault condition
                    # where the maximum SAT has been reached
                    dx_result.command(self.sat_stpt_cname, self.min_sat_stpt)
                    sat_stpt = '%s' % float('%.2g' % self.min_sat_stpt)
                    msg = ('The SAT was detected to be too high.')
                    # dx_msg = 52.1
            else:
                # Create diagnostic message for fault condition
                # without auto-correction
                msg = ('The SAT has been detected to be too high.')
                # dx_msg = 53.1
        else:
            msg = ('No problem detected.')
            color_code = 'GREEN'
            # dx_msg = 50.0

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

    def no_sat_stpt_reset(self, dx_result):
        """Auto-RCx  to detect whether a supply-air temperature set point
        reset is implemented.
        """
        if not self.satemp_stpt_reset:
            return dx_result

        satemp_daily_range = max(self.satemp_stpt_reset) - min(self.satemp_stpt_reset)
        if satemp_daily_range <= self.sat_reset_threshold:
            msg = ('A supply-air temperature reset was not detected. '
                   'This can result in excess energy consumption.')
            color_code = 'RED'
            # dx_msg = 81.1
        else:
            msg = ('No problems detected for supply-air temperature set point '
                   'reset diagnostic.')
            color_code = 'GREEN'
            # dx_msg = 80.0

        dx_table = {
            'datetime': str(self.dx_time),
            'diagnostic_name': SA_TEMP_RCX3,
            'diagnostic_message': msg,
            'energy_impact': None,
            'color_code': color_code
        }

        dx_result.insert_table_row('Airside_RCx', dx_table)
        dx_result.log(msg, logging.INFO)
        return dx_result
