#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:32 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
from ccpn.util.Logging import getLogger
from collections import OrderedDict

POSITIONS = 'positions'
HEIGHT = 'height'
VOLUME = 'volume'
LINEWIDTHS = 'lineWidths'

MODES = [POSITIONS, HEIGHT, VOLUME, LINEWIDTHS]
OTHER = 'Other'
H = 'H'
N = 'N'
C = 'C'
DefaultAtomWeights = OrderedDict(((H, 7.00), (N, 1.00), (C, 4.00), (OTHER, 1.00)))

def getPeakPosition(peak, dim, unit='ppm'):

  if len(peak.dimensionNmrAtoms) > dim:
    # peakDim = peak.position[dim]

    if peak.position[dim] is None:
      value = None              #"*NOT SET*"

    elif unit == 'ppm':
      value = peak.position[dim]

    elif unit == 'point':
      value = peak.pointPosition[dim]

    elif unit == 'Hz':
      # value = peak.position[dim]*peak._apiPeak.sortedPeakDims()[dim].dataDimRef.expDimRef.sf
      value = peak.position[dim]*peak.peakList.spectrum.spectrometerFrequencies[dim]

    else: # sampled
      # value = unit.pointValues[int(peak._apiPeak.sortedPeakDims()[dim].position)-1]
      raise ValueError("Unit passed to getPeakPosition must be 'ppm', 'point', or 'Hz', was %s"
                     % unit)

    if isinstance(value, (int, float, np.float32, np.float64)):
      return '{0:.2f}'.format(value)

    return None

    # if isinstance(value, [int, float]):
    # # if type(value) is int or type(value) in (float, float32, float64):
    #   return '%7.2f' % float(value)

def getPeakAnnotation(peak, dim, separator=', '):
  if len(peak.dimensionNmrAtoms) > dim:
    return separator.join([dna.pid.id for dna in peak.dimensionNmrAtoms[dim]])

def getPeakLinewidth(peak, dim):
  if dim < len(peak.lineWidths):
    lw = peak.lineWidths[dim]
    if lw:
      return float(lw)


def _getAtomWeight(axisCode, atomWeights) -> float or int:
  '''

  :param axisCode: str of peak axis code
  :param atomWeights: dictionary of atomWeights eg {'H': 7.00, 'N': 1.00, 'C': 4.00, 'Other': 1.00}
  :return: float or int from dict atomWeights
  '''
  value = 1.0
  if len(axisCode) > 0:
    firstLetterAxisCode = axisCode[0]
    if firstLetterAxisCode in atomWeights:
      value = atomWeights[firstLetterAxisCode]
    else:
      if OTHER in atomWeights:
        if atomWeights[OTHER] != 1:
          value = atomWeights[OTHER]
      else:
        value = 1.0

  return value


def getDeltaShiftsNmrResidue(nmrResidue, nmrAtoms, spectra, mode=POSITIONS, atomWeights=None):
  '''
  
  :param nmrResidue: 
  :param nmrAtoms: nmr Atoms to compare. str 'H' , 'N' , 'CA' etc
  :param spectra: compare peaks only from given spectra
  :return: 
  '''

  deltas = []
  peaks = []

  if len(spectra) <=1:
    return
  if atomWeights is None:
    atomWeights = DefaultAtomWeights

  for  nmrAtomName in nmrAtoms:
    nmrAtom = nmrResidue.getNmrAtom(str(nmrAtomName))
    if nmrAtom is not None:
      peaks += [p for p in nmrAtom.assignedPeaks if p.peakList.spectrum in spectra and p not in peaks]


  if len(peaks)>0:
    for i, peak in enumerate(peaks):
      if peak.peakList.spectrum in spectra:
        try: #some None value can get in here
          if mode == POSITIONS:
            delta = None
            for i, axisCode in enumerate(peak.axisCodes):
              if axisCode:
                weight = _getAtomWeight(axisCode, atomWeights)
                if axisCode[0] in nmrAtoms:
                  if delta is None:
                    delta = 0.0
                  delta += ((peak.position[i] - list(peaks)[0].position[i]) * weight) ** 2
                  delta = delta ** 0.5

            deltas += [delta]



            # if len(peak.position) == 2:
            #   delta1Atoms = (peak.position[0] - list(peaks)[0].position[0])
            #   delta2Atoms = (peak.position[1] - list(peaks)[0].position[1])
            #
            #   deltas += [((delta1Atoms * weight1) ** 2 + (delta2Atoms * weight2) ** 2) ** 0.5, ]

          if mode == VOLUME:
            delta1Atoms = (peak.volume - list(peaks)[0].volume)
            deltas += [((delta1Atoms)** 2 ) ** 0.5, ]

          if mode == HEIGHT:
            delta1Atoms = (peak.height - list(peaks)[0].height)
            deltas += [((delta1Atoms) ** 2) ** 0.5,]

          if mode == LINEWIDTHS:
            if len(peak.lineWidths) == 2:
              delta1Atoms = (peak.lineWidths[0] - list(peaks)[0].lineWidths[0])
              delta2Atoms = (peak.lineWidths[1] - list(peaks)[0].lineWidths[1])
              deltas += [((delta1Atoms * weight1) ** 2 + (delta2Atoms * weight2) ** 2) ** 0.5,]
        except Exception as e:
          message = 'Error for calculation mode: %s on %s and %s. ' % (mode, peak.pid, list(peaks)[0].pid) + str(e)
          getLogger().debug(message)




  if deltas and not None in deltas:
    return round(float(np.mean(deltas)),3)
  return



































