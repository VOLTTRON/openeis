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
import math
from datetime import timedelta as td
import sys
import dateutil.tz
from numpy import mean
from openeis.applications import (DrivenApplicationBaseClass,
                                  OutputDescriptor,
                                  ConfigDescriptor,
                                  InputDescriptor,
                                  Results,
                                  Descriptor,
                                  reports)

FAN_OFF = -99.3
INCONSISTENT_DATE = -89.2
INSUFFICIENT_DATA = -79.2
RED = "RED"
GREY = "GREY"
GREEN = "GREEN"
DUCT_STC_RCX = "Duct Static Pressure Control Loop Dx"
DUCT_STC_RCX1 = "Low Duct Static Pressure Dx"
DUCT_STC_RCX2 = "High Duct Static Pressure Dx"
DUCT_STC_RCX3 = "No Static Pressure Reset Dx"
DX = "/diagnostic message"

DX_LIST = [DUCT_STC_RCX, DUCT_STC_RCX1, DUCT_STC_RCX2]
__version__ = "1.0.6"

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

    if minimum_diagnostic_time is not None and timestamp_array:
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
                msg = " {} - No problem detected or {} set".format(key, dx_name)
                result = 0.0 + dx_offset
        else:
            color_code = GREY
            msg = "{} - {} set point data is not available.".format(key, dx_name)
            result = 2.2 + dx_offset
        dx_result.log(msg)
        color_code_dict.update({key: color_code})
        diagnostic_msg.update({key: result})
        # dx_table = {dx_name + DX: diagnostic_msg}
    dx_table = create_dx_table(str(timestamp), DUCT_STC_RCX, diagnostic_msg, color_code_dict)

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
    dx_msg = {'low': message, 'normal': message, 'high': message}
    color_code_dict = {'low': GREY, 'normal': GREY, 'high': GREY}
    for diagnostic in dx_list:
        # dx_table = {diagnostic + DX: dx_msg}
        # table_key = create_table_key(analysis, cur_time)
        dx_table = create_dx_table(cur_time, diagnostic, dx_msg, color_code_dict)
        dx_result.insert_table_row(analysis, dx_table)
    return dx_result


