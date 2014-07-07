'''
Created on Apr 28, 2014

- assumes that each algo run would create a new table with a unique id
TODO: import database Table object and TableColumn object from Django database model
'''

db_type_map = {
               "int":"inttabledata_set",
               "string":"stringtabledata_set",
               "float":"floattabledata_set",
               "boolean":"booleantabledata_set",
               "datetime":"timetabledata_set"
               }

'''
example input map:

input_map =
{
    'OAT_TEMPS': ('topic1','topic2', 'topic3'),
    'OCC_MODE': ('topic4',)
}

'''

from  django.db.models import Sum

#from foo import get_sensor

from datetime import datetime
from collections import defaultdict
from pprint import pprint
from openeis.projects.storage.sensorstore import get_sensors

class DatabaseInput:

    def __init__(self, sensormap_id, topic_map, dataset_ids=None):
        '''
        Expected topic_map:
        {
            'OAT_TEMPS': ('topic1','topic2', 'topic3'),
            'OCC_MODE': ('topic4',)
        }
        '''

        self.topic_map = topic_map.copy()

        self.dataset_ids = dataset_ids

        self.sensor_map = {}
        self.sensor_meta_map = {}
        for input_name, topics in self.topic_map.items():
            self.sensor_map[input_name] = tuple(get_sensors(sensormap_id,x)[0] for x in topics)

        self.topic_meta = {}

        for input_name, topics in self.topic_map.items():
            self.topic_meta[input_name] = {}
            for topic in topics:
                self.topic_meta[input_name][topic] = get_sensors(sensormap_id,topic)[0][0]

    def get_topics(self):
        return self.topic_map.copy()

    def get_topics_meta(self):
        '''Returns topics with their meta data'''
        return self.topic_meta.copy()

    def get_start_end_times(self):
        """Return a tuple of datetime objects representing the start and end times of the data."""
        pass

    @staticmethod
    def merge(*args, drop_partial_lines=True):
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
                            new_current.append((datetime.max,None))
                current = new_current
                oldest = min(current, key=lambda x:x[0] )[0]
                if oldest == datetime.max:
                    break


        return merge_drop() if drop_partial_lines else merge_no_drop()

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

        group_by_aggregation - Aggregation method to use. Defaults to Sum.
                               See https://docs.djangoproject.com/en/1.6/ref/models/querysets/#aggregation-functions


        returns => {group:result list} if wrap_for_merge is True
        otherwise returns => result list
        """
        qs = (x() for _,x in self.sensor_map[group_name])

        if self.dataset_ids is not None:
            qs = (x.filter(ingest_id__in=self.dataset_ids) for x in qs)

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


