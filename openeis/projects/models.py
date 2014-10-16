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

import contextlib
import datetime
import json
import jsonschema
import posixpath
import random
import string

from django.contrib.auth.models import User
from django.db import connections, models
from django.db.models.query import QuerySet
from django.core.exceptions import ValidationError
from django import dispatch

import jsonschema.exceptions

from .protectedmedia import ProtectedFileSystemStorage
from .storage import sensormap
from .storage.csvfile import CSVFile


class JSONString(str):
    pass


class JSONField(models.TextField, metaclass=models.SubfieldBase):

    description = 'JSON encoded object'

    def to_python(self, value):
        if value is None or value == '':
            return value
        if not isinstance(value, str) or isinstance(value, JSONString):
            return value
        try:
            result = json.loads(value)
        except ValueError as e:
            raise ValidationError('Invalid JSON data: {}'.format(e))
        if isinstance(result, str):
            return JSONString(result)
        return result

    def get_prep_value(self, value):
        try:
            return json.dumps(value, separators=(',', ':'))
        except TypeError:
            raise ValidationError('Cannot serialize object to JSON')

    def value_to_string(self, obj):
        return super()._get_val_from_obj(obj)



class Organization(models.Model):
    '''Group and manage users by organization.'''

    name = models.CharField(max_length=100)
    members = models.ManyToManyField(
            User, through='Membership', related_name='organizations')

    def __str__(self):
        return self.name


class Membership(models.Model):
    '''Intermediate table for Organization/User relationship.'''

    organization = models.ForeignKey(Organization)
    user = models.ForeignKey(User)
    is_admin = models.BooleanField(verbose_name='Administrator status',
            help_text='Designates whether the user can manage organization '
                      'membership.')

    class Meta:
        verbose_name_plural = 'Membership'

    def __str__(self):
        return '{} {} of {}'.format(
                self.user.get_full_name() or '@' + self.user.username,
                'administrator' if self.is_admin else 'member',
                self.organization)


class Project(models.Model):
    '''Organizes and groups a users files, mappings, and results.'''

    name = models.CharField(max_length=100)
    owner = models.ForeignKey(User, related_name='projects')

    def __str__(self):
        return self.name


def _data_file_path(instance, filename):
    name = ''.join(random.choice(_CODE_CHOICES) for i in range(32))
    return posixpath.join('projects', 'datafiles', name)


class DataFile(models.Model):
    '''Represents an uploaded data file to feed applications.'''

    _ts_schema = {
        "type": "object",
        "required": ["columns"],
        "properties": {
            "columns": {
                "oneOf": [
                    {
                        "type": "array",
                        "items": {
                            "oneOf": [
                                {"type": "string"},
                                {"type": "integer", "minimum": 0}
                            ]
                        },
                        "minItems": 1,
                        "uniqueItems": True
                    },
                    {"type": "string"},
                    {"type": "integer", "minimum": 0}
                ]
            },
            "format": {"type": ["string"]}
        },
        "additionalProperties": False
    }

    FORMAT_CHOICES = (('csv', 'CSV'), ('greenbutton', 'GreenButton'))


    project = models.ForeignKey(Project, related_name='files')
    name = models.CharField(max_length=100)
    format = models.CharField(max_length=32, choices=FORMAT_CHOICES,default='csv')
    file = models.FileField(
            upload_to=_data_file_path, storage=ProtectedFileSystemStorage())
    uploaded = models.DateTimeField(
            auto_now_add=True, help_text='Date and time file was uploaded')
    comments = models.CharField(max_length=255, blank=True)
    timestamp = JSONField(blank=True)
    time_zone = models.CharField(max_length=64, blank=True)
    time_offset = models.FloatField(default=0)

    def __str__(self):
        return self.file.name

    def csv_head(self, count=15):
        file = self.file
        if file.closed:
            file.open()
        rows = []
        with contextlib.closing(file):
            csv_file = CSVFile(file)
            if (csv_file.has_header):
                count += 1;
            for row in csv_file:
                rows.append(row)
                if len(rows) >= count:
                    break
            return csv_file.has_header, rows

    def clean_fields(self, exclude=None):
        '''Validate JSON against schema.'''
        super().clean_fields(exclude=exclude)
        if (exclude and 'timestamp' in exclude or
                self.timestamp is None or self.timestamp == ''):
            return
        validator = jsonschema.Draft4Validator(self._ts_schema)
        try:
            validator.validate(self.timestamp)
        except jsonschema.ValidationError as e:
            raise ValidationError({'timestamp' + ''.join('[{!r}]'.format(name)
                                   for name in e.path): [e.message]})


_CODE_CHOICES = string.ascii_letters + string.digits

def _verification_code():
    return ''.join(random.choice(_CODE_CHOICES) for i in range(50))


class AccountVerification(models.Model):
    account = models.ForeignKey(User)
    initiated = models.DateTimeField(auto_now_add=True)
    code = models.CharField(max_length=50, unique=True,
                            default=_verification_code)
    what = models.CharField(max_length=20)
    data = JSONField(blank=True)


