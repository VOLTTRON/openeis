from openeis.applications import DriverApplicationBaseClass, InputDescriptor, OutputDescriptor, ConfigDescriptor
import logging

table_name = '{input_group}'
output_topic = '{input_topic}'
class Application(DriverApplicationBaseClass):
    """
    Test application for verifying application API
    """



    def __init__(self,*args, building_sq_ft=-1, building_year_constructed=-1, building_name=None,**kwargs):
        #Called after app has been staged
        """
        When applications extend this base class, they need to make
        use of any kwargs that were setup in config_param
        """
        super().__init__(*args,**kwargs)

        self.default_building_name_used = False

        if building_sq_ft < 0:
            raise Exception("Invalid input for building_sq_ft")
        if building_year_constructed < 0:
            raise Exception("Invalid input for building_sq_ft")
        if building_name is None:
            building_name = "None supplied"
            self.default_building_name_used = True

        self.sq_ft = building_sq_ft
        self.building_year = building_year_constructed
        self.building_name = building_name



    @classmethod
    def get_config_parameters(cls):
        #Called by UI
        return {
                    "building_sq_ft": ConfigDescriptor(float, "Square footage", value_min=200),
                    "building_year_constructed": ConfigDescriptor(int, "Consruction Year", value_min=1800, value_max=2014),
                    "building_name": ConfigDescriptor(str, "Building Name", optional=True)

                }


    @classmethod
    def required_input(cls):
        #Called by UI
        return {
                    'OAT':InputDescriptor('OutdoorAirTemperature','Outdoor Temp', count_max=None),
                    'load':InputDescriptor('WholeBuildingEnergy','Building Load'),
                    'natgas':InputDescriptor('NaturalGas','Natural Gas usage')
                }

    @classmethod
    def output_format(cls, input_object):
        #Called when app is staged
        topic_map = input_object.get_topics()
        # Work with topics["OAT"][0] to get building topic
#         descriptor_column = 'site/building/analysis/description'
        output_needs = {}

        #Table per topic, regardless of group
        for group in topic_map:
            for topic in topic_map[group]:
                table = table_name.format(input_group= topic.replace('/','_'))
                output_needs[table] = {}
                output_needs[table]['Time']=OutputDescriptor('timestamp', output_topic.format(input_topic='Time'))
                output_needs[table][topic] = OutputDescriptor('String', output_topic.format(input_topic=topic))

#tables for groups

#         for group in topic_map:
#             table = table_name.format(input_group= group)
#             output_needs[table] = {}
#             for topic in topic_map[group]:
#                 outputle_needs[output_needs[table]][topic] = OutputDescriptor('String', output_topic.format(input_topic=topic))
#
        return output_needs

    def report(self):
        #Called by UI to create Viz
        """Describe how to present output to user
        Display this viz with these columns from this table


        display elements is a list of display objects specifying viz and columns for that viz
        """
        display_elements = []

        return display_elements

    def execute(self):
        #Called after User hits GO
        print("Do stuff")
        self.out.log("Starting analysis", logging.INFO)
#         #Go through some data
#         data_start, data_end = self.inp.get_start_end_times()
#
#         #A year ago ignoring time info
#         year_ago = (data_end - relativedelta(year=1)).replace(hour=0,minute=0,second=0)
#
#         #A month ago ignoring time info
#         month_ago = (data_end - relativedelta(month=1)).replace(hour=0,minute=0,second=0)
#
#         #
#         oat_qs = self.inp.get_query_sets('OAT')
#         load_qs = self.inp.get_query_sets('OAT')
#         gas_qs = self.inp.get_query_sets('OAT')

        groupnames = self.inp.get_topics()

        for groupname in groupnames:
            self.parrot_group(groupname)


    def parrot_group(self, groupname):
        """
        Take a group name, and output all the topics to their own tables... theoretically
        """
        querysets = self.inp.get_query_sets(groupname)
        group_topics = self.inp.get_topics()[groupname]
        i = 0
        for iterator in querysets:
            for x in iterator:
                time, reading = x
                self.out.insert_row(table_name.format(input_group= group_topics[i].replace('/','_')), {output_topic.format(input_topic='Time'):time,
                                                                                       output_topic.format(input_topic=group_topics[i]):reading})
            i +=1



