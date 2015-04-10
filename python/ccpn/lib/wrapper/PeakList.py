from ccpncore.lib.ccp.nmr.Nmr.PeakList import pickNewPeaks

import collections

Sequence = collections.abc.Sequence

def findPeaks(peakList:object, positions:Sequence=None, dataDims:Sequence=None):

  ordering = []

  for dataDim in dataDims:
    ordering.append(dataDim.dim-1)

  startPoint = []
  endPoint = []

  spectrum = peakList.spectrum

  for position in positions[1]:
    endPoint.append(int(spectrum.getDimPointFromValue(ordering[positions[1].index(position)], position)))

  for position in positions[0]:
    startPoint.append(int(spectrum.getDimPointFromValue(ordering[positions[0].index(position)], position)))

  return pickNewPeaks(peakList.apiPeakList, startPoint=startPoint, endPoint=endPoint, posLevel=1.0e7)