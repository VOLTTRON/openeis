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

'''
Created on Apr 28, 2014

- assumes that each algo run would create a new table with a unique id
TODO: import database Table object and TableColumn object from Django database model

example input map:

input_map =
{
    'OAT_TEMPS': ('topic1','topic2', 'topic3'),
    'OCC_MODE': ('topic4',)
}
'''

from collections import defaultdict
from datetime import datetime, timedelta
import logging

import pytz

from .. import models

_logger = logging.getLogger(__name__)

MAX_DATE =  pytz.utc.localize(datetime.max - timedelta(days=5))


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
        # if "All" in topic:
        #     topic = topic[:topic.index("/All")]
        #     first_meta = datamap['sensors'][topic]
        #     if 'type' in first_meta:
        #         for k, v in datamap['sensors'].items():
        #             if 'type' in v:
        #                 if v['type'] == first_meta['type']:
        #                     meta = v
        #                     sensor = mapdef.sensors.get(name=k)
        #                     def get_queryset():
        #                         return sensor.data
        #                     result.append((meta, get_queryset))
        #     else:
        #         raise "The 'All' option does not support meta without type"
        # else:
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


class DatabaseInput:

    def __init__(self, datamap_id, topic_map, dataset_id=None):
        '''
        Expected topic_map:
        {
            'OAT_TEMPS': ('topic1','topic2', 'topic3'),
            'OCC_MODE': ('topic4',)
        }
        '''

        self.topic_map = topic_map.copy()
        self.dataset_id = dataset_id
        self.data_map = {}
        self.sensor_meta_map = {}
        self.topic_meta = {}
        mapdef = models.DataMap.objects.get(pk=datamap_id)
        self.map_defintion = mapdef.map

        for input_name, topics in self.topic_map.items():
            for topic in topics:
                if "All" in topic:
                    topic = topic[:topic.index("/All")]
                    self.topic_map[input_name] = []
                    first_meta = self.map_defintion['sensors'][topic]
                    if 'type' in first_meta:
                        for k, v in self.map_defintion['sensors'].items():
                            if 'type' in v:
                                if v['type'] == first_meta['type']:
                                    self.topic_map[input_name].append(k)
        #{'zonetemp': ['ZoneBuilding/AHU1/Zone3/ZoneTemperature', 'ZoneBuilding/AHU1/Zone2/ZoneTemperature'],
        # 'fan_airflow': [], 'occupancy': [], 'zone_temp_setpoint': [], 'damper_position': []}
        for input_name, topics in self.topic_map.items():
            self.data_map[input_name] = tuple(get_sensors(datamap_id,x)[0] for x in topics)

        for input_name, topics in self.topic_map.items():
            self.topic_meta[input_name] = {}
            for topic in topics:
                self.topic_meta[input_name][topic] = get_sensors(datamap_id,topic)[0][0]
                self.topic_meta[input_name][topic]['timezone'] = self.get_tz_for_sensor(topic)

    def get_topics(self):
        return self.topic_map.copy()

    def get_sensormap(self):
        return self.map_defintion

    def get_tz_for_sensor(self, sensor_topic):
        #pop off base of topic
        base = sensor_topic.split('/')[0]
        
        #TODO: better warnings
        if (base in self.map_defintion['sensors'] and 
            'attributes' in self.map_defintion['sensors'][base].keys() and
            'timezone' in self.map_defintion['sensors'][base]['attributes'].keys()):
            tz = pytz.timezone(self.map_defintion['sensors'][base]['attributes']['timezone'])
        else:
            #_logger.warning(("No timezone for sensor", sensor_topic))
            tz = pytz.UTC
            
        return tz
    
    def localize_sensor_time(self, sensor_topic, timestamp):
        #Set utc if time is naive
        if timestamp.tzinfo == None:
            timestamp = timestamp.replace(tzinfo=pytz.UTC)
            
        tz = self.get_tz_for_sensor(sensor_topic)
        timestamp = timestamp.astimezone(tz)
        return timestamp

    def get_topics_meta(self):
        '''Returns topics with their meta data'''
        return self.topic_meta.copy()

    def get_start_end_times(self):
        """Return a tuple of datetime objects representing the start and end times of the data."""
        pass

    @staticmethod
    def merge(*args, drop_partial_lines=True, fill_in_data=None):
        '''
            args  - one or more results returned from get_query_sets() method
            drop_partial_lines - whether to drop incomplete sets, missing values are represented by None
        '''
        def merge_drop():
            "Drop incomplete rows"
            managed_query_sets = []

            for arg in args:
                for group, query_set_list in arg.items():
                    for query_set in query_set_list:
                        managed_query_sets.append((group,query_set.__iter__()))
            current = [x[1].__next__() for x in managed_query_sets]
            newest = max(current, key=lambda x:x[0] )[0]

            while True:
                if all(x[0] == newest for x in current):
                    result = defaultdict(list)
                    result['time']  = newest
                    for value, query in zip(current, managed_query_sets):
                        result[query[0]].append(value[1])

                    yield result
                    current = [x[1].__next__() for x in managed_query_sets]
                    newest = max(current, key=lambda x:x[0] )[0]
                else:
                    new_current = []
                    terminate = False
                    for value, query in zip(current, managed_query_sets):
                        if value[0] == newest:
                            new_current.append(value)
                        else:
                            try:
                                new_current.append(query[1].__next__())
                            except StopIteration:
                                terminate = True
                                break
                    if terminate:
                        break
                    current = new_current
                    newest = max(current, key=lambda x:x[0] )[0]

        def merge_no_drop():
            "Incomplete rows provide a None for missing values."
            managed_query_sets = []

            for arg in args:
                for group, query_set_list in arg.items():
                    for query_set in query_set_list:
                        managed_query_sets.append((group,query_set.__iter__()))
            current = [x[1].__next__() for x in managed_query_sets]
            oldest = min(current, key=lambda x:x[0] )[0]

            while True:
                result = defaultdict(list)
                result['time']  = oldest

                for value, query in zip(current, managed_query_sets):
                    if value[0] == oldest:
                        result[query[0]].append(value[1])
                    else:
                        result[query[0]].append(None)

                yield result
                new_current = []
                for value, query in zip(current, managed_query_sets):
                    if value[0] != oldest:
                        new_current.append(value)
                    else:
                        try:
                            new_current.append(query[1].__next__())
                        except StopIteration:
                            new_current.append((MAX_DATE,None))
                current = new_current
                oldest = min(current, key=lambda x:x[0] )[0]
                if oldest == MAX_DATE:
                    break


        return merge_drop() if drop_partial_lines else merge_no_drop()

    @staticmethod
    def merge_fill_in_data(*args, drop_partial_lines=True, fill_in_data=None):
        "Incomplete rows provide last known reading for missing values or None if no good value"
        #pass in a timedelta to advance time
        managed_query_sets = []

        latest_value = []

        for arg in args:
            for group, query_set_list in arg.items():
                for query_set in query_set_list:
                    managed_query_sets.append((group,query_set.__iter__()))
                    latest_value.append(None)
        current = [x[1].__next__() for x in managed_query_sets]
        oldest = min(current, key=lambda x:x[0] )[0]

        while True:
            result = defaultdict(list)
            result['time']  = oldest
            index = 0
            for value, query in zip(current, managed_query_sets):

                if value[0] == oldest:
                    result[query[0]].append(value[1])
                    latest_value[index] = value[1]
                else:
                    result[query[0]].append(latest_value[index])

                index += 1

            yield result
            new_current = []
            for value, query in zip(current, managed_query_sets):
                if value[0] != oldest:
                    new_current.append(value)
                else:
                    try:
                        new_current.append(query[1].__next__())
                    except StopIteration:
                        new_current.append((MAX_DATE,None))
            current = new_current
            oldest = min(current, key=lambda x:x[0] )[0]
            if oldest == MAX_DATE:
                break




    def get_query_sets(self, group_name,
                       order_by='time',
                       filter_=None,
                       exclude=None,
                       wrap_for_merge=False,
                       group_by=None, group_by_aggregation=None):
        """
        group - group of columns to retrieve.
        order_by - column to order_by ('time' or 'values'), defaults to 'time'
        filter_ - dictionary of filter() arguments
        exclude - dictionary of exclude() arguments

        wrap_for_merge - wraps the result in a dictionary ready to pass to self.merge().
                         Defaults to False

        group_by - period to group by
                   valid arguments are "minute", "hour" "day" "month" "year" "all"
                   "all" returns the aggregated value and not a query set.
                   wrap_for_merge has no effect on "all" output.

        group_by_aggregation - Aggregation method to use. Defaults to None.
                               See https://docs.djangoproject.com/en/1.6/ref/models/querysets/#aggregation-functions


        returns => {group:result list} if wrap_for_merge is True
        otherwise returns => result list
        """
        qs = (x() for _,x in self.data_map[group_name])

        if self.dataset_id is not None:
            qs = (x.filter(ingest_id=self.dataset_id) for x in qs)

        if filter_ is not None:
            qs = (x.filter(**filter_) for x in qs)

        if exclude is not None:
            qs = (x.exclude(**exclude) for x in qs)

        if group_by is not None:
            if group_by != 'all':
                pass
