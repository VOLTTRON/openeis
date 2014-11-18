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
def whole_building_datafile(project):
    return create_data_file(os.path.join(abs_file_dir, 'whole_building_energy_savings_data.csv'), 
                            project=project,
                            comments='whole building energy test data.')
@pytest.fixture
def base_datamap(project):
    return create_datamap(project)

@pytest.fixture
def base_dataset(project, base_datamap, whole_building_datafile):
    return create_dataset(name='Energy Signature Datamap', project=project, 
                          datamap=base_datamap, 
                          files={'0': whole_building_datafile})
    
    
def create_datamap(project):
    return models.DataMap.objects.create(project=project, name="Whole Building Map",
        map={
            
            "sensors": {
                "test_site/test_bldg":{
                    "level":"building"
                }, 
                "test_site/test_bldg/OutdoorAirTemperature":{
                    "type":"OutdoorAirTemperature", 
                    "file":"0", 
                    "unit":"fahrenheit", 
                    "column":"out-temp-F"
                },
                "test_site/test_bldg/WholeBuildingPower": {
                    "column": "whole-bldg-elec-W",
                    "unit":"kilowatt",
                    "type": "WholeBuildingPower",
                    "file": "0"
                },
                "test_site":{
                    "level":"site"
                }
            },
            "files": {
                "0": {
                    "signature": {
                        "headers": [
                            "datetime", 
                            "whole-bldg-elec-W", 
                            "out-temp-F"
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
    