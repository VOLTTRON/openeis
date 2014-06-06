from openeis.applications import DriverApplicationBaseClass, InputDescriptor, OutputDescriptor, ConfigDescriptor
import logging
import datetime
import numpy
import math
from datetime import timedelta
import django.db.models as django
from django.db.models import Max, Min,Avg,Sum,StdDev
from django.db import models
from dateutil.relativedelta import relativedelta

import dateutil
from django.db.models.aggregates import StdDev

class Application(DriverApplicationBaseClass):
    
    def __init__(self,*args,building_sq_ft=-1, building_name=None,**kwargs):
        #Called after app has been staged
        """
        When applications extend this base class, they need to make
        use of any kwargs that were setup in config_param
        """
        super().__init__(*args,**kwargs)
        
        self.default_building_name_used = False
        
        if building_sq_ft < 0:
            raise Exception("Invalid input for building_sq_ft")
        if building_name is None:
            building_name = "None supplied"
            self.default_building_name_used = True
        
        self.sq_ft = building_sq_ft
        self.building_name = building_name
        
   
    
    @classmethod
    def get_config_parameters(cls):
        #Called by UI
        return {
                    "building_sq_ft": ConfigDescriptor(float, "Square footage", minimum=200),
                    "building_name": ConfigDescriptor(str, "Building Name", optional=True)
                
                }
        
    
    @classmethod
    def required_input(cls):
        #Called by UI
        # Sort out units.
        return {
                    'load':InputDescriptor('WholeBuildingElectricity','Building Load')
                }
        
    @classmethod
    def output_format(cls, input_object):
        #Called when app is staged
        topics = input_object.get_topics()
        load_topic = topics['load'][0]
        load_topic_parts = load_topic.split('/')
        output_topic_base = load_topic_parts[:-1] 
        description_topic = '/'.join(output_topic_base+['dailySummary','description'])
        value_topic = '/'.join(output_topic_base+['dailySummary','value'])
        output_needs =  {'Daily_Summary_Table': 
                            {'Metric':OutputDescriptor('String', description_topic),
                             'value':OutputDescriptor('String', value_topic)}}  
        return output_needs
        
    def report(self):
        #Called by UI to create Viz
        """Describe how to present output to user
        Display this viz with these columns from this table
        
        
        display elements is a list of display objects specifying viz and columns for that viz 
        """
        display_elements = []
        
        return display_elements
        
    def execute(self):
        #Called after User hits GO
        "Do stuff"
        self.out.log("Starting daily summary", logging.INFO)
        #Go through some data
#         data_start, data_end = self.inp.get_start_end_times()
        
        #A year ago ignoring time info
