from openeis.applications.utest_applications.apptest import AppTestBase

from datetime import datetime

from separate_hours import separate_hours

class TestExcessiveNighttimeLighting(AppTestBase):

    def test_excessive_night_light_ones(self):
        a = datetime(2014, 1, 1, 0, 0, 0, 0)
        b = datetime(2014, 1, 2, 0, 0, 0, 0)
        # delta = 6 hours
        data = self.set_up_datetimes(a, b, 21600)
        all_ones = [1, 1, 1, 1, 1]
        self.append_data_to_datetime(data, all_ones)

        hours = [9, 17]
        days_op = [1, 2, 3, 4, 5]

        exp_non_op = [[datetime(2014, 1, 1, 0, 0), 1], 
                [datetime(2014, 1, 1, 6, 0), 1],
                [datetime(2014, 1, 1, 18, 0), 1],
                [datetime(2014, 1, 2, 0, 0), 1]]
        exp_op = [[datetime(2014, 1, 1, 12, 0), 1]]

        result_op, result_non_op = separate_hours(data, hours, days_op)

        self.assertEqual(exp_op, result_op)
        self.assertEqual(exp_non_op, result_non_op)
