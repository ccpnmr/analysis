__author__ = 'simon'
from numpy import array, amin, amax, average, empty, nan, nanmin, fabs, subtract, where, argmax, NAN
from ccpn import Sample


# class Sample:
#   """ This class is used for grouping and registering scores of samples when evaluating
#       samples. """
#
#   def __init__(self, name = None):
#
#     self.name = name
#     self.minScore = None
#     self.averageScore = None
#     self.pid = None
#     self.peakCollections = [] # A list of peakCollections. Each component in the sample has one peakCollection.

class ExperimentPeakCollection:
  """ This class group peaks related to one component in a sample. It also contains the current
      score of this component. """

  def __init__(self, name, peaks, sample = None):

    self.name = name
    self.peaks = peaks # Data model peaks
    self.sample = sample
    self.peakPositions = []
    self.score = None
    for peak in peaks:
      # print('peak',peak)
      self.peakPositions.append(peak.position[0])

  def getPeakPositions(self):

    return [peak.position[0] for peak in self.sample.peaks]


class ClusteringError(Exception):
   pass

class ObjectClustering:

  def __init__(self, samples, distanceFunction):
    """
    Constructor

    PARAMETERS
        data     - A list of objects.
        distanceFunction - A function determining the distance between two items.
                  Default: It assumes the tuples contain numeric values and
                            appiles a generalised form of the
                            euclidian-distance algorithm on them.
    """
    self.__data = samples
    self.distanceFunction = distanceFunction
    self.__initial_length = len(samples)

  def getNSamples(self, n):


    if self.__samples == [] or len(self.__samples) == 1 or n == self.__initial_length:
      return self.__samples

    ##____ It makes no sense to ask for more clusters than data-items available
    if n > self.__initial_length:
      raise ClusteringError( """Unable to generate more Samples than components
       available. You supplied %d components, and asked for %d Samples.""" %
       (self.__initial_length, n) )

    self.initialiseClusters(self.__samples, n)

    itemsMoved = True     # tells us if any item moved between the clusters,
                            # as we initialised the clusters, we assume that
                            # is the case
    lastMove = []
    sameMoveCnt = 0
    nIterations = 0

    while itemsMoved is True and sameMoveCnt < 5 and nIterations < n:
      thisMove = []
      itemsMoved = False
      for cluster in self.__clusters:
        for sample in cluster:
          res = self.assignItem(sample, cluster, thisMove)
          if itemsMoved is False:
            itemsMoved = res

      if lastMove == thisMove:
        sameMoveCnt += 1
      else:
        sameMoveCnt = 0
      lastMove = thisMove[:]
      nIterations += 1

    return self.__clusters

  def getNComponentsPerSample(self, n):

    # return the data straight away if there is nothing to cluster
    if self.__data == [] or len(self.__data) == 1 or n == self.__initial_length:
      return self.__data

    # It makes no sense to ask for more clusters than data-items available
    if n > self.__initial_length:
      raise ClusteringError( """Unable to generate more components per sample than components
              available. You supplied %d components, and asked for %d components per sample.""" %
              (self.__initial_length, n) )


    nSamples = self.__initial_length / n
    self.__initial_length = self.initialiseClusters(self.__data, nSamples)
    nSamples = self.__initial_length / n
    minNComponentsPerSample = self.__initial_length / nSamples
    distanceFunction = self.distanceFunction
    itemsMoved = True     # tells us if any item moved between the clusters,
                            # as we initialised the clusters, we assume that
                            # is the case
    lastMove = []
    sameMoveCnt = 0
    nIterations = 0

    tooFewComponentsInNSamples = 0

    while (itemsMoved is True or tooFewComponentsInNSamples) and sameMoveCnt < 10 and nIterations < self.__initial_length/3:
      thisMove = []
      itemsMoved = False
      for cluster in self.__clusters:
        for item in cluster:
          if nIterations > self.__initial_length / 6:
            res = self.assignItem(item, cluster, thisMove, False, minNComponentsPerSample)
          else:
            res = self.assignItem(item, cluster, thisMove, False, minNComponentsPerSample + 1)

          if itemsMoved is False:
            itemsMoved = res
          if res:
            if len(self.__clusters[thisMove[-1][1]]) == minNComponentsPerSample:
              tooFewComponentsInNSamples -= 1
            if len(cluster) == minNComponentsPerSample-1:
              tooFewComponentsInNSamples += 1
            break

      if thisMove and lastMove == thisMove:
        sameMoveCnt += 1
      else:
        sameMoveCnt = 0
      lastMove = thisMove[:]
      nIterations += 1
      if tooFewComponentsInNSamples <= 0:
        break

    sameMoveCnt = 0
    nIterations = 0
    ###____  In this second stage make sure there are not too few or too many components in the samples.
    while (itemsMoved is True or tooFewComponentsInNSamples) and sameMoveCnt < 10 and nIterations < self.__initial_length:
      thisMove = []
      itemsMoved = False

      for cluster in self.__clusters:
        mustMove = len(cluster) > minNComponentsPerSample
        print('mustMove', mustMove)
        if mustMove:
          ##____  Find the worst fitting component.
          worstItem = None
          worstScore = None
          for item in cluster:
            score = distanceFunction(item, cluster)
            if not worstScore or score < worstScore:
              worstScore = score
              worstItem = item

          res = self.assignItem(worstItem, cluster, thisMove, True, minNComponentsPerSample)
          if itemsMoved is False:
            itemsMoved = res
          if res:

            if len(self.__clusters[thisMove[-1][1]]) == minNComponentsPerSample:
              tooFewComponentsInNSamples -= 1
            if len(cluster) == minNComponentsPerSample-1:
              tooFewComponentsInNSamples += 1
            else:
              nIterations -= 1
            break

        else:
          for item in cluster:
            res = self.assignItem(item, cluster, thisMove, False, minNComponentsPerSample)
            if itemsMoved is False:
              itemsMoved = res
            if res:

              if len(self.__clusters[thisMove[-1][1]]) == minNComponentsPerSample:
                tooFewComponentsInNSamples -= 1
              if len(cluster) == minNComponentsPerSample-1:
                tooFewComponentsInNSamples += 1
              break

      if thisMove and lastMove == thisMove:
        sameMoveCnt += 1
      else:
        sameMoveCnt = 0
      lastMove = thisMove[:]
      nIterations += 1
      if tooFewComponentsInNSamples <= 0:
        break

    return self.__clusters

  def assignItem(self, item, origin, thisMove, mustMove = False, minNComponentsPerSample = None):
    """
    Assigns an item from a given cluster to the cluster at smallest distance (inverted here to group divert items)

    PARAMETERS
        item   - the item to be moved
        origin - the originating cluster
    """

    bestCluster = origin
    distanceFunction = self.distanceFunction
    if mustMove:
      bestClusterDist = -100
    else:
      bestClusterDist = distanceFunction(item, bestCluster)

    origDist = bestClusterDist
    print(item, bestCluster, bestClusterDist, 'ibb')

    if origDist == 5:
      return False

    for cluster in self.__clusters:
      if len(cluster) > 0:
        if cluster == origin or cluster == item:
          continue
        if minNComponentsPerSample and len(cluster) >= minNComponentsPerSample:
          continue

        if self.distanceFunction(item, cluster) > bestClusterDist:
          bestCluster = cluster
          bestClusterDist = distanceFunction(item, bestCluster)

    if bestCluster != origin:

      self.moveItem(item, origin, bestCluster)
      thisMove.append((self.__clusters.index(origin), self.__clusters.index(bestCluster)))
      return True
    else:
      return False

  def moveItem(self, item, origin, destination):
    """
    Moves an item from one cluster to another cluster

    PARAMETERS

        item        - the item to be moved
        origin      - the originating cluster
        destination - the target cluster
    """
    destination.append( origin.pop( origin.index(item) ) )

  def initialiseClusters(self, samples, clustercount):
    """
    Initialises the clusters by distributing the items from the data evenly
    across n clusters

    PARAMETERS
        input        - the data set (a list of tuples)
        clustercount - the amount of clusters (n)
    """
    ###____  initialise the clusters with empty lists
    self.__clusters = []

    for x in range(int(clustercount)):
      self.__clusters.append([])

    ##____  distribute the items into the clusters
    count = 1
    for sample in samples:

      if len(sample.spectra[0].peaks) > 0:
        self.__clusters[ int(count % (int(clustercount))) ].append(sample)
        count += 1

    return count

