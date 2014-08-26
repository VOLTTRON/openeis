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

"""
Energy signature: plot power as a function of outside temperature.

Shows the sensitivity of building electrical energy use to weather.

Includes a weather sensitivity metric.
"""


from openeis.applications import DriverApplicationBaseClass, InputDescriptor, \
    OutputDescriptor, ConfigDescriptor
from openeis.applications import reports
import logging
from django.db.models import Avg
from .utils.spearman import findSpearmanRank


WEATHER_SENSITIVITY_TABLE_NAME = 'Weather_Sensitivity'
LOAD_PROFILE_TABLE_NAME = 'Load_Profile'


class Application(DriverApplicationBaseClass):

    def __init__(self, *args, building_name=None, a_value_from_a_list=None,
                 **kwargs):
        # Called after app has been staged
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
        values = ['apple','banana', 'grapes','pear']


        return {
            "building_name": ConfigDescriptor(str, "Building Name", optional=True),
            "a_value_from_a_list": ConfigDescriptor(str, "Fruit", optional=True, value_list=values)
            }


    @classmethod
    def required_input(cls):
        # Called by UI
        # Sort out units.
        return {
            'oat':InputDescriptor('OutdoorAirTemperature', 'Outdoor Temp'),
            'load':InputDescriptor('WholeBuildingElectricity', 'Building Load')
            }

    @classmethod
    def output_format(cls, input_object):
        # Called when app is staged
        """
        Output:
            Energy Signature: outside air temperature and loads.
                Data will be used to scatter plot.
            Weather Sensitivity: dependent on OAT and loads.
        """
        topics = input_object.get_topics()
        load_topic = topics['load'][0]
        load_topic_parts = load_topic.split('/')
        output_topic_base = load_topic_parts[:-1]
        value_topic = '/'.join(output_topic_base + ['energysignature', 'weather sensitivity'])
        oat_topic = '/'.join(output_topic_base + ['energysignature', 'oat'])
        load_topic = '/'.join(output_topic_base + ['energysignature', 'load'])

        output_needs = {
            WEATHER_SENSITIVITY_TABLE_NAME: {
                'value':OutputDescriptor('string', value_topic)
                },
            LOAD_PROFILE_TABLE_NAME: {
                'oat':OutputDescriptor('float', oat_topic),
                'load':OutputDescriptor('float', load_topic)
                }
            }
        return output_needs


    @classmethod
    def reports(cls, output_object):
        # Called by UI to create Viz
        """Describe how to present output to user
        Display this viz with these columns from this table

        display_elements is a list of display objects specifying viz and columns
        for that viz
        """

        '''Name of the overall report'''
        report = reports.Report('Energy Signature Report')


        ''' The table report takes in a list of tuples which tell the report
         how to order columns and what to call them.
         ((db_col_nameA, report_display_name1),(db_col_nameB, report_display_name2),)
         In this example, db_col_nameA is labeled with report_display_name1
         and is the first column in the displayed report table

        In this application there is only one column in the report table
        "Sensitivity" and the values are drawn from the "value" column of the
        output data table that is used, WEATHER_SENSITIVITY_TABLE_NAME
        '''

        column_info = (('value', 'Sensitivity'),)

        ''' This text blurb will be displayed at the top of the report
        '''
        text_blurb = reports.TextBlurb("Analysis of the relationship of power intensity to outdoor temperature.")

        '''Add the element to the report'''
        report.add_element(text_blurb)

        '''
        The reports.Table takes an output table that was specified in the
        output_format method. This table name must match exactly the
        table name specified in output_needs.

        The displayed title of the report can be set with the keyword argument
        "title". This is used for display only.
        '''
        summary_table = reports.Table(WEATHER_SENSITIVITY_TABLE_NAME,
                                      column_info,
                                      title='Weather Sensitivity',
                                      description='A description of the sensitivity')

        '''Add the summary table to the report'''
        report.add_element(summary_table)


        ''' The ScatterPlot visualization can take a list of xydatasets to
        display. XYDataSet takes a table name as specified in the output_format
        method of the application. This table must exactly match the name of a
        table specified in output_needs. A title for display can also be set.

        The ScatterPlot also takes labels for the x and y axes.
        '''

        xy_dataset_list = []
        ''' Send in the oat and load columns of the Load_Profile table.'''
        xy_dataset_list.append(reports.XYDataSet(LOAD_PROFILE_TABLE_NAME, 'oat', 'load'))

        '''Create a scatterplot which uses the datasets in the xy_dataset_list'''
        scatter_plot = reports.ScatterPlot(xy_dataset_list,
                                           title='Time Series Load Profile',
                                           x_label='Outside Air Temperature',
                                           y_label='Power')
        '''Add it to the report'''
        report.add_element(scatter_plot)
        # list of report objects

        report_list = [report]

        return report_list

    def execute(self):
        # Called after User hits GO
        """
        Calculates weather sensitivity using Spearman rank.
        Also, outputs data points for energy signature scatter plot.
        """
        self.out.log("Starting Spearman rank", logging.INFO)

        # gather loads and outside air temperatures. Reduced to an hourly average
        load_query = self.inp.get_query_sets('load', group_by='hour',
                                             group_by_aggregation=Avg,
                                             exclude={'value':None},
                                             wrap_for_merge=True)
        oat_query = self.inp.get_query_sets('oat', group_by='hour',
                                             group_by_aggregation=Avg,
                                             exclude={'value':None},
                                             wrap_for_merge=True)

        merged_load_oat = self.inp.merge(load_query, oat_query)

        load_values = []
        oat_values = []

        # Output for scatter plot
        for x in merged_load_oat:
            load_values.append(x['load'][0])
            oat_values.append(x['oat'][0])
            self.out.insert_row(LOAD_PROFILE_TABLE_NAME, {
                "oat": x['oat'][0],
                "load": x['load'][0]
                })

        # find the Spearman rank
        weather_sensitivity = findSpearmanRank(load_values, oat_values)
        # TODO weather sensitivity as attribute for report generation

        self.out.insert_row(WEATHER_SENSITIVITY_TABLE_NAME, {
            "value": str(weather_sensitivity)
            })

