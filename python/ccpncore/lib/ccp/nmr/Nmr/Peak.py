"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
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

from ccpncore.util.typing import Sequence

def assignByDimensions(self:'Peak', value:Sequence):
  """Set per-dimension assignments on peak.
  value is a list of lists (one per dimension) of resonances.
  NB only works for single-PeakContrib, one-ref-per-dimension assignments
  NB resets PeakContribs
  """
  numDim =  self.peakList.dataSource.numDim
  if len(value) != numDim:
    raise ValueError("Assignment length does not match number of peak dimensions %s: %s"
                      % (numDim, value))

  for ii, val in enumerate(value):
    if len(set(val)) != len(val):
      raise ValueError("Assignments contain duplicates in dimension %s: %s" % (ii+1, val))

  peakContribs = self.sortedPeakContribs()
  if peakContribs:
    # Clear existing assignments, keeping first peakContrib
    peakContrib = peakContribs[0]
    for xx in peakContribs[1:]:
      xx.delete()
    for peakDim in self.peakDims:
      for peakDimContrib in peakDim.peakDimContribs:
        peakDimContrib.delete()

  else:
    # No assignments. Make peakContrib
    peakContrib = self.newPeakContrib()

  peakDims = self.sortedPeakDims()
  for ii,val in enumerate(value):
    peakDim = peakDims[ii]
    for resonance in val:
      peakDim.newPeakDimContrib(resonance=resonance, peakContribs=(peakContrib,))


def assignByContrbutions(self:'Peak', value:Sequence):
  """Set assignments on peak.
  value is a list of lists (one per combination) of resonances.
  NB only works for single-resonance, one-ref-per-dimension assignments
  NB sets one PeakContrib per combination
  """

  peakDims = self.sortedPeakDims()
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
  assignByDimensions(self, dimResonances)

  # Get first PeakContrib before we add new ones
  firstPeakContrib = self.findFirstPeakContrib()

  if value:
    # set PeakContribs, one per assignment tuple, skipping the first one
    for tt in value[1:]:
      ll = [peakDim.findFirstPeakDimContrib(resonance=tt[ii])
            for ii,peakDim in enumerate(peakDims)]
      self.newPeakContrib(peakDimContribs=ll)

    # reset PeakDimContribs for first PeakContrib
    ll = [peakDim.findFirstPeakDimContrib(resonance=value[0][ii])
          for ii,peakDim in enumerate(peakDims)]
    firstPeakContrib.peakDimContribs = ll