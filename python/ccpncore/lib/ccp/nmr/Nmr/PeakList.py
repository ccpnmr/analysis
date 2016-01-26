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

import numpy

from ccpncore.api.ccp.nmr.Nmr import PeakList

from ccpncore.util.Types import Sequence

def pickNewPeaks(self:PeakList, startPoint:Sequence[int], endPoint:Sequence[int],
                 posLevel:float=None, negLevel:float=None,
                 minLinewidth=None, exclusionBuffer=None,
                 minDropfactor:float=0.0, checkAllAdjacent:bool=True,
                 fitMethod:str=None, excludedRegions=None,
                 excludedDiagonalDims=None, excludedDiagonalTransform=None):

  # startPoint and endPoint are 0-based not 1-based
  
  # TBD: ignores aliasing for now
  
  from ccpnc.peak import Peak as CPeak

  if fitMethod:
    assert fitMethod in ('gaussian', 'lorentzian'), 'fitMethod = %s, must be one of ("gaussian", "lorentzian")' % fitMethod
    method = 0 if fitMethod == 'gaussian' else 1
    
  peaks = []

  if posLevel is None and negLevel is None:
    return peaks

  dataSource = self.dataSource
  numDim = dataSource.numDim

  if not minLinewidth:
    minLinewidth = [0.0] * numDim

  if not exclusionBuffer:
    exclusionBuffer =  [1] * numDim

  nonAdj = 1 if checkAllAdjacent else 0
  
  if not excludedRegions:
    excludedRegions = []
    
  if not excludedDiagonalDims:
    excludedDiagonalDims = []

  if not excludedDiagonalTransform:
    excludedDiagonalTransform = []

  startPoint = numpy.array(startPoint)
  endPoint = numpy.array(endPoint)
  
  startPoint, endPoint = numpy.minimum(startPoint, endPoint), numpy.maximum(startPoint, endPoint)
  
  # extend region by exclusionBuffer
  bufferArray = numpy.array(exclusionBuffer)
  startPointBuffer = startPoint - bufferArray
  endPointBuffer = endPoint + bufferArray

  dataArray, intRegion = dataSource.getRegionData(startPointBuffer, endPointBuffer)
  startPointInt, endPointInt = intRegion
  startPointInt = numpy.array(startPointInt)
  endPointInt = numpy.array(endPointInt)
  numPointInt = endPointInt - startPointInt
  startPointBuffer = numpy.maximum(startPointBuffer, startPointInt)
  endPointBuffer = numpy.minimum(endPointBuffer, endPointInt)
  if numpy.any(numPointInt <= 0): # return if any of the dimensions has <= 0 points
    return peaks
  
  #startPointBuffer = numpy.array(startPointBuffer, dtype='float32')
  excludedRegionsList = [numpy.array(excludedRegion, dtype='float32')-startPointBuffer for excludedRegion in excludedRegions]
  
  excludedDiagonalDimsList = []
  excludedDiagonalTransformList = []
  for n in range(len(excludedDiagonalDims)):
    dim1, dim2 = excludedDiagonalDims[n]
    a1, a2, b12, d = excludedDiagonalTransform[n]
    b12 += a1*startPointBuffer[dim1] - a2*startPointBuffer[dim2]
    excludedDiagonalDimsList.append(numpy.array((dim1, dim2), dtype='int32'))
    excludedDiagonalTransformList.append(numpy.array((a1, a2, b12, d), dtype='float32'))
  
  """
  existingPeaks = getRegionPeaks(peakList, startPointInt, endPointInt)
  existingPoints = set()
  for peak in existingPeaks:
    keys = [[],]

    for i, point in enumerate(peak.getPoints()):
      p1 = int(point)
      p2 = p1+1

      for key in keys[:]:
        keys.append(key + [p2],)
        key.append(p1)

    existingPoints.update([tuple(k) for k in keys])
  """
  doPos = posLevel is not None
  doNeg = negLevel is not None
  posLevel = posLevel or 0.0
  negLevel = negLevel or 0.0
    
  peakPoints = CPeak.findPeaks(dataArray, doNeg, doPos,
                               negLevel, posLevel, exclusionBuffer,
                               nonAdj, minDropfactor, minLinewidth,
                               excludedRegionsList, excludedDiagonalDimsList, excludedDiagonalTransformList)

  peakPoints = [(numpy.array(position), height) for position, height in peakPoints]
  
  # only keep those points which are inside original region, not extended region
  peakPoints = [(position, height) for position, height in peakPoints if ((startPoint-startPointInt) <= position).all() and (position <= (endPoint-startPointInt)).all()]

  # check new found positions against existing ones
  existingPositions = []
  for peak in self.peaks:
    position = numpy.array([peakDim.position for peakDim in peak.sortedPeakDims()])  # ignores aliasing
    existingPositions.append(position-1) # -1 because API position starts at 1
    
  exclusionBuffer = numpy.array(exclusionBuffer)
               
  peaks = []
  for position, height in peakPoints:
    
    position += startPointBuffer
    
    for existingPosition in existingPositions:
      delta = abs(existingPosition - position)
      if (delta < exclusionBuffer).all():
        break     
    else:      
      if fitMethod:
        position -= startPointBuffer
        numDim = len(position)
        firstArray = numpy.maximum(position - 2, 0)
        lastArray = numpy.minimum(position + 3, numPointInt)
        peakArray = position.reshape((1, numDim))
        peakArray = peakArray.astype('float32')
        firstArray = firstArray.astype('int32')
        lastArray = lastArray.astype('int32')
        regionArray = numpy.array((firstArray, lastArray))

        try:
          result = CPeak.fitPeaks(dataArray, regionArray, peakArray, method)
          height, center, linewidth = result[0]
        except Peak.error as e:
          # possibly should log error??
          dimCount = len(startPoint)
          height = float(dataArray[tuple(position[::-1])])
            # have to reverse position because dataArray backwards
            # have to float because API does not like numpy.float32
          center = position
          linewidth = dimCount * [None]
        position = center + startPointBuffer
      
      peak = self.newPeak()

      dataDims = dataSource.sortedDataDims()
      peakDims = peak.sortedPeakDims()

      for i, peakDim in enumerate(peakDims):
        dataDim = dataDims[i]

        if dataDim.className == 'FreqDataDim':
          dataDimRef = dataDim.primaryDataDimRef
        else:
          dataDimRef = None

        if dataDimRef:
          peakDim.numAliasing = int(divmod(position[i], dataDim.numPointsOrig)[0])
          peakDim.position = float(position[i] + 1 - peakDim.numAliasing * dataDim.numPointsOrig)  # API position starts at 1

        else:
          peakDim.position = float(position[i] + 1)
        
        if fitMethod and linewidth[i] is not None:
          peakDim.lineWidth = dataDim.valuePerPoint * linewidth[i] # conversion from points to Hz
        
      peak.height = height
      peaks.append(peak)
    
  return peaks

def fitExistingPeakList(self:PeakList, fitMethod:str=None):

  if fitMethod:
    # import has to be inside function because of circular imports
    from ccpncore.lib.spectrum import Peak as LibPeak
    LibPeak.fitExistingPeaks(self.sortedPeaks(), fitMethod)
