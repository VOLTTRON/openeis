"""
Cross-sectional benchmarking: retrieve an ENERGY STAR score from EPA's Target Finder.

Shows the building performance relative to a comparable peer group.
"""


from openeis.applications import DriverApplicationBaseClass, InputDescriptor,  \
    OutputDescriptor, ConfigDescriptor
import logging
from django.db.models import Sum
from .utils.gen_xml_tgtfndr import gen_xml_targetFinder
from .utils.retrieveEnergyStarScore_tgtfndr import retrieveScore


class Application(DriverApplicationBaseClass):

    def __init__(self, *args,
                    building_sq_ft=-1,
                    building_year_constructed=-1,
                    building_name=None,
                    building_function='Office',
                    building_zipcode=None,
                    **kwargs):
        #Called after app has been staged
        """
        When applications extend this base class, they need to make
        use of any kwargs that were setup in config_param
        """
        super().__init__(*args,**kwargs)

        self.default_building_name_used = False

        if building_sq_ft <= 0:
            raise Exception("Building floor area must be positive")
        if building_year_constructed < 0:
            raise Exception("Invalid input for building_year_constructed")
        if building_name is None:
            building_name = "None supplied"
            self.default_building_name_used = True
        if len(building_zipcode) < 5:
            raise Exception("Invalid input for building_zipcode")

        self.sq_ft = building_sq_ft
        self.building_year = building_year_constructed
        self.building_name = building_name
        #TODO: Provide list of Portfolio Manager valid building types.
        self.building_function = building_function
        self.building_zipcode = building_zipcode


    @classmethod
    def get_config_parameters(cls):
        #Called by UI
        return {
            "building_sq_ft": ConfigDescriptor(float, "Square footage", value_min=5000),
            "building_year_constructed": ConfigDescriptor(int, "Construction Year", value_min=1800, value_max=2014),
            "building_name": ConfigDescriptor(str, "Building Name", optional=True),
            "building_function": ConfigDescriptor(str, "Building Function", optional=True),
            "building_zipcode": ConfigDescriptor(str, "Building Zipcode")
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
        metric_name_topic = '/'.join(output_topic_base+['crossection', 'metric_name'])
        value_topic = '/'.join(output_topic_base+['crossection', 'value'])

        output_needs = {
            'CrossSectionalBM': {
                'Metric Name':OutputDescriptor('string', metric_name_topic),
                'Value':OutputDescriptor('string', value_topic)
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
        display_elements = []

        return display_elements

    def execute(self):
        #Called after User hits GO
        """
        Will output the following: year, aggregated load amounts,
        and aggregated gas amounts.
        """
        #NOTE: Connection check happens after data is formatted into XML and
        # sent into the web service request.
        self.out.log("Starting analysis", logging.INFO)

        bldgMetaData = dict()
        bldgMetaData['floor-area']  = self.sq_ft
        bldgMetaData['year-built']  = self.building_year
        bldgMetaData['bldg-name']   = self.building_name
        bldgMetaData['function']    = self.building_function
        bldgMetaData['zipcode']     = self.building_zipcode

        load_by_year = self.inp.get_query_sets('load', group_by='year',
                                               group_by_aggregation=Sum,
                                               exclude={'value':None},
                                               wrap_for_merge=True)
        gas_by_year = self.inp.get_query_sets('natgas', group_by='year',
                                              group_by_aggregation=Sum,
                                              exclude={'value':None},
                                              wrap_for_merge=True)

        merge_load_gas = self.inp.merge(load_by_year, gas_by_year)

        # Convert the generator to a list that can be indexed.
        merge_data_list = []
        for item in merge_load_gas:
            merge_data_list.append((item['time'], item['load'][0], item['natgas'][0]))

        recent_record = merge_data_list[len(merge_data_list)-1]

        #TODO: Get units from sensor maps.
        #TODO: Convert values to units that are PM Manager values.
        energyUseList = [['Electric','kWh (thousand Watt-hours)',int(recent_record[1])],
                         ['Natural Gas','kBtu (thousand Btu)',int(recent_record[2])]]

        # Generate XML-formatted data to pass data to the webservice.
        targetFinder_xml = gen_xml_targetFinder(bldgMetaData,energyUseList,'z_targetFinder_xml')
        # Function that does a URL Request with ENERGY STAR web server.
        PMMetrics = retrieveScore(targetFinder_xml)

        if PMMetrics == None:
            errmessage = 'Network connection needed to run application.'
            self.out.log(errmessage, logging.WARNING)
        else:
            self.out.log('Analysis successful', logging.INFO)
            self.out.insert_row('CrossSectionalBM', {
                'Metric Name': 'Year',
                'Value': recent_record[0]
                })
            self.out.insert_row('CrossSectionalBM', {
                'Metric Name': 'Target Finder Median Score',
                'Value': str(PMMetrics['medianScore'][0])
                })
            self.out.insert_row('CrossSectionalBM', {
                'Metric Name': 'Target Finder Score',
                'Value': str(PMMetrics['designScore'][0])
                })
