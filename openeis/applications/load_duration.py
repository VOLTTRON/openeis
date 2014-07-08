"""
Load duration: show the proportion of time that the building load is at or above a given level.
"""


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
        return {
            "building_name": ConfigDescriptor(str, "Building Name", optional=True)
            }


    @classmethod
    def required_input(cls):
        #Called by UI
        # Sort out units.
        return {
            'load':InputDescriptor('WholeBuildingElectricity','Building Load')
            }


    @classmethod
    def output_format(cls, input_object):
        # Called when app is staged
        """
        Output is the sorted load to be graphed later.
        """
        #TODO: find an easier way of formatting the topics
        topics = input_object.get_topics()
        load_topic = topics['load'][0]
        load_topic_parts = load_topic.split('/')
        output_topic_base = load_topic_parts[:-1]
        load_topic = '/'.join(output_topic_base+['loadduration','load'])

        output_needs = {
            'Load_Duration': {
                'sorted load':OutputDescriptor('float', load_topic)
                }
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
        """
            Output is sorted loads values.
        """
        self.out.log("Starting load duration", logging.INFO)

        load_query = self.inp.get_query_sets('load', order_by='value', exclude={'value':None})

        for x in load_query[0]:
            self.out.insert_row("Load_Duration", {"sorted load": x[1]})
