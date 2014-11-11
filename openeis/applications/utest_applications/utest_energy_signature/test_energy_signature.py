# """
# Unit tests for Energy Signature application.
# 
# =======
# Copyright (c) 2014, The Regents of the University of California, Department
# of Energy contract-operators of the Lawrence Berkeley National Laboratory.
# All rights reserved.
# 
# 1. Redistribution and use in source and binary forms, with or without
#    modification, are permitted provided that the following conditions are met:
# 
#    (a) Redistributions of source code must retain the copyright notice, this
#    list of conditions and the following disclaimer.
# 
#    (b) Redistributions in binary form must reproduce the copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 
#    (c) Neither the name of the University of California, Lawrence Berkeley
#    National Laboratory, U.S. Dept. of Energy nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
# 
# 2. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#    AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#    IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#    DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
#    ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#    (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#    LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
#    ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
#    THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# 
# 3. You are under no obligation whatsoever to provide any bug fixes, patches,
#    or upgrades to the features, functionality or performance of the source code
#    ("Enhancements") to anyone; however, if you choose to make your Enhancements
#    available either publicly, or directly to Lawrence Berkeley National
#    Laboratory, without imposing a separate written license agreement for such
#    Enhancements, then you hereby grant the following license: a non-exclusive,
#    royalty-free perpetual license to install, use, modify, prepare derivative
#    works, incorporate into other computer software, distribute, and sublicense
#    such enhancements or derivative works thereof, in binary and source code
#    form.
# 
# NOTE: This license corresponds to the "revised BSD" or "3-clause BSD" license
# and includes the following modification: Paragraph 3. has been added.
# """
import os
import pytest
from configparser import ConfigParser

from openeis.applications.utest_applications.appwrapper import run_appwrapper
from openeis.projects.models import (SensorIngest,
                                     DataMap,
                                     DataFile)

# Enables django database integration.
pytestmark = pytest.mark.django_db

# get the path to the current directory because that is where
# the expected outputs will be located.
basedir = os.path.abspath(os.path.dirname(__file__))

# The app that is being run.
app_name = 'energy_signature'


def build_expected(table_names, file_refs):
    '''Expected list of table-names to match with list of file_refs'''
    exp = {}
    for i in range(len(table_names)):
        exp[i] = file_refs[i]
        
    return exp


def test_energy_signature_basic(basic_dataset):
    expected_output = build_expected(('Scatterplot', 'Weather_Sensitivity'),
                                      ('energy_signature_negone_SP.csv', 
                                            'energy_signature_negone_WS.csv'))
    config = build_energysig_config_parser(app_name, 
                                           basic_dataset.id, 
                                           basic_dataset.map.id)
    run_appwrapper(config, expected_output)
#     es_basic_exp = {}
#     es_basic_ini = os.path.join(self.basedir,
#                                 'energy_signature_negone.ini')
#     es_basic_exp['Scatterplot'] = os.path.join(self.basedir,
#                                 'energy_signature_negone_SP.ref.csv')
#     es_basic_exp['Weather_Sensitivity'] = os.path.join(self.basedir,
#                                 'energy_signature_negone_WS.ref.csv')
    #self.run_it(es_basic_ini, es_basic_exp, clean_up=True)


# 
#     def test_energy_signature_missing(self):
#         es_missing_exp = {}
#         es_missing_ini = os.path.join(self.basedir,
#                                    'energy_signature_missing.ini')
#         es_missing_exp['Scatterplot'] = os.path.join(self.basedir,
#                                    'energy_signature_missing_SP.ref.csv')
#         es_missing_exp['Weather_Sensitivity'] = os.path.join(self.basedir,
#                                    'energy_signature_missing_WS.ref.csv')
#         self.run_it(es_missing_ini, es_missing_exp, clean_up=True)
#                                     'energy_signature_negone_WS.ref.csv')
#         self.run_it(es_basic_ini, es_basic_exp, clean_up=True)
# 
#     def test_energy_signature_missing(self):
#         es_missing_exp = {}
#         es_missing_ini = os.path.join(self.basedir,
#                                    'energy_signature_missing.ini')
#         es_missing_exp['Scatterplot'] = os.path.join(self.basedir,
#                                    'energy_signature_missing_SP.ref.csv')
#         es_missing_exp['Weather_Sensitivity'] = os.path.join(self.basedir,
#                                    'energy_signature_missing_WS.ref.csv')
#         self.run_it(es_missing_ini, es_missing_exp, clean_up=True)

def build_energysig_config_parser(app_name, dataset_id, sensormap_id):
    '''
    This function creates a config parser with the specified dataset and
    sensormap_id. 
    '''
    config = ConfigParser()
    
    config.add_section("global_settings")
    config.set("global_settings", 'application', app_name)
    config.set("global_settings", 'dataset_id', str(dataset_id))
    config.set("global_settings", 'sensormap_id', str(sensormap_id))
    
    config.add_section("application_config")
    config.set('application_config', 'building_name', '"bldg90"')

        
    config.add_section('inputs')
    config.set('inputs', "oat", 'lbnl/bldg90/OutdoorAirTemperature')
    config.set('inputs', 'load', 'lbnl/bldg90/WholeBuildingElectricity')
    
    return config
