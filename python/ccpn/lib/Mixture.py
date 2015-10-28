__author__ = 'simon'
from numpy import array, amin, amax, average, empty, nan, nanmin, fabs, subtract, where, argmax, NAN

from ccpn import Sample

class Mixture:
  """ This class is used for grouping and registering scores of mixtures when evaluating
      mixtures. """

  def __init__(self, name = None):

    self.name = name
    self.minScore = None
    self.averageScore = None
    self.pid = None
    self.peakCollections = [] # A list of peakCollections. Each compound in the mixture has one peakCollection.

class ExperimentPeakCollection:
  """ This class group peaks related to one compound in a mixture. It also contains the current
      score of this compound. """

  def __init__(self, name, peaks, mixture = None):

    self.name = name
    self.peaks = peaks # Data model peaks
    self.mixture = mixture
    self.peakPositions = []
    self.score = None
    for peak in peaks:
      self.peakPositions.append(peak.position[0])

  def getPeakPositions(self):

    return self.peakPositions


class ClusteringError(Exception):
   pass

class ObjectClustering:

  def __init__(self, data, getValue, distanceFunction):
    """
    Constructor

    PARAMETERS
        data     - A list of objects.
        getValue - A string containing the function name to get the relevant data from the object.
        distanceFunction - A function determining the distance between two items.
                  Default: It assumes the tuples contain numeric values and
                            appiles a generalised form of the
                            euclidian-distance algorithm on them.
    """
    self.__data = data
    self.getValue = getValue
    self.distanceFunction = distanceFunction
    self.__initial_length = len(data)

  def getNMixtures(self, n):
    """
    Generates <n> mixtures

    PARAMETERS
        n - The number of mixtures that should be generated.
            n must be greater than 1
    """

    # only proceed if we got sensible input
    if n <= 1:
      raise ClusteringError("When creating mixtures, you need to ask for at least two mixtures! You asked for %d." % n)

    # return the data straight away if there is nothing to cluster
    if self.__data == [] or len(self.__data) == 1 or n == self.__initial_length:
      return self.__data

    # It makes no sense to ask for more clusters than data-items available
    if n > self.__initial_length:
      raise ClusteringError( """Unable to generate more mixtures than compounds
available. You supplied %d compounds, and asked for %d mixtures.""" %
              (self.__initial_length, n) )

    self.initialiseClusters(self.__data, n)

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
        for item in cluster:
          res = self.assignItem(item, cluster, thisMove)
          if itemsMoved is False:
            itemsMoved = res
      #print thisMove, lastMove, sameMoveCnt, nIterations
      if lastMove == thisMove:
        sameMoveCnt += 1
      else:
        sameMoveCnt = 0
      lastMove = thisMove[:]
      nIterations += 1

    return self.__clusters

  def getNCompoundsPerMixture(self, n):
    """
    Generates mixtures with <n> compounds in each. There might be more or fewer if the compounds cannot be evenly distributed.

    PARAMETERS
        n - The number of compounds per mixture that should be generated.
            n must be greater than 1
    """

    # only proceed if we got sensible input
    if n <= 1:
      raise ClusteringError("When creating mixtures, you need to ask for at least two compounds per mixture! You asked for %d." % n)

    # return the data straight away if there is nothing to cluster
    if self.__data == [] or len(self.__data) == 1 or n == self.__initial_length:
      return self.__data

    # It makes no sense to ask for more clusters than data-items available
    if n > self.__initial_length:
      raise ClusteringError( """Unable to generate more compounds per mixture than compounds
available. You supplied %d compounds, and asked for %d compounds per mixture.""" %
              (self.__initial_length, n) )


    nMixtures = self.__initial_length / n

    self.__initial_length = self.initialiseClusters(self.__data, nMixtures)
    nMixtures = self.__initial_length / n

    #for cluster in self.__clusters:
      #print len(cluster), cluster, '\n'

    minNCompoundsPerMixture = self.__initial_length / nMixtures
    distanceFunction = self.distanceFunction
    getValue = self.getValue

    itemsMoved = True     # tells us if any item moved between the clusters,
                            # as we initialised the clusters, we assume that
                            # is the case
    lastMove = []
    sameMoveCnt = 0
    nIterations = 0

    tooFewCompoundsInNMixtures = 0

    while (itemsMoved is True or tooFewCompoundsInNMixtures) and sameMoveCnt < 10 and nIterations < self.__initial_length/3:
      thisMove = []
      itemsMoved = False
      for cluster in self.__clusters:
        for item in cluster:
          if nIterations > self.__initial_length / 6:
            res = self.assignItem(item, cluster, thisMove, False, minNCompoundsPerMixture)
          else:
            res = self.assignItem(item, cluster, thisMove, False, minNCompoundsPerMixture + 1)

          if itemsMoved is False:
            itemsMoved = res
          if res:
            if len(self.__clusters[thisMove[-1][1]]) == minNCompoundsPerMixture:
              tooFewCompoundsInNMixtures -= 1
            if len(cluster) == minNCompoundsPerMixture-1:
              tooFewCompoundsInNMixtures += 1
            break

      if thisMove and lastMove == thisMove:
        sameMoveCnt += 1
      else:
        sameMoveCnt = 0
      lastMove = thisMove[:]
      nIterations += 1
      if tooFewCompoundsInNMixtures <= 0:
        break

    sameMoveCnt = 0
    nIterations = 0
    # In this second stage make sure there are not too few or too many compounds in the mixtures.
    while (itemsMoved is True or tooFewCompoundsInNMixtures) and sameMoveCnt < 10 and nIterations < self.__initial_length:
      thisMove = []
      itemsMoved = False

      for cluster in self.__clusters:
        mustMove = len(cluster) > minNCompoundsPerMixture
        if mustMove:
          # Find the worst fitting component.
          worstItem = None
          worstScore = None
          for item in cluster:
            score = distanceFunction(item, cluster, getValue)
            if not worstScore or score < worstScore:
              worstScore = score
              worstItem = item

          res = self.assignItem(worstItem, cluster, thisMove, True, minNCompoundsPerMixture)
          if itemsMoved is False:
            itemsMoved = res
          if res:
            #print thisMove, len(self.__clusters[thisMove[-1][0]]), len(self.__clusters[thisMove[-1][1]])
            if len(self.__clusters[thisMove[-1][1]]) == minNCompoundsPerMixture:
              tooFewCompoundsInNMixtures -= 1
            if len(cluster) == minNCompoundsPerMixture-1:
              tooFewCompoundsInNMixtures += 1
            else:
              nIterations -= 1
            break

        else:
          for item in cluster:
            res = self.assignItem(item, cluster, thisMove, False, minNCompoundsPerMixture)
            if itemsMoved is False:
              itemsMoved = res
            if res:
              #print thisMove, len(self.__clusters[thisMove[-1][0]]), len(self.__clusters[thisMove[-1][1]])
              if len(self.__clusters[thisMove[-1][1]]) == minNCompoundsPerMixture:
                tooFewCompoundsInNMixtures -= 1
              if len(cluster) == minNCompoundsPerMixture-1:
                tooFewCompoundsInNMixtures += 1
              break

      #print thisMove, lastMove, sameMoveCnt, nIterations
      if thisMove and lastMove == thisMove:
        sameMoveCnt += 1
      else:
        sameMoveCnt = 0
      lastMove = thisMove[:]
      nIterations += 1
      if tooFewCompoundsInNMixtures <= 0:
        break

    return self.__clusters

  def assignItem(self, item, origin, thisMove, mustMove = False, minNCompoundsPerMixture = None):
    """
    Assigns an item from a given cluster to the cluster at smallest distance (inverted here to group divert items)

    PARAMETERS
        item   - the item to be moved
        origin - the originating cluster
    """

    getValue = self.getValue

    bestCluster = origin
    distanceFunction = self.distanceFunction
    if mustMove:
      bestClusterDist = -100
    else:
      bestClusterDist = distanceFunction(item, bestCluster, getValue)

    origDist = bestClusterDist

    if origDist == 5:
      return False
    #origLen = len(origin)

    for cluster in self.__clusters:
      if len(cluster) > 0:
        if cluster == origin or cluster == item:
          continue
        if minNCompoundsPerMixture and len(cluster) >= minNCompoundsPerMixture:
          continue

        if self.distanceFunction(item, cluster, getValue) > bestClusterDist:
          bestCluster = cluster
          bestClusterDist = distanceFunction(item, bestCluster, getValue)

    if bestCluster != origin:
      #print item.name, self.__clusters.index(origin), self.__clusters.index(bestCluster), bestClusterDist, origDist, origLen, len(bestCluster)
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

  def initialiseClusters(self, input, clustercount):
    """
    Initialises the clusters by distributing the items from the data evenly
    across n clusters

    PARAMETERS
        input        - the data set (a list of tuples)
        clustercount - the amount of clusters (n)
    """
    # initialise the clusters with empty lists
    self.__clusters = []
    # print(clustercount, 'clustercount', type(clustercount))
    for x in range(int(clustercount)):
      self.__clusters.append([])

    # distribute the items into the clusters
    count = 0
    for item in input:

      if len(item.peaks) > 0:
        self.__clusters[ int(count % (clustercount-1)) ].append(item)

        # print('count= ', count, 'clustercount =', clustercount,
        #       '\n int of count % clustercount)= ' , int(count % clustercount))

        count += 1
        # print('count+1= ', count)
        # print('item:', item)

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

