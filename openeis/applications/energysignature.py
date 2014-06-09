from openeis.applications import DriverApplicationBaseClass, InputDescriptor, OutputDescriptor, ConfigDescriptor
import logging
from django.db.models import Avg
from .utils.spearman import findSpearmanRank

"""
    Application to output the values for energy signature scatter plot
    which is outside air temperature graphed against load.  Also calculates
    weather sensitivity by analyzing loads against outside air temperature
    by finding the Spearman rank.
"""
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
                    "building_sq_ft": ConfigDescriptor(float, "Square footage", minimum=200),
                    "building_name": ConfigDescriptor(str, "Building Name", optional=True)
                
                }
        
    
    @classmethod
    def required_input(cls):
        #Called by UI
        # Sort out units.
        return {
                    'oat':InputDescriptor('OutdoorAirTemperature','Outdoor Temp'),
                    'load':InputDescriptor('WholeBuildingElectricity','Building Load')
                }
        
    @classmethod
    def output_format(cls, input_object):
        """
        Output:
            Energy Signature: outside air temperature and loads.
                Data will be used to scatter plot.
            Weather Sensitivity: dependent on OAT and loads.
        """
        #Called when app is staged
        topics = input_object.get_topics()
        load_topic = topics['load'][0]
        load_topic_parts = load_topic.split('/')
        output_topic_base = load_topic_parts[:-1] 
        value_topic = '/'.join(output_topic_base+['energysignature','weather sensitivity'])
        oat_topic = '/'.join(output_topic_base+['energysignature','oat'])
        load_topic = '/'.join(output_topic_base+['energysignature','load'])
        
        output_needs =  {'Weather Sensitivity': 
                            {'value':OutputDescriptor('String', value_topic)},
                        'Scatterplot':
                            {'oat':OutputDescriptor('float', oat_topic),
                             'load':OutputDescriptor('float', load_topic)}}  
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
        """
        Calculates weather sensitivity using Spearman rank.
        Also, outputs data points for energy signature scatter plot.
        """
        self.out.log("Starting Spearman rank", logging.INFO)
        
        # gather loads and outside air temperatures. Reduced to and hourly average
        load_query = self.inp.get_query_sets('load', group_by='hour',group_by_aggregation=Avg,
                                             exclude={'value':None})
        oat_query = self.inp.get_query_sets('oat', group_by='hour',group_by_aggregation=Avg,
                                             exclude={'value':None})
        
        merged_load_oat = self.inp.merge(load_query,oat_query)
        
        load_values = []
        oat_values = []
        
        # Output for scatter plot
        for x in merged_load_oat: 
            load_values.append(x['load'][0])
            oat_values.append(x['oat'][0])                
            self.out.insert_row("Scatterplot", {"oat": x['oat'][0], "load": x['load'][0]})
        
        # find the Spearman rank 
        weather_sensitivity = findSpearmanRank(load_values, oat_values)
        #TODO weather sensitivity as attribute for report generation
                            
        self.out.insert_row("Weather Sensitivity", {"value": str(weather_sensitivity)})
        