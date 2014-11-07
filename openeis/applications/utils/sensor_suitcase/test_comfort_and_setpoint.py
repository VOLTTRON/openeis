"""
Unit test `comfort_and_setpoint`.


Copyright
=========

OpenEIS Algorithms Phase 2 Copyright (c) 2014,
The Regents of the University of California, through Lawrence Berkeley National
Laboratory (subject to receipt of any required approvals from the U.S.
Department of Energy). All rights reserved.

If you have questions about your rights to use or distribute this software,
please contact Berkeley Lab's Technology Transfer Department at TTD@lbl.gov
referring to "OpenEIS Algorithms Phase 2 (LBNL Ref 2014-168)".

NOTICE:  This software was produced by The Regents of the University of
California under Contract No. DE-AC02-05CH11231 with the Department of Energy.
For 5 years from November 1, 2012, the Government is granted for itself and
others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide
license in this data to reproduce, prepare derivative works, and perform
publicly and display publicly, by or on behalf of the Government. There is
provision for the possible extension of the term of this license. Subsequent to
that period or any extension granted, the Government is granted for itself and
others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide
license in this data to reproduce, prepare derivative works, distribute copies
to the public, perform publicly and display publicly, and to permit others to
do so. The specific term of the license can be identified by inquiry made to
Lawrence Berkeley National Laboratory or DOE. Neither the United States nor the
United States Department of Energy, nor any of their employees, makes any
warranty, express or implied, or assumes any legal liability or responsibility
for the accuracy, completeness, or usefulness of any data, apparatus, product,
or process disclosed, or represents that its use would not infringe privately
owned rights.


License
=======

Copyright (c) 2014, The Regents of the University of California, Department
of Energy contract-operators of the Lawrence Berkeley National Laboratory.
All rights reserved.

1. Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions are met:

   (a) Redistributions of source code must retain the copyright notice, this
   list of conditions and the following disclaimer.

   (b) Redistributions in binary form must reproduce the copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

   (c) Neither the name of the University of California, Lawrence Berkeley
   National Laboratory, U.S. Dept. of Energy nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

2. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
   AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
   DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
   ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
   (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
   LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
   ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
   (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
   THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

3. You are under no obligation whatsoever to provide any bug fixes, patches,
   or upgrades to the features, functionality or performance of the source code
   ("Enhancements") to anyone; however, if you choose to make your Enhancements
   available either publicly, or directly to Lawrence Berkeley National
   Laboratory, without imposing a separate written license agreement for such
   Enhancements, then you hereby grant the following license: a non-exclusive,
   royalty-free perpetual license to install, use, modify, prepare derivative
   works, incorporate into other computer software, distribute, and sublicense
   such enhancements or derivative works thereof, in binary and source code
   form.

NOTE: This license corresponds to the "revised BSD" or "3-clause BSD" license
and includes the following modification: Paragraph 3. has been added.
"""


from openeis.applications.utest_applications.apptest import AppTestBase
from openeis.applications.utils.testing_utils import set_up_datetimes, append_data_to_datetime

from openeis.applications.utils.sensor_suitcase.comfort_and_setpoint import comfort_and_setpoint
import datetime
import copy

