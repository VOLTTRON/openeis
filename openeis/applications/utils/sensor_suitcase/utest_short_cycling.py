from openeis.applications.utest_applications.apptest import AppTestBase
from openeis.applications.utils.testing_utils import set_up_datetimes, append_data_to_datetime

import datetime
from short_cycling import short_cycling
import copy

#TODO: more extensive tests.
class TestShortCycling(AppTestBase):

    def test_short_cycling_basic(self):
        a = datetime.datetime(2014, 1, 1, 0, 0, 0, 0)
        b = datetime.datetime(2014, 1, 1, 0, 29, 0, 0)
        #delta = 1 minute
        HVACstat = set_up_datetimes(a, b, 60)
        print("hehe: ", len(HVACstat))
        HVAC_data = [0, 3, 0, 3, 0, 3, 0, 3, 0, 3, 0, 3, 0, 3, 0, 3, 0, 3, 0, 3,
                0, 3, 0, 3, 0, 3, 0, 3, 0, 3]
        append_data_to_datetime(HVACstat, HVAC_data)

        result = short_cycling(HVACstat)
        self.assertTrue(result)
