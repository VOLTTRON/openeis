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
from datetime import timedelta as td
import sys
import logging
import dateutil.tz
from openeis.applications.utils import conversion_utils as cu
from openeis.applications import (DrivenApplicationBaseClass,
                                  OutputDescriptor,
                                  ConfigDescriptor,
                                  InputDescriptor,
                                  Results,
                                  Descriptor,
                                  reports)

ECON1 = 'Temperature Sensor Dx'
ECON2 = 'Not Economizing When Unit Should Dx'
ECON3 = 'Economizing When Unit Should Not Dx'
ECON4 = 'Excess Outdoor-air Intake Dx'
ECON5 = 'Insufficient Outdoor-air Intake Dx'
DX = "/diagnostic message"
EI = "/energy impact"
dx_list = [ECON1, ECON2, ECON3, ECON4, ECON5]
RED = "RED"
GREY = "GREY"
GREEN = "GREEN"
WHITE = "WHITE"
FAN_OFF = -99.3
OAF = -89.2
OAT_LIMIT = -79.2
RAT_LIMIT = -69.2
MAT_LIMIT = -59.2
TEMP_SENSOR = -49.2

available_tz = {1: 'US/Pacific', 2: 'US/Mountain', 3: 'US/Central', 4: 'US/Eastern'}


def create_table_key(table_name, timestamp):
    return "&".join([table_name, timestamp.isoformat()])


def data_builder(value_tuple, point_name):
    value_list = []
    for item in value_tuple:
        value_list.append(item[1])
    return value_list


def create_dx_table(cur_time, diagnostic, message, color_code, energy_impact=None):
    dx_table = dict(datetime=str(cur_time),
                    diagnostic_name=diagnostic,
                    diagnostic_message=message,
                    energy_impact=energy_impact,
                    color_code=color_code)
    return dx_table


def mean(list_like):
    return sum(list_like)/len(list_like)


