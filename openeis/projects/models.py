import json
import posixpath
import random
import string

from django.contrib.auth.models import User
from django.db import models
from django.db.models.query import QuerySet
from django.core.exceptions import ValidationError

import jsonschema.exceptions

from .protectedmedia import ProtectedFileSystemStorage
from .storage import sensormap


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
    return posixpath.join('projects', str(instance.project.pk), filename)


class DataFile(models.Model):
    '''Represents an uploaded data file to feed applications.'''

    project = models.ForeignKey(Project, related_name='files')
    file = models.FileField(
            upload_to=_data_file_path, storage=ProtectedFileSystemStorage())
    uploaded = models.DateTimeField(
            auto_now_add=True, help_text='Date and time file was uploaded')
    comments = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.file.name


class JSONString(str):
    pass


class JSONField(models.TextField, metaclass=models.SubfieldBase):

    description = 'JSON encoded object'

    def to_python(self, value):
        if not value:
            return None
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


class SensorMapDefinition(models.Model):
    project = models.ForeignKey(Project, related_name='sensor_maps')
    name = models.CharField(max_length=100)
    map = JSONField()

    class Meta:
        unique_together = ('project', 'name')

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<{}: {}, {}>'.format(
                self.__class__.__name__, self.project, self.name)

    def clean_fields(self, exclude=None):
        '''Validate JSON against sensor map schema.'''
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
    

class TableDataQuerySet(QuerySet):
    sqlite_querys = {
                     "minute":"""strftime('%%Y-%%m-%%d %%H:%%M', time_stamp)""",
                     "hour":"""strftime('%%Y-%%m-%%d %%H', time_stamp)""",
                     "day":"""strftime('%%Y-%%m-%%d', time_stamp)""",
                     #"week":"""strftime('%%Y-%%m %W', time_stamp)""",
                     "month":"""strftime('%%Y-%%m', time_stamp)""",
                     "year":"""strftime('%%Y', time_stamp)""",
                     }
    
    is_sqlite = False
    
    def group_by(self, period, func):  
        if period not in self.sqlite_querys:
            raise ValueError('Invalid Period for grouping.')   
        if self.is_sqlite:
            select_data = {'d':self.sqlite_querys[period]}
        else:
            #Relax people... We validate the period above.
            select_data = {'d':"""date_trunc({0},time_stamp)""".format(period)}
            
        q = self.extra(select = select_data).values('d').annotate(aggregated_value=func('values'))
        return q

class TableDataManager(models.Manager):
    def get_query_set(self):
        return TableDataQuerySet(self.model)
    def __getattr__(self, name):
        return getattr(self.get_query_set(), name)