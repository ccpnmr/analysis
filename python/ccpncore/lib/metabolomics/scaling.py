import numpy as np
from .centering import meanCenter


def varianceScale(spectrumCluster, power):

  stdevs = np.std(spectrumCluster, axis=0)
  scaled = spectrumCluster / (stdevs ** power)
  return scaled


def unitVarianceScale(spectrumCluster):

  return varianceScale(spectrumCluster, power=1)


def paretoScale(spectrumCluster):

  return varianceScale(spectrumCluster, power=0.5)


def rangeScale(spectrumCluster):

  specMins = spectrumCluster.min(axis=0)
  specMaxs = spectrumCluster.max(axis=0)
  diffs = specMaxs - specMins
  scaled = spectrumCluster / diffs
  return scaled


def vastScale(spectrumCluster):

  means = np.mean(spectrumCluster, axis=0)
  stdevs = np.std(spectrumCluster, axis=0)
  vScale = means / stdevs
  scaled = unitVarianceScale(spectrumCluster) * vScale
  return scaled


def levelScale(spectrumCluster):

  means = np.mean(spectrumCluster, axis=0)
  scaled = spectrumCluster / means
  return scaled


def autoScale(spectrumCluster):
  mc = meanCenter(spectrumCluster)
  scaled = unitVarianceScale(mc)
  return scaled
