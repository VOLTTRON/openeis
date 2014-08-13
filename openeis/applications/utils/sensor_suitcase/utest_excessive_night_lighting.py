from openeis.applications.utest_applications.apptest import AppTestBase

import datetime
from excessive_night_lighting import excessive_nighttime

class TestExcessiveNighttimeLighting(AppTestBase):

    def test_excessive_night_light_ones(self):
        a = datetime.datetime(2014, 1, 1, 0, 0, 0, 0)
        b = datetime.datetime(2014, 1, 4, 0, 0, 0, 0)
        # delta = 6 hours
        base = self.set_up_datetimes(a, b, 21600)

        light_all_ones = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

        self.append_data_to_datetime(base, light_all_ones)

        result = excessive_nighttime(base, 8)
        self.assertTrue(result)
