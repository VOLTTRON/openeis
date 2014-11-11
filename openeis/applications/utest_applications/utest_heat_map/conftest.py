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
def heatmap_datafile(project):
    return create_data_file(os.path.join(abs_file_dir, 'heat_map_data.csv'), 
                            project=project,
                            comments='heatmap test data.')
@pytest.fixture
def basic_datamap(project):
    return create_datamap(project, "onetofive")

@pytest.fixture
def basic_dataset(project, basic_datamap, heatmap_datafile):
    return create_dataset(name='Heatmap Datamap', project=project, 
                          datamap=basic_datamap, 
                          files={'0': heatmap_datafile})
    
@pytest.fixture
def floats_datamap(project):
    return create_datamap(project, "floats")

@pytest.fixture
def floats_dataset(project, floats_datamap, heatmap_datafile):
    return create_dataset(name='Heatmap Datamap', project=project, 
                          datamap=floats_datamap, 
                          files={'0': heatmap_datafile})


@pytest.fixture
def missing_datamap(project):
    return create_datamap(project, "missing")

@pytest.fixture
def missing_dataset(project, missing_datamap, heatmap_datafile):
    return create_dataset(name='Heatmap Datamap', project=project, 
                          datamap=missing_datamap, 
                          files={'0': heatmap_datafile})
    
@pytest.fixture
def floats_missing_datamap(project):
    return create_datamap(project, "floatsandmissing")

@pytest.fixture
def floats_missing_dataset(project, floats_missing_datamap, heatmap_datafile):
    return create_dataset(name='Heatmap Datamap', project=project, 
                          datamap=floats_missing_datamap, 
                          files={'0': heatmap_datafile})


    
def create_datamap(project, column):
    return models.DataMap.objects.create(project=project, name="Heat Data Map",
        map={
            
            "sensors": {
                "lbnl/bldg90/WholeBuildingElectricity": {
                    "column": column,
                    "unit":"kilowatt",
                    "type": "WholeBuildingElectricity",
                    "file": "0"
                },
                "lbnl":{
                    "level":"site"
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
    