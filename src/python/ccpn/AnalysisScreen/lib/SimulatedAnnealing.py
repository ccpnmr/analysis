#  Part of the Simulated Annealing algorithm is inspired by NMRmix.
#  As pubblished in J.L. Stark, et al. NMRmix: a tool for the optimization of compound mixtures in 1D (1)H NMR ligand affinity screens
#  J Proteome Res, 15 (2016), pp. 1360–1368

import math
import random
import copy


def generatePeakPositions(numberOfPeaks, ppmStart, ppmEnd):
  peakPositions = []
  for x in range(numberOfPeaks):
    peakPositions.append(random.uniform(ppmStart, ppmEnd))
  return sorted(peakPositions)

def randomDictMixtures(name, compounds, nMixtures):
  mixturesDict = {}
  n,b,mixtures = len(compounds),0,[]
  compounds = list(compounds)
  for k in range(nMixtures):
      a, b = b, b + (n+k)//nMixtures
      key = str(name)+'-'+str(k+1)
      value = compounds[a:b]
      mixturesDict.update({key:value})
  return mixturesDict


def generateSimpleCompounds(numb, numberOfPeaks, ppmStart, ppmEnd):
  compounds = []
  for i in range(numb):
    compound = generatePeakPositions(numberOfPeaks, ppmStart, ppmEnd)
    compounds.append(compound)
  return compounds


def scoreCompound(compoundA, compoundB, minDist, scalingFactor=1):
  overlapCount = 0
  for shiftA in compoundA:
    for shiftB in compoundB:
      if abs(shiftA - shiftB) < minDist:
        overlapCount += 1
        continue
  return (scalingFactor * (overlapCount / len(compoundA)))


def scoreMixture(mixture, minDist):
  score = 0
  for compoundA in mixture:
    for compoundB  in mixture:
      if compoundA[0] is not compoundB[0]:
        score += scoreCompound(compoundA[1], compoundB[1], minDist=minDist)
  return score


def calculateTotalScore(mixturesDict, peaksDistance=0.01):
  score = 0
  for mixture in mixturesDict:
    score += scoreMixture(mixturesDict[mixture], peaksDistance)
  return (score)


def getAllOverlappedPositions(mixtures, minDist):

  for mixtureName, compounds in mixtures.items():
    for compound in compounds:
      compoundName, compoundPeakList = compound
      compoundsToCompare = [c[1] for c in compounds if c[0] != compoundName]
      overlaped = calculateOverlapCount(compoundPeakList, compoundsToCompare, minDist )
      if overlaped is None:
        print(compoundName, 'No Overlapped peaks found')
      else:
        score = len(overlaped) / len(compoundPeakList)
        # print(compoundName, ' --> Counts',len(list(set(overlaped))), ' --> Overlapped positions:', overlaped, 'score: -->', score)


def getOverlappedCount(mixtureCompounds, minDist=0.01):
    totalOverlapped  = 0
    for compound in mixtureCompounds:
      compoundName, compoundPeakList = compound
      compoundsToCompare = [c[1] for c in mixtureCompounds if c[0] != compoundName]
      overlaped = calculateOverlapCount(compoundPeakList, compoundsToCompare, minDist)
      if overlaped is None:
        print(compoundName, 'No Overlapped peaks found')
        continue
      else:
        totalOverlapped += len(list(set(overlaped)))
    return totalOverlapped

def getMixtureInfo(mixture, minDist):

  for compound in mixture:
    compoundName, compoundPeakList = compound
    compoundsToCompare = [c[1] for c in mixture if c[0] != compoundName]
    overlaped = calculateOverlapCount(compoundPeakList, compoundsToCompare, minDist )

    if overlaped is None:
      print(compoundName, 'No Overlapped peaks found')
    else:
      score = len(overlaped) / len(compoundPeakList)
      print(compoundName, ' --> Counts',len(list(set(overlaped))), ' --> Overlapped positions:', overlaped, 'score: -->', score)


def calculateOverlapCount(compoundA, mixture, minimalOverlap):
  for compound in mixture:
    overlaped = [peakA for peak in compound for peakA in compoundA if abs(peak - peakA) <= minimalOverlap]
    if len(overlaped)>0:
      return overlaped


def _calculateSingleCompoundScore(compoundA, mixture, minimalOverlap):
  for mix, compounds in mixture.items():
    print(mix)
    for compound in compounds:
      overlaped = [peakA for peak in compound[1] for peakA in compoundA[1] if abs(peak - peakA) <= 0.01]
      scoring = len(overlaped) / len(compoundA[1])

def findBestMixtures(mixturesSteps):
  bestMixturesStep = list(mixturesSteps.items())
  if len(bestMixturesStep) > 0:
    bestMixtures = min(bestMixturesStep)[1]
    return bestMixtures

def mixTwoMixturesDict(mixtures):
  mixturesList = list(mixtures.items())
  sampledMixtures = random.sample(mixturesList, 2)
  mixturesToMix = dict(sampledMixtures)
  swaps = []
  for i, mixture in enumerate(list(mixturesToMix.values())):
    randInt = random.randint(0, len((mixture)[i]) - 1)
    pick = list(mixturesToMix.values())[i][randInt]
    list(mixturesToMix.values())[i].remove(pick)
    swaps.append(pick)
  for i, mixture in enumerate(list(mixturesToMix.values())):
    pick = swaps.pop()
    list(mixturesToMix.values())[i].append(pick)
  for m in sampledMixtures:
    mixturesList.remove(m)
  mixedMixtures = mixturesList + list(mixturesToMix.items())
  return dict(mixedMixtures)


