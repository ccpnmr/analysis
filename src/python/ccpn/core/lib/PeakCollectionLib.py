"""
This module contains  clustering routines.
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-08-02 17:40:23 +0100 (Tue, August 02, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-07-12 15:39:33 +0100 (Tue, July 12, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================


from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar, notificationEchoBlocking
from ccpn.util.Logging import getLogger
from collections import defaultdict
from ccpn.util.Common import flattenLists
from ccpn.core.Peak import Peak


def _getClusteredPeaksBySpectralAssignemnt(spectra, peakListIndices=None) -> defaultdict:
    """A dict containing assignment:[peaks...]. Used to create collections from assignments"""
    assignmentsDict = defaultdict(list)
    peakListIndices = peakListIndices or [-1]*len(spectra)
    for spectrum, peakListIndex in zip(spectra, peakListIndices):
        for pk in spectrum.peakLists[peakListIndex].peaks:
            assignmentsDict[pk.assignments].append(pk)
    return assignmentsDict

def _getCollectionNameForAssignments(nmrAtoms):
    """ Get a formatted name to use as a collection name from the nmrAtoms.
    Format:
        {NmrChainName}.{nmrResidue.sequenceCode}.{nmrResidue.residueType}.{nmrAtom.names(comma-separated)}."""
    dd = defaultdict(list)
    for i in nmrAtoms:
        dd[(i.nmrResidue.nmrChain.name, i.nmrResidue.sequenceCode, i.nmrResidue.residueType)].append(i.name)
    prefix = '.'.join(flattenLists(list(dd.keys())))
    suffix = ','.join(flattenLists(list(dd.values())))
    if prefix and suffix:
        return f'{prefix}{suffix}'

def _getCollectionNameFromPeakPosition(peak):
    """ Get a formatted name to use as a collection name from the PeakPosition.
    Format:
        coll.{nmrResidue.sequenceCode}.{nmrResidue.residueType}.{nmrAtom.names(comma-separated)}."""
    position = [str(round(i, 3)) for i in peak.position]
    prefix = 'PeaksAt'
    suffix = ','.join(position)
    if prefix and suffix:
        return f'{prefix}:{suffix}'

def _getCollectionNameForPeak(peak):
    """ Get a formatted name to use as a collection name from the PeakAssignment or PeakPosition.
    """
    collectionName = _getCollectionNameForAssignments(flattenLists(peak.assignedNmrAtoms))
    if collectionName is None:
        collectionName = _getCollectionNameFromPeakPosition(peak)
    return collectionName


def renameCollectionFromAssignments(collection):
    """ Rename the collection. Useful for example to rename a collection which was created before assigning peaks. TODO"""
    pass

def renameCollectionFromPeaks(collection):
    peaks = collection.items
    if len(peaks)>0:
        peak = peaks[0]
        if isinstance(peak, Peak):
            name = _getCollectionNameFromPeakPosition(peak)
            collection.rename(name)


def createCollectionsFromSpectrumGroup(spectrumGroup, peakListIndices=None):
    collections = []
    clusteredPeaksByAssignemnt = _getClusteredPeaksBySpectralAssignemnt(spectrumGroup.spectra, peakListIndices)
    with undoBlockWithoutSideBar():
        with notificationEchoBlocking():
            project = spectrumGroup.project
            for assignments, peaks in clusteredPeaksByAssignemnt.items():
                name = _getCollectionNameForAssignments(flattenLists(assignments))
                if not name:
                    name = _getCollectionNameFromPeakPosition(peaks[0]) # alternatively get a name from ppm position
                collections.append(project.newCollection(peaks, name=name))
    return collections



