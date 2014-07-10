from openeis.applications.utest_applications.apptest import AppTestBase
from openeis.applications.utils import spearman
import numpy as np
import os

"""
Unit tests for applications.
"""

class TestDailySummary(AppTestBase):
    fixtures = [os.path.join('applications',
                             'utest_applications',
                             'utest_daily_summary',
                             'daily_summary_fixture.json')]

    def test_daily_summary_same_numbers(self):
        ds_same_num_exp = {}
        ds_same_num_ini = os.path.join('applications',
                                       'utest_applications',
                                       'utest_daily_summary',
                                       'daily_summary_same_number.ini')
        ds_same_num_exp['Daily_Summary_Table'] = os.path.join('applications',
                                       'utest_applications',
                                       'utest_daily_summary',
                                       'daily_summary_same_number.ref.csv')
        self.run_it(ds_same_num_ini, ds_same_num_exp, clean_up=True)

    def test_daily_summary_one_to_five(self):
        ds_onetofive_exp = {}
        ds_onetofive_ini = os.path.join('applications',
                                        'utest_applications',
                                        'utest_daily_summary',
                                        'daily_summary_onetofive.ini')
        ds_onetofive_exp['Daily_Summary_Table'] = os.path.join('applications',
                                        'utest_applications',
                                        'utest_daily_summary',
                                        'daily_summary_onetofive.ref.csv')
        self.run_it(ds_onetofive_ini, ds_onetofive_exp, clean_up=True)

    def test_daily_summary_missing_numbers(self):
        ds_missing_exp = {}
        ds_missing_ini = os.path.join('applications',
                                      'utest_applications',
                                      'utest_daily_summary',
                                      'daily_summary_missing.ini')
        ds_missing_exp['Daily_Summary_Table'] = os.path.join('applications',
                                      'utest_applications',
                                      'utest_daily_summary',
                                      'daily_summary_missing.ref.csv')
        self.run_it(ds_missing_ini, ds_missing_exp, clean_up=True)

    def test_daily_summary_floats(self):
        ds_floats_exp = {}
        ds_floats_ini = os.path.join('applications',
                                     'utest_applications',
                                     'utest_daily_summary',
                                     'daily_summary_floats.ini')
        ds_floats_exp['Daily_Summary_Table'] = os.path.join('applications',
                                     'utest_applications',
                                     'utest_daily_summary',
                                     'daily_summary_floats.ref.csv')
        self.run_it(ds_floats_ini, ds_floats_exp, clean_up=True)

#TODO: test floats and missing - still needs to be ironed out
# Weird timing issue.  Probably time zone related.

    def test_daily_summary_invalid(self):
        ds_incorrect_ini = os.path.join('applications',
                                        'utest_applications',
                                        'utest_daily_summary',
                                        'daily_summary_invalid.ini')
        self.assertRaises(Exception, self.run_application, ds_incorrect_ini)


class TestEnergySignature(AppTestBase):
    fixtures = [os.path.join('applications',
                            'utest_applications',
                            'utest_energy_signature',
                            'energy_signature_fixture.json')]

    def test_energy_signature_basic(self):
        es_basic_exp = {}
        es_basic_ini = os.path.join('applications',
                                    'utest_applications',
                                    'utest_energy_signature',
                                    'energy_signature_negone.ini')
        es_basic_exp['Scatterplot'] = os.path.join('applications',
                                    'utest_applications',
                                    'utest_energy_signature',
                                    'energy_signature_negone_SP.ref.csv')
        es_basic_exp['Weather_Sensitivity'] = os.path.join('applications',
                                    'utest_applications',
                                    'utest_energy_signature',
                                    'energy_signature_negone_WS.ref.csv')
        self.run_it(es_basic_ini, es_basic_exp, clean_up=True)

    def test_energy_signature_missing(self):
        es_missing_exp = {}
        es_missing_ini = os.path.join('applications',
                                    'utest_applications',
                                    'utest_energy_signature',
                                    'energy_signature_missing.ini')
        es_missing_exp['Scatterplot'] = os.path.join('applications',
                                    'utest_applications',
                                    'utest_energy_signature',
                                    'energy_signature_missing_SP.ref.csv')
        es_missing_exp['Weather_Sensitivity'] = os.path.join('applications',
                                    'utest_applications',
                                    'utest_energy_signature',
                                    'energy_signature_missing_WS.ref.csv')
        self.run_it(es_missing_ini, es_missing_exp, clean_up=True)

#TODO: Same number should break
#es_same_num_ini = os.path.join('energy_signature_samenum.ini'
#es_same_num_exp = ['energy_signature_missing_SP.ref.csv',\
#            'energy_signature_missing_WS.ref.csv']
#run_test(es_same_num_ini, es_same_num_exp, clean_up=True)
#print('========== \nSame number test passed. \n========== \n')


#Heat map test
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

