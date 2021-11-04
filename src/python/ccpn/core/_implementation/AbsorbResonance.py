"""
Additional methods for Resonance class
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
__dateModified__ = "$dateModified: 2021-11-04 13:25:04 +0000 (Thu, November 04, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2020-07-22 08:34:27 +0000 (Wed, July 22, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

from functools import partial
from ccpn.core._implementation.MergeObjects import mergeObjects
from ccpn.core.lib.ContextManagers import undoStackBlocking
from ccpn.util.Logging import getLogger


# def _recalculateShifts(project, selfApi):
#     # Must be after resonance merge, so that links to peaks are properly set
#     for shiftA in selfApi.shifts:
#         shiftA.recalculateValue()
#         project._data2Obj[shiftA]._refreshPid()


def _recalculateChemShifts(nmrAtoms, peaks, shifts):
    # update the assigned nmrAtom chemical shift values - notify the nmrResidues and chemicalShifts
    for sh in shifts:
        sh._recalculateShiftValue()
    for nmr in nmrAtoms:
        nmr._finaliseAction('change')
    for pk in peaks:
        pk._finaliseAction('change')
    for sh in shifts:
        sh._finaliseAction('change')


def absorbResonance(self: 'NmrAtom', nmrAtom) -> 'NmrAtom':
    """
    Transfers all information from resonanceB to resonanceA and deletes resonanceB

    .. describe:: Input

    Nmr.Resonance, Nmr.Resonance

    .. describe:: Output

    Nmr.Resonance
    """

    # NBNB TBD
    # This function does NOT consider what happens to other resonances
    # that are known to be directly bound to this one from peak assignments
    # E.g. the two resonances assigned to an HSQC peak
    # Merging a single resonance may make peak assignments inconsistent.

    if nmrAtom is self:
        return self

    if nmrAtom.isDeleted or nmrAtom._flaggedForDelete:
        return self

    if self.isDeleted or self._flaggedForDelete:
        raise RuntimeError("function absorbResonance call on deleted nmrAtom: @{}".format(self.serial))

    project = self.project

    selfApi = self._wrappedData
    resonanceB = nmrAtom._wrappedData

    isotopeA = self.isotopeCode
    isotopeB = resonanceB.isotopeCode

    if isotopeA and isotopeB:
        if isotopeA != isotopeB:
            getLogger().warning('NmrAtom Merge Failure: '
                                'Attempt to merge nmrAtoms with different isotope codes')
            return

    shifts = list(set(cs for nmrAt in [self, nmrAtom] for cs in nmrAt.chemicalShifts))
    pks = list(set(pk for pk in nmrAtom.assignedPeaks))

    with undoStackBlocking() as addUndoItem:
        # recalculate shifts in undo stack
        addUndoItem(undo=partial(_recalculateChemShifts, [self, nmrAtom], pks, shifts))

    # attributes where we have object.resonance
    controlData = {'findFirstMeasurement'   : ('shiftDifferences', 'hExchRates',
                                               'hExchProtections', 'shiftAnisotropies',
                                               't1s', 't1Rhos', 't2s'),
                   'findFirstDerivedData'   : ('pkas',),
                   'findFirstPeakDimContrib': ('peakDimContribs',)
                   }

    for funcName in controlData:
        for attrName in controlData[funcName]:
            for objectA in list(selfApi.__dict__.get(attrName)):
                objectB = getattr(objectA.parent, funcName)(resonance=resonanceB)
                if objectB is not None:
                    mergeObjects(project, objectB, objectA, _useV3Delete=True)

    # attributes where we have object.resonances
    controlData = {'findFirstMeasurement'    : ('jCouplings',
                                                'noes', 'rdcs', 'dipolarRelaxations'),
                   'findFirstDerivedData'    : ('isotropicS2s', 'spectralDensities',
                                                'datums'),
                   'findFirstPeakDimContribN': ('peakDimContribNs',)
                   }

    for funcName in controlData:
        for attrName in controlData[funcName]:
            for objectA in list(selfApi.__dict__.get(attrName)):
                testKey = set(objectA.__dict__['resonances'])
                testKey.remove(selfApi)
                testKey.add(resonanceB)
                testKey = frozenset(testKey)
                objectB = getattr(objectA.parent, funcName)(resonances=testKey)

                if objectB is not None:
                    mergeObjects(project, objectB, objectA, _useV3Delete=True)

    # # Get rid of duplicate appData
    # for appData in selfApi.applicationData:
    #     matchAppData = resonanceB.findFirstApplicationData(application=appData.application,
    #                                                        keyword=appData.keyword)
    #     if matchAppData:
    #         resonanceB.removeApplicationData(matchAppData)
    #         # NOTE:ED - need undo/redo here?

    # # pre-merge the peak assignments
    # _assignNew = nmrAtom.assignedPeaks
    # for pk in _assignNew:
    #     _assigned = list(pk.dimensionNmrAtoms)
    #     # swap the nmrAto assignment in the lists
    #     _newAssigned = tuple(tuple(set(self if nmrAt == nmrAtom else nmrAt for nmrAt in _assignDim)) for _assignDim in _assigned)
    #     pk.dimensionNmrAtoms = _newAssigned

    mergeObjects(project, resonanceB, selfApi, _useV3Delete=True, )  #_mergeFunc=_mergeResonances)

    # Must be after resonance merge, so that links to peaks are properly set
    _recalculateChemShifts([self], pks, shifts)

    with undoStackBlocking() as addUndoItem:
        # recalculate shifts in undo stack
        addUndoItem(redo=partial(_recalculateChemShifts, [self], pks, shifts))

    return self
