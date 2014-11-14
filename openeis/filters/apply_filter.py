import datetime
from openeis.projects import models
from openeis.filters import column_modifiers

def apply_filter_config(dataset_id,config):
    
    sensoringest = models.SensorIngest.objects.get(pk=dataset_id)
    datamap = sensoringest.map
    sensors = list(datamap.sensors.all())
    sensor_names = [s.name for s in sensors]
    sensordata = [sensor.data.filter(ingest=sensoringest) for sensor in sensors]
    generators = {} 
    for name, qs in zip(sensor_names, sensordata):
        #TODO: Add data type from schema
        value = {"gen":_iter_data(qs),
                 "type":None}
        generators[name] = value
        
    generators, errors = _create_and_update_filters(generators, config)
    
    if errors:
        return errors
    
    datamap.id = None 
    datamap.name = datamap.name+' version - '+str(datetime.datetime.now())
    datamap.save()
    
    sensoringest.name = str(sensoringest.id) + ' - '+str(datetime.datetime.now())
    sensoringest.id = None
    sensoringest.map = datamap
    sensoringest.save()
    
    for sensor in sensors:
        sensor.id= None
        sensor.map = datamap
        sensor.save()
        data_class = sensor.data_class
        generator = generators[sensor.name]['gen']
        sensor_data_list = []
        for time,value in generator:
            sensor_data = data_class(sensor=sensor, ingest=sensoringest,
                                     time=time, value=value)
            sensor_data_list.append(sensor_data)
            if len(sensor_data_list) >= 1000:
                data_class.objects.bulk_create(sensor_data_list)
                sensor_data_list = []
        if sensor_data_list:
            data_class.objects.bulk_create(sensor_data_list)
            
    return datamap.id

def _iter_data(sensordata):
    for data in sensordata:
        if data.value is not None:
            yield data.time, data.value
            
def _create_and_update_filters(generators, configs):
    errors = []
    
    print("column mods: ", column_modifiers)
    
    for topic, filter_name, filter_config in configs:
        if not isinstance(topic, str):
            topic = topic[0]
        parent_filter_dict = generators.get(topic)
        if parent_filter_dict is None:
            errors.append('Invalid Topic for DataMap: ' + str(topic))
            continue
        
        parent_filter = parent_filter_dict['gen']
        parent_type = parent_filter_dict['type']
        
        filter_class = column_modifiers.get(filter_name)
        if filter_class is None:
            errors.append('Invalid filter name: ' + str(filter_name))
            continue
        
        try:
            new_filter = filter_class(parent=parent_filter, **filter_config)
        except Exception as e:
            errors.append('Error configuring filter: '+str(e))
            continue
            
        value = parent_filter_dict.copy()
        
        value['gen']=new_filter
        value['type']=parent_type
        
        generators[topic] = value
    
    return generators, errors
