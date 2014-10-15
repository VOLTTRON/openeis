"""
Unit test `whole_building_energy_savings.py`.

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
from openeis.applications.utils.testing_utils import set_up_datetimes, append_data_to_datetime  # TODO: remove append_data_to_datetime if possible

import datetime
import numpy
from openeis.applications.utils.baseline_models import day_time_temperature_model as dtt
import os
import copy  # TODO: Remove if possible

class TestDayTimeTemperature(AppTestBase):
    fixtures = [
        os.path.join(os.path.abspath(os.path.dirname(__file__)), 'whole_building_energy_savings_fixture.json')
        ]

    def setUp(self):
        self.basedir = os.path.abspath(os.path.dirname(__file__))

    def test_util_findDateIndex(self):
        # Testing index finder for specific dates.
        a = datetime.datetime(2014, 1, 1, 0, 0, 0, 0)
        b = datetime.datetime(2014, 1, 2, 0, 0, 0, 0)
        datetime_list = numpy.array(set_up_datetimes(a, b, 3600)).flatten()
        testDateIndex = dtt.findDateIndex(
            datetime_list,
            datetime.datetime(2014, 1, 1, 7, 0, 0, 0)
            )
        self.assertEqual(testDateIndex, 0)
        testDateIndex = dtt.findDateIndex(
            datetime_list,
            datetime.datetime(2014, 2, 1, 0, 0, 0, 0)
            )
        self.assertEqual(testDateIndex, 24)

    def test_whole_building_energy_savings_base(self):
        wbes_base_ini = os.path.join(self.basedir,
            'whole_building_energy_savings_base.ini')
        wbes_base_exp = {}
        wbes_base_exp['DayTimeTemperatureModel'] = os.path.join(self.basedir,
            'whole_building_energy_savings_base.ref.csv')
        self.run_it(wbes_base_ini, wbes_base_exp, clean_up=True)
