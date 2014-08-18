'''
Created on Apr 28, 2014

- assumes that each algo run would create a new table with a unique id
'''

import logging
import io
from .. import models
from . import sensorstore
from collections import defaultdict

BATCH_SIZE = 1000
LOG_TABLE_NAME = 'log'

class DatabaseOutput:

    def __init__(self, analysis, output_map):
        '''
        analysis - Analysis model instance to associate output to
        Expected output_map:
           {
               'OAT': {'Timestamp':OutputDescriptor('timestamp', 'foo/bar/timestamp'),'OAT':OutputDescriptor('OutdoorAirTemperature', 'foo/bar/oat')},
               'Sensor': {'SomeValue':OutputDescriptor('int', 'some_output/value'),
                          'SomeOtherValue':OutputDescriptor('boolean', 'some_output/value),
                          'SomeString':OutputDescriptor('string', 'some_output/string)}
           }
        '''

        self.table_map = {}

        self.batch_store = defaultdict(list)

        for table_name, table_description in output_map.items():
            fields = {col_name: descriptor.output_type
                      for col_name, descriptor
                      in table_description.items()}
            app_output = models.AppOutput.objects.create(analysis=analysis,
                                                         name=table_name,
                                                         fields=fields)
            model_klass = sensorstore.get_data_model(app_output,
                                                     analysis.dataset.map.project.id,
                                                     fields)

            self.table_map[table_name] = model_klass

        #create the logging table
        logging_fields = {'msg':'string', 'level':'integer', 'datetime':'datetime'}
        log_output = models.AppOutput.objects.create(analysis=analysis,
                                                     name=LOG_TABLE_NAME,
                                                     fields=logging_fields)
        log_klass = sensorstore.get_data_model(log_output,
                                               analysis.dataset.map.project.id,
                                               logging_fields)

        self.table_map[LOG_TABLE_NAME] = log_klass

        self.log_level = logging.ERROR
        if analysis.debug:
            self.log_level = logging.DEBUG


    def insert_row(self,table_name,row_data):
        #Dictionary of name and values based on the outputschema of the application
        klass = self.table_map[table_name]
        instance = klass(**row_data)
        self.batch_store[table_name].append(instance)

        if len(self.batch_store[table_name]) >= BATCH_SIZE:
            klass.objects.bulk_create(self.batch_store[table_name])
            self.batch_store[table_name] = []

    def log(self, msg, level=logging.DEBUG, timestamp=None):
        if level >= self.log_level:
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

class DatabaseOutputIO(DatabaseOutput): 
    def __init__(self, analysis, output_map):
        '''
        analysis - Analysis model instance to associate output to
        Expected output_map:
           {
               'OAT': {'Timestamp':OutputDescriptor('timestamp', 'foo/bar/timestamp'),'OAT':OutputDescriptor('OutdoorAirTemperature', 'foo/bar/oat')},
               'Sensor': {'SomeValue':OutputDescriptor('int', 'some_output/value'),
                          'SomeOtherValue':OutputDescriptor('boolean', 'some_output/value),
                          'SomeString':OutputDescriptor('string', 'some_output/string)}
           }
        '''
        super().__init__(analysis, output_map)

        self.output_names = {}
        for table_name, table_description in output_map.items():
            self.output_names[table_name] = table_description.keys()

        self.file_prefix = analysis.application+'_'+datetime.now().strftime('%m-%d-%Y %H %M %S')

        self._logger = logging.getLogger()
        formatter = logging.Formatter('%(levelname)s:%(name)s %(message)s')
        self._logger.setLevel(logging.INFO)

        str_handler = logging.StreamHandler()
        str_handler.setLevel(logging.ERROR)
        str_handler.setFormatter(formatter)
        self._logger.addHandler(str_handler)

        log_io = io.StringIO()
        file_handler = logging.StreamHandler(log_io)
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)

        self.csv_table_map = {}
        self.csv_file_io_table_map = {}
        for table_name, topics in output_map.items():
            csv_file_io = io.StringIO()
            self.csv_table_map[table_name] = csv.DictWriter(csv_file_io, topics.keys())
            self.csv_table_map[table_name].writeheader()
            self.csv_file_io_table_map[table_name] = csv_file_io
            
       
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
        print('Writing to IO.')
        for table_name, fields in self.output_names.items():
            klass = self.table_map[table_name]
            dict_writer =  self.csv_table_map[table_name]
            for k in klass.objects.all():
                row_data = dict((field, getattr(k, field)) for field in fields)
                dict_writer.writerow(row_data)

