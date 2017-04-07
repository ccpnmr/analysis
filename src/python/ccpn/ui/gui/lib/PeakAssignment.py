"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================

__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:41:03 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"

__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import typing
from ccpn.util import Common as commonUtil
from ccpn.core.ChemicalShiftList import ChemicalShiftList
from ccpn.core.NmrAtom import NmrAtom
from ccpn.core.Peak import Peak


def nmrAtomsForPeaks(peaks:typing.List[Peak], nmrAtoms:typing.List[NmrAtom], intraResidual:bool=False, doubleTolerance:bool=False):
    '''Get a set of nmrAtoms that fit to the dimensions of the
       peaks.

    '''

    selected = matchingNmrAtomsForPeaks(peaks, nmrAtoms, doubleTolerance=doubleTolerance)
    if intraResidual:
        selected = filterIntraResidual(selected)
    return selected


def filterIntraResidual(nmrAtomsForDimensions:typing.List[NmrAtom]):
    '''Takes a N-list of lists of nmrAtoms, where N
       is the number of peak dimensions and only returns
       those which belong to residues that show up in
       at least to of the dimensions (This is the behaviour
       in v2, if I am correct).

    '''

    nmrResiduesForDimensions = []
    allNmrResidues = set()
    for nmrAtoms in nmrAtomsForDimensions:
        nmrResidues = set([nmrAtom.nmrResidue for nmrAtom in nmrAtoms if nmrAtom.nmrResidue])
        nmrResiduesForDimensions.append(nmrResidues)
        allNmrResidues.update(nmrResidues)

    selectedNmrResidues = set()
    for nmrResidue in allNmrResidues:
        frequency = 0
        for nmrResidues in nmrResiduesForDimensions:
            if nmrResidue in nmrResidues:
                frequency += 1
        if frequency > 1:
            selectedNmrResidues.add(nmrResidue)

    nmrAtomsForDimenionsFiltered = []
    for nmrAtoms in nmrAtomsForDimensions:
        nmrAtoms_filtered = set()
        for nmrAtom in nmrAtoms:
            if nmrAtom.nmrResidue in selectedNmrResidues:
                nmrAtoms_filtered.add(nmrAtom)
        nmrAtomsForDimenionsFiltered.append(nmrAtoms_filtered)

    return nmrAtomsForDimenionsFiltered


def matchingNmrAtomsForPeaks(peaks:typing.List[Peak], nmrAtoms:typing.List[NmrAtom], doubleTolerance:bool=False):
    '''Get a set of nmrAtoms that fit to the dimensions of the
       peaks. This function does the actual calculation and does
       not involve filtering like in nmrAtoms_for_peaks, where
       more filters can be specified in the future.

    '''

    dimensionCount = [len(peak.position) for peak in peaks]
    #All peaks should have the same number of dimensions.
    if not len(set(dimensionCount)) == 1:
        return []
    N_dims = dimensionCount[0]
    dim_nmrAtoms = []

    for dim in range(N_dims):
        matching = matchingNmrAtomsForDimensionOfPeaks(peaks,
                                                            dim,
                                                            nmrAtoms,
                                                            doubleTolerance=doubleTolerance)
        dim_nmrAtoms.append(matching)
    return dim_nmrAtoms


def matchingNmrAtomsForDimensionOfPeaks(peaks:typing.List[Peak], dim:int, nmrAtoms:typing.List[NmrAtom],
                                             doubleTolerance:bool=False):
    '''Finds out which nmrAtom can be assigned to a specific
       dimension of all the peaks, the N dimension for instance.
       Only returns those nmrAtoms that can be assigned to this
       dimension of all the selected peaks.

    '''

    if not sameAxisCodes(peaks, dim):
        return set()
    fittingSets = []
    for peak in peaks:
        matchingNmrAtoms = matchingNmrAtomsForPeakDimension(peak, dim,
                                                            nmrAtoms,
                                                            doubleTolerance=doubleTolerance)
        # '&=' is set intersection update
        common = intersectionOfAll(fittingSets)
    return matchingNmrAtoms


def matchingNmrAtomsForPeakDimension(peak:Peak, dim:int, nmrAtoms:typing.List[NmrAtom],
                                         doubleTolerance:bool=False):
    '''Just finds the nmrAtoms that fit a dimension of one peak.

    '''

    fitting_nmrAtoms = set()
    # shiftList = getShiftlistForPeak(peak)
    shiftList = peak.peakList.chemicalShiftList
    position = peak.position[dim]
    # isotopeCode = getIsotopeCodeForPeakDimension(peak, dim)
    isotopeCode = peak.peakList.spectrum.isotopeCodes[dim]
    tolerance = peak.peakList.spectrum.assignmentTolerances[dim]
    if not position or not isotopeCode or not shiftList:
        return fitting_nmrAtoms
    if not tolerance:
        tolerance = 0.05
    if doubleTolerance:
        tolerance *= 2

    for nmrAtom in nmrAtoms:
        if nmrAtom.isotopeCode == isotopeCode and withinTolerance(nmrAtom, position,
                                                                  shiftList, tolerance):
          fitting_nmrAtoms.add(nmrAtom)

    return fitting_nmrAtoms


def withinTolerance(nmrAtom:NmrAtom, position:float, shiftList:ChemicalShiftList, tolerance:float):
    '''Decides whether the shift of the nmrAtom is
       within the tolerance to be assigned to the
       peak dimension.

    '''
    shift = shiftList.getChemicalShift(nmrAtom.id)
    #delta = delta_shift(nmrAtom, position, shiftList)
    if shift and abs(position - shift.value) < tolerance:
        return True
    return False


#def delta_shift(nmrAtom, position, shiftList):

#    shift = shiftList.getChemicalShift(nmrAtom.id)
#    if shift:
#        return position - shift.value
#    return None


def peaksAreOnLine(peaks:typing.List[Peak], dim:int):
    '''Returns True when multiple peaks are located
       on a line in the given dimensions.
    '''

    if not sameAxisCodes(peaks, dim):
        return False
    # Take the two furthest peaks (in this dimension) of the selection.
    positions = sorted([peak.position[dim] for peak in peaks])
    max_difference = abs(positions[0] - positions[-1])
    #Use the smallest tolerance of all peaks.
    tolerance = min([getAssignmentToleranceForPeakDimension(peak, dim) for peak in peaks])
    if max_difference < tolerance:
        return True
    return False


def sameAxisCodes(peaks:typing.List[Peak], dim:int):
    '''Checks whether all peaks have the same axisCode
       for in the given dimension.

    '''

    if len(peaks) > 1:
        # axisCode = getAxisCodeForPeakDimension(peaks[0], dim)
        axisCode = peaks[0].peakList.spectrum.axisCodes[dim]
        for peak in peaks[1:]:
            if not commonUtil.axisCodesCompare(peak.peakList.spectrum.axisCodes[dim], axisCode):
                return False
    return True


# Here come some functions that should probably live somewhere else.
# They all involve api lookups that would otherwise make the
# code less readable.

# REplaced by project.nmrAtoms.
# For isotope filtering, filter the result on nmrAtom.isotopeCode.
# def getAllNmrAtoms(project, isotope=None):
#     nmrAtoms = [nmrAtom for nmrResidue in project.nmrResidues for nmrAtom in nmrResidue.nmrAtoms]
#     if isotope:
#         selected = [a for a in nmrAtoms if a.isotope == isotope]
#         nmrAtoms = selected
#     return nmrAtoms

# replaced by inline code
# def getIsotopeCodeForPeakDimension(peak, dim):
#     return peak.peakList.spectrum.isotopeCodes[dim]


def getAssignmentToleranceForPeakDimension(peak:Peak, dim:int):
    spectrum = peak.peakList.spectrum
    if spectrum.assignmentTolerances[dim] is not None:
      return spectrum.assignmentTolerances[dim]
    else:
      assignmentTolerances = list(spectrum.assignmentTolerances)
      assignmentTolerances[dim] = 0.01
      spectrum.assignmentTolerances = assignmentTolerances
      return spectrum.assignmentTolerances[dim]

# Replaced by nmrAtom.isotopeCode
# def getIsotopeCode(nmrAtom):
#     return nmrAtom._apiResonance.isotopeCode


# replaced by inline code
# def getAxisCodeForPeakDimension(peak, dim):
#     return peak.peakList.spectrum.axisCodes[dim]


# replaced by inline code
# def getShiftlistForPeak(peak):
#     return peak.peakList.spectrum.chemicalShiftList

# Just Math

# Replaced by set.intersection(*sets)
def intersectionOfAll(sets):

    if not sets:
        return set()
    if len(sets) == 1:
        return sets[0]
    intersection = sets[0]
    for s in sets[1:]:
        intersection = intersection.intersection(s)
    return intersection
