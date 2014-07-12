'''
Created on Apr 23, 2014

'''
from abc import ABCMeta,abstractmethod
#from schema.schema import sensordata
import logging
import pkgutil

_applicationList = [name for _, name, _ in pkgutil.iter_modules(__path__)]

_applicationDict = {}

class InputDescriptor:

    def __init__(self,
                 sensor_type,
                 desc,
                 count=1,
                 count_min=1,
                 count_max=1,
                 _id=None):
        # TODO: Throw exception on invalid values
        self.sensor_type = sensor_type
        self.desc = desc
        self.count = count
        if(count_min is not None and count < count_min):
            count_min = count
        self.count_min = count_min
        if(count_max is not None and count > count_max):
            count_max = count
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
                 desc,
                 optional=False,
                 default=None,
                 value_min=None,
                 value_max=None):
        # TODO: Throw exception on invalid values
        self.config_type = config_type
        self.desc = desc
        self.default = default
        self.value_min = value_min
        self.value_max = value_max

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
        self._pre_execute()
        self.execute()
        self._post_execute()
    
    @classmethod
    def single_file_input(cls):
        #change this to true if all input must come from the same file.
        return False

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
                'Sensor': {'SomeValue':OutputDescriptor('int', 'some_output/value'),
                           'SomeOtherValue':OutputDescriptor('boolean', 'some_output/value),
                           'SomeString':OutputDescriptor('string', 'some_output/string)}}
        """

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

    @abstractmethod
    def report(self):
        """describe output"""


class DrivenApplicationBaseClass(DriverApplicationBaseClass, metaclass=ABCMeta):
    @classmethod
    def single_file_input(cls):
        return True

    def execute(self):
        '''Iterate over input calling run each time'''
        pass

    @classmethod
    @abstractmethod
    def inputs(cls):
        return True

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
        self.terminate = terminate

    def command(self, point, value):
        self.commands[point]=value

    def log(self, message, level=logging.DEBUG):
        self.log_messages.append((level, message))

    def terminate(self, terminate):
        self.terminate = bool(terminate)

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