class Application(DrivenApplicationBaseClass):
    """
    Application to detect and correct operational problems for AHUs/RTUs.

    This application uses metered data from zones server by an AHU/RTU
    to detect operational problems and where applicable correct these problems
    by modifying set points.  When auto-correction cannot be applied then
    a message detailing the diagnostic results will be made available to
    the building operator.
    """
    # Diagnostic Point Names (Must match OpenEIS data-type names)
    fan_status_name = 'fan_status'
    oat_name = 'oa_temp'
    mat_name = 'ma_temp'
    rat_name = 'ra_temp'
    oad_sig_name = 'damper_signal'
    cool_call_name = 'cool_call'
    fan_sp_name = 'fan_speedcmd'
    timestamp = 'date'
    oaf_name = 'oa_fraction'
    cc_valve_name = 'cc_valve_pos'
    dat_name = 'da_temp'
    dat_stpt_name = 'dat_stpt_name'
    #TODO: temp set data_window=1 to test

    def __init__(self, *args,
                 open_damper_time=5, low_supply_fan_threshold=15.0,
                 temp_damper_threshold=90.0,

                 a0_sensitivity="all", a1_local_tz=1,
                 a2_data_window=30, a3_no_required_data=20, a4_device_type='AHU',
                 a5_economizer_type='DDB', a6_econ_hl_temp=65.0, a7_temp_deadband=1.0, a8_eer=10.0, a9_rated_cfm=1000.0,
                 aa_oaf_temperature_threshold=5.0, ab_cooling_enabled_threshold=5.0, ac_constant_volume=0,

                 b0_temp_difference_threshold=4.0, b1_mat_low_threshold=50.0,
                 b2_mat_high_threshold=90.0, b3_rat_low_threshold=50.0,
                 b4_rat_high_threshold=90.0, b5_oat_low_threshold=30.0,
                 b6_oat_high_threshold=100.0, b7_oat_mat_check=6.0,

                 c0_open_damper_threshold=90.0, c1_oaf_economizing_threshold=25.0,
                 c2_minimum_damper_setpoint=15.0, c3_excess_damper_threshold=20.0,
                 c4_desired_oaf=10.0, c5_excess_oaf_threshold=20.0,
                 d1_ventilation_oaf_threshold=5.0,
                 **kwargs):
        # initialize user configurable parameters.
        super().__init__(*args, **kwargs)
        # OpenEIS Spefic parameters
        self.default_building_name_used = False
        try:
            self.cur_tz = available_tz[a1_local_tz]
        except:
            self.cur_tz = 'UTC'

        def get_or_none(name):
            value = kwargs["point_mapping"].get(name, None)
            if value:
                value = value.lower()
            return value

        self.device_type = a4_device_type.lower()
        if self.device_type not in ("ahu", "rtu"):
            raise Exception('device_type must be specified as "AHU" or "RTU" in configuration file.')
            sys.exit()

        # OpenEIS specfic change
        # Application.analysis = analysis = kwargs["analysis_name"]
        Application.analysis = analysis = "EconomizerAIRCx"

        if a0_sensitivity not in ["all", 'high', 'normal', 'low']:
            a0_sensitivity = None

        if self.fan_sp_name is None and self.fan_status_name is None:
            raise Exception("SupplyFanStatus or SupplyFanSpeed are required to verify AHU status.")

        # Precondition flags
        self.oaf_condition = None
        self.unit_status = None
        self.sensor_limit = None
        self.temp_sensor_problem = None

        # Time based configurations
        self.data_window = data_window = td(minutes=a2_data_window)
        open_damper_time = td(minutes=open_damper_time)
        no_required_data = a3_no_required_data

        # diagnostic threshold parameters
        self.economizer_type = a5_economizer_type.lower()
        self.econ_hl_temp = float(a6_econ_hl_temp) if self.economizer_type == "hl" else None
        self.constant_volume = ac_constant_volume

        self.cooling_enabled_threshold = ab_cooling_enabled_threshold
        self.low_supply_fan_threshold = low_supply_fan_threshold
        self.oaf_temperature_threshold = aa_oaf_temperature_threshold
        self.oat_thresholds = [b5_oat_low_threshold, b6_oat_high_threshold]
        self.rat_thresholds = [b3_rat_low_threshold, b4_rat_high_threshold]
        self.mat_thresholds = [b1_mat_low_threshold, b2_mat_high_threshold]
        self.temp_band = a7_temp_deadband
        cfm = float(a9_rated_cfm)
        eer = float(a8_eer)

        if a0_sensitivity is not None and a0_sensitivity != "custom":
            temp_difference_threshold = {
                'low': max(b0_temp_difference_threshold + 2.0, 6.0),
                'normal': max(b0_temp_difference_threshold, 4.0),
                'high': max(b0_temp_difference_threshold - 2.0, 2.0)
            }
            oat_mat_check = {
                'low': b7_oat_mat_check * 1.5,
                'normal': b7_oat_mat_check,
                'high': b7_oat_mat_check * 0.5
            }
            oaf_economizing_threshold = {
                'low': 90.0 - 3.0 * c2_minimum_damper_setpoint,
                'normal': 90.0 - 2.0 * c2_minimum_damper_setpoint,
                'high': 90.0 - c2_minimum_damper_setpoint
            }
            open_damper_threshold = {
                'low': max(c2_minimum_damper_setpoint * 0.5, 10.0),
                'normal': max(c2_minimum_damper_setpoint, 20.0),
                'high': max(c2_minimum_damper_setpoint * 2.0, 40.0)
            }
            excess_damper_threshold = {
                'low': c2_minimum_damper_setpoint * 2.0,
                'normal': c2_minimum_damper_setpoint,
                'high': c2_minimum_damper_setpoint * 0.5
            }
            excess_oaf_threshold = {
                'low': c2_minimum_damper_setpoint * 2.0 + 10.0,
                'normal': c2_minimum_damper_setpoint + 10.0,
                'high': c2_minimum_damper_setpoint * 0.5 + 10.0
            }
            ventilation_oaf_threshold = {
                'low': c4_desired_oaf * 0.75,
                'normal': c4_desired_oaf * 0.5,
                'high': c4_desired_oaf * 0.25
            }
            if a0_sensitivity != "all":
                remove_sensitivities = [item for item in ['high', 'normal', 'low'] if item != a0_sensitivity]
                if remove_sensitivities:
                    for remove in remove_sensitivities:
                        temp_difference_threshold.pop(remove)
                        oat_mat_check.pop(remove)
                        oaf_economizing_threshold.pop(remove)
                        open_damper_threshold.pop(remove)
                        excess_damper_threshold.pop(remove)
                        excess_oaf_threshold.pop(remove)
                        ventilation_oaf_threshold.pop(remove)
        elif a0_sensitivity == "custom":
            temp_difference_threshold = {'normal': b0_temp_difference_threshold}
            oat_mat_check = {'normal': b7_oat_mat_check}
            oaf_economizing_threshold = {'normal': c1_oaf_economizing_threshold}
            open_damper_threshold = {'normal': c0_open_damper_threshold}
            excess_damper_threshold = {'normal': c3_excess_damper_threshold}
            excess_oaf_threshold = {'normal': c5_excess_oaf_threshold}
            ventilation_oaf_threshold = {'normal': d1_ventilation_oaf_threshold}
        else:
            temp_difference_threshold = {'normal': b0_temp_difference_threshold}
            oat_mat_check = {'normal': b7_oat_mat_check}
            oaf_economizing_threshold = {'normal': 90.0 - 2.0 * c2_minimum_damper_setpoint}
            open_damper_threshold = {'normal': max(c2_minimum_damper_setpoint, 10.0)}
            excess_damper_threshold = {'normal': c2_minimum_damper_setpoint}
            excess_oaf_threshold = {'normal': c2_minimum_damper_setpoint + 10.0}
            ventilation_oaf_threshold = {'normal': c4_desired_oaf * 0.5}

        Application.sensitivities = temp_difference_threshold.keys()

        self.econ1 = TempSensorDx(data_window, no_required_data,
                                  temp_difference_threshold, open_damper_time,
                                  oat_mat_check, temp_damper_threshold,
                                  analysis)

        self.econ2 = EconCorrectlyOn(oaf_economizing_threshold,
                                     open_damper_threshold,
                                     c2_minimum_damper_setpoint,
                                     data_window, no_required_data,
                                     cfm, eer, analysis)

        self.econ3 = EconCorrectlyOff(data_window, no_required_data,
                                      c2_minimum_damper_setpoint,
                                      excess_damper_threshold,
                                      c4_desired_oaf, cfm, eer, analysis)

        self.econ4 = ExcessOA(data_window, no_required_data,
                              excess_oaf_threshold,
                              c2_minimum_damper_setpoint,
                              excess_damper_threshold,
                              c4_desired_oaf, cfm, eer, analysis)

        self.econ5 = InsufficientOA(data_window, no_required_data,
                                    ventilation_oaf_threshold, c4_desired_oaf,
                                    analysis)

    @classmethod
    def get_config_parameters(cls):
        """
        Generate required configuration parameters with description
        for user
        :return:
        """
        dgr_sym = u'\N{DEGREE SIGN}'
        return {
            'a0_sensitivity':
            ConfigDescriptor(str,
                             'Sensitivity: values can be all (produces a result for low, normal, and high), '
                             'low, normal, high, or custom. Setting sensitivity to custom allows you to enter your '
                             'own values for all threshold values',
                              value_default="all"),
            'a1_local_tz':
            ConfigDescriptor(int,
                            "Integer corresponding to local timezone: [1: 'US/Pacific', 2: 'US/Mountain', 3: 'US/Central', 4: 'US/Eastern']",
                             value_default=1),
            'a2_data_window':
            ConfigDescriptor(int,
                             'Minimum Elapsed time for analysis '
                             '(minutes)', value_default=30),
            # 'open_damper_time':
            # ConfigDescriptor(float,
            #                'Delay time for steady-state conditions '
            #                 '(minutes)', value_default=5),
            # 'temp_damper_threshold':
            # ConfigDescriptor(float,
            #                 'Damper position to check for OAT/MAT '
            #                 'consistency (%)',
            #                 value_default=90.0),

            'a3_no_required_data':
            ConfigDescriptor(int,
                             'Number of required data measurements to '
                             'perform diagnostic',
                             value_default=20),
            'a4_device_type':
            ConfigDescriptor(str,
                            'Device type - RTU or AHU (default is AHU)',
                             value_default='AHU'),
            'a5_economizer_type':
            ConfigDescriptor(str,
                             'Economizer type - differential dry bulb (DDB) '
                             'or High limit set point (HL)',
                             value_default='DDB'),
            'a6_econ_hl_temp':
            ConfigDescriptor(float,
                             'High limit (HL) temperature set point for '
                             'HL economizer ({drg}F)'.format(drg=dgr_sym),
                             value_default=60.0),
            'a7_temp_deadband':
            ConfigDescriptor(float,
                             'Economizer control temperature dead-band ({drg}F)'.format(drg=dgr_sym),
                             value_default=1.0),
            'a8_eer':
            ConfigDescriptor(float,
                             'AHU/RTU rated Energy Efficiency Ratio (EER)',
                             value_default=10.0),
            'a9_rated_cfm':
            ConfigDescriptor(float,
                             'Rated CFM of supply fan at 100% supply fan speed (CFM)',
                             value_default=1000.0),
            'aa_oaf_temperature_threshold':
            ConfigDescriptor(float,
                             'Required difference between outdoor-air and '
                             'return-air temperatures for an accurate '
                             'diagnostic ({drg}F)'.format(drg=dgr_sym),
                              value_default=5.0),
            'ab_cooling_enabled_threshold':
            ConfigDescriptor(float,
                             'Minimum AHU chilled water valve position for '
                             'determining if the AHU is in a cooling mode (%)',
                             value_default=5.0),
            'ac_constant_volume':
            ConfigDescriptor(int,
                             'Boolen value to indicate if the supply '
                             'fan is runs at a constant speed (does not have '
                             'a variable frequency drive)',
                             value_default=0),
            'b0_temp_difference_threshold':
            ConfigDescriptor(float,
                             "'Temperature Sensor Dx' - Threshold for "
                             "detecting temperature sensor problems "
                             "({drg}F)".format(drg=dgr_sym),
                             value_default=4.0),
            'b1_mat_low_threshold':
            ConfigDescriptor(float,
                             'Mixed-air temperature sensor low limit ({drg}F)'
                             .format(drg=dgr_sym),
                             value_default=50.0),
            'b2_mat_high_threshold':
            ConfigDescriptor(float,
                             'Mixed-air temperature sensor high limit ({drg}F)'
                             .format(drg=dgr_sym),
                             value_default=90.0),
            'b3_rat_low_threshold':
            ConfigDescriptor(float,
                             'Return-air temperature sensor low limit ({drg}F)'
                             .format(drg=dgr_sym),
                             value_default=50),
            'b4_rat_high_threshold':
            ConfigDescriptor(float,
                             'Return-air temperature sensor high limit '
                             '({drg}F)'.format(drg=dgr_sym),
                             value_default=90.0),
            'b5_oat_low_threshold':
            ConfigDescriptor(float,
                             'Outdoor-air temperature sensor low limit '
                             '({drg}F)'.format(drg=dgr_sym),
                             value_default=30.0),
            'b6_oat_high_threshold':
            ConfigDescriptor(float,
                             'Outdoor-air temperature sensor high limit '
                             '({drg}F)'.format(drg=dgr_sym),
                             value_default=100.0),
            'b7_oat_mat_check':
            ConfigDescriptor(float,
                             "'Temperature Sensor Dx' - Threshold value for "
                             "temperature difference between outdoor-air "
                             "temperature and mixed-air temperature reading "
                             "when the outdoor-air damper is near 100% open "
                             "({drg}F)".format(drg=dgr_sym),
                             value_default=6.0),
            'c0_open_damper_threshold':
            ConfigDescriptor(float,
                             "'Economizing When Unit Should Dx' - Threshold for "
                             "the outdoor-air damper position when conditions "
                             "are favorable for economizing – value above which "
                             "the damper is considered open for economizing (%)",
                             value_default=75.0),
            'c1_oaf_economizing_threshold':
            ConfigDescriptor(float,
                             "'Economizing When Unit Should Dx' - Value "
                             "below 100% in which the outdoor-air fraction, "
                             "as a percent, is considered insufficient for "
                             "economizing (%)",
                              value_default=25.0),
            'c2_minimum_damper_setpoint':
            ConfigDescriptor(float,
                             'Minimum outdoor-air damper set point (%)',
                             value_default=15.0),
            'c3_excess_damper_threshold':
            ConfigDescriptor(float,
                             "'Economizing When Unit Should Not Dx' - "
                             "Threshold value above the minimum outdoor-air "
                             "damper set point at which a fault will be identified "
                             "- when conditions are not favorable for economizing "
                             "or the AHU/RTU is not cooling (%)",
                             value_default=20.0),
            'c4_desired_oaf':
            ConfigDescriptor(float,
                             'The desired minimum outdoor-air fraction as a percent (%)',
                             value_default=10.0),
            'c5_excess_oaf_threshold':
            ConfigDescriptor(float,
                             "'Excess Outdoor-air Intake Dx' - Threshold value "
                             "above the desired minimum outdoor-air fraction as "
                             "a percent where a fault will be indicated, when "
                             "AHU/RTU is not economizing (%)",
                             value_default=30.0),
            'd1_ventilation_oaf_threshold':
            ConfigDescriptor(float,
                             "'Insufficient Outdoor-air Intake Dx' - The "
                             "value below the desired minimum outdoor-air "
                             "fraction (percent) where a fault will be "
                             "identified (%)",
                             value_default=5.0)
            }

    @classmethod
    def get_self_descriptor(cls):
        name = 'AIRCx for Economizer HVAC Systems'
        desc = 'Automated Retro-commisioning Diagnostics for HVAC Economizer Systems'
        note = 'Sensitivity: value can be all, low, normal, high, or custom. ' \
               'Setting values of all, low, normal, or high will ' \
               'ignore other threshold values.'
        return Descriptor(name=name, description=desc, note=note)

    @classmethod
    def required_input(cls):
        """
        Generate required inputs with description for user.
        :return:
        """
        return {
            cls.fan_status_name:
            InputDescriptor('SupplyFanStatus',
                            'AHU Supply Fan Status (required for Dx)', count_min=0),
            cls.fan_sp_name:
            InputDescriptor('SupplyFanSpeed',
                            'AHU supply fan speed', count_min=0),
            cls.oat_name:
            InputDescriptor('OutdoorAirTemperature',
                            'AHU or building outdoor-air temperature',
                            count_min=1),
            cls.mat_name:
            InputDescriptor('MixedAirTemperature',
                            'AHU mixed-air temperature',
                            count_min=1),
            cls.rat_name:
            InputDescriptor('ReturnAirTemperature',
                            'AHU return-air temperature', count_min=1),
            cls.oad_sig_name:
            InputDescriptor('OutdoorDamperSignal',
                            'AHU outdoor-air damper signal (required for Dx)', count_min=0),
            cls.cc_valve_name:
            InputDescriptor('CoolingCoilValvePosition',
                            'AHU chilled water cooling coil valve command. '
                            'CoolingCoilValvePosition (for AHUs) or '
                            'CoolingCall (for RTUs) is required for Dx.', count_min=0),
            cls.cool_call_name:
            InputDescriptor(
                'CoolingCall',
                'RTU thermostat cooling call command or compressor command '
                '(this includes AHUs that utilize DX cooling). '
                'CoolingCoilValvePosition (AHUs) or CoolingCall (RTUs) '
                'is required for Dx.',
                count_min=0),
            cls.dat_name:
            InputDescriptor('DischargeAirTemperature',
                            'AHU discharge-air temperature', count_min=0),
            cls.dat_stpt_name:
            InputDescriptor('DischargeAirTemperatureSetPoint',
                            'AHU discharge-air temperature setpoint', count_min=0)

        }

    def reports(self):
        """
        Called by UI to create Viz.

        Describes how to present output to user
        :return:
        """
        report = reports.Report('Retuning Report')
        report.add_element(reports.RetroCommissioningAFDDEcam(
            table_name="EconomizerAIRCx"))
        return [report]

    @classmethod
    def output_format(cls, input_object):
        '''Called when application is staged.

        Output will have the date-time and  error-message.
        '''
        result = super().output_format(input_object)

        topics = input_object.get_topics()
        diagnostic_topic = topics[cls.oat_name][0]
        diagnostic_topic_parts = diagnostic_topic.split('/')
        output_topic_base = diagnostic_topic_parts[:-1]
        datetime_topic = '/'.join(output_topic_base + ['EconomizerAIRCx', cls.timestamp])
        message_topic = '/'.join(output_topic_base +['EconomizerAIRCx', 'message'])
        diagnostic_name = '/'.join(output_topic_base+['EconomizerAIRCx', 'diagnostic_name'])
        energy_impact = '/'.join(output_topic_base+['EconomizerAIRCx', 'energy_impact'])
        color_code = '/'.join(output_topic_base+['EconomizerAIRCx', 'color_code'])
        oat_topic = '/'.join(output_topic_base+['EconomizerAIRCx', cls.oat_name])
        mat_topic = '/'.join(output_topic_base+['EconomizerAIRCx', cls.mat_name])
        rat_topic = '/'.join(output_topic_base+['EconomizerAIRCx', cls.rat_name])
        dat_topic = '/'.join(output_topic_base+['EconomizerAIRCx', cls.dat_name])
        datstpt_topic = '/'.join(output_topic_base+['EconomizerAIRCx', cls.dat_stpt_name])
        fsp_topic = '/'.join(output_topic_base+['EconomizerAIRCx', cls.fan_sp_name])
        fst_topic = '/'.join(output_topic_base+['EconomizerAIRCx', cls.fan_status_name])
        od_topic = '/'.join(output_topic_base+['EconomizerAIRCx', cls.oad_sig_name])
        ccv_topic = '/'.join(output_topic_base+['EconomizerAIRCx', cls.cool_call_name])
        oaf_topic = '/'.join(output_topic_base+['EconomizerAIRCx', cls.oaf_name])
        output_needs = {
            'EconomizerAIRCx': {
                'datetime': OutputDescriptor('string', datetime_topic),
                'diagnostic_name': OutputDescriptor('string', diagnostic_name),
                'diagnostic_message': OutputDescriptor('string', message_topic),
                'energy_impact': OutputDescriptor('string', energy_impact),
                'color_code': OutputDescriptor('string', color_code),
                'OutdoorAirTemperature': OutputDescriptor('float', oat_topic),
                'MixedAirTemperature': OutputDescriptor('float', mat_topic),
                'ReturnAirTemperature': OutputDescriptor('float', rat_topic),
                'DischargeAirTemperature': OutputDescriptor('float', dat_topic),
                'DischargeAirTemperatureSetPoint': OutputDescriptor('float', datstpt_topic),
                'SupplyFanStatus': OutputDescriptor('float', fst_topic),
                'SupplyFanSpeed': OutputDescriptor('float', fsp_topic),
                'OutdoorDamper': OutputDescriptor('float', od_topic),
                'CCV': OutputDescriptor('float', ccv_topic),
                'OutdoorAirFraction': OutputDescriptor('float', oaf_topic)
            }
        }

        result.update(output_needs)
        return result

    def create_units_dict(self):
        """
        OpenEIS specific function to obtain units for temperature sensors.
        :return:
        """
        base_topic = self.inp.get_topics()
        meta_topics = self.inp.get_topics_meta()
        unit_dict = {
            self.oat_name: meta_topics[self.oat_name][base_topic[self.oat_name][0]]['unit'],
            self.mat_name: meta_topics[self.mat_name][base_topic[self.mat_name][0]]['unit'],
            self.rat_name: meta_topics[self.rat_name][base_topic[self.rat_name][0]]['unit']
        }
        if len(base_topic[self.dat_name]) > 0:
            unit_dict[self.dat_name] = meta_topics[self.dat_name][base_topic[self.dat_name][0]]['unit']
        if len(base_topic[self.dat_stpt_name]) > 0:
            unit_dict[self.dat_stpt_name] = meta_topics[self.dat_stpt_name][base_topic[self.dat_stpt_name][0]]['unit']
        return unit_dict

    def run(self, cur_time, points):
        """
        Main run method that is called by the DrivenBaseClass.

        run receives a dictionary of data 'points' and an associated timestamp
        for the data cur_time'.  run then passes the appropriate data to
        each diagnostic when calling
        the diagnostic message.
        :param cur_time:
        :param points:
        :return:
        """
        device_dict = {}
        dx_result = Results()

        # OpenEIS spefic block
        to_zone = dateutil.tz.gettz(self.cur_tz)
        cur_time = cur_time.astimezone(to_zone)
        unit_dict = self.create_units_dict()
        # End OpenEIS specific block

        for point, value in points.items():
            point_device = [name.lower() for name in point.split("&&&")]
            if point_device[0] not in device_dict:
                device_dict[point_device[0]] = [(point_device[1], value)]
            else:
                device_dict[point_device[0]].append((point_device[1], value))

        damper_data = []
        oat_data = []
        mat_data = []
        rat_data = []
        cooling_data = []
        fan_sp_data = []
        fan_status_data = []
        missing_data = []

        # OpenEIS Points
        dat_data = []
        dat_stpt_data = []
        ccv_data = []

        for key, value in device_dict.items():
            data_name = key
            if value is None:
                continue
            if data_name == self.fan_status_name: #Fan status
                fan_status_data = data_builder(value, data_name)
            elif data_name == self.oad_sig_name:
                damper_data = data_builder(value, data_name)
            elif data_name == self.oat_name:
                oat_data = data_builder(value, data_name)
            elif data_name == self.mat_name:
                mat_data = data_builder(value, data_name)
            elif data_name == self.rat_name:
                rat_data = data_builder(value, data_name)
            elif data_name == self.cool_call_name:
                cooling_data = data_builder(value, data_name)
            elif data_name == self.cc_valve_name:
                ccv_data = data_builder(value, data_name)
            elif data_name == self.fan_sp_name:
                fan_sp_data = data_builder(value, data_name)
            elif data_name == self.dat_stpt_name:
                dat_stpt_data = data_builder(value, data_name)
            elif data_name == self.dat_name:
                dat_data = data_builder(value, data_name)

        if not oat_data:
            missing_data.append(self.oat_name)
        if not rat_data:
            missing_data.append(self.rat_name)
        if not mat_data:
            missing_data.append(self.mat_name)
        if not damper_data:
            missing_data.append(self.oad_sig_name)
        if not fan_status_data and not fan_sp_data:
            missing_data.append(self.fan_status_name)

        # OpenEIS specific block [Charting functionality]
        if 'celcius' in unit_dict.values() or 'kelvin' in unit_dict.values():
            if unit_dict[self.oat_name] == 'celcius':
                oat_data = cu.convertCelciusToFahrenheit(oat_data)
            elif unit_dict[self.oat_name] == 'kelvin':
                oat_data = cu.convertKelvinToCelcius(cu.convertCelciusToFahrenheit(oat_data))
            if unit_dict.get(self.mat_name, "") == 'celcius':
                mat_data = cu.convertCelciusToFahrenheit(mat_data)
            elif unit_dict.get(self.mat_name, "") == 'kelvin':
                mat_data = cu.convertKelvinToCelcius(cu.convertCelciusToFahrenheit(mat_data))
            if unit_dict.get(self.rat_name, "") == 'celcius':
                rat_data = cu.convertCelciusToFahrenheit(rat_data)
            elif unit_dict.get(self.rat_name, "") == 'kelvin':
                rat_data = cu.convertKelvinToCelcius(cu.convertCelciusToFahrenheit(rat_data))
            if unit_dict.get(self.dat_name, "") == 'celcius':
                dat_data = cu.convertCelciusToFahrenheit(dat_data)
            elif unit_dict.get(self.dat_name, "") == 'kelvin':
                dat_data = cu.convertKelvinToCelcius(cu.convertCelciusToFahrenheit(dat_data))
            if unit_dict.get(self.dat_stpt_name, "") == 'celcius':
                dat_stpt_data = cu.convertCelciusToFahrenheit(dat_stpt_data)
            elif unit_dict[self.dat_stpt_name] == 'kelvin':
                dat_stpt_data = cu.convertKelvinToCelcius(cu.convertCelciusToFahrenheit(dat_stpt_data))

        oat = mean(oat_data)
        mat = mean(mat_data)
        rat = mean(rat_data)

        oaf = (mat - rat)/(oat - rat) if (oat - rat) != 0 else 0
        dx_result.log("Calcualted OAF is {} for timesamp {}".format(oaf, cur_time))
        oaf = max(0.0, min(1.0, oaf)) * 100.0

        dat = dat_stpt = None
        fanstatus = fan_sp = ccv = None
        oad = None

        if dat_data:
            dat = mean(dat_data)
        if dat_stpt_data:
            dat_stpt= mean(dat_stpt_data)
        if fan_status_data:
            fanstatus = max(fan_status_data)
        if fan_sp_data:
            fan_sp = mean(fan_sp_data)
        if damper_data:
            oad = mean(damper_data)
        if ccv_data:
            ccv = mean(ccv_data)

        if self.device_type.lower() == "ahu":
            if ccv_data:
                cooling_data = ccv_data
            elif cooling_data:
                self.device_type = "rtu"
            else:
                missing_data.append(self.cc_valve_name)
        elif self.device_type.lower() == "rtu":
            if not cooling_data:
                if ccv_data:
                    cooling_data = ccv_data
                    self.device_type = "ahu"
                else:
                    missing_data.append(self.cool_call_name)

        ecam_data = {
            'datetime': str(cur_time),
            'OutdoorAirTemperature': oat,
            'MixedAirTemperature': mat,
            'ReturnAirTemperature': rat,
            'OutdoorAirFraction': oaf,
            'DischargeAirTemperature': None if dat is None else dat,
            'DischargeAirTemperatureSetPoint': None if dat_stpt is None else dat_stpt,
            'SupplyFanStatus': None if fanstatus is None else fanstatus,
            'SupplyFanSpeed': None if fan_sp is None else fan_sp,
            'OutdoorDamper': None if oad is None else oad,
            'CCV': None if ccv is None else ccv,
            'diagnostic_name': None,
            'diagnostic_message': None,
            'energy_impact': None,
            'color_code': None
        }

        ####Start EconomizerAIRCx######
        current_fan_status, fan_sp = self.check_fan_status(fan_status_data, fan_sp_data, cur_time)
        dx_result = self.check_elapsed_time(dx_result, cur_time, self.unit_status, FAN_OFF, ecam_data)

        if missing_data:
            dx_result.log("Missing data from publish: {}".format(missing_data))
            return insert_ecam_data(dx_result, {}, ecam_data)

        if not current_fan_status:
            dx_result.log("Supply fan is off: {}".format(cur_time))
            return insert_ecam_data(dx_result, {}, ecam_data)
        else:
            dx_result.log("Supply fan is on: {}".format(cur_time))

        if fan_sp is None and self.constant_volume:
            fan_sp = 100.0

        self.check_temperature_condition(oat, rat, cur_time)
        dx_result = self.check_elapsed_time(dx_result, cur_time, self.oaf_condition, OAF, ecam_data)

        if self.oaf_condition:
            dx_result.log("OAT and RAT readings are too close.")
            return insert_ecam_data(dx_result, {}, ecam_data)

        limit_condition = self.sensor_limit_check(oat, rat, mat, cur_time)
        dx_result = self.check_elapsed_time(dx_result, cur_time, self.sensor_limit, limit_condition[1], ecam_data)
        if limit_condition[0]:
            dx_result.log("Temperature sensor is outside of bounds: {} -- {}".format(limit_condition,
                                                                                     self.sensor_limit))
            return insert_ecam_data(dx_result, {}, ecam_data)

        dx_result, self.temp_sensor_problem = self.econ1.econ_alg1(dx_result, oat, rat, mat, oad, cur_time, ecam_data)
        econ_condition, cool_call = self.determine_cooling_condition(cooling_data, oat, rat)
        dx_result.log("Cool call: {} - Economizer status: {}".format(cool_call, econ_condition))

        if self.temp_sensor_problem is not None and not self.temp_sensor_problem:
            dx_result = self.econ2.econ_alg2(dx_result, cool_call, oat, rat, mat,
                                             oad, econ_condition, cur_time, fan_sp, ecam_data)

            dx_result = self.econ3.econ_alg3(dx_result, oat, rat, mat, oad,
                                             econ_condition, cur_time, fan_sp, ecam_data)

            dx_result = self.econ4.econ_alg4(dx_result, oat, rat, mat, oad,
                                             econ_condition, cur_time, fan_sp, ecam_data)

            dx_result = self.econ5.econ_alg5(dx_result, oat, rat, mat, cur_time, ecam_data)
        elif self.temp_sensor_problem:
            self.pre_conditions(dx_list[1:], TEMP_SENSOR, cur_time, dx_result)
            self.econ2.clear_data()
            self.econ3.clear_data()
            self.econ4.clear_data()
            self.econ5.clear_data()
        return insert_ecam_data(dx_result, {}, ecam_data)

    def clear_all(self):
        """
        Reinitialize all data arrays for diagnostics.
        :return:
        """
        self.econ1.clear_data()
        self.econ2.clear_data()
        self.econ3.clear_data()
        self.econ4.clear_data()
        self.econ5.clear_data()
        self.temp_sensor_problem = None
        self.unit_status = None
        self.oaf_condition = None
        self.sensor_limit = None
        return

    def determine_cooling_condition(self, cooling_data, oat, rat):
        """
        Determine if the unit is in a cooling mode and if conditions
        are favorable for economizing.
        :param cooling_data:
        :param oat:
        :param rat:
        :return:
        """
        if self.device_type == "ahu":
            clg_vlv_pos = mean(cooling_data)
            cool_call = True if clg_vlv_pos > self.cooling_enabled_threshold else False
        elif self.device_type == "rtu":
            cool_call = int(max(cooling_data))

        if self.economizer_type == "ddb":
            econ_condition = oat < (rat - self.temp_band)
        else:
            econ_condition = oat < (self.econ_hl_temp - self.temp_band)

        return econ_condition, cool_call

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
            supply_fan_status = 1 if fan_speed > self.low_supply_fan_threshold else 0

        if not supply_fan_status:
            if self.unit_status is None:
                self.unit_status = cur_time
        else:
            self.unit_status = None
        return supply_fan_status, fan_speed

    def check_temperature_condition(self, oat, rat, cur_time):
        """
        Ensure the OAT and RAT have minimum difference to allow
        for a conclusive diagnostic.
        :param oat:
        :param rat:
        :param cur_time:
        :return:
        """
        if abs(oat - rat) < self.oaf_temperature_threshold:
            if self.oaf_condition is None:
                self.oaf_condition = cur_time
        else:
            self.oaf_condition = None
        return

    def check_elapsed_time(self, dx_result, cur_time, condition, message, ecam_data):
        """
        Check for persistence of failure to meet pre-conditions for diagnostics.
        :param dx_result:
        :param cur_time:
        :param condition:
        :param message:
        :return:
        """
        elapsed_time = cur_time - condition if condition is not None else td(minutes=0)
        if elapsed_time >= self.data_window:
            dx_result = self.pre_conditions(dx_list, message, cur_time, dx_result, ecam_data)
            self.clear_all()
        return dx_result

    def pre_conditions(self, diagnostics, message, cur_time, dx_result, ecam_data):
        """
        Publish pre-conditions not met message.
        :param diagnostics:
        :param message:
        :param cur_time:
        :param dx_result:
        :return:
        """
        dx_msg = {}
        color_code_dict = {}
        for sensitivity in Application.sensitivities:
            dx_msg[sensitivity] = message
            color_code_dict[sensitivity] = GREY if message != FAN_OFF else WHITE

        for diagnostic in diagnostics:
            # dx_table = {diagnostic + DX: dx_msg}
            # table_key = create_table_key(self.analysis, cur_time)
            # dx_result.insert_table_row(table_key, dx_table)
            dx_table = create_dx_table(cur_time, diagnostic, dx_msg, color_code_dict, energy_impact=None)
            dx_result = insert_ecam_data(dx_result, dx_table, ecam_data)
        return dx_result

    def sensor_limit_check(self, oat, rat, mat, cur_time):
        """
        Check temperature limits on sensors.
        :param oat:
        :param rat:
        :param mat:
        :param cur_time:
        :return:
        """
        sensor_limit = (False, None)
        if oat < self.oat_thresholds[0] or oat > self.oat_thresholds[1]:
            sensor_limit = (True, OAT_LIMIT)
        elif rat < self.rat_thresholds[0] or rat > self.rat_thresholds[1]:
            sensor_limit = (True, RAT_LIMIT)
        elif mat < self.mat_thresholds[0] or mat > self.mat_thresholds[1]:
            sensor_limit = (True, MAT_LIMIT)

        if sensor_limit[0]:
            if self.sensor_limit is None:
                self.sensor_limit = cur_time
        else:
            self.sensor_limit = None
        return sensor_limit


