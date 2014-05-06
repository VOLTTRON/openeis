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
    'OAT_TEMPS': ((DateTableColumn,TableColumn), (DateTableColumn,TableColumn), (DateTableColumn,TableColumn)),
    'OCC_MODE': ((DateTableColumn,TableColumn),)
}

'''


class DatabaseInput:
    
    def __init__(self,input_map):
        '''
        Expected input map:
        
        '''
        self.create_column_map(input_map)        
        
             
    def create_column_map(self,input_map):
        self.column_map = {}
        for input_name, inputs in input_map:
            managers = []
            for date_column, data_column in inputs:
                date_manager = date_column.timetabledata_set
                data_manager = getattr(data_column, db_type_map[data_column.db_type])
                managers.append(date_manager, data_manager)
            self.column_map[input_name] = tuple(managers)
                
         

    def query_range(self, ):
        pass