#         year_ago = (data_end - relativedelta(year=1)).replace(hour=0,minute=0,second=0)
#         
#         #A month ago ignoring time info
#         month_ago = (data_end - relativedelta(month=1)).replace(hour=0,minute=0,second=0)
        
        #
        
        
        floorAreaSqft = self.sq_ft
        load_max = self.inp.get_query_sets('load',group_by='all',group_by_aggregation=Max)['load'][0]
        load_min = self.inp.get_query_sets('load',group_by='all',group_by_aggregation=Min)['load'][0]
        
        load_query = self.inp.get_query_sets('load')['load'][0]

        
        #TODO: Time Zone support
        load_values = [] 
        load_startDay = load_query.earliest()[0].date()
        load_endDay = load_query.latest()[0].date()
        current_Day = load_startDay
        load_day_list_95 = [] 
        load_day_list_5 = []
        
        for x in load_query: 
            load_values.append(x[1])
        
        peakLoad = max(load_values) * 1000
        peakLoadIntensity = peakLoad / self.sq_ft
                        
        while current_Day <= load_endDay:
            load_day_query = load_query.filter(time__year=current_Day.year,
                                            time__month=current_Day.month,
                                            time__day=current_Day.day) 
            current_Day += relativedelta(days=1)
            
            load_day_values = [x[1] for x in load_day_query]
            if ( len(load_day_values) < 5):
                continue
                
            load_day_list_95.append(numpy.percentile(load_day_values,95))
            load_day_list_5.append(numpy.percentile(load_day_values,5))
            
            
        load_day_95_mean = numpy.mean(load_day_list_95)
        load_day_5_mean = numpy.mean(load_day_list_5)
        load_day_ratio_mean = numpy.mean(numpy.divide(load_day_list_5, load_day_list_95))
        load_day_range_mean = numpy.mean(numpy.subtract(load_day_list_95,load_day_list_5))

        hourly_variability = []
        for h in range(24):        
            hourly_mean = self.inp.get_query_sets('load',group_by='all', 
                                                            group_by_aggregation=Avg,
                                                            filter_={'time__hour':h})['load'][0]

            hour_load_query= self.inp.get_query_sets('load',filter_={'time__hour':h})['load'][0] 
            counts = hour_load_query.count()
            rootmeansq = math.sqrt(sum((x[1]-hourly_mean)**2 for x in hour_load_query)/(counts-1))
            
            hourly_variability.append(rootmeansq/hourly_mean)
            
        load_variability = numpy.mean(hourly_variability)
        
        
        self.out.insert_row("Daily_Summary_Table", {"Metric": "Load Max Intensity", 
                                                    "value": str(load_max/floorAreaSqft)})
        self.out.insert_row("Daily_Summary_Table", {"Metric": "Load Min Intensity", 
                                                    "value": str(load_min/floorAreaSqft)})        
        self.out.insert_row("Daily_Summary_Table", {"Metric": "Daily Load 95th Percentile", 
                                                    "value": str(load_day_95_mean)})        
        self.out.insert_row("Daily_Summary_Table", {"Metric": "Daily Load 5th Percentile", 
                                                    "value": str(load_day_5_mean)})        
        self.out.insert_row("Daily_Summary_Table", {"Metric": "Daily Load Ratio", 
                                                    "value": str(load_day_ratio_mean)})                
        self.out.insert_row("Daily_Summary_Table", {"Metric": "Daily Load Range", 
                                                    "value": str(load_day_range_mean)})
        self.out.insert_row("Daily_Summary_Table", {"Metric": "Load Variability", 
                                                    "value": str(load_variability)})
        self.out.insert_row("Daily_Summary_Table", {"Metric": "Peak Load Benchmark",
                                                     "value": str(peakLoadIntensity)})
        
#         month_filter ={'time__gte':month_ago}
        
#         
#         
#         
#         std_dev_load_by_hour  = load_by_hour.filter(time__hour=1).aggregate(value=StdDev('values'))
#     
#         print(std_dev_load_by_hour)
#         print(load_min)
#         print(load_max)
        
        

        
        
        
        #loads by day for dailysummary stats
        #peak95
        #mbase5
        #bpratio
        #range

#         self.out.insert_row("Analysis_Table", {"Metric": "Load StdDev", "value": str(django.StdDev(load_month_by_day))})
#         self.out.insert_row("Analysis_Table", {"Metric": "Load Mean", "value": str(django.Avg(load_month_by_day))})
#         self.out.insert_row("Analysis_Table", {"Metric": "Load Variance", "value": str(django.Variance(load_month_by_day))})
#         
        
        #Setup heat map
        
        
#         success = gr_bldg.genEnergySignaturePlot(oatsCurrYear, loadsCurrYear,
#             bldgMetaData['oat-units'], bldgMetaData['load-units'],
#             figWritePath=os.path.join(outDirName,figRelPath))
 
#         for 
#         self.out.insert_row("HeatMap", {"Times by Day": thing, "Loads by Day": str(django.Max(load_month_by_day))})
        
        
        
        
        
        
        
#         
#         oat_sum = self.inp.group_by('OAT',data_start, data_end, "hour")
#         load_sum = self.inp.group_by('laod',data_start, data_end, "hour")
#         natgas_sum = self.inp.group_by('natgas',data_start, data_end, "hour")
#         
#         merged_group = self.inp.merge(oat_sum, load_sum, natgas_sum)
#         
        
         
        