def insert_ecam_data(diagnostic_result, data, ecam_data):
        merged_data = merge_ecam_data(data, ecam_data)
        diagnostic_result.insert_table_row('EconomizerAIRCx', merged_data)
        return diagnostic_result

def merge_ecam_data(data, ecam_data):
    merged_data = ecam_data.copy()
    merged_data.update(data)
    return merged_data


class TempSensorDx(object):
    """
    Air-side HVAC temperature sensor diagnostic for AHU/RTU systems.

    TempSensorDx uses metered data from a BAS or controller to
    diagnose if any of the temperature sensors for an AHU/RTU are accurate and
    reliable.
    """

    def __init__(self, data_window, no_required_data, temp_diff_thr, open_damper_time,
                 oat_mat_check, temp_damper_threshold, analysis):
        self.oat_values = []
        self.rat_values = []
        self.mat_values = []
        self.timestamp = []

        self.temp_sensor_problem = None
        self.analysis = analysis
        self.max_dx_time = td(minutes=60)

        # Application thresholds (Configurable)
        self.data_window = data_window
        self.no_required_data = no_required_data
        self.oat_mat_check = oat_mat_check
        self.temp_diff_thr = temp_diff_thr
        self.sensor_damper_dx = DamperSensorInconsistencyDx(data_window,
                                                            no_required_data,
                                                            open_damper_time,
                                                            oat_mat_check,
                                                            temp_damper_threshold,
                                                            analysis)

    def econ_alg1(self, dx_result, oat, rat, mat, oad, cur_time, ecam_data):
        """
        Check app. pre-quisites and manage data set for analysis.
        :param dx_result:
        :param oat:
        :param rat:
        :param mat:
        :param oad:
        :param cur_time:
        :return:
        """
        self.oat_values.append(oat)
        self.mat_values.append(mat)
        self.rat_values.append(rat)
        self.timestamp.append(cur_time)
        elapsed_time = self.timestamp[-1] - self.timestamp[0]

        dx_result.log("Elapsed: {} -- required: {}".format(elapsed_time, self.data_window))
        if elapsed_time >= self.data_window and len(self.timestamp) >= self.no_required_data:
            table_key = create_table_key(self.analysis, self.timestamp[-1])

            if elapsed_time > self.max_dx_time:
                dx_msg = {key: 3.2 for key in Application.sensitivities}
                color_code_dict = {key: GREY for key in Application.sensitivities}
                # dx_result.insert_table_row(table_key, {ECON1 + DX: dx_msg})
                dx_table = create_dx_table(cur_time, ECON1, dx_msg, color_code_dict)
                dx_result = insert_ecam_data(dx_result, dx_table, ecam_data)
                self.clear_data()
                return dx_result, self.temp_sensor_problem

            dx_result = self.temperature_sensor_dx(dx_result, table_key, cur_time, ecam_data)
            return dx_result, self.temp_sensor_problem

        dx_result = self.sensor_damper_dx.econ_alg(dx_result, oat, mat, oad, cur_time, ecam_data)
        return dx_result, self.temp_sensor_problem

    def aggregate_data(self):
        oa_ma = [(x - y) for x, y in zip(self.oat_values, self.mat_values)]
        ra_ma = [(x - y) for x, y in zip(self.rat_values, self.mat_values)]
        ma_oa = [(y - x) for x, y in zip(self.oat_values, self.mat_values)]
        ma_ra = [(y - x) for x, y in zip(self.rat_values, self.mat_values)]
        avg_oa_ma = mean(oa_ma)
        avg_ra_ma = mean(ra_ma)
        avg_ma_oa = mean(ma_oa)
        avg_ma_ra = mean(ma_ra)
        return avg_oa_ma, avg_ra_ma, avg_ma_oa, avg_ma_ra

    def temperature_sensor_dx(self, dx_result, table_key, cur_time, ecam_data):
        """
        Temperature sensor diagnostic.
        :param dx_result:
        :param table_key:
        :return:
        """
        avg_oa_ma, avg_ra_ma, avg_ma_oa, avg_ma_ra = self.aggregate_data()
        dx_msg = {}
        color_code_dict = {}
        for key, value in self.temp_diff_thr.items():
            if avg_oa_ma > value and avg_ra_ma > value:
                msg = ("{}: MAT is less than OAT and RAT - Sensitivity: {}".format(ECON1, key))
                color_code = RED
                result = 1.1
            elif avg_ma_oa > value and avg_ma_ra > value:
                msg = ("{}: MAT is greater than OAT and RAT - Sensitivity: {}".format(ECON1, key))
                color_code = RED
                result = 2.1
            else:
                msg = "{}: No problems were detected - Sensitivity: {}".format(ECON1, key)
                color_code = GREEN
                result = 0.0
                self.temp_sensor_problem = False
            dx_result.log(msg)
            dx_msg.update({key: result})
            color_code_dict.update({key: color_code})

        if dx_msg["normal"] > 0.0:
            self.temp_sensor_problem = True

        dx_table = create_dx_table(cur_time, ECON1, dx_msg, color_code_dict)
        dx_result = insert_ecam_data(dx_result, dx_table, ecam_data)
        # dx_table = {ECON1 + DX: diagnostic_msg}
        # dx_result.insert_table_row(table_key, dx_table)
        self.clear_data()
        return dx_result

    def clear_data(self):
        """
        Reinitialize data arrays.
        :return:
        """
        self.oat_values = []
        self.rat_values = []
        self.mat_values = []
        self.timestamp = []
        if self.temp_sensor_problem:
            self.temp_sensor_problem = None


