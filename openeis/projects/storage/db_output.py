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
            'OCC_MODE': ('topic4')
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
from datetime import datetime 

class DatabaseOutputFile:
    def __init__(self, algo_name, topic_map):
        '''
        output_id  - AlgoName_Timestamp
        Expected output_map:
           {
               'OAT': {'Timestamp':OutputDescriptor('timestamp', 'foo/bar/timestamp'),'OAT':OutputDescriptor('OutdoorAirTemperature', 'foo/bar/oat')}, 
               'Sensor': {'SomeValue':OutputDescriptor('int', 'some_output/value'), 
                          'SomeOtherValue':OutputDescriptor('boolean', 'some_output/value),
                          'SomeString':OutputDescriptor('string', 'some_output/string)}
           } 
        '''
        file_prefix = algo_name+'_'+str(datetime.now())
        self.sensor_map = {}
        for output_name, topics in self.topic_map.items():
            self.column_map[output_name] = csv.DictWriter(file_prefix+'_'+output_name+'.csv', topics.keys())
            self.column_map[output_name].writeheader()
            
            
    def insert_row(self,table_name,row_data):
        #Dictionary of name and values based on the outputschema of the application
        pass
        
    def log(self, msg, level=logging.DEBUG, timestamp=None):
        pass