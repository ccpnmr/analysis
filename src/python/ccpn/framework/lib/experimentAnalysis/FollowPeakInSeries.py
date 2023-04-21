"""
This module defines base classes for Series Analysis
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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2023-04-21 16:41:02 +0100 (Fri, April 21, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-08-01 14:51:53 +0100 (Mon, August 01, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
import abc
from ccpn.core.PeakList import PeakList
from ccpn.util.Logging import getLogger
from collections import defaultdict
from ccpn.core.lib.PeakCollectionLib import _getCollectionNameForPeak, _makeCollectionsOfPeaks


class FollowPeakAbc(abc.ABC):

    name = 'FollowPeak Abc'
    info = 'Abc class'

    def __init__(self, sourcePeakList, targetPeakLists,  cloneAssignment=False,
                  **kwargs):

        self.sourcePeakList = sourcePeakList
        self.targetPeakLists = targetPeakLists
        self.cloneAssignment = cloneAssignment
        self.project = self.sourcePeakList.project

    def matchPeaks(self):
        """ """
        collectionPeaks = defaultdict(set)  ## set to avoid duplicates

        for peak in self.sourcePeakList.peaks:
            collectedPeaks = set()
            matchedPeaks = self.getCollectionPeaks(peak,  self.targetPeakLists)
            if len(matchedPeaks) == 0:
                continue
            for matchedPeak in matchedPeaks:
                collectedPeaks.add(matchedPeak)
                if self.cloneAssignment:
                    try:
                        peak.copyAssignmentTo(matchedPeak)
                    except Exception as e:
                        getLogger().warning(f'Failed to copy assignments for peak {peak}. Skipping with error: {e}')
                collectionName = _getCollectionNameForPeak(matchedPeak)
                collectionPeaks[collectionName] = collectedPeaks

        return collectionPeaks


    def getMatchedIndex(self, originPosition, targets) -> int:
        '''
        :param originPosition:  1D array. e.g.: the peak position as an array
        :param targets: array of  available positions excluding the originPosition.
        :return: int.  the index of the matched item in targets.
        '''
        raise RuntimeError('Method to be implemented in subclass')

    def getMatchedPeak(self, originPeak, targetPeaks):
        '''
        :param originPeak: peak object
        :param targetPeaks: peaks to be matched to originPeak
        :return: the matched peak object from the targetPeaks list
        '''
        if len(targetPeaks)==0:
            getLogger().warning(f'Cannot match {originPeak} to targetPeaks. None provided!')
            return
        targetPeaks = np.array(targetPeaks)
        targetPeak = targetPeaks[0]
        destinationAxisCodes = targetPeak.spectrum.axisCodes
        dimensionMapping = originPeak.spectrum.getByAxisCodes('dimensions', destinationAxisCodes, exactMatch=False)
        originPosition = originPeak.getByDimensions('position', dimensionMapping)
        originPosition = np.array(originPosition)
        targets = np.array([pk.position for pk in targetPeaks])
        ix = self.getMatchedIndex(originPosition, targets)
        return targetPeaks[ix]

    def getCollectionPeaks(self, originPeak, targetPeakLists:list):
        '''
        :param originPeak: iterable, (1D array, list, tuple) containing items to be matched to the targets
        :param targetPeakLists:  list of PeakLists.
        :return: a list of matchedPeaks
        Given a list of peakList (the PeakList object containing peaks) find the best match from each of the list.
        Used to create collections. Subclass for following peak in Perturbation Analysis.
        '''
        matched = []
        for peakList in targetPeakLists:
            if isinstance(peakList, PeakList) and len(peakList.peaks)>0:
                matched.append(self.getMatchedPeak(originPeak, peakList.peaks))
        return matched

class FollowByMinimalShiftMapping(FollowPeakAbc):

    name = 'Minimal Distance'
    info = 'Use the Minimal Distance  among items to create clusters'


    def matchPeaks(self):
        """
        Compute the (Euclidian) distance between each pair of the two collections of peak inputs.
        """

        from scipy.spatial.distance import cdist
        from scipy.optimize import linear_sum_assignment

        collectionPeaks = defaultdict(set)
        # Loop over the targetPeakLists and compare to the originPeaks and not to previous List in the targetPeakList.
        # This might spot peaks in slow exchange (e.g.: "disappear" at a middle of the titration and "reappear" at the end.)
        for targetPeakList in self.targetPeakLists:
            targetPeaks = targetPeakList.peaks
            targetPeaks = np.array(targetPeaks)
            targetPeakPos = [pk.position for pk in targetPeaks]
            targetPeakPos = np.array(targetPeakPos)
            originPeaks = self.sourcePeakList.peaks
            originPeaks = np.array(originPeaks)
            originPeakPos = [pk.position for pk in originPeaks]
            originPeakPos = np.array(originPeakPos)
            if len(targetPeaks) == 0:
                continue
            if len(originPeaks) == 0:
                break
            ## Compute distance between each pair of the two PeakLists
            distanceMatrix = cdist(originPeakPos, targetPeakPos, metric='seuclidean',)
            originIndexes, targetIndexes = linear_sum_assignment(distanceMatrix)
            originPeaks = originPeaks[originIndexes]
            targetPeaks = targetPeaks[targetIndexes]
            # make the collection set
            for o, t in list(zip(originPeaks, targetPeaks)):
                collectionName = _getCollectionNameForPeak(o)
                collectionPeaks[collectionName].add(t)
                collectionPeaks[collectionName].add(o)
                if self.cloneAssignment:
                    try:
                        o.copyAssignmentTo(t)
                    except Exception as e:
                        getLogger().warning(f'Failed to copy assignments for peak {o}. Skipping with error: {e}')
        return collectionPeaks


class FollowSameAssignmentPeak(FollowPeakAbc):

    name = 'Same Assignment'
    info = 'Find peaks assigned to the same NmrAtoms'

    def getMatchedIndex(self, originPosition, targets) -> int:
        raise RuntimeError('Not in use for this Subclass')

    def getMatchedPeak(self, originPeak, targetPeaks):
        matched  = []
        for peak in targetPeaks:
            if peak.assignedNmrAtoms == originPeak.assignedNmrAtoms:
                matched.append(peak)
        return matched

    def getCollectionPeaks(self, originPeak, targetPeakLists:list):
        '''
        :param originPeak: iterable, (1D array, list, tuple) containing items to be matched to the targets
        :param targetPeakLists:  list of PeakLists.
        :return: a list of matchedPeaks
        '''

        matched = []
        for peakList in targetPeakLists:
            if isinstance(peakList, PeakList) and len(peakList.peaks)>0:
                sameAssignmentPeaks = self.getMatchedPeak(originPeak, peakList.peaks)
                if len(sameAssignmentPeaks)>0:
                    matched.append(sameAssignmentPeaks[0])
        return matched



AVAILABLEFOLLOWPEAKS = {
                    FollowSameAssignmentPeak.name: FollowSameAssignmentPeak,
                    FollowByMinimalShiftMapping.name: FollowByMinimalShiftMapping
                    }
