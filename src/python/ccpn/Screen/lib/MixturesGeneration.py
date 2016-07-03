

from numpy import array, amin, amax, average, empty, nan, nanmin, fabs, subtract, where, argmax, NAN
import math
from collections import defaultdict
from itertools import chain, combinations
from collections import OrderedDict
from ccpn.Screen.lib.SimulatedAnnealing import randomDictMixtures, iterateAnnealing, getOverlappedCount , scoreMixture, calculateOverlapCount


def _initialiseMixtures(params):

  calculationMethod = _getCalculationMethod(params)
  simulatedAnnealingParm = _getSimulatedAnnealingParm(params)
  mode = _getMode(params)
  modeNumber = _getNumber(params)
  minimalDistance= _getMinimalDistance(params)
  spectra = _getSpectra(params)
  replaceMixtures = _getReplace(params)
  peaksAreTopick = _getPeakPicking(params)
  noiseLevel = _getNoiseLevel(params)
  pickFilter = _getFilter(params)
  pickFilterMode = _getFilterMode(params)
  ignoredRegions = _getIgnoredRegions(params)
  project = _getProjectFromSpectrum(spectra[0])
  currentVirtualSamples = _getCurrentVirtualSamples(project)
  if peaksAreTopick:
    _pickPeaks(spectra, pickFilter, pickFilterMode, ignoredRegions, noiseLevel)

  if replaceMixtures:
    _deleteMixtures(currentVirtualSamples)
    _generateMixtures(project,spectra, calculationMethod, simulatedAnnealingParm, mode, modeNumber, minimalDistance,)
  else:
    _generateMixtures(project,spectra, calculationMethod, simulatedAnnealingParm, mode, modeNumber, minimalDistance)


def _getCalculationMethod(params):
  return params['calculationMethod']

def _getSimulatedAnnealingParm(params):
  return params['simulatedAnnealingParm']

def _getNoiseThreshold(params):
  return params['threshold']

def _getMode(params):
  return params['mode']

def _getNumber(params):
  return params['number']

def _getMinimalDistance(params):
  return params['minimalDistance']

def _getSpectra(params):
  return params['spectra']

def _getReplace(params):
  value = params['replace']
  if value == 'Yes':
    return True

def _getPeakPicking(params):
  value = params['peakPicking']
  if value == 'Automatic':
    return True

def _getNoiseLevel(params):
  value = params['noiseLevel']
  if value == 'Estimated':
    return 0
  else:
    noiseLevel = _getNoiseThreshold(params)
    return noiseLevel

def _getFilter(params):
  return params['filter']

def _getFilterMode(params):
  return params['filterMode']

def _getIgnoredRegions(params):
  return params['ignoredRegions']

def _getProjectFromSpectrum(spectrum):
  return spectrum.project

def _deleteMixtures(currentMixtures):
  for mixture in currentMixtures:
    mixture.delete()

def getCompounds(spectra):
  compounds = []
  peakLists = [s.peakLists[0] for s in spectra]
  for peakList in peakLists:
    name, space, value = str(peakList.id).partition('-')
    compound = [name, [peak.position[0] for peak in peakList.peaks]]
    compounds.append(compound)
  return compounds

def _generateMixtures(project, spectra, method, methodParam, mode, n, minDistance):
  compounds = getCompounds(spectra)
  startTemp, finalTemp, maxSteps, k, coolingMethod, nIterations = list(methodParam.values())

  mixturesNumber = _getMixturesNumber(len(spectra), mode, n)
  randomMixtures = randomDictMixtures('Mixture',compounds, mixturesNumber)
  if method == 'Simulated Annealing':
    mixtures = iterateAnnealing(randomMixtures, startTemp, finalTemp, maxSteps, k, coolingMethod, nIterations, minDistance)
    _createSamples(project, mixtures, minDistance)

def _getMixturesNumber(lenght, mode, n):
  if mode == 'Select number of Mixtures':
    return n
  else:
    return  math.floor(lenght/n)


def _createSamples(project, mixtures, minDistance):
  for mixtureName, mixtureCompounds in mixtures.items():
    compoundNames = [compound[0] for compound in mixtureCompounds]
    sample = project.newSample(name=str(mixtureName))
    sample.isVirtual = True
    # for compoundName in compoundNames:
    #   newSampleComponent = sample.newSampleComponent(name=(str(compoundName)+'-1'), labeling='H')

    _setMixtureScores(mixtureCompounds, sample)
    _setSampleComponentScores(project, sample, mixtureCompounds, minDistance)

def _setMixtureScores(mixtureCompounds, sample, minimalOverlap=0.01):
    sample.score = round(scoreMixture(mixtureCompounds, minimalOverlap), 2)
    sample.overlaps = getOverlappedCount(mixtureCompounds)

def _getMixtureFromSample(sample):
  mixtureName = str(sample.name)
  spectra = []
  for sampleComponent in sample.sampleComponents:
    spectrum = sampleComponent.substance.referenceSpectra[0]
    spectra.append(spectrum)
  return {mixtureName:getCompounds(spectra)}

def _getMixturesFromVirtualSamples(virtualSamples):
  mixtures = {}
  for sample in virtualSamples:
    mixture = _getMixtureFromSample(sample)
    mixtures.update(mixture)

  return mixtures

def _getCurrentVirtualSamples(project):
  ''' gets all virtual samples from project and converts them to dictionary mixtures'''
  currentVirtualSamples = []
  for sample in project.samples:
    if sample.isVirtual:
      virtualSample = sample
      currentVirtualSamples.append(virtualSample)
  return currentVirtualSamples

def _pickPeaks(spectra, filter, filterMode, ignoredRegions, noiseThreshold):
  for spectrum in spectra:
    spectrum.peakLists[0].pickPeaks1dFiltered(size=filter, mode=filterMode, ignoredRegions=ignoredRegions,
                                              noiseThreshold=noiseThreshold)


def _setSampleComponentScores(project,sample, mixtureCompounds, minDist):

  for compound in mixtureCompounds:
    compoundName, compoundPeakList = compound
    newSampleComponent = sample.newSampleComponent(name=(str(compoundName) + '-1'), labeling='H')
    compoundsToCompare = [c[1] for c in mixtureCompounds if c[0] != compoundName]
    overlaped = calculateOverlapCount(compoundPeakList, compoundsToCompare, minDist)

    if overlaped is None:
      print(compoundName, 'No Overlapped peaks found')
      newSampleComponent.score = 0

    else:
      score = len(overlaped) / len(compoundPeakList)

      # print(compoundName, ' --> Counts', len(list(set(overlaped))), ' --> Overlapped positions:', overlaped,
      #       'score: -->',round(score,2))
      newSampleComponent.score = round(score,2)
      newSampleComponent.overlaps = list(set(overlaped))