class Application(DrivenApplicationBaseClass):
    """
    Air-side HVAC Auto-Retuning Diagnostics
    for AHUs
    """
    fan_status_name = 'fan_status'
    zn_damper_name = 'zone_damper'
    fan_sp_name = 'fan_speedcmd'
    duct_stcpr_name = 'duct_stp'
    duct_stcpr_stpt_name = 'duct_stcpr_stpt'

    def __init__(self, *args, a0_no_required_data=10, a1_data_window=0,
                 a2_local_tz=1, a3_sensitivity="all", warm_up_time=15,

                 stcpr_retuning=0.15, max_duct_stcpr_stpt=2.5,
                 high_sf_thr=95.0,
                 b1_zn_high_damper_thr=90.0,
                 b2_zn_low_damper_thr=10.0, min_duct_stcpr_stpt=0.2,
                 b3_hdzn_damper_thr=30.0, low_sf_thr=10.0,
                 b0_stpt_deviation_thr=10.0,
                 b4_stcpr_reset_thr=0.25, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.cur_tz = available_tz[a2_local_tz]
        except:
            self.cur_tz = 'UTC'

        # Point names (Configurable)
        def get_or_none(name):
            value = kwargs["point_mapping"].get(name, None)
            if value:
                value = value.lower()
            return value

        self.warm_up_start = None
        self.warm_up_flag = True
        self.unit_status = None
        self.analysis  = "Airside_RCx"
        sensitivity = a3_sensitivity.lower() if a3_sensitivity is not None else None

        if sensitivity not in ["all", "high", "normal", "low"]:
            sensitivity = None

        if self.fan_sp_name is None and self.fan_status_name is None:
            raise Exception("SupplyFanStatus or SupplyFanSpeed are required to verify AHU status.")
            sys.exit()

        # Application thresholds (Configurable)
        self.data_window = td(minutes=a1_data_window) if a1_data_window != 0 else None
        self.low_sf_thr = float(low_sf_thr)
        self.high_sf_thr = float(high_sf_thr)
        self.warm_up_flag = None
        self.warm_up_time = td(minutes=warm_up_time)
        self.warm_up_start = None
        auto_correct_flag = True
        analysis = "Airside_RCx"
        stcpr_cname = self.duct_stcpr_stpt_name

        if sensitivity is not None and sensitivity != "custom":
            # SAT AIRCx Thresholds
            stpt_deviation_thr = {
                "low": b0_stpt_deviation_thr * 1.5,
                "normal": b0_stpt_deviation_thr,
                "high": b0_stpt_deviation_thr * 0.5
            }
            zn_high_damper_thr = {
                "low": b1_zn_high_damper_thr + 5.0,
                "normal": b1_zn_high_damper_thr,
                "high": b1_zn_high_damper_thr - 5.0
            }
            zn_low_damper_thr = {
                "low": b2_zn_low_damper_thr + 5.0,
                "normal": b2_zn_low_damper_thr,
                "high": b2_zn_low_damper_thr - 5.0
            }
            hdzn_damper_thr = {
                "low": b3_hdzn_damper_thr - 5.0,
                "normal": b3_hdzn_damper_thr,
                "high": b3_hdzn_damper_thr + 5.0
            }
            stcpr_reset_thr = {
                "low": b4_stcpr_reset_thr * 1.5,
                "normal": b4_stcpr_reset_thr,
                "high": b4_stcpr_reset_thr * 0.5
            }

            if sensitivity != "all":
                remove_sensitivities = [item for item in ["high", "normal", "low"] if item != sensitivity]
                if remove_sensitivities:
                    for remove in remove_sensitivities:
                        stpt_deviation_thr.pop(remove)
                        zn_high_damper_thr.pop(remove)
                        zn_low_damper_thr.pop(remove)
                        stcpr_reset_thr.pop(remove)

        else:
            stpt_deviation_thr = {"normal": b0_stpt_deviation_thr}
            zn_high_damper_thr = {"normal": b1_zn_high_damper_thr}
            zn_low_damper_thr = {"normal": b2_zn_low_damper_thr}
            hdzn_damper_thr = {"normal": b3_hdzn_damper_thr}
            stcpr_reset_thr = {"normal": b4_stcpr_reset_thr}

        self.stcpr_aircx = DuctStaticAIRCx(
            a0_no_required_data, self.data_window,
            auto_correct_flag, stpt_deviation_thr,
            max_duct_stcpr_stpt, stcpr_retuning,
            zn_high_damper_thr, zn_low_damper_thr,
            hdzn_damper_thr, min_duct_stcpr_stpt,
            analysis, stcpr_cname)

        self.stcpr_reset_aircx = StcprResetAIRCx(a0_no_required_data, stcpr_reset_thr, analysis)

    @classmethod
    def get_config_parameters(cls):
        """
        Generate required configuration
        parameters with description for user
        :return:
        """
        dgr_sym = u'\N{DEGREE SIGN}'
        return {
            'a3_sensitivity':
            ConfigDescriptor(str,
                             'Sensitivity: values can be all (produces a result for low, normal, and high), '
                             'low, normal, high, or custom. Setting sensitivity to custom allows you to customize your '
                             'all threshold values',
                             value_default="all"),
            'a0_no_required_data':
            ConfigDescriptor(int,
                             'Number of required data measurements to perform diagnostic',
                             value_default=10),
            'a1_data_window':
            ConfigDescriptor(int,
                             'Minimum elapsed time for analysis (minutes).  A default value of 0 will produce hourly results',
                             value_default=0),
            'a2_local_tz':
             ConfigDescriptor(int,
                              "Integer corresponding to local time zone: [1: 'US/Pacific', 2: 'US/Mountain', 3: 'US/Central', 4: 'US/Eastern']",
                               value_default=1),

            'b0_stpt_deviation_thr':
            ConfigDescriptor(float,
                             "'Duct Static Pressure Set Point Control Loop Dx' - '"
                             "the allowable percent deviation from the set point for the duct static pressure",
                             value_default=10.0),
            'b1_zn_high_damper_thr':
            ConfigDescriptor(float,
                             ("'Low Duct Static Pressure Dx'- zone high damper threshold (%)"),
                             value_default=90.0),
            'b2_zn_low_damper_thr':
            ConfigDescriptor(float,
                             ("'Low Duct Static Pressure Dx' - zone low damper threshold (%)"),
                             value_default=10.0),
            'b3_hdzn_damper_thr':
            ConfigDescriptor(float,
                             "'High Duct Static Pressure Dx' - zone damper threshold (%)",
                             value_default=30.0),
            'b4_stcpr_reset_thr':
            ConfigDescriptor(float,
                             "'No Static Pressure Reset Dx' - the required difference between the minimum and the maximum duct static pressure set point for detection of a duct static pressure set point reset (inch w.g.)",
                             value_default=0.25)
            }

    @classmethod
    def get_self_descriptor(cls):
        name = 'AIRCx for AHUs: Static Pressure'
        desc = 'AIRCx for AHUs: Static Pressure'
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
            cls.zn_damper_name:
            InputDescriptor('TerminalBoxDamperCommand',
                            'All terminal-box damper commands', count_min=1),
            cls.duct_stcpr_name:
            InputDescriptor('DuctStaticPressure', 'AHU duct static pressure',
                            count_min=1),
            cls.duct_stcpr_stpt_name:
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
        dx_result = Results()

        for key, value in points.items():
            point_device = [_name.lower() for _name in key.split("&&&")]
            if point_device[0] not in device_dict:
                device_dict[point_device[0]] = [(point_device[1], value)]
            else:
                device_dict[point_device[0]].append((point_device[1], value))

        fan_status_data = []
        fan_sp_data = []
        stc_pr_data = []
        stcpr_stpt_data = []
        zn_dmpr_data = []

        for key, value in device_dict.items():
            data_name = key
            if value is None:
                continue
            if data_name == self.fan_status_name:
                fan_status_data = data_builder(value, data_name)
            elif data_name == self.fan_sp_name:
                fan_sp_data = data_builder(value, data_name)
            elif data_name == self.duct_stcpr_stpt_name:
                stcpr_stpt_data = data_builder(value, data_name)
            elif data_name == self.duct_stcpr_name:
                stc_pr_data = data_builder(value, data_name)
            elif data_name == self.zn_damper_name:
                zn_dmpr_data = data_builder(value, data_name)

        missing_data = []
        if not stc_pr_data:
            missing_data.append(self.duct_stcpr_name)
        if not stcpr_stpt_data:
            dx_result.log('Duct static pressure set point data is '
                          'missing. This will limit the effectiveness of '
                          'the duct static pressure diagnostics.')
        missing_data = []
        if not fan_status_data and not fan_sp_data:
            missing_data.append(self.fan_status_name)
        if not stc_pr_data:
            missing_data.append(self.duct_stcpr_name)
        if not stcpr_stpt_data:
            dx_result.log("Duct static pressure set point data is missing.")
        if not zn_dmpr_data:
            missing_data.append(self.zn_damper_name)

        if missing_data:
            dx_result.log("Missing data from publish: {}".format(missing_data))
            return dx_result

        current_fan_status, fan_sp = self.check_fan_status(fan_status_data, fan_sp_data, cur_time)
        dx_result = self.check_elapsed_time(dx_result, cur_time, self.unit_status, FAN_OFF)

        if not current_fan_status:
            dx_result.log("Supply fan is off: {}".format(cur_time))
            self.warm_up_flag = True
            return dx_result

        dx_result.log("Supply fan is on: {}".format(cur_time))

        low_sf_cond = True if fan_sp is not None and fan_sp > self.high_sf_thr else False
        high_sf_cond = True if fan_sp is not None and fan_sp < self.low_sf_thr else False

        if self.warm_up_flag:
            self.warm_up_flag = False
            self.warm_up_start = cur_time
            return dx_result

        if self.warm_up_start is not None and (cur_time - self.warm_up_start) < self.warm_up_time:
            dx_result.log("Unit is in warm-up. Data will not be analyzed.")
            return dx_result

        dx_result = self.stcpr_aircx.stcpr_aircx(cur_time, stcpr_stpt_data, stc_pr_data,
                                                 zn_dmpr_data, low_sf_cond, high_sf_cond,
                                                 dx_result)
        dx_result = self.stcpr_reset_aircx.stcpr_reset_aircx(cur_time, current_fan_status,
                                                             stcpr_stpt_data, dx_result)

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
        if self.data_window is not None:
            if elapsed_time >= self.data_window:
                dx_result = pre_conditions(message, DX_LIST, self.analysis, cur_time, dx_result)
                self.clear_all()
        elif condition is not None and condition.hour != cur_time.hour:
            message_time = condition.replace(minute=0)
            dx_result = pre_conditions(message, DX_LIST, self.analysis, message_time, dx_result)
            self.clear_all()
        return dx_result

    def clear_all(self):
        self.stcpr_aircx.reinitialize()
        self.warm_up_start = None
        self.warm_up_flag = True
        self.unit_status = None

class DuctStaticAIRCx(object):
    """
    Air-side HVAC Self-Correcting Diagnostic: Detect and correct
    duct static pressure problems.
    """

    def __init__(self, no_req_data, data_window, auto_correct_flag,
                 stpt_deviation_thr, max_stcpr_stpt, stcpr_retuning,
                 zn_high_dmpr_thr, zn_low_dmpr_thr, hdzn_dmpr_thr,
                 min_stcpr_stpt, analysis, stcpr_stpt_cname):
        # Initialize data arrays
        self.table_key = None
        self.zn_dmpr_array = []
        self.stcpr_stpt_array = []
        self.stcpr_array = []
        self.timestamp_array = []

        # Initialize configurable thresholds
        self.analysis = analysis
        self.stcpr_stpt_cname = stcpr_stpt_cname
        self.no_req_data = no_req_data
        self.stpt_deviation_thr = stpt_deviation_thr
        self.max_stcpr_stpt = max_stcpr_stpt
        self.stcpr_retuning = stcpr_retuning
        self.zn_high_dmpr_thr = zn_high_dmpr_thr
        self.zn_low_dmpr_thr = zn_low_dmpr_thr
        self.data_window = data_window

        self.auto_correct_flag = auto_correct_flag
        self.min_stcpr_stpt = float(min_stcpr_stpt)
        self.hdzn_dmpr_thr = hdzn_dmpr_thr
        self.dx_offset = 0.0

    def reinitialize(self):
        """
        Reinitialize data arrays.
        :return:
        """
        self.table_key = None
        self.zn_dmpr_array = []
        self.stcpr_stpt_array = []
        self.stcpr_array = []
        self.timestamp_array = []

    def stcpr_aircx(self, current_time, stcpr_stpt_data, stcpr_data,
                    zn_dmpr_data, low_sf_cond, high_sf_cond, dx_result):
        """
        Check duct static pressure AIRCx pre-requisites and manage analysis data set.
        :param current_time:
        :param stcpr_stpt_data:
        :param stcpr_data:
        :param zn_dmpr_data:
        :param low_sf_cond:
        :param high_sf_cond:
        :param dx_result:
        :return:
        """
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
                avg_stcpr_stpt, dx_table, dx_result = setpoint_control_check(self.stcpr_stpt_array, self.stcpr_array,
                                                                             self.stpt_deviation_thr, DUCT_STC_RCX,
                                                                             self.dx_offset, self.timestamp_array[-1],
                                                                             dx_result)

                # dx_result.insert_table_row(self.table_key, dx_table)
                dx_result.insert_table_row(self.analysis, dx_table)
                dx_result = self.low_stcpr_aircx(dx_result, avg_stcpr_stpt, low_sf_cond)
                dx_result = self.high_stcpr_aircx(dx_result, avg_stcpr_stpt, high_sf_cond)
                self.reinitialize()
            return dx_result
        finally:
            self.stcpr_stpt_array.append(mean(stcpr_data))
            self.stcpr_array.append(mean(stcpr_stpt_data))
            self.zn_dmpr_array.append(mean(zn_dmpr_data))
            self.timestamp_array.append(current_time)

    def low_stcpr_aircx(self, dx_result, avg_stcpr_stpt, low_sf_condition):
        """
        AIRCx to identify and correct low duct static pressure.
        :param dx_result:
        :param avg_stcpr_stpt:
        :param low_sf_condition:
        :return:
        """
        zn_dmpr = self.zn_dmpr_array[:]
        zn_dmpr.sort(reverse=False)
        dmpr_low_temps = zn_dmpr[:int(math.ceil(len(self.zn_dmpr_array) * 0.5)) if len(self.zn_dmpr_array) != 1 else 1]
        dmpr_low_avg = mean(dmpr_low_temps)

        dmpr_high_temps = zn_dmpr[
                          int(math.ceil(len(self.zn_dmpr_array) * 0.5)) - 1 if len(self.zn_dmpr_array) != 1 else 0:]
        dmpr_high_avg = mean(dmpr_high_temps)
        thresholds = zip(self.zn_high_dmpr_thr.items(), self.zn_low_dmpr_thr.items())
        diagnostic_msg = {}
        color_code_dict = {}

        for (key, zn_high_dmpr_thr), (key2, zn_low_dmpr_thr) in thresholds:
            if dmpr_high_avg > zn_high_dmpr_thr and dmpr_low_avg > zn_low_dmpr_thr:
                if low_sf_condition is not None and low_sf_condition:
                    msg = "{} - duct static pressure too low. Supply fan at maximum.".format(key)
                    color_code = RED
                    result = 15.1
                elif avg_stcpr_stpt is None:
                    # Create diagnostic message for fault
                    # when duct static pressure set point
                    # is not available.
                    msg = "{} - duct static pressure is too low but set point data is not available.".format(key)
                    color_code = RED
                    result = 14.1
                elif self.auto_correct_flag:
                    aircx_stcpr_stpt = avg_stcpr_stpt + self.stcpr_retuning
                    if aircx_stcpr_stpt <= self.max_stcpr_stpt:
                        dx_result.command(self.stcpr_stpt_cname, aircx_stcpr_stpt)
                        stcpr_stpt = "%s" % float("%.2g" % aircx_stcpr_stpt)
                        stcpr_stpt = stcpr_stpt + " in. w.g."
                        msg = "{} - duct static pressure too low. Set point increased to: {}".format(key,
                                                                                                     stcpr_stpt)
                        color_code = RED
                        result = 11.1
                    else:
                        dx_result.command(self.stcpr_stpt_cname, self.max_stcpr_stpt)
                        stcpr_stpt = "%s" % float("%.2g" % self.max_stcpr_stpt)
                        stcpr_stpt = stcpr_stpt + " in. w.g."
                        msg = "{} - duct static pressure too low. Set point increased to max {}.".format(key,
                                                                                                         stcpr_stpt)
                        color_code = RED
                        result = 12.1
                else:
                    msg = "{} - duct static pressure is too low but auto-correction is not enabled.".format(key)
                    color_code = RED
                    result = 13.1
            else:
                msg = "{} - no retuning opportunities detected for Low duct static pressure diagnostic.".format(key)
                color_code = GREEN
                result = 10.0
            color_code_dict.update({key: color_code})
            diagnostic_msg.update({key: result})
            dx_result.log(msg)

        dx_table = create_dx_table(str(self.timestamp_array[-1]), DUCT_STC_RCX1, diagnostic_msg, color_code_dict)
        dx_result.insert_table_row(self.analysis, dx_table)
        # dx_result.insert_table_row(self.table_key, {DUCT_STC_RCX1 + DX: diagnostic_msg})
        return dx_result

    def high_stcpr_aircx(self, dx_result, avg_stcpr_stpt, high_sf_condition):
        """
        AIRCx to identify and correct high duct static pressure.
        :param dx_result:
        :param avg_stcpr_stpt:
        :param high_sf_condition:
        :return:
        """
        zn_dmpr = self.zn_dmpr_array[:]
        zn_dmpr.sort(reverse=True)
        zn_dmpr = zn_dmpr[:int(math.ceil(len(self.zn_dmpr_array) * 0.5)) if len(self.zn_dmpr_array) != 1 else 1]
        avg_zn_damper = mean(zn_dmpr)
        diagnostic_msg = {}
        color_code_dict = {}

        for key, hdzn_dmpr_thr in self.hdzn_dmpr_thr.items():
            if avg_zn_damper <= hdzn_dmpr_thr:
                if high_sf_condition is not None and high_sf_condition:
                    msg = "{} - duct static pressure too high. Supply fan at minimum.".format(key)
                    color_code = RED
                    result = 25.1
                elif avg_stcpr_stpt is None:
                    # Create diagnostic message for fault
                    # when duct static pressure set point
                    # is not available.
                    msg = "{} - duct static pressure is too high but set point data is not available.".format(key)
                    color_code = RED
                    result = 24.1
                elif self.auto_correct_flag:
                    aircx_stcpr_stpt = avg_stcpr_stpt - self.stcpr_retuning
                    if aircx_stcpr_stpt >= self.min_stcpr_stpt:
                        dx_result.command(self.stcpr_stpt_cname, aircx_stcpr_stpt)
                        stcpr_stpt = "%s" % float("%.2g" % aircx_stcpr_stpt)
                        stcpr_stpt = stcpr_stpt + " in. w.g."
                        msg = "{} - duct static pressure too high. Set point decreased to: {}".format(key,
                                                                                                      stcpr_stpt)
                        color_code = RED
                        result = 21.1
                    else:
                        dx_result.command(self.stcpr_stpt_cname, self.min_stcpr_stpt)
                        stcpr_stpt = "%s" % float("%.2g" % self.min_stcpr_stpt)
                        stcpr_stpt = stcpr_stpt + " in. w.g."
                        msg = "{} - duct static pressure too high. Set point decreased to min {}.".format(key,
                                                                                                          stcpr_stpt)
                        color_code = RED
                        result = 22.1
                else:
                    msg = "{} - duct static pressure is too high but auto-correction is not enabled.".format(key)
                    color_code = RED
                    result = 23.1
            else:
                msg = "{} - No retuning opportunities detected for high duct static pressure diagnostic.".format(key)
                color_code = GREEN
                result = 20.0
            color_code_dict.update({key: color_code})
            diagnostic_msg.update({key: result})
            dx_result.log(msg)

        dx_table = create_dx_table(str(self.timestamp_array[-1]), DUCT_STC_RCX2, diagnostic_msg, color_code_dict)
        dx_result.insert_table_row(self.analysis, dx_table)
        # dx_result.insert_table_row(self.table_key, {DUCT_STC_RCX2 + DX: diagnostic_msg})
        return dx_result


class StcprResetAIRCx(object):
    """
    Operational schedule, supply-air temperature set point reset, and duct static pressure reset
    AIRCx for AHUs or RTUs.
    """
    def __init__(self, no_req_data, stcpr_reset_thr, analysis):

        self.stcpr_stpt_array = []
        self.reset_table_key = None
        self.timestamp_array = []
        self.analysis = analysis
        # self.dx_table = {}

        # Application thresholds (Configurable)
        self.no_req_data = no_req_data
        self.stcpr_reset_thr = stcpr_reset_thr

    def stcpr_reset_aircx(self, current_time, current_fan_status, stcpr_stpt_data, dx_result):
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
            stcpr_run_status = check_run_status(self.timestamp_array, current_time, self.no_req_data,
                                                run_schedule="daily", minimum_point_array=self.stcpr_stpt_array)

            if not self.timestamp_array:
                return dx_result

            self.reset_table_key = reset_name = create_table_key(self.analysis, self.timestamp_array[0])
            if stcpr_run_status is None:
                dx_result.log("{} - Insufficient data to produce - {}".format(current_time, DUCT_STC_RCX3))
                dx_result = pre_conditions(INSUFFICIENT_DATA, [DUCT_STC_RCX3], self.analysis, current_time, dx_result)
                self.stcpr_stpt_array = []
                self.timestamp_array = []
            elif stcpr_run_status:
                dx_result = self.no_static_pr_reset(dx_result)
                self.stcpr_stpt_array = []
                self.timestamp_array = []

            return dx_result

        finally:
            self.timestamp_array.append(current_time)
            if current_fan_status:
                if stcpr_stpt_data:
                    self.stcpr_stpt_array.append(mean(stcpr_stpt_data))

    def no_static_pr_reset(self, dx_result):
        """
        AIRCx  to detect whether a static pressure set point reset is implemented.
        :param dx_result:
        :return:
        """
        diagnostic_msg = {}
        color_code_dict = {}
        stcpr_daily_range = max(self.stcpr_stpt_array) - min(self.stcpr_stpt_array)
        for key, stcpr_reset_thr in self.stcpr_reset_thr.items():
            if stcpr_daily_range < stcpr_reset_thr:
                msg = ("No duct static pressure reset detected. A duct static "
                       "pressure set point reset can save significant energy.")
                color_code = RED
                result = 71.1
            else:
                msg = ("{} - No problems detected for duct static pressure set point "
                       "reset diagnostic.".format(key))
                color_code = GREEN
                result = 70.0
            dx_result.log(msg)
            color_code_dict.update({key: color_code})
            diagnostic_msg.update({key: result})

        dx_table = create_dx_table(str(self.timestamp_array[-1]), DUCT_STC_RCX3, diagnostic_msg, color_code_dict)
        dx_result.insert_table_row(self.analysis, dx_table)
        # dx_result.insert_table_row(self.reset_table_key, {DUCT_STC_RCX3 + DX:  diagnostic_msg})
        return dx_result