def getReferenceDataExperiments(refDataStores, solvent = None, temperature = None, pH = None):
  """ Gets all Experiments of the RefNmrSpectra in refDataStores.

      refDataStores is a list of dataStores in which to look for RefSampleComponentStores.
      If solvent, temperature and pH is provided it will try to find
      experiments matching those parameters, if available. If that cannot be done it will find experiments
      matching as many of the parameters as possible with priority solvent > temperature > pH. The
      tolerance for temperature is 5 K and for pH 1.
      The experiments of the dataSources of all RefNmrSpectra are returned.
  """
  experiments = set()

  for refDataStore in refDataStores:
    componentStore = refDataStore.refSampleComponentStore
    for component in componentStore.components:
      compExps = set()
      refNmrSpectra = refDataStore.findAllRefNmrSpectra(componentName = component.name)
      if len(refNmrSpectra) > 1:
        for i in range(4):
          for refNmrSpectrum in refNmrSpectra:
            if i < 3 and solvent and solvent != 'any' and refNmrSpectrum.solvent != solvent:
              continue
            if i < 2 and temperature != None and (refNmrSpectrum.temperature == None or abs(refNmrSpectrum.temperature - temperature) > 5):
              continue
            if i < 1 and pH != None and (refNmrSpectrum.pH == None or abs(refNmrSpectrum.pH - pH) > 1):
              continue
            if refNmrSpectrum.dataSource:
              compExps.add(refNmrSpectrum.dataSource.experiment)

      elif refNmrSpectrum.dataSource:
        compExps.add(refNmrSpectra.pop().dataSource.experiment)

      # If there is more than one experiment pick the most recent one.
      compExps = sorted(compExps, key=lambda exp: exp.date, reverse = True)
      if compExps:
        experiments.add(compExps[0])

  return experiments

