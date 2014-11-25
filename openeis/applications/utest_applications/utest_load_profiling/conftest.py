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
def load_profile_datafile(project):
    return create_data_file(os.path.join(abs_file_dir, 'load_profiling_data.csv'), 
                            project=project,
                            comments='Load Profiling test data.')

@pytest.fixture
def basic_datamap(project):
    return create_datamap(project, "onetofive")

@pytest.fixture
def basic_dataset(project, basic_datamap, load_profile_datafile):
    return create_dataset(name='Load Profiling Datamap', project=project, 
                          datamap=basic_datamap, 
                          files={'0': load_profile_datafile})

def create_datamap(project, column):
    return models.DataMap.objects.create(project=project, name="Load Profiling Map",
        map={
            "version": 1,
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
                        "columns": [0]
                    }
                }
            },
            "sensors": {
                "lbnl": {
                    "level": "site"
                },
                "lbnl/bldg90": {
                    "level": "building"
                },
                "lbnl/bldg90/WholeBuildingPower": {
                    "type": "WholeBuildingPower",
                    "column": "onetofive",
                    "unit": "kilowatt",
                    "file": "0"
                }
            }
        })