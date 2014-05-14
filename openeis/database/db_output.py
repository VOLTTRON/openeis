'''
Created on Apr 28, 2014

- assumes that each algo run would create a new table with a unique id
TODO: import database Table object and TableColumn object from Django database model
'''
from schema.schema import sensordata
from projects.models import (Table, 
                             TableColumn,
                             IntTableData, 
                             StringTableData, 
                             FloatTableData, 
                             BooleanTableData, 
                             TimeTableData)

db_type_map = {
               "int":IntTableData,
               "string":StringTableData,
               "float":FloatTableData,
               "boolean":BooleanTableData,
               "datetime":TimeTableData
               }

class DatabaseOutput:
    
    def __init__(self,input_id, topic_map):
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
        pass
        
    def log(self, level, msg, timestamp=None):
        pass