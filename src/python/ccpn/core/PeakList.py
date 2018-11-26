"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================

__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:29 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================

__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Sequence, List, Optional
import collections
import numpy

from numpy import argwhere
from scipy.ndimage import maximum_filter, minimum_filter
from ccpn.util import Common as commonUtil
from scipy.integrate import trapz

from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Spectrum import Spectrum
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import PeakList as ApiPeakList
from ccpn.core.lib.SpectrumLib import _oldEstimateNoiseLevel1D
from ccpnmodel.ccpncore.lib import Util as modelUtil
# from ccpnmodel.ccpncore.lib.CopyData import copySubTree
from ccpnmodel.ccpncore.lib._ccp.nmr.Nmr.PeakList import fitExistingPeakList
from ccpnmodel.ccpncore.lib._ccp.nmr.Nmr.PeakList import pickNewPeaks
from ccpn.util.decorators import notify, propertyUndo
from ccpn.util.decorators import newObject, logCommand


def _estimateNoiseLevel1D(y):
    '''
    # TODO split in two functions . Clean up line 62:  e =
    Estimates the noise threshold based on the max intensity of the first portion of the spectrum where
    only noise is present. To increase the threshold value: increase the factor.
    return:  float of estimated noise threshold and Signal to Noise Ratio
    '''
    import numpy as np
    import math

    if y is not None:
        firstEstimation = np.std(y[:int(len(y) / 20)])
        estimatedGaussian = np.random.normal(size=y.shape) * firstEstimation
        e = (np.std(estimatedGaussian) + (np.std(firstEstimation) - np.std(estimatedGaussian)))
        e2 = np.max(estimatedGaussian) + (abs(np.min(estimatedGaussian)))
        if e < e2:
            e = e2

        eS = np.where(y >= e)
        eSN = np.where(y <= -e)
        eN = np.where((y < e) & (y > -e))
        estimatedSignalRegionPos = y[eS]
        estimatedSignalRegionNeg = y[eSN]
        estimatedSignalRegion = np.concatenate((estimatedSignalRegionPos, estimatedSignalRegionNeg))
        estimatedNoiseRegion = y[eN]

        lenghtESR = len(estimatedSignalRegion)
        lenghtENR = len(estimatedNoiseRegion)
        if lenghtESR > lenghtENR:
            l = lenghtENR
        else:
            l = lenghtESR
        if l == 0:
            SNR = 1
        else:
            noise = estimatedNoiseRegion[:l - 1]
            signalAndNoise = estimatedSignalRegion[:l - 1]
            signal = abs(signalAndNoise - noise)

            signal[::-1].sort()  # descending
            noise[::1].sort()
            signal = signal.compressed()  # remove the mask
            noise = noise.compressed()  # remove the mask
            s = signal[:int(l / 2)]
            n = noise[:int(l / 2)]
            if len(signal) == 0:
                return 1, e

            SNR = math.log10(abs(np.mean(s) ** 2 / np.mean(n) ** 2))
            if SNR:
                return SNR, e
            else:
                return 1, e

        return SNR, e
    else:
        return 1, 0


def _filtered1DArray(data, ignoredRegions):
    # returns an array without ignoredRegions. Used for automatic 1d peak picking
    ppmValues = data[0]
    masks = []
    for region in ignoredRegions:
        mask = (ppmValues > region[0]) | (ppmValues < region[1])
        masks.append(mask)
    fullmask = [all(mask) for mask in zip(*masks)]
    newArray = (numpy.ma.MaskedArray(data, mask=numpy.logical_not((fullmask, fullmask))))
    return newArray


