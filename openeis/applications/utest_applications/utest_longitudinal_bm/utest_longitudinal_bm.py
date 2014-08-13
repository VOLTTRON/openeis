from openeis.applications.utest_applications.apptest import AppTestBase
import os

"""
Unit tests for Longitudinal Benchmarking application.
"""

class TestLongitudinalBM(AppTestBase):
    fixtures = [os.path.join('applications',
                            'utest_applications',
                            'utest_longitudinal_bm',
                            'longitudinal_bm_fixture.json')]

    def test_longitudinal_BM_basic(self):
        lb_basic_exp = {}
        lb_basic_ini = os.path.join('applications',
                                    'utest_applications',
                                    'utest_longitudinal_bm',
                                    'longitudinal_bm_basic.ini')
        lb_basic_exp['Longitudinal_BM'] = os.path.join('applications',
                                    'utest_applications',
                                    'utest_longitudinal_bm',
                                    'longitudinal_bm_basic.ref.csv')
        self.run_it(lb_basic_ini, lb_basic_exp, clean_up=True)

    def test_longitudinal_BM_missing(self):
        lb_missing_exp = {}
        lb_missing_ini = os.path.join('applications',
                                    'utest_applications',
                                    'utest_longitudinal_bm',
                                    'longitudinal_bm_missing.ini')
        lb_missing_exp['Longitudinal_BM'] = os.path.join('applications',
                                    'utest_applications',
                                    'utest_longitudinal_bm',
                                    'longitudinal_bm_missing.ref.csv')
        self.run_it(lb_missing_ini, lb_missing_exp, clean_up=True)

    def test_longitudinal_BM_floats(self):
        lb_floats_exp = {}
        lb_floats_ini = os.path.join('applications',
                                    'utest_applications',
                                    'utest_longitudinal_bm',
                                    'longitudinal_bm_floats.ini')
        lb_floats_exp['Longitudinal_BM'] = os.path.join('applications',
                                    'utest_applications',
                                    'utest_longitudinal_bm',
                                    'longitudinal_bm_floats.ref.csv')
        self.run_it(lb_floats_ini, lb_floats_exp, clean_up=True)

    def test_longitudinal_BM_floats_missing(self):
        lb_floats_missing_exp = {}
        lb_floats_missing_ini = os.path.join('applications',
                                    'utest_applications',
                                    'utest_longitudinal_bm',
                                    'longitudinal_bm_floats_missing.ini')
        lb_floats_missing_exp['Longitudinal_BM'] = os.path.join('applications',
                                    'utest_applications',
                                    'utest_longitudinal_bm',
                                    'longitudinal_bm_floats_missing.ref.csv')
        self.run_it(lb_floats_missing_ini, lb_floats_missing_exp,
                clean_up=True)


