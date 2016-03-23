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

    #zonetemp value must not be a substring of zonetemp_sp (eg. zonetemp vs zonetemp_sp)
    timestamp = 'date' #For Rcx
    zone_temp_name = 'ZoneTemperature'
    zone_setpoint_name = 'ZoneTemperatureSetPoint'
    zone_reheatvlv_name = 'TerminalBoxReheatValvePosition'
    zone_damperpos_name = 'TerminalBoxDamperCommand'
    zone_occ_name = 'ZoneOccupancyMode'
    zone_airflow_name = 'TerminalBoxFanAirflow'
    sep = '___'
    table_name = 'ZoneEcam'
    zone_topics = [
        zone_temp_name, zone_setpoint_name,
        zone_reheatvlv_name, zone_damperpos_name,
        zone_occ_name, zone_airflow_name
    ]
    
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
        name = 'Zone Data Visualization'
        desc = 'Zone Data Visualization.'
        return Descriptor(name=name, description=desc)

    @classmethod
    def required_input(cls):
        '''Generate required inputs with description for user.'''
        return {
            cls.zone_temp_name:
            InputDescriptor('ZoneTemperature',
                            cls.zone_temp_name, count_min=1, count_max=1),
            cls.zone_damperpos_name:
            InputDescriptor('TerminalBoxDamperCommand',
                            cls.zone_damperpos_name, count_min=0, count_max=1),
            cls.zone_setpoint_name:
            InputDescriptor('ZoneTemperatureSetPoint',
                            cls.zone_setpoint_name, count_min=0, count_max=1),
            cls.zone_reheatvlv_name:
            InputDescriptor('TerminalBoxReheatValvePosition',
                            cls.zone_reheatvlv_name, count_min=0, count_max=1),
            cls.zone_occ_name:
            InputDescriptor('OccupancyMode',
                            cls.zone_occ_name, count_min=0, count_max=1),
            cls.zone_airflow_name:
            InputDescriptor('TerminalBoxFanAirflow',
                            cls.zone_airflow_name, count_min=0, count_max=1),
        }

    def reports(self):
        '''Called by UI to create Viz.

        Describe how to present output to user
        '''
        report = reports.Report('Retuning - Zones')
        report.add_element(reports.ZoneEcam(table_name='ZoneEcam'))
        return [report]

    @classmethod
    def output_format(cls, input_object):
        '''Called when application is staged.

        Output will have the date-time and  error-message.
        '''
        result = super().output_format(input_object)
        topics = input_object.get_topics()

        output_needs = {
            cls.table_name: {
                'datetime': OutputDescriptor('string', '')
            }
        }

        for zone_topic in cls.zone_topics:
            if zone_topic in topics.keys():
                for i, topic in enumerate(topics[zone_topic], start=1):
                    topic_parts = topic.split('/')
                    zone = topic_parts[-2]
                    output_needs[cls.table_name][zone_topic + cls.sep + zone] = OutputDescriptor('float', '')

        # for topic in topics[cls.zone_temp_name]:
        #     topic_parts = topic.split('/')
        #     zone = topic_parts[2]
        #     output_needs[cls.table_name][cls.zone_temp_name + cls.sep +zone] = OutputDescriptor('float', '')
        #
        # for topic in topics[cls.zone_setpoint_name]:
        #     topic_parts = topic.split('/')
        #     zone = topic_parts[2]
        #     output_needs[cls.table_name][cls.zone_setpoint_name + cls.sep + zone] = OutputDescriptor('float', "")
        #
        # for topic in topics[cls.zone_reheatvlv_name]:
        #     topic_parts = topic.split('/')
        #     zone = topic_parts[2]
        #     output_needs[cls.table_name][cls.zone_reheatvlv_name + cls.sep + zone] = OutputDescriptor('float', '')
        #
        # for topic in topics[cls.zone_occ_name]:
        #     topic_parts = topic.split('/')
        #     zone = topic_parts[2]
        #     output_needs[cls.table_name][cls.zone_occ_name + cls.sep + zone] = OutputDescriptor('float', '')
        #
        # for topic in topics[cls.zone_damperpos_name]:
        #     topic_parts = topic.split('/')
        #     zone = topic_parts[2]
        #     output_needs[cls.table_name][cls.zone_damperpos_name + cls.sep + zone] = OutputDescriptor('float', '')
        #
        # for topic in topics[cls.zone_airflow_name]:
        #     topic_parts = topic.split('/')
        #     zone = topic_parts[2]
        #     output_needs[cls.table_name][cls.zone_airflow_name + cls.sep + zone] = OutputDescriptor('float', '')

        result.update(output_needs)
        return result

    def run(self, current_time, points):
        """
            Main run method that is called by the DrivenBaseClass.
            points ex: [{'zonetemp_1':72.0,'zonetemp_2':69.2}]
        """
        result = Results()
        topics = self.inp.get_topics()
        topic = topics[self.zone_temp_name][0]
        current_time = self.inp.localize_sensor_time(topic, current_time)

        out_data = {
            'datetime': str(current_time)
        }
        for zone_topic in self.zone_topics:
            if zone_topic in topics.keys():
                for i, topic in enumerate(topics[zone_topic], start=1):
                    topic_parts = topic.split('/')
                    zone = topic_parts[-2] #the second last item
                    out_data[zone_topic + self.sep + zone] = points[zone_topic + '_' + str(i)]

        result.insert_table_row(self.table_name, out_data)
        return result
