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
not necessarily constitute or imply its endorsement, recommendation
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
import fnmatch
from math import fabs as abs
from openeis.applications import (DrivenApplicationBaseClass,
                                  OutputDescriptor,
                                  ConfigDescriptor,
                                  InputDescriptor,
                                  Results,
                                  Descriptor,
                                  reports)

Hot_water_RCx = 'Hot Water Central Plant Diagnostics'
hotwater_dx1 = 'High HW loop Differential Pressure Dx'
hotwater_dx2 = 'HW loop Differential Pressure Reset Dx'
hotwater_dx3 = 'HW loop High Supply Temperature Dx'
hotwater_dx4 = 'HW loop Supply Temperature Reset Dx'
hotwater_dx5 = 'HW loop Low Delta-T Dx'
time_format = '%m/%d/%Y %H:%M'


class Application(DrivenApplicationBaseClass):
    '''
    Air-side HVAC diagnostic to check if an AHU/RTU
    is not economizing when it should.
    '''
    loop_dp_name = 'loop_dp'
    loop_dp_stpt_name = 'loop_dp_stpt'
    boiler_status_name = 'boiler_status'
    pump_status_name = 'pump_status'

    hw_pump_vfd_name = 'hw_pump_vfd'
    hws_temp_name = 'hws_temp'
    hw_stsp_name = 'hw_stsp'
    hwr_temp_name = 'hwr_temp'

    def __init__(self, *args,
                 min_dp_threshold=2.5,
                 max_dp_threshold=25.0,
                 data_window=180, dp_reset_threshold=10.0,
                 no_required_data=50,
                 dp_reset_threshold=5.0, setpoint_allowable_deviation=10.0,
                 data_sample_rate=None,
                 dp_pump_threshold=45.0,

                 hw_st_threshold=120.0,
                 hw_pump_vfd_threshold=70.0,

                 min_hwst_threshold=70.0,
                 max_hwst_threshold=180.0, min_hwrt_threshold=70.0,
                 max_hwrt_threshold=180.0,
                 delta_t_threshold=10.0, desired_delta_t=20.0,

                 hwst_reset_threshold=10.0,
                 **kwargs):

        super().__init__(*args, **kwargs)

        Application.pre_requiste_messages = []
        Application.pre_msg_time = []

        self.loop_dp_name = Application.loop_dp_name
        self.loop_dp_stpt_name = Application.loop_dp_stpt_name

        self.boiler_status_name = Application.boiler_status_name
        self.pump_status_name = Application.pump_status_name

        self.hw_pump_vfd_name = Application.hw_pump_vfd_name
        self.hws_temp_name = Application.hws_temp_name
        self.hw_stsp_name = Application.hw_stsp_name
        self.hwr_temp_name = Application.hwr_temp_name

        '''Pre-requisite messages'''
        self.pre_msg1 = ('Loop DP indicates the system may be off. '
                         'The current data will not be used for '
                         'the diagnostic.')
        self.pre_msg2 = ('Loop DP is outside of normal operation range. '
                         'Check the functionality of the pressure transducer '
                         'and/or adjust algorithm thresholds.')
        self.pre_msg3 = ('Required data for diagnostic is not available. '
                         'Can not confirm hot water system is ON')
        self.pre_msg4 = ('Pump status indicates the system may be off. '
                         'The current data will not be used for '
                         'the diagnostic.')
        self.pre_msg5 = ('Boiler status indicates the HW system is not '
                         'active. This diagnostic will only run when at '
                         'least one boiler is on.')
        self.pre_msg6 = ('Missing hot water differential pressure, verify '
                         'that the HW loop DP is available.')
        self.pre_msg7 = ('Missing required data for diagnostic: '
                         'hot-water pump VFD command.')
        self.pre_msg8 = ('Missing hot water supply temperature data, '
                         'verify that the supply temperature data '
                         'is available.')
        self.pre_msg9 = ('Missing hot water return temperature data, '
                         'verify that the hot water return temperature '
                         'is available.')

        Application.pre_msg10 = ('Hot water supply temperature is outside '
                                 'of configured operation range')
        Application.pre_msg11 = ('Hot water return temperature is outside '
                                 'of configured operation range')
        self.data_window = float(data_window)
        self.min_dp_threshold = float(min_dp_threshold)
        self.max_dp_threshold = float(max_dp_threshold)

        self.hw_dx1 = HW_loopdp_RCx(no_required_data, data_window,
                                    setpoint_allowable_deviation,
                                    dp_pump_threshold,
                                    data_sample_rate)

        self.hw_dx2 = HW_temp_RCx(no_required_data, data_window,
                                  hw_st_threshold,
                                  hw_pump_vfd_threshold,
                                  setpoint_allowable_deviation,
                                  min_hwst_threshold, max_hwst_threshold,
                                  min_hwrt_threshold, max_hwrt_threshold,
                                  delta_t_threshold, desired_delta_t,
                                  data_sample_rate)

        self.hw_dx3 = HW_reset_RCx(no_required_data,
                                   hwst_reset_threshold,
                                   dp_reset_threshold)

    @classmethod
    def get_config_parameters(cls):
        '''
        Generate required configuration
        parameters with description for user
        '''
        return {
            'data_window': ConfigDescriptor(int, 'Minimum Elapsed time for '
                                            'analysis (default=15 minutes)',
                                            optional=True),
            'min_dp_threshold': ConfigDescriptor(float,
                                                 'Hot water loop minimum '
                                                 'operational differential '
                                                 'pressure (default=2.5 psi)',
                                                 optional=True),
            'max_dp_threshold': ConfigDescriptor(float,
                                                 'Hot water loop maximum '
                                                 'operational differential '
                                                 'pressure (default=25.0 psi)',
                                                 optional=True),
            'data_sample_rate':
                ConfigDescriptor(int, ('Data trending rate(minutes/sample)')),

            'setpoint_allowable_deviation':
                ConfigDescriptor(float,
                                 'Percent allowable deviation from set '
                                 'points (HWS and loop DP (default=10.0%)',
                                 optional=True),


            'dp_pump_threshold':
                ConfigDescriptor(float,
                                 'Pump threshold to determine if the loop DP '
                                 'is too high (default=45.0%)',
                                 optional=True),

            'dp_reset_threshold':
                ConfigDescriptor(float,
                                 'HW loop DP threshold to detect DP reset '
                                 '(default=5.0 psi)', optiional=True),

            'hwst_reset_threshold':
                ConfigDescriptor(float,
                                 'HW supply temperature threshold to detect '
                                 'HW supply temperature reset (10.0)',
                                 optional=True),

            'hw_st_threshold':
                ConfigDescriptor(float,
                                 'HW supply temperature threshold to detect '
                                 'if the HW supply temperature is too '
                                 'high (default=120.0F)', optional=True),
            'hw_pump_vfd_threshold':
                ConfigDescriptor(float,
                                 'HW loop pump VFD command threshold used to '
                                 'determine if the HW supply temperature is '
                                 'too high (default=25.0%)', optional=True),

            'min_hwst_threshold':
                ConfigDescriptor(float,
                                 'Minimum allowable operational HW '
                                 'supply temperature (default=125.0)'),
            'max_hwst_threshold':
                ConfigDescriptor(float, 'Maximum allowable operational '
                                 'HW supply temperature (default=185.0F)',
                                 optional=True),
            'min_hwrt_threshold':
                ConfigDescriptor(float,
                                 'Minimum allowable operational '
                                 'HW return temperature (default=115.0F)',
                                 optional=True),
            'max_hwrt_threshold':
                ConfigDescriptor(float,
                                 'Maximum allowable operational '
                                 'HW supply temperature (default=175.0F)',
                                 optional=True),
            'desired_delta_t':
                ConfigDescriptor(float,
                                 'Desired delta-T (differenece between HWS '
                                 'and HWR temperatures (default=20.0F))',
                                 optional=True),
            'delta_t_threshold':
                ConfigDescriptor(float,
                                 'Band around desired delta-T where '
                                 'where delat-T is considered '
                                 'OK (default=10F)', optional=True)
            }

    @classmethod
    def get_self_descriptor(cls):
        name = 'hw_distribution_system_rcx'
        desc = ('Automated Retro-commissioning for '
                'hot-water distribution system')
        return Descriptor(name=name, description=desc)

    def data_check(self, point_dict, _name, opt_name='zyxwvutsrq'):
        data_check = False
        point_values = []

        if opt_name is None or not opt_name:
            opt_name = 'zyxwvutsrq'

        for key, value in point_dict.items():
            if key.startswith(_name) and opt_name not in key:
                data_check = True
                if value is not None:
                    point_values.append(value)
        return data_check, point_values

    @classmethod
    def required_input(cls):
        '''
        Generate required inputs with description for
        user
        '''
        return {
            cls.loop_dp_name:
                InputDescriptor('Hot water loop differential pressure',
                                'Hot water central plant loop differential '
                                'pressure',
                                count_min=1),
            cls.loop_dp_stpt_name:
                InputDescriptor('Loop differential pressure set point',
                                'Hot water central plant loop differential '
                                'pressure set point',
                                count_min=1),
            cls.pump_status_name:
                InputDescriptor('Pump status',
                                'Hot water central plant pump status',
                                count_min=0),
            cls.boiler_status_name:
                InputDescriptor('Boiler status',
                                'Hot water central plant boiler status',
                                count_min=1),
            cls.hw_pump_vfd_name:
                InputDescriptor('Hot water pump VFD command',
                                'Hot water central plant pump VFD commands',
                                count_min=1),
            cls.hws_temp_name:
                InputDescriptor('Hot water supply temperature',
                                'Hot water central plant supply '
                                'water temperature',
                                count_min=1),
            cls.hw_stsp_name:
                InputDescriptor('Hot water supply temperature set point',
                                'Hot water central plant supply water '
                                'temperature set point',
                                count_min=1),
            cls.hwr_temp_name:
                InputDescriptor('Hot water return temperature',
                                'Hot water central plant return '
                                'water temperature', count_min=1)
        }

    def reports(self):
        '''
        Called by UI to create Viz.
        Describe how to present output to user
        '''
        report = reports.Report('Retuning Report')

        report.add_element(reports.RetroCommissioningOAED(table_name='Hot_water_RCx'))
        report.add_element(reports.RetroCommissioningAFDD(table_name='Hot_water_RCx'))

        return [report]

    @classmethod
    def output_format(cls, input_object):
        '''
        Called when application is staged.
        Output will have the date-time and  error-message.
        '''
        result = super().output_format(input_object)

        topics = input_object.get_topics()
        diagnostic_topic = topics[cls.loop_dp_name][0]
        diagnostic_topic_parts = diagnostic_topic.split('/')
        output_topic_base = diagnostic_topic_parts[:-1]
        datetime_topic = '/'.join(output_topic_base+['hotwater_dx', 'date'])
        message_topic = '/'.join(output_topic_base+['hotwater_dx', 'message'])
        diagnostic_name = '/'.join(output_topic_base+['hotwater_dx',
                                                      'diagnostic_name'])
        energy_impact = '/'.join(output_topic_base+['hotwater_dx',
                                                    'energy_impact'])
        color_code = '/'.join(output_topic_base+['hotwater_dx',
                                                 'color_code'])

        output_needs = {
            'Hot_water_RCx': {
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
        '''
        Check algorithm pre-quisites and assemble data set for analysis.
        '''
        topics = self.inp.get_topics()
        diagnostic_topic = topics[self.fan_status_name][0]

        current_time = self.inp.localize_sensor_time(diagnostic_topic, current_time)

        
        device_dict = {}
        diagnostic_result = Results()

        for key, value in points.items():
            device_dict[key.lower()] = value

        self.pre_msg_time.append(current_time)
        message_check = datetime.timedelta(minutes=(self.data_window))

        if (self.pre_msg_time[-1]-self.pre_msg_time[0]) >= message_check:
            msg_lst = [self.pre_msg1, self.pre_msg2, self.pre_msg3,
                       self.pre_msg4, self.pre_msg5, self.pre_msg6,
                       self.pre_msg7, self.pre_msg8, self.pre_msg9,
                       Application.pre_msg10, Application.pre_msg11]
            for item in msg_lst:
                if (Application.pre_requiste_messages.count(item) >
                   (0.25) * len(self.pre_msg_time)):
                    diagnostic_result.log(item, logging.INFO)
            Application.pre_requiste_messages = []
            self.pre_msg_time = []

        flow_check, dp_data = self.data_check(device_dict,
                                              self.loop_dp_name,
                                              self.loop_dp_stpt_name)

        for value in dp_data:
            if value < self.min_dp_threshold:
                Application.pre_requiste_messages.append(self.pre_msg1)
                return diagnostic_result
            elif value > self.max_dp_threshold:
                Application.pre_requiste_messages.append(self.pre_msg2)
                return diagnostic_result

        if not flow_check or not dp_data:
            pump_id = fnmatch.filter(device_dict,
                                     ''.join(['*',
                                              self.pump_status_name,
                                              '*']))

            if not pump_id:
                Application.pre_requiste_messages.append(self.pre_msg3)
                return diagnostic_result

            pump_stat = (list(device_dict[val] for val in pump_id if val in
                              device_dict and int(device_dict[val]) > 0))

            if not pump_stat:
                Application.pre_requiste_messages.append(self.pre_msg4)
                return diagnostic_result

        boiler_id = fnmatch.filter(device_dict,
                                   ''.join(['*',
                                            self.boiler_status_name,
                                            '*']))
        boiler_stat = (list(device_dict[val] for val in
                            boiler_id if val in device_dict
                            and int(device_dict[val]) > 0))
        if not boiler_stat:
            Application.pre_requiste_messages.append(self.pre_msg5)
            return diagnostic_result

        loop_dp_values = []
        loop_dp_stpt_values = []
        hw_pump_vfd_values = []
        hw_stsp_values = []
        hws_temp_values = []
        hwr_temp_values = []

        for key, value in device_dict.items():
            if key.startswith(self.loop_dp_stpt_name) and value is None:
                loop_dp_stpt_values.append(value)
            elif key.startswith(self.loop_dp_name) and value is None:
                loop_dp_values.append(value)
            elif key.startswith(self.hw_pump_vfd_name) and value is None:
                hw_pump_vfd_values.append(value)
            elif key.startswith(self.hw_stsp_name) and value is None:
                hw_stsp_values.append(value)
            elif key.startswith(self.hws_temp_name) and value is None:
                hws_temp_values.append(value)
            elif key.startswith(self.hwr_temp_name) and value is None:
                hwr_temp_values.append(value)

        if not loop_dp_values:
            Application.pre_requiste_messages.append(self.pre_msg6)
        if not hw_pump_vfd_values:
            Application.pre_requiste_messages.append(self.pre_msg7)
        if not hws_temp_values:
            Application.pre_requiste_messages.append(self.pre_msg8)
        if not hwr_temp_values:
            Application.pre_requiste_messages.append(self.pre_msg9)

        if (not loop_dp_values and
           not (hws_temp_values and hwr_temp_values)):
            return diagnostic_result

        diagnostic_result = self.hw_dx1.hw_dp_rcx(diagnostic_result,
                                                  current_time,
                                                  loop_dp_stpt_values,
                                                  loop_dp_values,
                                                  hw_pump_vfd_values)

        diagnostic_result = self.hw_dx2.temp_rcx(diagnostic_result,
                                                 current_time,
                                                 hws_temp_values,
                                                 hwr_temp_values,
                                                 hw_pump_vfd_values)

        diagnostic_result = self.hw_dx3.reset_rcx(current_time, hw_stsp_values,
                                                  loop_dp_stpt_values,
                                                  diagnostic_result)
        Application.pre_requiste_messages = []
        self.pre_msg_time = []
        return diagnostic_result


class HW_loopdp_RCx(object):
    '''
    Hot water central plant diagnostics for differential pressure
    '''
    def __init__(self, no_required_data, data_window,
                 setpoint_allowable_deviation,
                 dp_pump_threshold, data_sample_rate):
        self.hw_pump_vfd_values = []
        self.loop_dp_values = []
        self.loop_dp_stpt_values = []
        self.timestamp = []
        self.no_required_data = int(no_required_data)
        self.data_window = float(data_window)
        self.data_sample_rate = int(data_sample_rate)
        self.setpoint_allowable_deviation = float(setpoint_allowable_deviation)
        self.dp_pump_threshold = float(dp_pump_threshold)

    def hw_dp_rcx(self, diagnostic_result, current_time, loop_dp_stpt_values,
                  loop_dp_values, hw_pump_vfd_values):
        '''
        High HW loop differential pressure diagnostic
        '''
        self.hw_pump_vfd_values.append(
            sum(hw_pump_vfd_values) /
            len(hw_pump_vfd_values))

        self.loop_dp_values.append(sum(loop_dp_values)/len(loop_dp_values))

        self.loop_dp_stpt_values.append(
            sum(loop_dp_stpt_values) /
            len(loop_dp_stpt_values))

        self.timestamp.append(current_time)
        time_check = datetime.timedelta(minutes=self.data_window)
        elapsed_time = ((self.timestamp[-1] - self.timestamp[0]) +
                        datetime.timedelta(minutes=self.data_sample_rate))

        if (elapsed_time >= time_check and
           len(self.timestamp) >= self.no_required_data):

            avg_loop_dp = (sum(self.loop_dp_values))/(len(self.loop_dp_values))
            if self.loop_dp_stpt_values:
                setpoint_tracking = [abs(x-y) for
                                     x, y in zip(self.loop_dp_stpt_values,
                                                 self.loop_dp_values)]

                setpoint_tracking = (sum(setpoint_tracking) /
                                     (len(setpoint_tracking)
                                      * avg_loop_dp)*100)

                if setpoint_tracking > self.setpoint_allowable_deviation:
                    diagnostic_message = ('{name}: Hot water loop '
                                          'differential pressure is '
                                          'deviating significantly from '
                                          'the set point.'
                                          .format(name=Hot_water_RCx))
                    color_code = 'RED'
                    energy_impact = None
                    dx_table = {
                        'datetime': str(self.timestamp[-1]),
                        'diagnostic_name': Hot_water_RCx,
                        'diagnostic_message': diagnostic_message,
                        'energy_impact': energy_impact,
                        'color_code': color_code
                        }
                    diagnostic_result.insert_table_row('Hot_water_RCx',
                                                       dx_table)
                    diagnostic_result.log(diagnostic_message, logging.INFO)
            diagnostic_result = self.high_dp_rcx(diagnostic_result)
        return diagnostic_result

    def high_dp_rcx(self, result):
        '''
        If the detected problems(s) are consistent
        then generate a fault message(s).
        '''
        if self.hw_pump_vfd_values:
            avg_pump_vfd = (sum(self.hw_pump_vfd_values) /
                            len(self.hw_pump_vfd_values))

            color_code = 'GREY'
            energy_impact = None

            if (avg_pump_vfd > self.dp_pump_threshold):
                diagnostic_message = ('{name}: The HW loop DP has been '
                                      'detected to be too high.'
                                      .format(name=hotwater_dx1))
            else:
                diagnostic_message = ('{name}: No re-tuning opportunity '
                                      'detected for the high HW loop DP.'
                                      .format(name=hotwater_dx1))

            dx_table = {
                'datetime': str(self.timestamp[-1]),
                'diagnostic_name': hotwater_dx1,
                'diagnostic_message': diagnostic_message,
                'energy_impact': energy_impact,
                'color_code': color_code
                }
        else:
            diagnostic_message = ('{name}: HW system pump VFD command was not '
                                  'detected. High HW DP Diagnostic requires '
                                  'the pump VFD command'
                                  .format(name=hotwater_dx1))
            dx_table = {
                'datetime': str(self.timestamp[-1]),
                'diagnostic_name': hotwater_dx1,
                'diagnostic_message': diagnostic_message,
                'energy_impact': None,
                'color_code': 'GREY'
                }
        self.hw_pump_vfd_values = []
        result.insert_table_row('Hot_water_RCx', dx_table)
        result.log(diagnostic_message, logging.INFO)
        return result


class HW_temp_RCx(object):
    '''
    Hot water central plant diagnostics for differential pressure
    '''
    def __init__(self, no_required_data, data_window,
                 hw_st_threshold, hw_pump_vfd_threshold,
                 setpoint_allowable_deviation, min_hwst_threshold,
                 max_hwst_threshold, min_hwrt_threshold, max_hwrt_threshold,
                 delta_t_threshold, desired_delta_t, data_sample_rate):

        self.hw_stsp_values = []
        self.hws_temp_values = []
        self.hw_pump_vfd_values = []
        self.hwr_temp_values = []
        self.timestamp = []

        self.data_window = float(data_window)
        self.no_required_data = int(no_required_data)
        self.setpoint_allowable_deviation = float(setpoint_allowable_deviation)
        self.data_sample_rate = int(data_sample_rate)
        self.hw_st_threshold = float(hw_st_threshold)
        self.hw_pump_vfd_threshold = float(hw_pump_vfd_threshold)

        self.min_hwst_threshold = float(min_hwst_threshold)
        self.max_hwst_threshold = float(max_hwst_threshold)
        self.min_hwrt_threshold = float(min_hwrt_threshold)
        self.max_hwrt_threshold = float(max_hwrt_threshold)

        self.delta_t_threshold = float(delta_t_threshold)
        self.desired_delta_t = float(desired_delta_t)

    def temp_rcx(self, diagnostic_result, current_time, hws_temp_values,
                 hwr_temp_values, hw_pump_vfd_values):
        limit_check = False
        for value in hws_temp_values:
            if (value < self.min_hwst_threshold or
               value > self.max_hwst_threshold):
                Application.pre_requiste_messages.append(Application.pre_msg10)
                limit_check = True
        for value in hwr_temp_values:
            if (value < self.min_hwrt_threshold or
               value > self.max_hwrt_threshold):
                Application.pre_requiste_messages.append(Application.pre_msg11)
                limit_check = True

        if limit_check:
            return diagnostic_result

        self.hws_temp_values.append(sum(hws_temp_values)/len(hws_temp_values))
        self.hwr_temp_values.append(sum(hwr_temp_values)/len(hwr_temp_values))

        self.hw_pump_vfd_values.append(
            sum(hw_pump_vfd_values) /
            len(hw_pump_vfd_values))

        self.timestamp.append(current_time)
        time_check = datetime.timedelta(minutes=self.data_window)

        elapsed_time = ((self.timestamp[-1] - self.timestamp[0]) +
                        datetime.timedelta(minutes=self.data_sample_rate))

        if (elapsed_time >= time_check and
           len(self.timestamp) >= self.no_required_data):

            if self.hw_stsp_values:
                avg_hw_stsp = sum(self.hw_stsp_values)/len(self.hw_stsp_values)
                set_point_tracking = [abs(x-y) for
                                      x, y in zip(self.hw_stsp_values,
                                                  self.hw_st_values)]

                set_point_tracking = (sum(set_point_tracking) /
                                      (len(set_point_tracking)
                                       * avg_hw_stsp) * 100)
                if set_point_tracking > self.setpoint_allowable_deviation:
                    diagnostic_message = ('{name}: Hot water supply '
                                          'temperature is deviating '
                                          'significantly from the hot '
                                          'water supply temperature '
                                          'set point.'
                                          .format(name=Hot_water_RCx))
                    color_code = 'RED'
                    energy_impact = None
                    dx_table = {
                        'datetime': str(self.timestamp[-1]),
                        'diagnostic_name': Hot_water_RCx,
                        'diagnostic_message': diagnostic_message,
                        'energy_impact': energy_impact,
                        'color_code': color_code
                        }
                    diagnostic_result.insert_table_row('Hot_water_RCx',
                                                       dx_table)
                    diagnostic_result.log(diagnostic_message, logging.INFO)
            diagnostic_result = self.high_hwst_rcx(diagnostic_result)
            diagnostic_result = self.low_hw_delta_t_rcx(diagnostic_result)
        return diagnostic_result

    def high_hwst_rcx(self, result):
        '''
        If the detected problem(s) are consistent
        then generate a fault message.
        '''
        if self.hw_pump_vfd_values:
            avg_hwst = sum(self.hws_temp_values)/len(self.hws_temp_values)
            avg_pump_vfd = (
                sum(self.hw_pump_vfd_values) /
                len(self.hw_pump_vfd_values))

            if (avg_hwst > self.hw_st_threshold and
               avg_pump_vfd < self.hw_pump_vfd_threshold):
                diagnostic_message = ('{name}: Hot water supply temperature '
                                      'set point was detected to be too high.'
                                      .format(name=hotwater_dx3))
                color_code = 'RED'
                energy_impact = None
            else:
                diagnostic_message = ('{name}: No Re-tuning opportunity '
                                      'detected for the high hot water supply '
                                      'set point diagnostic.'
                                      .format(name=hotwater_dx3))
                color_code = 'GREEN'
                energy_impact = None

            dx_table = {
                'datetime': str(self.timestamp[-1]),
                'diagnostic_name': hotwater_dx3,
                'diagnostic_message': diagnostic_message,
                'energy_impact': energy_impact,
                'color_code': color_code
                }
        else:
            diagnostic_message = ('{name}: HW system pump VFD command '
                                  'was not detected. The High HW Supply '
                                  'Temperature Diagnostic requires the pump '
                                  'VFD command'.format(name=hotwater_dx3))
            dx_table = {
                'datetime': str(self.timestamp[-1]),
                'diagnostic_name': hotwater_dx3,
                'diagnostic_message': diagnostic_message,
                'energy_impact': None,
                'color_code': 'GREY'
                }
        self.hw_pump_vfd_values = []
        result.insert_table_row('Hot_water_RCx', dx_table)
        result.log(diagnostic_message, logging.INFO)
        return result

    def low_hw_delta_t_rcx(self, result):
        '''
        If the detected problems(s) are consistent
        then generate a fault message(s).
        '''
        diff_supply_return = [(x-y) for
                              x, y in zip(self.hws_temp_values,
                                          self.hwr_temp_values)]
        avg_delta_t = sum(diff_supply_return)/len(diff_supply_return)

        if (self.desired_delta_t - avg_delta_t) > self.delta_t_threshold:
            '''Create diagnostic message for fault condition'''
            diagnostic_message = ('{name}: Hot water loop delta-T was lower '
                                  'than expected'.format(name=hotwater_dx5))
            color_code = 'RED'
            energy_impact = None
        else:
            '''Create diagnostic message for no-fault condition'''
            diagnostic_message = ('{name}: No re-tuning opportunity detected '
                                  'for the low hot water loop delta-T '
                                  'diagnostic.'.format(name=hotwater_dx5))
            color_code = 'GREEN'
            energy_impact = None

        dx_table = {
            'datetime': str(self.timestamp[-1]),
            'diagnostic_name': hotwater_dx5,
            'diagnostic_message': diagnostic_message,
            'energy_impact': energy_impact,
            'color_code': color_code
            }

        result.insert_table_row('Hot_water_RCx', dx_table)
        result.log(diagnostic_message, logging.INFO)
        self.hw_stsp_values = []
        self.hws_temp_values = []
        self.hw_pump_vfd_values = []
        self.timestamp = []
        self.oa_temp_values = []
        self.rht_vlv_values = []
        self.hwr_temp_values = []

        Application.pre_requiste_messages = []
        Application.pre_msg_time = []
        return result


class HW_reset_RCx(object):
    '''
    HW reset auto-detect RCx
    '''
    def __init__(self, no_required_data, dp_reset, hwst_reset):
        self.hw_stsp_values = []
        self.no_required_data = int(no_required_data)
        self.loop_dp_stpt_values = []
        self.timestamp = []
        self.dp_reset_threshold = float(dp_reset)
        self.hw_reset_threshold = float(hwst_reset)

    def reset_rcx(self, current_time, hw_st_sp, hw_dp_sp,
                  diagnostic_result):
        '''
        Check schedule status and unit operational status
        '''
        run = False
        if self.timestamp and self.timestamp[-1].date() != current_time.date():
            run = True

        loop_dp_stpt = sum(hw_dp_sp)/len(hw_dp_sp)
        hw_stsp = sum(hw_st_sp)/len(hw_st_sp)

        if run and len(self.timestamp) >= self.no_required_data:
            diagnostic_result = self.no_hwst_reset_rcx(diagnostic_result)
            diagnostic_result = self.no_static_pr_reset_rcx(diagnostic_result)

            self.timestamp = []
            self.loop_dp_stpt_values = []
            self.hw_stsp_values = []

        self.timestamp.append(current_time)
        self.loop_dp_stpt_values.append(loop_dp_stpt)
        self.hw_stsp_values.append(hw_stsp)
        return diagnostic_result

    def no_hwst_reset_rcx(self, result):
        '''
        If the detected problems(s) are consistent
        then generate a fault message(s).
        '''

        hw_st_condition = max(self.hw_stsp_values) - min(self.hw_stsp_values)

        if hw_st_condition < self.hw_reset_threshold:
            diagnostic_message = ('{name}: No hot water temperature reset was '
                                  'detected for this system. Enable or add '
                                  'hot water reset to improve system '
                                  'performance and save energy.'
                                  .format(name=hotwater_dx4))
            color_code = 'RED'
            energy_impact = None
        else:
            diagnostic_message = ('{name}: No retuning opportunity '
                                  'detected for the hot water supply set '
                                  'point reset diagnostic.'
                                  .format(name=hotwater_dx4))
            color_code = 'GREEN'
            energy_impact = None

        dx_table = {
            'datetime': str(self.timestamp[-1]),
            'diagnostic_name': hotwater_dx4,
            'diagnostic_message': diagnostic_message,
            'energy_impact': energy_impact,
            'color_code': color_code
            }

        result.insert_table_row('Hot_water_RCx', dx_table)
        result.log(diagnostic_message, logging.INFO)
        return result

    def no_static_pr_reset_rcx(self, result):
        '''
        If the detected problems(s) are
        consistent then generate a fault message(s).
        '''
        loop_dpst_condition = (max(self.loop_dp_stpt_values) -
                               min(self.loop_dp_stpt_values))

        energy_impact = None
        color_code = 'GREY'

        if loop_dpst_condition < self.dp_diff_threshold:
            diagnostic_message = ('{name}: No hot water DP reset was detected '
                                  'for this system. Enable or add hot water '
                                  'DP reset to improve system performance '
                                  'and save energy'.format(name=hotwater_dx2))
            color_code = 'RED'
        else:
            diagnostic_message = ('{name}: No Re-tuning opportunity detected '
                                  'for the DP reset diagnostic.'
                                  .format(name=hotwater_dx2))
            color_code = 'GREEN'

        dx_table = {
            'datetime': str(self.timestamp[-1]),
            'diagnostic_name': hotwater_dx2,
            'diagnostic_message': diagnostic_message,
            'energy_impact': energy_impact,
            'color_code': color_code
            }
        result.insert_table_row('Hot_water_RCx', dx_table)
        result.log(diagnostic_message, logging.INFO)
        self.timestamp = []
        self.loop_dp_stpt_values = []
        return result