class DataMap(models.Model):
    project = models.ForeignKey(Project, related_name='datamaps')
    name = models.CharField(max_length=100)
    map = JSONField()
    removed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('project', 'name')

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<{}: {}, {}>'.format(
                self.__class__.__name__, self.project, self.name)

    def clean_fields(self, exclude=None):
        '''Validate JSON against data map schema.'''
        super().clean_fields(exclude=exclude)
        if exclude and 'map' in exclude:
            return
        schema = sensormap.Schema()
        errors = schema.validate(self.map)
        if not errors:
            return
        raise ValidationError({('map' + ''.join('[{!r}]'.format(name)
                                for name in path)): value
                               for path, value in errors.items()})


class SensorIngest(models.Model):
    project = models.ForeignKey(Project, related_name='datasets')
    name = models.CharField(max_length=100)
    map = models.ForeignKey(DataMap, related_name='datasets')
    # time of ingest
    start = models.DateTimeField(auto_now_add=True)
    end = models.DateTimeField(null=True, default=None)

    def merge(self, start=None, end=None, include_header=True):
        '''Return an iterator over the merged dataset.

        If start is an integer, skip start rows. If start is a datetime
        object, include only rows with times greater than or equal to the
        start time. If end is an integer, return no more than that number
        of rows. If end is a date, include only rows less than the end time.
        If include_header is True (the default), also add a header row at
        the top.
        '''
        def _iter_data(data):
            '''Helper generator to aid in merging columns. Expects to be
            accessed twice per row. The first call yields the time of the
            next item or None if none remain.  The second call should send
            the time of the current row and will yield the item if the
            time matches the current item and advance the iterator or
            None otherwise.
            '''
            for i in data:
                while True:
                    time = (yield i.time)
                    if i.time == time:
                        yield i
                        break
                    yield None
            while True:
                yield None
        sensors = list(self.map.sensors.order_by('name'))
        data = [sensor.data.filter(ingest=self) for sensor in sensors]
        # Filter by start and end times
        if isinstance(start, datetime.datetime):
            data = [d.filter(time__gte=start) for d in data]
        if isinstance(end, datetime.datetime):
            data = [d.filter(time__lt=end) for d in data]
        def _merge():
            iterators = [_iter_data(d) for d in data]
            while True:
                try:
                    time = min(t for t in (next(i) for i in iterators) if t)
                except ValueError:
                    break
                yield [time] + [d and d.value for d in [i.send(time) for i in iterators]]
        generator = _merge()
        # Filter by start row and end count
        if isinstance(start, int):
            iterator = iter(generator)
            for i in range(start):
                next(iterator)
        if not isinstance(end, int):
            end = None
        if include_header:
            yield ['time'] + [sensor.name for sensor in sensors]
        for i, row in enumerate(generator):
            if end and i >= end:
                break
            yield row


@dispatch.receiver(models.signals.post_delete, sender=SensorIngest)
def handle_dataset_delete(sender, instance, using, **kwargs):
    datamap = instance.map
    if datamap and datamap.removed and not datamap.datasets.exists():
        datamap.delete()


