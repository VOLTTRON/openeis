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
        output data table that is used, LOAD_PROFILE_TABLE_NAME
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
        ''' Send in the oat and load columns of the Weather_Sensitivity table.'''
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

