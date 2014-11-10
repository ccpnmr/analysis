"""
======================COPYRIGHT/LICENSE START==========================

DataSource.py: Utility functions for ccp.nmr.Nmr.DataSource

Copyright (C) 2005-2013 Wayne Boucher, Rasmus Fogh, Tim Stevens and Wim Vranken (University of Cambridge and EBI/PDBe)

=======================================================================

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

A copy of this license can be found in ../../../license/LGPL.license

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA


======================COPYRIGHT/LICENSE END============================

for further information, please contact :

- CCPN website (http://www.ccpn.ac.uk/)
- PDBe website (http://www.ebi.ac.uk/pdbe/)

=======================================================================

If you are using this software for academic purposes, we suggest
quoting the following references:

===========================REFERENCE START=============================
R. Fogh, J. Ionides, E. Ulrich, W. Boucher, W. Vranken, J.P. Linge, M.
Habeck, W. Rieping, T.N. Bhat, J. Westbrook, K. Henrick, G. Gilliland,
H. Berman, J. Thornton, M. Nilges, J. Markley and E. Laue (2002). The
CCPN project: An interim report on a data model for the NMR community
(Progress report). Nature Struct. Biol. 9, 416-418.

Wim F. Vranken, Wayne Boucher, Tim J. Stevens, Rasmus
H. Fogh, Anne Pajon, Miguel Llinas, Eldon L. Ulrich, John L. Markley, John
Ionides and Ernest D. Laue (2005). The CCPN Data Model for NMR Spectroscopy:
Development of a Software Pipeline. Proteins 59, 687 - 696.

Rasmus H. Fogh, Wayne Boucher, Wim F. Vranken, Anne
Pajon, Tim J. Stevens, T.N. Bhat, John Westbrook, John M.C. Ionides and
Ernest D. Laue (2005). A framework for scientific data modeling and automated
software development. Bioinformatics 21, 1678-1684.

===========================REFERENCE END===============================
"""

import numpy
import os

# Additional functions for ccp.nmr.Nmr.DataSource
#
# NB All functions must have a mandatory DataSource as the first parameter
# so they can be used as DataSource methods
from ccpncore.lib.ccp.nmr.Nmr.Experiment import getOnebondExpDimRefs, getAcqExpDim
from ccpncore.lib.ccp.nmr.Nmr.AbstractDataDim import getIsotopeCodes
# from ccpncore.lib.spectrum.Integral import getIntegralRegions, setIntegrals, calculateIntegralValues
from ccpncore.lib.spectrum.Integral import Integral as spInt


def getDimCodes(dataSource):
  """ Get dimcode of form hx1, hx2, x1, x2, where the x's are directly bound to 
  the corresponding H. suffix '1' is given to the acquisition proton dimension.
  Dimensions not matching the specs are given code None
  """
  isotopeCodes=getIsotopeCodesList(dataSource)
  
  acqExpDim = getAcqExpDim(dataSource.experiment)
  dataDims = dataSource.sortedDataDims()
  dimCodes = [None]*dataSource.numDim
  for ii,dataDim in enumerate(dataDims):
    if isotopeCodes[ii] == '1H':
      if dataDim.expDim is acqExpDim:
        dimCodes[ii] = 'hx1'
        xCode = 'x1'
      else:
        dimCodes[ii] = 'hx2'
        xCode = 'x2'
      for tt in getOnebondDataDims(dataSource):
        if tt[0] is dataDim:
          xDim = tt[1]
          dimCodes[dataDims.index(xDim)] = xCode
          break
  #
  return dimCodes
  
  
def getXEasyDimCodes(dataSource):
  """ Get Xeasy-style dimCodes in dim order for data Source
  For use in FormatCOnverter
  """
  #
  # Get isotopecode info
  #
  isotopeCodes = getIsotopeCodesList(dataSource)
  dimCodes = getDimCodes(dataSource)
  reverse = bool( 'x2' in dimCodes and not 'x1' in dimCodes)
  found = set()
  for ii,code in enumerate(dimCodes):
    elementType = isotopeCodes[ii][-1]
    if code and (('2' in code) != reverse):
      dimCodes[ii] = elementType.lower()
    else:
      dimCodes[ii] = elementType
    
  #
  # Fix in homonuclear 2D case...
  #
  #firstDimCode = dimCodes[0]
  #if dimCodes.count(firstDimCode) == len(dimCodes):
  #  if firstDimCode == firstDimCode.lower():
  #    dimCodes[0] = firstDimCode.upper()
  #
  # and generally distinguish duplicates. Rasmus Fogh 15/6/12
  foundset = set()
  for ii,ss in enumerate(dimCodes):
    if ss in foundset:
      ss = ss.upper()
    if ss in foundset:
      ss = ss.lower()
    dimCodes[ii] = ss
    foundset.add(ss)
  #
  return dimCodes
  

