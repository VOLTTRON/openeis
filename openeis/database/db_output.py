'''
Created on Apr 28, 2014

- assumes that each algo run would create a new table with a unique id
TODO: import database Table object and TableColumn object from Django database model
'''

class DatabaseOutput:
    
    def __init__(self,required_output):
        self.table_map = {}
        
        for (name,columns) in required_output.iter_items():
            self.create_table(name,columns)
             
    def create_table(self,name, columns):
        t = Table(name=name)
        column_info = {}
        for col,type in columns.iter_items():
            col_meta = TableColumns(table=t, name=col, type=type)
            column_info[col] = col_meta
        self.table_map[name] = column_info
         
    def insert_row(self,table_name,row_data):
        column_models = self.table_map.get(table_name)
        
        if column_models is None:
            #TODO: report an error.
            return
        
        for column_name, value in row_data.iter_items():
            column_model = column_models.get(column_name)
            if column_model is None:
                #TODO :report an error
                continue
            
            #table