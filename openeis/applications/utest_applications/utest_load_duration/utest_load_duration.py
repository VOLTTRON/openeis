from openeis.applications.utest_applications.apptest import AppTestBase
import os

"""
Unit tests for Load Duration application.
"""

class TestLoadDuration(AppTestBase):
    fixtures = [os.path.join('applications',
                            'utest_applications',
                            'utest_load_duration',
                            'load_duration_fixture.json')]

    def test_load_duration_basic(self):
        ld_basic_exp = {}
        ld_basic_ini = os.path.join('applications',
                                    'utest_applications',
                                    'utest_load_duration',
                                    'load_duration_basic.ini')
        ld_basic_exp['Load_Duration'] = os.path.join('applications',
                                    'utest_applications',
                                    'utest_load_duration', 
                                    'load_duration_basic.ref.csv')
        self.run_it(ld_basic_ini, ld_basic_exp, clean_up=True)

    def test_load_duration_missing(self):
        ld_missing_exp = {}
        ld_missing_ini = os.path.join('applications',
                                    'utest_applications',
                                    'utest_load_duration',
                                    'load_duration_missing.ini')
        ld_missing_exp['Load_Duration'] = os.path.join('applications',
                                    'utest_applications',
                                    'utest_load_duration',
                                    'load_duration_missing.ref.csv')
        self.run_it(ld_missing_ini, ld_missing_exp, clean_up=True)

    def test_load_duration_floats(self):
        ld_floats_exp = {}
        ld_floats_ini = os.path.join('applications',
                                    'utest_applications',
                                    'utest_load_duration',
                                    'load_duration_floats.ini')
        ld_floats_exp['Load_Duration'] = os.path.join('applications',
                                    'utest_applications',
                                    'utest_load_duration',
                                    'load_duration_floats.ref.csv')
        self.run_it(ld_floats_ini, ld_floats_exp, clean_up=True)

    def test_load_duration_floats_missing(self):
        ld_floats_missing_exp = {}
        ld_floats_missing_ini = os.path.join('applications',
                                    'utest_applications',
                                    'utest_load_duration',
                                    'load_duration_floats_missing.ini')
        ld_floats_missing_exp['Load_Duration'] = os.path.join('applications',
                                    'utest_applications',
                                    'utest_load_duration',
                                    'load_duration_floats_missing.ref.csv')
        self.run_it(ld_floats_missing_ini, ld_floats_missing_exp, 
                clean_up=True)


