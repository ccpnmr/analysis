__author__ = 'TJ Ragan'

import unittest

import numpy as np
import numpy.testing as npt

from ccpn.Metabolomics.lib.decomposition import PCA


class TestPCA(unittest.TestCase):
  def setUp(self):
    self.spectra = {'SP1-1': np.array([[2,1], [-1,-1]]),
                    'SP1-2': np.array([[2,1], [-2,-1]]),
                    'SP1-3': np.array([[2,1], [-3,-2]]),
                    'SP1-4': np.array([[2,1], [1,1]]),
                    'SP1-5': np.array([[2,1], [2,1]]),
                    'SP1-6': np.array([[2,1], [3,2]]),
                   }
    self.pca = PCA(self.spectra)

  def test_explained_variance(self):
    self.assertEqual(len(self.pca.explainedVariance), 2)
    self.assertAlmostEqual(self.pca.explainedVariance[0], 0.99244289)
    self.assertAlmostEqual(self.pca.explainedVariance[1], 0.00755711)

  def test_scores(self):
    self.assertEqual(len(self.pca.scores['PC1']), 6)
    self.assertEqual(len(self.pca.scores.loc['SP1-1']), 2)
    self.assertAlmostEqual(self.pca.scores.loc['SP1-1', 'PC1'], -1.38340577873)
    self.assertAlmostEqual(self.pca.scores['PC1']['SP1-1'], -1.38340577873)


  def test_loadings(self):
    self.assertEqual(len(self.pca.loadings['PC1']), 2)
    self.assertEqual(len(self.pca.loadings.loc[2]), 2)
    npt.assert_array_almost_equal(self.pca.loadings['PC1'], [0.838492, 0.544914])
    npt.assert_array_almost_equal(self.pca.loadings['PC2'], [0.544914, -0.838492])


if __name__ == '__main__':
  unittest.main()
