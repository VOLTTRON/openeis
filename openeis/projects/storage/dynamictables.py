'''
Created on May 15, 2014
'''
from django.db import models

def create_model(name, fields=None, app_label='', module='', options=None, admin_opts=None):
    """
    Create specified model
    """
    class Meta:
        # Using type('Meta', ...) gives a dictproxy error during model creation
        pass

    if app_label:
        # app_label must be set using the Meta inner class
        setattr(Meta, 'app_label', app_label)

    # Update Meta with any options that were provided
    if options is not None:
        for key, value in options.iteritems():
            setattr(Meta, key, value)

    # Set up a dictionary to simulate declarations within a class
    attrs = {'__module__': module, 'Meta': Meta}

    # Add in any fields that were provided
    if fields:
        attrs.update(fields)

    # Create the class, which automatically triggers ModelBase processing
    model = type(name, (models.Model,), attrs)

    # Create an Admin class if admin options were provided
#     if admin_opts is not None:
#         class Admin(admin.ModelAdmin):
#             pass
#         for key, value in admin_opts:
#             setattr(Admin, key, value)
#         admin.site.register(model, Admin)

    return model

def create_table_models(basename):
    return [create_model(basename,
                         {
                          'first_name': models.CharField(max_length=255),
                          'last_name': models.CharField(max_length=255),
                          })]
    
# class Table(models.Model):
#     """
#     A Table is akin to a csv file.
#     """
#     name = models.CharField(max_length=30)
#     row_count = models.PositiveIntegerField(default=0)
#  
# class TableColumn(models.Model):
#     table = models.ForeignKey(Table, related_name="columns")
#     column = models.AutoField(primary_key=True)
#     name = models.CharField(max_length=30)
#     db_type = models.CharField(max_length=30)
#     oeis_type = models.CharField(max_length=30)
#     
# class BaseTableData(models.Model):
#     row = models.IntegerField()
#     column = models.ForeignKey(TableColumn)
#     table = models.ForeignKey(Table) 
#     
#     class Meta:
#         abstract = True
#  
# class IntTableData(BaseTableData):
#     value = models.IntegerField() 
#      
# class FloatTableData(BaseTableData):
#     value = models.FloatField() 
#      
# class StringTableData(BaseTableData):
#     value = models.TextField() 
#      
# class BooleanTableData(BaseTableData):
#     value = models.BooleanField() 
#      
# class TimeTableData(BaseTableData):
#     value=models.DateTimeField()     
