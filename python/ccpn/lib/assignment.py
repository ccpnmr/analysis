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


def isInterOnlyExpt(string):
  expList = ['HNCO', 'CONH', 'CONN', 'H[N[CO', 'seq.', 'HCA_NCO.Jmultibond']
  if(any(expType in string.upper() for expType in expList)):
    return True

def getExptDict(project):
  exptDict = {}
  for peakList in project.peakLists[1:]:
    exptDict[peakList.spectrum.experimentType] = []
  return exptDict

def assignAlphas(nmrResidue, peaks, shiftList):

  if len(peaks) > 1:
    a3 = nmrResidue.fetchNmrAtom(name='CA-1')
    a4 = nmrResidue.fetchNmrAtom(name='CA')
    if peaks[0].height > peaks[1].height:
      peaks[0].assignDimension(axisCode='C', value=[a4])
      peaks[1].assignDimension(axisCode='C', value=[a3])
      try:
        shiftList.newChemicalShift(value = peaks[0].position[1], nmrAtom=a4)
        shiftList.newChemicalShift(value = peaks[1].position[1], nmrAtom=a3)
      except:
        pass
    if peaks[0].height < peaks[1].height:
      peaks[0].assignDimension(axisCode='C', value=[a3])
      peaks[1].assignDimension(axisCode='C', value=[a4])
      try:
        shiftList.newChemicalShift(value = peaks[0].position[1], nmrAtom=a4)
        shiftList.newChemicalShift(value = peaks[1].position[1], nmrAtom=a3)
      except:
        pass
  elif len(peaks) == 1:
    peaks[0].assignDimension(axisCode='C', value=[nmrResidue.fetchNmrAtom(name='CA')])
    try:
      shiftList.newChemicalShift(value = peaks[0].position[1], nmrAtom=nmrResidue.fetchNmrAtom(name='CA'))
    except:
      pass

def assignBetas(nmrResidue, peaks, shiftList):

  if len(peaks) > 1:
    a3 = nmrResidue.fetchNmrAtom(name='CB-1')
    a4 = nmrResidue.fetchNmrAtom(name='CB')
    if abs(peaks[0].height) > abs(peaks[1].height):
      peaks[0].assignDimension(axisCode='C', value=[a4])
      peaks[1].assignDimension(axisCode='C', value=[a3])
      try:
        shiftList.newChemicalShift(value = peaks[0].position[1], nmrAtom=a4)
        shiftList.newChemicalShift(value = peaks[1].position[1], nmrAtom=a3)
      except:
        pass
    if abs(peaks[0].height) < abs(peaks[1].height):
      peaks[0].assignDimension(axisCode='C', value=[a3])
      peaks[1].assignDimension(axisCode='C', value=[a4])
      try:
        shiftList.newChemicalShift(value = peaks[0].position[1], nmrAtom=a4)
        shiftList.newChemicalShift(value = peaks[1].position[1], nmrAtom=a3)
      except:
        pass
  elif len(peaks) == 1:
    peaks[0].assignDimension(axisCode='C', value=[nmrResidue.fetchNmrAtom(name='CB')])
    try:
      shiftList.newChemicalShift(value = peaks[0].position[1], nmrAtom=nmrResidue.fetchNmrAtom(name='CB'))
    except:
      pass