class PeakList(AbstractWrapperObject):
    """An object containing Peaks. Note: the object is not a (subtype of a) Python list.
    To access all Peak objects, use PeakList.peaks."""

    #: Short class name, for PID.
    shortClassName = 'PL'
    # Attribute it necessary as subclasses must use superclass className
    className = 'PeakList'

    _parentClass = Spectrum

    #: Name of plural link to instances of class
    _pluralLinkName = 'peakLists'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiPeakList._metaclass.qualifiedName()

    # Special error-raising functions for people who think PeakList is a list
    def __iter__(self):
        raise TypeError("'PeakList object is not iterable - for a list of peaks use Peaklist.peaks")

    def __getitem__(self, index):
        raise TypeError("'PeakList object does not support indexing - for a list of peaks use Peaklist.peaks")

    def __len__(self):
        raise TypeError("'PeakList object has no length - for a list of peaks use Peaklist.peaks")

    # CCPN properties
    @property
    def _apiPeakList(self) -> ApiPeakList:
        """API peakLists matching PeakList."""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """id string - serial number converted to string."""
        return str(self._wrappedData.serial)

    @property
    def serial(self) -> int:
        """serial number of PeakList, used in Pid and to identify the PeakList."""
        return self._wrappedData.serial

    @property
    def _parent(self) -> Spectrum:
        """Spectrum containing Peaklist."""
        return self._project._data2Obj[self._wrappedData.dataSource]

    spectrum = _parent

    @property
    def title(self) -> str:
        """title of PeakList (not used in PID)."""
        return self._wrappedData.name

    @title.setter
    def title(self, value: str):
        self._wrappedData.name = value

    @property
    def comment(self) -> str:
        """Free-form text comment"""
        return self._wrappedData.details

    @comment.setter
    def comment(self, value: str):
        self._wrappedData.details = value

    @property
    def symbolStyle(self) -> str:
        """Symbol style for peak annotation display in all displays."""
        return self._wrappedData.symbolStyle

    @symbolStyle.setter
    def symbolStyle(self, value: str):
        self._wrappedData.symbolStyle = value

    @property
    def symbolColour(self) -> str:
        """Symbol colour for peak annotation display in all displays."""
        return self._wrappedData.symbolColour

    @symbolColour.setter
    def symbolColour(self, value: str):
        self._wrappedData.symbolColour = value

    @property
    def textColour(self) -> str:
        """Text colour for peak annotation display in all displays."""
        return self._wrappedData.textColour

    @textColour.setter
    def textColour(self, value: str):
        self._wrappedData.textColour = value

    @property
    def isSimulated(self) -> bool:
        """True if this PeakList is simulated."""
        return self._wrappedData.isSimulated

    @isSimulated.setter
    def isSimulated(self, value: bool):
        self._wrappedData.isSimulated = value

    # Library functions

    ###def pickPeaksNd(self, positions:Sequence[float]=None,
    def pickPeaksNd(self, regionToPick: Sequence[float] = None,
                    doPos: bool = True, doNeg: bool = True,
                    fitMethod: str = 'gaussian', excludedRegions=None,
                    excludedDiagonalDims=None, excludedDiagonalTransform=None,
                    minDropfactor: float = 0.1):

        # TODO NBNB Add doc string and put type annotation on all parameters

        # regionToPick = [hRange, cRange, nRange] for 3D, for example

        defaults = collections.OrderedDict(
                ###( ('positions', None), ('doPos', True), ('doNeg', True),
                (('regionToPick', None), ('doPos', True), ('doNeg', True),
                 ('fitMethod', 'gaussian'), ('excludedRegions', None), ('excludedDiagonalDims', None),
                 ('excludedDiagonalTransform', None), ('minDropfactor', 0.1)
                 )
                )
        startPoint = []
        endPoint = []
        spectrum = self.spectrum
        dataDims = spectrum._apiDataSource.sortedDataDims()
        aliasingLimits = spectrum.aliasingLimits
        apiPeaks = []
        # for ii, dataDim in enumerate(dataDims):
        spectrumReferences = spectrum.mainSpectrumReferences
        if None in spectrumReferences:
            # TODO if we want to pick in Sampeld fo FId dimensions, this must be added
            raise ValueError("pickPeaksNd() only works for Frequency dimensions"
                             " with defined primary SpectrumReferences ")
        if regionToPick is None:
            regionToPick = self.spectrum.aliasingLimits
        for ii, spectrumReference in enumerate(spectrumReferences):
            aliasingLimit0, aliasingLimit1 = aliasingLimits[ii]
            value0 = regionToPick[ii][0]
            value1 = regionToPick[ii][1]
            value0, value1 = min(value0, value1), max(value0, value1)
            if value1 < aliasingLimit0 or value0 > aliasingLimit1:
                break  # completely outside aliasing region
            value0 = max(value0, aliasingLimit0)
            value1 = min(value1, aliasingLimit1)
            # -1 below because points start at 1 in data model
            # position0 = dataDim.primaryDataDimRef.valueToPoint(value0) - 1
            # position1 = dataDim.primaryDataDimRef.valueToPoint(value1) - 1
            position0 = spectrumReference.valueToPoint(value0) - 1
            position1 = spectrumReference.valueToPoint(value1) - 1
            position0, position1 = min(position0, position1), max(position0, position1)
            # want integer grid points above position0 and below position1
            # add 1 to position0 because above
            # add 1 to position1 because doing start <= x < end not <= end
            # yes, this negates -1 above but they are for different reasons
            position0 = int(position0 + 1)
            position1 = int(position1 + 1)
            # startPoint.append((dataDim.dim, position0))
            # endPoint.append((dataDim.dim, position1))
            startPoint.append((spectrumReference.dimension, position0))
            endPoint.append((spectrumReference.dimension, position1))
        else:
            startPoints = [point[1] for point in sorted(startPoint)]
            endPoints = [point[1] for point in sorted(endPoint)]
            # print(isoOrdering, startPoint, startPoints, endPoint, endPoints)

            posLevel = spectrum.positiveContourBase if doPos else None
            negLevel = spectrum.negativeContourBase if doNeg else None

            undo = self._project._undo
            self._startCommandEchoBlock('pickPeaksNd', values=locals(), defaults=defaults)
            self._project.blankNotification()
            # undo.increaseBlocking()
            try:
                apiPeaks = pickNewPeaks(self._apiPeakList, startPoint=startPoints, endPoint=endPoints,
                                        posLevel=posLevel, negLevel=negLevel, fitMethod=fitMethod,
                                        excludedRegions=excludedRegions, excludedDiagonalDims=excludedDiagonalDims,
                                        excludedDiagonalTransform=excludedDiagonalTransform, minDropfactor=minDropfactor)

            finally:
                self._endCommandEchoBlock()
                self._project.unblankNotification()
                # undo.decreaseBlocking()

        data2ObjDict = self._project._data2Obj
        result = [data2ObjDict[apiPeak] for apiPeak in apiPeaks]
        for peak in result:
            peak._finaliseAction('create')

        return result

    def pickPeaks1d(self, dataRange, intensityRange=None, size: int = 3, mode: str = 'wrap') -> List['Peak']:
        """
        Pick 1D peaks from a dataRange (E.G selection in ViewBox)
        """

        self._project.suspendNotification()

        try:
            if dataRange[0] < dataRange[1]:
                dataRange[0], dataRange[1] = dataRange[1], dataRange[0]
            # code below assumes that dataRange[1] > dataRange[0]
            peaks = []
            spectrum = self.spectrum
            # data1d = spectrum._apiDataSource.get1dSpectrumData()
            data1d = numpy.array([self.spectrum.positions, self.spectrum.intensities])
            selectedData = data1d[:, (data1d[0] < dataRange[0]) * (data1d[0] > dataRange[1])]
            if selectedData.size == 0:
                return peaks
            maxFilter = maximum_filter(selectedData[1], size=size, mode=mode)
            boolsMax = selectedData[1] == maxFilter
            indices = argwhere(boolsMax)

            minFilter = minimum_filter(selectedData[1], size=size, mode=mode)
            boolsMin = selectedData[1] == minFilter
            negBoolsPeak = boolsMin
            indicesMin = argwhere(negBoolsPeak)

            fullIndices = numpy.append(indices, indicesMin)  # True positional indices

            for position in fullIndices:
                peakPosition = [float(selectedData[0][position])]
                height = selectedData[1][position]
                if intensityRange is None or intensityRange[0] <= height <= intensityRange[1]:
                    peaks.append(self.newPeak(height=float(height), position=peakPosition))

        finally:
            self._project.resumeNotification()

        return peaks

    def pickPeaks1dFiltered(self, size: int = 9, mode: str = 'wrap', factor=2, excludeRegions=None,
                            positiveNoiseThreshold=None, negativeNoiseThreshold=None, negativePeaks=True):
        """
        Pick 1D peaks form data in  self.spectrum
        """
        defaults = collections.OrderedDict((('size', 9), ('mode', 'wrap'), ('excludeRegions', None), ('positiveNoiseThreshold', None)))

        self._startCommandEchoBlock('pickPeaks1dFiltered', values=locals(), defaults=defaults)
        ll = []
        try:
            if excludeRegions is None:
                excludeRegions = [[-20.1, -19.1]]
            excludeRegions = [sorted(pair, reverse=True) for pair in excludeRegions]
            peaks = []
            spectrum = self.spectrum
            # data = spectrum._apiDataSource.get1dSpectrumData()
            data = numpy.array([spectrum.positions, spectrum.intensities])
            ppmValues = data[0]
            if positiveNoiseThreshold == 0.0 or positiveNoiseThreshold is None:
                positiveNoiseThreshold = _oldEstimateNoiseLevel1D(spectrum.intensities, factor=factor)
                if spectrum.noiseLevel is None:
                    positiveNoiseThreshold = _oldEstimateNoiseLevel1D(spectrum.intensities, factor=factor)
                    negativeNoiseThreshold = -positiveNoiseThreshold

            if negativeNoiseThreshold == 0.0 or negativeNoiseThreshold is None:
                negativeNoiseThreshold = _oldEstimateNoiseLevel1D(spectrum.intensities, factor=factor)
                if spectrum.noiseLevel is None:
                    negativeNoiseThreshold = -positiveNoiseThreshold

            masks = []
            for region in excludeRegions:
                mask = (ppmValues > region[0]) | (ppmValues < region[1])
                masks.append(mask)
            fullmask = [all(mask) for mask in zip(*masks)]
            newArray2 = (numpy.ma.MaskedArray(data, mask=numpy.logical_not((fullmask, fullmask))))

            if (newArray2.size == 0) or (data.max() < positiveNoiseThreshold):
                return peaks

            posBoolsVal = newArray2[1] > positiveNoiseThreshold
            maxFilter = maximum_filter(newArray2[1], size=size, mode=mode)
            boolsMax = newArray2[1] == maxFilter
            boolsPeak = posBoolsVal & boolsMax
            indices = argwhere(boolsPeak)

            if negativePeaks:
                minFilter = minimum_filter(data[1], size=size, mode=mode)
                boolsMin = newArray2[1] == minFilter
                negBoolsVal = newArray2[1] < negativeNoiseThreshold
                negBoolsPeak = negBoolsVal & boolsMin
                indicesMin = argwhere(negBoolsPeak)
                indices = numpy.append(indices, indicesMin)

            for position in indices:
                peakPosition = [float(newArray2[0][position])]
                height = newArray2[1][position]
                peaks.append(self.newPeak(height=float(height), position=peakPosition))

        finally:
            self._endCommandEchoBlock()
        return peaks

    def _noiseLineWidth(self):
        from ccpn.core.IntegralList import _getPeaksLimits

        x, y = numpy.array(self.spectrum.positions), numpy.array(self.spectrum.intensities)
        x, y = x[:int(len(x) / 20)], y[:int(len(x) / 20)],
        noiseMean = numpy.mean(y)
        intersectingLine = [noiseMean] * len(x)
        limitsPairs = _getPeaksLimits(x, y, intersectingLine)
        widths = [0]
        for i in limitsPairs:
            lineWidth = abs(i[0] - i[1])
            widths.append(lineWidth)
        return numpy.std(widths)

    # def automatic1dPeakPicking(self, sizeFactor=3, negativePeaks=True, minimalLineWidth=None, ignoredRegions=None):
    #   '''
    #   :param ignoredRegions: in the form [[-20.1, -19.1]]
    #   :param noiseThreshold: float
    #   :param sizeFactor: smoothing value. increase to pick less "shoulder" point of peaks
    #   :param negativePeaks: pick peaks in the negative region
    #   :return:
    #   '''
    #
    #   from ccpn.core.IntegralList import _getPeaksLimits
    #
    #   self._startCommandEchoBlock('automatic1dPeakPicking', values=locals())
    #   integralList = self.spectrum.newIntegralList()
    #   if minimalLineWidth is None:
    #     minimalLineWidth = self._noiseLineWidth()
    #   try:
    #     x,y = numpy.array(self.spectrum.positions), numpy.array(self.spectrum.intensities)
    #
    #     data =[x,y]
    #     if ignoredRegions is None:
    #       ignoredRegions = [[-20.1, -19.1]]
    #
    #     peaks = []
    #     SNR = None
    #     defaultSize = 9 #Default value but automatically calculated below
    #     filteredArray = _filtered1DArray(data, ignoredRegions)
    #
    #     SNR, noiseThreshold = _estimateNoiseLevel1D(filteredArray[1])
    #     ratio = numpy.std(abs(filteredArray[1])) / noiseThreshold
    #     # size = (1 / ratio) * 100 * sizeFactor
    #     # important bit to auto calculate the smooting factor (size)
    #     import math
    #     plusPercent = sizeFactor
    #     ftr = math.log(noiseThreshold)
    #     size = (SNR*ftr)/SNR
    #     if size is None or 0:
    #       size = defaultSize
    #     percent = (size*plusPercent)/100
    #     size+=percent
    #
    #     size = sizeFactor
    #     # print('noiseThreshold: {}, SNR: {}, ratio: {},  size: {}, '.format(noiseThreshold, SNR, ratio, size))
    #     print('size: {}, '.format(size))
    #     posBoolsVal = filteredArray[1] > noiseThreshold
    #     maxFilter = maximum_filter(filteredArray[1], size=size, mode='wrap')
    #     boolsMax = filteredArray[1] == maxFilter
    #     boolsPeak = posBoolsVal & boolsMax
    #     indices = numpy.argwhere(boolsPeak)
    #
    #     if negativePeaks:
    #       minFilter = minimum_filter(filteredArray[1], size=size, mode='wrap')
    #       boolsMin = filteredArray[1] == minFilter
    #       negBoolsVal = filteredArray[1] < -noiseThreshold
    #       negBoolsPeak = negBoolsVal & boolsMin
    #       indicesMin = numpy.argwhere(negBoolsPeak)
    #       indices = numpy.append(indices, indicesMin)
    #
    #     ps = []
    #
    #     for position in indices:
    #       peakPosition = [float(filteredArray[0][position])]
    #       height = filteredArray[1][position]
    #       ps.append({'positions': peakPosition, 'height': height})
    #
    #       #searches for integrals
    #     intersectingLine = [noiseThreshold]*len(x)
    #     limitsPairs = _getPeaksLimits(x, y, intersectingLine)
    #
    #     results = []
    #     for i in limitsPairs:
    #       peaksBetweenLimits = []
    #
    #       lineWidth = abs(i[0] - i[1])
    #       if lineWidth > minimalLineWidth:
    #         for p in ps:
    #           peakPosition = p['positions']
    #           height = p['height']
    #           if i[0]>peakPosition[0]>i[1]: #peak  position is between limits
    #             peaksBetweenLimits.append(p)
    #       results.append({'limits':i, 'peaksBetweenLimits':peaksBetweenLimits})
    #
    #     if len(results)>1:
    #       ll = []
    #       for item in results:
    #         peaks = item['peaksBetweenLimits']
    #         limits = item['limits'] #list of [max, min]
    #         if len(peaks) == 1: #only a peak inside.
    #           peakPos = peaks[0].get('positions')
    #           peakHeigh = float(peaks[0].get('height'))
    #
    #           lw = abs(limits[0] - limits[1])
    #           region = numpy.where((x <= limits[0]) & (x >= limits[1]))
    #           integral = trapz(y[region])
    #           peak = self.newPeak(height=peakHeigh, position=peakPos, volume=float(integral),
    #                               lineWidths=[lw,])
    #           newIntegral = integralList.newIntegral(limits=[[min(limits), max(limits)]])
    #           newIntegral.peak = peak
    #           newIntegral._baseline = noiseThreshold
    #
    #         if len(peaks)>1:
    #           minL = min(limits)
    #
    #           for peak in sorted(peaks, key=lambda k: k['positions'][0]):  # smallest to biggest
    #
    #
    #             peakPos = peak.get('positions')
    #             peakHeigh = float(peak.get('height'))
    #             oldMin = minL
    #             deltaPos = abs(peakPos - minL)
    #             tot = peakPos + deltaPos
    #             minL = tot
    #             if minL > max(limits):
    #               minL = max(limits)
    #             ll.append({'limits':(oldMin, minL), 'peak':peak})
    #
    #       for d in ll:
    #         newMax = max(d['limits'])
    #         newMin = min(d['limits'])
    #         peak = d['peak']
    #
    #         peakPos = peak.get('positions')
    #         peakHeigh = float(peak.get('height'))
    #         newLw = abs(newMax - newMin)
    #         region = numpy.where((x <= newMax) & (x >= newMin))
    #         integral = trapz(region)
    #         peak = self.newPeak(height=peakHeigh, position=peakPos, volume=float(integral),
    #                             )
    #         newIntegral = integralList.newIntegral(limits=[[newMin,newMax]])
    #         newIntegral.peak = peak
    #         newIntegral._baseline = noiseThreshold
    #
    #     self.spectrum.signalToNoiseRatio = SNR
    #
    #   finally:
    #     self._endCommandEchoBlock()
    #
    #   return peaks

    def peakFinder1D(self, deltaFactor=1.5, ignoredRegions=[[20, 19]], negativePeaks=True):
        from ccpn.core.lib.peakUtils import peakdet, _getIntersectionPoints, _pairIntersectionPoints
        from scipy import signal
        import numpy as np
        import time

        self._startCommandEchoBlock('automatic1dPeakPicking', values=locals())
        try:
            spectrum = self.spectrum
            integralList = self.spectrum.newIntegralList()

            peaks = []
            x, y = spectrum.positions, spectrum.intensities
            masked = _filtered1DArray(numpy.array([x, y]), ignoredRegions)
            filteredX, filteredY = masked[0], masked[1]
            SNR, noiseThreshold = _estimateNoiseLevel1D(filteredY)

            maxValues, minValues = peakdet(y=filteredY, x=filteredX, delta=noiseThreshold / deltaFactor)
            for position, height in maxValues:
                peak = self.newPeak(position=[position], height=height)

            # const = round(len(y) * 0.0039, 1)
            # correlatedSignal1 = signal.correlate(y, np.ones(int(const)), mode='same') / const
            # intersectionPoints = _getIntersectionPoints(x, y, correlatedSignal1)
            # pairIntersectionPoints = _pairIntersectionPoints(intersectionPoints)
            #
            #
            # for limits in list(pairIntersectionPoints):
            #   for position, height in maxValues:
            #     if height > delta: # ensure are only the positive peaks
            #       if max(limits) > position > min(limits):  # peak  position is between limits
            #         lw = max(limits) - min(limits)
            #         peak = self.newPeak(position=[position], height=height, lineWidths = [lw])
            #         newIntegral = integralList.newIntegral(limits=[[min(limits), max(limits)]])
            #         newIntegral.peak = peak
            #         peak.volume = newIntegral.value
            #         peaks.append(peak)
            #
            # if negativePeaks:
            #   for i in minValues:
            #     if i[1] < -delta:
            #       peaks.append(self.newPeak(position=[i[0]], height=i[1]))
        finally:
            self._endCommandEchoBlock()
        # return peaks

    def copyTo(self, targetSpectrum: Spectrum, **kwargs) -> 'PeakList':
        """Make (and return) a copy of the PeakList attached to targetSpectrum

        Peaklist attributes can be passed in as keyword arguments"""

        singleValueTags = ['isSimulated', 'symbolColour', 'symbolStyle', 'textColour', 'textColour',
                           'title', 'comment']

        dimensionCount = self.spectrum.dimensionCount
        if dimensionCount != targetSpectrum.dimensionCount:
            raise ValueError("Cannot copy %sD %s to %sD %s"
                             % (dimensionCount, self.longPid,
                                targetSpectrum.dimensionCount, targetSpectrum.longPid))

        params = dict(((tag, getattr(self, tag)) for tag in singleValueTags))
        params['comment'] = "Copy of %s\n" % self.longPid + (params['comment'] or '')
        for key, val in kwargs.items():
            if key in singleValueTags:
                params[key] = val
            else:
                raise ValueError("PeakList has no attribute %s" % key)
        newPeakList = targetSpectrum.newPeakList(**params)
        newPeakList.symbolColour = targetSpectrum.positiveContourColour
        newPeakList.textColour = targetSpectrum.positiveContourColour
        for peak in self.peaks:
            peak.copyTo(newPeakList)
        #
        return newPeakList

    def subtractPeakLists(self, peakList2: 'PeakList') -> 'PeakList':
        """
        Subtracts peaks in peakList2 from peaks in peakList1, based on position,
        and puts those in a new peakList3.  Assumes a common spectrum for now.
        """

        def _havePeakNearPosition(values, tolerances, peaks) -> Optional['Peak']:

            for peak in peaks:
                for i, position in enumerate(peak.position):
                    if abs(position - values[i]) > tolerances[i]:
                        break
                else:
                    return peak

        self._startCommandEchoBlock('subtractPeakLists', values={'peakList2': peakList2},
                                    parName='newPeakList')

        try:

            spectrum = self.spectrum

            assert spectrum is peakList2.spectrum, 'For now requires both peak lists to be in same spectrum'

            # dataDims = spectrum.sortedDataDims()
            tolerances = self.spectrum.assignmentTolerances

            peaks2 = peakList2.peaks
            peakList3 = spectrum.newPeakList()

            for peak1 in self.peaks:
                values1 = [peak1.position[dim] for dim in range(len(peak1.position))]
                if not _havePeakNearPosition(values1, tolerances, peaks2):
                    peakList3.newPeak(height=peak1.height, volume=peak1.volume, figureOfMerit=peak1.figureOfMerit,
                                      annotation=peak1.annotation, position=peak1.position,
                                      pointPosition=peak1.pointPosition)


        finally:
            self._endCommandEchoBlock()

        return peakList3

    def refit(self, method: str = 'gaussian'):
        fitExistingPeakList(self._apiPeakList, method)

    def restrictedPick(self, positionCodeDict, doPos, doNeg):

        codes = list(positionCodeDict.keys())
        positions = [positionCodeDict[code] for code in codes]
        axisCodeMapping = commonUtil._axisCodeMapIndices(codes, self.spectrum.axisCodes)

        # divide by 2 to get the double-width tolerance, i.e. the width of the region - CHECK WITH GEERTEN
        tolerances = tuple(tol / 2 for tol in self.spectrum.assignmentTolerances)

        limits = self.spectrum.spectrumLimits
        selectedRegion = []
        minDropFactor = self.project._appBase.preferences.general.peakDropFactor

        for ii, mapping in enumerate(axisCodeMapping):
            if mapping is not None:
                selectedRegion.insert(ii, [positions[mapping] - tolerances[ii], positions[mapping] + tolerances[ii]])
            else:
                selectedRegion.insert(ii, [limits[ii][0], limits[ii][1]])

        regionToPick = selectedRegion
        peaks = self.pickPeaksNd(regionToPick, doPos=doPos, doNeg=doNeg, minDropfactor=minDropFactor)
        return peaks

    def reorderValues(self, values, newAxisCodeOrder):
        """Reorder values in spectrum dimension order to newAxisCodeOrder
        by matching newAxisCodeOrder to spectrum axis code order"""
        return commonUtil.reorder(values, self._parent.axisCodes, newAxisCodeOrder)

    # def __str__(self):
    #   """Readable string representation"""
    #   return "<%s; #peaks:%d (isSimulated=%s)>" % (self.pid, len(self.peaks), self.isSimulated)

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Spectrum) -> list:
        """get wrappedData (PeakLists) for all PeakList children of parent Spectrum"""
        return [x for x in parent._wrappedData.sortedPeakLists() if x.dataType == 'Peak']

    def _finaliseAction(self, action: str):
        """Subclassed to handle associated peakListViews
        """
        super()._finaliseAction(action=action)

        if action in ['change']:
            for plv in self.peakListViews:
                plv._finaliseAction(action=action)

    #===========================================================================================
    # Hot fixed methods (baahhhhhh)
    # Copied from their respective locations
    #===========================================================================================

    @logCommand('peaklist.')
    @newObject()
    def newPeak(self, height: float = None, volume: float = None,
                heightError: float = None, volumeError: float = None,
                figureOfMerit: float = 1.0, annotation: str = None, comment: str = None,
                position: Sequence[float] = (), positionError: Sequence[float] = (),
                pointPosition: Sequence[float] = (), boxWidths: Sequence[float] = (),
                lineWidths: Sequence[float] = (), serial: int = None):
        """Create a new Peak within a peakList

        NB you must create the peak before you can assign it. The assignment attributes are:
        - assignedNmrAtoms - A tuple of all (e.g.) assignment triplets for a 3D spectrum
        - dimensionNmrAtoms - A tuple of tuples of assignments, one for each dimension

        See the Peak class for details

        :param height:
        :param volume:
        :param heightError:
        :param volumeError:
        :param figureOfMerit:
        :param annotation:
        :param comment:
        :param position:
        :param positionError:
        :param pointPosition:
        :param boxWidths:
        :param lineWidths:
        :param serial:
        :return new peak:
        """
        from ccpn.core.Peak import _newPeak

        return _newPeak(self, height=height, volume=volume,
                        heightError=heightError, volumeError=volumeError,
                        figureOfMerit=figureOfMerit, annotation=annotation, comment=comment,
                        position=position, positionError=positionError,
                        pointPosition=pointPosition, boxWidths=boxWidths,
                        lineWidths=lineWidths, serial=serial
                        )


