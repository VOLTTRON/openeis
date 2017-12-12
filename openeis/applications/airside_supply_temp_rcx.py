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
import sys
from datetime import timedelta as td
from numpy import mean
import dateutil.tz
from collections import defaultdict
from openeis.applications import (DrivenApplicationBaseClass,
                                  OutputDescriptor,
                                  ConfigDescriptor,
                                  InputDescriptor,
                                  Results,
                                  Descriptor,
                                  reports)

SA_TEMP_RCX = 'Supply-air Temperature Set Point Control Dx'
SA_TEMP_RCX1 = 'Low Supply-air Temperature Dx'
SA_TEMP_RCX2 = 'High Supply-air Temperature Dx'
SA_TEMP_RCX3 = 'No Supply-air Temperature Reset Dx'
DX = '/diagnostic message'
DX_LIST = [SA_TEMP_RCX, SA_TEMP_RCX1, SA_TEMP_RCX2]

FAN_OFF = -99.3
INCONSISTENT_DATE = -89.2
INSUFFICIENT_DATA = -79.2

RED = "RED"
GREY = "GREY"
WHITE = "WHITE"
GREEN = "GREEN"
DGR_SYM = u"\N{DEGREE SIGN}"

available_tz = {1: 'US/Pacific', 2: 'US/Mountain', 3: 'US/Central', 4: 'US/Eastern'}

"""Common functions used across multiple algorithms."""


def create_dx_table(cur_time, diagnostic, message, color_code, energy_impact=None):
    dx_table = dict(datetime=str(cur_time),
                    diagnostic_name=diagnostic,
                    diagnostic_message=message,
                    energy_impact=energy_impact,
                    color_code=color_code)
    return dx_table


def create_table_key(table_name, timestamp):
    return "&".join([table_name, timestamp.isoformat()])


def data_builder(value_tuple, point_name):
    value_list = []
    for item in value_tuple:
        value_list.append(item[1])
    return value_list


def check_date(current_time, timestamp_array):
    """
    Check current timestamp with previous timestamp to verify that there are no large missing data gaps.
    :param current_time:
    :param timestamp_array:
    :return:
    """
    if not timestamp_array:
        return False
    if current_time.date() != timestamp_array[-1].date():
        if (timestamp_array[-1].date() + td(days=1) != current_time.date() or
                (timestamp_array[-1].hour != 23 and current_time.hour == 0)):
            return True
        return False


def check_run_status(timestamp_array, current_time, no_required_data, minimum_diagnostic_time=None,
                     run_schedule="hourly", minimum_point_array=None):
    """
    The diagnostics run at a regular interval (some minimum elapsed amount of time) and have a
    minimum data count requirement (each time series of data must contain some minimum number of points).
    :param timestamp_array:
    :param current_time:
    :param no_required_data:
    :param minimum_diagnostic_time:
    :param run_schedule:
    :param minimum_point_array:
    :return:
    """
    def minimum_data():
        min_data_array = timestamp_array if minimum_point_array is None else minimum_point_array
        if len(min_data_array) < no_required_data:
            return None
        return True

    if minimum_diagnostic_time is not None:
        if timestamp_array:
            sampling_interval = td(minutes=
                round(((timestamp_array[-1] - timestamp_array[0])/len(timestamp_array)).total_seconds()/60))
            required_time = (timestamp_array[-1] - timestamp_array[0]) + sampling_interval
            if required_time >= minimum_diagnostic_time:
                return minimum_data()
        return False

    if run_schedule == "hourly":
        if timestamp_array and timestamp_array[-1].hour != current_time.hour:
            return minimum_data()
    elif run_schedule == "daily":
        if timestamp_array and timestamp_array[-1].date() != current_time.date():
            return minimum_data()
    return False


