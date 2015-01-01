"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

from collections.abc import Sequence

def setPeakDimAssignments(peak, value:Sequence):
  """Set per-dimension assignments on peak.
  value is a list of lists (one per dimension) of resonances.
  NB only works for single-PeakContrib, one-ref-per-dimension assignments
  NB resets PeakContribs
  """
  numDim =  peak.peakList.dataSource.numDim
  if len(value) != numDim:
    raise ValueError("Assignment length does not match number fo peak dimensions %s: %s"
                      % (numDim, value))

  for ii, val in enumerate(value):
    if len(set(val)) != len(val):
      raise ValueError("Assignments contain duplicates in dimension %s: %s" % (ii+1, val))

  peakContribs = peak.sortedPeakContribs
  if peakContribs:
    # Clear existing assignmetns, keeping first peakContrib
    peakContrib = peakContribs[0]
    for xx in peakContribs[1:]:
      xx.delete()
    for peakDim in peak.peakDims:
      for peakDimContrib in peakDim.peakDimContribs:
        peakDimContrib.delete()

  else:
    # No assignments. Make peakContrib
    peakContrib = peak.newPeakContrib()

  peakDims = peak.sortedPeakDims()
  for ii,val in enumerate(value):
    peakDim = peakDims[ii]
    for resonance in val:
      peakDim.newPeakDimContrib(resonance=resonance, peakContrib=peakContrib)


def setAssignments(peak, value:Sequence):
  """Set assignments on peak.
  value is a list of lists (one per combination) of resonances.
  NB only works for single-resonance, one-ref-per-dimension assignments
  NB sets one PeakContrib per combination
  """

  peakDims = peak.sortedPeakDims()
  dimensionCount = len(peakDims)
  dimResonances = []
  for ii in range(dimensionCount):
    dimResonances.append([])

  # get per-dimension resonances
  for tt in value:
    for ii,resonance in enumerate(tt):
      if resonance not in dimResonances[ii]:
        dimResonances[ii].append(resonance)

  # reassign dimension resonances
  setPeakDimAssignments(peak, dimResonances)

  # Get first PeakContrib before we add new ones
  firstPeakContrib = peak.findFirstPeakContrib()

  if value:
    # set PeakContribs, one per assignment tuple, skipping the first one
    for tt in value[1:]:
      ll = [peakDim.findFirstPeakDimContrib(resonance=tt[ii])
            for ii,peakDim in enumerate(peakDims)]
      peak.newPeakContrib(peakDimContribs=ll)

    # reset PeakDimContribs for first PeakContrib
    ll = [peakDim.findFirstPeakDimContrib(resonance=value[0][ii])
          for ii,peakDim in enumerate(peakDims)]
    firstPeakContrib.peakDimContribs = ll