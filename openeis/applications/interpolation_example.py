from openeis.applications import DriverApplicationBaseClass, InputDescriptor, OutputDescriptor, ConfigDescriptor
from openeis.projects.storage.db_output import DatabaseOutputFile
import logging
import datetime
from datetime import timedelta
from pytz import timezone
import django.db.models as django
from django.db.models import Max, Min,Avg,Sum,StdDev, Variance
from django.db import models
from dateutil.relativedelta import relativedelta
from openeis.applications import reports
import dateutil
from django.db.models.aggregates import StdDev
from builtins import print
from openeis.projects.storage import db_output



class Application(DriverApplicationBaseClass):

    def __init__(self,*args,building_sq_ft=-1, building_year_constructed=-1, building_name=None,**kwargs):
        #Called after app has been staged
        """
        When applications extend this base class, they need to make
        use of any kwargs that were setup in config_param
        """
        super().__init__(*args,**kwargs)

#        self.default_building_name_used = False
#
#        if building_sq_ft < 0:
#            raise Exception("Invalid input for building_sq_ft")
#        if building_year_constructed < 0:
#            raise Exception("Invalid input for building_sq_ft")
#        if building_name is None:
#            building_name = "None supplied"
#            self.default_building_name_used = True
#
#        self.sq_ft = building_sq_ft
#        self.building_year = building_year_constructed
#        self.building_name = building_name



    @classmethod
    def get_config_parameters(cls):
        #Called by UI
        return {
#                    "building_sq_ft": ConfigDescriptor(float, "Square footage", value_min=200),
#                    "building_year_constructed": ConfigDescriptor(int, "Consruction Year", value_min=1800, value_max=2014),
#                    "building_name": ConfigDescriptor(str, "Building Name", optional=True)

                }


    @classmethod
    def required_input(cls):
        #Called by UI
        return {
                    'oat':InputDescriptor('OutdoorAirTemperature','Outdoor Temp', count_min=1,count_max=10),
                    'load':InputDescriptor('WholeBuildingElectricity','Building Load'),
#                    'natgas':InputDescriptor('WholeBuildingGas','Natural Gas usage')
                }

    @classmethod
    def output_format(cls, input_object):
        #Called when app is staged
        topics = input_object.get_topics()
        # Work with topics["OAT"][0] to get building topic
#         'SomeString':OutputDescriptor('string', 'some_output/string)}
        oats = topics['oat']

        output_needs =  {'Time_Table':
                            {'time':OutputDescriptor('timestamp', 'site/building/analysis/date'),
                             'load':OutputDescriptor('float', 'site/building/analysis/load')}}
        count = 0
        for oat in oats:
            name = "oat" + str(count)
            output_needs['Time_Table'][name] = OutputDescriptor('float', 'site/building/analysis/{}'.format(name))
            count += 1

        return output_needs

    @classmethod
    def reports(cls, output_object):
        #Called by UI to create Viz
        """Describe how to present output to user
        Display this viz with these columns from this table


        display elements is a list of display objects specifying viz and columns for that viz
        """
        rep_desc = 'Data Interpolation Example'

        report = reports.Report(rep_desc)

        column_info = (('time', 'Timestamp'), ('load', 'Load'))
#
        print(output_object)
        print(output_object.__class__.__name__)
#        print(output_object.output_names)
#        print(output_object.output_names['Time_Table'])
        keys = None

        if isinstance(output_object, dict):
            keys = output_object['Time_Table'].keys()
        elif isinstance(output_object, DatabaseOutputFile):
            keys = list(output_object.output_names['Time_Table'])

