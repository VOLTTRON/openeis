import json
import posixpath
import random
import string

from django.contrib.auth.models import User
from django.db import models
from django.core.exceptions import ValidationError

from .protectedmedia import ProtectedFileSystemStorage


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
        except ValueError:
            raise ValidationError('Invalid JSON data')
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


#class UnitType(models.Model):   
#    unit_type_group = models.TextField()
#    
#class Unit(models.Model):
#    key = models.TextField()
#    value = models.TextField()
#    other = models.TextField()
#    unit_type = models.ForeignKey(UnitType, related_name="units")
#        
#class ValidateOnSaveMixin(object):
#    def save(self, force_insert=False, force_update=False, **kwargs):
#        if not (force_insert or force_update):
#            self.full_clean()
#        super(ValidateOnSaveMixin, self).save(force_insert, force_update,
#                                              **kwargs)
#
#def validate_path_name(value):
#    if '/' in value:
#        raise ValidationError("{} contains an invalid character".format(value))
#    
#class SensorTree(models.Model):
#    parent = models.ForeignKey("self")
#    name = models.CharField(max_length=100, validators=[validate_path_name])
#    extra = JSONField()
#    # site, building, system, subsystem
#    level = models.CharField(max_length=20)
#    
#    class Meta:
#        unique_together = ('name', 'map_definition')
#    
#    @property
#    def full_path(self):
#        names = []
#        node = self
#        while node:
#            names.append(node.name)
#            node = node.parent
#        names.reverse()
#        return '/'.join(names)
#    
#    def __str__(self):
#        return self.name
#    
#    def __repr__(self):
#        return '<{}: {}>'.format(self.__class__.__name__, self.full_path)
# 
#
#class MapDefinition(models.Model):    
#    root = models.ForeignKey(SensorTree)
#    name = models.CharField(max_length=100)
#    extra = JSONField()
#    project = models.ForeignKey(Project)
#    
#    class Meta:
#        unique_together = ('name', 'project')
#    
#    def __str__(self):
#        return self.name
#    
#    def __repr__(self):
#        return '<{}: {}>'.format(self.__class__.__name__, self.name)
#
#    
#class SensorMapFile(models.Model):
#    name = models.CharField(max_length=100)
#    extra = JSONField()
#    signature = models.CharField(max_length=32)
#    ts_fields = models.CharField(max_length=255)
#    ts_format = models.CharField(max_length=32)
#    map_definition = models.ForeignKey(MapDefinition, related_name="map_files")
#    
#    class Meta:
#        unique_together = ('name', 'map_definition')
#    
#    def __str__(self):
#        return self.name
#    
#    def __repr__(self):
#        return '<{}: {}>'.format(self.__class__.__name__, self.name)
#
#    
#class Sensor(models.Model):
#    name = models.CharField(max_length=100, validators=[validate_path_name])
#    extra = JSONField()
#    tree = models.ForeignKey(SensorTree, related_name="sensors")
#    extra = models.TextField()
#    source_file = models.ForeignKey(SensorMapFile)
#    source_column = models.CharField(max_length=255)
#    unit_key = models.CharField(max_length=50)
#    type_key = models.CharField(max_length=50)
#    
#    class Meta:
#        unique_together = ('name', 'tree')
#    
#    @property
#    def full_path(self):
#        names = [self.name]
#        node = self.tree
#        while node:
#            names.append(node.name)
#            node = node.parent
#        names.reverse()
#        return '/'.join(names)
#    
#    def __str__(self):
#        return self.name
#    
#    def __repr__(self):
#        return '<{}: {}>'.format(self.__class__.__name__, self.full_path)
#
# 
#class Table(models.Model):
#    """
#    A Table is akin to a csv file.
#    """
#    name = models.CharField(max_length=30)
#    row_count = models.PositiveIntegerField(default=0)
# 
#class TableColumn(models.Model):
#    table = models.ForeignKey(Table, related_name="columns")
#    column = models.AutoField(primary_key=True)
#    name = models.CharField(max_length=30)
#    db_type = models.CharField(max_length=30)
#    oeis_type = models.CharField(max_length=30)
#    
#class BaseTableData(models.Model):
#    row = models.IntegerField()
#    column = models.ForeignKey(TableColumn)
#    table = models.ForeignKey(Table) 
#    
#    class Meta:
#        abstract = True
# 
#class IntTableData(BaseTableData):
#    value = models.IntegerField() 
#     
#class FloatTableData(BaseTableData):
#    value = models.FloatField() 
#     
#class StringTableData(BaseTableData):
#    value = models.TextField() 
#     
#class BooleanTableData(BaseTableData):
#    value = models.BooleanField() 
#     
#class TimeTableData(BaseTableData):
#    value=models.DateTimeField()     
