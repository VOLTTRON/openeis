"""
Heat map: show electricity use by time-of-day, across many days.

Shows extent of daily, weekly, and seasonal load profiles.
"""

from openeis.applications import reports
from openeis.applications import DriverApplicationBaseClass, InputDescriptor,  \
    OutputDescriptor, ConfigDescriptor
import logging


class Application(DriverApplicationBaseClass):

    def __init__(self, *args, building_name=None, **kwargs):
        #Called after app has been staged
        """
        When applications extend this base class, they need to make
        use of any kwargs that were setup in config_param
        """
        super().__init__(*args,**kwargs)

        self.default_building_name_used = False

        if building_name is None:
            building_name = "None supplied"
            self.default_building_name_used = True

        self.building_name = building_name


    @classmethod
    def get_config_parameters(cls):
        #Called by UI
        
        values = []
        values.append("ISB1")
        values.append("ISB2")
        
        return {
            "building_name": ConfigDescriptor(str, "Building Name", optional=True,value_list=values)
            }

    @classmethod
    def required_input(cls):
        #Called by UI
        return {
            'load':InputDescriptor('WholeBuildingElectricity','Building Load'),
            }


    @classmethod
    def output_format(cls, input_object):
        # Called when app is staged
        """
        Output will have the date, hour, and respective load.
        To be graphed in a heat map later.
        """
        topics = input_object.get_topics()
        load_topic = topics['load'][0]
        load_topic_parts = load_topic.split('/')
        output_topic_base = load_topic_parts[:-1]
        date_topic = '/'.join(output_topic_base+['heatmap', 'date'])
        hour_topic = '/'.join(output_topic_base+['heatmap', 'time'])
        load_topic = '/'.join(output_topic_base+['heatmap', 'load'])
        output_needs = {
            'Heat_Map': {
                'date': OutputDescriptor('string', date_topic),
                'hour': OutputDescriptor('integer', hour_topic),
                'load': OutputDescriptor('float', load_topic)
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
        
        report = reports.Report('Heat Map for Load')
        
        heat_map = reports.HeatMap(table_name='Heat_Map', x_column='hour', y_column='date', z_column='load')
        report.add_element(heat_map)

        report_list = [report]

        return report_list

    def execute(self):
        #Called after User hits GO
        #maybe can be combined with dailySummary
        """
        Output values for Heat Map.
        """
        self.out.log("Starting analysis", logging.INFO)

        loads = self.inp.get_query_sets('load', exclude={'value':None})
        for x in loads[0]:
            self.out.insert_row("Heat_Map", {
                'date': x[0].date(),
                'hour': x[0].hour,
                'load': x[1]
                }
            )
            print(x[0].date(), x[0].hour, x[1])
            