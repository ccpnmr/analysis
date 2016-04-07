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

import re

from typing import Sequence, List

import collections


# Additional functions for ccp.nmr.Nmr.Experiment
#
# NB All functions must have a mandatory Experiment as the first parameter
# so they can be used as Experiment methods



def getAcqExpDim(self:'Experiment', ignorePreset:bool=False) -> 'ExpDim':
  """
  ExpDim that corresponds to acquisition dimension. NB uses heuristics

  .. describe:: Input
  
   Nmr.Experiment
  
  .. describe:: Output
  
  Nmr.ExpDim
  """
  
  ll = self.findAllExpDims(isAcquisition=True)
  if len(ll) == 1 and not ignorePreset:
    # acquisition dimension set - return it
    result = ll.pop()
  
  else:
    # no reliable acquisition dimension set
    result = None
    
    dataSources = self.sortedDataSources()
    if dataSources:
      dataSource = dataSources[0]
      for ds in dataSources[1:]:
        # more than one data source. Pick one of the largest.
        if ds.numDim > dataSource.numDim:
          dataSource = ds
      
      # Take dimension with most points
      useDim = None
      currentVal = -1
      for dd in dataSource.sortedDataDims():
        if hasattr(dd, 'numPointsOrig'):
          val = dd.numPointsOrig
        else:
          val = dd.numPoints
        if val > currentVal:
          currentVal = val
          useDim = dd
      
      if useDim is not None:
        result = useDim.expDim
  
    if result is None:
      # no joy so far - just take first ExpDim
      ll = self.sortedExpDims()
      if ll:
        result = ll[0]
      
  #
  return result
  
  
def getOnebondExpDimRefs(self:'Experiment') -> List[List['ExpDimRef']]:
  """
  Get pairs of experiment dimensions that are connected by onebond transfers
  
  .. describe:: Input
  
  Nmr.Experiment
  
  .. describe:: Output

  List of 2-List of Nmr.ExpDimRefs
  """

  expDimRefs   = []
  expTransfers = []
  
  for expTransfer in self.sortedExpTransfers():
    if expTransfer.transferType in ('onebond',):
      expTransfers.append(expTransfer)
  
  for expTransfer in expTransfers:
    expDimRefs.append(expTransfer.sortedExpDimRefs())
  
  return expDimRefs


def resetAxisCodes(self:'Experiment'):
  """Set axis codes from per-dimension parameters and heuristics, e.g. for newly loaded spectrum
  NB ignores expTransfer and links to NmrExpPrototype"""

  # dataDims = spectrum.sortedDataDims()

  # NB determine acquisition dimension to decide which end to start indexing
  axisCodes = []
  usedCodes = set()
  for expDim in self.sortedExpDims():
    for expDimRef in expDim.sortedExpDimRefs():
      elementNames = [str(re.match('\d+(\D+)', x).group(1)) for x in expDimRef.isotopeCodes]

      measurementType = expDimRef.measurementType.lower()
      if measurementType in ('shift', 'troesy', 'shiftanisotropy'):
        # NB TROESY and SHiftAnisotropy ae i practice never used.
        # If they do appear this is the better treatment
        axisCode = elementNames[0]

        dataDimRef = expDimRef.findFirstDataDimRef()
        if dataDimRef is not None:
          if axisCode == 'C':
            # Try to make more specific for CO
            # Other axisCodes are probably too hard to pin down, unfortunately
            minFrequency = dataDimRef.pointToValue(1) - dataDimRef.spectralWidth
            if minFrequency > 150.:
              axisCode = 'CO'

      elif measurementType == 'jcoupling':
        axisCode = 'J' + ''.join([x.lower() for x in elementNames])
      elif measurementType == 'mqshift':
        axisCode = 'MQ' + ''.join([x.lower() for x in elementNames])
      elif measurementType in ('rdc', 'dipolarcoupling'):
        axisCode = 'DC' + ''.join([x.lower() for x in elementNames])
      else:
        # E.g. T1, T2, ...
        # Not always correct, but the best we can do for now.
        axisCode = 'delay'

      index = 0
      useCode = axisCode
      while useCode in usedCodes:
        index += 1
        useCode = '%s%s' % (axisCode, index)
      usedCodes.add(useCode)
      expDimRef.axisCode = useCode



def createDataSource(self:'Experiment', name:str, numPoints:Sequence, sw:Sequence,
                     refppm:Sequence, refpt:Sequence, dataStore:'DataStore'=None,
                     scale:float=1.0, details:str=None, numPointsOrig:Sequence=None,
                     pointOffset:Sequence=None, isComplex:Sequence=None,
                     **additionalParameters) -> 'DataSource':
  """Create a processed DataSource, with FreqDataDims, and one DataDimRef for each DataDim.
  NB Assumes that number and order of dimensions match the Experiment.
  Parameter names generally follow CCPN data model names. dataStore is a BlockedBinaryMatrix object
  Sequence type parameters are one per dimension.
  Additional  parameters for the DataSource are passed in additionalParameters"""

  numDim = len(numPoints)

  if numDim != self.numDim:
    raise ValueError('numDim = %d != %d = experiment.numDim' % (numDim, self.numDim))

  spectrum = self.newDataSource(name=name, dataStore=dataStore, scale=scale, details=details,
                                      numDim=numDim, dataType='processed', **additionalParameters)

  # NBNB TBD This is not a CCPN attribute. Removed. Put back if you need it after all,
  # spectrum.writeable = writeable

  if not numPointsOrig:
    numPointsOrig = numPoints

  if not pointOffset:
    pointOffset = (0,) * numDim

  if not isComplex:
    isComplex = (False,) * numDim


  for n , expDim in enumerate(self.sortedExpDims()):
    freqDataDim = spectrum.newFreqDataDim(dim=n+1, numPoints=numPoints[n],
                             isComplex=isComplex[n], numPointsOrig=numPointsOrig[n],
                             pointOffset=pointOffset[n],
                             valuePerPoint=sw[n]/float(numPoints[n]), expDim=expDim)
    expDimRef = (expDim.findFirstExpDimRef(measurementType='Shift') or expDim.findFirstExpDimRef())
    if expDimRef:
      freqDataDim.newDataDimRef(refPoint=refpt[n], refValue=refppm[n], expDimRef=expDimRef)

  return spectrum