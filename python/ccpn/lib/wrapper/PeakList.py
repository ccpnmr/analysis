from ccpncore.lib.ccp.nmr.Nmr.PeakList import pickNewPeaks

import collections

Sequence = collections.abc.Sequence

def findPeaks(peakList:object, positions:Sequence=None, dataDims:Sequence=None):

  ordering = [dataDim.dim-1 for dataDim in dataDims]

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
  print(ordering, startPoint, startPoints, endPoint, endPoints)

  posLevel = spectrum.positiveContourBase*5e2
  negLevel = spectrum.negativeContourBase*5e2

  print(posLevel)

  return pickNewPeaks(peakList.apiPeakList, startPoint=startPoints, endPoint=endPoints, posLevel=posLevel, negLevel=negLevel)