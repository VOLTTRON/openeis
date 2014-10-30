"""
Energy signature: plot power as a function of outside temperature.

Shows the sensitivity of building electrical energy use to weather.

Includes a weather sensitivity metric.


Copyright
=========

OpenEIS Algorithms Phase 2 Copyright (c) 2014,
The Regents of the University of California, through Lawrence Berkeley National
Laboratory (subject to receipt of any required approvals from the U.S.
Department of Energy). All rights reserved.

If you have questions about your rights to use or distribute this software,
please contact Berkeley Lab's Technology Transfer Department at TTD@lbl.gov
referring to "OpenEIS Algorithms Phase 2 (LBNL Ref 2014-168)".

NOTICE:  This software was produced by The Regents of the University of
California under Contract No. DE-AC02-05CH11231 with the Department of Energy.
For 5 years from November 1, 2012, the Government is granted for itself and
others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide
license in this data to reproduce, prepare derivative works, and perform
publicly and display publicly, by or on behalf of the Government. There is
provision for the possible extension of the term of this license. Subsequent to
that period or any extension granted, the Government is granted for itself and
others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide
license in this data to reproduce, prepare derivative works, distribute copies
to the public, perform publicly and display publicly, and to permit others to
do so. The specific term of the license can be identified by inquiry made to
Lawrence Berkeley National Laboratory or DOE. Neither the United States nor the
United States Department of Energy, nor any of their employees, makes any
warranty, express or implied, or assumes any legal liability or responsibility
for the accuracy, completeness, or usefulness of any data, apparatus, product,
or process disclosed, or represents that its use would not infringe privately
owned rights.


License
=======

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
from openeis.applications.utils.spearman import findSpearmanRank
from openeis.applications.utils import conversion_utils as cu


WEATHER_SENSITIVITY_TABLE_NAME = 'Weather_Sensitivity'
LOAD_VS_OAT_TABLE_NAME = 'Load_vs_Oat'


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
    def get_app_descriptor(cls):    
        name = 'Energy Signature and Weather Sensitivity'
        desc = 'Energy signatures are used to monitor and maintain\
                the performance of temperature-dependent loads such as\
                whole-building electric or gas use, or heating and cooling systems\
                or components.\n\
                Weather sensitivity is a single summary statistic\
                that contextualizes the shape of the energy signature.'
        return ApplicationDescriptor(app_name=name, description=desc)
        
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
        weather_topic = '/'.join(output_topic_base + ['energysignature', 'weather sensitivity'])
        oat_topic = '/'.join(output_topic_base + ['energysignature', 'oat'])
        load_topic = '/'.join(output_topic_base + ['energysignature', 'load'])

        output_needs = {
            WEATHER_SENSITIVITY_TABLE_NAME: {
                'value':OutputDescriptor('string', weather_topic)
                },
            LOAD_VS_OAT_TABLE_NAME: {
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

        reportName = 'Energy Signature and Weather Sensitivity Report'
        report = reports.Report(reportName)

        text_blurb = reports.TextBlurb("Analysis of the relationship of power intensity to outdoor temperature.")
        report.add_element(text_blurb)

        column_info = (('value', 'Sensitivity'),)  # TODO: Does that stray comma need to be there?
        summary_table = reports.Table(
            WEATHER_SENSITIVITY_TABLE_NAME,
            column_info,
            title='Weather Sensitivity',
            description='A description of the sensitivity'
            )
        report.add_element(summary_table)

        text_guide1 = reports.TextBlurb(
            text="If weather sensitivity > 0.7 the building energy use is \"highly\" sensitive "  \
                "to outside air temperature. There may be opportunities to improve building insulation and ventilation."
            )
        report.add_element(text_guide1)

        xy_dataset_list = []
        xy_dataset_list.append(
            reports.XYDataSet(LOAD_VS_OAT_TABLE_NAME, 'oat', 'load')
            )
        scatter_plot = reports.ScatterPlot(
            xy_dataset_list,
            title='Energy Signature',
            x_label='Outside Air Temperature [F]',
            y_label='Energy [kWh]'
            )
        report.add_element(scatter_plot)

        text_guide2 = reports.TextBlurb(
            text="The lack of any pattern may indicate your building is not sensitive to outdoor temperature."
            )
        report.add_element(text_guide2)

        text_guide3 = reports.TextBlurb(text="A steep slope indicates high sensitivity to outdoor temperature.")
        report.add_element(text_guide3)

        text_guide4 = reports.TextBlurb(
            text="The balance point is the temperature at which the building does not require any heating or cooling."
            )
        report.add_element(text_guide4)

        report_list = [report]

        return report_list


    def execute(self):
        """
        Calculates weather sensitivity using Spearman rank.
        Also, outputs data points for energy signature scatter plot.
        """

        self.out.log("Starting application: energy signature.", logging.INFO)

        self.out.log("Querying database.", logging.INFO)
        load_query = self.inp.get_query_sets('load', group_by='hour',
                                             group_by_aggregation=Avg,
                                             exclude={'value':None},
                                             wrap_for_merge=True)
        oat_query = self.inp.get_query_sets('oat', group_by='hour',
                                             group_by_aggregation=Avg,
                                             exclude={'value':None},
                                             wrap_for_merge=True)

        self.out.log("Getting unit conversions.", logging.INFO)
        base_topic = self.inp.get_topics()
        meta_topics = self.inp.get_topics_meta()

        load_unit = meta_topics['load'][base_topic['load'][0]]['unit']
        self.out.log(
            "Convert loads from [{}] to [kW].".format(load_unit),
            logging.INFO
            )
        load_convertfactor = cu.getFactor_powertoKW(load_unit)

        temperature_unit = meta_topics['oat'][base_topic['oat'][0]]['unit']
        self.out.log(
            "Convert temperatures from [{}] to [F].".format(temperature_unit),
            logging.INFO
            )

        load_values = []
        oat_values = []

        self.out.log("Pulling data from database.", logging.INFO)
        merged_load_oat = self.inp.merge(load_query, oat_query)
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
            self.out.insert_row(LOAD_VS_OAT_TABLE_NAME, {
                "oat": x['oat'][0],
                "load": x['load'][0]
                })

        self.out.log("Calculating the Spearman rank.", logging.INFO)
        weather_sensitivity = findSpearmanRank(load_values, oat_values)

        self.out.log("Adding weather sensitivity to table.", logging.INFO)
        self.out.insert_row(WEATHER_SENSITIVITY_TABLE_NAME, {
            "value": "{:.2f}".format(weather_sensitivity)
            })
