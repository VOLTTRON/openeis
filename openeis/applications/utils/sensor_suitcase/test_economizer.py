"""
Unit test `economizer.py`.


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

import datetime
from openeis.applications.utils.sensor_suitcase.economizer import economizer
import copy

class TestEconomizer(AppTestBase):

    def test_economizer_basic(self):
        a = datetime.datetime(2014, 1, 1, 0, 0, 0, 0)
        b = datetime.datetime(2014, 1, 4, 0, 0, 0, 0)
        #delta = 6 hours
        base = set_up_datetimes(a, b, 21600)

        DAT = copy.deepcopy(base)
        DAT_temp = [69, 69, 69, 69, 69, 69, 69, 69, 69, 69, 69, 69, 69]
        append_data_to_datetime(DAT, DAT_temp)

        OAT = copy.deepcopy(base)
        OAT_temp = [65, 65, 65, 65, 65, 65, 65, 65, 65, 65, 65, 65, 65]
        append_data_to_datetime(OAT, OAT_temp)

        HVACstat = copy.deepcopy(base)
        HVAC_data = [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
        append_data_to_datetime(HVACstat, HVAC_data)

        result = economizer(DAT, OAT, HVACstat, 10000, 5000)
        expected = {
            'Problem': "Under use of 'free cooling', i.e.,under-economizing.",
            'Diagnostic': "More than 30 percent of the time, the " + \
                    "economizer is not taking advantage of 'free cooling' " + \
                    "when it is possible to do so.",
            'Recommendation': "Ask an HVAC service contractor to check " + \
                    "the economizer control sequence, unless the RTU does" + \
                    "not have an economizer.",
            'Savings': 0.16 * 10000 * 0.1
            }

        self.assertEqual(expected, result)


    def test_economizer_no_flag(self):
        a = datetime.datetime(2014, 1, 1, 0, 0, 0, 0)
        b = datetime.datetime(2014, 1, 4, 0, 0, 0, 0)
        #delta = 6 hours
        base = set_up_datetimes(a, b, 21600)

        DAT = copy.deepcopy(base)
        DAT_temp = [69, 69, 69, 69, 69, 69, 69, 69, 69, 69, 69, 69, 69]
        append_data_to_datetime(DAT, DAT_temp)

        OAT = copy.deepcopy(base)
        OAT_temp = [65, 65, 65, 65, 65, 65, 65, 65, 65, 65, 65, 65, 65]
        append_data_to_datetime(OAT, OAT_temp)

        HVACstat = copy.deepcopy(base)
        HVAC_data = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        append_data_to_datetime(HVACstat, HVAC_data)

        result = economizer(DAT, OAT, HVACstat, 10000, 5000)
        expected = {}

        self.assertEqual(expected, result)
