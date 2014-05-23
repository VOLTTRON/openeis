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
        output_id  - name identifying the algortihm
        Expected output_map:
           {
               'OAT': {'Timestamp':OutputDescriptor('timestamp', 'foo/bar/timestamp'),'OAT':OutputDescriptor('OutdoorAirTemperature', 'foo/bar/oat')}, 
               'Sensor': {'SomeValue':OutputDescriptor('int', 'some_output/value'), 
                          'SomeOtherValue':OutputDescriptor('boolean', 'some_output/value),
                          'SomeString':OutputDescriptor('string', 'some_output/string)}
           } 
        '''
        file_prefix = algo_name+'_'+datetime.now().strftime('%m-%d-%Y %H %M %S')
        
        log_file = file_prefix + '.log'
        self._logger = logging.getLogger()
        formatter = logging.Formatter('%(levelname)s:%(name)s %(message)s')
        self._logger.setLevel(logging.INFO)
        
        str_handler = logging.StreamHandler()
        str_handler.setLevel(logging.ERROR)
        str_handler.setFormatter(formatter)
        self._logger.addHandler(str_handler)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)
        
        self.table_map = {}
        for table_name, topics in topic_map.items():
            csv_file = file_prefix+'_'+table_name+'.csv'
            self.table_map[table_name] = csv.DictWriter(open(csv_file,'w', newline=''), topics.keys())
            self.table_map[table_name].writeheader()
        
            
            
    def insert_row(self,table_name,row_data):
        #Dictionary of name and values based on the outputschema of the application
        self.table_map[table_name].writerow(row_data)
        
    
    def log(self, msg, level=logging.DEBUG, timestamp=None):
        if timestamp is not None:
            self._logger.log(level, '{time} - {msg}'.format(time=timestamp.strftime('%m/%d/%Y %H:%M:%S'),msg=msg))
        else:
            self.logger.log(level, 'NO TIME GIVEN - {msg}'.format(msg=msg))
            

if __name__ == '__main__':

    from openeis.algorithm.base import OutputDescriptor
      
    topic_map = {'OAT': {'Timestamp':OutputDescriptor('timestamp', 'foo/bar/timestamp'),'OAT':OutputDescriptor('OutdoorAirTemperature', 'foo/bar/oat')}, }
    output  = DatabaseOutputFile('test_algo', topic_map)
    
    row_data = {'Timestamp': datetime(2000,1,1,8,0,0),
                'OAT': 52.3}
    output.insert_row('OAT', row_data)
    
    output.log('test message', logging.ERROR, datetime.now())
    