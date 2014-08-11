from openeis.applications.utest_applications.apptest import AppTestBase
import os

"""
Unit tests for Load Profiling application.
"""

class TestLoadProfiling(AppTestBase):
    fixtures = [os.path.join('applications',
                            'utest_applications',
                            'utest_load_profiling',
                            'load_profiling_fixture.json')]

    def test_load_profiling_basic(self):
        lp_basic_exp = {}
        lp_basic_ini = os.path.join('applications',
                                    'utest_applications',
                                    'utest_load_profiling',
                                    'load_profiling_basic.ini')
        lp_basic_exp['Load_Profiling'] = os.path.join('applications',
                                    'utest_applications',
                                    'utest_load_profiling',
                                    'load_profiling_basic.ref.csv')
        self.run_it(lp_basic_ini, lp_basic_exp, clean_up=True)

    def test_load_profiling_missing(self):
        lp_missing_exp = {}
        lp_missing_ini = os.path.join('applications',
                                    'utest_applications',
                                    'utest_load_profiling',
                                    'load_profiling_missing.ini')
        lp_missing_exp['Load_Profiling'] = os.path.join('applications',
                                    'utest_applications',
                                    'utest_load_profiling',
                                    'load_profiling_missing.ref.csv')
        self.run_it(lp_missing_ini, lp_missing_exp, clean_up=True)

    def test_load_profiling_floats(self):
        lp_floats_exp = {}
        lp_floats_ini = os.path.join('applications',
                                    'utest_applications',
                                    'utest_load_profiling',
                                    'load_profiling_floats.ini')
        lp_floats_exp['Load_Profiling'] = os.path.join('applications',
                                    'utest_applications',
                                    'utest_load_profiling',
                                    'load_profiling_floats.ref.csv')
        self.run_it(lp_floats_ini, lp_floats_exp, clean_up=True)

    def test_load_profiling_floats_missing(self):
        lp_floats_missing_exp = {}
        lp_floats_missing_ini = os.path.join('applications',
                                    'utest_applications',
                                    'utest_load_profiling',
                                    'load_profiling_floats_missing.ini')
        lp_floats_missing_exp['Load_Profiling'] = os.path.join('applications',
                                    'utest_applications',
                                    'utest_load_profiling',
                                    'load_profiling_floats_missing.ref.csv')
        self.run_it(lp_floats_missing_ini, lp_floats_missing_exp,
                clean_up=True)


