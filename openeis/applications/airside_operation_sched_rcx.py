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
from numpy import mean
from datetime import datetime
from dateutil.parser import parse
import dateutil.tz
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


class Application(DrivenApplicationBaseClass):
    """
    Air-side HVAC Auto-Retuning Diagnostics
    for AHUs.
    """
    fan_status_name = 'fan_status'
    fan_speedcmd_name = 'fan_speedcmd'
    duct_stp_name = 'duct_stp'

    def __init__(
            self, *args, no_required_data=10,
            unocc_time_threshold=30.0, unocc_stp_threshold=0.2, local_tz=1,
            monday_sch=['5:30', '18:30'], tuesday_sch=['5:30', '18:30'],
            wednesday_sch=['5:30', '18:30'], thursday_sch=['5:30', '18:30'],
            friday_sch=['5:30', '18:30'], saturday_sch=['0:00', '0:00'],
            sunday_sch=['0:00', '0:00'],
            analysis_name='', sensitivity=1, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.cur_tz = available_tz[local_tz]
        except:
            self.cur_tz = 'UTC'
        analysis = analysis_name
        self.fan_status_name = Application.fan_status_name
        self.duct_stp_name = Application.duct_stp_name
        self.local_tz = local_tz
        # Optional points
        self.override_state = 'AUTO'
        if Application.fan_speedcmd_name is not None:
            self.fansp_name = Application.fan_speedcmd_name.lower()
        else:
            self.fansp_name = None

        no_required_data = int(no_required_data)

        if sensitivity == 0:
            # low sensitivity
            unocc_time_threshold = 45.0
            unocc_stp_threshold = 0.1
        elif sensitivity == 1:
            # normal sensitivity
            unocc_time_threshold = 30.0
            unocc_stp_threshold = 0.2
        elif sensitivity == 2:
            # high sensitivity
            unocc_time_threshold = 15.0
            unocc_stp_threshold = 0.3

        self.sched_occ_dx = (
            SchedResetRcx(unocc_time_threshold, unocc_stp_threshold,
                          monday_sch, tuesday_sch, wednesday_sch, thursday_sch,
                          friday_sch, saturday_sch, sunday_sch,
                          no_required_data, analysis))

    @classmethod
    def get_config_parameters(cls):
        """
        Generate required configuration
        parameters with description for user
        """
        dgr_sym = u'\N{DEGREE SIGN}'
        return {
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
                             value_default=['6:30', '18:30']),
            'tuesday_sch':
            ConfigDescriptor(str,
                             'Tuesday AHU occupied schedule, '
                             'Used to detect the '
                             'time when the supply fan should '
                             'be operational',
                             value_default=['6:30', '18:30']),
            'wednesday_sch':
            ConfigDescriptor(str,
                             'Wednesday AHU occupied schedule, '
                             'Used to detect the '
                             'time when the supply fan should '
                             'be operational',
                             value_default=['6:30', '18:30']),
            'thursday_sch':
            ConfigDescriptor(str,
                             'Thursday AHU occupied schedule, '
                             'Used to detect the '
                             'time when the supply fan should '
                             'be operational',
                             value_default=['6:30', '18:30']),
            'friday_sch':
            ConfigDescriptor(str,
                             'Friday AHU occupied schedule, '
                             'Used to detect the '
                             'time when the supply fan should '
                             'be operational',
                             value_default=['6:30', '18:30']),
            'saturday_sch':
            ConfigDescriptor(str,
                             'Saturday AHU occupied schedule, '
                             'Used to detect the '
                             'time when the supply fan should '
                             'be operational (unoccupied)',
                             value_default=['0:00', '0:00']),
            'sunday_sch':
            ConfigDescriptor(str,
                             'Sunday AHU occupied schedule, '
                             'Used to detect the '
                             'time when the supply fan should '
                             'be operational (unoccupied)',
                             value_default=['0:00', '0:00']),
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
        name = 'Auto-RCx for AHU: Operation Schedule'
        desc = 'Auto-RCx for AHU: Operation Schedule'
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
            cls.duct_stp_name:
            InputDescriptor('DuctStaticPressure', 'AHU duct static pressure',
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
        """Check application pre-quisites and assemble analysis data set.
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

        stc_pr_data = []

        def data_builder(value_tuple, point_name):
            value_list = []
            for item in value_tuple:
                value_list.append(item[1])
            return value_list

        for key, value in device_dict.items():
            data_name = key
            if value is None:
                continue
            if data_name == self.duct_stp_name:
                stc_pr_data = data_builder(value, data_name)

        missing_data = []

        if not stc_pr_data:
            missing_data.append(self.duct_stp_name)
        if not fan_status:
            missing_data.append(self.fan_status_name)
        if missing_data:
            raise Exception('Missing required data: {}'.format(missing_data))
            return diagnostic_result
        dx_status, diagnostic_result = (
            self.sched_occ_dx.sched_rcx_alg(cur_time, stc_pr_data, fan_status, diagnostic_result))
        return diagnostic_result


class SchedResetRcx(object):
    """Schedule, supply-air temperature, and duct static pressure auto-detect
    diagnostics for AHUs or RTUs.
    """

    def __init__(self, unocc_time_threshold, unocc_stp_threshold,
                 monday_sch, tuesday_sch, wednesday_sch, thursday_sch,
                 friday_sch, saturday_sch, sunday_sch,
                 no_req_data, analysis):
        self.fanstat_values = []
        self.schedule = {}
        self.stcpr_arr = []
        self.stcpr_stpt_arr = []
        self.sat_stpt_arr = []
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
        self.timestamp_arr = []

        self.schedule = {0: self.monday_sch, 1: self.tuesday_sch,
                         2: self.wednesday_sch, 3: self.thursday_sch,
                         4: self.friday_sch, 5: self.saturday_sch,
                         6: self.sunday_sch}

        # Application thresholds (Configurable)
        self.no_req_data = no_req_data
        self.unocc_time_threshold = float(unocc_time_threshold)
        self.unocc_stp_threshold = float(unocc_stp_threshold)


    def reinitialize(self):
        """Reinitialize data arrays"""
        self.stcpr_arr = []
        self.fanstat_values = []
        self.sched_time = []
        self.dx_table = {}
        self.timestamp_arr = []


    def sched_rcx_alg(self, current_time, stcpr_data, fan_stat_data, dx_result):
        """Check schedule status and unit operational status."""
        dx_status = 1
        fan_status = None
        schedule = self.schedule[current_time.weekday()]
        run_diagnostic = False

        if self.timestamp_arr and self.timestamp_arr[-1].date() != current_time.date():
            run_diagnostic = True

        if not run_diagnostic:
            if current_time.time() < schedule[0] or current_time.time() > schedule[1]:
                self.stcpr_arr.extend(stcpr_data)
                self.fanstat_values.append((current_time, int(max(fan_stat_data))))
                self.sched_time.append(current_time)

        if run_diagnostic and len(self.timestamp_arr) >= self.no_req_data:
            self.dx_time = self.timestamp_arr[-1]
            dx_result = self.unocc_fan_operation(dx_result)

            self.reinitialize()
        elif run_diagnostic:
            dx_msg = 61.2
            msg = 'Insufficient data for conclusive diagnostic'
            color_code = 'GREY'
            dx_table = {
                'datetime': str(self.timestamp_arr[-1]),
                'diagnostic_name': SCHED_RCX,
                'diagnostic_message': msg,
                'energy_impact': None,
                'color_code': color_code
            }
            dx_result.insert_table_row('Airside_RCx', dx_table)
            self.reinitialize()
            if current_time.time() < schedule[0] or current_time.time() > schedule[1]:
                self.stcpr_arr.extend(stcpr_data)
                self.fanstat_values.append((current_time, int(max(fan_stat_data))))
                self.sched_time.append(current_time)
            dx_status = 0
        self.timestamp_arr.append(current_time)
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
                push_time = self.sched_time[0].date() if self.sched_time else self.timestamp_arr[0].date()
                push_time = datetime.combine(push_time, datetime.min.time())
                push_time = push_time.replace(hour=_hour)
                # dx_table = {SCHED_RCX + DX: 60.0}
                if hourly_counter[_hour] > self.unocc_time_threshold:
                    dx_table = {
                        'datetime': str(push_time),
                        'diagnostic_name': SCHED_RCX,
                        'diagnostic_message': msg,
                        'energy_impact': None,
                        'color_code': color_code
                    }
                    # table_key = create_table_key(self.sched_file_name_id, push_time)
                    dx_result.insert_table_row('Airside_RCx', dx_table)
        else:
            push_time = self.timestamp_arr[-1]
            # table_key = create_table_key(self.sched_file_name_id, push_time)
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
