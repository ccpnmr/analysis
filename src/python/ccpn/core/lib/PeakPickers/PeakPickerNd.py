"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-02-16 13:22:59 +0000 (Tue, February 16, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2021-02-08 11:42:15 +0000 (Mon, February 08, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
from ccpn.core.lib.PeakPickers.PeakPickerABC import PeakPickerABC, SimplePeak
from ccpnc.peak import Peak as CPeak
from ccpn.util.Logging import getLogger


GAUSSIANMETHOD = 'gaussian'
LORENTZIANMETHOD = 'lorentzian'
PARABOLICMETHOD = 'parabolic'
PICKINGMETHODS = (GAUSSIANMETHOD, LORENTZIANMETHOD, PARABOLICMETHOD)


class PeakPickerNd(PeakPickerABC):
    """A simple Nd peak picker for testing
    """

    peakPickerType = "PeakPickerNd"
    onlyFor1D = False

    def __init__(self, spectrum):
        super().__init__(spectrum=spectrum)
        self.noise = None
        self.positiveThreshold = spectrum.positiveContourBase if spectrum.includePositiveContours else None
        self.negativeThreshold = spectrum.negativeContourBase if spectrum.includeNegativeContours else None

        # set some defaults
        self.dropFactor = 0.1
        self.minimumLineWidth = None
        self.checkAllAdjacent = True
        self.fitMethod = PARABOLICMETHOD
        self.singularMode = True

    def findPeaks(self, data) -> list:
        """Find peaks
        """

        # NOTE:ED - need to validate the parameters first

        if self.noise is None:
            getLogger().debug('spectrum.estimateNoise on findPeaks')
            self.noise = self.spectrum.estimateNoise()

        # set threshold values
        doPos = self.positiveThreshold is not None
        doNeg = self.negativeThreshold is not None
        posLevel = self.positiveThreshold or 0.0
        negLevel = self.negativeThreshold or 0.0

        # accounted for by pickPeaks in superclass
        exclusionBuffer = [0] * self.dimensionCount

        excludedRegionsList = []
        excludedDiagonalDimsList = []
        excludedDiagonalTransformList = []
        nonAdj = 1 if self.checkAllAdjacent else 0
        minLinewidth = [0.0] * self.dimensionCount if not self.minimumLineWidth else self.minimumLineWidth

        pointPeaks = CPeak.findPeaks(data, doNeg, doPos,
                                     negLevel, posLevel, exclusionBuffer,
                                     nonAdj,
                                     self.dropFactor,
                                     minLinewidth,
                                     excludedRegionsList, excludedDiagonalDimsList, excludedDiagonalTransformList)

        # the above can be replaced with the peak list for
        # refit peaks, etc.

        # get the peak maxima from pointPeaks
        pointPeaks = [(np.array(position), height) for position, height in pointPeaks]

        # ignore exclusion buffer for the minute
        validPointPeaks = [pk for pk in pointPeaks]

        allPeaksArray = None
        allRegionArrays = []
        regionArray = None

        # get the offset of the bottom left of the slice region
        startPoint = np.array([pp[0] for pp in self.sliceTuples])
        endPoint = np.array([pp[1] for pp in self.sliceTuples])
        numPointInt = (endPoint - startPoint) + 1

        bLeftAll = None
        for position, height in validPointPeaks:

            # get the region containing this point
            bLeft = np.maximum(position - 2, 0)
            tRight = np.minimum(position + 3, numPointInt)
            localRegionArray = np.array((bLeft, tRight), dtype=np.int32)

            # get the larger regionArray size containing all points so far
            # the actual picked region may be huge, only need the bounds containing the maxima
            bLeftAll = np.maximum(position - 3, 0)
            tRightAll = np.minimum(position + 4, numPointInt)
            if regionArray is not None:
                bLeftAll = np.array(np.minimum(bLeftAll, regionArray[0]), dtype=np.int32)
                tRightAll = np.array(np.maximum(tRightAll, regionArray[1]), dtype=np.int32)

            # numpy arrays need tweaking to pass to the c code
            peakArray = position.reshape((1, self.dimensionCount))
            peakArray = peakArray.astype(np.float32)
            regionArray = np.array((bLeftAll, tRightAll), dtype=np.int32)

            if allPeaksArray is None:
                allPeaksArray = peakArray
            else:
                allPeaksArray = np.append(allPeaksArray, peakArray, axis=0)
            allRegionArrays.append(localRegionArray)

        if allPeaksArray is not None and allPeaksArray.size != 0:

            fitMethod = self.fitMethod
            singularMode = self.singularMode

            try:
                result = ()
                if fitMethod == PARABOLICMETHOD:  # and singularMode is True:

                    # parabolic - generate all peaks in one operation
                    result = CPeak.fitParabolicPeaks(data, regionArray, allPeaksArray)

                else:
                    method = 1 if fitMethod == LORENTZIANMETHOD else 0

                    # currently gaussian or lorentzian
                    if singularMode is True:

                        # fit peaks individually in small regions
                        for peakArray, localRegionArray in zip(allPeaksArray, allRegionArrays):
                            peakArray = peakArray.reshape((1, self.dimensionCount))
                            peakArray = peakArray.astype(np.float32)
                            localResult = CPeak.fitPeaks(data, localRegionArray, peakArray, method)

                            result += tuple(localResult)
                    else:

                        # fit all peaks in one operation
                        result = CPeak.fitPeaks(data, regionArray, allPeaksArray, method)

                # Why is point reversed but not lineWidths?
                return [SimplePeak(points=point[::-1], height=height, lineWidths=pointLineWidths)
                        for height, point, pointLineWidths in result]

            except CPeak.error as es:
                getLogger().warning(f'Aborting peak fit: {es}')
                return []

        return []

    def fitExistingPeaks(self, **args):
        pass


PeakPickerNd.register()