class DatabaseOutputFile(DatabaseOutputIO):
    def __init__(self, analysis, output_map):
        '''
        analysis - Analysis model instance to associate output to
        Expected output_map:
           {
               'OAT': {'Timestamp':OutputDescriptor('timestamp', 'foo/bar/timestamp'),'OAT':OutputDescriptor('OutdoorAirTemperature', 'foo/bar/oat')},
               'Sensor': {'SomeValue':OutputDescriptor('int', 'some_output/value'),
                          'SomeOtherValue':OutputDescriptor('boolean', 'some_output/value),
                          'SomeString':OutputDescriptor('string', 'some_output/string)}
           }
        '''
        super().__init__(analysis, output_map)
        
    def log(self, msg, level=logging.DEBUG, timestamp=None):
        super().log(msg, level=level, timestamp=timestamp)

    def close(self):
        super().close()
        print('Writing log file.')
        log_file = self.file_prefix+'.log'
        with open(log_file,'w') as f:
            f.write(self._logger.handlers[2].stream.getvalue())
        print('Writing CSV files.')
        for table_name in self.csv_file_io_table_map:
            csv_file_io = self.csv_file_io_table_map[table_name]
            csv_file = self.file_prefix +'_'+table_name+'.csv'
            with open(csv_file,'wb') as f:
                f.write(bytes(csv_file_io.getvalue(), 'UTF-8'))
                    
        
from zipfile import ZipFile
   
class DatabaseOutputDebug(DatabaseOutputIO):
    def __init__(self, analysis, output_map):
        '''
        analysis - Analysis model instance to associate output to
        Expected output_map:
           {
               'OAT': {'Timestamp':OutputDescriptor('timestamp', 'foo/bar/timestamp'),'OAT':OutputDescriptor('OutdoorAirTemperature', 'foo/bar/oat')},
               'Sensor': {'SomeValue':OutputDescriptor('int', 'some_output/value'),
                          'SomeOtherValue':OutputDescriptor('boolean', 'some_output/value),
                          'SomeString':OutputDescriptor('string', 'some_output/string)}
           }
        '''
        super().__init__(analysis, output_map)
        
    def log(self, msg, level=logging.DEBUG, timestamp=None):
        super().log(msg, level=level, timestamp=timestamp)

    def close(self):
        super().close()
        print('Writing Debug zip file.')
        zip_file = self.file_prefix +'.zip'
        with ZipFile(zip_file, 'w') as myzip:
            lof_file = self.file_prefix+".log"
            myzip.writestr(lof_file,self._logger.handlers[2].stream.getvalue())
            for table_name in self.csv_file_io_table_map:
                csv_file_io = self.csv_file_io_table_map[table_name]
                csv_file = self.file_prefix +'_'+table_name+'.csv'
                myzip.writestr(csv_file,csv_file_io.getvalue())    
                

if __name__ == '__main__':

    from openeis.applications import OutputDescriptor

    topic_map = {'OAT': {'Timestamp':OutputDescriptor('timestamp', 'foo/bar/timestamp'),'OAT':OutputDescriptor('OutdoorAirTemperature', 'foo/bar/oat')}, }
    output  = DatabaseOutputFile('test_algo', topic_map)

    row_data = {'Timestamp': datetime(2000,1,1,8,0,0),
                'OAT': 52.3}
    output.insert_row('OAT', row_data)

    output.log('test message', logging.ERROR, datetime.now())

