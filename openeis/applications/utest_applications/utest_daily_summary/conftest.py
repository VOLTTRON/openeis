import os
import pytest

from openeis.applications.utest_applications.conftest import (project,
                                                              create_data_file,
                                                              create_dataset)  

abs_file_dir = os.path.join(os.path.dirname(__file__))

@pytest.fixture
def daily_summary_datafile(project):
    return create_data_file(os.path.join(abs_file_dir, 'energy_signature_data.csv'), 
                            project=project,
                            comments='Energy signature test data data.')