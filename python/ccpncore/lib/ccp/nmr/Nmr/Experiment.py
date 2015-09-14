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
"""
======================COPYRIGHT/LICENSE START==========================

Experiment.py: Utility functions for ccp.nmr.Nmr.Experiment

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
import re
from ccpncore.lib.typing import Sequence

# Additional functions for ccp.nmr.Nmr.Experiment
#
# NB All functions must have a mandatory Experiment as the first parameter
# so they can be used as Experiment methods



def getAcqExpDim(experiment, ignorePreset=False):
  """
  ExpDim that corresponds to acquisition dimension. NB uses heuristics

  .. describe:: Input
  
   Nmr.Experiment
  
  .. describe:: Output
  
  Nmr.ExpDim
  """
  
  ll = experiment.findAllExpDims(isAcquisition=True)
  if len(ll) == 1 and not ignorePreset:
    # acquisition dimension set - return it
    result = ll.pop()
  
  else:
    # no reliable acquisition dimension set
    result = None
    
    dataSources = experiment.sortedDataSources()
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
      ll = experiment.sortedExpDims()
      if ll:
        result = ll[0]
      
  #
  return result
  
  
def getOnebondExpDimRefs(experiment):
  """
  Get pairs of experiment dimensions that are connected by onebond transfers
  
  .. describe:: Input
  
  Nmr.Experiment
  
  .. describe:: Output

  List of 2-List of Nmr.ExpDimRefs
  """

  expDimRefs   = []
  expTransfers = []
  
  for expTransfer in experiment.sortedExpTransfers():
    if expTransfer.transferType in ('onebond',):
      expTransfers.append(expTransfer)
  
  for expTransfer in expTransfers:
    expDimRefs.append(expTransfer.sortedExpDimRefs())
  
  return expDimRefs


def resetAxisCodes(experiment):
  """Set axis codes from per-dimension parameters and heuristics, e.g. for newly loaded spectrum
  NB ignores expTransfer and links to NmrExpPrototype"""

  # dataDims = spectrum.sortedDataDims()

  # NB determine acquisition dimension to decide which end to start indexing
  axisCodes = []
  usedCodes = set()
  for expDim in experiment.sortedExpDims():
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



def createDataSource(experiment:object, name:str, numPoints:Sequence, sw:Sequence,
                     refppm:Sequence, refpt:Sequence, dataStore:object=None,
                     scale:float=1.0, details:str=None, numPointsOrig:Sequence=None,
                     pointOffset:Sequence=None, isComplex:Sequence=None,
                     **additionalParameters) -> object:
  """Create a processed DataSource, with FreqDataDims, and one DataDimRef for each DataDim.
  NB Assumes that number and order of dimensions match the Experiment.
  Parameter names generally follow CCPN data model names. dataStore is a BlockedBinaryMatrix object
  Sequence type parameters are one per dimension.
  Additional  parameters for the DataSource are passed in additionalParameters"""

  numDim = len(numPoints)

  if numDim != experiment.numDim:
    raise ValueError('numDim = %d != %d = experiment.numDim' % (numDim, experiment.numDim))

  spectrum = experiment.newDataSource(name=name, dataStore=dataStore, scale=scale, details=details,
                                      numDim=numDim, dataType='processed', **additionalParameters)

  # NBNB TBD This is not a CCPN attribute. Removed. Put back if you need it after all,
  # spectrum.writeable = writeable

  if not numPointsOrig:
    numPointsOrig = numPoints

  if not pointOffset:
    pointOffset = (0,) * numDim

  if not isComplex:
    isComplex = (False,) * numDim


  for n , expDim in enumerate(experiment.sortedExpDims()):
    freqDataDim = spectrum.newFreqDataDim(dim=n+1, numPoints=numPoints[n],
                             isComplex=isComplex[n], numPointsOrig=numPointsOrig[n],
                             pointOffset=pointOffset[n],
                             valuePerPoint=sw[n]/float(numPoints[n]), expDim=expDim)
    expDimRef = (expDim.findFirstExpDimRef(measurementType='Shift') or expDim.findFirstExpDimRef())
    if expDimRef:
      freqDataDim.newDataDimRef(refPoint=refpt[n], refValue=refppm[n], expDimRef=expDimRef)

  return spectrum