class SensorIngestFile(models.Model):
    ingest = models.ForeignKey(SensorIngest, related_name='files')
    # name matches a file in the data map definition
    name = models.CharField(max_length=255)
    file = models.ForeignKey(DataFile, related_name='ingests',
                             null=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = ('ingest', 'name')


INFO = 20
WARNING = 30
ERROR = 40
CRITICAL = 50
class SensorIngestLog(models.Model):
    
    LOG_LEVEL_CHOICES = ((INFO, 'Info'), (WARNING, 'Warning'),
                         (ERROR, 'Error'), (CRITICAL, 'Critical'))

    dataset = models.ForeignKey(SensorIngest, related_name='logs')
    file = models.ForeignKey(SensorIngestFile, related_name='logs', null=True)
    row = models.IntegerField()
    # Timestamps can include multiple columns
    column = models.CommaSeparatedIntegerField(max_length=20)
    level = models.SmallIntegerField(choices=LOG_LEVEL_CHOICES)
    message = models.CharField(max_length=255)


class Sensor(models.Model):
    BOOLEAN = 'b'
    FLOAT = 'f'
    INTEGER = 'i'
    STRING = 's'

    DATA_TYPE_CHOICES = ((BOOLEAN, 'boolean'), (FLOAT, 'float'),
                         (INTEGER, 'integer'), (STRING, 'string'))

    map = models.ForeignKey(DataMap, related_name='sensors')
    # name matches the sensor path in the definition
    name = models.CharField(max_length=255)
    data_type = models.CharField(max_length=1, choices=DATA_TYPE_CHOICES)

    class Meta:
        unique_together = ('map', 'name')

    @property
    def data(self):
        return getattr(self, self.get_data_type_display() + 'sensordata_set')

    @property
    def data_class(self):
        return globals()[self.get_data_type_display().capitalize() + 'SensorData']


class SensorDataQuerySet(QuerySet):
    class pg_trunc(dict):
        def __missing__(self, key):
            if key not in {'minute', 'hour', 'day', 'month', 'year'}:
                raise KeyError(key)
            return "date_trunc('{0}', {{field}})".format(key)

    trunc_funcs = {
        "mysql": {
            "year": "strftime('%%Y', {field})",
            "month": "strftime('%%Y-%%m', {field})",
            "day": "strftime('%%Y-%%m-%%d', {field})",
            "hour": "strftime('%%Y-%%m-%%d %%H', {field})",
            "minute": "strftime('%%Y-%%m-%%d %%H:%%i', {field})",
        },
        "oracle": {
            "year": "trunc({field}, 'YEAR')",
            "month": "trunc({field}, 'MONTH')",
            "day": "trunc({field}, 'DAY')",
            "hour": "trunc({field}, 'HH24')",
            "minute": "trunc({field}, 'MI')",
        },
        "postgresql": pg_trunc(),
        "sqlite": {
            "year": "strftime('%%Y', {field})",
            "month": "strftime('%%Y-%%m', {field})",
            "day": "strftime('%%Y-%%m-%%d', {field})",
            "hour": "strftime('%%Y-%%m-%%d %%H', {field})",
            "minute": "strftime('%%Y-%%m-%%d %%H:%%M', {field})",
        },
    }

    def trunc_date(self, kind, *args, **kwargs):
        '''Truncate a date field to the level indicated by kind.

        kind must be one of 'year', 'month', 'day', 'hour', or 'minute'.
        args and kwargs contain field names to truncate. Names in args
        retain the same name while those in values of kwargs get named
        according to the key.
        '''
        backend = connections[self.db].vendor
        try:
            trunc = self.trunc_funcs[backend]
        except KeyError:
            raise NotImplementedError('group_by is not implemented for the '
                                      '{} database backend'.format(backend))
        try:
            func = trunc[kind]
        except KeyError:
            raise ValueError('invalid truncation kind: {}'.format(kind))
        for arg in args:
            if arg in kwargs:
                raise ValueError('field given twice: {}'.format(arg))
            kwargs[arg] = arg
        select = {dest: func.format(field=source)
                  for dest, source in kwargs.items()}
        return self.extra(select=select) if select else self

    def timeseries(self, *, trunc_kind=None, aggregate=None):
        '''Return timeseries pairs from the table.

        Returns 2-tuples of time-value pairs. If trunc_kind is given,
        the time is truncated to the given precision. If aggregate is
        given, the series values are aggregated according to the given
        aggregation method and grouped by the time.
        '''
        queryset = self
        if trunc_kind:
            queryset = queryset.trunc_date(trunc_kind, 'time')
        if aggregate:
            queryset = queryset.values('time').annotate(value=aggregate('value'))
        return queryset.values_list('time', 'value')


class SensorDataManager(models.Manager):
    def get_queryset(self):
        return SensorDataQuerySet(self.model)
    @property
    def timeseries(self):
        return self.get_queryset().timeseries
    @property
    def trunc_date(self):
        return self.get_queryset().trunc_date



class BaseSensorData(models.Model):
    sensor = models.ForeignKey(Sensor)
    ingest = models.ForeignKey(SensorIngest)
    time = models.DateTimeField()

    class Meta:
        abstract = True
        ordering = ['time']
        get_latest_by = 'time'


class BooleanSensorData(BaseSensorData):
    value = models.NullBooleanField()
    objects = SensorDataManager()

class FloatSensorData(BaseSensorData):
    value = models.FloatField(null=True)
    objects = SensorDataManager()

class IntegerSensorData(BaseSensorData):
    value = models.IntegerField(null=True)
    objects = SensorDataManager()

class StringSensorData(BaseSensorData):
    value = models.TextField(null=True)
    objects = SensorDataManager()


class Analysis(models.Model):
    '''A run of a single application against a single dataset.'''

    project = models.ForeignKey(Project, related_name='analyses')
    name = models.CharField(max_length=100)
    dataset = models.ForeignKey(SensorIngest, related_name='analyses',
        null=True, on_delete=models.SET_NULL)
    application = models.CharField(max_length=255)
    '''
    Expected configuration to be a json string like
    {
        "inputs": {
            "key": ["ISB1/OutdoorAirTemperature","TOPIC2"]
        },
        "parameters": {
            "config1": "value1",
            "config2": intvalue
        }
    }
    '''
    configuration = JSONField()
    debug = models.BooleanField(default=False)
    # Ran successfully or not
    status = models.CharField(max_length=50, default='queued')
    # Initially queued
    added = models.DateTimeField(auto_now_add=True)
    started = models.DateTimeField(null=True, default=None)
    ended = models.DateTimeField(null=True, default=None)
    progress_percent = models.FloatField(default=0)
    reports = JSONField()


def _share_key():
    return ''.join(random.choice(_CODE_CHOICES) for i in range(16))


class SharedAnalysis(models.Model):
    analysis = models.OneToOneField(Analysis, primary_key=True)
    key = models.CharField(max_length=16, default=_share_key)


class AppOutput(models.Model):
    analysis = models.ForeignKey(Analysis, related_name='app_output')
    name = models.CharField(max_length=255)
    fields = JSONField()
