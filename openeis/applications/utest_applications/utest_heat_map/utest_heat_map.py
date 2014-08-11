from openeis.applications.utest_applications.apptest import AppTestBase
import os

"""
Unit tests for Heat Map application.
"""

class TestHeatMap(AppTestBase):
    fixtures = [os.path.join('applications',
                            'utest_applications',
                            'utest_heat_map',
                            'heat_map_fixture.json')]

    def test_heat_map_basic(self):
        hm_basic_exp = {}
        hm_basic_ini = os.path.join('applications',
                                    'utest_applications',
                                    'utest_heat_map',
                                    'heat_map_basic.ini')
        hm_basic_exp['Heat_Map'] = os.path.join('applications',
                                    'utest_applications',
                                    'utest_heat_map',
                                    'heat_map_basic.ref.csv')
        self.run_it(hm_basic_ini, hm_basic_exp, clean_up=True)

    def test_heat_map_missing(self):
        hm_missing_exp = {}
        hm_missing_ini = os.path.join('applications',
                                    'utest_applications',
                                    'utest_heat_map',
                                    'heat_map_missing.ini')
        hm_missing_exp['Heat_Map'] = os.path.join('applications',
                                    'utest_applications',
                                    'utest_heat_map',
                                    'heat_map_missing.ref.csv')
        self.run_it(hm_missing_ini, hm_missing_exp, clean_up=True)

    def test_heat_map_floats(self):
        hm_floats_exp = {}
        hm_floats_ini = os.path.join('applications',
                                    'utest_applications',
                                    'utest_heat_map',
                                    'heat_map_floats.ini')
        hm_floats_exp['Heat_Map'] = os.path.join('applications',
                                    'utest_applications',
                                    'utest_heat_map',
                                    'heat_map_floats.ref.csv')
        self.run_it(hm_floats_ini, hm_floats_exp, clean_up=True)

    def test_heat_map_floats_missing(self):
        hm_floats_missing_exp = {}
        hm_floats_missing_ini = os.path.join('applications',
                                    'utest_applications',
                                    'utest_heat_map',
                                    'heat_map_floats_and_missing.ini')
        hm_floats_missing_exp['Heat_Map'] = os.path.join('applications',
                                    'utest_applications',
                                    'utest_heat_map',
                                    'heat_map_floats_missing.ref.csv')
        self.run_it(hm_floats_missing_ini, hm_floats_missing_exp,
                clean_up=True)



