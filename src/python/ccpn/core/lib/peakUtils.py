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
__version__ = "$Revision: 3.0.b2 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np

def getPeakPosition(peak, dim, unit='ppm'):

  if len(peak.dimensionNmrAtoms) > dim:
    # peakDim = peak.position[dim]

    if peak.position[dim] is None:
      value = "*NOT SET*"

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

    if type(value) is int or type(value) is float:
      return '%7.2f' % float(value)

def getPeakAnnotation(peak, dim, separator=', '):
  if len(peak.dimensionNmrAtoms) > dim:
    return separator.join([dna.pid.id for dna in peak.dimensionNmrAtoms[dim]])

def getPeakLinewidth(peak, dim):
  if dim < len(peak.lineWidths):
    lw = peak.lineWidths[dim]
    if lw:
      return float(lw)


def getDeltaShiftsNmrResidue(nmrResidue, nmrAtoms, spectra, atomWeights=None):
  '''
  
  :param nmrResidue: 
  :param nmrAtoms: nmr Atoms to compare. str 'H' , 'N' , 'CA' etc
  :param spectra: compare peaks only from given spectra
  :return: 
  '''

  deltas = []
  peaks = []
  if atomWeights is None:
    atomWeights = {'H': 7, 'N': 1, 'C': 4, 'Other': 1}
  weight1, weight2 = atomWeights['H'], atomWeights['N']

  if len(nmrAtoms) == 2:
    nmrAtom1 = nmrResidue.getNmrAtom(str(nmrAtoms[0]))
    nmrAtom2 = nmrResidue.getNmrAtom(str(nmrAtoms[1]))


    if nmrAtom1 and nmrAtom2 is not None:
      if nmrAtom1.name != nmrAtom2.name:
        for k, weight in atomWeights.items():
          if k in nmrAtom1.name:
            weight1 = weight
          if k in nmrAtom2.name:
            weight2 = weight
        peaks = [p for p in nmrAtom1.assignedPeaks if p.peakList.spectrum in spectra]
        peaks += [p for p in nmrAtom2.assignedPeaks if p.peakList.spectrum in spectra and not peaks]

  if len(peaks)>0:
    for i, peak in enumerate(peaks):
      if peak.peakList.spectrum in spectra:
        if len(peak.position) == 2:
          delta1Atoms = (peak.position[0] - list(peaks)[0].position[0])
          delta2Atoms = (peak.position[1] - list(peaks)[0].position[1])

          deltas += [((delta1Atoms * weight1) ** 2 + (delta2Atoms * weight2) ** 2) ** 0.5,]
  if deltas and not None in deltas:
    return round(float(np.mean(deltas)),3)
  return


  # TODO make for nDs
  # defaultWeights = {'H': 7.0, 'N': 1.0, 'C': 4.0}
  # if atomWeights is not None:
  #   atomWeights = defaultWeights.update(atomWeights)
  # else:
  #   atomWeights = defaultWeights
  # weight1, weight2 = atomWeights['H'], atomWeights['N']
  #
  # delta = 0.0
  # for dim in peak.dimensiomns:
  #   axisCode = dim.axisCode
  #   weight = atomWeights.getDefault(axisCode[0:1], 1.0)
  #   delta += ((peak.position[dim] - peak2.position[dim]) * weight ) **2
  #
  # delta = delta**0.5



































