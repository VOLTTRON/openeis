from openeis.applications.utest_applications.apptest import AppTestBase

import datetime
import sensor_suitcase
import copy

#TODO: more extensive tests.
class TestEconomizer(AppTestBase):

    def test_economizer_basic(self):
        a = datetime.datetime(2014, 1, 1, 0, 0, 0, 0)
        b = datetime.datetime(2014, 1, 4, 0, 0, 0, 0)
        #delta = 6 hours
        base = self.set_up_datetimes(a, b, 21600)

        DAT = copy.deepcopy(base)
        DAT_temp = [69, 69, 69, 69, 69, 69, 69, 69, 69, 69, 69, 69, 69]
        self.append_data_to_datetime(DAT, DAT_temp)

        OAT = copy.deepcopy(base)
        OAT_temp = [65, 65, 65, 65, 65, 65, 65, 65, 65, 65, 65, 65, 65]
        self.append_data_to_datetime(OAT, OAT_temp)

        HVACstat = copy.deepcopy(base)
        HVAC_data = [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
        self.append_data_to_datetime(HVACstat, HVAC_data)

        result = sensor_suitcase.economizer(DAT, OAT, HVACstat)
        self.assertIsNotNone(result, 
                "Should return a dictionary of suggestions, but does not.")


class TestExcessiveDaytimeLighting(AppTestBase):

    def test_excessive_day_light_ones(self):
        a = datetime.datetime(2014, 1, 1, 0, 0, 0, 0)
        b = datetime.datetime(2014, 1, 4, 0, 0, 0, 0)
        # delta = 6 hours
        base = self.set_up_datetimes(a, b, 21600)

        light_one = copy.deepcopy(base)
        light_all_ones = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

        self.append_data_to_datetime(light_one, light_all_ones)

        result = sensor_suitcase.excessive_daylight(light_one, 8)
        self.assertTrue(result)
