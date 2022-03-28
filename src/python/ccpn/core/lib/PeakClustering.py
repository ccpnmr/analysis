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


import abc
import numpy as np
import itertools
from typing import Tuple
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar
from ccpn.util.Logging import getLogger

class PeakClustererABC(object):
    """
    Base class for peak clustering
    """

    name = 'PeakClustererABC'
    info = 'The algorithm textual information'

    def __init__(self, peaks, tolerances, **kwargs):

        self.peaks = peaks
        self.tolerances = tolerances # list of tolerances (in points) in the same length as the spectrum.dimensionCount
        self.kwargs = kwargs
        self._checkInititialConditions()

    @abc.abstractmethod
    def findClusters(self, *args, **kwargs)  -> Tuple[Tuple['Peak', ...], ...]:
        """
        The main method to find clusters given a list of peaks.
        Implement method in subclass.
        :param args: any
        :param kwargs: any
        :return: A tuple of tuples of peaks. Each tuple represents a cluster.
        """
        pass

    def setClusterIdToPeaks(self, clusters):
        """
        :param clusters: A tuple of tuples of peaks. Each tuple is a cluster.
        :return: None. Adds the enumeration as cluster Id to the peaks
        """
        with undoBlockWithoutSideBar():
            for num, cluster in enumerate(clusters):
                for peak in cluster:
                    peak.clusterId = num + 1

    def _checkInititialConditions(self, errorPolicy='warning'):
        """
        Check if the Clustering can initiate.
        :param errorPolicy: One of warning, raise, critical
        :return: None
        """
        isOkToProceed = all([pk.spectrum.dimensionCount == len(self.tolerances) for pk in self.peaks])
        if not isOkToProceed:
            doLog = getattr(getLogger(), errorPolicy, getLogger().warning)
            doLog('Searching tolerances not set correctly. Ensure all peaks are of same dimensionality '
                                'and the tolerances list is the same length as the spectrum.dimensionCount')

    def _getOverlapPairsByPositions(self):
        """
        Consider two peaks adjacent if the PointPositions are within the tolerances.
        :param peaks:
        :param tolerances: list of tolerances (in points). Same length of spectrum.dimensionCount
        :return: A list of adjacent pairs of peaks
        """
        overlaps = []
        lims = np.array(self.tolerances)
        for pair in itertools.combinations(self.peaks, 2):
            dd = np.abs(np.array(pair[0].pointPositions) - np.array(pair[1].pointPositions))
            if all(dd < lims):
                overlaps.append(pair)
        return overlaps

class DFSPeakClusterer(PeakClustererABC):

    name = 'DFSPeakClusterer '
    info = 'Depth-first search (DFS) algorithm for peak clustering by pointPositions'

    def findClusters(self, *args, **kwargs):
        overlappedPeaks = self._getOverlapPairsByPositions()
        positions = [pk.pointPositions for pk in self.peaks]
        overlappedPositions = [(pair[0].pointPositions, pair[1].pointPositions) for pair in overlappedPeaks]
        result = DFSPeakClusterer._getClusterOverlaps(positions, overlappedPositions)
        clusteredPeaks = []
        for i, group in enumerate(result):
            peakCluster = []
            for peak in self.peaks:
                for j in group:
                    if j == peak.pointPositions:
                        peakCluster.append(peak)
            clusteredPeaks.append(tuple(peakCluster))
        return tuple(clusteredPeaks)

    @staticmethod
    def _getClusterOverlaps(nodes, adjacents):
        """
        Ref: https://stackoverflow.com/questions/14607317/
        """
        clusters = []
        nodes = list(nodes)
        while len(nodes):
            node = nodes[0]
            path = DFSPeakClusterer._getPathByDFS(node, adjacents, nodes)
            clusters.append(path)
            for pt in path:
                nodes.remove(pt)
        return clusters

    @staticmethod
    def _getPathByDFS(start, adjacents, nodes):
        """
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