def compare(a, bList, getValue):

  maxDiff = None


  aVals = array(getattr(a, getValue)()[:10])
  if not aVals.any():
    return None

  thisMaxDiff = None
  thisMinDiff = None
  mins = empty((len(aVals), len(bList)))
  for i, b in enumerate(bList):
    if a == b:
      mins[:, i] = nan
      continue
    bVals = array(getattr(b, getValue)())
    if not bVals.any():
      continue

    diffs = fabs(subtract.outer(aVals, bVals))
    mins[:, i] = nanmin(diffs, 1)

  mins = nanmin(mins, 1)
  maxDiff = amax(mins)
  #maxInd = argmax(mins)
  #maxDiff = mins[maxInd]

  if maxDiff == None:
    return 0.0000001

  maxDiff = max(maxDiff, 0.0000001)

  return maxDiff

def compareWithLevels(a, bList, getValue):
  """ Compares a with all objects in bList using the getValue function.
      The returned value is between 0 and 4 if  0.01 <= difference <= 0.15.
      If the difference is less than 0.01 or larger than 0.15 -10 or 5 is returned respectively. """

  value = compare(a, bList, getValue)

  if not value:
    return 0

  # if value > 0.15:
  #   return 5
  # if value > 0.10:
  #   return 4
  # if value > 0.08:
  #   return 3
  # if value > 0.06:
  #   return 2
  # if value > 0.04:
  #   return 1
  # if value < 0.01:
  #   return -10

  if value > 0.50:
    return 10
  if value > 0.40:
    return 9
  if value > 0.30:
    return 8
  if value > 0.20:
    return 7
  if value > 0.18:
    return 6
  if value > 0.15:
    return 5
  if value > 0.10:
    return 4
  if value > 0.08:
    return 3
  if value > 0.06:
    return 2
  if value > 0.04:
    return 1
  if value > 0.02:
    return 0
  if value < 0.02:
    return -1
  if value < 0.01:
    return -2



  return 0

