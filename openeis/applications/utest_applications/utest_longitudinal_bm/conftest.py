import os
import pytest
import itertools

from openeis.applications.utest_applications.fixture_support import (project, 
                                                                      active_user,
                                                                      create_dataset,
                                                                      create_data_file)
from openeis.projects import (models, views) 

abs_file_dir = os.path.join(os.path.dirname(__file__))

@pytest.fixture
def longitudinal_bm_datafile(project):
    return create_data_file(os.path.join(abs_file_dir, 'longitudinal_bm_data.csv'), 
                            project=project,
                            comments='longitudinal_bm_datafile test data.')
@pytest.fixture
def basic_datamap(project):
    return create_datamap(project, "onetofive", 'onetofive')

@pytest.fixture
def basic_dataset(project, basic_datamap, longitudinal_bm_datafile):
    return create_dataset(name='longitudinal_bm_datafile Datamap', project=project, 
                          datamap=basic_datamap, 
                          files={'0': longitudinal_bm_datafile})
    
@pytest.fixture
def missing_datamap(project):
    return create_datamap(project, "missing", "missing")

@pytest.fixture
def missing_dataset(project, missing_datamap, longitudinal_bm_datafile):
    return create_dataset(name='longitudinal_bm_datafile Datamap', project=project, 
                          datamap=missing_datamap, 
                          files={'0': longitudinal_bm_datafile})

@pytest.fixture
def floats_datamap(project):
    return create_datamap(project, "floats", 'floats')

@pytest.fixture
def floats_dataset(project, floats_datamap, longitudinal_bm_datafile):
    return create_dataset(name='longitudinal_bm_datafile Datamap', project=project, 
                          datamap=floats_datamap, 
                          files={'0': longitudinal_bm_datafile})

@pytest.fixture
def floats_missing_datamap(project):
    return create_datamap(project, "floatsandmissing", 'floatsandmissing')

@pytest.fixture
def floats_missing_dataset(project, floats_missing_datamap, longitudinal_bm_datafile):
    return create_dataset(name='longitudinal_bm_datafile Datamap', project=project, 
                          datamap=floats_missing_datamap, 
                          files={'0': longitudinal_bm_datafile})

def create_datamap(project, gas_column, power_column):
    return models.DataMap.objects.create(project=project, name="Longitudinal_BM Map",
        map={
             "sensors": {
                "lbnl/bldg90/WholeBuildingGas": {
                    "column": gas_column,
                    "unit": "kilobtus_per_hour",
                    "file": "0",
                    "type": "WholeBuildingGas"
                },
                "lbnl/bldg90/WholeBuildingPower": {
                    "column": power_column,
                    "unit": "kilowatt",
                    "file": "0",
                    "type": "WholeBuildingPower"
                },
                "lbnl": {
                    "level": "site"
                },
                "lbnl/bldg90": {
                    "level": "building"
                }
            },
            "files": {
                "0": {
                    "signature": {
                        "headers": [
                            "datetime", 
                            "onetofive", 
                            "floats", 
                            "missing", 
                            "floatsandmissing"
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
    