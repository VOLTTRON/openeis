'''
Created on Apr 28, 2014

- assumes that each algo run would create a new table with a unique id
TODO: import database Table object and TableColumn object from Django database model
'''

import logging

class DatabaseOutput:
    
    def __init__(self,output_id, topic_map):
        '''
        Expected output_map:
        {
            'OAT_TEMPS': ('topic1','topic2', 'topic3'),
            'OCC_MODE': ('topic4',)
        }        
        '''
        
        self.topic_map = topic_map.copy()
        
        self.sensor_map = {}
        for input_name, topics in self.topic_map.items():
            self.column_map[input_name] = tuple(get_sensor(input_id,x) for x in topics)
            
            
    def insert_row(self,table_name,row_data):
        #Dictionary of name and values based on the outputschema of the application
        pass
        
    def log(self, msg, level=logging.DEBUG, timestamp=None):
        pass

import csv    
class DatabaseOutputFile:
    def __init__(self,output_id, topic_map):
        '''
        Expected output_map:
        {
            'OAT_TEMPS': ('topic1','topic2', 'topic3'),
            'OCC_MODE': ('topic4',)
        }        
        '''
        
        self.sensor_map = {}
        for output_name, topics in self.topic_map.items():
            self.column_map[output_name] = csv.DictWriter(output_name+'csv', topics)
            
            
    def insert_row(self,table_name,row_data):
        #Dictionary of name and values based on the outputschema of the application
        pass
        
    def log(self, msg, level=logging.DEBUG, timestamp=None):
        pass