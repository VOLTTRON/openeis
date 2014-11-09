"""
Daily summary: find daily metrics for electrical loads.

Calculates the following metrics:
    - Load Max Intensity
    - Load Min Intensity
    - Daily Load 95th Percentile
    - Daily Load 5th Percentile
    - Daily Load Ratio
    - Daily Load Range
    - Load Variability
    - Peak Load Benchmark


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
    OutputDescriptor, ConfigDescriptor, ApplicationDescriptor
from openeis.applications import reports
import logging
import numpy
import math
from django.db.models import Max, Min, Avg
from dateutil.relativedelta import relativedelta
from openeis.applications.utils import conversion_utils as cu


class Application(DriverApplicationBaseClass):

    def __init__(self, *args, building_sq_ft=-1, building_name=None, **kwargs):
        # Called after app has been staged
        """
        When applications extend this base class, they need to make
        use of any kwargs that were setup in config_param
        """
        super().__init__(*args, **kwargs)

        self.default_building_name_used = False

        if building_sq_ft <= 0:
            raise Exception("Building floor area must be positive")
        if building_name is None:
            building_name = "None supplied"
            self.default_building_name_used = True

        self.sq_ft = building_sq_ft
        self.building_name = building_name

    @classmethod
    def get_app_descriptor(cls):    
        name = 'Daily Summary'
        desc = 'Daily summary is a collection of metrics that summarize the daily energy use.\
                Metrics included in the application are load variability, load minimum and maximum,\
                peak load benchmark, daily load ratio, and daily load range.'
        return ApplicationDescriptor(app_name=name, description=desc)
        
    @classmethod
    def get_config_parameters(cls):
        # Called by UI
        return {
            "building_sq_ft": ConfigDescriptor(float, "Square footage", value_min=200),
            "building_name": ConfigDescriptor(str, "Building Name", optional=True)
            }

    @classmethod
    def required_input(cls):
        # Called by UI
        # Sort out units.
        return {
            'load':InputDescriptor('WholeBuildingElectricity', 'Building Load')
            }

    @classmethod
    def output_format(cls, input_object):
        # Called when app is staged
        """
        Output will be the metric followed by the value of respective metric.
        """
        topics = input_object.get_topics()
        load_topic = topics['load'][0]
        load_topic_parts = load_topic.split('/')
        output_topic_base = load_topic_parts[:-1]
        metricname_topic = '/'.join(output_topic_base + ['dailySummary','metricname'])
        value_topic = '/'.join(output_topic_base + ['dailySummary', 'value'])
        description_topic = '/'.join(output_topic_base + ['dailySummary', 'description'])

        output_needs = {
            'Daily_Summary_Table': {
                'Metric':OutputDescriptor('string', metricname_topic),
                'value':OutputDescriptor('string', value_topic),
                'description':OutputDescriptor('string', description_topic)
                }
            }
        return output_needs

    @classmethod
    def reports(cls, output_object):
        # Called by UI to create Viz
        """Describe how to present output to user
        Display this viz with these columns from this table

        display_elements is a list of display objects specifying viz and
        columns for that viz
        """

        # text blurb
        # table

        rep_desc = 'Daily Summary Report'

        report = reports.Report(rep_desc)

        column_info = (('Metric', 'Summary Metrics'), ('value', 'Summary Values'),('description','Guide'))

#         text_blurb = reports.TextBlurb('')
        summary_table = reports.Table('Daily_Summary_Table',
                                      column_info,
                                      title='Load Summary Metrics',
                                      description='A table showing the calculated building performance metrics')


        report.add_element(summary_table)

        # list of report objects

        report_list = [report]

        return report_list

    def execute(self):
        # Called after User hits GO
        """
        Calculates the following metrics and outputs.
            -Daily Load 95th Percentile
            -Daily Load 5th Percentile
            -Daily Load Ratio
            -Daily Load Range
            -Load Variability
            -Peak Load Benchmark
        """

        self.out.log("Starting application: daily summary.", logging.INFO)

        self.out.log("Querying database.", logging.INFO)
        peakLoad = self.inp.get_query_sets('load', group_by='all',
                                           group_by_aggregation=Max)[0]
        load_query = self.inp.get_query_sets('load', exclude={'value':None})[0]

        load_startDay = load_query.earliest()[0].date()
        load_endDay = load_query.latest()[0].date()
        current_Day = load_startDay
        load_day_list_95 = []
        load_day_list_5 = []

        self.out.log("Getting unit conversions.", logging.INFO)
        base_topic = self.inp.get_topics()
        meta_topics = self.inp.get_topics_meta()

        load_unit = meta_topics['load'][base_topic['load'][0]]['unit']
        self.out.log(
            "Convert loads from [{}] to [kW].".format(load_unit),
            logging.INFO
            )
        load_convertfactor = cu.getFactor_powertoKW(load_unit)

        self.out.log("Calculating peak benchmark metric.", logging.INFO)
        floorAreaSqft = self.sq_ft
        peakLoadIntensity = peakLoad / floorAreaSqft

        self.out.log("Calculating daily top and bottom percentile.", logging.INFO)
        while current_Day <= load_endDay:
            load_day_query = load_query.filter(time__year=current_Day.year,
                                            time__month=current_Day.month,
                                            time__day=current_Day.day)
            current_Day += relativedelta(days=1)

            load_day_values = [x[1] for x in load_day_query]
            if (len(load_day_values) < 5):
                continue

            load_day_list_95.append(numpy.percentile(load_day_values, 95))
            load_day_list_5.append(numpy.percentile(load_day_values, 5))

        # average them
        load_day_95_mean = numpy.mean(load_day_list_95)
        load_day_5_mean = numpy.mean(load_day_list_5)
        load_day_ratio_mean = numpy.mean(numpy.divide(load_day_list_5,
                                                      load_day_list_95))
        load_day_range_mean = numpy.mean(numpy.subtract(load_day_list_95,
                                                        load_day_list_5))

        self.out.log("Calculating load variability.", logging.INFO)
        # TODO: Generate error if there are not 24 hours worth of data for
        # every day and less than two days of data.
        hourly_variability = []

        for h in range(24):
            hourly_mean = self.inp.get_query_sets('load', group_by='all',
                                                  group_by_aggregation=Avg,
                                                  filter_={'time__hour':h})[0]
            hour_load_query = self.inp.get_query_sets('load',
                                                     filter_={'time__hour':h},
                                                     exclude={'value':None})[0]
            counts = hour_load_query.count()
            if (counts < 2):
                raise Exception("Must have more than 1 day of data!")
            rootmeansq = math.sqrt(
                sum((x[1] - hourly_mean) ** 2 for x in hour_load_query)
                / (counts - 1)
                )
            hourly_variability.append(rootmeansq / hourly_mean)

        load_variability = numpy.mean(hourly_variability)

        self.out.log("Compiling the report table.", logging.INFO)
        self.out.insert_row("Daily_Summary_Table", {
            "Metric": "Peak Load Benchmark [W/sf]",
            "value": "{:.2f}".format(peakLoadIntensity * load_convertfactor * 1000.),
            "description": "This is the absolute maximum electric load based on all of your data. "  \
                "The median for commercial buildings under 150,000 sf is 4.4 W/sf. "  \
                "Values much higher than 4.4 therefore indicate an opportunity to improve building performance."
            })
        self.out.insert_row("Daily_Summary_Table", {
            "Metric": "Daily Load 95th Percentile [kW]",
            "value": "{:.2f}".format(load_day_95_mean * load_convertfactor),
            "description": "The daily maximum usage could be dominated by a single large load, or "  \
                "could be the sum of several smaller ones. "  \
                "Long periods of usage near the maximum increase overall energy use."
            })
        self.out.insert_row("Daily_Summary_Table", {
            "Metric": "Daily Load 5th Percentile [kW]",
            "value": "{:.2f}".format(load_day_5_mean * load_convertfactor),
            "description": "Minimum usage is often dominated by loads that run 24 hours a day. "  \
                "In homes, these include refrigerators and vampire loads. "  \
                "In commercial buildings, these include ventilation, hallway lighting, computers, and vampire loads."
            })
        self.out.insert_row("Daily_Summary_Table", {
            "Metric": "Daily Load Range [kW]",
            "value": "{:.2f}".format(load_day_range_mean * load_convertfactor),
            "description": "This is a rough estimate of the total load turned on and off every day. "  \
                "Higher values may indicate good control, but could also indicate excessive peak usage."
            })
        self.out.insert_row("Daily_Summary_Table", {
            "Metric": "Daily Load Ratio",
            "value": "{:.2f}".format(load_day_ratio_mean),
            "description": "Values over 0.33 indicate that significant loads are shut off for parts of the day. "  \
                "To save energy, look to extend and deepen shutoff periods, while also reducing peak energy use."
            })
        self.out.insert_row("Daily_Summary_Table", {
            "Metric": "Load Variability",
            "value": "{:.2f}".format(load_variability),
            "description":"This metric is used to understand regularity of operations, "  \
                "and the likelihood of consistency in the building's demand responsiveness. "  \
                "It gives a coefficient of variation that ranges from 0 to 1. "  \
                "This coefficient can be interpreted based on general guidelines. "  \
                "For example, variability above 0.15 is generally considered high for commercial buildings."
            })