# NB renamed from getSpectrumIsotopes getIsotopeCodesList
#def getSpectrumIsotopes(dataSource):
def getIsotopeCodesList(dataSource):
  """
  Give isotope code strings pertaining to the dimensions of a given NMR spectrum 
  
  .. describe:: Input
  
  Nmr.DataSource
  
  .. describe:: Output

  List of Strings (comma-joined Nmr.ExpDimRef.IsotopeCodes)
  """

  isotopes = []
  for dataDim in dataSource.sortedDataDims():
    isotopeCodes = list(getIsotopeCodes(dataDim))
    isotopes.append(','.join(sorted(isotopeCodes)) or None)
  
  return isotopes
  
       
def getOnebondDataDims(spectrum):
  """
  Get pairs of spectrum data dimensions that are connected by onebond transfers
  
  .. describe:: Input
  
  Nmr.DataSource
  
  .. describe:: Output

  List of 2-List of Nmr.DataDims
  """
  
  dataDims = []
  expDimRefs = getOnebondExpDimRefs(spectrum.experiment)

  for expDimRef0, expDimRef1 in expDimRefs:
    dataDim0 = spectrum.findFirstDataDim(expDim=expDimRef0.expDim)
    dataDim1 = spectrum.findFirstDataDim(expDim=expDimRef1.expDim)

    if dataDim0 and dataDim1:
      dataDims.append( [dataDim0,dataDim1] )

  return dataDims

def _cumulativeArray(array):
  """ get total size and strides array. 
      NB assumes fastest moving index first """

  ndim = len(array)
  cumul = ndim * [0]
  n = 1
  for i, size in enumerate(array):
    cumul[i] = n
    n = n * size

  return (n, cumul)
  

