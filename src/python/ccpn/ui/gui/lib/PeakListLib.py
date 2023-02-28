"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2023-02-28 13:03:57 +0000 (Tue, February 28, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.isotopes import name2IsotopeCode
from collections import defaultdict
from itertools import product
from ccpn.util.Logging import getLogger


def restrictedPick(peakListView, axisCodes, peak=None, nmrResidue=None):
    """
    Takes a Peak or an NmrResidue, not both, a set of axisCodes, and a PeakListView.
    Derives positions for picking and feeds them into a PeakList wrapper function that
    performs the picking.
    """

    spectrum = peakListView.spectrumView.spectrum
    peakList = spectrum.peakLists[0]
    doPos = peakListView.spectrumView.displayPositiveContours
    doNeg = peakListView.spectrumView.displayNegativeContours

    if peak and nmrResidue:
        # cannot do both at the same time
        return

    if not peak and not nmrResidue:
        # nothing selected
        return

    if peak:
        if (positionCodeDict := {peak.peakList.axisCodes[ii]: peak.position[ii] for ii in range(len(peak.position))}):
            peaks = peakList.restrictedPick(positionCodeDict, doPos, doNeg)
            return peakList, peaks

    allPeaks = []
    if nmrResidue:
        # make sure it is the main-nmrResidue with all the nmrAtoms
        nmrResidue = nmrResidue.mainNmrResidue

        allShifts = defaultdict(list, {})
        shiftList = spectrum.chemicalShiftList

        _mapping = [(atm.isotopeCode, shiftList.getChemicalShift(atm).value) for atm in nmrResidue.nmrAtoms if shiftList.getChemicalShift(atm)]
        for isoCode, shift in _mapping:
            allShifts[isoCode].append(shift)

        # shiftIsotopeCodes = [name2IsotopeCode(code) for code in axisCodes]
        shiftIsotopeCodes = list(map(name2IsotopeCode, axisCodes))

        # make all combinations of position dicts for the shift found for each shift
        _combis = [{axisCodes[shiftIsotopeCodes.index(iso)]: sh for ii, (iso, sh) in enumerate(zip(allShifts.keys(), val)) if iso in shiftIsotopeCodes}
                   for val in product(*allShifts.values())]

        for _posCodeDict in _combis:
            if not _posCodeDict:
                raise ValueError(f'There are no restricted axes associated with {spectrum.id}')

            peaks = peakList.restrictedPick(_posCodeDict, doPos, doNeg)
            allPeaks += peaks

    return peakList, allPeaks
