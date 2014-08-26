"""
Unit test `spearman.py`.

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
from testing_utils import findMean, findCorrelationCoeff
import spearman
import numpy as np

class TestSpearmanRank(AppTestBase):

    # Test ranking
    def test_rank_basic(self):
        row = [1, 2, 3, 4, 5]
        exp_ranks = np.array([1, 2, 3, 4, 5])
        ranks = spearman._rankForSpearman(np.array(row))
        self.nearly_same(ranks, exp_ranks, absTol=1e-18, relTol=1e-12)

    def test_rank_floats_and_ints(self):
        row = [5.0, 4.0, 3.0, 2, 1]
        exp_ranks = np.array([5, 4, 3, 2, 1])
        ranks = spearman._rankForSpearman(np.array(row))
        self.nearly_same(ranks, exp_ranks, absTol=1e-18, relTol=1e-12)

    def test_rank_floats(self):
        row = [1.0, 2.0, 1.0, 4.0, 5.0]
        exp_ranks = np.array([1.5, 3, 1.5, 4, 5])
        ranks = spearman._rankForSpearman(np.array(row))
        self.nearly_same(ranks, exp_ranks, absTol=1e-18, relTol=1e-12)

    def test_rank_same_num(self):
        row = [1.0, 1, 1]
        exp_ranks = np.array([2, 2, 2])
        ranks = spearman._rankForSpearman(np.array(row))
        self.nearly_same(ranks, exp_ranks, absTol=1e-18, relTol=1e-12)

    def test_rank_mostly_same_num(self):
        row = [9, 9, 3, 9, 9]
        exp_ranks = np.array([3.5, 3.5, 1, 3.5, 3.5])
        ranks = spearman._rankForSpearman(np.array(row))
        self.nearly_same(ranks, exp_ranks, absTol=1e-18, relTol=1e-12)

    def test_rank_few_floats(self):
        row = [6.6, 1.1, 3.3, 1.1]
        exp_ranks = np.array([4, 1.5, 3, 1.5])
        ranks = spearman._rankForSpearman(np.array(row))
        self.nearly_same(ranks, exp_ranks, absTol=1e-18, relTol=1e-12)

    # Test coefficient with self
    def test_coeff_self_basic(self):
        row = [1, 2, 3, 4, 5]
        coeff = spearman.findSpearmanRank(row, row)
        self.nearly_same(coeff, 1.0, absTol=1e-18, relTol=1e-12)

    def test_coeff_self_floats_ints(self):
        row = [5.0, 4.0, 3.0, 2, 1]
        coeff = spearman.findSpearmanRank(row, row)
        self.nearly_same(coeff, 1.0, absTol=1e-18, relTol=1e-12)

    def test_coeff_self_some_same(self):
        row = [1.0, 2.0, 1.0, 4.0, 5.0]
        coeff = spearman.findSpearmanRank(row, row)
        self.nearly_same(coeff, 1.0, absTol=1e-18, relTol=1e-12)

    # Test coefficient with others
    def test_coeff_basic(self):
        row1 = [1, 2, 3, 4, 5]
        ranks1 = np.array([1, 2, 3, 4, 5])
        ranksMean1 = ranks1 - 3
        row2 = [5.0, 4.0, 3.0,   2,   1]
        ranks2 = np.array([5, 4, 3, 2, 1])
        ranksMean2 = ranks2 - 3
        spear1_2 = spearman.findSpearmanRank(row1, row2)
        spear2_1 = spearman.findSpearmanRank(row2, row1)
        spearExpect = findCorrelationCoeff(ranksMean1, ranksMean2, True)
        self.assertTrue(spearExpect == -1)
        self.nearly_same(spear1_2, spearExpect, absTol=1e-18, relTol=1e-12)
        self.nearly_same(spear2_1, spearExpect, absTol=1e-18, relTol=1e-12)

    def test_coeff_with_same(self):
        row1 = [1, 2, 3, 4, 5]
        ranks1 = np.array([1, 2, 3, 4, 5])
        ranksMean1 = ranks1 - 3
        row2 = [1.0, 2.0, 1.0, 4.0, 5.0]
        ranks2 = np.array([1.5, 3, 1.5, 4, 5])
        ranksMean2 = ranks2 - np.mean(ranks2)
        spear1_2 = spearman.findSpearmanRank(row1, row2)
        spear2_1 = spearman.findSpearmanRank(row2, row1)
        spearExpect = findCorrelationCoeff(ranksMean1, ranksMean2, True)
        self.nearly_same(spear1_2, spearExpect, absTol=1e-18, relTol=1e-12)
        self.nearly_same(spear2_1, spearExpect, absTol=1e-18, relTol=1e-12)

    def test_coeff_with_same_and_floats(self):
        row1 = [5.0, 4.0, 3.0, 2, 1]
        ranks1 = np.array([5, 4, 3, 2, 1])
        ranksMean1 = ranks1 - 3
        row2 = [1.0, 2.0, 1.0, 4.0, 5.0]
        ranks2 = np.array([1.5, 3, 1.5, 4, 5])
        ranksMean2 = ranks2 - np.mean(ranks2)
        spear1_2 = spearman.findSpearmanRank(row1, row2)
        spear2_1 = spearman.findSpearmanRank(row2, row1)
        spearExpect = findCorrelationCoeff(ranksMean1, ranksMean2, True)
        self.nearly_same(spear1_2, spearExpect, absTol=1e-18, relTol=1e-12)
        self.nearly_same(spear2_1, spearExpect, absTol=1e-18, relTol=1e-12)
