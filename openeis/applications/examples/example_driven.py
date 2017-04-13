# -*- coding: utf-8 -*- {{{
# vim: set fenc=utf-8 ft=python sw=4 ts=4 sts=4 et:
#
# Copyright (c) 2014, Battelle Memorial Institute
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.
#
#
# This material was prepared as an account of work sponsored by an
# agency of the United States Government.  Neither the United States
# Government nor the United States Department of Energy, nor Battelle,
# nor any of their employees, nor any jurisdiction or organization
# that has cooperated in the development of these materials, makes
# any warranty, express or implied, or assumes any legal liability
# or responsibility for the accuracy, completeness, or usefulness or
# any information, apparatus, product, software, or process disclosed,
# or represents that its use would not infringe privately owned rights.
#
# Reference herein to any specific commercial product, process, or
# service by trade name, trademark, manufacturer, or otherwise does
# not necessarily constitute or imply its endorsement, recommendation,
# or favoring by the United States Government or any agency thereof,
# or Battelle Memorial Institute. The views and opinions of authors
# expressed herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY
# operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830
#
#}}}

from openeis.applications import (DrivenApplicationBaseClass,
                                  InputDescriptor,
                                  OutputDescriptor,
                                  ConfigDescriptor,
                                  Results,
                                  Descriptor,
                                  reports)

import logging

class Application(DrivenApplicationBaseClass):
    """
    Test application for verifying application API
    """



    def __init__(self,*args, building_sq_ft=-1, building_year_constructed=-1, building_name=None,**kwargs):
        #Called after app has been staged
        """
        When applications extend this base class, they need to make
        use of any kwargs that were setup in config_param
        """
        super().__init__(*args,**kwargs)

        self.default_building_name_used = False

        if building_sq_ft < 0:
            raise Exception("Invalid input for building_sq_ft")
        if building_year_constructed < 0:
            raise Exception("Invalid input for building_sq_ft")
        if building_name is None:
            building_name = "None supplied"
            self.default_building_name_used = True

        self.sq_ft = building_sq_ft
        self.building_year = building_year_constructed
        self.building_name = building_name

        self.first = True

        self.counter = 0

    @classmethod
    def get_self_descriptor(cls):
        name = 'test_driven'
        desc = 'test_driven'
        return Descriptor(name=name, description=desc)


    @classmethod
    def get_config_parameters(cls):
        #Called by UI
        return {
                    "building_sq_ft": ConfigDescriptor(float, "Square footage", value_min=200),
                    "building_year_constructed": ConfigDescriptor(int, "Consruction Year", value_min=1800, value_max=2014),
                    "building_name": ConfigDescriptor(str, "Building Name", optional=True)

                }
        
    
    @classmethod
    def required_input(cls):
        return {
                    'OAT':InputDescriptor('OutdoorAirTemperature','Outdoor Temp', count_max=None),
                    'load':InputDescriptor('WholeBuildingElectricity','Building Load'),
                    'natgas':InputDescriptor('NaturalGasEnergy','Natural Gas usage')
                }

    @classmethod
    def output_format(cls, input_object):
        output_needs = super().output_format(input_object)
        #Called when app is staged
        topic_map = input_object.get_topics()
        # Work with topics["OAT"][0] to get building topic
#         descriptor_column = 'site/building/analysis/description'
        output_needs['output'] = {'time': OutputDescriptor('timestamp', 'time')}

        out_col_fmt = '{g}_{n}'

        #Table per topic, regardless of group
        for group, topic_list in topic_map.items():
            for i, topic in enumerate(topic_list,start=1):
                out_topic = topic+'/output'
                out_col = out_col_fmt.format(g=group, n=i)
                output_needs['output'][out_col] = OutputDescriptor('string', out_topic)

#tables for groups

#         for group in topic_map:
#             table = table_name.format(input_group= group)
#             output_needs[table] = {}
#             for topic in topic_map[group]:
#                 outputle_needs[output_needs[table]][topic] = OutputDescriptor('String', output_topic.format(input_topic=topic))
#
        return output_needs

    @classmethod
    def reports(cls, output_object):
        # Called by UI to create Viz
        """Describe how to present output to user
        Display this viz with these columns from this table
        """
        report = reports.Report('Report for Example Driven Application')

        text_blurb = reports.TextBlurb(text="Sample Text Blurb.")
        report.add_element(text_blurb)

        report_list = [report]

        return report_list

    def run(self, time, inputs):
        results = Results()

        if self.first:
            results.log('First Post!!!!11111ELEVENTY', logging.INFO)
            self.first = False

        inputs['time'] = time

        results.insert_table_row('output', inputs)

        self.counter += 1
        results.command('/awesome/counter', self.counter)

        return results

    def shutdown(self):
        results = Results()
        results.log('ARG!! I DIED!!', logging.INFO)
        return results



