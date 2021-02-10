import numpy as np

def PQN(spectrumCluster):

  tsa = TSA(spectrumCluster)
  avg = tsa.mean(axis=0)
  quotients = tsa/avg
  medians = np.median(quotients, axis=1)
  pqn = (tsa.T/medians).T
  return pqn


def TSA(spectrumCluster):

  sums = spectrumCluster.sum(axis=1)
  tsa = (spectrumCluster.T/sums).T
  return tsa

def getSpectrumCluster(spectra):
  pointCount = spectra[0].pointCounts[0]
  array1 = np.empty([len(spectra), pointCount])
  for i in range(len(spectra)):
    array1[i] = spectra[i].getSliceData()

  return array1

def updateSpectrumCluster(spectra, spectrumCluster):
  for i in range(len(spectra)):
    plot = spectra[i].spectrumViews[0].plot
    xData = spectra[i].spectrumViews[0].data[0]
    yData = spectrumCluster[i]
    plot.setData(xData, yData)