#=========================================================================================
# CCPN functions
#=========================================================================================

# Connections to parents:

def _newPeakList(self: Spectrum, title: str = None, comment: str = None,
                 isSimulated: bool = False, symbolStyle: str = None, symbolColour: str = None,
                 textColour: str = None, serial: int = None) -> PeakList:
    """Create new empty PeakList within Spectrum

    :param title:
    :param comment:
    :param isSimulated:
    :param symbolStyle:
    :param symbolColour:
    :param textColour:
    :param serial:
    :return: a new PeakList attached to the spectrum.
    """
    # __doc__ added to Spectrum

    defaults = collections.OrderedDict((('title', None), ('comment', None), ('isSimulated', False),
                                        ('serial', None), ('symbolStyle', None), (
                                            'symbolColour', None), ('textColour', None),
                                        )
                                       )

    apiDataSource = self._wrappedData
    self._startCommandEchoBlock('newPeakList', values=locals(), defaults=defaults,
                                parName='newPeakList')
    result = None
    dd = {'name': title, 'details': comment, 'isSimulated': isSimulated}
    if symbolColour:
        dd['symbolColour'] = symbolColour
    if symbolStyle:
        dd['symbolStyle'] = symbolStyle
    if textColour:
        dd['textColour'] = textColour
    try:
        obj = apiDataSource.newPeakList(**dd)
        result = self._project._data2Obj.get(obj)
        if serial is not None:
            try:
                result.resetSerial(serial)
                # modelUtil.resetSerial(obj, serial, 'peakLists')
            except ValueError:
                self.project._logger.warning("Could not reset serial of %s to %s - keeping original value"
                                             % (result, serial))
            result._finaliseAction('rename')

    finally:
        self._endCommandEchoBlock()
    #
    return result


Spectrum.newPeakList = _newPeakList
del _newPeakList

# Notifiers:
