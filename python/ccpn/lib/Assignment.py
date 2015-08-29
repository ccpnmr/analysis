"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================

CCP_CODES =  ['Ala','Cys','Asp','Glu','Phe','Gly','His','Ile','Lys','Leu','Met','Asn',
              'Pro','Gln','Arg','Ser','Thr','Val','Trp','Tyr']

ATOM_NAMES = ['C', 'CA', 'CB', 'CD', 'CD*', 'CD1', 'CD2', 'CE', 'CE*', 'CE1', 'CE2', 'CE3', 'CG',
              'CG1', 'CG2', 'CH2', 'CZ', 'CZ2', 'CZ3', 'H', 'HA', 'HA2', 'HA3', 'HB', 'HB*', 'HB2',
              'HB3', 'HD*', 'HD1', 'HD1*', 'HD2', 'HD2*', 'HD3', 'HE', 'HE*', 'HE1', 'HE2', 'HE21',
              'HE22', 'HE3', 'HG', 'HG1', 'HG1*', 'HG12', 'HG13', 'HG2', 'HG2*', 'HG3', 'HH', 'HH11',
              'HH12', 'HH2', 'HH21', 'HH22', 'HZ', 'HZ*', 'HZ2', 'HZ3', 'N', 'ND1', 'NE', 'NE1',
              'NE2', 'NH1', 'NH2', 'NZ']

from ccpncore.lib.assignment.ChemicalShift import getSpinSystemResidueProbability, getAtomProbability, getResidueAtoms

from sklearn import svm
from sklearn.tree import DecisionTreeClassifier

def isInterOnlyExpt(string):
  expList = ['HNCO', 'CONH', 'CONN', 'H[N[CO', 'seq.', 'HCA_NCO.Jmultibond']
  if(any(expType in string.upper() for expType in expList)):
    return True

def getExptDict(project):
  exptDict = {}
  for peakList in project.peakLists[1:]:
    exptDict[peakList.spectrum.experimentType] = []
  return exptDict

def assignAlphas(nmrResidue, peaks):

  if len(peaks) > 1:
    chain = nmrResidue.nmrChain
    newNmrResidue = chain.fetchNmrResidue(nmrResidue.sequenceCode+'-1')
    a3 = newNmrResidue.fetchNmrAtom(name='CA')
    a4 = nmrResidue.fetchNmrAtom(name='CA')
    if peaks[0].height > peaks[1].height:
      peaks[0].assignDimension(axisCode='C', value=[a4])
      peaks[1].assignDimension(axisCode='C', value=[a3])
    if peaks[0].height < peaks[1].height:
      peaks[0].assignDimension(axisCode='C', value=[a3])
      peaks[1].assignDimension(axisCode='C', value=[a4])
  elif len(peaks) == 1:
    peaks[0].assignDimension(axisCode='C', value=[nmrResidue.fetchNmrAtom(name='CA')])


def assignBetas(nmrResidue, peaks):

  if len(peaks) > 1:
    chain = nmrResidue.nmrChain
    newNmrResidue = chain.fetchNmrResidue(nmrResidue.sequenceCode+'-1')
    a3 = newNmrResidue.fetchNmrAtom(name='CB')
    a4 = nmrResidue.fetchNmrAtom(name='CB')
    if abs(peaks[0].height) > abs(peaks[1].height):
      peaks[0].assignDimension(axisCode='C', value=[a4])
      peaks[1].assignDimension(axisCode='C', value=[a3])

    if abs(peaks[0].height) < abs(peaks[1].height):
      peaks[0].assignDimension(axisCode='C', value=[a3])
      peaks[1].assignDimension(axisCode='C', value=[a4])

  elif len(peaks) == 1:
    peaks[0].assignDimension(axisCode='C', value=[nmrResidue.fetchNmrAtom(name='CB')])

def getNmrResiduePrediction(nmrResidue, chemicalShiftList):
  """
  Takes ccpnCode and chemicalShift and predicts atom type
  :param nmrResidue:
  :param chemicalShiftList:
  :return: dictionary of assignments {(ccpCode, atomName): prediction probability }
  """

  predictions = {}
  spinSystem = nmrResidue._wrappedData
  for code in CCP_CODES:
    predictions[code] = float(getSpinSystemResidueProbability(spinSystem, chemicalShiftList, code))
  tot = sum(predictions.values())
  refinedPredictions = {}
  for code in CCP_CODES:
    v = round(predictions[code]/tot * 100, 2)
    if v > 0:
      refinedPredictions[code] = v

  finalPredictions = []

  for value in sorted(refinedPredictions.values(), reverse=True)[:5]:
    key = [key for key, val in refinedPredictions.items() if val==value][0]
    finalPredictions.append([key, str(value)+' %'])

  return finalPredictions

def getNmrAtomPrediction(ccpCode, value):
  """
  Takes ccpnCode and chemicalShift and predicts atom type
  :param ccpCode:
  :param value:
  :return: dictionary of assignments {(ccpCode, atomName): prediction probability }
  """
  predictions = {}
  atomNames = getResidueAtoms(ccpCode)
  for atomName in atomNames:
    predictions[ccpCode, atomName] = getAtomProbability(ccpCode, atomName, value)

  tot = sum(predictions.values())
  refinedPredictions = {}
  for key, value in predictions.items():
    v = round(value/tot * 100, 2)
    if v > 0:
      refinedPredictions[key] = v
  #
  finalPredictions = []
  #
  for value in sorted(refinedPredictions.values(), reverse=True)[:5]:
    key = [key for key, val in refinedPredictions.items() if val==value][0]
    finalPredictions.append([key, str(value)+' %'])

  return finalPredictions

