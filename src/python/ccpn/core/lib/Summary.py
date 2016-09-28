"""Module Documentation here

"""
# =========================================================================================
# Licence, Reference and Credits
# =========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2016-09-07 12:42:52 +0100 (Wed, 07 Sep 2016) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

# =========================================================================================
# Last code modification:
# =========================================================================================
__author__ = "$Author: skinnersp $"
__date__ = "$Date: 2016-09-07 12:42:52 +0100 (Wed, 07 Sep 2016) $"
__version__ = "$Revision: 9852 $"


# =========================================================================================
# Start of code
# =========================================================================================

def _percentage(count, totalCount, decimalPlaceCount=0):

  if totalCount:
    return int(round((100.0 * count) / totalCount, decimalPlaceCount))
  else:
    return 0

# PEAKLISTS

def partlyAssignedPeakCount(peakList):

  return len([peak for peak in peakList.peaks if peak.isPartlyAssigned()])

def partlyAssignedPeakPercentage(peakList):

  return _percentage(partlyAssignedPeakCount(peakList), len(peakList.peaks))

def fullyAssignedPeakCount(peakList):

  return len([peak for peak in peakList.peaks if peak.isFullyAssigned()])

def fullyAssignedPeakPercentage(peakList):

  return _percentage(fullyAssignedPeakCount(peakList), len(peakList.peaks))

# CHAINS

def assignableAtomCount(chain):
  """Counts atoms that are not marked as exchanging with water
  Compound atoms (e.g. MB, QGB, HB%, HBx or HBy) are not counted
  For groups of equivalent atoms only the atom name ending in '1' is counted
  Sometimes-equivalent atom groups (rotating aromatic rings) count as equivalent
  """

  # return len([atom for atom in chain.atoms if atom._isAssignable()])
  count = 0
  if chain:
    for atom in chain.atoms:
      if not atom.componentAtoms and not atom.exchangesWithWater:
        # Skip compound atoms, look only at simple ones
        if any(x.isEquivalentAtomGroup for x in atom.compoundAtoms):
          # Atom is part of an equivalent group
          if atom.name.endswith('1'):
            # Only take the equivalent atom if it sends with 1
            count += 1
        else:
          # Tom not in equivalent group
          count += 1
  #
  return count




def assignedAtomCount(chain):

  # NB this is not quite precise
  # You could get miscounting if you have both stereo, non-stereo, and wildcard/pseudo
  # NmrAtoms for the same atoms, and you could in theory get miscounts for nested
  # pairs (like guanidinium C-(NH2)2
  # Also e.g. Tyr/Phe HD% is counted as one resonance, whereas it is counted as
  # two assignable atoms.
  # But I leave the details to someone else - this should be decent.
  #
  # count = 0
  #
  # nmrChain = chain.nmrChain
  # if nmrChain is not None:
  #   for nmrAtom in nmrChain.nmrAtoms:
  #     atom = nmrAtom.atom
  #     if atom is not None:
  #       count += atom._assignedCount()
  #
  # return count
  # Will soon be just 'xy', but meanwhile
  xyWildcards = 'XYxy'

  count = 0

  if chain:
    nmrChain = chain.nmrChain
    if nmrChain:
      for nmrAtom in nmrChain.nmrAtoms:
        atom = nmrAtom.atom
        if atom:

          if len(atom.componentAtoms) < 2:
            # Single atom
            count += 1

          elif atom.isEquivalentAtomGroup:
            #  equivalent atoms, CH3 or aromatic ring
            count += 1

          elif any(x in xyWildcards for x in nmrAtom.name):
            # xy wildcard atom, including isopropyl groups
            count += 1

  #
  return count

def assignedAtomPercentage(chain):

  return _percentage(assignedAtomCount(chain), assignableAtomCount(chain))


