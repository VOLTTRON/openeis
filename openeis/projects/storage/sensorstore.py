'''
Created on May 14, 2014

This module will contain the api associated with the application/algorithm storing
and retrieving data.
'''

from .. import models

def put_output():
    pass

def put_sensors(sensormap_id, topicstreams):
    '''
    Persists a sensors data to the datastore.  At this point the topicstreams have
    been validated as correct and will now be persisted in the database.
    Arguments:
        sensormap_id - references a SensorMapDefinition.  The SensorMapDefinition
                       will be used to formulate how to reference specific columns
                       of data.
                       
        topicstreams - A list of topic, stream pairs
                       Ex
                       [
                           {
                               'topics': ['OAT', 'OAT2'],
                               'stream': streamableobject
                            },
                            {
                                'topics': ['OAT4'],
                                'stream': streamableobject
                            }
                        ]                                
    '''
    pass



def get_sensors(sensormap_id, topics):
    '''
    Get sensors returns a list of two-tuples.   The first element in the
    tuple will be a meta object that will hold the mapping definition and
    the sensor definition.  The second element will be a function that will
    take no arguments and will return a new queryset.  The queryset will hold
    two columns of data, the time and the data point value.  
    '''
    if isinstance(topics, str):
        topics = [topics]
    result = []
    mapdef = models.SensorMapDefinition.objects.get(pk=sensormap_id)
    sensormap = mapdef.map
    for topic in topics:
        meta = sensormap['sensors'][topic]
        # XXX: Augment metadata by adding general definition properties
        if 'type' in meta:
            sensor = mapdef.sensors.get(name=topic)
            def get_queryset():
                return sensor.data
        else:
            get_queryset = None
        result.append((meta, get_queryset))
    return result


def __generate_table_name(sensormap):
    pass

if __name__ == '__main__':
    pass
