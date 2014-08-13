"""
Load profile: show building loads over time.
"""


from openeis.applications import DriverApplicationBaseClass, InputDescriptor,  \
    OutputDescriptor, ConfigDescriptor
from openeis.applications import reports
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
        return {
            "building_name": ConfigDescriptor(str, "Building Name", optional=True)
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
        Output is hour with respective load, to be put in a line graph later.
        """
        topics = input_object.get_topics()
        load_topic = topics['load'][0]
        load_topic_parts = load_topic.split('/')
        output_topic_base = load_topic_parts[: -1]
        time_topic = '/'.join(output_topic_base+['timeseries', 'time'])
        load_topic = '/'.join(output_topic_base+['timeseries', 'load'])

        # Work with topics["OAT"][0] to get building topic
        output_needs = {
            'Load_Profiling': {
                'timestamp':OutputDescriptor('datetime', time_topic),
                'load':OutputDescriptor('float', load_topic)
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
        report = reports.Report('Building Load Profile Report')

        text_blurb = reports.TextBlurb(text="A plot showing building energy consumption over a time period.")
        report.add_element(text_blurb)
        
        xy_dataset_list = []
        xy_dataset_list.append(reports.XYDataSet('Scatterplot', 'timestamp', 'load'))

        scatter_plot = reports.ScatterPlot(xy_dataset_list,
                                           title='Time Series Load Profile',
                                           x_label='Timestamp', 
                                           y_label='Power'
                                           )

        report.add_element(scatter_plot)

        report_list = [report]

        return report_list

    def execute(self):
        #Called after User hits GO
        "Outputs values for line graph."
        self.out.log("Starting analysis", logging.INFO)

        load_by_hour = self.inp.get_query_sets('load', exclude={'value': None})

        for x in load_by_hour[0]:
            self.out.insert_row("Load_Profiling", {
                'timestamp': x[0],
                'load': x[1]
                })
