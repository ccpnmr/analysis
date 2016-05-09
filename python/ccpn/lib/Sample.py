""" Ccpn-specific variant of functions for sorting and comparison."""

#=========================================================================================
#  Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2016-03-07 16:38:17 +0000 (Mon, 07 Mar 2016) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: simon $"
__date__ = "$Date: 2016-03-07 16:38:17 +0000 (Mon, 07 Mar 2016) $"
__version__ = "$Revision: 9128 $"

#=========================================================================================
# Start of code
#=========================================================================================
from numpy import array, amin, amax, average, empty, nan, nanmin, fabs, subtract, where, argmax, NAN
import math
from collections import defaultdict
from itertools import chain, combinations


def setupSamples(spectra=None, mode:str=None, n:int=None, minimalOverlap:float=None, mixtureName:str=None):
  """ Analyses the peak positions in experiments (should be one reference experiment per component) and suggests samples with
      low overlap of at least one peak in each sample. ignoredRegions can be used to specify parts of the spectra that should
      be ignored. mode can be 'nSamples' or 'nComponentsPerSample' to choose if n is the number of wanted samples or the
      number of components in each sample. """

  if mixtureName is None:
    mixtureName = 'Mixture-1' # arbitrary

  cluster = ObjectClustering(spectra)

  if mode == 'nSamples':
    cluster.mixtures = cluster.getNSamples(n)
    cluster.name = mixtureName
    createSample(cluster)

  if mode == 'nComponentsPerSample':
    cluster.mixtures = cluster.getNComponentsPerSample(n)
    cluster.name = mixtureName
    createSample(cluster)

  if mode == 'bestMatch':
    cluster = bestMatch(spectra, minimalOverlap)
    cluster.name = mixtureName
    if cluster:
      createSample(cluster)
    else:
      print('impossible to create Mixture with at least ', minimalOverlap , 'ppm minimalOverlap')


def bestMatch(spectra, minimalOverlap):
  '''
  This function creates all possible clusters. From one cluster with one mixture with all spectra
  until a cluster with the maximum number of mixtures with at least 2 spectra in each.
  The minimum score is calculated for each spectrum in each mixture. Each cluster is given the minimum score of the mixture.
  :return: cluster with less mixtures (higher num of spectra inside) with best score
  '''
  num = [x for x in reversed(range(len(spectra))) if x >= 2]

  clusters = []
  if len(num)>0:
    for n in num:
      cluster = ObjectClustering(spectra)
      cluster.mixtures = cluster.getNComponentsPerSample(n)
      cluster.name = 'Cluster'+str(n)
      cluster.numOfMixtures = str(len(cluster.mixtures))
      clusters.append(cluster)

  for cluster in clusters:
    scores = []
    for mixture in cluster.mixtures:
      results = array([scoring(spectrum, mixture, minimalOverlap)[1] for spectrum in mixture])
      minimumScore = amin(results)
      scores.append(float(minimumScore))
    cluster.minScore = amin(scores)
    if cluster.minScore >= minimalOverlap:
      return cluster



def createSample(cluster):
  project = cluster.mixtures[0][0].project
  samplesData = []
  for sample in project.samples:
    text, space, serialMixture, = sample.name.partition('-')
    clusterNum, mixtureNum = serialMixture.split('-')
    clusterNum = int(clusterNum)
    clusterNum +=1
    cluster.name = text+space+str(clusterNum)


  for i, mixture in enumerate(cluster.mixtures):
      project = mixture[0].project

      newMixture = project.newSample(name=(cluster.name+'-'+str(i+1)))
      samplesData.append(newMixture)
      newMixture.spectra = [spectrum for spectrum in mixture]

      for spectrum in mixture:
        newMixtureComponent = newMixture.newSampleComponent(name=(str(spectrum.name)), labeling='H')
        spectrum.score = scoring(spectrum, newMixture.spectra)
        newMixtureComponent.score = spectrum.score

      results = array([scoring(spectrum, newMixture.spectra)[0] for spectrum in newMixture.spectra])
      newMixture.minScore = int(amin(results))
      newMixture.averageScore = math.floor(average(results))
  return samplesData


def allCombinations(ss, value): #Test only
  return chain(*map(lambda x: combinations(ss, x), range(value,value+1)))


def scoring(spectrum, mixtureSpectra, minimalOverlap=None):
  """ The score is given by the distance of the best resolved peak to its closest neighbour. value =  Distance in ppm to
   closest peak. Smaller is the distance and consequently lower the score and more overlapped is that component to its neighbour.
   func used:
   - empty: returns a new array of given shape and type, without initializing entries. Parameters: shape and type
   - nanmin: returns minimum of an array or minimum along an axis, ignoring any NaNs.
   - ufunc.outer(A, B) applies the ufunc op to all pairs (a, b) with a in A and b in B
   - fabs: returns the absolute values
    """

  peakPos = [peak.position[0] for peak in spectrum.peaks]

  peakPosArray = array(peakPos[:10])

  mins = empty((len(peakPosArray), len(mixtureSpectra)))
  #empty returns a new array of given shape and type, without initializing entries.
  #Parameters: shape and type

  for i, spectrumB in enumerate(mixtureSpectra):

    if spectrum == spectrumB:
      mins[:, i] = nan
      continue

    spectrumBpositions = [peak.position[0] for peak in spectrumB.peaks]
    global spectrumBpositions
    peakPositionArray = array([peak.position[0] for peak in spectrumB.peaks])
    diffs = fabs(subtract.outer(peakPosArray, peakPositionArray))
    mins[:, i] = nanmin(diffs, 1)

  mins = nanmin(mins, 1)

  value = amin(mins)


  if value > 0.020:
    return [10, 0.20]

  if value > 0.018:
    return [9, 0.018]

  if value > 0.016:
    return [8, 0.016]

  if value > 0.014:
    return [7, 0.014]

  if value > 0.012:
    return [6, 0.012]

  if value > 0.10:
    return [5, 0.10]

  if value > 0.08:
    return [4, 0.08]

  if value > 0.06:
    return [3, 0.06]

  if value > 0.04:
    print([posA for posB in spectrumBpositions for posA in peakPos if abs(posA-posB)<0.04],'value', value, spectrum)
    return [2, 0.04]

  if value > 0.02:
    print([posA for posB in spectrumBpositions for posA in peakPos if abs(posA-posB)<0.03],'value', value, spectrum)
    return [1, 0.02]

  if value < 0.02:
    print([posA for posB in spectrumBpositions for posA in peakPos if abs(posA-posB)<0.02],'value', value, spectrum)
    return [0, 0.01]

  if value < 0.00:
    return [-1, 0.00]


class ObjectClustering:

  def __init__(self, spectra):
    self.spectra = spectra
    self.initialLength = len(spectra)
    self.name = str
    self.numOfMixtures = int

  def getNSamples(self, n):
    self.initialiseClusters(self.spectra, n)
    return self.__clusters

  def getNComponentsPerSample(self, n):
    nSample = math.floor(self.initialLength / n)
    self.initialLength = self.initialiseClusters(self.spectra, nSample)
    return self.__clusters

  def initialiseClusters(self, spectra, clustercount):
    self.__clusters = []
    for x in range(int(clustercount)):
      self.__clusters.append([])
    count = 0

    for spectrum in spectra:
      peaks = [peak.position[0] for peak in spectrum.peaks]
      if len(peaks) > 0:
        self.__clusters[ int(count % (int(clustercount))) ].append(spectrum)
        count += 1
    return count