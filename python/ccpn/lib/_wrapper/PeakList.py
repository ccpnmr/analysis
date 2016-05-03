"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================
from ccpncore.lib.ccp.nmr.Nmr.PeakList import pickNewPeaks, fitExistingPeakList
from ccpncore.lib.spectrum import Spectrum as spectrumLib

from ccpncore.util.CopyData import copySubTree
from typing import Sequence
import numpy
from numpy import argwhere
from scipy.ndimage import maximum_filter

def pickPeaksNd(self:'PeakList', positions:Sequence=None, dataDims:Sequence=None,
                doPos:bool=True, doNeg:bool=True,
                fitMethod:str='gaussian', excludedRegions:Sequence=None,
                excludedDiagonalDims:Sequence=None, excludedDiagonalTransform:Sequence=None):

  # ordering = [dataDim.dim-1 for dataDim in dataDims]
  # isoOrdering = [dataDim.getIsotopeCodes() for dataDim in dataDims]

  self._project.suspendNotification()

  try:

    startPoint = []
    endPoint = []

    spectrum = self.spectrum
    for ii, dataDim in enumerate(dataDims):
      # -1 below because points start at 1 in data model
      position0 = dataDim.primaryDataDimRef.valueToPoint(positions[0][ii]) - 1
      position1 = dataDim.primaryDataDimRef.valueToPoint(positions[1][ii]) - 1
      position0, position1 = min(position0, position1), max(position0, position1)
      # want integer grid points above position0 and below position1
      # add 1 to position0 because above
      # add 1 to position1 because doing start <= x < end not <= end
      # yes, this negates -1 above but they are for different reasons
      position0 = int(position0+1)
      position1 = int(position1+1)
      startPoint.append((dataDim.dim, position0))
      endPoint.append((dataDim.dim, position1))
      #startPoint.append([dataDim.dim, int(dataDim.primaryDataDimRef.valueToPoint(positions[0][ii])-1)])
      #endPoint.append([dataDim.dim, int(dataDim.primaryDataDimRef.valueToPoint(positions[1][ii])-1)])


    # for position in positions[1]:
    #   dimension = ordering[positions[1].index(position)]
    #   endPoint.append([dimension, int(spectrum.getDimPointFromValue(dimension, position))])
    #
    # for position in positions[0]:
    #   dimension = ordering[positions[0].index(position)]
    #   startPoint.append([dimension, int(spectrum.getDimPointFromValue(dimension, position))])

    startPoints = [point[1] for point in sorted(startPoint)]
    endPoints = [point[1] for point in sorted(endPoint)]
    # print(isoOrdering, startPoint, startPoints, endPoint, endPoints)

    posLevel = spectrum.positiveContourBase if doPos else None
    negLevel = spectrum.negativeContourBase if doNeg else None

    apiPeaks = pickNewPeaks(self._apiPeakList, startPoint=startPoints, endPoint=endPoints,
                   posLevel=posLevel, negLevel=negLevel, fitMethod=fitMethod, excludedRegions=excludedRegions,
                   excludedDiagonalDims=excludedDiagonalDims, excludedDiagonalTransform=excludedDiagonalTransform)

    data2ObjDict = self._project._data2Obj

  finally:
    self._project.resumeNotification()

  return [data2ObjDict[apiPeak] for apiPeak in apiPeaks]
  