def getPeaksFromExperiment(spectrum, ignoredRegions=None, nMaxPeaks=10):
  return spectrum.peakLists[0].peaks

def setupMixtures(spectra, n, mode):
  """ Analyses the peak positions in experiments (should be one reference experiment per compound) and suggests mixtures with
      low overlap of at least one peak in each mixture. ignoredRegions can be used to specify parts of the spectra that should
      be ignored. mode can be 'nMixtures' or 'nCompoundsPerMixture' to choose if n is the number of wanted mixtures or the
      number of compounds in each mixture. """

  projectId = None
  project = None
  nmrProjectId = None
  nmrProject = None
  expPeakCollection = []

  mixturesData = []

  for spectrum in spectra:
    expPeaks = getPeaksFromExperiment(spectrum, nMaxPeaks = 10)
    #if expPeaks:
    expPeakCollection.append(ExperimentPeakCollection(spectrum.name, expPeaks))

  cl = ObjectClustering(expPeakCollection, 'getPeakPositions', compareWithLevels)
  if mode == 'nMixtures':
    clusters = cl.getNMixtures(n)
  elif mode == 'nCompoundsPerMixture':
    clusters = cl.getNCompoundsPerMixture(n)
  else:
    return []

  for i, cluster in enumerate(clusters):


    project = spectrum.project
    currentMixture = project.newSample(name=str(i+1))




    # currentMixture.pid = 'SA:%s' % str(i+1)

    mixturesData.append(currentMixture)
    currentMixture.peakCollections = cluster
    results = array([compareWithLevels(obj, cluster, 'getPeakPositions') for obj in cluster])
    try:
      currentMixture.minScore = amin(results)
      currentMixture.averageScore = average(results)
    except ValueError:
      pass



    # print("Sample %d, components:  %d" % (currentMixture.name, (len(currentMixture.peakCollections)-1)))
    #
    # print("Sample", currentMixture.name)
    # print("Average score", currentMixture.averageScore)
    #
    # if currentMixture.minScore is not None:
    #   print("Minimum score", currentMixture.minScore)
    #
    # print("Mixture %d, %d compounds, score %.0f:" % (currentMixture.name, (len(currentMixture.peakCollections)-1), currentMixture.minScore ))


    # resultMixture = ("Sample %d, %d components, score %.0f:, average %.1f:" % (currentMixture.name, (len(currentMixture.peakCollections)-1), currentMixture.minScore,  currentMixture.averageScore ))

    # print([e.name for e in currentMixture.peakCollections])
    # print(dir(currentMixture.name))
    # "%.1f", currentMixture.avScore

    for obj in currentMixture.peakCollections:
      obj.mixture = currentMixture
      obj.score = compareWithLevels(obj, currentMixture.peakCollections, 'getPeakPositions')
      #print obj.name, [round(pos, 3) for pos in obj.getPeakPositions()], obj.score
    #print ""

    from application.core.modules.ScoringMixture import MixtureTable


  return mixturesData

