"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:32 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2016-09-07 12:42:52 +0100 (Wed, 07 Sep 2016) $"
#=========================================================================================
# Start of code
#=========================================================================================

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
                    # Atom not in equivalent group
                    count += 1
    #
    return count


def assignedAtomCount(chain):
    # Will soon be just 'xy', but meanwhile
    xyWildcards = 'XYxy'

    count = 0

    if chain:
        nmrChain = chain.nmrChain
        if nmrChain:
            for nmrAtom in nmrChain.nmrAtoms:
                atom = nmrAtom.atom
                if atom:

                    componentAtoms = atom.componentAtoms
                    if componentAtoms and any(x in xyWildcards for x in nmrAtom.name):
                        # XY wildcard = count as one of the constituent atoms
                        atom = componentAtoms[0]
                    componentCount = len(atom.componentAtoms)

                    if componentCount < 2:
                        # Single atom
                        count += 1

                    elif atom.isEquivalentAtomGroup:
                        #  equivalent atoms, CH3 or aromatic ring
                        count += 1

                    else:
                        # Wilcard atom, e.g. Ser HB% or Val HG% (with two components)
                        count += componentCount

    #
    return count


def assignedAtomPercentage(chain):
    return _percentage(assignedAtomCount(chain), assignableAtomCount(chain))
