from openeis.applications.utest_applications.apptest import AppTestBase
from openeis.applications.utils.testing_utils import set_up_datetimes, append_data_to_datetime

import datetime
from economizer import economizer
import copy

#TODO: more extensive tests.
class TestEconomizer(AppTestBase):

    def test_economizer_basic(self):
        a = datetime.datetime(2014, 1, 1, 0, 0, 0, 0)
        b = datetime.datetime(2014, 1, 4, 0, 0, 0, 0)
        #delta = 6 hours
        base = set_up_datetimes(a, b, 21600)

        DAT = copy.deepcopy(base)
        DAT_temp = [69, 69, 69, 69, 69, 69, 69, 69, 69, 69, 69, 69, 69]
        append_data_to_datetime(DAT, DAT_temp)

        OAT = copy.deepcopy(base)
        OAT_temp = [65, 65, 65, 65, 65, 65, 65, 65, 65, 65, 65, 65, 65]
        append_data_to_datetime(OAT, OAT_temp)

        HVACstat = copy.deepcopy(base)
        HVAC_data = [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
        append_data_to_datetime(HVACstat, HVAC_data)

        result = economizer(DAT, OAT, HVACstat)
        self.assertIsNotNone(result, 
                "Should return a dictionary of suggestions, but does not.")

