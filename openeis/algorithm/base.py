'''
Created on Apr 23, 2014

'''
from abc import ABCMeta,abstractmethod

class DriverBaseClass(metaclass=ABCMeta):
    
    @classmethod
    @abstractmethod
    def required_input(cls):
        "required input schema"
    
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
        "config schema description"
    
    @abstractmethod
    def run(self,inp,out):
        "runs algorithm"