__author__ = 'simon'

from numpy import array, amin, amax, average, empty, nan, nanmin, fabs, subtract, where, argmax, NAN
from ccpn import Sample
# from ccpnmrcore.modules.SamplesTable import SampleTable
import math

def setupSamples(samples, n, mode, minimalOverlap):
  """ Analyses the peak positions in experiments (should be one reference experiment per component) and suggests samples with
      low overlap of at least one peak in each sample. ignoredRegions can be used to specify parts of the spectra that should
      be ignored. mode can be 'nSamples' or 'nComponentsPerSample' to choose if n is the number of wanted samples or the
      number of components in each sample. """

  expPeakCollection = []
  samplesData = []

  for sample in samples:
    for spectrum in sample.spectra:
      expPeaks = spectrum.peaks
      peaks = [peak.position for peak in sample.spectra[0].peaks]
      expPeakCollection.append(ExperimentPeaks(spectrum.name, expPeaks))

  cl = ObjectClustering(expPeakCollection, 'getPeaks', minimalOverlap)

  if mode == 'nSamples':
    clusters = cl.getNSamples(n)
  elif mode == 'nComponentsPerSample':
    clusters = cl.getNComponentsPerSample(n)

  for i, cluster in enumerate(clusters):
    project = samples[0].project
    newSample = project.newSample(name=str(i+1+len(project.samples)))
    samplesData.append(newSample)
    newSample.peakCollections = cluster
    newSample.spectra = [project.getByPid('SP:'+item.name) for item in cluster]

    results = array([scoring(obj, cluster, 'getPeaks', minimalOverlap) for obj in cluster])

    newSample.minScore = int(amin(results))
    newSample.averageScore = math.floor(average(results))
    nComponents = (len(cluster))

    # print('Name: %s, N Components: %.0f, MinScore: %.1f, AverScore: %.2f' %
    #       (newSample.pid, nComponents, newSample.minScore, newSample.averageScore))

    for obj in newSample.peakCollections:
      obj.sample = newSample
      obj.score = scoring(obj, newSample.peakCollections, 'getPeaks', minimalOverlap)
  return samplesData

def scoring(ExperimentPeaks, ListExperimentPeaks, getPeaks, minimalOverlap=None):

  """ The score is given by the distance of the best resolved peak to its closest neighbour. value =  Distance in ppm to
   closest peak. Smaller is the distance and consequently lower the score and more overalapped is that component to its neighbour. """

  ExperimentPeaksVals = array(getattr(ExperimentPeaks, getPeaks)()[:10])
  mins = empty((len(ExperimentPeaksVals), len(ListExperimentPeaks)))
  for i, b in enumerate(ListExperimentPeaks):
    if ExperimentPeaks == b:
      mins[:, i] = nan
      continue
    bVals = array(getattr(b, getPeaks)())
    diffs = fabs(subtract.outer(ExperimentPeaksVals, bVals))
    mins[:, i] = nanmin(diffs, 1)
  mins = nanmin(mins, 1)
  value = amax(mins)

  if value <= minimalOverlap:
    raise ValueError('Unable to generate Samples with a too low minimal overlap')

  if value > 0.20:
    return 10
  if value > 0.18:
    return 9
  if value > 0.16:
    return 8
  if value > 0.14:
    return 7
  if value > 0.12:
    return 6
  if value > 0.10:
    return 5
  if value > 0.08:
    return 4
  if value > 0.06:
    return 3
  if value > 0.04:
    return 2
  if value > 0.02:
    return 1
  if value < 0.02:
    return 0
  if value < 0.00:
    return -1

class ExperimentPeaks:

  def __init__(self, name, peaks):
    self.name = name
    peaks = peaks
    self.peakPositions = []
    self.score = None
    for peak in peaks:
      peakPosition = self.peakPositions
      self.peakPositions.append(peak.position[0])

  def getPeaks(self):#peaks in [numbers]
    return self.peakPositions

class ObjectClustering:

  def __init__(self, samples, peakLists, minimalOverlap):

    self.__data = samples
    self.peakLists = peakLists
    self.minimalOverlap = minimalOverlap
    self.__initial_length = len(samples)

  def getNSamples(self, n):

    self.initialiseClusters(self.__data, n)
    return self.__clusters

  def getNComponentsPerSample(self, n):

    nSample = math.floor(self.__initial_length / n)
    self.__initial_length = self.initialiseClusters(self.__data, nSample)
    return self.__clusters

  def initialiseClusters(self, samples, clustercount):
    self.__clusters = []
    for x in range(int(clustercount)):
      self.__clusters.append([])
    count = 0
    for sample in samples:
      if len(sample.peakPositions) > 0:
        self.__clusters[ int(count % (int(clustercount))) ].append(sample)
        count += 1
    return count