# def pickPeaks1d(self:'PeakList', spectrumView, size:int=3, mode:str='wrap'):
def pickPeaks1d(self:'PeakList', data1d, dataRange, size:int=3, mode:str='wrap'):
  """
  NBNB refactored. Should not take a SpectrumView in ccpn/lib, should take 1d data array
  """

  self._project.suspendNotification()

  try:
    peaks = []
    spectrum = self.spectrum
    data1d = spectrum._apiDataSource.get1dSpectrumData()
    selectedData = data1d[:, (data1d[0] < dataRange[0]) * (data1d[0] > dataRange[1])]
    threshold = spectrum.estimateNoise()
    if (selectedData.size == 0) or (selectedData.max() < threshold):
     return peaks
    boolsVal = selectedData[1] > threshold
    maxFilter = maximum_filter(selectedData[1], size=size, mode=mode)
    boolsMax = selectedData[1] == maxFilter
    boolsPeak = boolsVal & boolsMax
    indices = argwhere(boolsPeak) # True positional indices
    for position in indices:
      peakPosition = [float(selectedData[0][position])]
      height = selectedData[1][position]
      self.newPeak(height=float(height), position=peakPosition)

  finally:
    self._project.resumeNotification()




def pickPeaks1dFiltered(self:'PeakList', size:int=9, mode:str='wrap', ignoredRegions=None, noiseThreshold=None):


  self._project.suspendNotification()

  try:
    if not ignoredRegions:
      ignoredRegions = [[-20.1,-19.1]]

    peaks = []
    spectrum = self.spectrum

    data = spectrum._apiDataSource.get1dSpectrumData()


    ppmValues = data[0]

    if noiseThreshold == 0:
      noiseThreshold = spectrum.estimateNoise()*5

    masks = []
    for region in ignoredRegions:

      mask = (ppmValues > region[0]) | (ppmValues < region[1])
      masks.append(mask)

    fullmask = [all(mask) for mask in zip(*masks)]
    newArray2 = (numpy.ma.MaskedArray(data, mask=numpy.logical_not((fullmask, fullmask))))

    if (newArray2.size == 0) or (data.max() < noiseThreshold):
     return peaks
    boolsVal = newArray2[1] > noiseThreshold
    maxFilter = maximum_filter(newArray2[1], size=size, mode=mode)


    boolsMax = newArray2[1] == maxFilter
    boolsPeak = boolsVal & boolsMax
    indices = argwhere(boolsPeak) # True positional indices
    for position in indices:
      peakPosition = [float(newArray2[0][position])]
      height = newArray2[1][position]
      self.newPeak(height=float(height), position=peakPosition)

  finally:
    self._project.resumeNotification()



def _havePeakNearPosition(values, tolerances, peaks):

  for peak in peaks:
    for i, position in enumerate(peak.position):
      if abs(position - values[i]) > tolerances[i]:
        break
    else:
      return peak

def subtractPeakLists(self:'PeakList', peakList2:'PeakList'):
  """
  Subtracts peaks in peakList2 from peaks in peakList1, based on position,
  and puts those in a new peakList3.  Assumes a common spectrum for now.
  """

  self._project.suspendNotification()

  try:

    spectrum = self.spectrum

    assert spectrum is peakList2.spectrum, 'For now requires both peak lists to be in same spectrum'

    # dataDims = spectrum.sortedDataDims()
    tolerances = self.spectrum.assignmentTolerances

    peaks2 = peakList2.peaks
    peakList3 = spectrum.newPeakList()

    for peak1 in self.peaks:
      values1 = [peak1.position[dim] for dim in range(len(peak1.position))]
      if not _havePeakNearPosition(values1, tolerances, peaks2):
        peakList3.newPeak(height=peak1.height, volume=peak1.volume, figureOfMerit=peak1.figureOfMerit,
                         annotation=peak1.annotation, position=peak1.position, pointPosition=peak1.pointPosition)


  finally:
    self._project.resumeNotification()

def copyPeaks(self:'PeakList', sinkSpectrum:'Spectrum', fitPositions:bool=False):
  refAxisCodes = self.spectrum.axisCodes
  sinkAxisCodes = sinkSpectrum.axisCodes

  if not spectrumLib.doAxisCodesMatch(sinkAxisCodes, refAxisCodes):
    print('axis codes of the source and sink peaklists do not match')
    return

  if not fitPositions:
    copySubTree(self, sinkSpectrum)

  # else:

def refit(self:'PeakList', method:str='gaussian'):
  fitExistingPeakList(self._apiPeakList, method)
