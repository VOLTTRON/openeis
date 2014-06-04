from openeis.applications import DriverApplicationBaseClass, InputDescriptor, OutputDescriptor, ConfigDescriptor
import logging
import datetime
from datetime import timedelta
import django.db.models as django
from django.db.models import Max, Min,Avg,Sum,StdDev, Variance
from django.db import models
from dateutil.relativedelta import relativedelta

import dateutil
from django.db.models.aggregates import StdDev

class Application(DriverApplicationBaseClass):
    
    def __init__(self,*args,building_sq_ft=-1, building_year_constructed=-1, building_name=None,**kwargs):
        #Called after app has been staged
        """
        When applications extend this base class, they need to make
        use of any kwargs that were setup in config_param
        """
        super().__init__(*args,**kwargs)
        
        self.default_building_name_used = False
        
        if building_sq_ft < 0:
            raise Exception("Invalid input for building_sq_ft")
        if building_year_constructed < 0:
            raise Exception("Invalid input for building_sq_ft")
        if building_name is None:
            building_name = "None supplied"
            self.default_building_name_used = True
        
        self.sq_ft = building_sq_ft
        self.building_year = building_year_constructed
        self.building_name = building_name
        
   
    
    @classmethod
    def get_config_parameters(cls):
        #Called by UI
        return {
                    "building_sq_ft": ConfigDescriptor(float, "Square footage", minimum=200),
                    "building_year_constructed": ConfigDescriptor(int, "Consruction Year", minimum=1800, maximum=2014),
                    "building_name": ConfigDescriptor(str, "Building Name", optional=True)
                
                }
        
    
    @classmethod
    def required_input(cls):
        #Called by UI
        return {
                    'OAT':InputDescriptor('OutdoorAirTemperature','Outdoor Temp', count=1,max_count=None),
                    'load':InputDescriptor('WholeBuildingEnergy','Building Load'),
                    'natgas':InputDescriptor('NaturalGas','Natural Gas usage')
                }
        
    @classmethod
    def output_format(cls, input_object):
        #Called when app is staged
        topics = input_object.get_topics()
        # Work with topics["OAT"][0] to get building topic
        output_needs =  {'Analysis_Table': 
                            {'Metric':OutputDescriptor('String', 'site/building/analysis/description'),'value':OutputDescriptor('String', 'site/building/analysis/value')},  
                        'HeatMap': 
                            {'Times by day':OutputDescriptor('String', 'site/building/analysis/times'), 'Loads by Day':OutputDescriptor('String', 'site/building/analysis/load')}}
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
        self.out.log("Starting analysis", logging.INFO)
        #Go through some data
#         data_start, data_end = self.inp.get_start_end_times()
        
        #A year ago ignoring time info
#         year_ago = (data_end - relativedelta(year=1)).replace(hour=0,minute=0,second=0)
#         
#         #A month ago ignoring time info
#         month_ago = (data_end - relativedelta(month=1)).replace(hour=0,minute=0,second=0)
        
        #
        
        
        #To be used for generating an energy signature plot
#         oat_year_by_day = self.inp.group_by('OAT',year_ago, data_end, "day")
#         load_year_by_day = self.inp.group_by('load',year_ago, data_end, "day")
#         natgas_year_by_day = self.inp.group_by('natgas',year_ago, data_end, "day")
#         
#         oat_month_by_day = self.inp.group_by('OAT',month_ago, data_end, "day")
#         load_month_by_day = self.inp.group_by('load',month_ago, data_end, "day")
#         natgas_month_by_day = self.inp.group_by('natgas',month_ago, data_end, "day")
        
        
        load_max = self.inp.get_query_sets('load',group_by='all',group_by_aggregation=Max)['load'][0]
        load_min = self.inp.get_query_sets('load',group_by='all',group_by_aggregation=Min)['load'][0]
        
#         month_filter ={'time__gte':month_ago}
        
        load_by_hour = self.inp.get_query_sets('load',group_by='hour', 
                                                    group_by_aggregation=Sum)['load'][0]
        by_hour = load_by_hour.filter(time__hour=1)
        
        
        std_dev_load_by_hour  = load_by_hour.filter(time__hour=1).aggregate(value=Sum('value'))
        #load_by_hour.filter(time__hour=1).timeseries(aggregate=StdDev) 
                                
         
    
        print(std_dev_load_by_hour)
        print(load_min)
        print(load_max)
        
        

        
        
        
        #loads by day for dailysummary stats
        #peak95
        #mbase5
        #bpratio
        #range
#         self.out.insert_row("Analysis_Table", {"Metric": "Load Max", "value": str(load_max)})
#         self.out.insert_row("Analysis_Table", {"Metric": "Load Min", "value": str(load_min)})
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
        
         
        