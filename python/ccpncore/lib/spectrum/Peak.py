"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2015-11-13 13:57:05 +0000 (Fri, 13 Nov 2015) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: skinnersp $"
__date__ = "$Date: 2015-11-13 13:57:05 +0000 (Fri, 13 Nov 2015) $"
__version__ = "$Revision: 8845 $"

#=========================================================================================
# Start of code
#=========================================================================================

import numpy

from ccpncore.api.ccp.nmr.Nmr import Peak as ApiPeak

from ccpncore.util.Types import Sequence

def fitExistingPeaks(peaks:Sequence[ApiPeak], fitMethod:str=None):

  if not fitMethod:
    return
 
  assert fitMethod in ('gaussian', 'lorentzian'), 'fitMethod = %s, must be one of ("gaussian", "lorentzian")' % fitMethod
  method = 0 if fitMethod == 'gaussian' else 1

  from ccpnc.peak import Peak as CPeak

  for peak in peaks:
    dataSource = peak.peakList.dataSource
    numDim = dataSource.numDim
    dataDims = dataSource.sortedDataDims()

    peakDims = peak.sortedPeakDims()
    position = [peakDim.position - 1 for peakDim in peakDims] # API position starts at 1
    numPoints = [peakDim.dataDim.numPoints for peakDim in peakDims]
    position = numpy.round(numpy.array(position))
    numPoints = numpy.array(numPoints)

    firstArray = numpy.maximum(position-2, 0)
    lastArray = numpy.minimum(position+3, numPoints)
    dataArray, intRegion = dataSource.getRegionData(firstArray, lastArray)
    firstArray = firstArray.astype('int32')
    lastArray = lastArray.astype('int32')
    peakArray = (position-firstArray).reshape((1, numDim))
    peakArray = peakArray.astype('float32')
    regionArray = numpy.array((firstArray-firstArray, lastArray-firstArray))
    try:
      result = CPeak.fitPeaks(dataArray, regionArray, peakArray, method)
      height, center, linewidth = result[0]
    except CPeak.error as e:
      return
      # possibly should log error??

    position = firstArray + center

    for i, peakDim in enumerate(peakDims):
      peakDim.position = position[i] + 1 # API position starts at 1
      peakDim.lineWidth = linewidth[i]

    peak.height = height
