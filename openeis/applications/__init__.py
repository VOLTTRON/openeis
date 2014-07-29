'''
Created on Apr 23, 2014

'''
from abc import ABCMeta,abstractmethod
#from schema.schema import sensordata
import logging
import pkgutil
from collections import defaultdict
from datetime import datetime

_applicationList = [name for _, name, _ in pkgutil.iter_modules(__path__)]

_applicationDict = {}

class InputDescriptor:

    def __init__(self,
                 sensor_type,
                 display_name,
                 count_min=1,
                 count_max=1,
                 _id=None):
        # TODO: Throw exception on invalid values
        self.sensor_type = sensor_type
        self.display_name = display_name
        self.count_min = count_min
        self.count_max = count_max

class OutputDescriptor:

    def __init__(self,
                 output_type,
                 topic):
        #TODO: check and throw exception if self.sensor_data is none
        #self.output_type = sensordata.get(sensor_type)
        self.output_type = output_type
        self.topic = topic

class ConfigDescriptor:
    def __init__(self,
                 config_type,
                 display_name,
                 optional=False,
                 value_default=None,
                 value_min=None,
                 value_max=None):
        # TODO: Throw exception on invalid values
        self.config_type = config_type
        self.display_name = display_name
        self.optional = optional
        self.value_default = value_default
        self.value_min = value_min
        self.value_max = value_max
        
class ApplicationDescriptor:
    def __init__(self,
                 app_name,
                 description=''):
        self.app_name = app_name
        self.description = description

class DriverApplicationBaseClass(metaclass=ABCMeta):

    def __init__(self,inp=None,out=None,**kwargs):
        """
        When applications extend this base class, they need to make
        use of any kwargs that were setup in config_param
        """
        super().__init__(**kwargs)
        self.inp = inp
        self.out = out


    def _pre_execute(self):
        pass
    
    def _post_execute(self):
        self.out.close()
    
    def run_application(self):
        try:
            self._pre_execute()
            self.execute()
        finally:
            self._post_execute()
    
    @classmethod
    @abstractmethod
    def required_input(cls):
        """
        Applications will override this method to return a dictionary specifying their
        data needs. This method will be called by the UI to do the mapping based on this.

        required input schema
                {
                    'key1':InputDescriptor1,
                    'key2':InputDescriptor2
                }
             e.g.:
                # OAT1 returns a list of 1 OAT
                # OAT2 returns a list of 3 OATs
                # CFP1 returns a list of minimum 3 and maximum all CFP1

                {
                    'OAT1':InputDescriptor('OutdoorAirTemperature','Hillside OAT'),
                    'OAT2':InputDescriptor('OutdoorAirTemperature','Roof OATs',count_min=3)
                    'CFP1':InputDescriptor('CondenserFanPower','CFP Desc',count_min=3,count_max=None)
                }
        """

    @classmethod
    @abstractmethod
    def output_format(cls, input_object):
        """
        The output object takes the resulting input object as a argument
         so that it may give correct topics to it's outputs if needed.

        output schema description
           {TableName1: {name1:OutputDescriptor1, name2:OutputDescriptor2,...},....}

           eg: {'OAT': {'Timestamp':OutputDescriptor('timestamp', 'foo/bar/timestamp'),'OAT':OutputDescriptor('OutdoorAirTemperature', 'foo/bar/oat')},
                'Sensor': {'SomeValue':OutputDescriptor('integer', 'some_output/value'),
                           'SomeOtherValue':OutputDescriptor('boolean', 'some_output/value),
                           'SomeString':OutputDescriptor('string', 'some_output/string)}}
                           
        Should always call the parent class output_format and update the dictionary returned from
        the parent.
        
        result = super().output_format(input_object)
        my_output = {...}
        result.update(my_output)
        return result 
        """
        return {}

    @classmethod
    @abstractmethod
    def get_config_parameters(cls):
        """default config schema description used by the UI to get user input
            which will be passed into the application
            Default values are used to prepopulate the UI, not to pass into the app by default

            See ConfigDescriptor for all arguments.
            {
                'Key1':ConfigDescriptor(Type1,Description1),
                'Key2':ConfigDescriptor(Type2,Description2)
            }

            e.g.:
            {
                "building_sq_ft": ConfigDescriptor(float, "Square footage"),
                "building_year_constructed": ConfigDescriptor(int, "Consruction Year"),
                "building_name": ConfigDescriptor(str, "Building Name", optional=True)
            }
        """

    @abstractmethod
    def execute(self):
        """
        Called when user says Go! in the UI
        """
        "The algorithm to run."

    @classmethod
    @abstractmethod
    def report(cls, output_obj):
        """describe output"""


class DrivenApplicationBaseClass(DriverApplicationBaseClass, metaclass=ABCMeta):
    
    def drop_partial_lines(self):
        """Specifies the merge strategy for driven application data.
        This is used as the drop_partial_lines argument for the 
        DatabaseInput.merge call used to preprocess incoming data."""        
        return False


    def execute(self):
        '''Iterate over input calling run each time'''
        query_list = []
        topic_map = self.inp.get_topics()
        
        for input_name in topic_map: 
            query_list.append(self.inp.get_query_sets(input_name, wrap_for_merge=True))
            
        merged_input_gen = self.inp.merge(*query_list, drop_partial_lines=self.drop_partial_lines())
        
        time_stamp = datetime.min
        
        for merged_input in merged_input_gen:
            time_stamp = merged_input.pop('time')
            flat_input = self._flatten_input(merged_input)
            results = self.run(time_stamp, flat_input)
            
            if not self._process_results(time_stamp, results):
                break

        results = self.shutdown()
        self._process_results(time_stamp, results)
            
    
    def _process_results(self, time_stamp, results):
        '''
        Iterate over results and put values in command, log and any other table specified by results.
        Return False if application has terminated normally.
        '''
        for point, value in results.commands.items():
            row = {"timestamp":time_stamp,
                   "point": point,
                   "value": value}
            self.out.insert_row('commands', row)
            
        for level, msg in results.log_messages:
            self.out.log(msg, level, time_stamp)
            
        for table, rows in results.table_output.items():
            for row in rows:
                self.out.insert_row(table, row)
            
        if results._terminate:
            self.out.log('Terminated normally', logging.DEBUG, time_stamp)
            return False
        
        return True
    
    
    @staticmethod
    def _flatten_input(merged_input):
        '''
        flattens the input dictionary returned from self.inp.merge
        '''
        result={}
        key_template = '{table}_{n}'
        for table, value_list in merged_input.items():
            for n, value in enumerate(value_list, start=1):
                key = key_template.format(table=table, n=n)
                result[key] = value
                
        return result
    
    @classmethod
    def output_format(cls, input_object):
        '''
        Override this method to add output tables.
        
        Call super().output_format and update the dictionary returned from
        the parent.
        
        result = super().output_format(input_object)
        my_output = {...}
        result.update(my_output)
        return result 
        '''
        results = super().output_format(input_object)  
        command_table = {'commands': {'timestamp':OutputDescriptor('timestamp', 'commands/timestamp'),
                                      'point':OutputDescriptor('string', 'commands/point'),
                                      'value':OutputDescriptor('float', 'commands/value')}}
        results.update(command_table)
        return results

    @abstractmethod
    def run(self, time, inputs):
        '''Do work for each batch of timestamped inputs
           time- current time
           inputs - dict of point name -> value

           Must return a results object.'''
        pass

    def shutdown(self):
        '''Override this to add shutdown routines.'''
        return Results()

class Results:
    def __init__(self, terminate=False):
        self.commands = {}
        self.log_messages = []
        self._terminate = terminate
        self.table_output = defaultdict(list)

    def command(self, point, value):
        self.commands[point]=value

    def log(self, message, level=logging.DEBUG):
        self.log_messages.append((level, message))

    def terminate(self, terminate):
        self._terminate = bool(terminate)
    
    def insert_table_row(self, table, row):
        self.table_output[table].append(row)

for applicationName in _applicationList:
    try:
        absolute_app = '.'+applicationName
        module = __import__(applicationName,globals(),locals(),['Application'], 1)
        klass = module.Application
    except Exception as e:
        logging.error('Module {name} cannot be imported. Reason: {ex}'.format(name=applicationName, ex=e))
        continue

    #Validation of Algorithm class

    if not issubclass(klass, DriverApplicationBaseClass):
        logging.warning('The implementation of {name} does not inherit from openeis.algorithm.DriverApplicationBaseClass.'.format(name=applicationName))

    _applicationDict[applicationName] = klass

# print(_applicationDict)


def get_algorithm_class(name):
    return _applicationDict.get(name)
