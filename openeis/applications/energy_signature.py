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


    def report(self):
        # Called by UI to create Viz
        """Describe how to present output to user
        Display this viz with these columns from this table

        display_elements is a list of display objects specifying viz and columns
        for that viz
        """

        report = reports.Report('Energy Signature Report')

        column_info = (('value', 'Sensitivity'),)

#         text_blurb = reports.TextBlurb('')
        summary_table = reports.Table('Weather_Sensitivity',
                                      column_info,
                                      title='Weather Sensitivity',
                                      desc='A description of the sensitivity')

        report.add_element(summary_table)


        xy_dataset_list = []
        xy_dataset_list.append(reports.XYDataSet('Scatterplot', 'oat', 'load'))

        scatter_plot = reports.ScatterPlot(xy_dataset_list,
                                           title='Time Series Load Profile',
                                           x_label='Outside Air Temperature', y_label='Power')

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
            self.out.insert_row("Scatterplot", {
                "oat": x['oat'][0],
                "load": x['load'][0]
                })

        # find the Spearman rank
        weather_sensitivity = findSpearmanRank(load_values, oat_values)
        # TODO weather sensitivity as attribute for report generation

        self.out.insert_row("Weather_Sensitivity", {
            "value": str(weather_sensitivity)
            })

        print(self.report()[0])
