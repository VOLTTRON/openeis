"""
Heat map: show electricity use by time-of-day, across many days.

Shows extent of daily, weekly, and seasonal load profiles.
"""


from openeis.applications import DriverApplicationBaseClass, InputDescriptor,  \
    OutputDescriptor, ConfigDescriptor
import logging


class Application(DriverApplicationBaseClass):

    def __init__(self,*args,building_sq_ft=-1, building_name=None,**kwargs):
        #Called after app has been staged
        """
        When applications extend this base class, they need to make
        use of any kwargs that were setup in config_param
        """
        super().__init__(*args,**kwargs)

        self.default_building_name_used = False

        if building_sq_ft < 0:
            raise Exception("Invalid input for building_sq_ft")
        if building_name is None:
            building_name = "None supplied"
            self.default_building_name_used = True

        self.sq_ft = building_sq_ft
        self.building_name = building_name



    @classmethod
    def get_config_parameters(cls):
        #Called by UI
        return {
                    "building_sq_ft": ConfigDescriptor(float, "Square footage", value_min=200),
                    "building_name": ConfigDescriptor(str, "Building Name", optional=True)
                }


    @classmethod
    def required_input(cls):
        #Called by UI
        return {
                    'load':InputDescriptor('WholeBuildingEnergy','Building Load'),
                }

    @classmethod
    def output_format(cls, input_object):
        """
        Output will have the date, hour, and respective load.
        To be graphed in a heat map later.
        """
        #Called when app is staged
        topics = input_object.get_topics()
        load_topic = topics['load'][0]
        load_topic_parts = load_topic.split('/')
        output_topic_base = load_topic_parts[:-1]
        date_topic = '/'.join(output_topic_base+['heatmap', 'date'])
        hour_topic = '/'.join(output_topic_base+['heatmap', 'time'])
        load_topic = '/'.join(output_topic_base+['heatmap', 'load'])
        output_needs =  {'Heat Map':
                            {'date': OutputDescriptor('datetime', date_topic),\
                             'hour': OutputDescriptor('int', hour_topic), \
                             'load': OutputDescriptor('float', load_topic)}
                         }

        return output_needs

    def report(self):
        #Called by UI to create Viz
        """Describe how to present output to user
        Display this viz with these columns from this table

        display_elements is a list of display objects specifying viz and columns
        for that viz
        """
        display_elements = []

        return display_elements

    def execute(self):
        #Called after User hits GO
        #maybe can be combined with dailySummary
        """
        Output values for Heat Map.
        """
        self.out.log("Starting analysis", logging.INFO)

        load_by_hour = self.inp.get_query_sets('load', exclude={'value':None})

        date = []
        load_vals = []

        for x in load_by_hour[0]:
            # TODO: The following two lines were removed, but in a commit (7dd5f36) that
            # was not, apparently, about removing them.  Verify that these should
            # be removed.  If so, then also remove the list creation steps that happen
            # right above this loop.
            # date.append(x[0])
            # load_vals.append(x[1])
            self.out.insert_row("Heat Map",\
                                {'date': x[0].date(),
                                 'hour': x[0].hour,
                                 'load': x[1]})



