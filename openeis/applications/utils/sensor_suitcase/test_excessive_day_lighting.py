"""
Unit test `excessive_daylight_lighting.py`.


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
from openeis.applications.utils.sensor_suitcase.utils import separate_hours

import datetime as dt
import numpy as np
from openeis.applications.utils.sensor_suitcase.excessive_daylight_lighting import excessive_daylight

class TestExcessiveDaytimeLighting(AppTestBase):

    def test_excessive_day_light_ones(self):
        a = dt.datetime(2014, 1, 1, 0, 0, 0, 0)
        b = dt.datetime(2014, 1, 4, 0, 0, 0, 0)
        base = set_up_datetimes(a, b, 21600)

        light_all_ones = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

        append_data_to_datetime(base, light_all_ones)

        result = excessive_daylight(base, [[7,17],[1,2,3,4,5],[]], 100, 100)
        self.assertTrue('Problem' in result.keys())

    def test_excessive_day_light_zeroes(self):
        a = dt.datetime(2014, 1, 1, 0, 0, 0, 0)
        b = dt.datetime(2014, 1, 4, 0, 0, 0, 0)
        base = set_up_datetimes(a, b, 21600)

        light_all_ones = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        append_data_to_datetime(base, light_all_ones)

        result = excessive_daylight(base, [[7,17],[1,2,3,4,5],[]], 100, 100)
        self.assertTrue(result == {})

    def test_excessive_day_light_expect_fail(self):
        """Test: The lights are on throughout the whole occupied period."""
        a = dt.datetime(2014, 1, 1, 0, 0, 0, 0)
        b = dt.datetime(2014, 1, 3, 0, 0, 0, 0)
        base = set_up_datetimes(a, b, 3600)

        light_stat = np.zeros(len(base), bool)
        light_stat[7:17] = True
        light_stat[31:41] = True
        append_data_to_datetime(base, light_stat)

        result = excessive_daylight(base, [[7,17],[1,2,3,4,5],[]], 100, 100)
        self.assertTrue('Problem' in result.keys())

    def test_excessive_day_light_expect_success_on_off(self):
        """Test: The lights turn on and off twice during the occupied period."""
        a = dt.datetime(2014, 1, 1, 0, 0, 0, 0)
        b = dt.datetime(2014, 1, 2, 0, 0, 0, 0)
        base = set_up_datetimes(a, b, 3600)

        light_stat = np.zeros(len(base), bool)
        light_stat[7:11] = True
        light_stat[13:14] = True
        light_stat[16] = True
        append_data_to_datetime(base, light_stat)

        result = excessive_daylight(base, [[7,17],[1,2,3,4,5],[]], 100, 100)
        self.assertTrue(result == {})

    def test_excessive_day_light_expect_success_unoccupied_time(self):
        """Test: The lights not on during half of the whole occupied period."""
        a = dt.datetime(2014, 1, 1, 0, 0, 0, 0)
        b = dt.datetime(2014, 1, 2, 0, 0, 0, 0)
        base = set_up_datetimes(a, b, 3600)

        light_stat = np.zeros(len(base), bool)
        light_stat[15:23] = True
        append_data_to_datetime(base, light_stat)
        result = excessive_daylight(base, [[7,17],[1,2,3,4,5],[]], 100, 100)

        self.assertTrue(result == {})
