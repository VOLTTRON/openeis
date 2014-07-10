from openeis.applications.utest_applications.apptest import AppTestBase
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
        spearExpect = self._findCorrelationCoeff(ranksMean1, ranksMean2, True)
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
        spearExpect = self._findCorrelationCoeff(ranksMean1, ranksMean2, True)
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
        spearExpect = self._findCorrelationCoeff(ranksMean1, ranksMean2, True)
        self.nearly_same(spear1_2, spearExpect, absTol=1e-18, relTol=1e-12)
        self.nearly_same(spear2_1, spearExpect, absTol=1e-18, relTol=1e-12)