def setpoint_control_check(set_point_array, point_array, deviation_thr, dx_name, dx_offset, timestamp, dx_result):
    """
    Verify that point if tracking with set point - identify potential control or sensor problems.
    :param set_point_array:
    :param point_array:
    :param allowable_deviation:
    :param dx_name:
    :param dx_offset:
    :param dx_result:
    :return:
    """
    avg_set_point = None
    set_point_array = [float(pt) for pt in set_point_array if pt != 0]
    diagnostic_msg = {}
    color_code_dict = {}

    for key, deviation_threshold in deviation_thr.items():
        if set_point_array:
            avg_set_point = mean(set_point_array)
            zipper = (set_point_array, point_array)
            set_point_tracking = [abs(x - y) for x, y in zip(*zipper)]
            set_point_tracking = mean(set_point_tracking)/avg_set_point*100

            if set_point_tracking > deviation_threshold:
                color_code = RED
                msg = '{} - {}: point deviating significantly from set point.'.format(key, dx_name)
                result = 1.1 + dx_offset
            else:
                color_code = GREEN
                msg = " {} - No problem detected for {} set".format(key, dx_name)
                result = 0.0 + dx_offset
        else:
            color_code = GREY
            msg = "{} - {} set point data is not available.".format(key, dx_name)
            result = 2.2 + dx_offset
        dx_result.log(msg)
        color_code_dict.update({key: color_code})
        diagnostic_msg.update({key: result})
        # dx_table = {dx_name + DX: diagnostic_msg}
    dx_table = create_dx_table(str(timestamp), SA_TEMP_RCX, diagnostic_msg, color_code_dict)

    return avg_set_point, dx_table, dx_result


def pre_conditions(message, dx_list, analysis, cur_time, dx_result):
    """
    Check for persistence of failure to meet pre-conditions for diagnostics.
    :param message:
    :param dx_list:
    :param analysis:
    :param cur_time:
    :param dx_result:
    :return:
    """
    diagnostic_msg = {}
    color_code_dict = {}
    for sensitivity in pre_condition_sensitivities:
        diagnostic_msg[sensitivity] = message
        color_code_dict[sensitivity] = GREY if message != FAN_OFF else WHITE

    for diagnostic in dx_list:
        # dx_table = {diagnostic + DX: dx_msg}
        # table_key = create_table_key(analysis, cur_time)
        dx_table = create_dx_table(cur_time, diagnostic, diagnostic_msg, color_code_dict)
        dx_result.insert_table_row(analysis, dx_table)
    return dx_result


