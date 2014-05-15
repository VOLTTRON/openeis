from base import DriverApplicationBaseClass, InputDescriptor, OutputDescriptor
import logging
import datetime
import django.db.models as django

class ExampleApp(DriverApplicationBaseClass):
    
    def __init__(self,building_sq_ft=-1, building_year_constructed=-1, building_name=None,**kwargs):
        #Called after app has been staged
        """
        When applications extend this base class, they need to make
        use of any kwargs that were setup in config_param
        """
        super().__init__(**kwargs)
        
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
                    "building_sq_ft": (float, None, True),
                    "building_year_constructed": (int, None, True),
                    "building_name": (str, "", False)
                
                }
        
    
    @classmethod
    def required_input(cls):
        #Called by UI
        return {
                    'OAT':InputDescriptor('OutdoorAirTemperature','Outdoor Temp'),
                    'load':InputDescriptor('WholeBuildingEnergy','Building Load'),
                    'natgas':InputDescriptor('NaturalGas','Natural Gas usage')
                }
        
    @classmethod
    def output_format(cls, input_object):
        #Called when app is staged
        topics = input_object.get_topics()
        # Work with topics["OAT"][0] to get building topic
        output_needs =  {'Analysis_Table': 
                            {'Metric':OutputDescriptor('String', 'site/building/analysis/description'),'value':OutputDescriptor('String', 'site/building/analysis/value')},  
                        'HeatMap': 
                            {'SomeValue':OutputDescriptor('int', 'site/building/analysis/description'), 'SomeOtherValue':OutputDescriptor('boolean', 'site/building/analysis/description')}}
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
        "Do stuff"
        self.out.log("Starting analysis", logging.INFO)
        #Go through some data
        data_start, data_end = self.inp.get_start_end_times()
        oat_query_set = self.inp.query_range('OAT',data_start, data_end)
        oat_stddev = django.StdDev(oat_query_set)
        
        self.out.insert_row("Analaysis_Table", {"Metric": "OAT StdDev", "value": str(oat_stddev)})
        
        
        oat_sum = self.inp.group_by('OAT',data_start, data_end, "hour")
        load_sum = self.inp.group_by('laod',data_start, data_end, "hour")
        natgas_sum = self.inp.group_by('natgas',data_start, data_end, "hour")
        
        merged_group = self.inp.merge(oat_sum, load_sum, natgas_sum)
        
        
         
        