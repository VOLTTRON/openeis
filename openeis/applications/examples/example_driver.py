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
 
import logging
 
from django.db.models import Avg
 
from openeis.applications import DriverApplicationBaseClass, reports
from openeis.core.descriptors import Descriptor, InputDescriptor, \
    OutputDescriptor, ConfigDescriptor


class Application(DriverApplicationBaseClass):
    def __init__(self, *args, building_name=None, **kwargs):
        #Called after app has been staged
        """
        When applications extend this base class, they need to make
        use of any kwargs that were setup in config_param
        """
        super().__init__(*args, **kwargs)
        self.default_building_name_used = False
        if building_name is None:
            building_name = 'None supplied'
            self.default_building_name_used = True
        
        self.building_name = building_name
     
    @classmethod
    def get_self_descriptor(cls):
        name = 'Example Driver Application - Electricity Map'
        desc = 'This is an example driver application.\
                This method returns a Descriptor used by the UI on the run\
                analysis screen.\
                This Electricity Map is similar to Heat Map, however it\
                calculates WholeBuildingElectricity'
        return Descriptor(name=name, description=desc)
     
    @classmethod
    def get_config_parameters(cls):
        # Called by UI
        return {
            "building_name": ConfigDescriptor(str, "Building Name", optional=True)
            }
     
    @classmethod
    def required_input(cls):
        #Called by UI
        '''Returns a dictionary of required data.'''
        return {
             'electricity':InputDescriptor('WholeBuildingElectricity', 'Building Electricity')
            }
     
    @classmethod
    def output_format(cls, input_object):
        # Called when app is staged
        '''
        Output will have date, hour, and electricity use, used in a map later.
        '''
        topics = input_object.get_topics()
        load_topic = topics['electricity'][0]
        load_topic_parts = load_topic.split('/')
        output_topic_base = load_topic_parts[:-1]
        date_topic = '/'.join(output_topic_base+['heatmap', 'date'])
        hour_topic = '/'.join(output_topic_base+['heatmap', 'time'])
        load_topic = '/'.join(output_topic_base+['heatmap', 'electricity'])
        output_needs = {
            'Heat_Map': {
                'date': OutputDescriptor('string', date_topic),
                'hour': OutputDescriptor('integer', hour_topic),
                'electricity': OutputDescriptor('float', load_topic)
                }
            }
        return output_needs

    def reports(self):
        #Called by UI to create Viz
        """Describe how to present output to user
        Display this viz with these columns from this table

        display_elements is a list of display objects specifying viz and columns
        for that viz
        """

        report = reports.Report('Heat Map for Building Energy Electricity')

        text_blurb = reports.TextBlurb(text="Analysis of the extent of a building's daily, weekly, and seasonal shut off.")
        report.add_element(text_blurb)

        heat_map = reports.HeatMap(table_name='Heat_Map',
                                   x_column='hour',
                                   y_column='date',
                                   z_column='electricity',
                                   x_label='Hour of the Day',
                                   y_label='Date',
                                   z_label='Building Energy [kWh]')
        report.add_element(heat_map)

        text_guide1 = reports.TextBlurb(text="Horizontal banding indicates shut off during\
                                              periodic days (e.g. weekends).")
        report.add_element(text_guide1)

        text_guide2 = reports.TextBlurb(text="Unusual or unexplainable \"hot spots\"\
                                              may indicate poor equipment control.")
        report.add_element(text_guide2)

        text_guide3 = reports.TextBlurb(text="Vertical banding indicates consistent\
                                              daily scheduling of usage.")
        report.add_element(text_guide3)

        report_list = [report]

        return report_list

    def execute(self):
        """
        Output values for Heat Map.
        """
        self.out.log("Starting application: heat map.", logging.INFO)

        self.out.log("Querying database.", logging.INFO)
        loads = self.inp.get_query_sets('electricity', group_by='hour',
                                        group_by_aggregation=Avg,
                                        exclude={'value':None})
        
        base_topic = self.inp.get_topics()

        self.out.log("Compiling the report table.", logging.INFO)
        for x in loads[0]:
            datevalue = self.inp.localize_sensor_time(base_topic['electricity'][0], x[0])
            self.out.insert_row("Heat_Map", {
                'date': datevalue.date(),
                'hour': datevalue.hour,
                'electricity': x[1]
                }
            )