class DamperSensorInconsistencyDx(object):
    """
    Air-side HVAC temperature sensor diagnostic for AHU/RTU systems.

    TempSensorDx uses metered data from a BAS or controller to
    diagnose if any of the temperature sensors for an AHU/RTU are accurate and
    reliable.
    """

    def __init__(self, data_window, no_required_data, open_damper_time,
                 oat_mat_check, temp_damper_threshold, analysis):
        self.oat_values = []
        self.mat_values = []
        self.timestamp = []
        self.steady_state = None
        self.open_damper_time = open_damper_time
        self.econ_time_check = open_damper_time
        self.data_window = data_window
        self.no_required_data = no_required_data
        self.oad_temperature_threshold = temp_damper_threshold
        self.oat_mat_check = oat_mat_check
        self.analysis = analysis

    def econ_alg(self, dx_result, oat, mat, oad, cur_time, ecam_data):
        """
        Check diagnostic prerequisites and manage data arrays.
        :param dx_result:
        :param oat:
        :param mat:
        :param oad:
        :param cur_time:
        :return:
        """
        if oad > self.oad_temperature_threshold:
            if self.steady_state is None:
                self.steady_state = cur_time
            elif cur_time - self.steady_state >= self.econ_time_check:
                self.oat_values.append(oat)
                self.mat_values.append(mat)
                self.timestamp.append(cur_time)
        else:
            self.steady_state = None

        elapsed_time = self.timestamp[-1] - self.timestamp[0] if self.timestamp else td(minutes=0)

        if elapsed_time >= self.data_window:
            if len(self.oat_values) > self.no_required_data:
                mat_oat_diff_list = [abs(x - y) for x, y in zip(self.oat_values, self.mat_values)]
                open_damper_check = mean(mat_oat_diff_list)
                # table_key = create_table_key(self.analysis, self.timestamp[-1])
                dx_msg = {}
                color_code_dict = {}
                for key, threshold in self.oat_mat_check.items():
                    if open_damper_check > threshold:
                        msg = "{}: The OAT and MAT at 100% OAD - Sensitivity: {}".format(ECON1, key)
                        color_code = RED
                        result = 0.1
                        dx_result.log(msg)
                    else:
                        color_code = GREEN
                        result = 0.0
                    dx_msg.update({key: result})
                    color_code_dict.update({key: color_code})

                dx_table = create_dx_table(cur_time, ECON1, dx_msg, color_code_dict)
                dx_result = insert_ecam_data(dx_result, dx_table, ecam_data)
                # dx_table = {ECON1 + DX: diagnostic_msg}
                # dx_result.insert_table_row(table_key, dx_table)
            self.clear_data()
        return dx_result

    def clear_data(self):
        """
        Reinitialize data arrays.
        :return:
        """
        self.oat_values = []
        self.mat_values = []
        self.steady_state = None
        self.timestamp = []


