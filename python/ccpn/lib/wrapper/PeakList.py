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

import collections

from numpy import argwhere
from scipy.ndimage import maximum_filter

Sequence = collections.abc.Sequence

def findPeaksNd(peakList:object, positions:Sequence=None, dataDims:Sequence=None):


  print(positions, dataDims)

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

  posLevel = spectrum.positiveContourBase*100
  negLevel = spectrum.negativeContourBase*100

  print(posLevel)

  return pickNewPeaks(peakList.apiPeakList, startPoint=startPoints, endPoint=endPoints, posLevel=posLevel, negLevel=negLevel)

def findPeaks1d(peakList, spectrumView, size=3, mode='wrap'):


   peaks = []
   spectrum = peakList.spectrum
   ignoredRegions = [4.25, 5.4]
   data = spectrumView.data
   ppmValues = data[0]
   intensities = data[1]
   import numpy
   array1 = numpy.where(ignoredRegions[0] > ppmValues)
   array2 = numpy.where(ppmValues > ignoredRegions[1])# or ppmValues > ignoredRegions[1])[0])
   print(array1, array2)
   # print(array1[0], array1[-1], array2[0], array2[-1])
   # print(len(data[0]))
   # array4 = numpy.array(data[0][array1[0]:array1[1], data[1][array1[0]:array1[1]]])
   # array3 = data[array2[0]:array2[1]+1, array2[0]:array2[-1]+1]
   # print(len(data[0]))
   # # array4 = data[17094:32766, 17094:32766]
   # print('4',array4)
   # print('3',array3)
   #
   #
   # # for datum in ppmValues:
   # #   if datum < ignoredRegions[0] or datum > ignoredRegions[1]:
   # #     print(ppmValues.index(datum), datum)
   # threshold = spectrum.estimateNoise()*10
   # if (data.size == 0) or (data.max() < threshold):
   #  return peaks
   # boolsVal = array3[1] > threshold
   # maxFilter = maximum_filter(array3[1], size=size, mode=mode)
   # boolsMax = array3[1] == maxFilter
   # boolsPeak = boolsVal & boolsMax
   # indices = argwhere(boolsPeak) # True positional indices
   # for position in indices:
   #   peakPosition = [float(array3[0][position])]
   #   height = array3[1][position]
   #   peakList.newPeak(height=float(height), position=peakPosition)
   #
   #
   # boolsVal = array4[1] > threshold
   # maxFilter = maximum_filter(array4[1], size=size, mode=mode)
   # boolsMax = array4[1] == maxFilter
   # boolsPeak = boolsVal & boolsMax
   # indices = argwhere(boolsPeak) # True positional indices
   # for position in indices:
   #   peakPosition = [float(array4[0][position])]
   #   height = array4[1][position]
   #   peakList.newPeak(height=float(height), position=peakPosition)
   # # print(self.peakListItems[peakList.pid])#.createPeakItems()

def findPeaks1dFiltered(peakList, spectrumView, size=3, mode='wrap'):


   peaks = []
   spectrum = peakList.spectrum
   ignoredRegions = [4.25, 5.4]
   data = spectrumView.data
   ppmValues = data[0]
   intensities = data[1]
   import numpy
   array1 = numpy.where(ppmValues < ignoredRegions[0])[0]# or ppmValues > ignoredRegions[1])[0])
   array2 = numpy.where(ppmValues > ignoredRegions[1])[0]
   print(array1[0], array1[-1], array2[0], array2[-1])
   # array4 = data[array1[0]:array1[-1]+1, array1[0]:array1[-1]+1]
   array3 = data[array2[0]:array2[-1]+1, array2[0]:array2[-1]+1]

   array4 = data[0:17465, 0:17465]
   # for datum in ppmValues:
   #   if datum < ignoredRegions[0] or datum > ignoredRegions[1]:
   #     print(ppmValues.index(datum), datum)
   threshold = spectrum.estimateNoise()*10
   # if (data.size == 0) or (data.max() < threshold):
   #  return peaks
   boolsVal = array3[1] > threshold
   maxFilter = maximum_filter(array3[1], size=size, mode=mode)

   boolsMax = array3[1] == maxFilter

   boolsPeak = boolsVal & boolsMax
   indices = argwhere(boolsPeak) # True positional indices
   for position in indices:
     peakPosition = [float(array3[0][position])]
     height = array3[1][position]
     peakList.newPeak(height=float(height), position=peakPosition)
   boolsVal = array4[1] > threshold
   maxFilter = maximum_filter(array4[1], size=size, mode=mode)

   boolsMax = array4[1] == maxFilter

   boolsPeak = boolsVal & boolsMax
   indices = argwhere(boolsPeak) # True positional indices
   for position in indices:
     peakPosition = [float(array4[0][position])]
     height = array4[1][position]
     peakList.newPeak(height=float(height), position=peakPosition)
   # print(self.peakListItems[peakList.pid])#.createPeakItems()

   # return peakList
