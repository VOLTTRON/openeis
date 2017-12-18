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
from numpy import mean
from datetime import datetime
from dateutil.parser import parse
import dateutil.tz
import collections
from openeis.applications import (DrivenApplicationBaseClass,
                                  OutputDescriptor,
                                  ConfigDescriptor,
                                  InputDescriptor,
                                  Results,
                                  Descriptor,
                                  reports)

available_tz = {1: 'US/Pacific', 2: 'US/Mountain', 3: 'US/Central', 4: 'US/Eastern'}

FAN_OFF = -99.3
INCONSISTENT_DATE = -89.2
INSUFFICIENT_DATA = -79.2
RED = "RED"
GREY = "GREY"
GREEN = "GREEN"
WHITE = "WHITE"

SCHED_RCX = 'Operational Schedule Dx'
DX = '/diagnostic message'


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
        sampling_interval = (timestamp_array[-1] - timestamp_array[0])/len(timestamp_array)
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
        dx_table = create_dx_table(cur_time, diagnostic, diagnostic_msg, "GREY")
        dx_result.insert_table_row(analysis, dx_table)
    return dx_result


class Application(DrivenApplicationBaseClass):
    """
    Air-side HVAC Auto-Retuning Diagnostics
    for AHUs.
    """
    fan_status_name = 'fan_status'
    fan_sp_name = 'fan_sp'
    duct_stcpr_name = 'duct_stcpr'

    def __init__(
            self, *args, no_required_data=10, a2_unocc_time_thr=30.0,
            a3_unocc_stcpr_thr=0.2, a1_local_tz=1, b0_monday_sch=['5:30', '18:30'],
            b1_tuesday_sch=['5:30', '18:30'], b2_wednesday_sch=['5:30', '18:30'],
            b3_thursday_sch=['5:30', '18:30'], b4_friday_sch=['5:30', '18:30'],
            b5_saturday_sch=['0:00', '0:00'], b6_sunday_sch=['0:00', '0:00'],
            a0_sensitivity="all", **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.cur_tz = available_tz[a1_local_tz]
        except:
            self.cur_tz = 'UTC'
        analysis = "Airside_RCx"
        self.low_sf_thr = 10.0
        no_required_data = int(no_required_data)
        sensitivity = a0_sensitivity.lower() if a0_sensitivity is not None else None
        self.unit_status = None
        if sensitivity is not None and sensitivity != "custom":
            unocc_stcpr_thr = {
                "low": a3_unocc_stcpr_thr * 1.5,
                "normal": a3_unocc_stcpr_thr,
                "high": a3_unocc_stcpr_thr * 0.625
            }
            unocc_time_thr = {
                "low": a2_unocc_time_thr * 1.5,
                "normal": a2_unocc_time_thr,
                "high": a2_unocc_time_thr * 0.5
            }

            if sensitivity != "all":
                remove_sensitivities = [item for item in ["high", "normal", "low"] if item != sensitivity]
                if remove_sensitivities:
                    for remove in remove_sensitivities:
                        unocc_time_thr.pop(remove)
                        unocc_stcpr_thr.pop(remove)
        else:
            unocc_stcpr_thr = {"normal": a3_unocc_stcpr_thr}
            unocc_time_thr = {"normal": a2_unocc_time_thr}

        global pre_condition_sensitivities
        pre_condition_sensitivities = unocc_stcpr_thr.keys()

        self.sched_aircx = ScheduleAIRCx(unocc_time_thr, unocc_stcpr_thr,
                                         b0_monday_sch, b1_tuesday_sch,
                                         b2_wednesday_sch, b3_thursday_sch,
                                         b4_friday_sch, b5_saturday_sch,
                                         b6_sunday_sch, no_required_data,
                                         analysis)
    @classmethod
    def get_config_parameters(cls):
        """
        Generate required configuration
        parameters with description for user
        """
        dgr_sym = u'\N{DEGREE SIGN}'
        config_dict = [

            ('a0_sensitivity',
             ConfigDescriptor(str,
                              'Sensitivity: values can be all (produces a result for low, normal, and high), '
                              'low, normal, high, or custom. Setting sensitivity to custom allows you to customize your '
                              'all threshold values',
                              value_default="all")),
            ('a1_local_tz',
             ConfigDescriptor(int,
                              "Integer corresponding to local timezone: [1: 'US/Pacific', 2: 'US/Mountain', 3: 'US/Central', 4: 'US/Eastern']",
                               value_default=1)),
            ('a2_unocc_time_thr',
            ConfigDescriptor(float,
                             'Threshold for acceptable unoccupied run-time percentage for AHU supply fan (%)',
                             value_default=30.0)),
            ('a3_unocc_stcpr_thr',
            ConfigDescriptor(float,
                             'Threshold for the AHU average static pressure during unoccupied periods (inch w.g.)',
                             value_default=0.2)),
            ('b0_monday_sch',
            ConfigDescriptor(str,
                             'Monday occupancy schedule for AHU',
                             value_default=['5:30', '18:30'])),
            ('b1_tuesday_sch',
            ConfigDescriptor(str,
                             'Tuesday occupancy schedule for AHU',
                             value_default=['5:30', '18:30'])),
            ('b2_wednesday_sch',
            ConfigDescriptor(str,
                             'Wednesday occupancy schedule for AHU',
                             value_default=['5:30', '18:30'])),
            ('b3_thursday_sch',
            ConfigDescriptor(str,
                             'Thursday occupancy schedule for AHU',
                             value_default=['5:30', '18:30'])),
            ('b4_friday_sch',
            ConfigDescriptor(str,
                             'Friday occupancy schedule for AHU',
                             value_default=['5:30', '18:30'])),
            ('b5_saturday_sch',
            ConfigDescriptor(str,
                             'Saturday occupancy schedule for AHU (default: unoccupied)',
                             value_default=['0:00', '0:00'])),
            ('b6_sunday_sch',
            ConfigDescriptor(str,
                             'Sunday occupancy schedule for AHU (default: unoccupied)',
                             value_default=['0:00', '0:00']))
        ]

        config = collections.OrderedDict(config_dict)

        return config

    @classmethod
    def get_self_descriptor(cls):
        name = 'AIRCx for AHUs: Operation Schedule'
        desc = 'AIRCx for AHUs: Operation Schedule'
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
            cls.duct_stcpr_name:
            InputDescriptor('DuctStaticPressure', 'AHU duct static pressure',
                            count_min=1)
            }

    def reports(self):
        """
        Called by UI to assemble information for creation of the diagnostic
        visualization.
        """
        report = reports.Report('Retuning Report')
        report.add_element(reports.RxOperationSchedule(
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
        """
        Check application pre-quisites and assemble analysis data set.
        Receives mapped data from the DrivenBaseClass.  Filters non-relevent
        data and assembles analysis data set for diagnostics.
        """
        # topics = self.inp.get_topics()
        # diagnostic_topic = topics[self.fan_status_name][0]
        # cur_time = self.inp.localize_sensor_time(diagnostic_topic, current_time)
        to_zone = dateutil.tz.gettz(self.cur_tz)
        cur_time = cur_time.astimezone(to_zone)

        device_dict = {}
        dx_result = Results()

        for key, value in points.items():
            point_device = [_name.lower() for _name in key.split("&")]
            if point_device[0] not in device_dict:
                device_dict[point_device[0]] = [(point_device[1], value)]
            else:
                device_dict[point_device[0]].append((point_device[1], value))

        fan_status_data = []
        stc_pr_data = []
        fan_sp_data = []

        for key, value in device_dict.items():
            data_name = key
            if value is None:
                continue
            if data_name == self.fan_status_name:
                fan_status_data = data_builder(value, data_name)
            elif data_name == self.duct_stcpr_name:
                stc_pr_data = data_builder(value, data_name)
            elif data_name == self.fan_sp_name:
                fan_sp_data = data_builder(value, data_name)

        missing_data = []
        if not fan_status_data and not fan_sp_data:
            missing_data.append(self.fan_status_name)
        if not stc_pr_data:
            missing_data.append(self.duct_stcpr_name)


        if missing_data:
            dx_result.log("Missing data from publish: {}".format(missing_data))
            return dx_result

        current_fan_status, fan_sp = self.check_fan_status(fan_status_data, fan_sp_data, cur_time)

        dx_result = self.sched_aircx.sched_aircx(cur_time, stc_pr_data, current_fan_status, dx_result)

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


class ScheduleAIRCx(object):
    """
    Operational schedule, supply-air temperature set point reset, and duct static pressure reset
    AIRCx for AHUs or RTUs.
    """
    def __init__(self, unocc_time_thr, unocc_stcpr_thr,
                 monday_sch, tuesday_sch, wednesday_sch, thursday_sch,
                 friday_sch, saturday_sch, sunday_sch,
                 no_req_data, analysis):
        self.fan_status_array = []
        self.schedule = {}
        self.stcpr_array = []
        self.schedule_time_array = []

        self.stcpr_stpt_array = []
        self.sat_stpt_array = []
        self.reset_table_key = None
        self.timestamp_array = []
        self.dx_table = {}

        def date_parse(dates):
            return [parse(timestamp_array).time() for timestamp_array in dates]

        self.analysis = analysis
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
        self.pre_msg = ("Current time is in the scheduled hours "
                        "unit is operating correctly.")

        # Application thresholds (Configurable)
        self.no_req_data = no_req_data
        self.unocc_time_thr = unocc_time_thr
        self.unocc_stcpr_thr = unocc_stcpr_thr

    def reinitialize_sched(self):
        """
        Reinitialize schedule data arrays
        :return:
        """
        self.stcpr_array = []
        self.fan_status_array = []
        self.schedule_time_array = []
        self.timestamp_array = []

    def sched_aircx(self, current_time, stcpr_data, current_fan_status, dx_result):
        """
        Main function for operation schedule AIRCx - manages data arrays checks AIRCx run status.
        :param current_time:
        :param stcpr_data:
        :param current_fan_status:
        :param dx_result:
        :return:
        """
        schedule = self.schedule[current_time.weekday()]
        try:
            run_status = check_run_status(self.timestamp_array, current_time, self.no_req_data, run_schedule="daily")

            if run_status is None:
                # schedule_name = create_table_key(self.analysis, self.timestamp_array[0])
                dx_result.log("{} - Insufficient data to produce a valid diagnostic result.".format(current_time))
                dx_result = pre_conditions(INSUFFICIENT_DATA, [SCHED_RCX], self.analysis, current_time, dx_result)
                self.reinitialize_sched()
                return dx_result

            if run_status:
                dx_result = self.unocc_fan_operation(dx_result)
                self.reinitialize_sched()

            return dx_result

        finally:
            self.timestamp_array.append(current_time)
            if current_time.time() < schedule[0] or current_time.time() > schedule[1]:
                self.stcpr_array.extend(stcpr_data)
                self.fan_status_array.append((current_time, current_fan_status))
                self.schedule_time_array.append(current_time)

    def unocc_fan_operation(self, dx_result):
        """
        AIRCx to determine if AHU is operating excessively in unoccupied mode.
        :param dx_result:
        :return:
        """
        avg_duct_stcpr = 0
        percent_on = 0
        fan_status_on = [(fan[0].hour, fan[1]) for fan in self.fan_status_array if int(fan[1]) == 1]
        fanstat = [(fan[0].hour, fan[1]) for fan in self.fan_status_array]
        hourly_counter = []
        thresholds = zip(self.unocc_time_thr.items(), self.unocc_stcpr_thr.items())
        diagnostic_msg = {}
        color_code_dict = {}

        for counter in range(24):
            fan_on_count = [fan_status_time[1] for fan_status_time in fan_status_on if fan_status_time[0] == counter]
            fan_count = [fan_status_time[1] for fan_status_time in fanstat if fan_status_time[0] == counter]
            if len(fan_count):
                hourly_counter.append(fan_on_count.count(1)/len(fan_count)*100)
            else:
                hourly_counter.append(0)

        if self.schedule_time_array:
            if self.fan_status_array:
                percent_on = (len(fan_status_on)/len(self.fan_status_array)) * 100.0
            if self.stcpr_array:
                avg_duct_stcpr = mean(self.stcpr_array)

            for (key, unocc_time_thr), (key2, unocc_stcpr_thr) in thresholds:
                if percent_on > unocc_time_thr:
                    msg = "{} - Supply fan is on during unoccupied times".format(key)
                    color_code = RED
                    result = 63.1
                else:
                    if avg_duct_stcpr < unocc_stcpr_thr:
                        msg = "{} - No problems detected for schedule diagnostic.".format(key)
                        color_code = GREEN
                        result = 60.0
                    else:
                        msg = ("{} - Fan status show the fan is off but the duct static "
                               "pressure is high, check the functionality of the "
                               "pressure sensor.".format(key))
                        color_code = GREY
                        result = 64.2
                color_code_dict.update({key: color_code})
                diagnostic_msg.update({key: result})
                dx_result.log(msg)
        else:
            msg = "ALL - No problems detected for schedule diagnostic."
            dx_result.log(msg)
            color_code_dict = {"low": GREEN, "normal": GREEN, "high": GREEN}
            diagnostic_msg = {"low": 60.0, "normal": 60.0, "high": 60.0}

        if 64.2 not in diagnostic_msg.values():
            for _hour in range(24):
                diagnostic_msg = {}
                color_code_dict = {}
                utc_offset = self.timestamp_array[0].isoformat()[-6:]
                push_time = self.timestamp_array[0].date()
                push_time = datetime.combine(push_time, datetime.min.time())
                push_time = push_time.replace(hour=_hour)
                for key, unocc_time_thr in self.unocc_time_thr.items():
                    diagnostic_msg.update({key: 60.0})
                    color_code_dict.update({key: GREEN})
                    if hourly_counter[_hour] > unocc_time_thr:
                        diagnostic_msg.update({key: 63.1})
                        color_code_dict.update({key: RED})
                dx_table = create_dx_table(str(push_time), SCHED_RCX, diagnostic_msg, color_code_dict)
                dx_result.insert_table_row(self.analysis, dx_table)
                # dx_table = {SCHED_RCX + DX:  diagnostic_msg}
                # table_key = create_table_key(self.analysis, push_time) + utc_offset
                # dx_result.insert_table_row(table_key, dx_table)
        else:
            push_time = self.timestamp_array[0].date()
            dx_table = create_dx_table(str(push_time), SCHED_RCX, diagnostic_msg, color_code_dict)
            dx_result.insert_table_row(self.analysis, dx_table)
            # table_key = create_table_key(self.analysis, push_time)
            # dx_result.insert_table_row(table_key, {SCHED_RCX + DX:  diagnostic_msg})

        return dx_result