class Application(DrivenApplicationBaseClass):
    """
    Air-side HVAC Auto-Retuning Diagnostics
    for AHUs
    """
    fan_status_name = 'fan_status'
    zn_reheat_name = 'zn_reheat'
    zn_damper_name = 'zn_damper'
    fan_sp_name = 'fan_sp'
    sat_name = 'sat'
    sat_stpt_name = 'sat_stpt'

    def __init__(self, *args,
                 a0_no_required_data=10, a1_data_window=30,
                 warm_up_time=30, a2_local_tz=1,
                 a3_sensitivity="all", b0_stpt_deviation_thr=10.0,
                 b1_rht_on_thr=10.0, b2_reheat_valve_thr=50.0,
                 b3_percent_reheat_thr=25.0, b4_sat_high_damper_thr=80.0,
                 b5_percent_damper_thr=50.0, b6_sat_reset_thr=5.0,
                 min_sat_stpt=50.0, sat_retuning=1.0,
                 max_sat_stpt=75.0,**kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.cur_tz = available_tz[a2_local_tz]
        except:
            self.cur_tz = "UTC"

        # Point names (Configurable)
        def get_or_none(name):
            value = kwargs["point_mapping"].get(name, None)
            if value:
                value = value.lower()
            return value

        auto_correct_flag = True
        self.warm_up_start = None
        self.warm_up_flag = True
        self.warm_up_time = td(minutes=warm_up_time)
        self.unit_status = None

        self.analysis = analysis = "Airside_RCx"
        sensitivity = a3_sensitivity.lower() if a3_sensitivity is not None else None

        if sensitivity not in ["all", "high", "normal", "low"]:
            sensitivity = None

        if self.fan_sp_name is None and self.fan_status_name is None:
            raise Exception("SupplyFanStatus or SupplyFanSpeed are required to verify AHU status.")
            sys.exit()

        no_required_data = a0_no_required_data
        self.data_window = td(minutes=a1_data_window) if a1_data_window != 0 else None
        self.low_sf_thr = 10.0

        if sensitivity is not None and sensitivity != "custom":
            # SAT AIRCx Thresholds
            stpt_deviation_thr = {
                "low": b0_stpt_deviation_thr * 1.5,
                "normal": b0_stpt_deviation_thr,
                "high": b0_stpt_deviation_thr * 0.5
            }
            percent_reheat_thr = {
                "low": b3_percent_reheat_thr,
                "normal": b3_percent_reheat_thr,
                "high": b3_percent_reheat_thr
            }
            percent_damper_thr = {
                "low": b5_percent_damper_thr + 15.0,
                "normal": b5_percent_damper_thr,
                "high": b5_percent_damper_thr - 15.0
            }
            reheat_valve_thr = {
                "low": b2_reheat_valve_thr * 1.5,
                "normal": b2_reheat_valve_thr,
                "high": b2_reheat_valve_thr * 0.5
            }
            sat_high_damper_thr = {
                "low": b4_sat_high_damper_thr + 15.0,
                "normal": b4_sat_high_damper_thr,
                "high": b4_sat_high_damper_thr - 15.0
            }
            sat_reset_thr = {
                "low": max(b6_sat_reset_thr - 2.0, 0.5),
                "normal": b6_sat_reset_thr,
                "high": b6_sat_reset_thr + 2.0
            }
            if sensitivity != "all":
                remove_sensitivities = [item for item in ["high", "normal", "low"] if item != sensitivity]
                if remove_sensitivities:
                    for remove in remove_sensitivities:
                        stpt_deviation_thr.pop(remove)
                        percent_reheat_thr.pop(remove)
                        percent_damper_thr.pop(remove)
                        reheat_valve_thr.pop(remove)
                        sat_high_damper_thr.pop(remove)
                        sat_reset_thr.pop(remove)
        else:
            stpt_deviation_thr = {"normal": b0_stpt_deviation_thr}
            percent_reheat_thr = {"normal": b3_percent_reheat_thr}
            percent_damper_thr = {"normal": b5_percent_damper_thr}
            reheat_valve_thr = {"normal": b2_reheat_valve_thr}
            sat_high_damper_thr = {"normal": b4_sat_high_damper_thr}
            sat_reset_thr = {"normal": b6_sat_reset_thr}

        global pre_condition_sensitivities
        pre_condition_sensitivities = stpt_deviation_thr.keys()

        self.sat_aircx = SupplyTempAIRCx(no_required_data, self.data_window,
                                         auto_correct_flag, stpt_deviation_thr,
                                         b1_rht_on_thr, sat_high_damper_thr,
                                         percent_damper_thr, percent_reheat_thr,
                                         min_sat_stpt, sat_retuning,
                                         reheat_valve_thr, max_sat_stpt,
                                         analysis, self.sat_stpt_name)

        self.satr_reset_aircx = SatResetAIRCx(a0_no_required_data, sat_reset_thr, analysis)

    @classmethod
    def get_config_parameters(cls):
        """
        Generate required configuration
        parameters with description for user
        """
        return {
            'a0_no_required_data':
            ConfigDescriptor(int,
                             'Number of required data measurements to perform diagnostic',
                             value_default=10),
            'a1_data_window':
            ConfigDescriptor(int,
                             'Minimum elapsed time for analysis (minutes). '
                             'The default value of 0 will produce hourly results',
                             value_default=0),
            'a2_local_tz':
             ConfigDescriptor(int,
                              "Integer corresponding to local time zone: [1: 'US/Pacific', 2: 'US/Mountain', 3: 'US/Central', 4: 'US/Eastern']",
                              value_default=1),
            'a3_sensitivity':
            ConfigDescriptor(str,
                             'Sensitivity: values can be all (produces a result for low, normal, and high), '
                             'low, normal, high, or custom. Setting sensitivity to custom allows you to customize your '
                             'all threshold values',
                             value_default="all"),
            # 'warm_up_time':
            # ConfigDescriptor(int,
            #                 'When the system starts this much '
            #                 'time will be allowed to elapse before adding '
            #                 'using data for analysis (minutes)',
            #                 value_default=30),
            'b0_stpt_deviation_thr':
            ConfigDescriptor(float,
                             'Allowable deviation from set points '
                             'before a fault message is generated '
                             '(%)', value_default=10.0),
            'b1_rht_on_thr':
             ConfigDescriptor(float,
                             'Minimum reheat command for zone reheat to be considered ON (%)',
                              value_default=10.0),

            'b2_reheat_valve_thr':
            ConfigDescriptor(float,
                             "'Low Supply-air Temperature Dx' – average zone reheat valve command threshold",
                             value_default=50.0),
            'b3_percent_reheat_thr':
            ConfigDescriptor(float,
                             ('Threshold for average percent of zones where terminal box reheat is ON (%)'),
                             value_default=25.0),
            'b4_sat_high_damper_thr':
            ConfigDescriptor(float,
                             "'High Supply-air Temperature Dx' - threshold for determining when zone dampers are commanded to value higher than optimum [high zone damper threshold] (%)",
                             value_default=80),
            'b5_percent_damper_thr':
            ConfigDescriptor(float,
                             "'High Supply-air Temperature Dx' - threshold for determining when the average percent of zones dampers are commanded to value higher than optimum (%)",
                             value_default=50.0),
            'b6_sat_reset_thr':
            ConfigDescriptor(float,
                             "'No Supply Temperature Reset Dx' - the required difference between the minimum and the maximum supply-air temperature set point for detection of a supply-air temperature set point reset ({drg}F)".format(drg=DGR_SYM),
                             value_default=3.0)
            }

    @classmethod
    def get_self_descriptor(cls):
        """Name and description for of application for UI"""
        name = 'AIRCx for AHUs: Supply Temperature'
        desc = 'AIRCx for AHUs: Supply Temperature'
        note = 'Sensitivity: value can be all, low, normal, high, or custom. ' \
               'Setting values of all, low, normal, or high will ' \
               'ignore other threshold values.'
        return Descriptor(name=name, description=desc, note=note)

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
            cls.fan_sp_name:
            InputDescriptor('SupplyFanSpeed',
                            'AHU supply fan speed', count_min=0),
            cls.zn_reheat_name:
            InputDescriptor('TerminalBoxReheatValvePosition',
                            'All terminal-box re-heat valve commands',
                            count_min=1),
            cls.zn_damper_name:
            InputDescriptor('TerminalBoxDamperCommand',
                            'All terminal-box damper commands', count_min=1),

            cls.sat_name:
            InputDescriptor('DischargeAirTemperature', 'AHU supply-air '
                            '(discharge-air) temperature', count_min=1),
            cls.sat_stpt_name:
            InputDescriptor('DischargeAirTemperatureSetPoint',
                            'Supply-air temperature set-point', count_min=1)
            }

    def reports(self):
        """
        Called by UI to assemble information for creation of the diagnostic
        visualization.
        """
        report = reports.Report('Retuning Report')
        report.add_element(reports.RxSupplyTemp(table_name='Airside_RCx'))
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
        diagnostic_name = '/'.join(output_topic_base + ['Airside_RCx', 'diagnostic_name'])
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

    def run(self, cur_time, points):

        to_zone = dateutil.tz.gettz(self.cur_tz)
        cur_time = cur_time.astimezone(to_zone)
        device_dict = {}
        dx_result = Results()

        for key, value in points.items():
            point_device = [_name.lower() for _name in key.split("&&&")]
            if point_device[0] not in device_dict:
                device_dict[point_device[0]] = [(point_device[1], value)]
            else:
                device_dict[point_device[0]].append((point_device[1], value))

        fan_status_data = []
        fan_sp_data = []
        zn_dmpr_data = []
        sat_data = []
        zn_rht_data = []
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
            if data_name == self.fan_status_name:
                fan_status_data = data_builder(value, data_name)
            elif data_name == self.fan_sp_name:
                fan_sp_data = data_builder(value, data_name)
            elif data_name == self.sat_stpt_name:
                sat_stpt_data = data_builder(value, data_name)
            elif data_name == self.sat_name:
                sat_data = data_builder(value, data_name)
            elif data_name == self.zn_reheat_name:
                zn_rht_data = data_builder(value, data_name)
            elif data_name == self.zn_damper_name:
                zn_dmpr_data = data_builder(value, data_name)

        missing_data = []
        if not sat_data:
            missing_data.append(self.sat_name)
        if not zn_rht_data:
            missing_data.append(self.zn_reheat_name)
        if not sat_stpt_data:
            dx_result.log('Supply-air temperature set point data is '
                          'missing. This will limit the effectiveness of '
                          'the supply-air temperature diagnostics.')
        if not fan_status_data and not fan_sp_data:
            missing_data.append(self.fan_status_name)
        if not zn_dmpr_data:
            missing_data.append(self.zn_damper_name)

        if missing_data:
            dx_result.log('Missing required data: {}'.format(missing_data))
            return dx_result

        current_fan_status, fan_sp = self.check_fan_status(fan_status_data, fan_sp_data, cur_time)
        dx_result = self.check_elapsed_time(dx_result, cur_time, self.unit_status, FAN_OFF)

        if not current_fan_status:
            dx_result.log("Supply fan is off: {}".format(cur_time))
            self.warm_up_flag = True
            return dx_result

        dx_result.log("Supply fan is on: {}".format(cur_time))

        if self.warm_up_flag:
            self.warm_up_flag = False
            self.warm_up_start = cur_time
            return dx_result

        if self.warm_up_start is not None and (cur_time - self.warm_up_start) < self.warm_up_time:
            dx_result.log("Unit is in warm-up. Data will not be analyzed.")
            return dx_result

        dx_result = self.satr_reset_aircx.sat_reset_aircx(cur_time, sat_stpt_data, dx_result)
        dx_result = self.sat_aircx.sat_aircx(cur_time, sat_data, sat_stpt_data,
                                             zn_rht_data, zn_dmpr_data, dx_result)
        return dx_result

    def check_fan_status(self, fan_status_data, fan_sp_data, cur_time):
        """
        :param fan_status_data:
        :param fan_sp_data:
        :param cur_time:
        :return:
        """
        supply_fan_status = int(max(fan_status_data)) if fan_status_data else None

        fan_speed = mean(fan_sp_data) if fan_sp_data else None
        if supply_fan_status is None:
            supply_fan_status = 1 if fan_speed > self.low_sf_thr else 0

        if not supply_fan_status:
            if self.unit_status is None:
                self.unit_status = cur_time
        else:
            self.unit_status = None
        return supply_fan_status, fan_speed

    def check_elapsed_time(self, dx_result, cur_time, condition, message):
        """
        Check for persistence of failure to meet pre-conditions for diagnostics.
        :param dx_result:
        :param cur_time:
        :param condition:
        :param message:
        :return:
        """
        elapsed_time = cur_time - condition if condition is not None else td(minutes=0)
        if self.data_window is not None and elapsed_time >= self.data_window:
            dx_result = pre_conditions(message, DX_LIST, self.analysis, cur_time, dx_result)
            self.clear_all()
        elif condition is not None and condition.hour != cur_time.hour:
            message_time = condition.replace(minute=0)
            dx_result = pre_conditions(message, DX_LIST, self.analysis, message_time, dx_result)
            self.clear_all()
        return dx_result

    def clear_all(self):
        self.sat_aircx.reinitialize()
        self.warm_up_start = None
        self.warm_up_flag = True
        self.unit_status = None