def getIsotopeCodeOfAxis(axisCode):
  """

  Takes an axisCode and returns the appropriate isotope code
  Inputs:
  :param axisCode
  :returns isotopeCode
  """
  if axisCode[0] == 'C':
    return '13C'
  if axisCode[0] == 'N':
    return '15N'
  if axisCode[0] == 'H':
    return '1H'

def copyAssignments(referencePeakList, matchPeakList):
  """

  Takes a reference peakList, creates an SVM for it and uses the SVM to assign nmrAtoms to dimensions
  of a match peakList based on matching axis codes
  Inputs
  :param referencePeakList:
  :param matchPeakList:

  """
  import numpy
  project = referencePeakList.project
  refAxisCodes = referencePeakList.spectrum.axisCodes
  refPositions = [numpy.array(peak.position) for peak in referencePeakList.peaks]
  refLabels = [peak.pid for peak in referencePeakList.peaks]
  # print('refAxisCodes', refAxisCodes)
  clf = svm.SVC(class_weight='auto', kernel='poly')
  clf.fit(refPositions, refLabels)

  matchAxisCodes = matchPeakList.spectrum.axisCodes


  mappingArray = [matchAxisCodes.index(i) for i in refAxisCodes if i in refAxisCodes]

  for peak in matchPeakList.peaks:
    matchArray = []
    for dim in mappingArray:
      matchArray.append(peak.position[dim])

    result = ''.join((clf.predict(numpy.array(matchArray))))
    print(clf.predict(numpy.array(matchArray)), matchArray, peak.position)
    # for value in checkArray:
    #   print(abs(value), peak.peakList.spectrum.assignmentTolerances)

    dimNmrAtoms = project.getById(result).dimensionNmrAtoms
    for axisCode in refAxisCodes:
      # print(axisCode)
      peak.assignDimension(axisCode=axisCode, value=dimNmrAtoms[refAxisCodes.index(axisCode)])

def propagateAssignments(peaks, referencePeak=None, tolerances=None):

  if referencePeak:
    peaksIn = [referencePeak, ]
  else:
    peaksIn = peaks

  if not tolerances:
    tolerances = []

  dimNmrAtoms = {}

  for peak in peaksIn:
    for i, dimensionNmrAtom in enumerate(peak.dimensionNmrAtoms):

      key = peak.peakList.spectrum.axisCodes[i]
      if dimNmrAtoms.get(key) is None:
        dimNmrAtoms[key] = []

      if len(peak.dimensionNmrAtoms[i]) > 0:
        for dimensionNmrAtoms in peak.dimensionNmrAtoms[i]:
          nmrAtom = dimensionNmrAtoms

          dimNmrAtoms[key].append(nmrAtom)

  print('dimNmrAtoms', dimNmrAtoms)

  shiftRanges = {}

  for peak in peaksIn:
    for i, axisCode in enumerate(peak.peakList.spectrum.axisCodes):

      if axisCode not in shiftRanges:
        shiftMin, shiftMax = peak.peakList.spectrum.spectrumLimits[i]
        shiftRanges[axisCode] = (shiftMin, shiftMax)

      else:
          shiftMin, shiftMax = shiftRanges[axisCode]

      if i < len(tolerances):
        tolerance = tolerances[i]
      else:
        tolerance = peak.peakList.spectrum.assignmentTolerances[i]

      pValue = peak.position[i]

      extantNmrAtoms = []

      for dimensionNmrAtom in peak.dimensionNmrAtoms:
        extantNmrAtoms.append(dimensionNmrAtom)

      assignNmrAtoms = []
      closeNmrAtoms = []

      for nmrAtom in dimNmrAtoms[axisCode]:
        if nmrAtom not in extantNmrAtoms:
          shiftList = peak.peakList.spectrum.chemicalShiftList
          shift = shiftList.findChemicalShift(nmrAtom)

          if shift:

            sValue = shift.value

            if not (shiftMin < sValue < shiftMax):
              continue

            assignNmrAtoms.append(nmrAtom)

            if abs(sValue-pValue) <= tolerance:
              closeNmrAtoms.append(nmrAtom)

      # print(closeNmrAtoms)
      if closeNmrAtoms:
        for nmrAtom in closeNmrAtoms:
          print(axisCode, nmrAtom)
          peak.assignDimension(axisCode, nmrAtom)

      elif not extantNmrAtoms:
        for nmrAtom in assignNmrAtoms:
          print(axisCode, nmrAtom)
          peak.assignDimension(axisCode, nmrAtom)




def getAxisCodeForPeakDimension(peak, dim):
    return peak.peakList.spectrum.axisCodes[dim]

def assignPeakDimension(peak, dim, nmrAtom):
    axisCode = getAxisCodeForPeakDimension(peak, dim)
    peak.assignDimension(axisCode=axisCode, value=[nmrAtom])
    shiftList = peak.peakList.spectrum.chemicalShiftList
    shiftList.newChemicalShift(value=peak.position[dim], nmrAtom=nmrAtom)





