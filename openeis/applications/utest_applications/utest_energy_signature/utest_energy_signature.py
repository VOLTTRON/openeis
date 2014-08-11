from openeis.applications.utest_applications.apptest import AppTestBase
import os

"""
Unit tests for Energy Signature application.
"""

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


