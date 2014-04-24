'''
Created on Apr 23, 2014

'''
from abc import ABCMeta,abstractmethod
from schema.schema import sensordata

class InputDescriptor:
    
    def __init__(self,
                 sensor_type,
                 desc,
                 minimum=1,
                 maximum=1):
        #TODO: check and throw exception if self.sensor_data is none
        self.sensor_data = sensordata.get(sensor_type)
        self.desc = desc
        self.minimum = minimum
        if(maximum is not None and minimum > maximum):
            maximum = minimum
        self.maximum = maximum
        

class DriverBaseClass(metaclass=ABCMeta):
    
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
                    'CFP1':InputDescriptor('CondenserFanPower','Roof OATs',minimum=3,maximum=None)
                }
        """
    
    @classmethod
    @abstractmethod
    def output_format(cls):
        """output schema description
           {TableName1: {name1:type1, name2:type2,...},....}
           eg: {'OAT': {'Timestamp':datetime,'OAT':float}, 
                'Sensor': {'SomeValue':int, 'SomeOtherValue':boolean}} 
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
                'output_label': (str, None)
            }
        """
    
    @abstractmethod
    def run(self,inp,out):
        "runs algorithm"