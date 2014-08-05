'''
Created on Apr 28, 2014

- assumes that each algo run would create a new table with a unique id
'''

import logging

from openeis.projects.storage import sensorstore
from collections import defaultdict 

BATCH_SIZE = 1000
LOG_TABLE_NAME = 'log'

class DatabaseOutput:
    
    def __init__(self,output_id, output_map):
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
        
        self.table_map = {}
        self.app_table_map = {}
        
        self.batch_store = defaultdict(list)
        
        for table_name, table_description in output_map.items():
            fields = ((col_name, descriptor.output_type) 
                      for col_name, descriptor 
                      in table_description.items())
            app_output, model_klass = sensorstore.create_output(output_id, fields)
            
            self.table_map[table_name] = model_klass
            self.app_table_map[table_name] = app_output
            
        #create the logging table
        logging_fields = {'msg':'string', 'level':'integer', 'datetime':'datetime'}
        log_output, log_klass = sensorstore.create_output(output_id, logging_fields)
        self.table_map[LOG_TABLE_NAME] = log_klass
        self.app_table_map[LOG_TABLE_NAME] = log_output
            
            
    def insert_row(self,table_name,row_data):
        #Dictionary of name and values based on the outputschema of the application
        klass = self.table_map[table_name]
        instance = klass(**row_data)
        self.batch_store[table_name].append(instance)
        
        if len(self.batch_store[table_name]) >= BATCH_SIZE:
            klass.objects.bulk_create(self.batch_store[table_name])
            self.batch_store[table_name] = []
        
    def log(self, msg, level=logging.DEBUG, timestamp=None):
        logging_fields = {'msg':msg, 'level':level, 'datetime':timestamp}
        self.insert_row(LOG_TABLE_NAME, logging_fields)
    
    def close(self):
        for table_name, batch_list in self.batch_store.items():
            if batch_list:
                klass = batch_list[0].__class__
                klass.objects.bulk_create(batch_list)
                self.batch_store[table_name] = []

import csv
from datetime import datetime 

class DatabaseOutputFile(DatabaseOutput):
    def __init__(self, algo_name, output_id, output_map):
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
        super().__init__(output_id, output_map)
        
        self.output_names = {}
        for table_name, table_description in output_map.items():
            self.output_names[table_name] = table_description.keys()
        
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
        
        self.csv_table_map = {}
        for table_name, topics in output_map.items():
            csv_file = file_prefix+'_'+table_name+'.csv'
            self.csv_table_map[table_name] = csv.DictWriter(open(csv_file,'w', newline=''), topics.keys())
            self.csv_table_map[table_name].writeheader()
        
            
            
#     def insert_row(self,table_name,row_data):
#         #Dictionary of name and values based on the outputschema of the application
#         self.table_map[table_name].writerow(row_data)
        
    
    def log(self, msg, level=logging.DEBUG, timestamp=None):
        super().log(msg, level=level, timestamp=timestamp)
        
        if timestamp is not None:
            self._logger.log(level, '{time} - {msg}'.format(time=timestamp.strftime('%m/%d/%Y %H:%M:%S'),msg=msg))
        else:
            self._logger.log(level, 'NO TIME GIVEN - {msg}'.format(msg=msg))
            
    def close(self):
        super().close()
        print('Writing CSV files.')
        for table_name, fields in self.output_names.items():
            klass = self.table_map[table_name]
            dict_writer =  self.csv_table_map[table_name]
            for k in klass.objects.all():
                row_data = dict((field, getattr(k, field)) for field in fields)
                dict_writer.writerow(row_data)
            

if __name__ == '__main__':

    from openeis.applications import OutputDescriptor
      
    topic_map = {'OAT': {'Timestamp':OutputDescriptor('timestamp', 'foo/bar/timestamp'),'OAT':OutputDescriptor('OutdoorAirTemperature', 'foo/bar/oat')}, }
    output  = DatabaseOutputFile('test_algo', topic_map)
    
    row_data = {'Timestamp': datetime(2000,1,1,8,0,0),
                'OAT': 52.3}
    output.insert_row('OAT', row_data)
    
    output.log('test message', logging.ERROR, datetime.now())
    