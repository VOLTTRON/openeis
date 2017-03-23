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
import re
from openeis.applications.utils import conversion_utils as cu
from openeis.applications import (DrivenApplicationBaseClass,
                                  OutputDescriptor,
                                  ConfigDescriptor,
                                  InputDescriptor,
                                  Results,
                                  Descriptor,
                                  reports)

ECON1 = 'Temperature Sensor Dx'
ECON2 = 'Economizing When Unit Should Dx'
ECON3 = 'Economizing When Unit Should Not Dx'
ECON4 = 'Excess Outdoor-air Intake Dx'
ECON5 = 'Insufficient Outdoor-air Intake Dx'


class Application(DrivenApplicationBaseClass):
    '''Application to detect and correct operational problems for AHUs/RTUs.

    This application uses metered data from zones server by an AHU/RTU
    to detect operational problems and where applicable correct these problems
    by modifying set points.  When auto-correction cannot be applied then
    a message detailing the diagnostic results will be made available to
    the building operator.
    '''
    # Diagnostic Point Names (Must match OpenEIS data-type names)
    fan_status_name = 'fan_status'
    oa_temp_name = 'oa_temp'
    ma_temp_name = 'ma_temp'
    ra_temp_name = 'ra_temp'
    damper_signal_name = 'damper_signal'
    cool_call_name = 'cool_call'
    fan_speedcmd_name = 'fan_speedcmd'
    timestamp = 'date'
    oaf_name = 'oa_fraction'
    cc_valve_name = 'cc_valve_pos'
    da_temp_name = 'da_temp'
    da_temp_setpoint_name = 'da_temp_setpoint'
    #TODO: temp set data_window=1 to test
    def __init__(self, *args, building_name=None,
                 economizer_type='DDB', econ_hl_temp=65.0,
                 device_type='AHU', temp_deadband=1.0,
                 data_window=1, no_required_data=20,
                 open_damper_time=5,
                 low_supply_fan_threshold=20.0,
                 mat_low_threshold=50.0, mat_high_threshold=90.0,
                 oat_low_threshold=30.0, oat_high_threshold=100.0,
                 rat_low_threshold=50.0, rat_high_threshold=90.0,
                 temp_difference_threshold=4.0, oat_mat_check=5.0,
                 open_damper_threshold=90.0, oaf_economizing_threshold=25.0,
                 oaf_temperature_threshold=4.0,
                 cooling_enabled_threshold=5.0,
                 minimum_damper_setpoint=15.0, excess_damper_threshold=20.0,
                 excess_oaf_threshold=20.0, desired_oaf=10.0,
                 ventilation_oaf_threshold=5.0,
                 insufficient_damper_threshold=15.0,
                 temp_damper_threshold=90.0, rated_cfm=1000.0, eer=10.0,
                 sensitivity=1.0,
                 **kwargs):
        # initialize user configurable parameters.
        super().__init__(*args, **kwargs)
        self.default_building_name_used = False

        if building_name is None:
            building_name = "None supplied"
            self.default_building_name_used = True

        self.building_name = building_name

        self.device_type = device_type.lower()
        self.economizer_type = economizer_type.lower()
        if self.economizer_type == 'hl':
            self.econ_hl_temp = float(econ_hl_temp)
        Application.pre_requiste_messages = []
        Application.pre_msg_time = []
        self.oaf_temperature_threshold = float(oaf_temperature_threshold)
        # Application thresholds (Configurable)
        self.data_window = float(data_window)
        no_required_data = int(no_required_data)
        self.mat_low_threshold = float(mat_low_threshold)
        self.mat_high_threshold = float(mat_high_threshold)
        self.oat_low_threshold = float(oat_low_threshold)
        self.oat_high_threshold = float(oat_high_threshold)
        self.rat_low_threshold = float(rat_low_threshold)
        self.rat_high_threshold = float(rat_high_threshold)
        self.temp_deadband = float(temp_deadband)
        self.low_supply_fan_threshold = float(low_supply_fan_threshold)
        self.cooling_enabled_threshold = float(cooling_enabled_threshold)
        cfm = float(rated_cfm)
        eer = float(eer)

        if sensitivity == 0.0:
            # low sensitivity
            temp_difference_threshold = float(temp_difference_threshold) * 1.5
            oat_mat_check = float(oat_mat_check) * 1.5
            open_damper_threshold = float(open_damper_threshold) * 1.5
            excess_damper_threshold = float(excess_damper_threshold) * 1.5
            oaf_economizing_threshold= float(oaf_economizing_threshold) * 1.5
            excess_oaf_threshold = float(minimum_damper_setpoint) * 1.5
            insufficient_damper_threshold = float(minimum_damper_setpoint) * 0.5
        elif sensitivity == 2.0:
            # high sensitivity
            temp_difference_threshold = float(temp_difference_threshold) * 0.5
            oat_mat_check = float(oat_mat_check) * 0.5
            open_damper_threshold = float(open_damper_threshold) * 0.5
            excess_damper_threshold = float(excess_damper_threshold) * 0.5
            oaf_economizing_threshold= float(oaf_economizing_threshold) * 0.5
            excess_oaf_threshold = float(minimum_damper_setpoint) * 0.5
            insufficient_damper_threshold = float(minimum_damper_setpoint) * 1.5
        else:
            # Normal sensitivtyy
            temp_difference_threshold = float(temp_difference_threshold)
            oat_mat_check = float(oat_mat_check)
            open_damper_threshold = float(open_damper_threshold)
            excess_damper_threshold = float(excess_damper_threshold)
            oaf_economizing_threshold = float(oaf_economizing_threshold)
            excess_oaf_threshold = float(minimum_damper_setpoint)
            insufficient_damper_threshold = float(minimum_damper_setpoint)


        # Pre-requisite messages
        self.pre_msg1 = ('Supply fan is off, current data will '
                         'not be used for diagnostics.')
        self.pre_msg2 = ('Supply fan status data is missing '
                         'from input(device or csv), could '
                         'not verify system was ON.')
        self.pre_msg3 = ('Missing required data for diagnostic: '
                         'Check BACnet configuration or CSV file '
                         'input for outside-air temperature.')
        self.pre_msg4 = ('Missing required data for diagnostic: '
                         'Check BACnet configuration or CSV file '
                         'input for return-air temperature.')
        self.pre_msg5 = ('Missing required data for diagnostic: '
                         'Check BACnet configuration or CSV '
                         'file input for mixed-air temperature.')
        self.pre_msg6 = ('Missing required data for diagnostic: '
                         'Check BACnet configuration or CSV '
                         'file input for damper signal.')
        self.pre_msg7 = ''.join(['Missing required data for diagnostic: ',
                                 'Check BACnet configuration or CSV file '
                                 'input for cooling call (AHU cooling coil,'
                                 'RTU cooling call or compressor command).'])
        self.pre_msg8 = ('Outside-air temperature is outside high/low '
                         'operating limits, check the functionality of '
                         'the temperature sensor.')
        self.pre_msg9 = ('Return-air temperature is outside high/low '
                         'operating limits, check the functionality of '
                         'the temperature sensor.')
        self.pre_msg10 = ('Mixed-air temperature is outside high/low '
                          'operating limits, check the functionality '
                          'of the temperature sensor.')
        self.econ1 = temperature_sensor_dx(data_window, no_required_data,
                                           temp_difference_threshold,
                                           open_damper_time,
                                           oat_mat_check,
                                           temp_damper_threshold)
        self.econ2 = econ_correctly_on(oaf_economizing_threshold,
                                       open_damper_threshold,
                                       data_window, no_required_data, cfm, eer)
        self.econ3 = econ_correctly_off(data_window, no_required_data,
                                        minimum_damper_setpoint,
                                        excess_damper_threshold,
                                        cooling_enabled_threshold,
                                        desired_oaf, cfm, eer)
        self.econ4 = excess_oa_intake(data_window, no_required_data,
                                      excess_oaf_threshold,
                                      minimum_damper_setpoint,
                                      excess_damper_threshold,
                                      desired_oaf, cfm, eer)
        self.econ5 = insufficient_oa_intake(data_window, no_required_data,
                                            ventilation_oaf_threshold,
                                            minimum_damper_setpoint,
                                            insufficient_damper_threshold,
                                            desired_oaf)

    @classmethod
    def get_config_parameters(cls):
        '''Generate required configuration parameters with description
        for user'''
        dgr_sym = u'\N{DEGREE SIGN}'
        return {
            'data_window':
            ConfigDescriptor(int,
                             'Minimum Elapsed time for analysis '
                             '(minutes)', value_default=30),
            'open_damper_time':
            ConfigDescriptor(float,
                             'Delay time for steady-state conditions '
                             '(minutes)', value_default=5),
            'no_required_data':
            ConfigDescriptor(int,
                             'Number of required data measurements to '
                             'perform diagnostic', value_default=20),
            'low_supply_fan_threshold':
            ConfigDescriptor(float,
                             'Value above which the supply fan will be '
                             'considered at its minimum speed (%)',
                             value_default=20.0),
            'rated_cfm':
            ConfigDescriptor(float,
                             'Rated CFM of supply fan at 100% speed (CFM)',
                             value_default=1000.0),
            'mat_low_threshold':
            ConfigDescriptor(float,
                             'Mixed-air temperature sensor low limit ({drg}F)'
                             .format(drg=dgr_sym),
                             value_default=50.0),
            'mat_high_threshold':
            ConfigDescriptor(float,
                             'Mixed-air temperature sensor high limit ({drg}F)'
                             .format(drg=dgr_sym),
                             value_default=90.0),
            'rat_low_threshold':
            ConfigDescriptor(float,
                             'Return-air temperature sensor low limit ({drg}F)'
                             .format(drg=dgr_sym),
                             value_default=50),
            'rat_high_threshold':
            ConfigDescriptor(float,
                             'Return-air temperature sensor high limit '
                             '({drg}F)'.format(drg=dgr_sym),
                             value_default=90.0),
            'oat_low_threshold':
            ConfigDescriptor(float,
                             'Outdoor-air temperature sensor low limit '
                             '({drg}F)'.format(drg=dgr_sym),
                             value_default=30.0),
            'oat_high_threshold':
            ConfigDescriptor(float,
                             'Outdoor-air temperature sensor high limit '
                             '({drg}F)'.format(drg=dgr_sym),
                             value_default=100.0),
            'temp_deadband': ConfigDescriptor(float,
                                              'Economizer control '
                                              'temperature dead-band ({drg}F)'
                                              .format(drg=dgr_sym),
                                              value_default=1.0),
            'minimum_damper_setpoint':
            ConfigDescriptor(float,
                             'Minimum outdoor-air damper set point (%)',
                             value_default=15.0),
            'excess_damper_threshold':
            ConfigDescriptor(float,
                             'Value above the minimum damper '
                             'set point at which a fault will be '
                             'called(%)', value_default=20.0),
            'econ_hl_temp':
            ConfigDescriptor(float,
                             'High limit (HL) temperature for HL type '
                             'economizer ({drg}F)'.format(drg=dgr_sym),
                             value_default=60.0),
            'cooling_enabled_threshold':
            ConfigDescriptor(float,
                             'Amount AHU chilled water valve '
                             'must be open to consider unit in cooling '
                             'mode (%).  If device is an RTU set to 1.0 '
                             '(cooling status)',
                              value_default=5.0),
            'insufficient_damper_threshold':
            ConfigDescriptor(float,
                             'Value below the minimum outdoor-air '
                             'damper set-point at which a fault will '
                             'be identified (%)', value_default=15.0),
            'ventilation_oaf_threshold':
            ConfigDescriptor(float,
                             'The value below the desired minimum OA '
                             '% where a fault will be indicated (%)',
                             value_default=5.0),
            'desired_oaf':
            ConfigDescriptor(float,
                             'The desired minimum OA percent '
                             '(%)', value_default=10.0),
            'excess_oaf_threshold':
            ConfigDescriptor(float,
                             'The value above the desired OA % where a '
                             'fault will be indicated '
                             '(%)', value_default=30.0),
            'economizer_type':
            ConfigDescriptor(str,
                             'Economizer type:  <DDB> - differential dry bulb '
                             '<HL> - High limit', value_default='DDB'),
            'open_damper_threshold':
            ConfigDescriptor(float,
                             'Threshold in which damper is considered open '
                             'for economizing (%)', value_default=75.0),
            'oaf_economizing_threshold':
            ConfigDescriptor(float,
                             'Value below 100% in which the OA is considered '
                             'insufficient for economizing (%)',
                             value_default=25.0),
            'oaf_temperature_threshold':
            ConfigDescriptor(float,
                             'Required difference between OAT and '
                             'RAT for accurate diagnostic ({drg}F)',
                             value_default=5.0),
            'device_type':
            ConfigDescriptor(str,
                             'Device type <RTU> or <AHU> (default=AHU)',
                             value_default='AHU'),
            'temp_difference_threshold':
            ConfigDescriptor(float,
                             'Threshold for detecting temperature sensor '
                             'problems ({drg}F)'.format(drg=dgr_sym),
                             value_default=4.0),
            'oat_mat_check':
            ConfigDescriptor(float,
                             'Temperature threshold for OAT and MAT '
                             'consistency check for times when the damper is '
                             'near 100% open ({drg}F)'.format(drg=dgr_sym),
                             value_default=5.0),
            'temp_damper_threshold':
            ConfigDescriptor(float,
                             'Damper position to check for OAT/MAT '
                             'consistency (%)',
                             value_default=90.0),
            'eer':
            ConfigDescriptor(float,
                             'AHU/RTU rated EER',
                             value_default=10.0),
            'sensitivity':
                ConfigDescriptor(float,
                                 'Sensitivity: values can be 0.0 (low sensitivity), '
                                 '1.0 (normal sensitivity), 2.0 (high sensitivity) ',
                                 value_default=1.0)
            }

    @classmethod
    def get_self_descriptor(cls):
        name = 'Auto-RCx/Ecam for Economizer HVAC Systems'
        desc = 'Automated Retro-commisioning for HVAC Economizer Systems'
        return Descriptor(name=name, description=desc)

    @classmethod
    def required_input(cls):
        '''Generate required inputs with description for user.'''
        return {
            cls.fan_status_name:
            InputDescriptor('SupplyFanStatus',
                            'AHU Supply Fan Status (required for Dx)', count_min=0),
            cls.fan_speedcmd_name:
            InputDescriptor('SupplyFanSpeed',
                            'AHU supply fan speed', count_min=0),
            cls.oa_temp_name:
            InputDescriptor('OutdoorAirTemperature',
                            'AHU or building outdoor-air temperature',
                            count_min=1),
            cls.ma_temp_name:
            InputDescriptor('MixedAirTemperature',
                            'AHU mixed-air temperature',
                            count_min=1),
            cls.ra_temp_name:
            InputDescriptor('ReturnAirTemperature',
                            'AHU return-air temperature', count_min=1),
            cls.damper_signal_name:
            InputDescriptor('OutdoorDamperSignal',
                            'AHU outdoor-air damper signal (required for Dx)', count_min=0),
            cls.cool_call_name:
            InputDescriptor('CoolingCall',
                            'AHU cooling coil command or RTU coolcall or '
                            'compressor command (integer, required for Dx)', count_min=0),
            cls.da_temp_name:
            InputDescriptor('DischargeAirTemperature',
                            'AHU discharge-air temperature', count_min=0),
            cls.da_temp_setpoint_name:
            InputDescriptor('DischargeAirTemperatureSetPoint',
                            'AHU discharge-air temperature setpoint', count_min=0),
            cls.cc_valve_name:
            InputDescriptor('CoolingCoilValvePosition',
                            'AHU cooling coil valve position',
                            count_min=0)

        }

    def reports(self):
        '''Called by UI to create Viz.

        Describe how to present output to user
        '''
        report = reports.Report('Retuning Report')

        # report.add_element(reports.RetroCommissioningOAED(
        #     table_name='Economizer_RCx'))
        report.add_element(reports.RetroCommissioningAFDDEcam(
            table_name='Economizer_RCx'))
        return [report]

    @classmethod
    def output_format(cls, input_object):
        '''Called when application is staged.

        Output will have the date-time and  error-message.
        '''
        result = super().output_format(input_object)

        topics = input_object.get_topics()
        diagnostic_topic = topics[cls.oa_temp_name][0]
        diagnostic_topic_parts = diagnostic_topic.split('/')
        output_topic_base = diagnostic_topic_parts[:-1]
        datetime_topic = '/'.join(output_topic_base +
                                  ['Economizer_RCx', cls.timestamp])
        message_topic = '/'.join(output_topic_base +
                                 ['Economizer_RCx', 'message'])
        diagnostic_name = '/'.join(output_topic_base +
                                   ['Economizer_RCx', 'diagnostic_name'])
        energy_impact = '/'.join(output_topic_base +
                                 ['Economizer_RCx', 'energy_impact'])
        color_code = '/'.join(output_topic_base +
                              ['Economizer_RCx', 'color_code'])
        oat_topic = '/'.join(output_topic_base+['Economizer_RCx', cls.oa_temp_name])
        mat_topic = '/'.join(output_topic_base+['Economizer_RCx', cls.ma_temp_name])
        rat_topic = '/'.join(output_topic_base+['Economizer_RCx', cls.ra_temp_name])
        dat_topic = '/'.join(output_topic_base+['Economizer_RCx', cls.da_temp_name])
        datstpt_topic = '/'.join(output_topic_base+['Economizer_RCx', cls.da_temp_setpoint_name])
        fsp_topic = '/'.join(output_topic_base+['Economizer_RCx', cls.fan_speedcmd_name])
        fst_topic = '/'.join(output_topic_base+['Economizer_RCx', cls.fan_status_name])
        od_topic = '/'.join(output_topic_base+['Economizer_RCx', cls.damper_signal_name])
        ccv_topic = '/'.join(output_topic_base+['Economizer_RCx', cls.cc_valve_name])
        oaf_topic = '/'.join(output_topic_base+['Economizer_RCx', cls.oaf_name])
        output_needs = {
            'Economizer_RCx': {
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



    def run(self, current_time, points):
        '''Main run method that is called by the DrivenBaseClass.

        run receives a dictionary of data 'points' and an associated timestamp
        for the data current_time'.  run then passes the appropriate data to
        each diagnostic when calling
        the diagnostic message.
        '''
        device_dict = {}
        diagnostic_result = Results()

        # ecam_data = {
        #     'datetime': str(current_time),
        #     'OutdoorAirTemperature': 70,
        #     'MixedAirTemperature': 70,
        #     'ReturnAirTemperature': 70,
        #     'DischargeAirTemperature': None,
        #     'DischargeAirTemperatureSetPoint': None,
        #     'SupplyFanStatus': None,
        #     'SupplyFanSpeed': None,
        #     'OutdoorDamper': None,
        #     'CCV': None,
        #     'OutdoorAirFraction': None,
        #     'diagnostic_name': '',
        #     'diagnostic_message': '',
        #     'energy_impact': '',
        #     'color_code': ''
        # }
        # diagnostic_result.insert_table_row('Economizer_RCx', ecam_data)
        # return diagnostic_result

        topics = self.inp.get_topics()
        diagnostic_topic = topics[self.oa_temp_name][0]
        current_time = self.inp.localize_sensor_time(diagnostic_topic,
                                                     current_time)
        base_topic = self.inp.get_topics()
        meta_topics = self.inp.get_topics_meta()
        unit_dict = {
            self.oa_temp_name: meta_topics[self.oa_temp_name][base_topic[self.oa_temp_name][0]]['unit'],
            self.ma_temp_name: meta_topics[self.ma_temp_name][base_topic[self.ma_temp_name][0]]['unit'],
            self.ra_temp_name: meta_topics[self.ra_temp_name][base_topic[self.ra_temp_name][0]]['unit']
        }
        if len(base_topic[self.da_temp_name]) > 0:
            unit_dict[self.da_temp_name] = meta_topics[self.da_temp_name][base_topic[self.da_temp_name][0]]['unit']
        if len(base_topic[self.da_temp_setpoint_name]) > 0:
            unit_dict[self.da_temp_setpoint_name] = \
                meta_topics[self.da_temp_setpoint_name][base_topic[self.da_temp_setpoint_name][0]]['unit']

        for key, value in points.items():
            device_dict[key.lower()] = value

        damper_data = []
        oatemp_data = []
        matemp_data = []
        ratemp_data = []
        cooling_data = []
        fan_speedcmd_data = []
        datemp_data = []
        datemp_stpt_data = []
        ccv_data = []
        fan_status_data = []
        for key, value in device_dict.items():
            #print("{0} {1}".format(key, value))
            if (key.startswith(self.damper_signal_name)
                    and value is not None):
                damper_data.append(value)
            elif (key.startswith(self.oa_temp_name)
                  and value is not None):
                oatemp_data.append(value)
            elif (key.startswith(self.ma_temp_name)
                  and value is not None):
                matemp_data.append(value)
            elif (key.startswith(self.ra_temp_name)
                  and value is not None):
                ratemp_data.append(value)
            elif (key.startswith(self.cool_call_name)
                  and value is not None):
                cooling_data.append(value)
            elif (key.startswith(self.fan_speedcmd_name)
                  and value is not None):
                fan_speedcmd_data.append(value)
            elif (key.startswith(self.da_temp_setpoint_name) #da_temp_setpoint is longer so it goes before da_setpoint
                  and value is not None):
                datemp_stpt_data.append(value)
            elif (key.startswith(self.da_temp_name) #DAT
                  and value is not None):
                datemp_data.append(value)
            elif (key.startswith(self.cc_valve_name) #CoolCoilValvePos
                  and value is not None):
                ccv_data.append(value)
            elif (key.startswith(self.fan_status_name) #Fan status
                  and value is not None):
                fan_status_data.append(value)

        if not oatemp_data:
            Application.pre_requiste_messages.append(self.pre_msg3)
        if not ratemp_data:
            Application.pre_requiste_messages.append(self.pre_msg4)
        if not matemp_data:
            Application.pre_requiste_messages.append(self.pre_msg5)


        if not (oatemp_data and ratemp_data and matemp_data):
            return diagnostic_result

        if 'celcius' or 'kelvin' in unit_dict.values:
            if unit_dict[self.oa_temp_name] == 'celcius':
                oatemp_data = cu.convertCelciusToFahrenheit(oatemp_data)
            elif unit_dict[self.oa_temp_name] == 'kelvin':
                oatemp_data = cu.convertKelvinToCelcius(
                    cu.convertCelciusToFahrenheit(oatemp_data))
            #if self.ma_temp_name in unit_dict:
            if unit_dict[self.ma_temp_name] == 'celcius':
                matemp_data = cu.convertCelciusToFahrenheit(matemp_data)
            elif unit_dict[self.ma_temp_name] == 'kelvin':
                matemp_data = cu.convertKelvinToCelcius(
                    cu.convertCelciusToFahrenheit(matemp_data))
            if self.ra_temp_name in unit_dict:
                if unit_dict[self.ra_temp_name] == 'celcius':
                    ratemp_data = cu.convertCelciusToFahrenheit(ratemp_data)
                elif unit_dict[self.ra_temp_name] == 'kelvin':
                    ratemp_data = cu.convertKelvinToCelcius(
                        cu.convertCelciusToFahrenheit(ratemp_data))
            if self.da_temp_name in unit_dict:
                if unit_dict[self.da_temp_name] == 'celcius':
                    datemp_data = cu.convertCelciusToFahrenheit(datemp_data)
                elif unit_dict[self.da_temp_name] == 'kelvin':
                    datemp_data = cu.convertKelvinToCelcius(
                        cu.convertCelciusToFahrenheit(datemp_data))
            if self.da_temp_setpoint_name in unit_dict:
                if unit_dict[self.da_temp_setpoint_name] == 'celcius':
                    datemp_stpt_data = cu.convertCelciusToFahrenheit(datemp_stpt_data)
                elif unit_dict[self.da_temp_setpoint_name] == 'kelvin':
                    datemp_stpt_data = cu.convertKelvinToCelcius(
                        cu.convertCelciusToFahrenheit(datemp_stpt_data))


        oatemp = (sum(oatemp_data) / len(oatemp_data))
        matemp = (sum(matemp_data) / len(matemp_data))
        ratemp = (sum(ratemp_data) / len(ratemp_data))
        oaf = None
        denominator = oatemp - ratemp
        if denominator == 0:
            oaf = 0
        else:
            oaf = (matemp - ratemp) / denominator
        if oaf > 1:
            oaf = 1
        elif oaf < 0:
            oaf = 0
        oaf = oaf * 100

        datemp = datemp_stpt = None
        fanstatus = fan_speedcmd = ccv = None
        damper_signal = None
        # if matemp_data:
        #     matemp = (sum(matemp_data) / len(matemp_data))
        if datemp_data:
            datemp = (sum(datemp_data) / len(datemp_data))
        if datemp_stpt_data:
            datemp_stpt = (sum(datemp_stpt_data) / len(datemp_stpt_data))
        if fan_status_data:
            fanstatus = (sum(fan_status_data) / len(fan_status_data))
        if fan_speedcmd_data:
            fan_speedcmd = (sum(fan_speedcmd_data) / len(fan_speedcmd_data))
        if len(damper_data) > 0:
            damper_signal = (sum(damper_data) / len(damper_data))
        if ccv_data:
            ccv = (sum(ccv_data) / len(ccv_data))

        ecam_data = {
            'datetime': str(current_time),
            'OutdoorAirTemperature': oatemp,
            'MixedAirTemperature': matemp,
            'ReturnAirTemperature': ratemp,
            'OutdoorAirFraction': oaf,
            'DischargeAirTemperature': None if datemp is None else datemp,
            'DischargeAirTemperatureSetPoint': None if datemp_stpt is None else datemp_stpt,
            'SupplyFanStatus': None if fanstatus is None else fanstatus,
            'SupplyFanSpeed': None if fan_speedcmd is None else fan_speedcmd,
            'OutdoorDamper': None if damper_signal is None else damper_signal,
            'CCV': None if ccv is None else ccv,
            'diagnostic_name': None,
            'diagnostic_message': None,
            'energy_impact': None,
            'color_code': None
        }
        # merged = merge_ecam_data({}, ecam_data)
        # for key, value in merged.items():
        #     print(key, value)
        # return insert_ecam_data(diagnostic_result, {}, ecam_data)

        ####Start Economizer Rcx######
        if not damper_data:
            Application.pre_requiste_messages.append(self.pre_msg6)
        if not cooling_data:
            Application.pre_requiste_messages.append(self.pre_msg7)

        if not (oatemp_data and ratemp_data and matemp_data and
                damper_data and cooling_data):
            diagnostic_result = self.pre_message(diagnostic_result, current_time)
            #diagnostic_result.insert_table_row('Economizer_RCx', ecam_data)
            return insert_ecam_data(diagnostic_result, {}, ecam_data)

        fan_stat_check = False
        for key, value in device_dict.items():
            if key.startswith(self.fan_status_name):
                if value is not None and not int(value):
                    Application.pre_requiste_messages.append(self.pre_msg1)
                    diagnostic_result = self.pre_message(diagnostic_result,
                                                         current_time)
                    return insert_ecam_data(diagnostic_result, {}, ecam_data)
                elif value is not None:
                    fan_stat_check = True
        if (not fan_stat_check and
                self.fan_speedcmd_name is not None):
            for key, value in device_dict.items():
                if key.startswith(self.fan_speedcmd_name):
                    fan_stat_check = True
                    if value < self.low_supply_fan_threshold:
                        Application.pre_requiste_messages.append(self.pre_msg1)
                        diagnostic_result = self.pre_message(diagnostic_result,
                                                             current_time)
                        return insert_ecam_data(diagnostic_result, {}, ecam_data)
        if not fan_stat_check:
            Application.pre_requiste_messages.append(self.pre_msg2)
            diagnostic_result = self.pre_message(diagnostic_result,
                                                 current_time)
            return insert_ecam_data(diagnostic_result, {}, ecam_data)

        #damper_signal = (sum(damper_data) / len(damper_data))
        #fan_speedcmd = None
        #if fan_speedcmd_data:
        #    fan_speedcmd = sum(fan_speedcmd_data)/len(fan_speedcmd_data)
        limit_check = False
        if oatemp < self.oat_low_threshold or oatemp > self.oat_high_threshold:
            Application.pre_requiste_messages.append(self.pre_msg8)
            limit_check = True
        if ratemp < self.rat_low_threshold or ratemp > self.rat_high_threshold:
            Application.pre_requiste_messages.append(self.pre_msg9)
            limit_check = True
        if matemp < self.mat_low_threshold or matemp > self.mat_high_threshold:
            Application.pre_requiste_messages.append(self.pre_msg10)
            limit_check = True
        if limit_check:
            diagnostic_result = self.pre_message(diagnostic_result,
                                                 current_time)
            return insert_ecam_data(diagnostic_result, {}, ecam_data)

        if abs(oatemp - ratemp) < self.oaf_temperature_threshold:
            diagnostic_result.log('OAT and RAT are too close, economizer '
                                  'diagnostic will not use data '
                                  'corresponding to: {timestamp} '
                                  .format(timestamp=str(current_time)),
                                  logging.DEBUG)
            return insert_ecam_data(diagnostic_result, {}, ecam_data)
        device_type_error = False
        if self.device_type == 'ahu':
            cooling_valve = sum(cooling_data) / len(cooling_data)
            if cooling_valve > self.cooling_enabled_threshold:
                cooling_call = True
            else:
                cooling_call = False
        elif self.device_type == 'rtu':
            cooling_call = int(max(cooling_data))
        else:
            device_type_error = True
            diagnostic_result.log('device_type must be specified '
                                  'as "AHU" or "RTU" Check '
                                  'Configuration input.', logging.INFO)
        if device_type_error:
            return insert_ecam_data(diagnostic_result, {}, ecam_data)
        if self.economizer_type == 'ddb':
            economizer_conditon = (oatemp < (ratemp - self.temp_deadband))
        else:
            economizer_conditon = (
                oatemp < (self.econ_hl_temp - self.temp_deadband))
        diagnostic_result = self.econ1.econ_alg1(diagnostic_result,
                                                 oatemp, ratemp, matemp,
                                                 damper_signal, current_time, ecam_data)
        if (temperature_sensor_dx.temp_sensor_problem is not None and
                temperature_sensor_dx.temp_sensor_problem is False):
            diagnostic_result = self.econ2.econ_alg2(diagnostic_result,
                                                     cooling_call, oatemp,
                                                     ratemp, matemp,
                                                     damper_signal,
                                                     economizer_conditon,
                                                     current_time,
                                                     fan_speedcmd,
                                                     ecam_data)
            diagnostic_result = self.econ3.econ_alg3(diagnostic_result,
                                                     oatemp, ratemp,
                                                     matemp, damper_signal,
                                                     economizer_conditon,
                                                     current_time,
                                                     fan_speedcmd,
                                                     ecam_data)
            diagnostic_result = self.econ4.econ_alg4(diagnostic_result,
                                                     oatemp, ratemp,
                                                     matemp, damper_signal,
                                                     economizer_conditon,
                                                     current_time,
                                                     fan_speedcmd,
                                                     ecam_data)
            diagnostic_result = self.econ5.econ_alg5(diagnostic_result,
                                                     oatemp, ratemp,
                                                     matemp, damper_signal,
                                                     economizer_conditon,
                                                     current_time,
                                                     ecam_data)
        else:
            # diagnostic_result = self.econ2.clear_data(diagnostic_result)
            # diagnostic_result = self.econ3.clear_data(diagnostic_result)
            # diagnostic_result = self.econ4.clear_data(diagnostic_result)
            # diagnostic_result = self.econ5.clear_data(diagnostic_result)
            self.damper_signal_values = []
            self.oa_temp_values = []
            self.ra_temp_values = []
            self.ma_temp_values = []
            self.fan_speed_values = []
            self.timestamp = []
            temperature_sensor_dx.temp_sensor_problem = None

        return diagnostic_result

    def pre_message(self, result, current_time):
        '''Handle reporting of diagnostic pre-requisite messages.

        Report to user when conditions are not favorable for a diagnostic.
        '''
        Application.pre_msg_time.append(current_time)
        pre_check = ((Application.pre_msg_time[-1] -
                      Application.pre_msg_time[0])
                     .total_seconds()/60)
        pre_check = pre_check if pre_check > 0.0 else 1.0
        if pre_check >= self.data_window:
            msg_lst = [self.pre_msg1, self.pre_msg2, self.pre_msg3,
                       self.pre_msg4, self.pre_msg5, self.pre_msg6,
                       self.pre_msg7, self.pre_msg8, self.pre_msg9,
                       self.pre_msg10]
            for item in msg_lst:
                if (Application.pre_requiste_messages.count(item) >
                        (0.25) * len(Application.pre_msg_time)):
                    result.log(item, logging.DEBUG)
            Application.pre_requiste_messages = []
            Application.pre_msg_time = []
        return result


def insert_ecam_data(diagnostic_result, data, ecam_data):
        merged_data = merge_ecam_data(data, ecam_data)
        diagnostic_result.insert_table_row('Economizer_RCx', merged_data)
        return diagnostic_result

def merge_ecam_data(data, ecam_data):
    merged_data = ecam_data.copy()
    merged_data.update(data)
    return merged_data

class temperature_sensor_dx(object):
    '''Air-side HVAC temperature sensor diagnostic for AHU/RTU systems.

    temperature_sensor_dx uses metered data from a BAS or controller to
    diagnose if any of the temperature sensors for an AHU/RTU are accurate and
    reliable.
    '''
    def __init__(self, data_window, no_required_data,
                 temp_difference_threshold, open_damper_time,
                 oat_mat_check, temp_damper_threshold):
        self.oa_temp_values = []
        self.ra_temp_values = []
        self.ma_temp_values = []
        self.timestamp = []
        self.open_damper_oat = []
        self.open_damper_mat = []
        self.econ_check = False
        self.steady_state_start = None
        self.open_damper_time = int(open_damper_time)
        self.econ_time_check = datetime.timedelta(
            minutes=self.open_damper_time - 1)
        temperature_sensor_dx.temp_sensor_problem = None

        '''Application thresholds (Configurable)'''
        self.data_window = float(data_window)
        self.no_required_data = no_required_data
        self.temp_difference_threshold = float(temp_difference_threshold)
        self.oat_mat_check = float(oat_mat_check)
        self.temp_damper_threshold = float(temp_damper_threshold)

    def econ_alg1(self, diagnostic_result, oatemp,
                  ratemp, matemp, damper_signal, current_time, ecam_data):
        '''Check app. pre-quisites and assemble data set for analysis.'''
        if (damper_signal) > self.temp_damper_threshold:
            if not self.econ_check:
                self.econ_check = True
                self.steady_state_start = current_time
            if ((current_time - self.steady_state_start)
                    >= self.econ_time_check):
                self.open_damper_oat.append(oatemp)
                self.open_damper_mat.append(matemp)
        else:
            self.econ_check = False

        self.oa_temp_values.append(oatemp)
        self.ma_temp_values.append(matemp)
        self.ra_temp_values.append(ratemp)

        if (self.timestamp and
                ((current_time - self.timestamp[-1])
                 .total_seconds()/60) > 5.0):
            self.econ_check = False

        self.timestamp.append(current_time)
        elapsed_time = ((self.timestamp[-1] - self.timestamp[0])
                        .total_seconds()/60)
        elapsed_time = elapsed_time if elapsed_time > 0 else 1.0

        if (elapsed_time >= self.data_window and
                len(self.timestamp) >= self.no_required_data):
            diagnostic_result = self.temperature_sensor_dx(
                diagnostic_result, current_time, ecam_data)

        return diagnostic_result

    def temperature_sensor_dx(self, result, current_time, ecam_data):
        '''
        If the detected problems(s) are
        consistent then generate a fault message(s).
        '''
        oa_ma = [(x - y)
                 for x, y in zip(self.oa_temp_values, self.ma_temp_values)]
        ra_ma = [(x - y)
                 for x, y in zip(self.ra_temp_values, self.ma_temp_values)]
        ma_oa = [(y - x)
                 for x, y in zip(self.oa_temp_values, self.ma_temp_values)]
        ma_ra = [(y - x)
                 for x, y in zip(self.ra_temp_values, self.ma_temp_values)]
        avg_oa_ma = sum(oa_ma) / len(oa_ma)
        avg_ra_ma = sum(ra_ma) / len(ra_ma)
        avg_ma_oa = sum(ma_oa) / len(ma_oa)
        avg_ma_ra = sum(ma_ra) / len(ma_ra)
        color_code = 'GREEN'
        Application.pre_requiste_messages = []
        Application.pre_msg_time = []
        dx_table = {}

        if len(self.open_damper_oat) > self.no_required_data:
            mat_oat_diff_list = [
                abs(x - y)for x, y in zip(self.open_damper_oat,
                                          self.open_damper_mat)]
            open_damper_check = sum(mat_oat_diff_list) / len(mat_oat_diff_list)

            if open_damper_check > self.oat_mat_check:
                temperature_sensor_dx.temp_sensor_problem = True
                diagnostic_message = ('The OAT and MAT and sensor '
                                      'readings are not consistent '
                                      'when the outdoor-air damper '
                                      'is fully open.')
                color_code = 'RED'
                dx_table = {
                    'datetime': str(current_time),
                    'diagnostic_name': ECON1,
                    'diagnostic_message': diagnostic_message,
                    'energy_impact': None,
                    'color_code': color_code
                }
                result.log(diagnostic_message, logging.INFO)
                #result.insert_table_row('Economizer_RCx', dx_table)
                result = insert_ecam_data(result, dx_table, ecam_data)
            self.open_damper_oat = []
            self.open_damper_mat = []

        if ((avg_oa_ma) > self.temp_difference_threshold and
                (avg_ra_ma) > self.temp_difference_threshold):
            diagnostic_message = ('Temperature sensor problem '
                                  'detected. Mixed-air temperature is '
                                  'less than outdoor-air and return-air'
                                  'temperature.')

            color_code = 'RED'
            dx_table = {
                'datetime': str(current_time),
                'diagnostic_name': ECON1,
                'diagnostic_message': diagnostic_message,
                'energy_impact': None,
                'color_code': color_code
            }
            temperature_sensor_dx.temp_sensor_problem = True

        elif((avg_ma_oa) > self.temp_difference_threshold and
             (avg_ma_ra) > self.temp_difference_threshold):
            diagnostic_message = ('Temperature sensor problem '
                                  'detected Mixed-air temperature is '
                                  'greater than outdoor-air and return-air '
                                  'temperature.')
            temperature_sensor_dx.temp_sensor_problem = True
            color_code = 'RED'
            dx_table = {
                'datetime': str(current_time),
                'diagnostic_name': ECON1,
                'diagnostic_message': diagnostic_message,
                'energy_impact': None,
                'color_code': color_code
            }

        elif (temperature_sensor_dx.temp_sensor_problem is None
              or not temperature_sensor_dx.temp_sensor_problem):
            diagnostic_message = 'No problems were detected.'
            temperature_sensor_dx.temp_sensor_problem = False
            color_code = 'GREEN'
            dx_table = {
                'datetime': str(current_time),
                'diagnostic_name': ECON1,
                'diagnostic_message': diagnostic_message,
                'energy_impact': None,
                'color_code': color_code
            }
        else:
            diagnostic_message = 'Diagnostic was inconclusive'
            temperature_sensor_dx.temp_sensor_problem = False
            color_code = 'GREEN'
            dx_table = {
                'datetime': str(current_time),
                'diagnostic_name': ECON1,
                'diagnostic_message': diagnostic_message,
                'energy_impact': None,
                'color_code': color_code
            }
        result.log(diagnostic_message, logging.INFO)
        #result.insert_table_row('Economizer_RCx', dx_table)
        result = insert_ecam_data(result, dx_table, ecam_data)
        result = self.clear_data(result)
        return result

    def clear_data(self, diagnostic_result):
        '''
        reinitialize class insufficient_oa data
        '''
        self.oa_temp_values = []
        self.ra_temp_values = []
        self.ma_temp_values = []
        self.timestamp = []
        return diagnostic_result


class econ_correctly_on(object):
    '''Air-side HVAC economizer diagnostic for AHU/RTU systems.

    econ_correctly_on uses metered data from a BAS or controller to diagnose
    if an AHU/RTU is economizing when it should.
    '''
    def __init__(self, oaf_economizing_threshold, open_damper_threshold,
                 data_window, no_required_data, cfm, eer):
        self.oa_temp_values = []
        self.ra_temp_values = []
        self.ma_temp_values = []
        self.fan_speed_values = []
        self.damper_signal_values = []
        self.timestamp = []
        self.output_no_run = []
        self.open_damper_threshold = float(open_damper_threshold)
        self.oaf_economizing_threshold = float(oaf_economizing_threshold)
        self.data_window = float(data_window)
        self.no_required_data = no_required_data
        self.cfm = cfm
        self.eer = eer

        '''Application result messages'''
        self.alg_result_messages = ['Conditions are favorable for '
                                    'economizing but the damper is frequently '
                                    'below 100% open.',
                                    'No problems detected.',
                                    'Conditions are favorable for '
                                    'economizing and the damper is 100% '
                                    'open but the OAF indicates the unit '
                                    'is not brining in near 100% OA.']

    def econ_alg2(self, diagnostic_result, cooling_call, oatemp, ratemp,
                  matemp, damper_signal, economizer_conditon, current_time,
                  fan_speedcmd, ecam_data):
        '''Check app. pre-quisites and assemble data set for analysis.'''
        if not cooling_call:
            diagnostic_result.log('The unit is not cooling, data '
                                  'corresponding to {timestamp} will '
                                  'not be used for {name} diagnostic.'.
                                  format(timestamp=str(current_time),
                                         name=ECON2), logging.DEBUG)
            self.output_no_run.append(current_time)
            if ((self.output_no_run[-1] - self.output_no_run[0]) >=
                    datetime.timedelta(minutes=(self.data_window))):
                diagnostic_result.log(('{name}: the unit is not cooling or '
                                       'economizing, keep collecting data.')
                                      .format(name=ECON2), logging.DEBUG)
                self.output_no_run = []
            #return diagnostic_result
            return insert_ecam_data(diagnostic_result, {}, ecam_data)

        if not economizer_conditon:
            diagnostic_result.log('{name}: Conditions are not favorable for '
                                  'economizing, data corresponding to '
                                  '{timestamp} will not be used.'.
                                  format(timestamp=str(current_time),
                                         name=ECON2), logging.DEBUG)
            self.output_no_run.append(current_time)
            if ((self.output_no_run[-1] - self.output_no_run[0]) >=
                    datetime.timedelta(minutes=(self.data_window))):
                diagnostic_result.log(('{name}: the unit is not cooling or '
                                       'economizing, keep collecting data.')
                                      .format(name=ECON2), logging.DEBUG)
                self.output_no_run = []
            #return diagnostic_result
            return insert_ecam_data(diagnostic_result, {}, ecam_data)

        self.oa_temp_values.append(oatemp)
        self.ma_temp_values.append(matemp)
        self.ra_temp_values.append(ratemp)
        self.timestamp.append(current_time)
        self.damper_signal_values.append(damper_signal)

        fan_speedcmd = fan_speedcmd/100.0 if fan_speedcmd is not None else 1.0
        self.fan_speed_values.append(fan_speedcmd)

        self.timestamp.append(current_time)

        elapsed_time = ((self.timestamp[-1] - self.timestamp[0])
                        .total_seconds()/60)
        elapsed_time = elapsed_time if elapsed_time > 0 else 1.0

        if (elapsed_time >= self.data_window and
                len(self.timestamp) >= self.no_required_data):
            diagnostic_result = self.not_economizing_when_needed(
                diagnostic_result, current_time, ecam_data)
        return diagnostic_result

    def not_economizing_when_needed(self, result, current_time, ecam_data):
        '''If the detected problems(s) are consistent then generate a fault
        message(s).
        '''
        oaf = [(m - r) / (o - r) for o, r, m in zip(self.oa_temp_values,
                                                    self.ra_temp_values,
                                                    self.ma_temp_values)]
        avg_step = ((self.timestamp[-1] - self.timestamp[0]).total_seconds()/60
                    if len(self.timestamp) > 1 else 1)
        avg_oaf = sum(oaf) / len(oaf) * 100.0
        avg_damper_signal = sum(
            self.damper_signal_values) / len(self.damper_signal_values)
        energy_impact = None

        if avg_damper_signal < self.open_damper_threshold:
            diagnostic_message = (self.alg_result_messages[0])
            color_code = 'RED'
        else:
            if (100.0 - avg_oaf) <= self.oaf_economizing_threshold:
                diagnostic_message = (self.alg_result_messages[1])
                color_code = 'GREEN'
                energy_impact = None
            else:
                diagnostic_message = (self.alg_result_messages[2])
                color_code = 'RED'

        energy_calc = [1.08 * spd * self.cfm * (ma - oa) / (1000.0 * self.eer)
                       for ma, oa, spd in zip(self.ma_temp_values,
                                              self.oa_temp_values,
                                              self.fan_speed_values)
                       if (ma - oa) > 0 and color_code == 'RED']

        if energy_calc:
            dx_time = (len(energy_calc) - 1) * \
                avg_step if len(energy_calc) > 1 else 1.0
            energy_impact = (sum(energy_calc) * 60.0) / \
                (len(energy_calc) * dx_time)
            energy_impact = '%s' % float('%.2g' % energy_impact)
            energy_impact = str(energy_impact)
            energy_impact = ''.join([energy_impact, ' kWh/h'])

        dx_table = {
            'datetime': str(current_time),
            'diagnostic_name': ECON2, 'diagnostic_message': diagnostic_message,
            'energy_impact': energy_impact,
            'color_code': color_code
            }
        result.log(diagnostic_message, logging.INFO)
        #result.insert_table_row('Economizer_RCx', dx_table)
        result = insert_ecam_data(result, dx_table, ecam_data)
        result = self.clear_data(result)
        return result

    def clear_data(self, diagnostic_result):
        '''
        reinitialize class insufficient_oa data.
        '''
        self.damper_signal_values = []
        self.oa_temp_values = []
        self.ra_temp_values = []
        self.ma_temp_values = []
        self.fan_speed_values = []
        self.timestamp = []
        return diagnostic_result


class econ_correctly_off(object):
    '''Air-side HVAC economizer diagnostic for AHU/RTU systems.

    econ_correctly_off uses metered data from a BAS or controller to diagnose
    if an AHU/RTU is economizing when it should not.
    '''

    def __init__(self, data_window, no_required_data, minimum_damper_setpoint,
                 excess_damper_threshold, cooling_enabled_threshold,
                 desired_oaf, cfm, eer):
        self.oa_temp_values = []
        self.ra_temp_values = []
        self.ma_temp_values = []
        self.damper_signal_values = []
        self.cool_call_values = []
        self.cfm = cfm
        self.eer = eer
        self.fan_speed_values = []
        self.timestamp = []

        # Application result messages
        self.alg_result_messages = ['The outdoor-air damper should be '
                                    'at the minimum position but is '
                                    'significantly above that value.',
                                    'No problems detected.',
                                    'The diagnostic led to '
                                    'inconclusive results, could not '
                                    'verify the status of the economizer.']
        self.cfm = cfm
        self.eer = float(eer)
        self.data_window = float(data_window)
        self.no_required_data = no_required_data
        self.minimum_damper_setpoint = float(minimum_damper_setpoint)
        self.excess_damper_threshold = float(excess_damper_threshold)
        self.cooling_enabled_threshold = float(cooling_enabled_threshold)
        self.desired_oaf = float(desired_oaf)

    def econ_alg3(self, diagnostic_result, oatemp, ratemp, matemp,
                  damper_signal, economizer_conditon, current_time,
                  fan_speedcmd, ecam_data):
        '''Check app. pre-quisites and assemble data set for analysis.'''
        if economizer_conditon:
            diagnostic_result.log(''.join([self.alg_result_messages[2],
                                           (' Data corresponding to '
                                            '{tstamp} will not '
                                            'be used for this diagnostic.'
                                            .format(tstamp=str
                                                    (current_time)))]),
                                  logging.DEBUG)
            return insert_ecam_data(diagnostic_result, {}, ecam_data)
        else:
            self.damper_signal_values.append(damper_signal)
            self.oa_temp_values.append(oatemp)
            self.ma_temp_values.append(matemp)
            self.ra_temp_values.append(ratemp)
            self.timestamp.append(current_time)
            fan_speedcmd = (fan_speedcmd/100.0 if fan_speedcmd is not None
                            else 1.0)
            self.fan_speed_values.append(fan_speedcmd)

        elapsed_time = ((self.timestamp[-1] - self.timestamp[0])
                        .total_seconds()/60)
        elapsed_time = elapsed_time if elapsed_time > 0 else 1.0

        if (elapsed_time >= self.data_window and
                len(self.timestamp) >= self.no_required_data):
            diagnostic_result = self.economizing_when_not_needed(
                diagnostic_result, current_time, ecam_data)
        return diagnostic_result

    def economizing_when_not_needed(self, result, current_time, ecam_data):
        '''If the detected problems(s)
        are consistent then generate a
        fault message(s).
        '''
        avg_step = ((self.timestamp[-1] - self.timestamp[0]).total_seconds()/60
                    if len(self.timestamp) > 1 else 1)
        desired_oaf = self.desired_oaf / 100.0
        energy_impact = None
        energy_calc = [
            (1.08 * spd * self.cfm * (ma - (oa * desired_oaf +
                                            (ra * (1.0 - desired_oaf))))) /
            (1000.0 * self.eer)
            for ma, oa, ra, spd in zip(self.ma_temp_values,
                                       self.oa_temp_values,
                                       self.ra_temp_values,
                                       self.fan_speed_values)
            if (ma - (oa * desired_oaf + (ra * (1.0 - desired_oaf)))) > 0]

        avg_damper = sum(self.damper_signal_values) / \
            len(self.damper_signal_values)

        if ((avg_damper - self.minimum_damper_setpoint)
                > self.excess_damper_threshold):
            diagnostic_message = self.alg_result_messages[0]
            color_code = 'RED'
        else:
            diagnostic_message = 'No problems detected.'
            color_code = 'GREEN'
            energy_impact = None

        if energy_calc and color_code == 'RED':
            dx_time = (len(energy_calc) - 1) * \
                avg_step if len(energy_calc) > 1 else 1.0
            energy_impact = (sum(energy_calc) * 60.0) / \
                (len(energy_calc) * dx_time)
            energy_impact = '%s' % float('%.2g' % energy_impact)
            energy_impact = str(energy_impact)
            energy_impact = ''.join([energy_impact, ' kWh/h'])

        dx_table = {
            'datetime': str(current_time),
            'diagnostic_name': ECON3,
            'diagnostic_message': diagnostic_message,
            'energy_impact': energy_impact,
            'color_code': color_code
            }

        #result.insert_table_row('Economizer_RCx', dx_table)
        result.log(diagnostic_message, logging.INFO)
        result = insert_ecam_data(result, dx_table, ecam_data)
        result = self.clear_data(result)
        return result

    def clear_data(self, diagnostic_result):
        '''
        reinitialize class insufficient_oa data
        '''
        self.damper_signal_values = []
        self.oa_temp_values = []
        self.ra_temp_values = []
        self.ma_temp_values = []
        self.fan_speed_values = []
        self.timestamp = []
        return diagnostic_result


class excess_oa_intake(object):
    ''' Air-side HVAC ventilation diagnostic.

    excess_oa_intake uses metered data from a controller or
    BAS to diagnose when an AHU/RTU is providing excess outdoor air.
    '''
    def __init__(self, data_window, no_required_data, excess_oaf_threshold,
                 minimum_damper_setpoint, excess_damper_threshold, desired_oaf,
                 cfm, eer):
        self.oa_temp_values = []
        self.ra_temp_values = []
        self.ma_temp_values = []
        self.damper_signal_values = []
        self.cool_call_values = []
        self.timestamp = []
        self.fan_speed_values = []
        # Application thresholds (Configurable)
        self.cfm = cfm
        self.eer = eer
        self.data_window = float(data_window)
        self.no_required_data = no_required_data
        self.excess_oaf_threshold = float(excess_oaf_threshold)
        self.minimum_damper_setpoint = float(minimum_damper_setpoint)
        self.desired_oaf = float(desired_oaf)
        self.excess_damper_threshold = float(excess_damper_threshold)

    def econ_alg4(self, diagnostic_result, oatemp, ratemp, matemp,
                  damper_signal, economizer_conditon, current_time,
                  fan_speedcmd, ecam_data):
        '''Check app. pre-quisites and assemble data set for analysis.'''

        if economizer_conditon:
            diagnostic_result.log('The unit may be economizing, '
                                  'data corresponding to {timestamp} '
                                  'will not be used for this diagnostic.'.
                                  format(timestamp=str(current_time)),
                                  logging.DEBUG)
            return insert_ecam_data(diagnostic_result, {}, ecam_data)
            #return diagnostic_result

        self.damper_signal_values.append(damper_signal)
        self.oa_temp_values.append(oatemp)
        self.ra_temp_values.append(ratemp)
        self.ma_temp_values.append(matemp)
        self.timestamp.append(current_time)
        fan_speedcmd = fan_speedcmd/100.0 if fan_speedcmd is not None else 1.0
        self.fan_speed_values.append(fan_speedcmd)

        elapsed_time = ((self.timestamp[-1] - self.timestamp[0])
                        .total_seconds()/60)
        elapsed_time = elapsed_time if elapsed_time > 0 else 1.0

        if (elapsed_time >= self.data_window and
                len(self.timestamp) >= self.no_required_data):
            diagnostic_result = self.excess_oa(diagnostic_result, current_time, ecam_data)
        return diagnostic_result

    def excess_oa(self, result, current_time, ecam_data):
        '''If the detected problems(s) are
        consistent generate a fault message(s).
        '''
        avg_step = ((self.timestamp[-1] - self.timestamp[0]).total_seconds()/60
                    if len(self.timestamp) > 1 else 1)
        oaf = [(m - r) / (o - r) for o, r, m in zip(self.oa_temp_values,
                                                    self.ra_temp_values,
                                                    self.ma_temp_values)]

        avg_oaf = sum(oaf) / len(oaf) * 100
        avg_damper = sum(self.damper_signal_values) / \
            len(self.damper_signal_values)

        desired_oaf = self.desired_oaf / 100.0
        energy_calc = [
            (1.08 * spd * self.cfm * (ma - (oa * desired_oaf +
                                            (ra * (1.0 - desired_oaf))))) /
            (1000.0 * self.eer)
            for ma, oa, ra, spd in zip(self.ma_temp_values,
                                       self.oa_temp_values,
                                       self.ra_temp_values,
                                       self.fan_speed_values)
            if (ma - (oa * desired_oaf + (ra * (1.0 - desired_oaf)))) > 0]
        color_code = 'GREY'
        energy_impact = None
        diagnostic_message = ''
        if avg_oaf < 0 or avg_oaf > 125.0:
            diagnostic_message = ('Inconclusive result, the OAF '
                                  'calculation led to an '
                                  'unexpected value: {oaf}'.
                                  format(oaf=avg_oaf))
            color_code = 'GREY'
            result.log(diagnostic_message, logging.INFO)
            dx_table = {
                'datetime': str(current_time),
                'diagnostic_name': ECON4,
                'diagnostic_message': diagnostic_message,
                'energy_impact': None,
                'color_code': color_code
            }
            #result.insert_table_row('Economizer_RCx', dx_table)
            result = insert_ecam_data(result, dx_table, ecam_data)
            result = self.clear_data(result)
            return result

        if ((avg_damper - self.minimum_damper_setpoint)
                > self.excess_damper_threshold):
            diagnostic_message = ('The damper should be at the '
                                  'minimum position for ventilation but '
                                  'is significantly higher than this value.')
            color_code = 'RED'

            if energy_calc:
                dx_time = (len(energy_calc) - 1) * \
                    avg_step if len(energy_calc) > 1 else 1.0
                energy_impact = (sum(energy_calc) * 60.0) / \
                    (len(energy_calc) * dx_time)
        if avg_oaf - self.desired_oaf > self.excess_oaf_threshold:
            if diagnostic_message:
                diagnostic_message += ('Excess outdoor-air is being '
                                       'provided, this could increase '
                                       'heating and cooling energy '
                                       'consumption.')
            else:
                diagnostic_message = ('Excess outdoor-air is being '
                                      'provided, this could increase '
                                      'heating and cooling energy '
                                      'consumption.')
            color_code = 'RED'

            if energy_calc:
                dx_time = (len(energy_calc) - 1) * \
                    avg_step if len(energy_calc) > 1 else 1.0
                energy_impact = (sum(energy_calc) * 60.0) / \
                    (len(energy_calc) * dx_time)
                energy_impact = '%s' % float('%.2g' % energy_impact)
                energy_impact = str(energy_impact)
                energy_impact = ''.join([energy_impact, ' kWh/h'])

        elif not diagnostic_message:
            diagnostic_message = ('The calculated outdoor-air '
                                  'fraction is within configured '
                                  'limits')
            color_code = 'GREEN'

        dx_table = {
            'datetime': str(current_time),
            'diagnostic_name': ECON4,
            'diagnostic_message': diagnostic_message,
            'energy_impact': energy_impact,
            'color_code': color_code
        }
        #result.insert_table_row('Economizer_RCx', dx_table)
        result.log(diagnostic_message, logging.INFO)
        result = insert_ecam_data(result, dx_table, ecam_data)
        result = self.clear_data(result)
        return result

    def clear_data(self, diagnostic_result):
        '''reinitialize class insufficient_oa data.'''
        self.damper_signal_values = []
        self.oa_temp_values = []
        self.ra_temp_values = []
        self.ma_temp_values = []
        self.fan_speed_values = []
        self.timestamp = []
        return diagnostic_result


class insufficient_oa_intake(object):
    ''' Air-side HVAC ventilation diagnostic.

    insufficient_oa_intake uses metered data from a controller or
    BAS to diagnose when an AHU/RTU is providing inadequate ventilation.
    '''

    def __init__(self, data_window, no_required_data,
                 ventilation_oaf_threshold, minimum_damper_setpoint,
                 insufficient_damper_threshold, desired_oaf):

        self.oa_temp_values = []
        self.ra_temp_values = []
        self.ma_temp_values = []
        self.damper_signal_values = []
        self.cool_call_values = []
        self.timestamp = []

        '''Application thresholds (Configurable)'''
        self.data_window = float(data_window)
        self.no_required_data = no_required_data

        self.ventilation_oaf_threshold = float(ventilation_oaf_threshold)
        self.insufficient_damper_threshold = float(
            insufficient_damper_threshold)
        self.minimum_damper_setpoint = float(minimum_damper_setpoint)
        self.desired_oaf = float(desired_oaf)

    def econ_alg5(self, diagnostic_result, oatemp, ratemp, matemp,
                  damper_signal, economizer_conditon, current_time, ecam_data):
        '''Check app. pre-quisites and assemble data set for analysis.'''
        self.oa_temp_values.append(oatemp)
        self.ra_temp_values.append(ratemp)
        self.ma_temp_values.append(matemp)
        self.damper_signal_values.append(damper_signal)

        self.timestamp.append(current_time)
        elapsed_time = ((self.timestamp[-1] - self.timestamp[0])
                        .total_seconds()/60)
        elapsed_time = elapsed_time if elapsed_time > 0 else 1.0

        if (elapsed_time >= self.data_window and
                len(self.timestamp) >= self.no_required_data):
            diagnostic_result = self.insufficient_oa(
                diagnostic_result, current_time, ecam_data)
        return diagnostic_result

    def insufficient_oa(self, result, current_time, ecam_data):
        '''If the detected problems(s) are
        consistent generate a fault message(s).
        '''
        oaf = [(m - r) / (o - r) for o, r, m in zip(self.oa_temp_values,
                                                    self.ra_temp_values,
                                                    self.ma_temp_values)]
        avg_oaf = sum(oaf) / len(oaf) * 100.0
        avg_damper_signal = (sum(
            self.damper_signal_values) / len(self.damper_signal_values))

        if avg_oaf < 0 or avg_oaf > 125.0:
            diagnostic_message = ('Inconclusive result, the OAF '
                                  'calculation led to an '
                                  'unexpected value: {oaf}'.
                                  format(oaf=avg_oaf))
            color_code = 'GREY'
            result.log(diagnostic_message, logging.INFO)
            dx_table = {
                'datetime': str(current_time),
                'diagnostic_name': ECON5,
                'diagnostic_message': diagnostic_message,
                'energy_impact': None,
                'color_code': color_code
            }
            #result.insert_table_row('Economizer_RCx', dx_table)
            result = insert_ecam_data(result, dx_table, ecam_data)
            result = self.clear_data(result)
            return result

        diagnostic_message = ''
        if (
                (self.minimum_damper_setpoint - avg_damper_signal) >
                self.insufficient_damper_threshold):
            diagnostic_message = ('Outdoor-air damper is '
                                  'significantly below the minimum '
                                  'configured damper position.')

            color_code = 'RED'
            dx_table = {
                'datetime': str(current_time),
                'diagnostic_name': ECON5,
                'diagnostic_message': diagnostic_message,
                'energy_impact': None,
                'color_code': color_code
            }
            result.log(diagnostic_message, logging.INFO)
            #result.insert_table_row('Economizer_RCx', dx_table)
            result = insert_ecam_data(result, dx_table, ecam_data)
            result = self.clear_data(result)
            return result

        if (self.desired_oaf - avg_oaf) > self.ventilation_oaf_threshold:
            diagnostic_message = ('Insufficient outdoor-air '
                                  'is being provided for '
                                  'ventilation.')
            color_code = 'RED'
            dx_table = {
                'datetime': str(current_time),
                'diagnostic_name': ECON5,
                'diagnostic_message': diagnostic_message,
                'energy_impact': None,
                'color_code': color_code
            }
        else:
            diagnostic_message = ('The calculated outdoor-air'
                                  'fraction was within acceptable '
                                  'limits.')
            color_code = 'GREEN'
            dx_table = {
                'datetime': str(current_time),
                'diagnostic_name': ECON5,
                'diagnostic_message': diagnostic_message,
                'energy_impact': None,
                'color_code': color_code
            }

        #result.insert_table_row('Economizer_RCx', dx_table)
        result.log(diagnostic_message, logging.INFO)
        result = insert_ecam_data(result, dx_table, ecam_data)
        Application.pre_msg_time = []
        Application.pre_requiste_messages = []
        result = self.clear_data(result)
        return result

    def clear_data(self, diagnostic_result):
        '''reinitialize class insufficient_oa data.'''
        self.damper_signal_values = []
        self.oa_temp_values = []
        self.ra_temp_values = []
        self.ma_temp_values = []
        self.timestamp = []
        return diagnostic_result
