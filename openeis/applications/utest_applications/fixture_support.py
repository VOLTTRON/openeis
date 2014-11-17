
import itertools
import os.path
import pytest

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

    config.set('inputs', 'load', 'lbnl/bldg90/WholeBuildingPower')

def create_data_file(path_and_name, **kwargs):
    if not os.path.exists(path_and_name):
        raise ValueError("Couldn't find file to create datafile\n"+ \
                         path_and_name)
    obj = models.DataFile.objects.create(name=os.path.basename(path_and_name), **kwargs)
    obj.file = obj.file.field.generate_filename(obj, path_and_name)
    path = path_and_name #os.path.join(os.path.dirname(models.__file__), 'fixtures', name)
    if not os.path.exists(os.path.dirname(obj.file.path)):
        os.makedirs(os.path.dirname(obj.file.path))
        
    with obj.file.storage.open(obj.file.path, 'wb') as dst, \
            open(path, 'rb') as src:
        while True:
            buf = src.read(4096)
            if not buf:
                break
            dst.write(buf)
    obj.save()
    return obj
    
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


