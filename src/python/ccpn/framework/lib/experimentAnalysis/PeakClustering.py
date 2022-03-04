"""
This module contains simple clustering functions.
If needed, it might evolve in ABC classes for accommodate different algorithms.
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
__dateModified__ = "$dateModified: 2022-03-04 18:50:46 +0000 (Fri, March 04, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-02-02 14:08:56 +0000 (Wed, February 02, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
import itertools
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar
from ccpn.util.Logging import getLogger

############################## Guess peak clusters    #################################

def _getClusterOverlaps(nodes, adjacents):
    """
    Ref: https://stackoverflow.com/questions/14607317/
    """
    clusters = []
    nodes = list(nodes)
    while len(nodes):
        node = nodes[0]
        path = _getPathByDFS(node, adjacents, nodes)
        clusters.append(path)
        for pt in path:
            nodes.remove(pt)
    return clusters

def _getPathByDFS(start, adjacents, nodes):
    """
    Depth-first search (DFS)
    Ref: https://stackoverflow.com/questions/14607317/"""
    path = []
    q = [start]
    while q:
        node = q.pop(0)
        if path.count(node) >= nodes.count(node):
            continue
        path = path + [node]
        nextNodes = [p2 for p1,p2 in adjacents if p1 == node]
        q = nextNodes + q
    return path

def _getOverlapPairsByPositions(peaks, tolerances):
    """
    Consider two peaks adjacent if the PointPositions are within the tolerances.
    :param peaks:
    :param tolerances: list of tolerances (in points). Same length of spectrum.dimensionCount
    :return: A list of adjacent pairs of peaks
    """
    overlaps = []
    lims = np.array(tolerances)
    for pair in itertools.combinations(peaks, 2):
        dd = np.abs(np.array(pair[0].pointPositions) - np.array(pair[1].pointPositions))
        if all(dd < lims):
            overlaps.append(pair)
    return overlaps

def setClusterIDs(peaks, tolerances):
    """
    An approach to calculate clusterIDs for a group of peaks using the in Depth-First-Search (DFS) algorithm.
    :param peaks: list of peaks.
    :param tolerances: tolerances per dimension in points. higher values will include more peaks in a cluster.
                        Must be the same length of spectrum.dimensionCount
    :return: list of list (of clusteredPeaks)
    """
    isOkToProceed = all([pk.spectrum.dimensionCount==len(tolerances) for pk in peaks])
    if not isOkToProceed:
        getLogger().warning('Searching tollerances not set correctly. Ensure all peaks are of same dimensionality '
                            'and the tolerances list is the same length as the spectrum.dimensionCount')
    overlappedPeaks = _getOverlapPairsByPositions(peaks, tolerances)
    positions = [pk.pointPositions for pk in peaks]
    overlappedPositions = [(pair[0].pointPositions, pair[1].pointPositions) for pair in overlappedPeaks]
    result = _getClusterOverlaps(positions, overlappedPositions)
    clusteredPeaks = []
    with undoBlockWithoutSideBar():
        for i, group in enumerate(result):
            peakCluster = []
            for peak in peaks:
                for j in group:
                    if j == peak.pointPositions:
                        peakCluster.append(peak)
                        peak.clusterId = i+1
            clusteredPeaks.append(peakCluster)
    return clusteredPeaks
