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
__dateModified__ = "$dateModified: 2022-07-13 11:03:43 +0100 (Wed, July 13, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-07-12 15:39:33 +0100 (Tue, July 12, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================


import abc
import numpy as np
import itertools
from typing import Tuple
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar, notificationEchoBlocking
from ccpn.util.Logging import getLogger
from collections import OrderedDict as od
from collections import defaultdict
from ccpn.util.Common import flattenLists



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
    return f'{prefix}.{suffix}'

def createCollectionsFromSpectralAssignemnts(spectrumGroup, peakListIndices=None):
    collections = []
    clusteredPeaksByAssignemnt = _getClusteredPeaksBySpectralAssignemnt(spectrumGroup.spectra, peakListIndices)
    with undoBlockWithoutSideBar():
        with notificationEchoBlocking():
            project = spectrumGroup.project
            for assignments, peaks in clusteredPeaksByAssignemnt.items():
                name = _getCollectionNameForAssignments(flattenLists(assignments))
                collections.append(project.newCollection(peaks, name=name))
            parentCollectionName = f'{spectrumGroup.name}_AssignmentsCollection'
            parentCollection = project.newCollection(collections, name=parentCollectionName)
    return parentCollection