def getLinearSteps(startTemp=1000.0, finalTemp = 0.1, maxSteps = 1000):
  tSteps = (startTemp - finalTemp) / maxSteps  # 1)
  temp = startTemp
  while True:
    yield temp
    temp -= tSteps

def getExponentialSteps(startTemp=1000.0, finalTemp = 0.1, maxSteps = 100):
  aTemp = math.exp((math.log(finalTemp / startTemp)) / maxSteps)
  temp = startTemp
  while True:
    yield temp
    temp *=  aTemp

def runCooling(type, startTemp=1000.0, finalTemp = 0.1, maxSteps = 1000):
  if type == 'exponential':
    coolingSchedule = getExponentialSteps(startTemp, finalTemp, maxSteps)
  elif type == 'Linear':
    coolingSchedule = getLinearSteps(startTemp, finalTemp, maxSteps)
  else:
    print('Cooling type not implemented yet, Used linear instead')
    coolingSchedule = getLinearSteps()
  return coolingSchedule

def getProbability(scoreDiff, currentTemp, tempK):
  if currentTemp == 0:
    return 0
  k = tempK
  probabilty = math.exp(-(scoreDiff)*k / ( currentTemp))
  return probabilty

# def test():
#   x = range(1000)
#   y = [getProbability( 0.5, x) for x in x]
#   # plt.plot(x,y)
#   # plt.ylim(ymax=1)
#   # plt.show()

def annealling(mixtures, coolingMethod='Linear', startTemp=1000, finalTemp=0.01,
               maxSteps=1000, tempK=200, minDistance=0.01):
  mixturesSteps = {}
  coolingSchedule = runCooling(coolingMethod, startTemp, finalTemp, maxSteps)
  currScore = calculateTotalScore(mixtures,minDistance)
  scores = []
  step = 1
  for currentTemp in coolingSchedule:
    newMixtures = mixTwoMixturesDict(mixtures)
    copyNewMixtures = copy.deepcopy(newMixtures)
    newScore = calculateTotalScore(newMixtures,minDistance)
    scoreDiff = abs(newScore - currScore)
    scores.append(newScore)
    if newScore == 0:
      return copyNewMixtures
    elif newScore <= currScore:
      mixtures = newMixtures
      currScore = newScore
      mixturesSteps.update({newScore: copyNewMixtures})
    else:
      probability = getProbability(scoreDiff,currentTemp, tempK)
      if random.random() < probability:
        mixtures = newMixtures
        currScore = newScore
        mixturesSteps.update({newScore: copyNewMixtures})
    step += 1
    if step > maxSteps:
      break

  bestMixtures = findBestMixtures(mixturesSteps)
  return  bestMixtures

def iterateAnnealing(mixtures, startTemp=1000, finalTemp=0.01, maxSteps=1000, tempK=200, coolingMethod='linear',
                     nIterations=1, minDistance=0.01):
  bestIteration = {} #score:mixture
  startingScore = calculateTotalScore(mixtures, minDistance)
  copyMixtures = copy.deepcopy(mixtures)
  if startingScore == 0:
    return mixtures
  i = 0
  while  i <= nIterations:
    newMixtures = annealling(mixtures, coolingMethod=coolingMethod, startTemp=startTemp, finalTemp=finalTemp,
                             maxSteps=maxSteps, tempK=tempK, minDistance=minDistance)
    copyNewMixtures = copy.deepcopy(newMixtures)
    if newMixtures:
      currScore = calculateTotalScore(newMixtures,minDistance)
      if currScore == 0:
        return copyNewMixtures
      if currScore <= startingScore:
        bestIteration.update({currScore: copyNewMixtures})
        startingScore = currScore
      i += 1
    if len(bestIteration)>0:
      bestMixtures = findBestMixtures(bestIteration)
      return bestMixtures
    else:
      print('No Better Iteration found, original mixtures are returned')
      sc = calculateTotalScore(copyMixtures, minDistance)
      return copyMixtures


def showScoresPerMixture(mixtures,minDistance):
  scoring = []
  for mixtureName, mixCompounds in mixtures.items():
    scoring.append(str(mixtureName)+ '  score: ' + str(scoreMixture(mixCompounds, minDistance)))
  return scoring


def greedyMixtures(compounds, maxSize, minDistance, maxPeaksOverlapped=None):
  mixtures = [[]] * len(compounds)
  for compound in compounds:
    compoundMixtured = False
    mixtureCount = 0
    while not compoundMixtured:
      if len(mixtures[mixtureCount]) < maxSize:
        mixtureScore = scoreMixture(mixtures[mixtureCount], minDistance)
        trialMixture = mixtures[mixtureCount] + [compound, ]
        if scoreMixture(trialMixture, minDistance) == mixtureScore:
          mixtures[mixtureCount] = trialMixture
          compoundMixtured = True
      mixtureCount += 1
  return [mixture for mixture in mixtures if len(mixture)>0]