class SupplyTempAIRCx(object):
    """Air-side HVAC Self-Correcting Diagnostic: Detect and correct supply-air
    temperature problems.
    Args:
        timestamp_array (List[datetime]): timestamps for analysis period.
        sat_stpt_arr (List[float]): supply-air temperature set point
            for analysis period.
        satemp_arr (List[float]): supply-air temperature for analysis period.
        rht_arr (List[float]): terminal box reheat command for analysis period.
    """
    def __init__(self, no_req_data, data_window, auto_correct_flag,
                 stpt_deviation_thr, rht_on_thr, high_dmpr_thr, percent_dmpr_thr,
                 percent_rht_thr, min_sat_stpt, sat_retuning, rht_valve_thr,
                 max_sat_stpt, analysis, sat_stpt_cname):
        self.timestamp_array = []
        self.sat_stpt_array = []
        self.sat_array = []
        self.rht_array = []
        self.percent_rht = []
        self.percent_dmpr = defaultdict(list)
        # self.table_key = None

        # Common RCx parameters
        self.analysis = analysis
        self.data_window = data_window
        self.sat_stpt_cname = sat_stpt_cname
        self.no_req_data = no_req_data
        self.auto_correct_flag = bool(auto_correct_flag)
        self.stpt_deviation_thr = stpt_deviation_thr
        self.rht_on_thr = rht_on_thr
        self.percent_rht_thr = percent_rht_thr

        # Low SAT RCx thresholds
        self.rht_valve_thr = rht_valve_thr
        self.max_sat_stpt = max_sat_stpt

        # High SAT RCx thresholds
        self.high_dmpr_thr = high_dmpr_thr
        self.percent_dmpr_thr = percent_dmpr_thr
        self.min_sat_stpt = min_sat_stpt
        self.sat_retuning = sat_retuning
        self.dx_offset = 30.0

    def reinitialize(self):
        """
        Reinitialize data arrays.
        :return:
        """
        self.table_key = None
        self.timestamp_array = []
        self.sat_stpt_array = []
        self.sat_array = []
        self.rht_array = []
        self.percent_rht = []
        self.percent_dmpr = defaultdict(list)

    def sat_aircx(self, current_time, sat_data, sat_stpt_data,
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
        tot_rht = sum(1. if val > self.rht_on_thr else 0. for val in zone_rht_data)
        count_rht = len(zone_rht_data)
        tot_dmpr = {}
        for key, thr in self.high_dmpr_thr.items():
            tot_dmpr[key] = sum(1. if val > thr else 0. for val in zone_dmpr_data)
        count_damper = len(zone_dmpr_data)
        try:
            if check_date(current_time, self.timestamp_array):
                dx_result = pre_conditions(INCONSISTENT_DATE, DX_LIST, self.analysis, current_time, dx_result)
                self.reinitialize()
                return dx_result

            run_status = check_run_status(self.timestamp_array, current_time, self.no_req_data, self.data_window)

            if run_status is None:
                dx_result.log("{} - Insufficient data to produce a valid diagnostic result.".format(current_time))
                dx_result = pre_conditions(INSUFFICIENT_DATA, DX_LIST, self.analysis, current_time, dx_result)
                self.reinitialize()
                return dx_result

            if run_status:
                self.table_key = create_table_key(self.analysis, self.timestamp_array[-1])
                avg_sat_stpt, dx_table, dx_result = setpoint_control_check(self.sat_stpt_array, self.sat_array,
                                                                           self.stpt_deviation_thr, SA_TEMP_RCX,
                                                                           self.dx_offset, self.timestamp_array[-1],
                                                                           dx_result)
                # dx_result.insert_table_row(self.table_key, dx_table)
                dx_result.insert_table_row(self.analysis, dx_table)
                dx_result = self.low_sat(dx_result, avg_sat_stpt)
                dx_result = self.high_sat(dx_result, avg_sat_stpt)
                self.reinitialize()
            return dx_result
        finally:
            self.sat_array.append(mean(sat_data))
            self.rht_array.append(mean(zone_rht_data))
            self.sat_stpt_array.append(mean(sat_stpt_data))
            self.percent_rht.append(tot_rht/count_rht)
            self.timestamp_array.append(current_time)
            for key in self.high_dmpr_thr:
                self.percent_dmpr[key].append(tot_dmpr[key]/count_damper)

    def low_sat(self, dx_result, avg_sat_stpt):
        """
        Diagnostic to identify and correct low supply-air temperature
        (correction by modifying SAT set point).
        :param dx_result:
        :param avg_sat_stpt:
        :return:
        """
        avg_zones_rht = mean(self.percent_rht)*100.0
        rht_avg = mean(self.rht_array)
        thresholds = zip(self.rht_valve_thr .items(), self.percent_rht_thr.items())
        diagnostic_msg = {}
        color_code_dict = {}

        for (key, rht_valve_thr), (key2, percent_rht_thr) in thresholds:
            if rht_avg > rht_valve_thr and avg_zones_rht > percent_rht_thr:
                if avg_sat_stpt is None:
                    # Create diagnostic message for fault
                    # when supply-air temperature set point
                    # is not available.
                    msg = "{} - The SAT too low but SAT set point data is not available.".format(key)
                    color_code = RED
                    result = 44.1
                elif self.auto_correct_flag:
                    aircx_sat_stpt = avg_sat_stpt + self.sat_retuning
                    if aircx_sat_stpt <= self.max_sat_stpt:
                        dx_result.command(self.sat_stpt_cname, aircx_sat_stpt)
                        sat_stpt = "%s" % float("%.2g" % aircx_sat_stpt)
                        msg = "{} - SAT too low. SAT set point increased to: {}{}F".format(key, DGR_SYM, sat_stpt)
                        color_code = RED
                        result = 41.1
                    else:
                        dx_result.command(self.sat_stpt_cname, self.max_sat_stpt)
                        sat_stpt = "%s" % float("%.2g" % self.max_sat_stpt)
                        sat_stpt = str(sat_stpt)
                        msg = "{} - SAT too low. Auto-correcting to max SAT set point {}{}F".format(key,
                                                                                                    DGR_SYM,
                                                                                                    sat_stpt)
                        color_code = RED
                        result = 42.1
                else:
                    msg = "{} - SAT detected to be too low but auto-correction is not enabled.".format(key)
                    color_code = RED
                    result = 43.1
            else:
                msg = "{} - No retuning opportunities detected for Low SAT diagnostic.".format(key)
                color_code = GREEN
                result = 40.0
            color_code_dict.update({key: color_code})
            diagnostic_msg.update({key: result})
            dx_result.log(msg)

        dx_table = create_dx_table(str(self.timestamp_array[-1]), SA_TEMP_RCX1, diagnostic_msg, color_code_dict)
        dx_result.insert_table_row(self.analysis, dx_table)
        # dx_result.insert_table_row(self.table_key, {SA_TEMP_RCX1 + DX: diagnostic_msg})
        return dx_result

    def high_sat(self, dx_result, avg_sat_stpt):
        """
        Diagnostic to identify and correct high supply-air temperature
        (correction by modifying SAT set point).
        :param dx_result:
        :param avg_sat_stpt:
        :return:
        """
        avg_zones_rht = mean(self.percent_rht)*100.0
        thresholds = zip(self.percent_dmpr_thr.items(), self.percent_rht_thr.items())
        diagnostic_msg = {}
        color_code_dict = {}

        for (key, percent_dmpr_thr), (key2, percent_rht_thr) in thresholds:
            avg_zone_dmpr_data = mean(self.percent_dmpr[key]) * 100.0
            if avg_zone_dmpr_data > percent_dmpr_thr and avg_zones_rht < percent_rht_thr:
                if avg_sat_stpt is None:
                    # Create diagnostic message for fault
                    # when supply-air temperature set point
                    # is not available.
                    color_code = RED
                    msg = "{} - The SAT too low but SAT set point data is not available.".format(key)
                    result = 54.1
                elif self.auto_correct_flag:
                    aircx_sat_stpt = avg_sat_stpt - self.sat_retuning
                    # Create diagnostic message for fault condition
                    # with auto-correction
                    if aircx_sat_stpt >= self.min_sat_stpt:
                        dx_result.command(self.sat_stpt_cname, aircx_sat_stpt)
                        sat_stpt = "%s" % float("%.2g" % aircx_sat_stpt)
                        msg = "{} - SAT too high. SAT set point decreased to: {}{}F".format(key, DGR_SYM, sat_stpt)
                        color_code = RED
                        result = 51.1
                    else:
                        # Create diagnostic message for fault condition
                        # where the maximum SAT has been reached
                        dx_result.command(self.sat_stpt_cname, self.min_sat_stpt)
                        sat_stpt = "%s" % float("%.2g" % self.min_sat_stpt)
                        msg = "{} - SAT too high. Auto-correcting to min SAT set point {}{}F".format(key,
                                                                                                     DGR_SYM,
                                                                                                     sat_stpt)
                        color_code = RED
                        result = 52.1
                else:
                    # Create diagnostic message for fault condition
                    # without auto-correction
                    msg = "{} - The SAT too high but auto-correction is not enabled.".format(key)
                    color_code = RED
                    result = 53.1
            else:
                msg = "{} - No problem detected for High SAT diagnostic.".format(key)
                color_code = GREEN
                result = 50.0
            color_code_dict.update({key: color_code})
            diagnostic_msg.update({key: result})
            dx_result.log(msg)

        dx_table = create_dx_table(str(self.timestamp_array[-1]), SA_TEMP_RCX2, diagnostic_msg, color_code_dict)
        dx_result.insert_table_row(self.analysis, dx_table)
        # dx_result.insert_table_row(self.table_key, {SA_TEMP_RCX2 + DX: diagnostic_msg})
        return dx_result


class SatResetAIRCx(object):
    """
    Operational schedule, supply-air temperature set point reset, and duct static pressure reset
    AIRCx for AHUs or RTUs.
    """
    def __init__(self, no_req_data, sat_reset_thr, analysis):
        self.sat_stpt_array = []
        self.reset_table_key = None
        self.timestamp_array = []
        self.analysis = analysis
        # self.dx_table = {}

        # Application thresholds (Configurable)
        self.no_req_data = no_req_data
        self.sat_reset_thr = sat_reset_thr

    def sat_reset_aircx(self, current_time, sat_stpt_data, dx_result):
        """
        Main function for set point reset AIRCx - manages data arrays checks AIRCx run status.
        :param current_time:
        :param current_fan_status:
        :param stcpr_stpt_data:
        :param sat_stpt_data:
        :param dx_result:
        :return:
        """
        try:
            sat_run_status = check_run_status(self.timestamp_array, current_time, self.no_req_data,
                                              run_schedule="daily", minimum_point_array=self.sat_stpt_array)

            if sat_run_status is None:
                dx_result.log("{} - Insufficient data to produce - {}".format(current_time, SA_TEMP_RCX3))
                dx_result = pre_conditions(INSUFFICIENT_DATA, [SA_TEMP_RCX3], self.analysis, current_time, dx_result)
                self.sat_stpt_array = []
                self.timestamp_array = []
            elif sat_run_status:
                dx_result = self.no_sat_stpt_reset(dx_result)
                self.sat_stpt_array = []
                self.timestamp_array = []

            return dx_result

        finally:
            self.timestamp_array.append(current_time)
            if sat_stpt_data:
                self.sat_stpt_array.append(mean(sat_stpt_data))

    def no_sat_stpt_reset(self, dx_result):
        """
        AIRCx to detect whether a supply-air temperature set point reset is implemented.
        :param dx_result:
        :return:
        """
        diagnostic_msg = {}
        color_code_dict = {}
        sat_daily_range = max(self.sat_stpt_array) - min(self.sat_stpt_array)
        for key, reset_thr in self.sat_reset_thr.items():
            if sat_daily_range < reset_thr:
                msg = "{} - SAT reset was not detected.  This can result in excess energy consumption.".format(key)
                result = 81.1
                color_code = RED
            else:
                msg = "{} - No problems detected for SAT set point reset diagnostic.".format(key)
                result = 80.0
                color_code = GREEN
            dx_result.log(msg)
            diagnostic_msg.update({key: result})
            color_code_dict.update({key: color_code})

        dx_table = create_dx_table(str(self.timestamp_array[-1]), SA_TEMP_RCX3, diagnostic_msg, color_code_dict)
        dx_result.insert_table_row(self.analysis, dx_table)
        # dx_result.insert_table_row(self.reset_table_key, {SA_TEMP_RCX3 + DX:  diagnostic_msg})
        return dx_result
