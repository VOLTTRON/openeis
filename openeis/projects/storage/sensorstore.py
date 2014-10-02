# -*- coding: utf-8 -*- {{{
# vim: set fenc=utf-8 ft=python sw=4 ts=4 sts=4 et:
#
# Copyright (c) 2014, Battelle Memorial Institute
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.
#
#
# This material was prepared as an account of work sponsored by an
# agency of the United States Government.  Neither the United States
# Government nor the United States Department of Energy, nor Battelle,
# nor any of their employees, nor any jurisdiction or organization
# that has cooperated in the development of these materials, makes
# any warranty, express or implied, or assumes any legal liability
# or responsibility for the accuracy, completeness, or usefulness or
# any information, apparatus, product, software, or process disclosed,
# or represents that its use would not infringe privately owned rights.
#
# Reference herein to any specific commercial product, process, or
# service by trade name, trademark, manufacturer, or otherwise does
# not necessarily constitute or imply its endorsement, recommendation,
# or favoring by the United States Government or any agency thereof,
# or Battelle Memorial Institute. The views and opinions of authors
# expressed herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY
# operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830
#
#}}}

'''Routines for storing and retrieving application/algorithm data.'''

import threading

from django.db.models import Manager as BaseManager

from .. import models
from . import dynamictables


_create_lock = threading.Lock()


def get_data_model(output, project_id, fields):
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
    openeis.projects.storage.dynamictables._fields. The same fields must
    be passed in as was supplied for create_output(). The resulting
    model will automatically fill in the source field with the given
    output and the manager will automatically filter the queryset by the
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
    attrs = {'source': models.models.ForeignKey(
                 models.AppOutput, related_name='+'),
             'objects': Manager(), '__init__': __init__, 'save': save}
    # Append PK to name since Django caches models by name
    model = dynamictables.create_model('AppOutputData' + str(output.pk),
            'appoutputdata', project_id, fields, attrs)
    with _create_lock:
        if not dynamictables.table_exists(model):
            dynamictables.create_table(model)
    return model


def put_sensors(datamap_id, topicstreams):
    '''Persists a sensors data to the datastore.

    At this point the topicstreams have been validated as correct and
    will now be persisted in the database.

    Arguments:
        datamap_id - references a DataMap.  The DataMap will be used to
                     formulate how to reference specific columns of data.

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


def get_sensors(datamap_id, topics):
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
    mapdef = models.DataMap.objects.get(pk=datamap_id)
    datamap = mapdef.map
    for topic in topics:
        meta = datamap['sensors'][topic]
        # XXX: Augment metadata by adding general definition properties
        if 'type' in meta:
            sensor = mapdef.sensors.get(name=topic)
            def get_queryset():
                return sensor.data
        else:
            get_queryset = None
        result.append((meta, get_queryset))
    return result
