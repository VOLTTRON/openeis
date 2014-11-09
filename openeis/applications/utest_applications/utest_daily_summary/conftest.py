import os
import pytest

from openeis.projects import models
from openeis.applications.utest_applications.conftest import (project,
                                                              create_data_file,
                                                              create_dataset,
                                                              active_user)  

abs_file_dir = os.path.join(os.path.dirname(__file__))

@pytest.fixture
def daily_summary_datafile(project):
    return create_data_file(os.path.join(abs_file_dir, 'daily_summary_data.csv'), 
                            project=project,
                            comments='Daily Summary test data.')

@pytest.fixture
def daily_summary_sensor_dataset(project, daily_summary_datamap, daily_summary_datafile):
    return create_dataset(name='Daily Summary Datamap', project=project, 
                          datamap=daily_summary_datamap, files={'0': daily_summary_datafile})
    
@pytest.fixture
def daily_summary_datamap(project):
    return models.DataMap.objects.create(project=project, name="Daily Summary Map",
        map={
            
            "sensors": {
                "lbnl/bldg90/WholeBuildingElectricity": {
                    "column": "samenumber",
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
                            "withmissing", 
                            "samenumber", 
                            "floats", 
                            "missingandfloats"
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