class EconCorrectlyOn(object):
    """Air-side HVAC economizer diagnostic for AHU/RTU systems.

    EconCorrectlyOn uses metered data from a BAS or controller to diagnose
    if an AHU/RTU is economizing when it should.
    """

    def __init__(self, oaf_economizing_threshold, open_damper_threshold,
                 minimum_damper_setpoint, data_window, no_required_data,
                 cfm, eer, analysis):
        self.oat_values = []
        self.rat_values = []
        self.mat_values = []
        self.fan_spd_values = []
        self.oad_values = []
        self.timestamp = []
        self.not_cooling = None
        self.not_economizing = None

        self.open_damper_threshold = open_damper_threshold
        self.oaf_economizing_threshold = oaf_economizing_threshold
        self.minimum_damper_setpoint = minimum_damper_setpoint
        self.data_window = data_window
        self.no_required_data = no_required_data
        self.cfm = cfm
        self.eer = eer

        self.analysis = analysis
        self.max_dx_time = td(minutes=60)

        # Application result messages
        self.alg_result_messages = [
            "Conditions are favorable for economizing but the the OAD is frequently below 100%.",
            "No problems detected.",
            "Conditions are favorable for economizing and OAD is 100% but the OAF is too low."
        ]

    def econ_alg2(self, dx_result, cooling_call, oat, rat, mat, oad, econ_condition, cur_time, fan_sp, ecam_data):
        """
        Check app. pre-quisites and assemble data set for analysis.
        :param dx_result:
        :param cooling_call:
        :param oat:
        :param rat:
        :param mat:
        :param oad:
        :param econ_condition:
        :param cur_time:
        :param fan_sp:
        :return:
        """
        dx_result, economizing = self.economizer_conditions(dx_result, cooling_call, econ_condition, cur_time, ecam_data)
        if not economizing:
            return dx_result

        self.oat_values.append(oat)
        self.mat_values.append(mat)
        self.rat_values.append(rat)
        self.oad_values.append(oad)
        self.timestamp.append(cur_time)

        fan_sp = fan_sp / 100.0 if fan_sp is not None else 1.0
        self.fan_spd_values.append(fan_sp)

        elapsed_time = self.timestamp[-1] - self.timestamp[0]
        if elapsed_time >= self.data_window and len(self.timestamp) >= self.no_required_data:
            table_key = create_table_key(self.analysis, self.timestamp[-1])

            if elapsed_time > self.max_dx_time:
                diagnostic_msg = {key: 13.2 for key in Application.sensitivities}
                color_code_dict = {key: GREY for key in Application.sensitivities}
                dx_table = create_dx_table(cur_time, ECON2, diagnostic_msg, color_code_dict)
                dx_result = insert_ecam_data(dx_result, dx_table, ecam_data)
                # dx_result.insert_table_row(table_key, {ECON2 + DX: result})
                self.clear_data()
                return dx_result
            dx_result = self.not_economizing_when_needed(dx_result, table_key, cur_time, ecam_data)
            return dx_result

        return dx_result

    def not_economizing_when_needed(self, dx_result, table_key, cur_time, ecam_data):
        """
        If the detected problems(s) are consistent then generate a fault
        message(s).
        :param dx_result:
        :param table_key:
        :return:
        """
        oaf = [(m - r) / (o - r) for o, r, m in zip(self.oat_values, self.rat_values, self.mat_values)]
        avg_oaf = max(0.0, min(100.0, mean(oaf)*100.0))
        avg_damper_signal = mean(self.oad_values)
        dx_msg = {}
        energy_impact = {}
        color_code_dict = {}
        thresholds = zip(self.open_damper_threshold.items(), self.oaf_economizing_threshold.items())
        for (key, damper_thr), (key2, oaf_thr) in thresholds:
            if avg_damper_signal - self.minimum_damper_setpoint < damper_thr:
                msg = "{}: {} - sensitivity: {}".format(ECON2, self.alg_result_messages[0], key)
                color_code = RED
                result = 11.1
                energy = self.energy_impact_calculation()
            else:
                if 100.0 - avg_oaf <= oaf_thr:
                    msg = "{}: {} - sensitivity: {}".format(ECON2, self.alg_result_messages[1], key)
                    color_code = GREEN
                    result = 10.0
                    energy = 0.0
                else:
                    msg = "{}: {} --OAF: {} - sensitivity: {}".format(ECON2, self.alg_result_messages[2], avg_oaf, key)
                    color_code = RED
                    result = 12.1
                    energy = self.energy_impact_calculation()
            dx_result.log(msg)
            dx_msg.update({key: result})
            energy_impact.update({key: energy})
            color_code_dict.update({key: color_code})

        dx_table = create_dx_table(cur_time, ECON2, dx_msg, color_code_dict, energy_impact)
        dx_result = insert_ecam_data(dx_result, dx_table, ecam_data)
        # dx_table = {
        #    ECON2 + DX: diagnostic_msg,
        #    ECON2 + EI: energy_impact
        # }
        # dx_result.insert_table_row(table_key, dx_table)
        self.clear_data()
        return dx_result

    def economizer_conditions(self, dx_result, cooling_call, econ_condition, cur_time, ecam_data):
        """
        Check if unit is in a cooling mode.
        :param dx_result:
        :param cooling_call:
        :param econ_condition:
        :param cur_time:
        :return:
        """
        if not cooling_call:
            dx_result.log("{}: not cooling for data for data {}".format(ECON2, cur_time))
            if self.not_cooling is None:
                self.not_cooling = cur_time
            if cur_time - self.not_cooling >= self.data_window:
                dx_result.log("{}: unit is not cooling - reinitialize!".format(ECON2))
                dx_msg = {key: 14.0 for key in Application.sensitivities}
                color_code_dict = {key: GREEN for key in Application.sensitivities}
                dx_table = create_dx_table(cur_time, ECON2, dx_msg, color_code_dict)
                dx_result = insert_ecam_data(dx_result, dx_table, ecam_data)
                # dx_table = {ECON2 + DX: diagnostic_msg}
                # table_key = create_table_key(self.analysis, cur_time)
                # dx_result.insert_table_row(table_key, dx_table)
                self.clear_data()
            return dx_result, False
        else:
            self.not_cooling = None

        if not econ_condition:
            dx_result.log("{}: Not economizing, for data {} -- {}.".format(ECON2, cur_time, self.not_economizing))
            if self.not_economizing is None:
                self.not_economizing = cur_time
            if cur_time - self.not_economizing >= self.data_window:
                dx_result.log("{}: unit is not economizing - reinitialize!".format(ECON2))
                dx_msg = {key: 15.0 for key in Application.sensitivities}
                color_code_dict = {key: GREEN for key in Application.sensitivities}
                dx_table = create_dx_table(cur_time, ECON2, dx_msg, color_code_dict)
                dx_result = insert_ecam_data(dx_result, dx_table, ecam_data)
                # dx_table = {ECON2 + DX: diagnostic_msg}
                # table_key = create_table_key(self.analysis, cur_time)
                # dx_result.insert_table_row(table_key, dx_table)
                self.clear_data()
            return dx_result, False
        else:
            self.not_economizing = None
        return dx_result, True

    def energy_impact_calculation(self):
        ei = 0.0
        energy_calc = [1.08 * s * self.cfm * (m - o) / (1000.0 * self.eer)
                       for m, o, s in zip(self.mat_values, self.oat_values, self.fan_spd_values)
                       if (m - o) > 0]
        if energy_calc:
            avg_step = (self.timestamp[-1] - self.timestamp[0]).total_seconds() / 60 if len(self.timestamp) > 1 else 1
            dx_time = (len(energy_calc) - 1) * avg_step if len(energy_calc) > 1 else 1.0
            ei = (sum(energy_calc) * 60.0) / (len(energy_calc) * dx_time)
            ei = round(ei, 2)
        return ei

    def clear_data(self):
        """
        Reinitialize data arrays.
        :return:
        """
        self.oad_values = []
        self.oat_values = []
        self.rat_values = []
        self.mat_values = []
        self.fan_spd_values = []
        self.timestamp = []
        self.not_economizing = None
        self.not_cooling = None


