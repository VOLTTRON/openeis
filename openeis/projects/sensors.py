'''
This python module contains sensor definitions for the openeis application.  It contains
a json generation tool for generating a static .json file for use in the client application.
'''
from _ctypes import ArgumentError

class Sensor:
    """
    Base class for all sensors in OpenEis
    """
    
    #__metaclass__ = Sensors
    
    def __init__(self, **kwargs):
        """
        Initialize a sensor object.  
        """
        self._unit_type = kwargs.pop('unit_type', None)
        if self.unit_type == None:
            raise ArgumentError('unit_type is required for sensor instance.')
        self._data_type = kwargs.pop('data_type', 'float')
        self._maximum = kwargs.pop('maximum', None)
        self._minimum = kwargs.pop('minimum', None)

    @property
    def sensor_type(self):
        return self.__class__
                    
    @property
    def minimum(self):
        """
        Returns the minimum value for the sensor.
        """
        return self._minimum
    

    @minimum.setter
    def minimum(self, value):
        """
        Sets the minimum value for the sensor.  If minimum is None then
        there is no minimum.
        """
        self._minimum = value


    @property
    def maximum(self):
        """
        Returns the maximum value of the sensor.
        """
        return self._maximum
    
    
    @maximum.setter
    def maximum(self, value):
        """
        Sets the maximum value for the sensor.  If maximum is None
        then the sensor has no maximum.
        """
        self._maximum = value     


    @property
    def unit_type(self):
        return self._unit_type

    
    @unit_type.setter
    def unit_type(self, value):
        self._unit_type = value

        
    @property
    def data_type(self):
        return self._data_type

    
    @data_type.setter
    def data_type(self, value):
        self._data_type = value

        
    @property
    def to_json(self):
        pass

CondenserFanPower = type("CondenserFanPower", (Sensor,), {'unit_type':'energy', 'data_type':"boolean"})
DischargeAirRelativeHumidity = type("DischargeAirRelativeHumidity", (Sensor,), {'unit_type':'dimensionless'})
DischargeAirTemperature = type("DischargeAirTemperature", (Sensor,),  {"unit_type": "temperature", 'data_type':"boolean"})
EconomizerMode = type("EconomizerMode", (Sensor,), {'unit_type':'dimensionless'})
FirstStageCooling = type("FirstStageCooling", (Sensor,), {"unit_type": "temperature"})
FirstStageHeating = type("FirstStageHeating", (Sensor,), {"unit_type": "temperature"})
MixedAirRelativeHumidity = type("MixedAirRelativeHumidity", (Sensor,), {'unit_type':'dimensionless'})
MixedAirTemperature = type("MixedAirTemperature", (Sensor,), {"unit_type": "temperature"})
OccupancyMode = type("OccupancyMode", (Sensor,), {'unit_type':'dimensionless'})
OutdoorAirRelativeHumidity = type("OutdoorAirRelativeHumidity", (Sensor,), {"unit_type": "dimensionless"})
OutdoorAirTemperature = type("OutdoorAirTemperature", (Sensor,), {"unit_type": "temperature"})
OutdoorDamperSignal = type("OutdoorDamperSignal", (Sensor,), {'unit_type':'dimensionless'})
ReturnAirRelativeHumidity = type("ReturnAirRelativeHumidity", (Sensor,), {'unit_type':'dimensionless'})
ReturnAirTemperature = type("ReturnAirTemperature", (Sensor,), {"unit_type": "temperature"})
SecondStageCooling = type("SecondStageCooling", (Sensor,), {"unit_type": "temperature"})
SecondStageHeating = type("SecondStageHeating", (Sensor,), {"unit_type": "temperature"})
SupplyFanPower = type("SupplyFanPower", (Sensor,), {"unit_type": "energy"})
SupplyFanSpeed = type("SupplyFanSpeed", (Sensor,), {'unit_type':'dimensionless'})
TotalPower = type("TotalPower", (Sensor,), {"unit_type": "energy"})
ZoneSetpoint = type("ZoneSetpoint", (Sensor,), {"unit_type": "temperature"})
ZoneTemperature = type("ZoneTemperature", (Sensor,), {"unit_type": "temperature"})

building_sensors = {}
site_sensors ={}
system_sensors = {}
sensors = {}

sensors = {
           "CondenserFanPower": CondenserFanPower(),
           "DischargeAirRelativeHumidity": DischargeAirRelativeHumidity(),
           "DischargeAirTemperature": DischargeAirTemperature(),
           "EconomizerMode": EconomizerMode(),
           "FirstStageCooling": FirstStageCooling(),
           "FirstStageHeating": FirstStageHeating(),
           "MixedAirRelativeHumidity": MixedAirRelativeHumidity(),
           "MixedAirTemperature": MixedAirTemperature(),
           "OccupancyMode": OccupancyMode(),
           "OutdoorAirRelativeHumidity": OutdoorAirRelativeHumidity(),
           "OutdoorAirTemperature": OutdoorAirTemperature(),
           "OutdoorDamperSignal": OutdoorDamperSignal(),
           "ReturnAirRelativeHumidity": ReturnAirRelativeHumidity(),
           "ReturnAirTemperature": ReturnAirTemperature(),
           "SecondStageCooling": SecondStageCooling(),
           "SecondStageHeating": SecondStageHeating(),
           "SupplyFanPower": SupplyFanPower(),
           "SupplyFanSpeed": SupplyFanSpeed(),
           "TotalPower": TotalPower(),
           "ZoneSetpoint": ZoneSetpoint(),
           "ZoneTemperature":ZoneTemperature
           }
           


def generate_static_json():
    pass



