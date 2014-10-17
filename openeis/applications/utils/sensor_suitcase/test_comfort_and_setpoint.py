"""
Unit test `comfort_and_setpoint`.

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

        comfort_result, setback_result = comfort_and_setpoint(IAT, DAT, op_hours, 5000, 1000)
        """
        setback_expected = {
            'Problem': "Overly narrow separation between heating " + \
                    "and cooling setpoints.",
            'Diagnostic': "During occupied hours, the cooling setpoint was lower " + \
                    "than 76F and the heating setpoint was greater than 72F.",
            'Recommendation': "Adjust the heating and cooling setpoints so that " + \
                    "they differ by more than four degrees.",
            'Savings': cooling_savings + heating_savings
            }
        """
        print(comfort_result)

        self.assertIsNot(comfort_result, False)

"""
negatives, all zeros
    def test_economizer_empty(self):
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
"""