#        print(keys)

        for key in keys:
            if key.startswith('oat'):
                column_info = column_info +((key,key),)

        text_blurb = reports.TextBlurb('')
        summary_table = reports.Table('Time_Table',
                                      column_info,
                                      title='Data Interpolation Results',
                                      description='A table showing data interpolation')


        report.add_element(summary_table)

        # list of report objects

        report_list = [report]

        return report_list

    def execute(self):
        #Called after User hits GO
        "Do stuff"
        self.out.log("Starting analysis", logging.INFO)

        load = self.inp.get_query_sets('load',wrap_for_merge=True)
        oat = self.inp.get_query_sets('oat',wrap_for_merge=True)

        data = self.inp.merge_fill_in_data(load,oat)

        for row in data:
            ts = row['time']
            ts = ts.astimezone(timezone('US/Pacific'))
            oats = row['oat']

            row_to_write = {"time": ts, "load": row['load'][0]}
            count = 0
            for oat in oats:
                name = 'oat'+str(count)
                row_to_write[name] = oats[count]
                count += 1
            self.out.insert_row("Time_Table", row_to_write)


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

#        print (self.inp.get_topics())
#
#        print (self.inp.get_topics_meta()['load']['pnnl/isb1/WholeBuildingElectricity']['unit'])
#        print (self.inp.get_topics_meta()['load'][self.inp.get_topics()['load'][0]]['unit'])




#        load_max = self.inp.get_query_sets('load',group_by='all',group_by_aggregation=Max)[0]
#        load_min = self.inp.get_query_sets('load',group_by='all',group_by_aggregation=Min)[0]
#
#        # gather loads and outside air temperatures. Reduced to and hourly average
#        load_query = self.inp.get_query_sets('load', group_by='hour',group_by_aggregation=Avg,
#                                             exclude={'value':None},
#                                             wrap_for_merge=True)
#        oat_query = self.inp.get_query_sets('oat', group_by='hour',group_by_aggregation=Avg,
#                                             exclude={'value':None},
#                                             wrap_for_merge=True)
#
#
##         merged_load_oat = self.inp.merge(load_query,oat_query, drop_partial_lines=True)
##         month_filter ={'time__gte':month_ago}
#
#        thing = self.inp.get_query_sets('load',group_by='hour',
#                                                    group_by_aggregation=Sum)
#
#        load_by_hour = self.inp.get_query_sets('load',group_by='hour',
#                                                    group_by_aggregation=Sum)[0]
#        by_hour = load_by_hour.filter(time__hour=1)
#
#
#        #std_dev_load_by_hour  = load_by_hour.filter(time__hour=1).aggregate(value=Sum('values'))
#        #load_by_hour.filter(time__hour=1).timeseries(aggregate=StdDev)
#
#
#
##         print(std_dev_load_by_hour)
#        print(load_min)
#        print(load_max)
#
#        print(self.inp.get_topics_meta())
#
#
#
#
#        #loads by day for dailysummary stats
#        #peak95
#        #mbase5
#        #bpratio
#        #range
##         self.out.insert_row("Analysis_Table", {"Metric": "Load Max", "value": str(load_max)})
##         self.out.insert_row("Analysis_Table", {"Metric": "Load Min", "value": str(load_min)})
##         self.out.insert_row("Analysis_Table", {"Metric": "Load StdDev", "value": str(django.StdDev(load_month_by_day))})
##         self.out.insert_row("Analysis_Table", {"Metric": "Load Mean", "value": str(django.Avg(load_month_by_day))})
##         self.out.insert_row("Analysis_Table", {"Metric": "Load Variance", "value": str(django.Variance(load_month_by_day))})
##
#
#        #Setup heat map
#
#
##         success = gr_bldg.genEnergySignaturePlot(oatsCurrYear, loadsCurrYear,
##             bldgMetaData['oat-units'], bldgMetaData['load-units'],
##             figWritePath=os.path.join(outDirName,figRelPath))
#
##         for
##         self.out.insert_row("HeatMap", {"Times by Day": thing, "Loads by Day": str(django.Max(load_month_by_day))})
#
#
#
#
#
#
#
##
##         oat_sum = self.inp.group_by('OAT',data_start, data_end, "hour")
##         load_sum = self.inp.group_by('laod',data_start, data_end, "hour")
##         natgas_sum = self.inp.group_by('natgas',data_start, data_end, "hour")
##
##         merged_group = self.inp.merge(oat_sum, load_sum, natgas_sum)
##



