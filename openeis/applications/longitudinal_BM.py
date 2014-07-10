"""
Longitudinal benchmarking: aggregate electric load and gas usage on a yearly basis.

Shows trends in building performance over time.
"""


from openeis.applications import DriverApplicationBaseClass, InputDescriptor, OutputDescriptor, ConfigDescriptor
import logging
from django.db.models import Sum


class Application(DriverApplicationBaseClass):

    def __init__(self, *args, building_name=None, **kwargs):
        #Called after app has been staged
        """
        When applications extend this base class, they need to make
        use of any kwargs that were setup in config_param
        """
        super().__init__(*args,**kwargs)

        self.default_building_name_used = False

        #match parameters
        if building_name is None:
            building_name = "None supplied"
            self.default_building_name_used = True

        self.building_name = building_name


    @classmethod
    def get_config_parameters(cls):
        #Called by UI
        #also matches parameters
        return {
            "building_name": ConfigDescriptor(str, "Building Name", optional=True)
            }


    @classmethod
    def required_input(cls):
        #Called by UI
        return {
            'load':InputDescriptor('WholeBuildingElectricity','Building Load'),
            'natgas':InputDescriptor('WholeBuildingGas', 'Natural Gas usage')
            }

    @classmethod
    def output_format(cls, input_object):
        # Called when app is staged
        """
        Output is the year with its respective load and natural gas amounts
        aggregated over the year.
        """
        topics = input_object.get_topics()
        load_topic = topics['load'][0]
        load_topic_parts = load_topic.split('/')
        output_topic_base = load_topic_parts[:-1]
        year_topic = '/'.join(output_topic_base+['longitudinalbm', 'time'])
        load_topic = '/'.join(output_topic_base+['longitudinalbm', 'load'])
        gas_topic = '/'.join(output_topic_base+['longitudinalbm', 'natgas'])

        #stuff needed to put inside output, will output by row, each new item
        #is a new file, title must match title in execute when writing to out
        output_needs = {
            'Longitudinal_BM': {
                'year':OutputDescriptor('int', year_topic),
                'load':OutputDescriptor('float', load_topic),
                'natgas':OutputDescriptor('float', gas_topic)
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
        Will output the following: year, aggregated load amounts,
        and aggregated gas amounts.
        """
        self.out.log("Starting analysis", logging.INFO)

        #grabs data by year and reduces it
        load_by_year = self.inp.get_query_sets('load', group_by='year',
                                               group_by_aggregation=Sum,
                                               exclude={'value':None},
                                               wrap_for_merge=True)

        gas_by_year = self.inp.get_query_sets('natgas', group_by='year',
                                              group_by_aggregation=Sum,
                                              exclude={'value':None},
                                              wrap_for_merge=True)

        merge_load_gas = self.inp.merge(load_by_year, gas_by_year)

        for x in merge_load_gas:
            self.out.insert_row("Longitudinal_BM", {
                'year': x['time'],
                'load': x['load'][0],
                'natgas': x['natgas'][0]
                })
