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
def energy_signature_datafile(project):
    return create_data_file(os.path.join(abs_file_dir, 'energy_signature_data.csv'), 
                            project=project,
                            comments='energy signature test data.')
@pytest.fixture
def basic_datamap(project):
    return create_datamap(project, "onetofive", "fivetoone")

@pytest.fixture
def basic_dataset(project, basic_datamap, energy_signature_datafile):
    return create_dataset(name='Energy Signature Datamap', project=project, 
                          datamap=basic_datamap, 
                          files={'0': energy_signature_datafile})
    
@pytest.fixture
def missing_datamap(project):
    return create_datamap(project, "floats", "missing")

@pytest.fixture
def missing_dataset(project, missing_datamap, energy_signature_datafile):
    return create_dataset(name='Energy Signature Datamap', project=project, 
                          datamap=missing_datamap, 
                          files={'0': energy_signature_datafile})
    
    
def create_datamap(project, power_column, outdoor_air_column):
    return models.DataMap.objects.create(project=project, name="Heat Data Map",
        map={"files": {
                "0": {
                    "signature": {
                        "headers": ["datetime",
                        "onetofive",
                        "fivetoone",
                        "floats",
                        "missing",
                        "samenumber",
                        "floatsandmissing",
                        "break"]
                    },
                    "timestamp": {
                        "columns": [0]
                    }
                }
            },
            "version": 1,
            "sensors": {
                "lbnl/bldg90/WholeBuildingPower": {
                    "file": "0",
                    "type": "WholeBuildingPower",
                    "column": power_column,
                    "unit": "kilowatt"
                },
                "lbnl/bldg90": {
                    "level": "building"
                },
                "lbnl": {
                    "level": "site"
                },
                "lbnl/bldg90/OutdoorAirTemperature": {
                    "file": "0",
                    "type": "OutdoorAirTemperature",
                    "column": outdoor_air_column,
                    "unit": "fahrenheit"
                }
            }
        })
    