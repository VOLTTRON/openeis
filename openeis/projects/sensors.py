'''
This python module loads sensor definitions from a json file for use within the openeis context.
'''
import json
import os
from _ctypes import ArgumentError

sensors = {}
building_sensors = {}
site_sensors = {}
systems = {}

# Path to the sensor_data.json file. 
sensor_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "static/projects/json/sensor_data.json")

def load_types():
    sensors.clear()
    building_sensors.clear()
    site_sensors.clear()
    systems.clear()
    
    jsonObj = json.load(open(sensor_data_path, 'r'))
    
    # First populate the sensors so that they can be referenced in the 
    # building and system objects.
    for child in jsonObj['sensors']:
        sensors[child] = type(child, (object,), jsonObj['sensors'][child])
    
    # building_sensors refrence only the types that are available for the
    # building.
    for child in jsonObj['building_sensors']['sensor_list']:
        building_sensors[child] = sensors[child]
    
    # site sensors reference only the types that are available at the site level.
    for child in jsonObj['site_sensors']['sensor_list']:
        site_sensors[child] = sensors[child]
    
    # build the systems so that tehy can be referenced by other systems
    for child in jsonObj['systems']:
        systems[child] = type(child, (object,), {'sensors':{}})
        sensor_list = {}
        for sensor_type_name in jsonObj['systems'][child]['sensor_list']:
            sensor_list[sensor_type_name] = sensors[sensor_type_name]
        
        systems[child].sensors = sensor_list #['sensors'].sensor_type_name = sensors[sensor_type_name]
    

load_types()




