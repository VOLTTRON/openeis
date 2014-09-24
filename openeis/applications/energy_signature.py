"""
Energy signature: plot power as a function of outside temperature.

Shows the sensitivity of building electrical energy use to weather.

Includes a weather sensitivity metric.

Copyright (c) 2014, The Regents of the University of California, Department
of Energy contract-operators of the Lawrence Berkeley National Laboratory.
All rights reserved.

1. Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions are met:

   (a) Redistributions of source code must retain the copyright notice, this
   list of conditions and the following disclaimer.

   (b) Redistributions in binary form must reproduce the copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

   (c) Neither the name of the University of California, Lawrence Berkeley
   National Laboratory, U.S. Dept. of Energy nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

2. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
   AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
   DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
   ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
   (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
   LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
   ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
   (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
   THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

3. You are under no obligation whatsoever to provide any bug fixes, patches,
   or upgrades to the features, functionality or performance of the source code
   ("Enhancements") to anyone; however, if you choose to make your Enhancements
   available either publicly, or directly to Lawrence Berkeley National
   Laboratory, without imposing a separate written license agreement for such
   Enhancements, then you hereby grant the following license: a non-exclusive,
   royalty-free perpetual license to install, use, modify, prepare derivative
   works, incorporate into other computer software, distribute, and sublicense
   such enhancements or derivative works thereof, in binary and source code
   form.

NOTE: This license corresponds to the "revised BSD" or "3-clause BSD" license
and includes the following modification: Paragraph 3. has been added.
"""


from openeis.applications import DriverApplicationBaseClass, InputDescriptor, \
    OutputDescriptor, ConfigDescriptor
from openeis.applications import reports
import logging
from django.db.models import Avg
from .utils.spearman import findSpearmanRank
from .utils import conversion_utils as cu


class Application(DriverApplicationBaseClass):

    def __init__(self, *args, building_name=None, **kwargs):
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
        return {
            "building_name": ConfigDescriptor(str, "Building Name", optional=True)
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
            'Weather_Sensitivity': {
                'value':OutputDescriptor('string', value_topic)
                },
            'Scatterplot': {
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

        report = reports.Report('Energy Signature Report')

        column_info = (('value', 'Sensitivity'),)

        text_blurb = reports.TextBlurb("Analysis of the relationship of power intensity to outdoor temperature.")
        report.add_element(text_blurb)
        summary_table = reports.Table('Weather_Sensitivity',
                                      column_info,
                                      title='Weather Sensitivity',
                                      description='A description of the sensitivity')

        report.add_element(summary_table)

        text_guide1 = reports.TextBlurb(text="If weather sensitivity > 0.7 the building energy use\
                                            is \"highly\" sensitive to outside air temperature. \
                                            There may be opportunities to improve building insulation \
                                            and ventilation.")
        report.add_element(text_guide1)

        xy_dataset_list = []
        xy_dataset_list.append(reports.XYDataSet('Scatterplot', 'oat', 'load'))

        scatter_plot = reports.ScatterPlot(xy_dataset_list,
                                           title='Time Series Load Profile',
                                           x_label='Outside Air Temperature [F]',
                                           y_label='Energy [kWh]')

        report.add_element(scatter_plot)
        
        text_guide2 = reports.TextBlurb(text="The lack of any pattern may indicate \
                                               your building is not sensitive to outdoor\
                                               temperature.")
        report.add_element(text_guide2)        
        
        text_guide3 = reports.TextBlurb(text="A steep slope indicates high sensitivity to outdoor temperature.")
        report.add_element(text_guide3)     

        text_guide4 = reports.TextBlurb(text="The balance point is the temperature at which the \
                                              building does not require any heating or cooling.")
        report.add_element(text_guide4)  
        

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

        # Get conversion factor
        base_topic = self.inp.get_topics()
        meta_topics = self.inp.get_topics_meta()
        load_unit = meta_topics['load'][base_topic['load'][0]]['unit']
        temperature_unit = meta_topics['oat'][base_topic['oat'][0]]['unit']
        
        load_convertfactor = cu.conversiontoKWH(load_unit)
        
        merged_load_oat = self.inp.merge(load_query, oat_query)

        load_values = []
        oat_values = []

        # Output for scatter plot
        for x in merged_load_oat:
            if temperature_unit == 'celcius':
                convertedTemp = cu.convertCelciusToFahrenheit(x['oat'][0])
            elif temperature_unit == 'kelvin':
                convertedTemp = cu.convertKelvinToCelcius(
                                cu.convertCelciusToFahrenheit(x['oat'][0]))
            else: 
                convertedTemp = x['oat'][0]
        
            load_values.append(x['load'][0]*load_convertfactor)
            oat_values.append(convertedTemp)
            self.out.insert_row("Scatterplot", {
                "oat": x['oat'][0],
                "load": x['load'][0]
                })

        # find the Spearman rank
        weather_sensitivity = findSpearmanRank(load_values, oat_values)
        # TODO weather sensitivity as attribute for report generation

        self.out.insert_row("Weather_Sensitivity", {
            "value": "{:.2f}".format(weather_sensitivity)
            })
