"""
Unit test `day_time_temperature_model.py`.

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

import datetime
import numpy
import day_time_temperature_model as dtt
import os
import copy

class TestDayTimeTemperature(AppTestBase):
    fixtures = [os.path.join('applications',
                     'utest_applications',
                     'utest_day_time_temperature_app',
                     'day_time_temperature_data.json')]

    def test_findDateIndex(self):
        a = datetime.datetime(2014, 1, 1, 0, 0, 0, 0)
        b = datetime.datetime(2014, 1, 2, 0, 0, 0, 0)
        datetime_list = numpy.array(set_up_datetimes(a, b, 3600)).flatten()
        
        # Testing index finder for specific dates.
        testDateIndex = dtt.findDateIndex(datetime_list, 
                                          datetime.datetime(2014, 1, 1, 7, 0, 0, 0))
        self.assertTrue(str.isdigit(str(testDateIndex)))

        testDateIndex = dtt.findDateIndex(datetime_list, 
                                          datetime.datetime(2014, 2, 1, 0, 0, 0, 0))
        self.assertIs(str.isdigit(str(testDateIndex)), False)
        
    def test_daytimetemperature_model(self):
        dtt_model_exp = {}
        dtt_model_ini = os.path.join('applications',
                                     'utest_applications',
                                     'utest_day_time_temperature_app',
                                     'daytimetemperature_config.ini')
        dtt_model_exp['DayTimeTemperatureModel'] = os.path.join('applications',
                                     'utest_applications',
                                     'utest_day_time_temperature_app',
                                     'day_time_temperature_app_data.ref.csv')
        self.run_it(dtt_model_ini, dtt_model_exp, clean_up=True)