#                 qs = (x.group_by(group_by, group_by_aggregation) for x in qs)
            else:
                return [x.aggregate(value=group_by_aggregation('value'))['value'] for x in qs]

        result = [x.order_by(order_by).timeseries(trunc_kind=group_by,
                                        aggregate=group_by_aggregation) for x in qs]

        return {group_name:result} if wrap_for_merge else result

#     def timeseries(self, *, trunc_kind=None, aggregate=None):
#         '''Return timeseries pairs from the table.
#
#         Returns 2-tuples of time-value pairs. If trunc_kind is given,
#         the time is truncated to the given precision. If aggregate is
#         given, the series values are aggregated according to the given
#         aggregation method and grouped by the time.
#         '''

if __name__ == '__main__':

    args = []

    t = {'OAT':[[(datetime(2000,1,1,8,0,0), 50.0),
                 (datetime(2000,1,1,9,0,0), 51.0),
                 (datetime(2000,1,1,10,0,0), 52.0)
                ],
                [(datetime(2000,1,1,8,0,0), 50.0),
                 (datetime(2000,1,1,9,0,0), 50.0),
                 (datetime(2000,1,1,10,0,0), 52.0)
                ]]}

    args.append(t)

    t = {'Energy':[[(datetime(2000,1,1,8,0,0), 100),
                 (datetime(2000,1,1,9,0,0), 100),
                 (datetime(2000,1,1,10,0,0), 100)
                ]]}

    args.append(t)

    print('Test merge no drop')
    for result in DatabaseInput.merge(*args,drop_partial_lines=False):
        print(result)

    print('Test merge with drop')
    for result in DatabaseInput.merge(*args):
        print(result)

    args = []

    t = {'OAT':[[(datetime(2000,1,1,8,0,0), 50.0),
                 (datetime(2000,1,1,9,0,0), 51.0),
                 (datetime(2000,1,1,10,0,0), 52.0)
                ],
                [(datetime(2000,1,1,8,0,0), 50.0),
                 (datetime(2000,1,1,9,0,0), 50.0),
                 (datetime(2000,1,1,10,0,0), 52.0)
                ]]}

    args.append(t)

    t = {'Energy':[[
                (datetime(2000,1,1,8,0,0), 100),
                 (datetime(2000,1,1,10,0,0), 100)
                ]]}

    args.append(t)


    print('Test merge no drop with missing timestamp in middle')
    for result in DatabaseInput.merge(*args,drop_partial_lines=False):
        print(result)

    print('Test merge with drop  with missing timestamp in middle')
    for result in DatabaseInput.merge(*args):
        print(result)

    args = []

    t = {'OAT':[[(datetime(2000,1,1,8,0,0), 50.0),
                 (datetime(2000,1,1,9,0,0), 51.0),
                 (datetime(2000,1,1,10,0,0), 52.0)
                ],
                [(datetime(2000,1,1,8,0,0), 50.0),
                 (datetime(2000,1,1,9,0,0), 50.0),
                 (datetime(2000,1,1,10,0,0), 52.0)
                ]]}

    args.append(t)

    t = {'Energy':[[
                    (datetime(2000,1,1,9,0,0), 100),
                    (datetime(2000,1,1,10,0,0), 100)
                ]]}

    args.append(t)


    print('Test merge no drop with missing first timestamp')
    for result in DatabaseInput.merge(*args,drop_partial_lines=False):
        print(result)

    print('Test merge with drop  with missing first timestamp')
    for result in DatabaseInput.merge(*args):
        print(result)

    args = []

    t = {'OAT':[[(datetime(2000,1,1,8,0,0), 50.0),
                 (datetime(2000,1,1,9,0,0), 51.0),
                 (datetime(2000,1,1,10,0,0), 52.0)
                ],
                [(datetime(2000,1,1,8,0,0), 50.0),
                 (datetime(2000,1,1,9,0,0), 50.0),
                 (datetime(2000,1,1,10,0,0), 52.0)
                ]]}

    args.append(t)

    t = {'Energy':[[(datetime(2000,1,1,8,0,0), 100),
                    (datetime(2000,1,1,9,0,0), 100),
                    ]]}

    args.append(t)


    print('Test merge no drop with missing last timestamp')
    for result in DatabaseInput.merge(*args,drop_partial_lines=False):
        print(result)

    print('Test merge with drop  with missing last timestamp')
    for result in DatabaseInput.merge(*args):
        print(result)


