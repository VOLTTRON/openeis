'''Routines for storing and retrieving application/algorithm data.'''

import threading

from django.db.models import Manager as BaseManager

from .. import models
from . import dynamictables


_create_lock = threading.Lock()


def create_output(analysis, name, fields):
    '''Create and return a model appropriate for application output.

    Dynamically generate a new AppOutput instance and a model with the
    given fields.
    '''
    output = models.AppOutput.objects.create(analysis=analysis, name=name)
    model = get_data_model(output, fields)
    with _create_lock:
        if not dynamictables.table_exists(model):
            dynamictables.create_table(model)
    return model


def get_data_model(output, fields):
    '''Return a model appropriate for application output.

    Dynamically generates a Django model for the given fields and binds
    it to the given project ID and output. output must either be an
    already saved instance of openeis.projects.models.AppOutput or the
    ID of of a saved instance. The project_id is not checked against the
    Project table; it is only useful for scoping the underlying tables
    by project. fields should be a dictionary or a list of 2-tuples that
    would be generated from an equivalent dictionary's items() method.
    Each field is defined by a name, which must be a valid Python
    identifier, and a type, which must be one of those mapped in
    openeis.projects.storage.dynamictables._fields. The same fields
    must be passed in as was supplied for create_output(). The resulting
    model will automatically fill in the source field with the given
    output and the manager will automatically filter the queryset by th
    given output.
    '''
    if isinstance(output, int):
        output = models.AppOutput.get(pk=output)
    def __init__(self, *args, **kwargs):
        kwargs['source'] = output
        super(self.__class__, self).__init__(*args, **kwargs)
    def save(self, *args, **kwargs):
        self.source = output
        super(self.__class__, self).save(*args, **kwargs)
    class Manager(BaseManager):
        def get_queryset(self):
            return super().get_queryset().filter(source=output)
    name = 'AppOutputData'
    project_id = output.analysis.dataset.map.project.id
    attrs = {'source': models.models.ForeignKey(
                 models.AppOutput, related_name='+'),
             '__name__': name, 'objects': Manager(),
             '__init__': __init__, 'save': save}
    return dynamictables._create_model(name, project_id, fields, attrs)


def put_output():
    pass


def put_sensors(sensormap_id, topicstreams):
    '''Persists a sensors data to the datastore.

    At this point the topicstreams have been validated as correct and
    will now be persisted in the database.

    Arguments:
        sensormap_id - references a SensorMapDefinition.  The
                       SensorMapDefinition will be used to formulate how
                       to reference specific columns of data.

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
    '''Get querysets for to given topics.

    get_sensors() returns a list of two-tuples. The first element is a
    meta object that will hold the mapping definition and the sensor
    definition. The second element is a function which takes no
    arguments and will return a new queryset. The queryset has two
    columns of data: the time and the data point value.
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
