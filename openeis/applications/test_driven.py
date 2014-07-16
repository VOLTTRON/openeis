from openeis.applications import (DrivenApplicationBaseClass, 
                                  InputDescriptor, 
                                  OutputDescriptor, 
                                  ConfigDescriptor, 
                                  Results)

import logging

class Application(DrivenApplicationBaseClass):
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
        
        self.first = True
        
        self.counter = 0



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
        results = super()
        return {
                    'OAT':InputDescriptor('OutdoorAirTemperature','Outdoor Temp', count_max=None),
                    'load':InputDescriptor('WholeBuildingEnergy','Building Load'),
                    'natgas':InputDescriptor('NaturalGas','Natural Gas usage')
                }

    @classmethod
    def output_format(cls, input_object):
        output_needs = super().output_format(input_object)
        #Called when app is staged
        topic_map = input_object.get_topics()
        # Work with topics["OAT"][0] to get building topic
#         descriptor_column = 'site/building/analysis/description'
        output_needs['output'] = {'time': OutputDescriptor('timestamp', 'time')}
        
        out_col_fmt = '{g}_{n}'

        #Table per topic, regardless of group
        for group, topic_list in topic_map.items():
            for i, topic in enumerate(topic_list,start=1):
                out_topic = topic+'/output'
                out_col = out_col_fmt.format(g=group, n=i)
                output_needs['output'][out_col] = OutputDescriptor('string', out_topic)

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

    def run(self, time, inputs):
        results = Results()
        
        if self.first:
            results.log('First Post!!!!11111ELEVENTY', logging.INFO)
            self.first = False
        
        inputs['time'] = time
        
        results.insert_table_row('output', inputs) 
        
        self.counter += 1
        results.command('/awesome/counter', self.counter)
        
        return results
    
    def shutdown(self):
        results = Results()
        results.log('ARG!! I DIED!!', logging.INFO)
        return results



