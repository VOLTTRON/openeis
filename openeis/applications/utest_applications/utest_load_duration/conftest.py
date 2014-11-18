import os
import pytest
import itertools

from openeis.applications.utest_applications.fixture_support import (project, 
                                                                     active_user,
                                                                     create_dataset,
                                                                     create_data_file)
from openeis.projects import models

abs_file_dir = os.path.join(os.path.dirname(__file__))


@pytest.fixture
def load_duration_datafile(project):
    return create_data_file(os.path.join(abs_file_dir, 'load_duration_data.csv'), 
                            project=project,
                            comments='load duration test data.')
@pytest.fixture
def basic_datamap(project):
    return create_datamap(project, "onetofive")

@pytest.fixture
def basic_dataset(project, basic_datamap, load_duration_datafile):
    return create_dataset(name='Load Duration Datamap', project=project, 
                          datamap=basic_datamap, 
                          files={'0': load_duration_datafile})
    
@pytest.fixture
def floats_datamap(project):
    return create_datamap(project, "floats")

@pytest.fixture
def floats_dataset(project, floats_datamap, load_duration_datafile):
    return create_dataset(name='Load Duration Datamap', project=project, 
                          datamap=floats_datamap, 
                          files={'0': load_duration_datafile})

@pytest.fixture
def missing_datamap(project):
    return create_datamap(project, "missing")

@pytest.fixture
def missing_dataset(project, missing_datamap, load_duration_datafile):
    return create_dataset(name='Load Duration Datamap', project=project, 
                          datamap=missing_datamap, 
                          files={'0': load_duration_datafile})

@pytest.fixture
def floats_missing_datamap(project):
    return create_datamap(project, "floatsandmissing")

@pytest.fixture
def floats_missing_dataset(project, floats_missing_datamap, load_duration_datafile):
    return create_dataset(name='Load Duration Datamap', project=project, 
                          datamap=floats_missing_datamap, 
                          files={'0': load_duration_datafile})


def create_datamap(project, column):
    return models.DataMap.objects.create(project=project, name="Load Duration Data Map",
                        map = {
                            "files": {
                                "0": {
                                    "timestamp": {
                                        "columns": [0]
                                    },
                                    "signature": {
                                        "headers": ["datetime",
                                        "onetofive",
                                        "floats",
                                        "missing",
                                        "floatsandmissing"]
                                    }
                                }
                            },
                            "sensors": {
                                "lbnl/bldg90": {
                                    "level": "building"
                                },
                                "lbnl": {
                                    "level": "site"
                                },
                                "lbnl/bldg90/WholeBuildingPower": {
                                    "unit": "kilowatt",
                                    "type": "WholeBuildingPower",
                                    "file": "0",
                                    "column": column
                                }
                            },
                            "version": 1
                        })