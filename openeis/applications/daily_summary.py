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
"""


from openeis.applications import DriverApplicationBaseClass, InputDescriptor, \
    OutputDescriptor, ConfigDescriptor
from openeis.applications import reports
import logging
import numpy
import math
from django.db.models import Max, Min, Avg
from dateutil.relativedelta import relativedelta


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
        description_topic = '/'.join(output_topic_base + ['dailySummary',
                                                        'description'])
        value_topic = '/'.join(output_topic_base + ['dailySummary', 'value'])
        output_needs = {
            'Daily_Summary_Table': {
                'Metric':OutputDescriptor('string', description_topic),
                'value':OutputDescriptor('string', value_topic)
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

        column_info = (('Metric', 'Summary Metrics'), ('value', 'Summary Values'))

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
            -Load Max Intensity
            -Load Min Intensity
            -Daily Load 95th Percentile
            -Daily Load 5th Percentile
            -Daily Load Ratio
            -Daily Load Range
            -Load Variability
            -Peak Load Benchmark
        """

        self.out.log("Starting daily summary", logging.INFO)

        floorAreaSqft = self.sq_ft
        load_max = self.inp.get_query_sets('load', group_by='all',
                                           group_by_aggregation=Max)[0]
        load_min = self.inp.get_query_sets('load', group_by='all',
                                           group_by_aggregation=Min)[0]
        load_query = self.inp.get_query_sets('load', exclude={'value':None})[0]

        # TODO: Time Zone support
        load_startDay = load_query.earliest()[0].date()
        load_endDay = load_query.latest()[0].date()
        current_Day = load_startDay
        load_day_list_95 = []
        load_day_list_5 = []

        # find peak load benchmark
        peakLoad = load_max * 1000
        peakLoadIntensity = peakLoad / floorAreaSqft

        # gather values in the 95th and 5th percentile every day
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

        # find the load variability
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


        self.out.insert_row("Daily_Summary_Table", {
            "Metric": "Load Max Intensity",
            "value": str(load_max / floorAreaSqft)
            })
        self.out.insert_row("Daily_Summary_Table", {
            "Metric": "Load Min Intensity",
            "value": str(load_min / floorAreaSqft)
            })
        self.out.insert_row("Daily_Summary_Table", {
            "Metric": "Daily Load 95th Percentile",
            "value": str(load_day_95_mean)
            })
        self.out.insert_row("Daily_Summary_Table", {
            "Metric": "Daily Load 5th Percentile",
            "value": str(load_day_5_mean)
            })
        self.out.insert_row("Daily_Summary_Table", {
            "Metric": "Daily Load Ratio",
            "value": str(load_day_ratio_mean)
            })
        self.out.insert_row("Daily_Summary_Table", {
            "Metric": "Daily Load Range",
            "value": str(load_day_range_mean)
            })
        self.out.insert_row("Daily_Summary_Table", {
            "Metric": "Load Variability",
            "value": str(load_variability)
            })
        self.out.insert_row("Daily_Summary_Table", {
            "Metric": "Peak Load Benchmark",
            "value": str(peakLoadIntensity)
            })

