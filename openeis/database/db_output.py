'''
Created on Apr 28, 2014

- assumes that each algo run would create a new table with a unique id
TODO: import database Table object and TableColumn object from Django database model
'''

class DatabaseOutput:
    
    def __init__(self,required_output):
        for (name,columns) in required_output.iter_items():
            self.create_table(name,columns)
             
    def create_table(self,name, columns):
        pass
#         t = Table(name=name)
#         column_models = {}
#         for col,type in columns.iter_items():
#             col_data = TableColumns(table=t, name=col, type=type)
#             column_models[col] = col_data      
         
    def insert_row(self,table_name,row_data):
        pass