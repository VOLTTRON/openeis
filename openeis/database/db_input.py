'''
Created on Apr 28, 2014

- assumes that each algo run would create a new table with a unique id
TODO: import database Table object and TableColumn object from Django database model
'''

# from schema.schema import sensordata
# from projects.models import (Table, 
#                              TableColumn,
#                              IntTableData, 
#                              StringTableData, 
#                              FloatTableData, 
#                              BooleanTableData, 
#                              TimeTableData)

db_type_map = {
               "int":"inttabledata_set",
               "string":"stringtabledata_set",
               "float":"floattabledata_set",
               "boolean":"booleantabledata_set",
               "datetime":"timetabledata_set"
               }

'''
example input map:

input_map = 
{
    'OAT_TEMPS': ('topic1','topic2', 'topic3'),
    'OCC_MODE': ('topic4',)
}

'''

from foo import get_sensor


class DatabaseInput:
    
    def __init__(self,input_id, topic_map):
        '''
        Expected input_map:
        {
            'OAT_TEMPS': ('topic1','topic2', 'topic3'),
            'OCC_MODE': ('topic4',)
        }        
        '''
        
        self.topic_map = topic_map.copy()
        
        self.sensor_map = {}
        for input_name, topics in self.topic_map.items():
            self.column_map[input_name] = tuple(get_sensor(input_id,x) for x in topics)
        
             
    def get_topics(self):
        return self.topic_map.copy()    
    
    def get_start_end_times(self):
        pass
         

    def query_range(self, ):
        pass
