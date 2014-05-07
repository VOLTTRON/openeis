import json
import posixpath
import random
import string

from django.contrib.auth.models import User
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from .protectedmedia import ProtectedFileSystemStorage
from .validation import is_valid_name

DEFAULT_CHAR_MAX_LEN = 30

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

class UnitType(models.Model):   
    unit_type_group = models.CharField(max_length=DEFAULT_CHAR_MAX_LEN)
    
class Unit(models.Model):
    key = models.CharField(max_length=DEFAULT_CHAR_MAX_LEN)
    value = models.CharField(max_length=DEFAULT_CHAR_MAX_LEN)
    other = models.CharField(max_length=DEFAULT_CHAR_MAX_LEN)
    unit_type = models.ForeignKey(UnitType, related_name="units")
        
class ValidateOnSaveMixin(object):
    def save(self, force_insert=False, force_update=False, **kwargs):
        if not (force_insert or force_update):
            self.full_clean()
        super(ValidateOnSaveMixin, self).save(force_insert, force_update,
                                              **kwargs)
    
    
class Site(ValidateOnSaveMixin, models.Model):
    """
    Site specific data.
    """    
    site_name = models.CharField(max_length=DEFAULT_CHAR_MAX_LEN )
    site_address = models.CharField(max_length=DEFAULT_CHAR_MAX_LEN, null=True, blank=True)
    site_city = models.CharField(max_length=DEFAULT_CHAR_MAX_LEN, null=True, blank=True)
    site_state = models.CharField(max_length=DEFAULT_CHAR_MAX_LEN, null=True, blank=True)
    
    def is_valid(self):
        """
        The site must have a valid name.
        
        raises ValidationError if the data is not valid
        """
        if not is_valid_name(self.site_name):
            raise ValidationError("Invalid site name specified!")
        
        return True
    
    def clean(self):
        """
        This will be called when the object is saved.
        """        
        self.is_valid()
        
        
class Building(ValidateOnSaveMixin, models.Model):
    building_name = models.CharField(max_length=DEFAULT_CHAR_MAX_LEN)
    site = models.ForeignKey(Site, related_name='sites')   
    building_address = models.CharField(max_length=DEFAULT_CHAR_MAX_LEN, null=True, blank=True)
    building_city = models.CharField(max_length=DEFAULT_CHAR_MAX_LEN, null=True, blank=True)
    building_state = models.CharField(max_length=DEFAULT_CHAR_MAX_LEN, null=True, blank=True)
    
    
    def is_valid(self):
        """
        The site must have a valid name.
        
        raises ValidationError if the data is not valid
        """
        if not is_valid_name(self.building_name):
            raise ValidationError("Invalid site name specified!")
        if not isinstance(self.site, Site):
            raise ValidationError("Site object must be specified!")
        
        return True
    
    def clean(self):
        """
        This will be called when the object is saved.
        """        
        self.is_valid()
        
        
             

    
class SystemType(ValidateOnSaveMixin, models.Model):
    "Specifies the classification of a specific system i.e. RTU"
    system_name = models.CharField(max_length=DEFAULT_CHAR_MAX_LEN)
    system_type = models.CharField(max_length=DEFAULT_CHAR_MAX_LEN)


class System(ValidateOnSaveMixin, models.Model):
    system_name = models.CharField(max_length=DEFAULT_CHAR_MAX_LEN)
    system_type = models.ForeignKey(SystemType)


# class SubSystem(models.Model):
#     parent = models.ForeignKey(System)
    

class SensorType(ValidateOnSaveMixin, models.Model):
    sensor_type_name = models.CharField(max_length=DEFAULT_CHAR_MAX_LEN)
    unit_type = models.ForeignKey(UnitType)
        
    
class Sensor(ValidateOnSaveMixin, models.Model):
    
    # See for details about Generic Relations that we are dealing with here
    # for the first time.
    #
    # The following three fields allow the parent to be one of Site,
    # Buildng, or System.
    content_type = models.ForeignKey(ContentType, null=True)
    object_id = models.PositiveIntegerField()
    parent_object = generic.GenericForeignKey('content_type', 'object_id')
    
    sensor_type = models.ForeignKey(SensorType)
    
    # https://docs.djangoproject.com/en/dev/topics/db/models/#abstract-base-classes
    # Abstract becaus we have common information but the value is going to be of a different
    # type between the classes.
    class Meta:
        abstract=True

 
class Table(models.Model):
    """
    A Table is akin to a csv file.
    """
    name = models.CharField(max_length=30)
    row_count = models.PositiveIntegerField(default=0)
 
class TableColumn(models.Model):
    table = models.ForeignKey(Table, related_name="columns")
    column = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30)
    db_type = models.CharField(max_length=30)
    oeis_type = models.CharField(max_length=30)
    
class BaseTableData(models.Model):
    row = models.IntegerField()
    column = models.ForeignKey(TableColumn)
    table = models.ForeignKey(Table) 
    
    class Meta:
        abstract = True
 
class IntTableData(BaseTableData):
    value = models.IntegerField() 
     
class FloatTableData(BaseTableData):
    value = models.FloatField() 
     
class StringTableData(BaseTableData):
    value = models.TextField() 
     
class BooleanTableData(BaseTableData):
    value = models.BooleanField() 
     
class TimeTableData(BaseTableData):
    value=models.DateTimeField()     
