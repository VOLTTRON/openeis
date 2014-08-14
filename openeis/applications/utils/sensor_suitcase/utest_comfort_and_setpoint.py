from openeis.applications.utest_applications.apptest import AppTestBase
from openeis.applications.utils.testing_utils import set_up_datetimes, append_data_to_datetime

from comfort_and_setpoint import comfort_and_setpoint
import datetime
import copy

#TODO: more extensive tests.
class TestComfortAndSetback(AppTestBase):

    def test_economizer_basic(self):
        a = datetime.datetime(2014, 1, 1, 0, 0, 0, 0)
        b = datetime.datetime(2014, 1, 4, 0, 0, 0, 0)
        #delta = 6 hours
        base = set_up_datetimes(a, b, 21600)

        DAT = copy.deepcopy(base)
        DAT_temp = [8, 8, 8, 8, 8, 8, 8, 8, 100, 100, 100, 100, 100]
        append_data_to_datetime(DAT, DAT_temp)

        IAT = copy.deepcopy(base)
        IAT_temp = [10, 10, 10, 10, 10, 10, 10, 10, 80, 80, 80, 80, 80]
        append_data_to_datetime(IAT, IAT_temp)

        op_hours = [[0, 23], [1, 2, 3, 4, 5, 6, 7], []]

        comfort, setback = comfort_and_setpoint(IAT, DAT, op_hours)

        self.assertIsNot(comfort, False)
        self.assertTrue(setback)
