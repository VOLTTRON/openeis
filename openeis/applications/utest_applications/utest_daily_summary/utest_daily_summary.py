from openeis.applications.utest_applications.apptest import AppTestBase
import os

"""
Unit tests for Daily Summary application.
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

    def test_daily_summary_invalid(self):
        ds_incorrect_ini = os.path.join('applications',
                                        'utest_applications',
                                        'utest_daily_summary',
                                        'daily_summary_invalid.ini')
        self.assertRaises(Exception, self.run_application, ds_incorrect_ini)

        