def getPlaneData(spectrum, position=None, xDim=0, yDim=1):
  """ Get plane data through position in dimensions xDim, yDim
      Returns 2D float32 NumPy array in order (y, x) 
      Returns None if numDim < 2 or if there is no dataStore """

  numDim = spectrum.numDim
  if numDim < 2:
    return None
    
  dataStore = spectrum.dataStore
  if not dataStore:
    return None
         
  assert numDim == 2 or (position and len(position) == numDim), 'numDim = %d, position = %s' % (numDim, position)
  assert xDim != yDim, 'xDim = yDim = %d' % xDim
  assert 0 <= xDim < numDim, 'xDim = %d' % xDim
  assert 0 <= yDim < numDim, 'yDim = %d' % yDim

  if not position:
    position = numDim*[0]

  dataDims = spectrum.sortedDataDims()
  numPoints = [dataDim.numPoints for dataDim in dataDims]
  xPoints = numPoints[xDim]
  yPoints = numPoints[yDim]
    
  for dim in range(numDim):
    point = position[dim]
    if point >= numPoints[dim]:
      raise ValueError('Plane index %d in dimension %d not within spectrum bounds (%d)' % (point, dim+1, numPoints[dim]))
    if point < 0:
      raise ValueError('Plane index %d in dimension %d less than 0' % (point, dim+1))

  blockSizes = dataStore.blockSizes
  blockSize, cumulativeBlockSizes = _cumulativeArray(blockSizes)
  wordSize = dataStore.nByte
  isBigEndian = dataStore.isBigEndian
  isFloatData = dataStore.numberType == 'float'
  headerSize = dataStore.headerSize
  format = dataStore.fileType
  #blockHeaderSize = dataStore.blockHeaderSize  # TBD: take this into account
  blocks = [1 + (numPoints[dim]-1) // blockSizes[dim] for dim in range(numDim)]
  numBlocks, cumulativeBlocks = _cumulativeArray(blocks)
  dtype = '%s%s%s' % (isBigEndian and '>' or '<', isFloatData and 'f' or 'i', wordSize)
  
  xblockSize = blockSizes[xDim]
  yblockSize = blockSizes[yDim]

  xblocks = 1 + (xPoints-1) // xblockSize
  yblocks = 1 + (yPoints-1) // yblockSize

  blockCoords = [position[dim] // blockSizes[dim] for dim in range(numDim)]
  blockSlice = numDim*[0]
    
  for dim in range(numDim):
    if dim not in (xDim, yDim):
      p = position[dim] % blockSizes[dim]
      blockSlice[numDim-dim-1] = slice(p, p+1)

  blockSizes = blockSizes[::-1]  # reverse (dim ordering backwards)
    
  data = numpy.zeros((yPoints, xPoints), dtype=numpy.float32)
  
  fileName = dataStore.fullPath
  fp = open(fileName, 'rb')
  
  for xblock in range(xblocks):
    
    blockCoords[xDim] = xblock
    xlower = xblock * xblockSize
    xupper = min(xlower+xblockSize, xPoints)
    blockSlice[numDim-xDim-1] = slice(xupper-xlower)
      
    for yblock in range(yblocks):
      
      blockCoords[yDim] = yblock
      ylower = yblock * yblockSize
      yupper = min(ylower+yblockSize, yPoints)
      blockSlice[numDim-yDim-1] = slice(yupper-ylower)
      
      ind =  sum(x[0]*x[1] for x in zip(blockCoords, cumulativeBlocks))
      offset = wordSize * (blockSize * ind) + headerSize
      fp.seek(offset, 0)
      blockData = numpy.fromfile(file=fp, dtype=dtype, count=blockSize).reshape(blockSizes) # data is in reverse order: e.g. z,y,x not x,y,z

      if blockData.dtype != numpy.float32:
        blockData = numpy.array(blockData, numpy.float32)
      
      blockPlane = blockData[tuple(blockSlice)]
        
      if xDim > yDim:
        blockPlane = blockPlane.transpose()
          
      blockPlane = blockPlane.squeeze()
      data[ylower:yupper, xlower:xupper] = blockPlane
    
  fp.close()
  
  return data

def getSliceData(spectrum, position=None, sliceDim=0):
  # Get an actual array of data points,
  # spanning blocks as required
  # returns 1D array

  numDim = spectrum.numDim
  if numDim < 1:
    return None

  dataStore = spectrum.dataStore
  if not dataStore:
    return None

  if not position:
    position = numDim * [0]

  dataDims = spectrum.sortedDataDims()
  numPoints = [dataDim.numPoints for dataDim in dataDims]
  slicePoints = numPoints[sliceDim]

  data = numpy.empty((slicePoints,), dtype=numpy.float32)

  for dim in range(numDim):
    point = position[dim]
    if point >= numPoints[dim]:
      raise ValueError('Slice index %d not within spectrum bounds' % point)
    if point < 0:
      raise ValueError('Slice index %d less than 0' % point)

  blockSizes = dataStore.blockSizes
  blockSize, cumulativeBlockSizes = _cumulativeArray(blockSizes)
  wordSize = dataStore.nByte
  isBigEndian = dataStore.isBigEndian
  isFloatData = dataStore.numberType == 'float'
  headerSize = dataStore.headerSize
  format = dataStore.fileType
  #blockHeaderSize = dataStore.blockHeaderSize  # TBD: take this into account
  blocks = [1 + (numPoints[dim]-1) // blockSizes[dim] for dim in range(numDim)]
  numBlocks, cumulativeBlocks = _cumulativeArray(blocks)
  dtype = '%s%s%s' % (isBigEndian and '>' or '<', isFloatData and 'f' or 'i', wordSize)

  sliceBlockSize = blockSizes[sliceDim]
  sliceBlocks = 1 + (slicePoints-1)//sliceBlockSize

  blockCoords = [position[dim]//blockSizes[dim] for dim in range(numDim)]
  blockSlice = numDim*[0]

  for dim in range(numDim):
    if dim != sliceDim:
      p = position[dim] % blockSizes[dim]
      blockSlice[numDim-dim-1] = slice(p,p+1)

  blockSizes = blockSizes[::-1]  # reverse (dim ordering backwards)

  fileName = dataStore.fullPath
  fp = open(fileName, 'rb')

  for sliceBlock in range(sliceBlocks):
    blockCoords[sliceDim] = sliceBlock
    sliceLower = sliceBlock * sliceBlockSize
    sliceUpper = min(sliceLower+sliceBlockSize, slicePoints)
    blockSlice[numDim-sliceDim-1] = slice(sliceUpper-sliceLower)

    ind =  sum(x[0]*x[1] for x in zip(blockCoords, cumulativeBlocks))
    offset = wordSize * (blockSize * ind) + headerSize
    fp.seek(offset, 0)
    blockData = numpy.fromfile(file=fp, dtype=dtype, count=blockSize).reshape(blockSizes) # data is in reverse order: e.g. z,y,x not x,y,z

    if blockData.dtype != numpy.float32:
      blockData = numpy.array(blockData, numpy.float32)

    data[sliceLower:sliceUpper] = blockData[blockSlice].squeeze()

  fp.close()

  return data

def getRegionData(spectrum, startPoint, endPoint):

  dataStore = spectrum.dataStore
  if not dataStore:
    return None
      
  blockSizes = dataStore.blockSizes
  dataDims = spectrum.sortedDataDims()
  numPoints = [dataDim.numPoints for dataDim in dataDims]
  numDim = spectrum.numDim
    
  blockRanges = []
  rangeSizes = []
  regionSizes = []
   
  startPoint = list(startPoint)
  endPoint = list(endPoint)
  for dim in range(numDim):
    start = min(startPoint[dim], endPoint[dim])
    end = max(startPoint[dim], endPoint[dim])
      
    start = min(max(1, int(start)), numPoints[dim]-1)
    end = min(max(1, int(end)), numPoints[dim]-1)
   
    startPoint[dim] = start
    endPoint[dim] = end

  intRegion = (startPoint, endPoint)
   
  n = 1
  for dim in dims:
    startBlockCoord = int(startPoint[dim]//blockSizes[dim])
    endBlockCoord = int(endPoint[dim]//blockSizes[dim])
    blockRange = range(startBlockCoord,endBlockCoord+1)
    blockRanges.append(blockRange)
    m = len(blockRange)
    rangeSizes.append(m)
    regionSizes.append(int(endPoint[dim]-startPoint[dim])+1)
    n *= m
   
  blockCoords = [None] * n
  for i in range(n):
    blockCoord = []

    j = i
    for dim in dims:
      index = j % rangeSizes[dim]
      blockCoord.append(blockRanges[dim][index])
      j = j // rangeSizes[dim]

    blockCoords[i] =  tuple(blockCoord)

  data = zeros(regionSizes, dtype=numpy.float32)

  dataSlice = [0] * numDim
  blockSlice = [0] * numDim

  blockSize, cumulativeBlockSizes = _cumulativeArray(blockSizes)
  wordSize = dataStore.nByte
  isBigEndian = dataStore.isBigEndian
  isFloatData = dataStore.numberType == 'float'
  headerSize = dataStore.headerSize
  format = dataStore.fileType
  blocks = [1 + (numPoints[dim]-1) // blockSizes[dim] for dim in range(numDim)]
  numBlocks, cumulativeBlocks = _cumulativeArray(blocks)
  dtype = '%s%s%s' % (isBigEndian and '>' or '<', isFloatData and 'f' or 'i', wordSize)
    
  for blockCoord in blockCoords:

    for i in dims:
      first = 1 + blockCoord[i] * blockSizes[i]
      next = first + blockSizes[i]
      offset = startPoint[i]

      if first < offset:
        blockLow = offset-first
      else:
        blockLow = 0

      if next > endPoint[i]+1:
        blockHigh = blockSizes[i] + (endPoint[i]+1-next)
      else:
        blockHigh = blockSizes[i]

      dataLow = first - offset + blockLow
      dataHigh = dataLow + (blockHigh-blockLow)

      dataSlice[i] = s_[dataLow:dataHigh]
      blockSlice[i] = s_[blockLow:blockHigh]

    ind =  sum(x[0]*x[1] for x in zip(blockCoord, cumulativeBlocks))
    offset = wordSize * (blockSize * ind) + headerSize
    fp.seek(offset, 0)
    blockData = numpy.fromfile(file=fp, dtype=dtype, count=blockSize).reshape(blockSizes) # data is in reverse order: e.g. z,y,x not x,y,z

    if blockData.dtype != numpy.float32:
      blockData = numpy.array(blockData, numpy.float32)
      
    data[dataSlice] = blockData[blockSlice].T

  return data.T, intRegion
  
def automaticIntegration(spectrum,spectralData):
#
  numDim = spectrum.numDim
  if numDim != 1:
    return
  dataStore = spectrum.dataStore
  if not dataStore:
    return None
  # spectrum.valueArray = [[]] * numDim
  # if len(valueArray[xDim]) != 0:
  #   valueArray = valueArray[xDim]
  valueArray = spectrum.valueArray = spectralData
  noise = estimateNoise(spectrum)
  level =  noise * 6
  # if len(self.peakList) > 0:
  #   integrals = self.getPeakIntegralRegions(valueArray[1, :], noise, level)
  # else:
  integrals = spInt.getIntegralRegions(spectralData[1, :], noise, level)
  spInt.setIntegrals(spectrum,integrals)

  #
  for integral in spectrum.integrals:
    integral.calculateBias(spectralData[1, :], noise)
    spInt.calculateIntegralValues(integral.points, spectralData[1, :], integral.bias*-1, integral.slope)

  if len(spectrum.integrals) > 0:
    spectrum.integralFactor = 1/spectrum.integrals[0].points[-1][0]
  else:
    spectrum.integralFactor = None
  for integral in spectrum.integrals:
    integral.calculateVolume()

  #
  # for a in spectrum.integrals:
  #   # print(spectrum.integralFactor)
  #


  return spectrum.integrals


# def setIntegrals(spectrum, dim, values, factor = 1.0):
#
#     self.integrals = []
#     # append = self.integrals.append

def estimateNoise(spectrum):

    if spectrum.noiseLevel:
      return spectrum.noiseLevel

    if spectrum.numDim > 1:
      planeData = getPlaneData([0] * spectrum.numDim, 0, 1)
      value = 1.1 * numpy.std(planeData.flatten()) # multiplier a guess
    else:

      if hasattr(spectrum, 'valueArray') and len(spectrum.valueArray) != 0:
        sliceData = spectrum.valueArray
      else:
        spectrum.valueArray = sliceData = getSliceData(spectrum)
      # print(sliceData)
      # print(sliceData[1])
      sliceDataStd = numpy.std(sliceData)
      sliceData = numpy.array(sliceData,numpy.float32)
      # Clip the data to remove outliers
      sliceData = sliceData.clip(-sliceDataStd, sliceDataStd)

      value = 1.1 * numpy.std(sliceData) # multiplier a guess

    #value *= self.scale

    spectrum.noiseLevel = float(value)

    return spectrum.noiseLevel # Qt can't serialise numpy float types

def getDimPointFromValue(spectrum, dimension, value):
  """ Convert from value (e.g. ppm) to point (counting from 0) for an arbitrary
      number of values in a given dimension (counting from 0).  If value is a
      number then return a number, otherwise return a list.
  """
  dataDim = spectrum.findFirstDataDim(dim=dimension+1)
  dataDimRef = dataDim.findFirstDataDimRef()
    
  if isinstance(value, (int, float)):
    point = dataDimRef.valueToPoint(value) - 1  # -1 because points in data model start from 1
  else:
    point = []
    for v in value:
      point.append(dataDimRef.valueToPoint(v) - 1)  # -1 because points in data model start from 1
      
  return point
    
def getDimValueFromPoint(spectrum, dimension, point):
  """ Convert from point (counting from 0) to value (e.g. ppm) for an arbitrary
      number of points in a given dimension (counting from 0).  If point is a
      number then return a number, otherwise return a list.
  """
  dataDim = spectrum.findFirstDataDim(dim=dimension+1)
  dataDimRef = dataDim.findFirstDataDimRef()

  if isinstance(point, (int, float)):
    value = dataDimRef.pointToValue(point+1)  # +1 because points in data model start from 1
  else:
    value = []
    for p in point:
      value.append(dataDimRef.pointToValue(p+1))  # +1 because points in data model start from 1
      
  return value




