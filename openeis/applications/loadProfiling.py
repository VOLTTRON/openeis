from openeis.applications import DriverApplicationBaseClass, InputDescriptor, OutputDescriptor, ConfigDescriptor
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
                    "building_sq_ft": ConfigDescriptor(float, "Square footage", minimum=200),
                    "building_name": ConfigDescriptor(str, "Building Name", optional=True)
                
                }
        
    
    @classmethod
    def required_input(cls):
        #Called by UI
        return {
                    'load':InputDescriptor('WholeBuildingEnergy','Building Load'),
                }

    """
    Output is hour with respective load, to be put in a line graph later.
    """        
    @classmethod
    def output_format(cls, input_object):
        #Called when app is staged
        topics = input_object.get_topics()
        load_topic = topics['load'][0]
        load_topic_parts = load_topic.split('/')
        output_topic_base = load_topic_parts[: -1]
        time_topic = '/'.join(output_topic_base+['timeseries', 'time'])
        load_topic = '/'.join(output_topic_base+['timeseries', 'load'])
        
        # Work with topics["OAT"][0] to get building topic
        output_needs =  {'Line Graph': 
                            {'hour':OutputDescriptor('datetime', time_topic),\
                             'value':OutputDescriptor('float', load_topic)}  
                        }
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
        
        load_by_hour = self.inp.get_query_sets('load', \
                                               exclude={'value': None})
        
        times = []
        load_vals = []
        
        for x in load_by_hour['load'][0]:
            times.append(x[0])
            load_vals.append(x[1])
            self.out.insert_row("Line Graph", \
                                {'hour': x[0], \
                                 'value': x[1]})