class EconCorrectlyOff(object):
    """
    Air-side HVAC economizer diagnostic for AHU/RTU systems.

    EconCorrectlyOff uses metered data from a BAS or controller to diagnose
    if an AHU/RTU is economizing when it should not.
    """
    def __init__(self, data_window, no_required_data, min_damper_sp,
                 excess_damper_threshold, desired_oaf, cfm, eer, analysis):
        self.oat_values = []
        self.rat_values = []
        self.mat_values = []
        self.oad_values = []
        self.fan_spd_values = []
        self.timestamp = []
        self.economizing = None
        self.cfm = cfm
        self.eer = eer
        # Application result messages
        self.alg_result_messages = \
            ["The OAD should be at the minimum position but is significantly above this value.",
             "No problems detected.",
             "Inconclusive results, could not verify the status of the economizer."]
        self.max_dx_time = td(minutes=60)
        self.data_window = data_window
        self.no_required_data = no_required_data
        self.min_damper_sp = min_damper_sp
        self.excess_damper_threshold = excess_damper_threshold
        self.desired_oaf = desired_oaf
        self.analysis = analysis
        self.cfm = cfm
        self.eer = eer

    def econ_alg3(self, dx_result, oat, rat, mat, oad, econ_condition, cur_time, fan_sp, ecam_data):
        """
        Check app. pre-quisites and assemble data set for analysis.
        :param dx_result:
        :param oat:
        :param rat:
        :param mat:
        :param oad:
        :param econ_condition:
        :param cur_time:
        :param fan_sp:
        :return:
        """
        dx_result, economizing = self.economizer_conditions(dx_result, econ_condition, cur_time, ecam_data)
        if economizing:
            return dx_result

        self.oad_values.append(oad)
        self.oat_values.append(oat)
        self.mat_values.append(mat)
        self.rat_values.append(rat)
        self.timestamp.append(cur_time)

        fan_sp = fan_sp / 100.0 if fan_sp is not None else 1.0
        self.fan_spd_values.append(fan_sp)

        elapsed_time = self.timestamp[-1] - self.timestamp[0]

        if elapsed_time >= self.data_window and len(self.timestamp) >= self.no_required_data:
            table_key = create_table_key(self.analysis, self.timestamp[-1])

            if elapsed_time > self.max_dx_time:
                dx_msg = {key: 23.2 for key in Application.sensitivities}
                color_code_dict = {key: GREY for key in Application.sensitivities}
                dx_table = create_dx_table(cur_time, ECON3, dx_msg, color_code_dict)
                dx_result = insert_ecam_data(dx_result, dx_table, ecam_data)
                # dx_result.insert_table_row(table_key, {ECON3 + DX: result})
                self.clear_data()
                return dx_result

            dx_result = self.economizing_when_not_needed(dx_result, table_key, cur_time, ecam_data)
            return dx_result
        return dx_result

    def economizing_when_not_needed(self, dx_result, table_key, cur_time, ecam_data):
        """
        If the detected problems(s) are consistent then generate a
        fault message(s).
        :param dx_result:
        :param table_key:
        :return:
        """
        desired_oaf = self.desired_oaf / 100.0
        avg_damper = mean(self.oad_values)
        dx_msg = {}
        energy_impact = {}
        color_code_dict = {}
        for key, threshold in self.excess_damper_threshold.items():
            if avg_damper - self.min_damper_sp > threshold:
                msg = "{}: {} - sensitivity: {}".format(ECON3, self.alg_result_messages[0], key)
                color_code = RED
                result = 21.1
                energy = self.energy_impact_calculation(desired_oaf)
            else:
                msg = "{}: {} - sensitivity: {}".format(ECON3, self.alg_result_messages[1], key)
                color_code = GREEN
                result = 20.0
                energy = 0.0
            dx_result.log(msg)
            dx_msg.update({key: result})
            energy_impact.update({key: energy})
            color_code_dict.update({key: color_code})

        dx_table = create_dx_table(cur_time, ECON3, dx_msg, color_code_dict, energy_impact)
        dx_result = insert_ecam_data(dx_result, dx_table, ecam_data)
        # dx_table = {
        #     ECON3 + DX: diagnostic_msg,
        #     ECON3 + EI: energy_impact
        # }
        # dx_result.insert_table_row(table_key, dx_table)
        self.clear_data()
        return dx_result

    def clear_data(self):
        """
        Reinitialize data arrays.
        :return:
        """
        self.oad_values = []
        self.oat_values = []
        self.rat_values = []
        self.mat_values = []
        self.fan_spd_values = []
        self.timestamp = []
        self.economizing = None

    def energy_impact_calculation(self, desired_oaf):
        ei = 0.0
        energy_calc = [
            (1.08 * spd * self.cfm * (m - (o * desired_oaf + (r * (1.0 - desired_oaf))))) / (1000.0 * self.eer)
            for m, o, r, spd in zip(self.mat_values, self.oat_values, self.rat_values, self.fan_spd_values)
            if (m - (o * desired_oaf + (r * (1.0 - desired_oaf)))) > 0
        ]
        if energy_calc:
            avg_step = (self.timestamp[-1] - self.timestamp[0]).total_seconds() / 60 if len(self.timestamp) > 1 else 1
            dx_time = (len(energy_calc) - 1) * avg_step if len(energy_calc) > 1 else 1.0
            ei = (sum(energy_calc) * 60.0) / (len(energy_calc) * dx_time)
            ei = round(ei, 2)
        return ei

    def economizer_conditions(self, dx_result, econ_condition, cur_time, ecam_data):
        if econ_condition:
            dx_result.log("{}: economizing, for data {} --{}.".format(ECON3, econ_condition, cur_time))
            if self.economizing is None:
                self.economizing = cur_time
            if cur_time - self.economizing >= self.data_window:
                dx_result.log("{}: economizing - reinitialize!".format(ECON3))
                dx_msg = {key: 25.0 for key in Application.sensitivities}
                color_code_dict = {key: GREEN for key in Application.sensitivities}
                dx_table = create_dx_table(cur_time, ECON3, dx_msg, color_code_dict)
                dx_result = insert_ecam_data(dx_result, dx_table, ecam_data)
                # dx_table = {ECON3 + DX: diagnostic_msg}
                # table_key = create_table_key(self.analysis, cur_time)
                # dx_result.insert_table_row(table_key, dx_table)
                self.clear_data()
            return dx_result, True
        else:
            self.economizing = None
        return dx_result, False


