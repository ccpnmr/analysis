"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:29 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
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
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, ccpNmrV3CoreSetter, logCommandBlock, \
    notificationBlanking, undoBlock

from ccpn.util.Logging import getLogger

GAUSSIANMETHOD = 'gaussian'
LORENTZIANMETHOD = 'lorentzian'
PARABOLICMETHOD = 'parabolic'
PICKINGMETHODS = (GAUSSIANMETHOD, LORENTZIANMETHOD, PARABOLICMETHOD)


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

    # @property
    # def comment(self) -> str:
    #     """Free-form text comment"""
    #     return self._wrappedData.details
    #
    # @comment.setter
    # def comment(self, value: str):
    #     self._wrappedData.details = value

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

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Spectrum) -> list:
        """get wrappedData (PeakLists) for all PeakList children of parent Spectrum"""
        return [x for x in parent._wrappedData.sortedPeakLists() if x.dataType == 'Peak']

    def _finaliseAction(self, action: str):
        """Subclassed to notify changes to associated peakListViews
        """
        super()._finaliseAction(action=action)

        # this is a can-of-worms for undelete at the minute
        try:
            if action in ['change']:
                for plv in self.peakListViews:
                    plv._finaliseAction(action=action)
        except Exception as es:
            raise RuntimeError('Error _finalising peakListViews: %s' % str(es))

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    ###def pickPeaksNd(self, positions:Sequence[float]=None,
    def pickPeaksNd(self, regionToPick: Sequence[float] = None,
                    doPos: bool = True, doNeg: bool = True,
                    fitMethod: str = PARABOLICMETHOD, excludedRegions=None,
                    excludedDiagonalDims=None, excludedDiagonalTransform=None,
                    minDropfactor: float = 0.1):

        # TODO NBNB Add doc string and put type annotation on all parameters

        # regionToPick = [hRange, cRange, nRange] for 3D, for example

        defaults = collections.OrderedDict(
                ###( ('positions', None), ('doPos', True), ('doNeg', True),
                (('regionToPick', None), ('doPos', True), ('doNeg', True),
                 ('fitMethod', PARABOLICMETHOD), ('excludedRegions', None), ('excludedDiagonalDims', None),
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

            # with logCommandBlock(get='self') as log:
            #     log('pickPeaksNd')
            #     with notificationBlanking():

            apiPeaks = pickNewPeaks(self._apiPeakList, startPoint=startPoints, endPoint=endPoints,
                                    posLevel=posLevel, negLevel=negLevel, fitMethod=fitMethod,
                                    excludedRegions=excludedRegions, excludedDiagonalDims=excludedDiagonalDims,
                                    excludedDiagonalTransform=excludedDiagonalTransform, minDropfactor=minDropfactor)

        data2ObjDict = self._project._data2Obj
        result = [data2ObjDict[apiPeak] for apiPeak in apiPeaks]
        # for peak in result:
        #     peak._finaliseAction('create')

        return result

    def pickPeaks1d(self, dataRange, intensityRange=None, size: int = 3, mode: str = 'wrap') -> List['Peak']:
        """
        Pick 1D peaks from a dataRange
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
                    peaks.append(self.newPeak(height=float(height), ppmPositions=peakPosition))

        finally:
            self._project.resumeNotification()

        return peaks

    def pickPeaks1dFiltered(self, size: int = 9, mode: str = 'wrap', factor=2, excludeRegions=None,
                            positiveNoiseThreshold=None, negativeNoiseThreshold=None, negativePeaks=True):
        """
        Pick 1D peaks form data in  self.spectrum
        """
        ll = []
        with logCommandBlock(get='self') as log:
            log('pickPeaks1dFiltered')

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
                peaks.append(self.newPeak(height=float(height), ppmPositions=peakPosition))

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
    #           peak = self.newPeak(height=peakHeigh, ppmPositions=peakPos, volume=float(integral),
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
    #         peakHeight = float(peak.get('height'))
    #         newLw = abs(newMax - newMin)
    #         region = numpy.where((x <= newMax) & (x >= newMin))
    #         integral = trapz(region)
    #         peak = self.newPeak(height=peakHeight, ppmPositions=peakPos, volume=float(integral),
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

        with logCommandBlock(get='self') as log:
            log('peakFinder1D')

            spectrum = self.spectrum
            integralList = self.spectrum.newIntegralList()

            peaks = []
            x, y = spectrum.positions, spectrum.intensities
            masked = _filtered1DArray(numpy.array([x, y]), ignoredRegions)
            filteredX, filteredY = masked[0], masked[1]
            SNR, noiseThreshold = _estimateNoiseLevel1D(filteredY)

            maxValues, minValues = peakdet(y=filteredY, x=filteredX, delta=noiseThreshold / deltaFactor)
            for position, height in maxValues:
                peak = self.newPeak(ppmPositions=[position], height=height)

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
            #         peak = self.newPeak(ppmPositions=[position], height=height, lineWidths = [lw])
            #         newIntegral = integralList.newIntegral(limits=[[min(limits), max(limits)]])
            #         newIntegral.peak = peak
            #         peak.volume = newIntegral.value
            #         peaks.append(peak)
            #
            # if negativePeaks:
            #   for i in minValues:
            #     if i[1] < -delta:
            #       peaks.append(self.newPeak(ppmPositions=[i[0]], height=i[1]))

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
        # newPeakList.symbolColour = targetSpectrum.positiveContourColour
        # newPeakList.textColour = targetSpectrum.positiveContourColour
        for peak in self.peaks:
            peak.copyTo(newPeakList)
        #
        return newPeakList

    def subtractPeakLists(self, peakListIn: 'PeakList') -> 'PeakList':
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

        peakList2 = [self.project.getByPid(peak) if isinstance(peak, str) else peak for peak in peakListIn]

        with logCommandBlock(prefix='newPeakList=', get='self') as log:
            peakStr = '[' + ','.join(["'%s'" % peak.pid for peak in peakList2]) + ']'
            log('subtractPeakLists', peaks=peakStr)

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
                                      annotation=peak1.annotation, ppmPositions=peak1.position,
                                      pointPosition=peak1.pointPosition)

        return peakList3

    # def refit(self, method: str = GAUSSIANMETHOD):
    #     fitExistingPeakList(self._apiPeakList, method)

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

        # regionToPick = selectedRegion
        # peaks = self.pickPeaksNd(regionToPick, doPos=doPos, doNeg=doNeg, minDropfactor=minDropFactor)

        axisCodeDict = dict((code, selectedRegion[ii]) for ii, code in enumerate(self.spectrum.axisCodes))
        peaks = self.pickPeaksRegion(axisCodeDict, doPos=doPos, doNeg=doNeg, minDropfactor=minDropFactor)

        return peaks

    def reorderValues(self, values, newAxisCodeOrder):
        """Reorder values in spectrum dimension order to newAxisCodeOrder
        by matching newAxisCodeOrder to spectrum axis code order"""
        return commonUtil.reorder(values, self._parent.axisCodes, newAxisCodeOrder)

    # def __str__(self):
    #   """Readable string representation"""
    #   return "<%s; #peaks:%d (isSimulated=%s)>" % (self.pid, len(self.peaks), self.isSimulated)

    # def positionIsInPlane(self, peakList, pointPosition) -> bool:
    #     """Is peak in currently displayed planes for strip?
    #     """
    #     spectrumView = self.findSpectrumView(peakList.spectrum)
    #     if spectrumView is None:
    #         return False
    #     displayIndices = spectrumView._displayOrderSpectrumDimensionIndices
    #     orderedAxes = self.orderedAxes[2:]
    #
    #     for ii, displayIndex in enumerate(displayIndices[2:]):
    #         if displayIndex is not None:
    #             # If no axis matches the index may be None
    #             pp = pointPosition[displayIndex]
    #             zPosition = peakList.spectrum.mainSpectrumReferences[ii].valueToPoint(pp)
    #             if not zPosition:
    #                 return False
    #             zPlaneSize = 0.
    #             zRegion = orderedAxes[ii].region
    #             if zPosition < zRegion[0] - zPlaneSize or zPosition > zRegion[1] + zPlaneSize:
    #                 return False
    #
    #     return True

    def pickPeaksRegion(self, regionToPick: dict = {},
                        doPos: bool = True, doNeg: bool = True,
                        minLinewidth=None, exclusionBuffer=None,
                        minDropfactor: float = 0.1, checkAllAdjacent: bool = True,
                        fitMethod: str = PARABOLICMETHOD, excludedRegions=None,
                        excludedDiagonalDims=None, excludedDiagonalTransform=None):
        """Pick peaks in the region defined by the regionToPick dict.

        Axis limits are passed in as a dict containing the axis codes and the required limits.
        Each limit is defined as a key, value pair: (str, tuple),
        with the tuple supplied as (min,max) axis limits in ppm.

        For axisCodes that are not included, the limits will by taken from the aliasingLimits of the spectrum.

        Illegal axisCodes will raise an error.

        Example dict:

        ::

            {'Hn': (7.0, 9.0),
             'Nh': (110, 130)
             }

        doPos, doNeg - pick positive/negative peaks or both.

        exclusionBuffer defines the size to extend the region by in index units, e.g. [1, 1, 1]
                    extends the region by 1 index point in all axes.
                    Default is 1 in all axis directions.

        minDropFactor - minimum drop factor, value between 0.0 and 1.0
                    Ratio of max value to adjacent values in dataArray. Default is 0.1
                    i.e., difference between all adjacent values and local maximum must be greater than 10%
                    for maximum to be considered as a peak.

        fitMethod - curve fitting method to find local maximum at peak location in dataArray.
                    Current methods are ('gaussian', 'lorentzian').
                    Default is gaussian.

        :param regionToPick: dict of axis limits
        :param doPos: pick positive peaks
        :param doNeg: pick negative peaks
        :param minLinewidth:
        :param exclusionBuffer: array of int
        :param minDropfactor: float defined on [0.0, 1.0] default is 0.1
        :param checkAllAdjacent: True/False, default True
        :param fitMethod: str in 'gaussian', 'lorentzian'
        :param excludedRegions:
        :param excludedDiagonalDims:
        :param excludedDiagonalTransform:
        :return: list of peaks.
        """

        from ccpnc.peak import Peak as CPeak

        spectrum = self.spectrum
        dataSource = spectrum._apiDataSource
        numDim = dataSource.numDim

        assert fitMethod in PICKINGMETHODS, 'pickPeaksRegion: fitMethod = %s, must be one of ("gaussian", "lorentzian", "parabolic")' % fitMethod
        # method = PICKINGMETHODS.index(fitMethod)

        peaks = []

        if not minLinewidth:
            minLinewidth = [0.0] * numDim

        if not exclusionBuffer:
            exclusionBuffer = [1] * numDim
        else:
            if len(exclusionBuffer) != numDim:
                raise ValueError('Error: pickPeaksRegion, exclusion buffer length must match dimension of spectrum')
            for nDim in range(numDim):
                if exclusionBuffer[nDim] < 1:
                    raise ValueError('Error: pickPeaksRegion, exclusion buffer must contain values >= 1')

        nonAdj = 1 if checkAllAdjacent else 0

        if not excludedRegions:
            excludedRegions = []

        if not excludedDiagonalDims:
            excludedDiagonalDims = []

        if not excludedDiagonalTransform:
            excludedDiagonalTransform = []

        posLevel = spectrum.positiveContourBase if doPos else None
        negLevel = spectrum.negativeContourBase if doNeg else None
        if posLevel is None and negLevel is None:
            return peaks

        # find the regions from the spectrum
        foundRegions = self.spectrum.getRegionData(exclusionBuffer, **regionToPick)

        for region in foundRegions:
            dataArray, intRegion, \
            startPoints, endPoints, \
            startPointBufferActual, endPointBufferActual, \
            startPointIntActual, numPointInt, \
            startPointBuffer, endPointBuffer = region

            if dataArray.size:

                # # testing - plot the dataArray during debugging
                # import numpy as np
                # from mpl_toolkits import mplot3d
                # import matplotlib.pyplot as plt
                #
                # fig = plt.figure(figsize=(10, 8), dpi=100)
                # ax = fig.gca(projection='3d')
                #
                # shape = dataArray.shape
                # rr = (np.max(dataArray) - np.min(dataArray)) * 100
                #
                # from ccpn.ui.gui.lib.GuiSpectrumViewNd import _getLevels
                # posLevels = _getLevels(spectrum.positiveContourCount, spectrum.positiveContourBase,
                #                             spectrum.positiveContourFactor)
                # posLevels = np.array(posLevels)
                #
                # dims = []
                # for ii in shape:
                #     dims.append(np.linspace(0, ii-1, ii))
                #
                # for ii in range(shape[0]):
                #     try:
                #         ax.contour(dims[2], dims[1], dataArray[ii] / rr, posLevels / rr, offset=(shape[0]-ii-1), cmap=plt.cm.viridis)
                #     except Exception as es:
                #         pass                    # trap stupid plot error
                #
                # ax.legend()
                # ax.set_xlim3d(-0.1, shape[2]-0.9)
                # ax.set_ylim3d(-0.1, shape[1]-0.9)
                # ax.set_zlim3d(-0.1, shape[0]-0.9)
                # # plt.show() is at the bottom of function

                # find new peaks

                # exclusion code copied from Nmr/PeakList.py
                excludedRegionsList = [numpy.array(excludedRegion, dtype='float32') - startPointBuffer for excludedRegion in excludedRegions]
                excludedDiagonalDimsList = []
                excludedDiagonalTransformList = []
                for n in range(len(excludedDiagonalDims)):
                    dim1, dim2 = excludedDiagonalDims[n]
                    a1, a2, b12, d = excludedDiagonalTransform[n]
                    b12 += a1 * startPointBuffer[dim1] - a2 * startPointBuffer[dim2]
                    excludedDiagonalDimsList.append(numpy.array((dim1, dim2), dtype='int32'))
                    excludedDiagonalTransformList.append(numpy.array((a1, a2, b12, d), dtype='float32'))

                doPos = posLevel is not None
                doNeg = negLevel is not None
                posLevel = posLevel or 0.0
                negLevel = negLevel or 0.0

                # Note: requires an exclusionBuffer of 1 in all axis directions
                peakPoints = CPeak.findPeaks(dataArray, doNeg, doPos,
                                             negLevel, posLevel, exclusionBuffer,
                                             nonAdj, minDropfactor, minLinewidth,
                                             excludedRegionsList, excludedDiagonalDimsList, excludedDiagonalTransformList)

                peakPoints = [(numpy.array(position), height) for position, height in peakPoints]

                # only keep those points which are inside original region, not extended region
                peakPoints = [(position, height) for position, height in peakPoints if
                              ((startPoints - startPointIntActual) <= position).all() and (position < (endPoints - startPointIntActual)).all()]

                # check new found positions against existing ones
                existingPositions = []
                for apiPeak in self._wrappedData.peaks:
                    position = numpy.array([peakDim.position for peakDim in apiPeak.sortedPeakDims()])  # ignores aliasing
                    existingPositions.append(position - 1)  # -1 because API position starts at 1

                # NB we can not overwrite exclusionBuffer, because it may be used as a parameter in redoing
                # and 'if not exclusionBuffer' does not work on numpy arrays.
                numpyExclusionBuffer = numpy.array(exclusionBuffer)

                validPeakPoints = []
                for thisPeak in peakPoints:

                    position, height = thisPeak

                    position += startPointBufferActual

                    for existingPosition in existingPositions:
                        delta = abs(existingPosition - position)

                        # TODO:ED changed to '<='
                        if (delta <= numpyExclusionBuffer).all():
                            break
                    else:
                        validPeakPoints.append(thisPeak)

                allPeaksArray = None
                allRegionArrays = []
                regionArray = None

                # can I divide the peaks into subregions to make the solver more stable?

                for position, height in validPeakPoints:

                    position -= startPointBufferActual
                    numDim = len(position)

                    # get the region containing this point
                    firstArray = numpy.maximum(position - 2, 0)
                    lastArray = numpy.minimum(position + 3, numPointInt)
                    localRegionArray = numpy.array((firstArray, lastArray))
                    localRegionArray = localRegionArray.astype('int32')

                    # get the larger regionArray size containing all points so far
                    firstArray = numpy.maximum(position - 3, 0)
                    lastArray = numpy.minimum(position + 4, numPointInt)
                    if regionArray is not None:
                        firstArray = numpy.minimum(firstArray, regionArray[0])
                        lastArray = numpy.maximum(lastArray, regionArray[1])

                    peakArray = position.reshape((1, numDim))
                    peakArray = peakArray.astype('float32')
                    firstArray = firstArray.astype('int32')
                    lastArray = lastArray.astype('int32')
                    regionArray = numpy.array((firstArray, lastArray))

                    if allPeaksArray is None:
                        allPeaksArray = peakArray
                    else:
                        allPeaksArray = numpy.append(allPeaksArray, peakArray, axis=0)
                    allRegionArrays.append(localRegionArray)

                if allPeaksArray is not None:

                    # parabolic - generate all peaks in one operation
                    result = CPeak.fitParabolicPeaks(dataArray, regionArray, allPeaksArray)

                    for height, centerGuess, linewidth in result:
                        center = numpy.array(centerGuess)

                        position = center + startPointBufferActual
                        peak = self._newPickedPeak(pointPositions=position, height=height,
                                                   lineWidths=linewidth, fitMethod=fitMethod)
                        peaks.append(peak)

                    if fitMethod != PARABOLICMETHOD:
                        self.fitExistingPeaks(peaks, fitMethod=fitMethod, singularMode=True)

                    # else:
                    #
                    # # result = CPeak.fitPeaks(dataArray, regionArray, allPeaksArray, method)
                    # result = CPeak.fitParabolicPeaks(dataArray, regionArray, allPeaksArray)
                    #
                    # for height, centerGuess, linewidth in result:
                    #
                    #     # clip the point to the exclusion area, to stop rogue peaks
                    #     # center = numpy.array(centerGuess).clip(min=position - numpyExclusionBuffer,
                    #     #                                        max=position + numpyExclusionBuffer)
                    #     center = numpy.array(centerGuess)
                    #
                    #     # outofPlaneMinTest = numpy.array([])
                    #     # outofPlaneMaxTest = numpy.array([])
                    #     # for ii in range(numDim):
                    #     #     outofPlaneMinTest = numpy.append(outofPlaneMinTest, 0.0)
                    #     #     outofPlaneMaxTest = numpy.append(outofPlaneMaxTest, dataArray.shape[numDim-ii-1]-1.0)
                    #     #
                    #     # # check whether the new peak is outside of the current plane
                    #     # outofPlaneCenter = numpy.array(centerGuess).clip(min=position - numpy.array(outofPlaneMinTest),
                    #     #                      max=position + numpy.array(outofPlaneMaxTest))
                    #     #
                    #     # print(">>>", center, outofPlaneCenter, not numpy.array_equal(center, outofPlaneCenter))
                    #
                    #     # ax.scatter(*center, c='r', marker='^')
                    #     #
                    #     # x2, y2, _ = mplot3d.proj3d.proj_transform(1, 1, 1, ax.get_proj())
                    #     #
                    #     # ax.text(*center, str(center), fontsize=12)
                    #
                    #     # except Exception as es:
                    #     #     print('>>>error:', str(es))
                    #     #     dimCount = len(startPoints)
                    #     #     height = float(dataArray[tuple(position[::-1])])
                    #     #     # have to reverse position because dataArray backwards
                    #     #     # have to float because API does not like numpy.float32
                    #     #     center = position
                    #     #     linewidth = dimCount * [None]
                    #
                    #     position = center + startPointBufferActual
                    #
                    #     peak = self._newPickedPeak(pointPositions=position, height=height,
                    #                                lineWidths=linewidth, fitMethod=fitMethod)
                    #     peaks.append(peak)
                    #
            # plt.show()

        return peaks

    def fitExistingPeaks(self, peaks: Sequence['Peak'], fitMethod: str = GAUSSIANMETHOD, singularMode=True):
        """Refit the current selected peaks.
        Must be called with opeaks that belong to this peakList
        """

        from ccpnc.peak import Peak as CPeak

        assert fitMethod in PICKINGMETHODS, 'pickPeaksRegion: fitMethod = %s, must be one of ("gaussian", "lorentzian", "parabolic")' % fitMethod
        method = PICKINGMETHODS.index(fitMethod)

        allPeaksArray = None
        allRegionArrays = []
        regionArray = None

        badPeaks = [peak for peak in peaks if peak.peakList is not self]
        if badPeaks:
            raise ValueError('List contains peaks that are not in the same peakList.')

        for peak in peaks:

            peak = peak._wrappedData

            dataSource = peak.peakList.dataSource
            numDim = dataSource.numDim
            dataDims = dataSource.sortedDataDims()

            peakDims = peak.sortedPeakDims()

            # generate a numpy array with the position of the peak in points rounded to integers
            position = [peakDim.position - 1 for peakDim in peakDims]  # API position starts at 1
            position = numpy.round(numpy.array(position))

            # generate a numpy array with the number of points per dimension
            numPoints = [peakDim.dataDim.numPoints for peakDim in peakDims]
            numPoints = numpy.array(numPoints)

            # consider for each dimension on the interval [point-3,point+4>, account for min and max
            # of each dimension
            if fitMethod == PARABOLICMETHOD or singularMode is True:
                firstArray = numpy.maximum(position - 2, 0)
                lastArray = numpy.minimum(position + 3, numPoints)
            else:
                # extra plane in each direction increases accuracy of group fitting
                firstArray = numpy.maximum(position - 3, 0)
                lastArray = numpy.minimum(position + 4, numPoints)

            # Cast to int for subsequent call
            firstArray = firstArray.astype('int32')
            lastArray = lastArray.astype('int32')
            localRegionArray = numpy.array((firstArray, lastArray), dtype=numpy.int32)

            if regionArray is not None:
                firstArray = numpy.minimum(firstArray, regionArray[0])
                lastArray = numpy.maximum(lastArray, regionArray[1])

            # peakArray = (position - firstArray).reshape((1, numDim))
            peakArray = position.reshape((1, numDim))
            peakArray = peakArray.astype('float32')
            regionArray = numpy.array((firstArray, lastArray), dtype=numpy.int32)

            if allPeaksArray is None:
                allPeaksArray = peakArray
            else:
                allPeaksArray = numpy.append(allPeaksArray, peakArray, axis=0)
            allRegionArrays.append(localRegionArray)

        if allPeaksArray is not None and allPeaksArray.size != 0:

            # map to (0, 0)
            regionArray = numpy.array((firstArray - firstArray, lastArray - firstArray))

            # Get the data; note that arguments has to be castable to int?
            dataArray, intRegion = dataSource.getRegionData(firstArray, lastArray)

            # update positions relative to the corner of the data array
            firstArray = firstArray.astype('float32')
            updatePeaksArray = None
            for pk in allPeaksArray:
                if updatePeaksArray is None:
                    updatePeaksArray = pk - firstArray
                    updatePeaksArray = updatePeaksArray.reshape((1, numDim))
                    updatePeaksArray = updatePeaksArray.astype('float32')
                else:
                    pk = pk-firstArray
                    pk = pk.reshape((1, numDim))
                    pk = pk.astype('float32')
                    updatePeaksArray = numpy.append(updatePeaksArray, pk, axis=0)

            try:
                result = ()
                if fitMethod == PARABOLICMETHOD:

                    # parabolic - generate all peaks in one operation
                    result = CPeak.fitParabolicPeaks(dataArray, regionArray, updatePeaksArray)

                else:
                    # currently gaussian or lorentzian
                    if singularMode is True:

                        # fit peaks individually
                        for peakArray, localRegionArray in zip(allPeaksArray, allRegionArrays):
                            peakArray = peakArray - firstArray
                            peakArray = peakArray.reshape((1, numDim))
                            peakArray = peakArray.astype('float32')
                            localRegionArray = numpy.array((localRegionArray[0] - firstArray, localRegionArray[1] - firstArray), dtype=numpy.int32)

                            localResult = CPeak.fitPeaks(dataArray, localRegionArray, peakArray, method)
                            result += tuple(localResult)
                    else:

                        # fit all peaks in one operation
                        result = CPeak.fitPeaks(dataArray, regionArray, updatePeaksArray, method)

            except CPeak.error as e:

                # there could be some fitting error
                getLogger().warning("Aborting peak fit, Error for peak: %s:\n\n%s " % (peak, e))
                return

            for pkNum, peak in enumerate(peaks):
                height, center, linewidth = result[pkNum]

                # work on the _wrappedData
                peak = peak._wrappedData
                peakDims = peak.sortedPeakDims()

                dataSource = peak.peakList.dataSource
                numDim = dataSource.numDim
                dataDims = dataSource.sortedDataDims()

                for i, peakDim in enumerate(peakDims):
                    # peakDim.position = position[i] + 1  # API position starts at 1

                    newPos = min(max(center[i], 0.5), dataArray.shape[i]-1.5)

                    # ignore if out of range
                    if abs(newPos - center[i]) < 1e-9:
                        peakDim.position = center[i] + firstArray[i] + 1.0  # API position starts at 1
                    peakDim.lineWidth = dataDims[i].valuePerPoint * linewidth[i]

                peak.height = dataSource.scale * height

    # if allPeaksArray is not None:
    #
    #     result = []
    #     if method == PICKINGMETHODS[2]:
    #
    #         # parabolic - generate all peaks in one operation
    #         result = CPeak.fitParabolicPeaks(dataArray, regionArray, allPeaksArray)
    #
    #     else:
    #
    #         # currently gaussian or lorentzian
    #         if peakFittingMethod == SINGULAR_FIT:
    #
    #         # fit peaks individually
    #
    #         else:
    #
    #             # fit all peaks in one operation
    #             result = CPeak.fitPeaks(dataArray, regionArray, allPeaksArray, method)
    #
    #     for height, centerGuess, linewidth in result:
    #         center = numpy.array(centerGuess)
    #
    #         position = center + startPointBufferActual
    #         peak = self._newPickedPeak(pointPositions=position, height=height,
    #                                    lineWidths=linewidth, fitMethod=fitMethod)
    #         peaks.append(peak)

    #===========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================

    @logCommand(get='self')
    def newPeak(self, ppmPositions: Sequence[float] = (), height: float = None,
                comment: str = None, **kwds):
        """Create a new Peak within a peakList.

        See the Peak class for details.

        Optional keyword arguments can be passed in; see Peak._newPeak for details.

        NB you must create the peak before you can assign it. The assignment attributes are:
        - assignments (assignedNmrAtoms) - A tuple of all (e.g.) assignment triplets for a 3D spectrum
        - assignmentsByDimensions (dimensionNmrAtoms) - A tuple of tuples of assignments, one for each dimension

        :param ppmPositions: peak position in ppm for each dimension (related attributes: positionError, pointPosition)
        :param height: height of the peak (related attributes: volume, volumeError, lineWidths)
        :param comment: optional comment string
        :return: a new Peak instance.
        """
        from ccpn.core.Peak import _newPeak  # imported here to avoid circular imports

        if height is None:
            height = self.spectrum.getHeight(ppmPositions)
        return _newPeak(self, ppmPositions=ppmPositions, height=height, comment=comment, **kwds)

    @logCommand(get='self')
    def _newPickedPeak(self, pointPositions: Sequence[float] = None, height: float = None,
                       lineWidths: Sequence[float] = (), fitMethod: str = PARABOLICMETHOD, **kwds):
        """Create a new Peak within a peakList from a picked peak

        See the Peak class for details.

        Optional keyword arguments can be passed in; see Peak._newPickedPeak for details.

        :param height: height of the peak (related attributes: volume, volumeError, lineWidths)
        :param pointPositions: peak position in points for each dimension (related attributes: positionError, pointPosition)
        :param fitMethod: type of curve fitting
        :param lineWidths:
        :param serial: optional serial number.
        :return: a new Peak instance.
        """
        from ccpn.core.Peak import _newPickedPeak  # imported here to avoid circular imports

        return _newPickedPeak(self, pointPositions=pointPositions, height=height,
                              lineWidths=lineWidths, fitMethod=fitMethod, **kwds)


#=========================================================================================
# Connections to parents:
#=========================================================================================

@newObject(PeakList)
def _newPeakList(self: Spectrum, title: str = None, comment: str = None,
                 isSimulated: bool = False, symbolStyle: str = None, symbolColour: str = None,
                 textColour: str = None, serial: int = None) -> PeakList:
    """Create new empty PeakList within Spectrum

    See the PeakList class for details.

    :param title:
    :param comment:
    :param isSimulated:
    :param symbolStyle:
    :param symbolColour:
    :param textColour:
    :param serial: optional serial number.
    :return: a new PeakList instance.
    """

    dd = {'name': title, 'details': comment, 'isSimulated': isSimulated}
    if symbolColour:
        dd['symbolColour'] = symbolColour
    if symbolStyle:
        dd['symbolStyle'] = symbolStyle
    if textColour:
        dd['textColour'] = textColour

    apiDataSource = self._apiDataSource
    apiPeakList = apiDataSource.newPeakList(**dd)
    result = self._project._data2Obj.get(apiPeakList)
    if result is None:
        raise RuntimeError('Unable to generate new PeakList item')

    if serial is not None:
        try:
            result.resetSerial(serial)
        except ValueError:
            self.project._logger.warning("Could not reset serial of %s to %s - keeping original value"
                                         % (result, serial))

    return result

#EJB 20181127: moved to Spectrum
# Spectrum.newPeakList = _newPeakList
# del _newPeakList

# Notifiers:
