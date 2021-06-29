"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-06-29 14:27:30 +0100 (Tue, June 29, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.isotopes import name2IsotopeCode


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
        return

    if not peak and not nmrResidue:
        return

    if peak:
        positionCodeDict = {peak.peakList.axisCodes[ii]: peak.position[ii] for ii in len(peak.position)}

    if nmrResidue:
        nmrResidueIsotopeCodes = [atom.isotopeCode for atom in nmrResidue.nmrAtoms]
        shiftList = spectrum.chemicalShiftList
        nmrResidueShifts = [shiftList.getChemicalShift(nmrAtom.id).value
                            for nmrAtom in nmrResidue.nmrAtoms
                            if shiftList.getChemicalShift(nmrAtom.id)]
        shiftDict = dict(zip(nmrResidueIsotopeCodes, nmrResidueShifts))
        shiftIsotopeCodes = [name2IsotopeCode(code) for code in axisCodes]
        positionCodeDict = {axisCodes[ii]: shiftDict[shiftIsotopeCode]
                            for ii, shiftIsotopeCode in enumerate(shiftIsotopeCodes) if shiftIsotopeCode in shiftDict}

        # sometimes get an error when using spectrum projections - but modification for the future
        # if ii in axisCodes and shiftIsotopeCode in shiftDict}

    peaks = peakList.restrictedPick(positionCodeDict, doPos, doNeg)

    return peakList, peaks