def evaluateMixtures(project, mixtures):
  """ Evaluate how well separated the peaks of the components in the mixture are. """

  mixturesData = []

  # refDataStores = project.refDataStores

  nMixtures = 0

  for name, mixture in mixtures.items():
    currentMixture = Sample(name = name)
    for compound in mixture:
      # exp = getReferenceDataExperimentOfCompound(refDataStores, compound)
      # if not exp:
      #   print compound, 'not found in reference data project.'
      #   continue

      expPeaks = getPeaksFromExperiment(exp, nMaxPeaks = 10)
      #if not expPeaks:
        #continue
      currentMixture.peakCollections.append(ExperimentPeakCollection(compound, expPeaks, currentMixture))

    nMixtures += 1
    mixturesData.append(currentMixture)

  for i, currentMixture in enumerate(mixturesData):
    results = array([compareWithLevels(obj, currentMixture.peakCollections, 'getPeakPositions') for obj in currentMixture.peakCollections])
    currentMixture.minScore = amin(results)
    currentMixture.averageScore = average(results)
    # print ("Mixture %d, %d compounds, score %.0f, %.1f:" % (currentMixture.name, len(currentMixture.peakCollections), currentMixture.minScore, currentMixture.averageScore))
    for obj in currentMixture.peakCollections:
      obj.score = compareWithLevels(obj, currentMixture.peakCollections, 'getPeakPositions')
      #print obj.name, [round(pos, 3) for pos in obj.getPeakPositions()], obj.score
    #print ""

  return mixturesData