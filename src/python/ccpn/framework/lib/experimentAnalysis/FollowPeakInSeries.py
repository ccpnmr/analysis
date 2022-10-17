"""
This module defines base classes for Series Analysis
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
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-10-17 10:49:55 +0100 (Mon, October 17, 2022) $"
__version__ = "$Revision: 3.1.0 $"
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


class FollowPeakAbc(abc.ABC):

    name = 'FollowPeak Abc'
    info = 'Abc class'

    @abc.abstractmethod
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

class FollowNearestPeak(FollowPeakAbc):

    name = 'Nearest Match'
    info = 'Find the nearest peak by ppm position'

    def getMatchedIndex(self, originPosition, targets, **kwargs) -> int:
        '''
        :param originPosition:  1D array. e.g.: the peak position as an array
        :param targets: array of  available positions excluding the originPosition.
        :param kwargs: any required for the algorithm, Ideally none or predefined.
        :return: int.  the index of the matched item in targets.
        originPosition = np.array([8.4918091  124.83767383])
        targets = array([  [  8.15360558, 119.62046656],
                           [  8.46365954, 120.46016675],
                           [  8.34154712, 121.38129515],
                           ...
                        ])
        expected index -> 2
        '''
        idx = np.array([np.linalg.norm(x + y) for (x, y) in targets - originPosition]).argmin()
        return idx


class _FollowByMinimalShiftMapping(FollowPeakAbc):
    """
    INTERNAL. under development
    """
    name = 'MinimalShiftMapping'
    info = 'Use the Minimal Shift Mapping to create clusters'


    def findMatches(self, originPeaks, targetPeaks):
        """
        INTERNAL. under development """
        getLogger().warn('Under development. Do not use yet.')
        from scipy.spatial.distance import cdist
        from scipy.optimize import linear_sum_assignment
        originPeaks = np.array(originPeaks)
        targetPeaks = np.array(targetPeaks)
        originPeakPos = [pk.position for pk in originPeaks]
        targetPeakPos = [pk.position for pk in targetPeaks]
        originPeakPos = np.array(originPeakPos)
        targetPeakPos = np.array(targetPeakPos)
        Vs= {'1H':1, '13C':0.25, '15N':0.142} # alpha factors
        ## Compute distance between each pair of the two PeakLists
        distanceMatrix = cdist(originPeakPos, targetPeakPos, metric='seuclidean', V=[0.142,1])
        originIndexes, targetIndexes = linear_sum_assignment(distanceMatrix)
        originPeaks = originPeaks[originIndexes]
        targetPeaks = targetPeaks[targetIndexes]
        return list(zip(originPeaks, targetPeaks))

class FollowSameAssignmentPeak(FollowPeakAbc):

    name = 'Same assignment'
    info = 'Find peaks assigned to the same NmrAtoms'

    def getMatchedIndex(self, originPosition, targets) -> int:
        raise RuntimeError('NYI')

    def getMatchedPeak(self, originPeak, targetPeaks):
        raise RuntimeError('NYI')

    def getCollectionPeaks(self, originPeak, targetPeakLists:list):
        raise RuntimeError('NYI')

AVAILABLEFOLLOWPEAKS = {
                    FollowNearestPeak.name: FollowNearestPeak,
                    # FollowSameAssignmentPeak.name: FollowSameAssignmentPeak
                    }