class TestComfortAndSetback(AppTestBase):

    def test_setback(self):
        a = datetime.datetime(2014, 1, 1, 0, 0, 0, 0)
        b = datetime.datetime(2014, 1, 3, 6, 0, 0, 0)
        #delta = 6 hours
        base = set_up_datetimes(a, b, 21600)

        DAT = copy.deepcopy(base)
        DAT_temp = [0, 0, 0, 0, 0, 100, 100, 100, 100, 100]
        append_data_to_datetime(DAT, DAT_temp)

        IAT = copy.deepcopy(base)
        IAT_temp = [50, 50, 50, 50, 50, 80, 80, 80, 80, 80]
        append_data_to_datetime(IAT, IAT_temp)

        # 24/7, no holidays
        op_hours = [[0, 23], [1, 2, 3, 4, 5, 6, 7], []]

        test_area = 5000
        test_elec_cost = 10000

        comfort_result, setback_result = comfort_and_setpoint(IAT, DAT, op_hours, \
                test_area, test_elec_cost)

        exp_cool_cost = (76 - 50) * 0.03 * 0.5 * 0.07 * 1 * test_elec_cost
        exp_heat_cost = (80 - 72) * 0.03 * 0.5 * 0.31 * 1 * test_elec_cost

        expected = {
            'Problem': "Overly narrow separation between heating " + \
                    "and cooling setpoints.",
            'Diagnostic': "During occupied hours, the cooling setpoint was lower " + \
                    "than 76F and the heating setpoint was greater than 72F.",
            'Recommendation': "Adjust the heating and cooling setpoints so that " + \
                    "they differ by more than four degrees.",
            'Savings': round(exp_cool_cost + exp_heat_cost, 2)
        }

        self.assertEqual(setback_result, expected)


    def test_comfort_overcooling(self):
        a = datetime.datetime(2014, 1, 1, 0, 0, 0, 0)
        b = datetime.datetime(2014, 1, 3, 6, 0, 0, 0)
        #delta = 6 hours
        base = set_up_datetimes(a, b, 21600)

        DAT = copy.deepcopy(base)
        DAT_temp = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        append_data_to_datetime(DAT, DAT_temp)

        IAT = copy.deepcopy(base)
        IAT_temp = [50, 50, 50, 50, 50, 50, 50, 50, 50, 50]
        append_data_to_datetime(IAT, IAT_temp)

        # 24/7, no holidays
        op_hours = [[0, 23], [1, 2, 3, 4, 5, 6, 7], []]

        test_area = 5000
        test_elec_cost = 10000

        comfort_result, setback_result = comfort_and_setpoint(IAT, DAT, op_hours, \
                test_area, test_elec_cost)

        exp_cool_cost = (76 - 50) * 0.03 * 1 * 0.07 * 1 * test_elec_cost

        expected = {
        'Problem': "Over-conditioning, thermostat cooling setpoint is low",
        'Diagnostic': "More than 30 percent of the time, the cooling setpoint " + \
                "during occupied hours was lower than 75F, a temperature that " + \
                "is comfortable to most occupants",
        'Recommendation': "Program your thermostats to increase the cooling " + \
                "setpoint during occupied hours.",
        'Savings': round(exp_cool_cost, 2)
        }

        self.assertEqual(comfort_result, expected)

    def test_comfort_undercooling(self):
        a = datetime.datetime(2014, 1, 1, 0, 0, 0, 0)
        b = datetime.datetime(2014, 1, 3, 6, 0, 0, 0)
        #delta = 6 hours
        base = set_up_datetimes(a, b, 21600)

        DAT = copy.deepcopy(base)
        DAT_temp = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
        append_data_to_datetime(DAT, DAT_temp)

        IAT = copy.deepcopy(base)
        IAT_temp = [200, 200, 200, 200, 200, 200, 200, 200, 200, 200]
        append_data_to_datetime(IAT, IAT_temp)

        # 24/7, no holidays
        op_hours = [[0, 23], [1, 2, 3, 4, 5, 6, 7], []]

        test_area = 5000
        test_elec_cost = 10000

        comfort_result, setback_result = comfort_and_setpoint(IAT, DAT, op_hours, \
                test_area, test_elec_cost)

        expected = {
        'Problem': "Under-conditioning, thermostat cooling " + \
                "setpoint is high.",
        'Diagnostic':  "More than 30 percent of the time, the cooling setpoint " + \
                "during occupied hours was greater than 80F.",
        'Recommendation': "Program your thermostats to decrease the cooling " + \
                "setpoint to improve building comfort during occupied hours."
        }

        self.assertEqual(comfort_result, expected)

    def test_comfort_overheating(self):
        a = datetime.datetime(2014, 1, 1, 0, 0, 0, 0)
        b = datetime.datetime(2014, 1, 3, 6, 0, 0, 0)
        #delta = 6 hours
        base = set_up_datetimes(a, b, 21600)

        DAT = copy.deepcopy(base)
        DAT_temp = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
        append_data_to_datetime(DAT, DAT_temp)

        IAT = copy.deepcopy(base)
        IAT_temp = [80, 80, 80, 80, 80, 80, 80, 80, 80, 80]
        append_data_to_datetime(IAT, IAT_temp)

        # 24/7, no holidays
        op_hours = [[0, 23], [1, 2, 3, 4, 5, 6, 7], []]

        test_area = 5000
        test_elec_cost = 10000

        comfort_result, setback_result = comfort_and_setpoint(IAT, DAT, op_hours, \
                test_area, test_elec_cost)

        exp_heat_cost = (80 - 72) * 0.03 * 1 * 0.31 * 1 * test_elec_cost

        expected = {
        'Problem': "Over-conditioning, thermostat heating " + \
                "setpoint is high.",
        'Diagnostic': "More than 30 percent of the time, the heating setpoint " + \
                "during occupied hours was greater than 72F, a temperature that " + \
                "is comfortable to most occupants.",
        'Recommendation': "Program your thermostats to decrease the heating " + \
                "setpoint during occupied hours.",
        'Savings': round(exp_heat_cost, 2)
        }

        self.assertEqual(comfort_result, expected)

    def test_comfort_underheating(self):
        a = datetime.datetime(2014, 1, 1, 0, 0, 0, 0)
        b = datetime.datetime(2014, 1, 3, 6, 0, 0, 0)
        #delta = 6 hours
        base = set_up_datetimes(a, b, 21600)

        DAT = copy.deepcopy(base)
        DAT_temp = [50, 50, 50, 50, 50, 50, 50, 50, 50, 50]
        append_data_to_datetime(DAT, DAT_temp)

        IAT = copy.deepcopy(base)
        IAT_temp = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        append_data_to_datetime(IAT, IAT_temp)

        # 24/7, no holidays
        op_hours = [[0, 23], [1, 2, 3, 4, 5, 6, 7], []]

        test_area = 5000
        test_elec_cost = 10000

        comfort_result, setback_result = comfort_and_setpoint(IAT, DAT, op_hours, \
                test_area, test_elec_cost)

        exp_cool_cost = (76 - 50) * 0.03 * 0.5 * 0.07 * 1 * test_elec_cost
        exp_heat_cost = (80 - 72) * 0.03 * 0.5 * 0.31 * 1 * test_elec_cost

        expected = {
        'Problem': "Under-conditioning - thermostat heating " + \
                "setpoint is low.",
        'Diagnostic': "For more than 30% of the time, the cooling setpoint " + \
                "during occupied hours was less than 69 degrees F.",
        'Recommendation': "Program thermostats to increase the heating " + \
                "setpoint to improve building comfort during occupied hours."
        }


        self.assertEqual(comfort_result, expected)

    def test_setback_comfort_and_setback_success(self):
        a = datetime.datetime(2014, 1, 1, 0, 0, 0, 0)
        b = datetime.datetime(2014, 1, 3, 6, 0, 0, 0)
        #delta = 6 hours
        base = set_up_datetimes(a, b, 21600)

        DAT = copy.deepcopy(base)
        DAT_temp = [75, 75, 75, 75, 75, 75, 75, 75, 75, 75]
        append_data_to_datetime(DAT, DAT_temp)

        IAT = copy.deepcopy(base)
        IAT_temp = [75, 75, 75, 75, 75, 75, 75, 75, 75, 75]
        append_data_to_datetime(IAT, IAT_temp)

        # 24/7, no holidays
        op_hours = [[0, 23], [1, 2, 3, 4, 5, 6, 7], []]

        test_area = 5000
        test_elec_cost = 10000

        comfort_result, setback_result = comfort_and_setpoint(IAT, DAT, op_hours, \
                test_area, test_elec_cost)

        self.assertEqual(comfort_result, {})
        self.assertEqual(setback_result, {})

    def test_setback_HVAC(self):
        a = datetime.datetime(2014, 1, 1, 0, 0, 0, 0)
        b = datetime.datetime(2014, 1, 3, 6, 0, 0, 0)
        #delta = 6 hours
        base = set_up_datetimes(a, b, 21600)

        DAT = copy.deepcopy(base)
        DAT_temp = [0, 0, 0, 0, 0, 100, 100, 100, 100, 100]
        append_data_to_datetime(DAT, DAT_temp)

        IAT = copy.deepcopy(base)
        IAT_temp = [50, 50, 50, 50, 50, 80, 80, 80, 80, 80]
        append_data_to_datetime(IAT, IAT_temp)

        HVAC = copy.deepcopy(base)
        HVAC_stat = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        append_data_to_datetime(HVAC, HVAC_stat)

        # 24/7, no holidays
        op_hours = [[0, 23], [1, 2, 3, 4, 5, 6, 7], []]

        test_area = 5000
        test_elec_cost = 10000

        comfort_result, setback_result = comfort_and_setpoint(IAT, DAT, op_hours, \
                test_area, test_elec_cost, HVAC)

        exp_cool_cost = (76 - 50) * 0.03 * 0.5 * 0.07 * 1 * test_elec_cost
        exp_heat_cost = (80 - 72) * 0.03 * 0.5 * 0.31 * 1 * test_elec_cost

        expected = {
            'Problem': "Overly narrow separation between heating " + \
                    "and cooling setpoints.",
            'Diagnostic': "During occupied hours, the cooling setpoint was lower " + \
                    "than 76F and the heating setpoint was greater than 72F.",
            'Recommendation': "Adjust the heating and cooling setpoints so that " + \
                    "they differ by more than four degrees.",
            'Savings': round(exp_cool_cost + exp_heat_cost, 2)
        }

        self.assertEqual(setback_result, expected)


    def test_comfort_overcooling_HVAC(self):
        a = datetime.datetime(2014, 1, 1, 0, 0, 0, 0)
        b = datetime.datetime(2014, 1, 3, 6, 0, 0, 0)
        #delta = 6 hours
        base = set_up_datetimes(a, b, 21600)

        DAT = copy.deepcopy(base)
        DAT_temp = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        append_data_to_datetime(DAT, DAT_temp)

        IAT = copy.deepcopy(base)
        IAT_temp = [50, 50, 50, 50, 50, 50, 50, 50, 50, 50]
        append_data_to_datetime(IAT, IAT_temp)

        HVAC = copy.deepcopy(base)
        HVAC_stat = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        append_data_to_datetime(HVAC, HVAC_stat)

        # 24/7, no holidays
        op_hours = [[0, 23], [1, 2, 3, 4, 5, 6, 7], []]

        test_area = 5000
        test_elec_cost = 10000

        comfort_result, setback_result = comfort_and_setpoint(IAT, DAT, op_hours, \
                test_area, test_elec_cost, HVAC)

        exp_cool_cost = (76 - 50) * 0.03 * 1 * 0.07 * 1 * test_elec_cost

        expected = {
        'Problem': "Over-conditioning, thermostat cooling setpoint is low",
        'Diagnostic': "More than 30 percent of the time, the cooling setpoint " + \
                "during occupied hours was lower than 75F, a temperature that " + \
                "is comfortable to most occupants",
        'Recommendation': "Program your thermostats to increase the cooling " + \
                "setpoint during occupied hours.",
        'Savings': round(exp_cool_cost, 2)
        }

        self.assertEqual(comfort_result, expected)

    def test_comfort_undercooling_HVAC(self):
        a = datetime.datetime(2014, 1, 1, 0, 0, 0, 0)
        b = datetime.datetime(2014, 1, 3, 6, 0, 0, 0)
        #delta = 6 hours
        base = set_up_datetimes(a, b, 21600)

        DAT = copy.deepcopy(base)
        DAT_temp = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
        append_data_to_datetime(DAT, DAT_temp)

        IAT = copy.deepcopy(base)
        IAT_temp = [200, 200, 200, 200, 200, 200, 200, 200, 200, 200]
        append_data_to_datetime(IAT, IAT_temp)

        HVAC = copy.deepcopy(base)
        HVAC_stat = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        append_data_to_datetime(HVAC, HVAC_stat)

        # 24/7, no holidays
        op_hours = [[0, 23], [1, 2, 3, 4, 5, 6, 7], []]

        test_area = 5000
        test_elec_cost = 10000

        comfort_result, setback_result = comfort_and_setpoint(IAT, DAT, op_hours, \
                test_area, test_elec_cost, HVAC)

        expected = {
        'Problem': "Under-conditioning, thermostat cooling " + \
                "setpoint is high.",
        'Diagnostic':  "More than 30 percent of the time, the cooling setpoint " + \
                "during occupied hours was greater than 80F.",
        'Recommendation': "Program your thermostats to decrease the cooling " + \
                "setpoint to improve building comfort during occupied hours."
        }

        self.assertEqual(comfort_result, expected)

    def test_comfort_overheating_HVAC(self):
        a = datetime.datetime(2014, 1, 1, 0, 0, 0, 0)
        b = datetime.datetime(2014, 1, 3, 6, 0, 0, 0)
        #delta = 6 hours
        base = set_up_datetimes(a, b, 21600)

        DAT = copy.deepcopy(base)
        DAT_temp = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
        append_data_to_datetime(DAT, DAT_temp)

        IAT = copy.deepcopy(base)
        IAT_temp = [80, 80, 80, 80, 80, 80, 80, 80, 80, 80]
        append_data_to_datetime(IAT, IAT_temp)

        HVAC = copy.deepcopy(base)
        HVAC_stat = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        append_data_to_datetime(HVAC, HVAC_stat)

        # 24/7, no holidays
        op_hours = [[0, 23], [1, 2, 3, 4, 5, 6, 7], []]

        test_area = 5000
        test_elec_cost = 10000

        comfort_result, setback_result = comfort_and_setpoint(IAT, DAT, op_hours, \
                test_area, test_elec_cost, HVAC)

        exp_heat_cost = (80 - 72) * 0.03 * 1 * 0.31 * 1 * test_elec_cost

        expected = {
        'Problem': "Over-conditioning, thermostat heating " + \
                "setpoint is high.",
        'Diagnostic': "More than 30 percent of the time, the heating setpoint " + \
                "during occupied hours was greater than 72F, a temperature that " + \
                "is comfortable to most occupants.",
        'Recommendation': "Program your thermostats to decrease the heating " + \
                "setpoint during occupied hours.",
        'Savings': round(exp_heat_cost, 2)
        }

        self.assertEqual(comfort_result, expected)

    def test_comfort_underheating_HVAC(self):
        a = datetime.datetime(2014, 1, 1, 0, 0, 0, 0)
        b = datetime.datetime(2014, 1, 3, 6, 0, 0, 0)
        #delta = 6 hours
        base = set_up_datetimes(a, b, 21600)

        DAT = copy.deepcopy(base)
        DAT_temp = [50, 50, 50, 50, 50, 50, 50, 50, 50, 50]
        append_data_to_datetime(DAT, DAT_temp)

        IAT = copy.deepcopy(base)
        IAT_temp = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        append_data_to_datetime(IAT, IAT_temp)

        HVAC = copy.deepcopy(base)
        HVAC_stat = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        append_data_to_datetime(HVAC, HVAC_stat)

        # 24/7, no holidays
        op_hours = [[0, 23], [1, 2, 3, 4, 5, 6, 7], []]

        test_area = 5000
        test_elec_cost = 10000

        comfort_result, setback_result = comfort_and_setpoint(IAT, DAT, op_hours, \
                test_area, test_elec_cost, HVAC)

        exp_cool_cost = (76 - 50) * 0.03 * 0.5 * 0.07 * 1 * test_elec_cost
        exp_heat_cost = (80 - 72) * 0.03 * 0.5 * 0.31 * 1 * test_elec_cost

        expected = {
        'Problem': "Under-conditioning - thermostat heating " + \
                "setpoint is low.",
        'Diagnostic': "For more than 30% of the time, the cooling setpoint " + \
                "during occupied hours was less than 69 degrees F.",
        'Recommendation': "Program thermostats to increase the heating " + \
                "setpoint to improve building comfort during occupied hours."
        }


        self.assertEqual(comfort_result, expected)

    def test_setback_comfort_success_HVAC(self):
        a = datetime.datetime(2014, 1, 1, 0, 0, 0, 0)
        b = datetime.datetime(2014, 1, 3, 6, 0, 0, 0)
        #delta = 6 hours
        base = set_up_datetimes(a, b, 21600)

        DAT = copy.deepcopy(base)
        DAT_temp = [0, 0, 0, 0, 0, 100, 100, 100, 100, 100]
        append_data_to_datetime(DAT, DAT_temp)

        IAT = copy.deepcopy(base)
        IAT_temp = [50, 50, 50, 50, 50, 80, 80, 80, 80, 80]
        append_data_to_datetime(IAT, IAT_temp)

        HVAC = copy.deepcopy(base)
        HVAC_stat = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        append_data_to_datetime(HVAC, HVAC_stat)

        # 24/7, no holidays
        op_hours = [[0, 23], [1, 2, 3, 4, 5, 6, 7], []]

        test_area = 5000
        test_elec_cost = 10000

        comfort_result, setback_result = comfort_and_setpoint(IAT, DAT, op_hours, \
                test_area, test_elec_cost, HVAC)

        self.assertEqual(comfort_result, {})
        self.assertEqual(setback_result, {})

