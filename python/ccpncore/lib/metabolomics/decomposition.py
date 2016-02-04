__author__ = 'TJ Ragan'

import numpy as np
import pandas as pd

import sklearn.decomposition

class PCA:
  '''
  For expediency, we're using the scikit-learn PCA algorithm, which mean centers just before the
  SVD step.  In the future we should implement our own to remove the forced mean centering.
  '''
  def __init__(self, spectra, nComponents=None):
    self.inputSpectra = spectra
    self.nComponents = nComponents
    self._translateData()
    self.fittedModel = self._fitPcaModel()

  @property
  def loadings(self):
    loadings = self._fittedPcaModel.components_.T
    columnNames = ['PC{}'.format(i+1) for i in range(loadings.shape[1])]
    loadingsDF = pd.DataFrame(loadings, index=self._inputDF.columns, columns=columnNames)
    loadingsDF.columns.rename('Principle Components', inplace=True)
    loadingsDF.index.rename('ppm', inplace=True)
    return loadingsDF

  @property
  def scores(self):
    scores = self._fittedPcaModel.transform(self._inputDF)
    colNames = ['PC{}'.format(i+1) for i in range(scores.shape[1])]
    scoresDF = pd.DataFrame(scores, index=self._inputDF.index, columns=colNames)
    scoresDF.columns.rename('Principle Components', inplace=True)
    scoresDF.index.rename('samples', inplace=True)
    return scoresDF

  @property
  def explainedVariance(self):
    return self._fittedPcaModel.explained_variance_ratio_


  def _translateData(self):
    l = [pd.Series(self.inputSpectra[name][1], index=self.inputSpectra[name][0], name=name)
         for name in sorted(self.inputSpectra.keys())]

    self._inputDF = pd.concat(l, axis=1).T


  def _fitPcaModel(self):
    self._fittedPcaModel = sklearn.decomposition.PCA(n_components=self.nComponents)
    self._fittedPcaModel.fit(self._inputDF)
