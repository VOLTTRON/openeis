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
def one_month_datafile(project):
    return create_data_file(os.path.join(abs_file_dir, "fixtures", '1Month_hourly.csv'), 
                            project=project,
                            comments='Month hourly test data.')
    
    
@pytest.fixture
def one_month_datamap(project):
    return create_datamap(project)

@pytest.fixture
def one_month_dataset(project, one_month_datamap, one_month_datafile):
    return create_dataset(name='Month Hourly Datamap', project=project, 
                          datamap=one_month_datamap, 
                          files={'0': one_month_datafile})


def create_datamap(project):
    return models.DataMap.objects.create(project=project, name="Daily Summary Map",
        map={
            "sensors": {
                "lbnl":{
                    "attributes": {
                        "timezone": "US/Pacific"
                    },
                    "level":"site"
                },
                "lbnl/bldg90": {
                    "level": "building"
                },
                "lbnl/bldg90/OutdoorAirTemperature": {
                    "column": "Hillside OAT [F]",
                    "unit":"fahrenheit",
                    "type": "OutdoorAirTemperature",
                    "file": "0"
                },
                "lbnl/bldg90/WholeBuildingPower": {
                    "column": "Main Meter [kW]",
                    "unit":"kilowatt",
                    "type": "WholeBuildingPower",
                    "file": "0"
                },
                "lbnl/bldg90/WholeBuildingGas": {
                    "column": "Boiler Gas [kBtu/hr]",
                    "unit":"kilobtu",
                    "type": "WholeBuildingGas",
                    "file": "0"
                }
            },
            "files": {
                "0": {
                    "signature": {
                        "headers": [
                            "datetime", 
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
    