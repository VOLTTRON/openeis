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
from math import fabs
from openeis.applications.utils import conversion_utils as cu
from openeis.applications import (DrivenApplicationBaseClass,
                                  OutputDescriptor,
                                  ConfigDescriptor,
                                  InputDescriptor,
                                  Results,
                                  Descriptor,
                                  reports)

HOT_WATER_RCX1 = 'HW Differential Pressure Control Loop Dx'
HOT_WATER_RCX2 = 'HW Supply Temperature Control Loop Dx'
HOTWATER_DX1 = 'HW loop High Differential Pressure Dx'
HOTWATER_DX2 = 'HW loop Differential Pressure Reset Dx'
HOTWATER_DX3 = 'HW loop High Supply Temperature Dx'
HOTWATER_DX4 = 'HW loop Supply Temperature Reset Dx'
HOTWATER_DX5 = 'HW loop Low Delta-T Dx'


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
    hw_stsp_name = 'hws_temp_stpt'
    hwr_temp_name = 'hwr_temp'
    oa_temp_name = 'oa_temp'
    hw_pump_status_name = 'hw_pump_status'
    boiler_status_name = 'boiler_status'

    table_name = 'HotWaterViz'

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
        name = 'Hot Water Plant Data Visualization'
        desc = ('Hot Water Plant Data Visualization.')
        return Descriptor(name=name, description=desc)

    @classmethod
    def required_input(cls):
        '''Generate required inputs with description for
        user.
        '''
        return {
            cls.loop_dp_name:
                InputDescriptor('LoopDifferentialPressure',
                                'Hot water central plant loop differential '
                                'pressure',
                                count_min=0),
            cls.loop_dp_stpt_name:
                InputDescriptor('LoopDifferentialPressureSetPoint',
                                'Hot water central plant loop differential '
                                'pressure set point',
                                count_min=0),
            cls.pump_status_name:
                InputDescriptor('PumpStatus',
                                'Hot water central plant pump status',
                                count_min=0),
            cls.boiler_status_name:
                InputDescriptor('BoilerStatus',
                                'Hot water central plant boiler status',
                                count_min=0),
            cls.hw_pump_vfd_name:
                InputDescriptor('PumpVFDCommand',
                                'Hot water central plant pump VFD commands',
                                count_min=0),
            cls.hws_temp_name:
                InputDescriptor('SupplyWaterTemperature',
                                'Hot water central plant supply '
                                'water temperature',
                                count_min=1),
            cls.hw_stsp_name:
                InputDescriptor('SupplyWaterTemperatureSetPoint',
                                'Hot water central plant supply water '
                                'temperature set point',
                                count_min=0),
            cls.hwr_temp_name:
                InputDescriptor('ReturnWaterTemperature',
                                'Hot water central plant return '
                                'water temperature', count_min=0),
            cls.oa_temp_name:
                InputDescriptor('OutdoorAirTemperature',
                                'Outdoor Air Temperature', count_min=0)
        }

    @classmethod
    def reports(cls, output_format):
        '''Called by UI to create Viz.
        Describe how to present output to user.
        '''
        report = reports.Report('Retuning Report')
        report.add_element(reports.HWPlantViz
                           (table_name=cls.table_name))

        return [report]

    @classmethod
    def output_format(cls, input_object):
        '''Called when application is staged.
        Output will have the date-time and  error-message.
        '''
        result = super().output_format(input_object)
        topics = input_object.get_topics()
        diagnostic_topic = topics[cls.hws_temp_name][0]
        diagnostic_topic_parts = diagnostic_topic.split('/')
        output_topic_base = diagnostic_topic_parts[:-1]
        datetime_topic = '/'.join(output_topic_base+[cls.table_name, 'date'])
        
        loop_dp_topic = '/'.join(output_topic_base+[cls.table_name, cls.loop_dp_name])
        loop_dp_stpt_topic = '/'.join(output_topic_base+[cls.table_name, cls.loop_dp_stpt_name])
        pump_status_topic = '/'.join(output_topic_base+[cls.table_name, cls.pump_status_name])
        boiler_status_topic = '/'.join(output_topic_base+[cls.table_name, cls.boiler_status_name])
        hw_pump_vfd_topic = '/'.join(output_topic_base+[cls.table_name, cls.hw_pump_vfd_name])
        hws_temp_topic = '/'.join(output_topic_base+[cls.table_name, cls.hws_temp_name])
        hw_stsp_topic = '/'.join(output_topic_base+[cls.table_name, cls.hw_stsp_name])
        hwr_temp_topic = '/'.join(output_topic_base+[cls.table_name, cls.hwr_temp_name])
        oat_topic = '/'.join(output_topic_base+[cls.table_name, cls.oa_temp_name])

        output_needs = {
            cls.table_name: {
                'datetime': OutputDescriptor('string', datetime_topic),
                'OutdoorAirTemperature': OutputDescriptor('float', oat_topic),
                'LoopDifferentialPressure': OutputDescriptor('float', loop_dp_topic),
                'LoopDifferentialPressureSetPoint': OutputDescriptor('float', loop_dp_stpt_topic),
                'PumpStatus': OutputDescriptor('float', pump_status_topic),
                'BoilerStatus': OutputDescriptor('float', boiler_status_topic),
                'HotWaterPumpVfd': OutputDescriptor('float', hw_pump_vfd_topic),
                'HotWaterSupplyTemperature': OutputDescriptor('float', hws_temp_topic),
                'HotWaterTemperatureSetPoint': OutputDescriptor('float', hw_stsp_topic),
                'HotWaterReturnTemperature': OutputDescriptor('float', hwr_temp_topic),
            }
        }
        result.update(output_needs)
        return result

    def run(self, current_time, points):
        '''
        Check algorithm pre-quisites and assemble data set for analysis.
        '''
        device_dict = {}
        result = Results()
        topics = self.inp.get_topics()
        topic = topics[self.hws_temp_name][0]
        current_time = self.inp.localize_sensor_time(topic, current_time)
        base_topic = self.inp.get_topics()
        meta_topics = self.inp.get_topics_meta()

        unit_dict = {}
        if len(base_topic[self.oa_temp_name]) > 0:
            unit_dict[self.oa_temp_name] = meta_topics[self.oa_temp_name][base_topic[self.oa_temp_name][0]]['unit']
        if len(base_topic[self.hws_temp_name]) > 0:
            unit_dict[self.hws_temp_name] = meta_topics[self.hws_temp_name][base_topic[self.hws_temp_name][0]]['unit']
        if len(base_topic[self.hwr_temp_name]) > 0:
            unit_dict[self.hwr_temp_name] = meta_topics[self.hwr_temp_name][base_topic[self.hwr_temp_name][0]]['unit']
        if len(base_topic[self.hw_stsp_name]) > 0:
            unit_dict[self.hw_stsp_name] = meta_topics[self.hw_stsp_name][base_topic[self.hw_stsp_name][0]]['unit']

        for key, value in points.items():
            device_dict[key.lower()] = value

        oatemp_data = []
        loop_dp_values = []
        loop_dp_stpt_values = []
        hw_pump_status_values = []
        boiler_status_values = []
        hw_pump_vfd_values = []
        hw_stsp_values = []
        hws_temp_values = []
        hwr_temp_values = []

        for key, value in device_dict.items():
            if key.startswith(self.loop_dp_stpt_name) and value is not None:
                loop_dp_stpt_values.append(value)
            elif key.startswith(self.loop_dp_name) and value is not None:
                loop_dp_values.append(value)
            elif key.startswith(self.hw_pump_status_name) and value is not None:
                hw_pump_status_values.append(value)
            elif key.startswith(self.boiler_status_name) and value is not None:
                boiler_status_values.append(value)
            elif key.startswith(self.hw_pump_vfd_name) and value is not None:
                hw_pump_vfd_values.append(value)
            elif key.startswith(self.hw_stsp_name) and value is not None:
                hw_stsp_values.append(value)
            elif key.startswith(self.hws_temp_name) and value is not None:
                hws_temp_values.append(value)
            elif key.startswith(self.hwr_temp_name) and value is not None:
                hwr_temp_values.append(value)
            elif (key.startswith(self.oa_temp_name) #OAT
                  and value is not None):
                oatemp_data.append(value)

        if 'celcius' or 'kelvin' in unit_dict.values:
            if self.oa_temp_name in unit_dict:
                if unit_dict[self.oa_temp_name] == 'celcius':
                    oatemp_data = cu.convertCelciusToFahrenheit(oatemp_data)
                elif unit_dict[self.oa_temp_name] == 'kelvin':
                    oatemp_data = cu.convertKelvinToCelcius(
                        cu.convertCelciusToFahrenheit(oatemp_data))
            if self.hw_stsp_name in unit_dict:
                if unit_dict[self.hw_stsp_name] == 'celcius':
                    hw_stsp_values = cu.convertCelciusToFahrenheit(hw_stsp_values)
                elif unit_dict[self.hw_stsp_name] == 'kelvin':
                    hw_stsp_values = cu.convertKelvinToCelcius(
                        cu.convertCelciusToFahrenheit(hw_stsp_values))
            if self.hw_stsp_name in unit_dict:
                if unit_dict[self.hws_temp_name] == 'celcius':
                    hws_temp_values = cu.convertCelciusToFahrenheit(hws_temp_values)
                elif unit_dict[self.hws_temp_name] == 'kelvin':
                    hws_temp_values = cu.convertKelvinToCelcius(
                        cu.convertCelciusToFahrenheit(hws_temp_values))
            if self.hwr_temp_name in unit_dict:
                if unit_dict[self.hwr_temp_name] == 'celcius':
                    hwr_temp_values = cu.convertCelciusToFahrenheit(hwr_temp_values)
                elif unit_dict[self.hwr_temp_name] == 'kelvin':
                    hwr_temp_values = cu.convertKelvinToCelcius(
                        cu.convertCelciusToFahrenheit(hwr_temp_values))


        oatemp = hw_stsp_temp = hws_temp = hwr_temp = None
        loop_dp = loop_dp_stpt = None
        hw_pump_status = boiler_status = None
        hw_pump_vfd = None

        if oatemp_data:
            oatemp = (sum(oatemp_data) / len(oatemp_data))
        if hw_stsp_values:
            hw_stsp_temp = (sum(hw_stsp_values) / len(hw_stsp_values))
        if hws_temp_values:
            hws_temp = (sum(hws_temp_values) / len(hws_temp_values))
        if hwr_temp_values:
            hwr_temp = (sum(hwr_temp_values) / len(hwr_temp_values))

        if loop_dp_stpt_values:
            loop_dp_stpt = (sum(loop_dp_stpt_values) / len(loop_dp_stpt_values))
        if loop_dp_values:
            loop_dp = (sum(loop_dp_values) / len(loop_dp_values))

        if hw_pump_status_values:
            hw_pump_status = (sum(hw_pump_status_values) / len(hw_pump_status_values))
        if boiler_status_values:
            boiler_status = (sum(boiler_status_values) / len(boiler_status_values))

        if hw_pump_vfd_values:
            hw_pump_vfd = (sum(hw_pump_vfd_values) / len(hw_pump_vfd_values))


        out_data = {
            'datetime': str(current_time),
        }

        if not oatemp is None:
            out_data['OutdoorAirTemperature'] = oatemp
        if not hws_temp is None:
            out_data['HotWaterSupplyTemperature'] = hws_temp
        if not hwr_temp is None:
            out_data['HotWaterReturnTemperature'] = hwr_temp
        if not hw_stsp_temp is None:
            out_data['HotWaterTemperatureSetPoint'] = hw_stsp_temp

        if not loop_dp is None:
            out_data['LoopDifferentialPressure'] = loop_dp
        if not loop_dp_stpt is None:
            out_data['LoopDifferentialPressureSetPoint'] = loop_dp_stpt

        if not hw_pump_status is None:
            out_data['PumpStatus'] = hw_pump_status
        if not boiler_status is None:
            out_data['BoilerStatus'] = boiler_status

        if not hw_pump_vfd is None:
            out_data['HotWaterPumpVfd'] = hw_pump_vfd

        result.insert_table_row(self.table_name, out_data)

        return result