def compare(a, bList):

  maxDiff = None
  if len(a.spectra) > 0:
    aVals = array([peak.position[0] for peak in a.spectra[0].peaks][:10])
    if not aVals.any():
      return None
    # print('a', a, 'bList', bList)
    thisMaxDiff = None
    thisMinDiff = None
    mins = empty((len(aVals), len(bList)))
    for i, b in enumerate(bList):
      if a == b:
        mins[:, i] = nan
        continue
      bVals = array([peak.position[0] for peak in a.spectra[0].peaks])
      if not bVals.any():
        continue

      diffs = fabs(subtract.outer(aVals, bVals))
      mins[:, i] = nanmin(diffs, 1)
    mins = nanmin(mins, 1)
    maxDiff = amax(mins)

    if maxDiff == None:
      return 0.0000001

    maxDiff = max(maxDiff, 0.0000001)
    return maxDiff

def compareWithLevels(a, bList):
  """

  The score is given by the distance of the best resolved peak to its closest neighbour.
  value =  Distance in ppm to closest peak
  if the closest peak to the considered one is distant more the 0.60ppm is return a minimal score of 10.
  Smaller is the distance and consequently lower the score and more overalapped is that component to its neighbour.

       """

  value = compare(a, bList)

  if not value:
    return 0

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
  #
  # if value < 0.00:
  #   return -1

  return 0

def getPeaksFromExperiment(spectrum, ignoredRegions=None, nMaxPeaks=10):
  return spectrum.peakLists[0].peaks

def setupSamples(samples, n, mode):
  """ Analyses the peak positions in experiments (should be one reference experiment per component) and suggests samples with
      low overlap of at least one peak in each sample. ignoredRegions can be used to specify parts of the spectra that should
      be ignored. mode can be 'nSamples' or 'nComponentsPerSample' to choose if n is the number of wanted samples or the
      number of components in each sample. """

  projectId = None
  project = None
  nmrProjectId = None
  nmrProject = None
  expPeakCollection = []
  # print(samples, 'inside setupSamples')
  samplesData = []
  # for sample in samples:
  #   expPeakCollection.append(ExperimentPeakCollection(spectrum.name, expPeaks))

  # cl = ObjectClustering(samples, 'getPeakPositions', compareWithLevels)
  cl = ObjectClustering(samples, compareWithLevels)

  if mode == 'nSamples':
    clusters = cl.getNSamples(n)
  elif mode == 'nComponentsPerSample':
    clusters = cl.getNComponentsPerSample(n)
  else:
    return []
  # print('clusters',clusters)

  project = samples[0].project

  for i, cluster in enumerate(clusters):
    print('cluster',cluster)

    newSample = project.newSample(name=str(i+10+len(project.samples)))
    for sample in cluster:
      for spectrum in sample.spectra:
        spectrum.sample = newSample
    samplesData.append(newSample)

    results = array([compareWithLevels(obj, cluster) for obj in cluster])
    print(results)
    try:
      newSample.minScore = str(amin(results))
      newSample.averageScore = average(results)


    except ValueError:
      pass
  #
  #   for obj in newComp.peakCollections:
  #     obj.sample = currentSample
  #     obj.score = compareWithLevels(obj, newComp.peakCollections, 'getPeakPositions')
  #
  #   from ccpnmrcore.modules.SamplesTable import SampleTable
  #
  return samplesData

def evaluateSamples(project, samples):
  """ Evaluate how well separated the peaks of the components in the sample are. """

  samplesData = []
  nSamples = 0

  for name, sample in samples.items():
    currentSample = Sample(name = name)
    for component in sample:
      expPeaks = getPeaksFromExperiment(exp, nMaxPeaks = 10)
      currentSample.peakCollections.append(ExperimentPeakCollection(component, expPeaks, currentSample))
    nSamples += 1
    samplesData.append(currentSample)

  for i, currentSample in enumerate(samplesData):
    results = array([compareWithLevels(obj, currentSample.peakCollections, 'getPeakPositions') for obj in currentSample.peakCollections])
    currentSample.minScore = amin(results)
    currentSample.averageScore = average(results)
    print ("Sample %d, %d Components, score %.0f, %.1f:" % (currentSample.name, len(currentSample.peakCaollections), currentSample.minScore, currentSample.averageScore))
    for obj in currentSample.peakCollections:
      obj.score = compareWithLevels(obj, currentSample.peakCollections, 'getPeakPositions')

  return samplesData