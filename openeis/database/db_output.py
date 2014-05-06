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
    
    def __init__(self,required_output):
        self.table_map = {}
        
        for (name,columns) in required_output.iter_items():
            self.create_table(name,columns)
             
    def create_table(self,name, columns):
        table = Table(name=name)
        column_info = {}
        for column_name,oeis_type in columns.iter_items():
            #get db_type for oeis_type
            sensor_type = sensordata.get(oeis_type)
            if sensor_type is None :
                if oeis_type not in db_type_map:
                    raise TypeError("Invalid data type {type}".format(type=oeis_type))
                db_type = oeis_type
            else:
                db_type = sensor_type["data_type"]
           
            column = TableColumn(table=table, name=column_name, db_type=db_type, oeis_type=oeis_type)
            column_info[column_name] = column, db_type_map[db_type]
        self.table_map[name] = table, column_info 
         
    def insert_row(self,table_name,row_data):
        col_table_tuple = self.table_map.get(table_name)
        if col_table_tuple is None:
            #TODO: report an error.
            return
        table, column_models = col_table_tuple
        row_index = table.row_count
        
        for column_name, value in row_data.iter_items():
            col_model_tuple  = column_models.get(column_name)
            if col_model_tuple is None:
                #TODO :report an error
                continue
            column_model, table_data_klass = col_model_tuple
            table_data_klass(column=column_model,table=table,row=row_index, value=value)
        table.row_cout += 1