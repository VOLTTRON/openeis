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


class Application(DrivenApplicationBaseClass):
    """
        Application to detect and correct operational problems for AHUs/RTUs.
    """

    #Because the data point is recognized by the prefix of the point name, avoid using names that have same prefix
    #Eg: da_temp and da_temp_sp make all da_temp_sp data points be included in da_temp
    timestamp = 'date' #For Rcx
    oa_temp_name = 'oa_temp'
    ma_temp_name = 'ma_temp'
    ra_temp_name = 'ra_temp'
    oaf_name = 'oa_fraction'
    fan_status_name = 'fan_status'
    fan_speedcmd_name = 'fan_speedcmd'
    outdoor_damper_name = 'damper_signal'
    da_temp_name = 'da_temp'
    da_temp_setpoint_name = 'discharge_temp_setpoint'
    occ_name = 'occupancy'
    discharge_sp_name = 'discharge_staticpressure'
    sp_setpoint_name = 'staticpressure_setpoint'

    returnfan_speedcmd_name = 'returnfan_speedcmd'
    cc_valve_name = 'cc_valve_pos'
    hc_valve_name = 'hc_valve_pos'

    def __init__(self, *args, building_name=None, **kwargs):
        #Called after app has been staged
        """
        When applications extend this base class, they need to make
        use of any kwargs that were setup in config_param
        """
        super().__init__(*args, **kwargs)

        self.default_building_name_used = False

        if building_name is None:
            building_name = "None supplied"
            self.default_building_name_used = True

        self.building_name = building_name

    @classmethod
    def get_config_parameters(cls):
        # Called by UI
        return {}

    @classmethod
    def get_self_descriptor(cls):
        name = 'Ecam Visualization for AHU HVAC Systems'
        desc = 'Ecam Visualization for AHU HVAC Systems'
        return Descriptor(name=name, description=desc)

    @classmethod
    def required_input(cls):
        '''Generate required inputs with description for user.'''
        return {
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
            cls.outdoor_damper_name:
            InputDescriptor('OutdoorDamperSignal', 'AHU outdoor-air damper '
                            'signal', count_min=0),
            cls.occ_name:
            InputDescriptor('OccupancyMode',
                            'OccupancyMode', count_min=0, count_max=1),
            cls.discharge_sp_name:
            InputDescriptor('DuctStaticPressure',
                            'DuctStaticPressure', count_min=0, count_max=1),
            cls.sp_setpoint_name:
            InputDescriptor('DuctStaticPressureSetPoint',
                            'DuctStaticPressureSetPoint', count_min=0),
            cls.fan_speedcmd_name:
            InputDescriptor('SupplyFanSpeed',
                            'AHU supply fan speed', count_min=0),
            cls.returnfan_speedcmd_name:
            InputDescriptor('ReturnFanSpeed',
                            'ReturnFanSpeed', count_min=0),
            cls.fan_status_name:
            InputDescriptor('SupplyFanStatus',
                            'AHU Supply Fan Status', count_min=0),
            cls.cc_valve_name:
            InputDescriptor('CoolingCoilValvePosition',
            #InputDescriptor('ChilledWaterValvePosition', #temporary
                            'AHU cooling coil valve position',
                            count_min=0),
            cls.hc_valve_name:
            InputDescriptor('HeatingCoilValvePosition',
            #InputDescriptor('ChilledWaterValvePosition', #temporary
                            'AHU heating coil valve position',
                            count_min=0),
            cls.da_temp_name:
            InputDescriptor('DischargeAirTemperature',
                            'AHU discharge-air temperature', count_min=0),
            cls.da_temp_setpoint_name:
            InputDescriptor('DischargeAirTemperatureSetPoint',
                            'AHU discharge-air temperature setpoint', count_min=0)
        }

    def reports(self):
        '''Called by UI to create Viz.

        Describe how to present output to user
        '''
        report = reports.Report('AHU Ecam Report')

        report.add_element(reports.AhuEcam(table_name='AhuEcam'))

        return [report]

    @classmethod
    def output_format(cls, input_object):
        '''Called when application is staged.

        Output will have the date-time and  error-message.
        '''
        result = super().output_format(input_object)
        topics = input_object.get_topics()
        topic = topics[cls.oa_temp_name][0]
        topic_parts = topic.split('/')
        output_topic_base = topic_parts[:-1]
        ts_topic = '/'.join(output_topic_base + ['ahuEcam', cls.timestamp])
        oat_topic = '/'.join(output_topic_base+['ahuEcam', cls.oa_temp_name])
        mat_topic = '/'.join(output_topic_base+['ahuEcam', cls.ma_temp_name])
        rat_topic = '/'.join(output_topic_base+['ahuEcam', cls.ra_temp_name])
        od_topic = '/'.join(output_topic_base+['ahuEcam', cls.outdoor_damper_name])
        occ_topic = '/'.join(output_topic_base+['ahuEcam', cls.occ_name])
        discharge_sp_topic = '/'.join(output_topic_base+['ahuEcam', cls.discharge_sp_name])
        sp_setpoint_topic = '/'.join(output_topic_base+['ahuEcam', cls.sp_setpoint_name])
        dat_topic = '/'.join(output_topic_base+['ahuEcam', cls.da_temp_name])
        datstpt_topic = '/'.join(output_topic_base+['ahuEcam', cls.da_temp_setpoint_name])
        fsp_topic = '/'.join(output_topic_base+['ahuEcam', cls.fan_speedcmd_name])
        fst_topic = '/'.join(output_topic_base+['ahuEcam', cls.fan_status_name])
        return_fanspeed_topic = '/'.join(output_topic_base+['ahuEcam', cls.returnfan_speedcmd_name])
        ccv_topic = '/'.join(output_topic_base+['ahuEcam', cls.cc_valve_name])
        hcv_topic = '/'.join(output_topic_base+['ahuEcam', cls.hc_valve_name])
        oaf_topic = '/'.join(output_topic_base+['ahuEcam', cls.oaf_name])

        output_needs = {
            'AhuEcam': {
                'datetime': OutputDescriptor('string', ts_topic),
                'OutdoorAirTemperature': OutputDescriptor('float', oat_topic),
                'MixedAirTemperature': OutputDescriptor('float', mat_topic),
                'ReturnAirTemperature': OutputDescriptor('float', rat_topic),
                'DischargeAirTemperature': OutputDescriptor('float', dat_topic),
                'DischargeAirTemperatureSetPoint': OutputDescriptor('float', datstpt_topic),
                'SupplyFanStatus': OutputDescriptor('float', fst_topic),
                'SupplyFanSpeed': OutputDescriptor('float', fsp_topic),
                'OutdoorDamper': OutputDescriptor('float', od_topic),
                'CCV': OutputDescriptor('float', ccv_topic),
                'HCV': OutputDescriptor('float', hcv_topic),
                'OutdoorAirFraction': OutputDescriptor('float', oaf_topic),
                'ReturnFanSpeed': OutputDescriptor('float', return_fanspeed_topic),
                'OccupancyMode': OutputDescriptor('float', occ_topic),
                'DuctStaticPressure': OutputDescriptor('float', discharge_sp_topic),
                'DuctStaticPressureSetPoint': OutputDescriptor('float', sp_setpoint_topic),
            }
        }

        #return output_needs
        result.update(output_needs)
        return result

    def run(self, current_time, points):
        """
            Main run method that is called by the DrivenBaseClass.
        """
        device_dict = {}
        result = Results()
        topics = self.inp.get_topics()
        topic = topics[self.oa_temp_name][0]
        current_time = self.inp.localize_sensor_time(topic, current_time)
        base_topic = self.inp.get_topics()
        meta_topics = self.inp.get_topics_meta()
        unit_dict = {
            self.oa_temp_name: meta_topics[self.oa_temp_name][base_topic[self.oa_temp_name][0]]['unit']
        }

        if len(base_topic[self.ma_temp_name]) > 0:
            unit_dict[self.ma_temp_name] = meta_topics[self.ma_temp_name][base_topic[self.ma_temp_name][0]]['unit']
        if len(base_topic[self.ra_temp_name]) > 0:
            unit_dict[self.ra_temp_name] = meta_topics[self.ra_temp_name][base_topic[self.ra_temp_name][0]]['unit']
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
        datemp_data = []
        datemp_stpt_data = []
        ccv_data = []
        fan_speedcmd_data = []
        fan_status_data = []
        hcv_data = []
        return_fan_speedcmd_data = []
        occ_data = []
        discharge_sp_data = []
        staticpressure_sp_data = []

        for key, value in device_dict.items():
            if (key.startswith(self.outdoor_damper_name) #Damper
                    and value is not None):
                damper_data.append(value)
            elif (key.startswith(self.oa_temp_name) #OAT
                  and value is not None):
                oatemp_data.append(value)
            elif (key.startswith(self.ma_temp_name) #MAT
                  and value is not None):
                matemp_data.append(value)
            elif (key.startswith(self.ra_temp_name) #RAT
                  and value is not None):
                ratemp_data.append(value)
            elif (key.startswith(self.da_temp_name) #DAT
                  and value is not None):
                datemp_data.append(value)
            elif (key.startswith(self.da_temp_setpoint_name) #DAT SetPoint
                  and value is not None):
                datemp_stpt_data.append(value)
            elif (key.startswith(self.cc_valve_name) #CoolCoilValvePos
                  and value is not None):
                ccv_data.append(value)
            elif (key.startswith(self.hc_valve_name) #HeatCoilValvePos
                  and value is not None):
                hcv_data.append(value)
            elif (key.startswith(self.fan_speedcmd_name) #Fan speed
                  and value is not None):
                fan_speedcmd_data.append(value)
            elif (key.startswith(self.fan_status_name) #Fan status
                  and value is not None):
                fan_status_data.append(value)
            elif (key.startswith(self.returnfan_speedcmd_name) #returnfan_speedcmd_name
                  and value is not None):
                return_fan_speedcmd_data.append(value)
            elif (key.startswith(self.occ_name) #Occupancy
                  and value is not None):
                occ_data.append(value)
            elif (key.startswith(self.discharge_sp_name) #discharge_sp_data
                  and value is not None):
                discharge_sp_data.append(value)
            elif (key.startswith(self.sp_setpoint_name) #staticpressure_sp_data
                  and value is not None):
                staticpressure_sp_data.append(value)

        if not oatemp_data:
            return result

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
        matemp_data = None
        ratemp = datemp = datemp_stpt = None
        fanstatus = fanspeed = outdoor_damper = ccv = hcv = None
        oaf = None

        return_fan_speedcmd = None
        occupancy = None
        discharge_sp = staticpressure_sp = None

        if matemp_data:
            matemp = (sum(matemp_data) / len(matemp_data))
        if ratemp_data:
            ratemp = (sum(ratemp_data) / len(ratemp_data))
        if datemp_data:
            datemp = (sum(datemp_data) / len(datemp_data))
        if datemp_stpt_data:
            datemp_stpt = (sum(datemp_stpt_data) / len(datemp_stpt_data))
        if fan_status_data:
            fanstatus = (sum(fan_status_data) / len(fan_status_data))
        if fan_speedcmd_data:
            fanspeed = (sum(fan_speedcmd_data) / len(fan_speedcmd_data))
        if damper_data:
            outdoor_damper = (sum(damper_data) / len(damper_data))
        if ccv_data:
            ccv = (sum(ccv_data) / len(ccv_data))
        if hcv_data:
            hcv = (sum(hcv_data) / len(hcv_data))
        if matemp_data and ratemp_data:
            denominator = oatemp - ratemp
            if denominator == 0:
                oaf = 0
            else:
                oaf = (matemp - ratemp) / denominator
            if oaf > 1:
                oaf = 1
            elif oaf < 0:
                oaf = 0
            oaf *= 100

        if return_fan_speedcmd_data:
            return_fan_speedcmd = (sum(return_fan_speedcmd_data) / len(return_fan_speedcmd_data))
        if occ_data:
            occupancy = (sum(occ_data) / len(occ_data))*100
        if discharge_sp_data:
            discharge_sp = (sum(discharge_sp_data) / len(discharge_sp_data))
        if staticpressure_sp_data:
            staticpressure_sp = (sum(staticpressure_sp_data) / len(staticpressure_sp_data))

        out_data = {
            'datetime': str(current_time),
            'OutdoorAirTemperature': oatemp,
            'MixedAirTemperature': None if not matemp else matemp,
            'ReturnAirTemperature': None if ratemp is None else ratemp,
            'DischargeAirTemperature': None if datemp is None else datemp,
            'DischargeAirTemperatureSetPoint': None if datemp_stpt is None else datemp_stpt,
            'SupplyFanStatus': None if fanstatus is None else fanstatus,
            'SupplyFanSpeed': None if fanspeed is None else fanspeed,
            'OutdoorDamper': None if outdoor_damper is None else outdoor_damper,
            'CCV': None if ccv is None else ccv,
            'HCV': None if hcv is None else hcv,
            'OutdoorAirFraction': None if oaf is None else oaf,
            'ReturnFanSpeed': None if return_fan_speedcmd is None else return_fan_speedcmd,
            'OccupancyMode': None if occupancy is None else occupancy,
            'DuctStaticPressure': None if discharge_sp is None else discharge_sp,
            'DuctStaticPressureSetPoint': None if staticpressure_sp is None else staticpressure_sp,
        }
        result.insert_table_row('AhuEcam', out_data)
        return result

