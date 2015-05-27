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
from ccpncore.lib.ccp.nmr.Nmr.PeakList import pickNewPeaks

from ccpnmrcore.modules.GuiSpectrumView1d import GuiSpectrumView1d

import collections

from numpy import argwhere
from scipy.ndimage import maximum_filter

Sequence = collections.abc.Sequence

def findPeaksNd(peakList:object, positions:Sequence=None, dataDims:Sequence=None, doPos:bool=True, doNeg:bool=True):

  ordering = [dataDim.dim-1 for dataDim in dataDims]
  isoOrdering = [dataDim.getIsotopeCodes() for dataDim in dataDims]

  startPoint = []
  endPoint = []

  spectrum = peakList.spectrum

  for position in positions[1]:
    dimension = ordering[positions[1].index(position)]
    endPoint.append([dimension, int(spectrum.getDimPointFromValue(dimension, position))])

  for position in positions[0]:
    dimension = ordering[positions[0].index(position)]
    startPoint.append([dimension, int(spectrum.getDimPointFromValue(dimension, position))])

  startPoints = [point[1] for point in sorted(startPoint)]
  endPoints = [point[1] for point in sorted(endPoint)]
  print(isoOrdering, startPoint, startPoints, endPoint, endPoints)

  posLevel = spectrum.positiveContourBase*100 if doPos else None
  negLevel = spectrum.negativeContourBase*100 if doNeg else None

  apiPeaks = pickNewPeaks(peakList.apiPeakList, startPoint=startPoints, endPoint=endPoints, posLevel=posLevel, negLevel=negLevel)

  data2ObjDict = peakList._project._data2Obj
  
  return [data2ObjDict[apiPeak] for apiPeak in apiPeaks]
  
def findPeaks1d(peakList, spectrumView, size=3, mode='wrap'):

   peaks = []
   spectrum = peakList.spectrum
   data = spectrumView.data
   threshold = spectrum.estimateNoise()*10
   if (data.size == 0) or (data.max() < threshold):
    return peaks
   boolsVal = data[1] > threshold
   maxFilter = maximum_filter(data[1], size=size, mode=mode)
   boolsMax = data[1] == maxFilter
   boolsPeak = boolsVal & boolsMax
   indices = argwhere(boolsPeak) # True positional indices
   for position in indices:
     peakPosition = [float(data[0][position])]
     height = data[1][position]
     # peakList.newPeak(height=float(height), position=peakPosition)





def findPeaks1dFiltered(peakList, size=9, mode='wrap'):


   peaks = []
   spectrum = peakList.spectrum
   ignoredRegions = [5.4, 4.25]
   data = GuiSpectrumView1d.getSliceData(spectrum)
   ppmValues = data[0]
   import numpy
   mask = (ppmValues > ignoredRegions[0]) | (ppmValues < ignoredRegions[1])

   newArray2 = (numpy.ma.MaskedArray(data, mask=numpy.logical_not((mask, mask))))
   threshold = spectrum.estimateNoise()
   if (newArray2.size == 0) or (data.max() < threshold):
    return peaks
   boolsVal = newArray2[1] > threshold
   maxFilter = maximum_filter(newArray2[1], size=size, mode=mode)
   boolsMax = newArray2[1] == maxFilter
   boolsPeak = boolsVal & boolsMax
   indices = argwhere(boolsPeak) # True positional indices
   for position in indices:
     peakPosition = [float(newArray2[0][position])]
     height = newArray2[1][position]
     print(peakPosition, height)
     peakList.newPeak(height=float(height), position=peakPosition)


   # # print(self.peakListItems[peakList.pid])#.createPeakItems()
