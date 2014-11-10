
import itertools
import os.path
import pytest

from configparser import ConfigParser

from openeis.projects import (models, views)

@pytest.fixture
def admin_user():
    '''Creates an administrator user.'''
    return models.User.objects.create(username='admin', password='password',
            is_superuser=True, is_staff=True, email='admin@example.com')

@pytest.fixture
def staff_user():
    '''Creates a usernamed staff with the password 'password'''
    return models.User.objects.create(username='staff', password='password',
            is_superuser=False, is_staff=True, email='staff@example.com')

@pytest.fixture
def active_user():
    '''Creates an active user in the database and returns it.'''
    return models.User.objects.create(username='active', password='password',
            is_superuser=False, is_staff=False, email='active@example.com')

@pytest.fixture
def inactive_user():
    '''Creates an inactive user and returns it.'''
    return models.User.objects.create(username='inactive', password='password',
            is_active=False, is_superuser=False, is_staff=False,
            email='inactive@example.com')


@pytest.fixture
def organization(staff_user, active_user):
    '''Creates an organization 'Test Organization' and adds the staff user and active user to it'''
    return models.Organization.objects.create(
            name='Test Organization', members=[staff_user, active_user])

@pytest.fixture
def project(active_user):
    '''Uses the injected active_user and creates a 'Test Project' in the 
    database, returns it'''
    return models.Project.objects.create(owner=active_user, name='Test Project')

def build_config_parser(app_name, dataset_id, sensormap_id):
    '''
    This function creates a config parser with the specified dataset and
    sensormap_id. 
    '''
    config = ConfigParser()
    
    config.add_section("global_settings")
    config.set("global_settings", 'application', app_name)
    config.set("global_settings", 'dataset_id', str(dataset_id))
    config.set("global_settings", 'sensormap_id', str(sensormap_id))
    
    config.add_section("application_config")
    config.set('application_config', 'building_sq_ft', '3000')
    config.set('application_config', 'building_name', '"bldg90"')
    
    config.add_section('inputs')
    config.set('inputs', 'load', 'lbnl/bldg90/WholeBuildingElectricity')
    
    return config

def create_data_file(name_or_full_path, **kwargs):
    '''Creates a data file object from the passed name_or_full_path.  
    
    If name_or_full_path is a rooted path, a file and exists then the file object 
    will be named the os.path.filename(name_or_full_path).  If name is a filename 
    then it is assumed that the model/fixtures folder will contain the passed 
    filename.
    '''    
    name = name_or_full_path
    # if name is rooted and the file exists then a full path to the 
    # file was pased to the directory.
    if os.path.isabs(name_or_full_path) and os.path.isfile(name_or_full_path):
        name = os.path.basename(name_or_full_path)
    
    obj = models.DataFile.objects.create(name=name, **kwargs)
    
        
    obj.file = obj.file.field.generate_filename(obj, name)
    
    # The user passed a full path
    if name != name_or_full_path:
        path = name_or_full_path
    else:
        path = os.path.join(os.path.dirname(models.__file__), 'fixtures', name)
    
    # Write file to the storage path.
    with obj.file.storage.open(obj.file.path, 'wb') as dst, \
            open(path, 'rb') as src:
        while True:
            buf = src.read(4096)
            if not buf:
                break
            dst.write(buf)
    obj.save()
    return obj


@pytest.fixture
def datafile_1month(project):
    return create_data_file('1Month_hourly.csv', project=project,
                            comments='One month of data.')

@pytest.fixture
def datafile_1month_pst(project):
    return create_data_file('1Month_hourly.csv', project=project,
            comments='One month of data with PST time zone.',
            time_zone='America/Los_Angeles')

@pytest.fixture
def datafile_1month_offset(project):
    return create_data_file('1Month_hourly.csv', project=project,
            comments='One month of data offset 30 minutes.', time_offset=1800)

@pytest.fixture
def datafile_4year(project):
    return create_data_file('test_4year.csv', project=project,
                            comments='Four years of data.')


@pytest.fixture
def datamap(project):
    return models.DataMap.objects.create(project=project, name='Test Data Map',
        map={
            "sensors": {
                "Test/WholeBuildingElectricity": {
                    "column": "Main Meter [kW]",
                    "unit": "kilowatt",
                    "type": "WholeBuildingElectricity",
                    "file": "0"
                },
                "Test/OutdoorAirTemperature": {
                    "column": "Hillside OAT [F]",
                    "unit": "fahrenheit",
                    "type": "OutdoorAirTemperature",
                    "file": "0"
                },
                "Test": {
                    "level": "building"
                }
            },
            "files": {
                "0": {
                    "signature": {
                        "headers": [
                            "Date",
                            "Hillside OAT [F]",
                            "Main Meter [kW]",
                            "Boiler Gas [kBtu/hr]"
                        ]
                    },
                    "timestamp": {
                        "columns": [
                            0
                        ]
                    }
                }
            },
            "version": 1
        })


@pytest.fixture
def mixed_datamap(datamap):
    map = datamap.map
    map['sensors']['Test/OutdoorAirTemperature']['file'] = '1'
    map['files']['1'] = map['files']['0']
    return models.DataMap.objects.create(project=datamap.project,
            name='Mixed Data Map', map=map)

def create_dataset(name, project, datamap, files):
    dataset = models.SensorIngest.objects.create(
            project=project, name=name, map=datamap)
    for name, file in files.items():
        models.SensorIngestFile.objects.create(
                ingest=dataset, name=name, file=file)
    keyfunc = lambda obj: obj.__class__.__name__
    it = views.iter_ingest(dataset)
    while True:
        batch = []
        for objects, *args in it:
            batch.extend(objects)
            if len(batch) >= 1000:
                break
        if not batch:
            break
        batch.sort(key=keyfunc)
        for class_name, group in itertools.groupby(batch, keyfunc):
            objects = list(group)
            cls = objects[0].__class__
            cls.objects.bulk_create(objects)
    return dataset

@pytest.fixture
def dataset(project, datamap, datafile_1month):
    return create_dataset(
            'Test Data Set', project, datamap, {'0': datafile_1month})

@pytest.fixture
def mixed_dataset(project, mixed_datamap,
        datafile_1month, datafile_1month_offset):
    return create_dataset(
            'Mixed Data Set', project, mixed_datamap,
            {'0': datafile_1month, '1': datafile_1month_offset})
