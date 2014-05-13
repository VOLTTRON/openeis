'''
Created on Apr 23, 2014

'''
from abc import ABCMeta,abstractmethod
from schema.schema import sensordata

class InputDescriptor:
    
    def __init__(self,
                 sensor_type,
                 desc,
                 count=1,
                 maximum=1,
                 _id=None):
        #TODO: check and throw exception if self.sensor_data is none
        self.sensor_data = sensordata.get(sensor_type)
        self.desc = desc
        self.count = count
        if(maximum is not None and count > maximum):
            maximum = count
        self.maximum = maximum
        
class OutputDescriptor:
    
    def __init__(self,
                 output_type,
                 topic):
        #TODO: check and throw exception if self.sensor_data is none
        self.output_type = sensordata.get(sensor_type)
        self.topic = topic
        

class DriverApplicationBaseClass(metaclass=ABCMeta):
    
    def __init__(self,inp=None,out=None,**kwargs):
        super().__init__(**kwargs)
        self.inp = inp
        self.out = out
    
    @classmethod
    @abstractmethod
    def required_input(cls):
        """required input schema
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
                    'OAT2':InputDescriptor('OutdoorAirTemperature','Roof OATs',minimum=3)
                    'CFP1':InputDescriptor('CondenserFanPower','CFP Desc',minimum=3,maximum=None)
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
           
           eg: {'OAT': {'Timestamp':OutputDescriptor('timestamp', 'foo/bar/timestamp),'OAT':OutputDescriptor('OutdoorAirTemperature', 'foo/bar/oat')}, 
                'Sensor': {'SomeValue':OutputDescriptor('int', 'some_output/value), 'SomeOtherValue':OutputDescriptor('boolean', 'some_output/value)}} 
        """
        
    @classmethod
    @abstractmethod
    def get_config_parameters(cls):
        """default config schema description
            {
                'Key1':(Type1,DefaultValue1),
                'Key2':(Type2,DefaultValue2)
            }
            
            e.g.: 
            {
                'matemp_missing': (int,0),
                'mat_low': (float, 50.4)
                'output_label': (str, '')
            }
        """
    
    @abstractmethod
    def run(self):
        "runs algorithm"