class ExcessOA(object):
    """
    Air-side HVAC ventilation diagnostic.

    ExcessOA uses metered data from a controller or
    BAS to diagnose when an AHU/RTU is providing excess outdoor air.
    """
    def __init__(self, data_window, no_required_data, excess_oaf_threshold,
                 min_damper_sp, excess_damper_threshold, desired_oaf,
                 cfm, eer, analysis):
        self.oat_values = []
        self.rat_values = []
        self.mat_values = []
        self.oad_values = []
        self.timestamp = []
        self.fan_spd_values = []
        self.economizing = None

        # Application thresholds (Configurable)
        self.cfm = cfm
        self.eer = eer
        self.max_dx_time = td(minutes=60)
        self.data_window = data_window
        self.no_required_data = no_required_data
        self.excess_oaf_threshold = excess_oaf_threshold
        self.min_damper_sp = min_damper_sp
        self.desired_oaf = desired_oaf
        self.excess_damper_threshold = excess_damper_threshold
        self.analysis = analysis

    def econ_alg4(self, dx_result, oat, rat, mat, oad, econ_condition, cur_time, fan_sp, ecam_data):
        """
        Check app. prerequisites and assemble data set for analysis.
        :param dx_result:
        :param oat:
        :param rat:
        :param mat:
        :param oad:
        :param econ_condition:
        :param cur_time:
        :param fan_sp:
        :return:
        """
        dx_result, economizing = self.economizer_conditions(dx_result, econ_condition, cur_time, ecam_data)
        if economizing:
            return dx_result

        self.oad_values.append(oad)
        self.oat_values.append(oat)
        self.rat_values.append(rat)
        self.mat_values.append(mat)
        self.timestamp.append(cur_time)

        fan_sp = fan_sp / 100.0 if fan_sp is not None else 1.0
        self.fan_spd_values.append(fan_sp)
        elapsed_time = self.timestamp[-1] - self.timestamp[0]

        if elapsed_time >= self.data_window and len(self.timestamp) >= self.no_required_data:
            table_key = create_table_key(self.analysis, self.timestamp[-1])
            if elapsed_time > self.max_dx_time:
                dx_msg = {key: 35.2 for key in Application.sensitivities}
                color_code_dict = {key: GREY for key in Application.sensitivities}
                dx_table = create_dx_table(cur_time, ECON4, dx_msg, color_code_dict)
                dx_result = insert_ecam_data(dx_result, dx_table, ecam_data)
                # dx_result.insert_table_row(table_key, {ECON4 + DX: diagnostic_msg})
                self.clear_data()
                return dx_result
            dx_result = self.excess_oa(dx_result, table_key, cur_time, ecam_data)
            return dx_result
        return dx_result

    def excess_oa(self, dx_result, table_key, cur_time, ecam_data):
        """
        If the detected problems(s) are consistent generate a fault message(s).
        :param dx_result:
        :param table_key:
        :return:
        """
        oaf = [(m - r) / (o - r) for o, r, m in zip(self.oat_values, self.rat_values, self.mat_values)]
        avg_oaf = mean(oaf) * 100.0
        avg_damper = mean(self.oad_values)
        desired_oaf = self.desired_oaf / 100.0
        msg = ""
        dx_msg = {}
        energy_impact = {}
        color_code_dict = {}

        if avg_oaf < 0 or avg_oaf > 125.0:
            msg = ("{}: Inconclusive result, unexpected OAF value: {}".format(ECON4, avg_oaf))
            dx_msg = {key: 31.2 for key in Application.sensitivities}
            color_code_dict = {key: GREY for key in Application.sensitivities}
            dx_table = create_dx_table(cur_time, ECON4, dx_msg, color_code_dict)
            dx_result = insert_ecam_data(dx_result, dx_table, ecam_data)
            dx_result.log(msg)
            # dx_table = {ECON4 + DX: result}
            # dx_result.insert_table_row(table_key, dx_table)
            self.clear_data()
            return dx_result

        avg_oaf = max(0.0, min(100.0, avg_oaf))
        thresholds = zip(self.excess_damper_threshold.items(), self.excess_oaf_threshold.items())
        for (key, damper_thr), (key2, oaf_thr) in thresholds:
            result = 30.0
            energy = 0.0
            color_code = GREEN
            if avg_damper - self.min_damper_sp > damper_thr:
                msg = "{}: The OAD should be at the minimum but is significantly higher.".format(ECON4)
                color_code = RED
                result = 32.1

            if avg_oaf - self.desired_oaf > oaf_thr:
                if result > 30.0:
                    msg += ("{}: The OAD should be at the minimum for ventilation "
                            "but is significantly above that value. Excess outdoor air is "
                            "being provided; This could significantly increase "
                            "heating and cooling costs".format(ECON4))
                    result = 34.1
                else:
                    msg = ("{}: Excess outdoor air is being provided, this could "
                           "increase heating and cooling energy consumption.".format(ECON4))
                    result = 33.1
                    color_code = RED

            elif result == 30.0:
                msg = ("{}: The calculated OAF is within configured limits.".format(ECON4))

            if result > 30:
                energy = self.energy_impact_calculation(desired_oaf)

            dx_result.log(msg)
            energy_impact.update({key: energy})
            dx_msg.update({key: result})
            color_code_dict.update({key: color_code})

        dx_table = create_dx_table(cur_time, ECON4, dx_msg, color_code_dict, energy_impact)
        dx_result = insert_ecam_data(dx_result, dx_table, ecam_data)
        # dx_table = {
        #     ECON4 + DX: diagnostic_msg,
        #     ECON4 + EI: energy_impact
        # }
        # dx_result.insert_table_row(table_key, dx_table)
        self.clear_data()
        return dx_result

    def clear_data(self):
        """
        Reinitialize class insufficient_oa data.
        :return:
        """
        self.oad_values = []
        self.oat_values = []
        self.rat_values = []
        self.mat_values = []
        self.fan_spd_values = []
        self.timestamp = []
        self.economizing = None
        return

    def energy_impact_calculation(self, desired_oaf):
        ei = 0.0
        energy_calc = [
            (1.08 * spd * self.cfm * (m - (o * desired_oaf + (r * (1.0 - desired_oaf))))) / (1000.0 * self.eer)
            for m, o, r, spd in zip(self.mat_values, self.oat_values, self.rat_values, self.fan_spd_values)
            if (m - (o * desired_oaf + (r * (1.0 - desired_oaf)))) > 0
        ]
        if energy_calc:
            avg_step = (self.timestamp[-1] - self.timestamp[0]).total_seconds() / 60 if len(self.timestamp) > 1 else 1
            dx_time = (len(energy_calc) - 1) * avg_step if len(energy_calc) > 1 else 1.0
            ei = (sum(energy_calc) * 60.0) / (len(energy_calc) * dx_time)
            ei = round(ei, 2)
        return ei

    def economizer_conditions(self, dx_result, econ_condition, cur_time, ecam_data):
        if econ_condition:
            dx_result.log("{}: economizing, for data {} .".format(ECON4, cur_time))
            if self.economizing is None:
                self.economizing = cur_time
            if cur_time - self.economizing >= self.data_window:
                dx_result.log("{}: economizing - reinitialize!".format(ECON4))
                dx_msg = {key: 36.0 for key in Application.sensitivities}
                color_code_dict = {key: GREEN for key in Application.sensitivities}
                dx_table = create_dx_table(cur_time, ECON4, dx_msg, color_code_dict)
                dx_result = insert_ecam_data(dx_result, dx_table, ecam_data)
                # dx_table = {ECON4 + DX: diagnostic_msg}
                # table_key = create_table_key(self.analysis, cur_time)
                # dx_result.insert_table_row(table_key, dx_table)
                self.clear_data()
            return dx_result, True
        else:
            self.economizing = None
        return dx_result, False


