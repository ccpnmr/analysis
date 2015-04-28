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

Sequence = collections.abc.Sequence

def findPeaks(peakList:object, positions:Sequence=None, dataDims:Sequence=None):


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