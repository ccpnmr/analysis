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

def pickNewPeaks(peakList, startPoint, endPoint, posLevel=None, negLevel=None,
                 minLinewidth=None, exclusionBuffer=None,
                 minDropfactor=0.0, checkAllAdjacent=True,
                 fitMethod=None):

  # TBD: ignores aliasing for now
  
  from ccpnc.peak import Peak

  if fitMethod:
    assert fitMethod in ('gaussian', 'lorentzian'), 'fitMethod = %s, must be one of ("gaussian", "lorentzian")' % fitMethod
    method = 0 if fitMethod == 'gaussian' else 1
    
  peaks = []

  if posLevel is None and negLevel is None:
    return peaks

  dataSource = peakList.dataSource
  numDim = dataSource.numDim

  if not minLinewidth:
    minLinewidth = [0.0] * numDim

  if not exclusionBuffer:
    exclusionBuffer =  [1] * numDim

  nonAdj = 1 if checkAllAdjacent else 0

  dataArray, intRegion = dataSource.getRegionData(startPoint, endPoint)
  startPoint, endPoint = intRegion
  startPoint = numpy.array(startPoint)
  endPoint = numpy.array(endPoint)
  numPoint = endPoint - startPoint

  """
  existingPeaks = getRegionPeaks(peakList, startPoint, endPoint)
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
  peakPoints = Peak.findPeaks(dataArray, doNeg, doPos,
                              negLevel, posLevel, exclusionBuffer,
                              nonAdj, minDropfactor, minLinewidth)

  existingPositions = []
  for peak in peakList.peaks:
    position = numpy.array([peakDim.position for peakDim in peak.sortedPeakDims()])  # ignores aliasing
    existingPositions.append(position-1) # -1 because API position starts at 1
    
  exclusionBuffer = numpy.array(exclusionBuffer)
               
  peaks = []
  for position, height in peakPoints:
    
    position = numpy.array(position) + startPoint
    
    for existingPosition in existingPositions:
      delta = abs(existingPosition - position)
      if (delta < exclusionBuffer).all():
        break     
    else:      
      if fitMethod:
        position -= startPoint
        numDim = len(position)
        firstArray = numpy.maximum(position - 2, 0)
        lastArray = numpy.minimum(position + 3, numPoint)
        peakArray = position.reshape((1, numDim))
        peakArray = peakArray.astype('float32')
        firstArray = firstArray.astype('int32')
        lastArray = lastArray.astype('int32')
        regionArray = numpy.array((firstArray, lastArray))

        try:
          result = Peak.fitPeaks(dataArray, regionArray, peakArray, method)
          height, center, linewidth = result[0]
        except Peak.error as e:
          # possibly should log error??
          dimCount = len(startPoint)
          height = dataArray[tuple(position)]
          center = position
          linewidth = dimCount * [None]
        position = center + startPoint
      
      peak = peakList.newPeak()

      dataDims = dataSource.sortedDataDims()
      peakDims = peak.sortedPeakDims()

      for i, peakDim in enumerate(peakDims):
        dataDim = dataDims[i]

        if dataDim.className == 'FreqDataDim':
          dataDimRef = dataDim.primaryDataDimRef
        else:
          dataDimRef = None

        if dataDimRef:
          #peakDim.numAliasing = int(divmod(position[i], dataDimRef.dataDim.numPointsOrig)[0])
          peakDim.numAliasing = 0   
          peakDim.position = float(position[i] + 1 - peakDim.numAliasing * dataDim.numPointsOrig)  # API position starts at 1

        else:
          peakDim.position = float(position[i] + 1)
        
        if fitMethod and linewidth[i] is not None:
          peakDim.lineWidth = linewidth[i]
        
      peak.height = height
      peaks.append(peak)
    
  return peaks