class InsufficientOA(object):
    """
    Air-side HVAC ventilation diagnostic.

    insufficient_oa_intake uses metered data from a controller or
    BAS to diagnose when an AHU/RTU is providing inadequate ventilation.
    """

    def __init__(self, data_window, no_required_data, ventilation_oaf_threshold, desired_oaf, analysis):

        self.oat_values = []
        self.rat_values = []
        self.mat_values = []
        self.timestamp = []
        self.max_dx_time = td(minutes=60)

        # Application thresholds (Configurable)
        self.data_window = data_window
        self.no_required_data = no_required_data
        self.ventilation_oaf_threshold = ventilation_oaf_threshold
        self.desired_oaf = desired_oaf
        self.analysis = analysis

    def econ_alg5(self, dx_result, oatemp, ratemp, matemp, cur_time, ecam_data):
        """
        Check app. pre-quisites and assemble data set for analysis.
        :param dx_result:
        :param oatemp:
        :param ratemp:
        :param matemp:
        :param damper_signal:
        :param econ_condition:
        :param cur_time:
        :param cooling_call:
        :return:
        """
        self.oat_values.append(oatemp)
        self.rat_values.append(ratemp)
        self.mat_values.append(matemp)
        self.timestamp.append(cur_time)

        elapsed_time = self.timestamp[-1] - self.timestamp[0]

        if elapsed_time >= self.data_window and len(self.timestamp) >= self.no_required_data:
            table_key = create_table_key(self.analysis, self.timestamp[-1])
            if elapsed_time > self.max_dx_time:
                dx_msg = {key: 44.2 for key in Application.sensitivities}
                color_code_dict = {key: GREY for key in Application.sensitivities}
                dx_table = create_dx_table(cur_time, ECON5, dx_msg, color_code_dict)
                dx_result = insert_ecam_data(dx_result, dx_table, ecam_data)
                # dx_result.insert_table_row(table_key, {ECON5 + DX: diagnostic_msg})
                self.clear_data()
                return dx_result
            dx_result = self.insufficient_oa(dx_result, table_key, cur_time, ecam_data)
            return dx_result
        return dx_result

    def insufficient_oa(self, dx_result, table_key, cur_time, ecam_data):
        """
        If the detected problems(s) are
        consistent generate a fault message(s).
        :param dx_result:
        :param cur_time:
        :param table_key:
        :return:
        """
        oaf = [(m - r) / (o - r) for o, r, m in zip(self.oat_values, self.rat_values, self.mat_values)]
        avg_oaf = mean(oaf) * 100.0
        dx_msg = {}
        color_code_dict = {}

        if avg_oaf < 0 or avg_oaf > 125.0:
            msg = ("{}: Inconclusive result, the OAF calculation led to an "
                   "unexpected value: {}".format(ECON5, avg_oaf))
            color_code = "GREY"
            diagnostic_msg = {key: 41.2 for key in Application.sensitivities}
            color_code_dict = {key: GREY for key in Application.sensitivities}
            dx_table = create_dx_table(cur_time, ECON5, diagnostic_msg, color_code_dict)
            dx_result = insert_ecam_data(dx_result, dx_table, ecam_data)
            dx_result.log(msg)
            # dx_table = {ECON5 + DX: diagnostic_msg}
            # dx_result.insert_table_row(table_key, dx_table)
            self.clear_data()
            return dx_result

        avg_oaf = max(0.0, min(100.0, avg_oaf))
        for key, threshold in self.ventilation_oaf_threshold.items():
            if self.desired_oaf - avg_oaf > threshold:
                msg = "{}: Insufficient OA is being provided for ventilation - sensitivity: {}".format(ECON5, key)
                color_code = RED
                result = 43.1
            else:
                msg = "{}: The calculated OAF was within acceptable limits - sensitivity: {}".format(ECON5, key)
                color_code = GREEN
                result = 40.0
            dx_result.log(msg)
            dx_msg.update({key: result})
            color_code_dict.update({key: color_code})

        dx_table = create_dx_table(cur_time, ECON5, dx_msg, color_code_dict)
        dx_result = insert_ecam_data(dx_result, dx_table, ecam_data)
        # dx_table = {ECON5 + DX: diagnostic_msg}
        # dx_result.insert_table_row(table_key, dx_table)
        self.clear_data()
        return dx_result

    def clear_data(self):
        """
        Reinitialize class insufficient_oa data.
        :return:
        """
        self.oat_values = []
        self.rat_values = []
        self.mat_values = []
        self.timestamp = []
        return
