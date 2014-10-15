"""
Unit tests for Load Profiling application.

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
import os


class TestLoadProfiling(AppTestBase):
    fixtures = [os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            'load_profiling_fixture.json')]

    def setUp(self):
        self.basedir = os.path.abspath(os.path.dirname(__file__))

    def test_load_profiling_basic(self):
        lp_basic_ini = os.path.join(self.basedir,
            'load_profiling_basic.ini')
        lp_basic_exp = {}
        lp_basic_ini = os.path.join(self.basedir,
                                    'load_profiling_basic.ini')
        lp_basic_exp['Load_Profiling'] = os.path.join(self.basedir,
                                    'load_profiling_basic.ref.csv')

        self.run_it(lp_basic_ini, lp_basic_exp, clean_up=True)

    def test_load_profiling_missing(self):
        lp_missing_ini = os.path.join(self.basedir,
            'load_profiling_missing.ini')
        lp_missing_exp = {}
        lp_missing_ini = os.path.join(self.basedir,
                                    'load_profiling_missing.ini')
        lp_missing_exp['Load_Profiling'] = os.path.join(self.basedir,
                                    'load_profiling_missing.ref.csv')
        self.run_it(lp_missing_ini, lp_missing_exp, clean_up=True)

    def test_load_profiling_floats(self):
        lp_floats_ini = os.path.join(self.basedir,
            'load_profiling_floats.ini')
        lp_floats_exp = {}
        lp_floats_ini = os.path.join(self.basedir,
                                    'load_profiling_floats.ini')
        lp_floats_exp['Load_Profiling'] = os.path.join(self.basedir,,
                                    'load_profiling_floats.ref.csv')
        self.run_it(lp_floats_ini, lp_floats_exp, clean_up=True)

    def test_load_profiling_floats_missing(self):
        lp_floats_missing_ini = os.path.join(self.basedir,
            'load_profiling_floats_missing.ini')
        lp_floats_missing_exp = {}
        lp_floats_missing_ini = os.path.join(self.basedir,
                                    'load_profiling_floats_missing.ini')
        lp_floats_missing_exp['Load_Profiling'] = os.path.join(self.basedir,
                                    'load_profiling_floats_missing.ref.csv')
        self.run_it(lp_floats_missing_ini, lp_floats_missing_exp,
                clean_up=True)

