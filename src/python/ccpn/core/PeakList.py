"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-03-16 17:29:24 +0000 (Mon, March 16, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
import math
from typing import Sequence, List, Optional
from ccpn.util.Common import percentage
from scipy.ndimage import maximum_filter, minimum_filter
from ccpn.util import Common as commonUtil
from ccpn.core.Spectrum import Spectrum
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import PeakList as ApiPeakList
from ccpn.core.lib.SpectrumLib import _oldEstimateNoiseLevel1D
from ccpnmodel.ccpncore.lib._ccp.nmr.Nmr.PeakList import pickNewPeaks
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, undoBlock, undoBlockWithoutSideBar, notificationEchoBlocking
from ccpn.util.Logging import getLogger
from ccpn.core.PMIListABC import PMIListABC


GAUSSIANMETHOD = 'gaussian'
LORENTZIANMETHOD = 'lorentzian'
PARABOLICMETHOD = 'parabolic'
PICKINGMETHODS = (GAUSSIANMETHOD, LORENTZIANMETHOD, PARABOLICMETHOD)


def _signalToNoiseFunc(noise, signal):
    snr = math.log10(abs(np.mean(signal) ** 2 / np.mean(noise) ** 2))
    return snr


# def _signalToNoiseFunc(noise, signal):
#     snr = math.log10(abs(np.mean(signal) ** 2 / np.mean(noise) ** 2))
#     return snr

# def _estimateSNR1D_OLD(y):
#
#     if y is None: return 0
#     e = _estimateNoiseLevel1D(y)
#     eS = np.where(y >= e)
#     eSN = np.where(y <= -e)
#     eN = np.where((y < e) & (y > -e))
#     estimatedSignalRegionPos = y[eS]
#     estimatedSignalRegionNeg = y[eSN]
#     estimatedSignalRegion = np.concatenate((estimatedSignalRegionPos, estimatedSignalRegionNeg))
#     estimatedNoiseRegion = y[eN]
#     lenghtESR = len(estimatedSignalRegion)
#     lenghtENR = len(estimatedNoiseRegion)
#     if lenghtESR > lenghtENR:
#         l = lenghtENR
#     else:
#         l = lenghtESR
#     if l == 0:
#         return 1
#     else:
#         noise = estimatedNoiseRegion[:l - 1]
#         signalAndNoise = estimatedSignalRegion[:l - 1]
#         signal = abs(signalAndNoise - noise)
#         signal[::-1].sort()  # descending
#         noise[::1].sort()
#         if hasattr(signal, 'compressed') and hasattr(noise, 'compressed'):
#             signal = signal.compressed()  # remove the mask
#             noise = noise.compressed()  # remove the mask
#         s = signal[:int(l / 2)]
#         n = noise[:int(l / 2)]
#         if len(signal) == 0:
#             return 1
#         SNR = _signalToNoiseFunc(n,s)
#         if SNR is not None:
#             return abs(SNR)
#         else:
#             return 1

def estimateSignalRegion(y, nlMax=None, nlMin=None):
    if y is None: return 0
    if nlMax is None or nlMin is None:
        nlMax, nlMin = estimateNoiseLevel1D(y)
    eS = np.where(y >= nlMax)
    eSN = np.where(y <= nlMin)
    eN = np.where((y < nlMax) & (y > nlMin))
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
        return np.array([])
    else:
        noise = estimatedNoiseRegion[:l - 1]
        signalAndNoise = estimatedSignalRegion[:l - 1]
        signal = abs(signalAndNoise - noise)
        signal[::-1].sort()  # descending
        noise[::1].sort()
        if hasattr(signal, 'compressed') and hasattr(noise, 'compressed'):
            signal = signal.compressed()  # remove the mask
            noise = noise.compressed()  # remove the mask
        s = signal[:int(l / 2)]
        n = noise[:int(l / 2)]
        if len(signal) == 0:
            return np.array([])
        else:
            return s


def estimateSNR_1D(noiseLevels, signalPoints, ratio=2.5):
    """

    :param noiseLevels: (max, min) floats
    :param signalPoints: iterable of floats estimated to be signal or peak heights
    :param ratio: default 2.5
    :return: array of snr for each point compared to the delta noise level
    """
    maxNL = max(noiseLevels)
    minNL = min(noiseLevels)
    dd = abs(maxNL - minNL)
    pp = np.array([s for s in signalPoints])
    if dd != 0 and dd is not None:
        snRatios = (ratio * pp) / dd
        return snRatios
    print('Failed to estimate SNR')
    return [None] * len(signalPoints)


def estimateNoiseLevel1D(y, f=10, stdFactor=0.5):
    """

    :param y: the y region of the spectrum.
    :param f: percentage of the spectrum to use. If given a portion known to be just noise, set it to 100.
    :param increaseBySTD: increase the estimated by the STD for the y region
    :param stdFactor: 0 to don't adjust the initial guess.
    :return:   (float, float) of estimated noise threshold  as max and min
    """

    eMax, eMin = 0, 0
    if stdFactor == 0:
        stdFactor = 0.01
        getLogger().warning('stdFactor of value zero is not allowed.')
    if y is None:
        return eMax, eMin
    percent = percentage(f, int(len(y)))
    fy = y[:int(percent)]

    stdValue = np.std(fy) * stdFactor

    eMax = np.max(fy) + stdValue
    eMin = np.min(fy) - stdValue
    return eMax, eMin


# def _estimateNoiseLevel1D_gaussian(y, f=5):
#     '''
#     Estimates the noise threshold based on the max intensity of the first portion of the spectrum where
#     only noise is present. To increase the threshold value: increase the factor.
#     return:  float of estimated noise threshold and Signal to Noise Ratio
#     '''
#     nl = 0
#     if y is None:
#         return nl
#     nls = []
#     for i in range(10): #reapet in a range to reduce the variability of the estimated gaussian values
#         percent = percentage(f, int(len(y)))
#         nl = np.std(y[:int(percent)]) # ! this can be out of bounds
#         estimatedGaussian = np.random.normal(size=y.shape) * nl
#         if len(estimatedGaussian)==0: return nl
#         eG = np.max(estimatedGaussian) + np.min(estimatedGaussian[estimatedGaussian>=0])
#         if nl < eG:
#             nl = eG
#         nls.append(nl)
#     if len(nls)>0:
#         nl = np.min(nls)
#     return nl

def _filterROI1Darray(x, y, roi):
    """ Return region included in the ROI ppm position"""
    mask = (x > max(roi)) | (x > min(roi))
    return x[mask], y[mask]


def _filtered1DArray(data, ignoredRegions):
    # returns an array without ignoredRegions. Used for automatic 1d peak picking
    ppmValues = data[0]
    masks = []
    ignoredRegions = [sorted(pair, reverse=True) for pair in ignoredRegions]
    for region in ignoredRegions:
        mask = (ppmValues > region[0]) | (ppmValues < region[1])
        masks.append(mask)
    fullmask = [all(mask) for mask in zip(*masks)]
    newArray = (np.ma.MaskedArray(data, mask=np.logical_not((fullmask, fullmask))))
    return newArray


class PeakList(PMIListABC):
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

    #=========================================================================================
    # CCPN properties
    #=========================================================================================

    @property
    def _apiPeakList(self) -> ApiPeakList:
        """API peakLists matching PeakList."""
        return self._wrappedData

    def _setPrimaryChildClass(self):
        """Set the primary classType for the child list attached to this container
        """
        from ccpn.core.Peak import Peak as klass

        if not klass in self._childClasses:
            raise TypeError('PrimaryChildClass %s does not exist as child of %s' % (klass.className,
                                                                                    self.className))
        self._primaryChildClass = klass

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
                    fitMethod: str = GAUSSIANMETHOD, excludedRegions=None,
                    excludedDiagonalDims=None, excludedDiagonalTransform=None,
                    minDropFactor: float = 0.1):

        # TODO NBNB Add doc string and put type annotation on all parameters

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
                                    excludedDiagonalTransform=excludedDiagonalTransform, minDropfactor=minDropFactor)

        data2ObjDict = self._project._data2Obj
        result = [data2ObjDict[apiPeak] for apiPeak in apiPeaks]
        # for peak in result:
        #     peak._finaliseAction('create')

        return result

    def pickPeaks1d(self, dataRange, intensityRange=None, size: int = 3, mode: str = 'wrap') -> List['Peak']:
        """
        Pick 1D peaks from a dataRange
        """
        from ccpn.core.lib.peakUtils import simple1DPeakPicker
        from ccpn.ui.gui.widgets.MessageDialog import _stoppableProgressBar
        from ccpn.ui.gui.widgets.MessageDialog import showYesNoWarning
        # maxValues, minValues = simple1DPeakPicker(y=filteredY, x=filteredX, delta=maxNoiseLevel + deltaAdjustment,
        #                                           negative=False)
        with undoBlockWithoutSideBar():
            with notificationEchoBlocking():

                if dataRange[0] < dataRange[1]:
                    dataRange[0], dataRange[1] = dataRange[1], dataRange[0]
                # code below assumes that dataRange[1] > dataRange[0]
                peaks = []
                spectrum = self.spectrum
                # data1d = spectrum._apiDataSource.get1dSpectrumData()
                data1d = np.array([self.spectrum.positions, self.spectrum.intensities])
                selectedData = data1d[:, (data1d[0] < dataRange[0]) * (data1d[0] > dataRange[1])]

                if selectedData.size == 0:
                    return peaks
                x,y = selectedData

                maxFilter = maximum_filter(selectedData[1], size=size, mode=mode)
                boolsMax = selectedData[1] == maxFilter
                indices = np.argwhere(boolsMax)

                minFilter = minimum_filter(selectedData[1], size=size, mode=mode)
                boolsMin = selectedData[1] == minFilter
                negBoolsPeak = boolsMin
                indicesMin = np.argwhere(negBoolsPeak)

                fullIndices = np.append(indices, indicesMin)  # True positional indices
                values = []
                for position in fullIndices:
                    peakPosition = [float(selectedData[0][position])]
                    height = selectedData[1][position]
                    if intensityRange is None or intensityRange[0] <= height <= intensityRange[1]:
                        values.append((float(height), peakPosition), )
                found = len(values)
                if found > 10:
                    title = 'Found %s peaks on %s'% (found, self.spectrum.name)
                    msg = 'Do you want continue? \n\n\n\nTo filter out more peaks: Increase the peak factor from preferences:' \
                          '\nProject > Preferences... > Spectrum > 1D Peak Picking Factor.\nAlso, try to select above the noise region'

                    proceed = showYesNoWarning(title, msg)
                    if not proceed:
                        return []
                for height, position in _stoppableProgressBar(values):
                    peaks.append(self.newPeak(height=float(height), ppmPositions=position))

            return peaks

    @logCommand(get='self')
    def pickPeaks1dFiltered(self, size: int = 9, mode: str = 'wrap', factor=10, excludeRegions=None,
                            positiveNoiseThreshold=None, negativeNoiseThreshold=None, negativePeaks=True,stdFactor=0.5):
        """
        Pick 1D peaks from data in self.spectrum.
        """
        with undoBlock():
            if excludeRegions is None:
                excludeRegions = [[-20.1, -19.1]]
            excludeRegions = [sorted(pair, reverse=True) for pair in excludeRegions]
            peaks = []
            spectrum = self.spectrum
            # data = spectrum._apiDataSource.get1dSpectrumData()
            data = np.array([spectrum.positions, spectrum.intensities])
            ppmValues = data[0]
            estimateNoiseLevel1D(spectrum.intensities, f=factor, stdFactor=0.5)

            if positiveNoiseThreshold == 0.0 or positiveNoiseThreshold is None:
                positiveNoiseThreshold,negativeNoiseThreshold = estimateNoiseLevel1D(spectrum.intensities,
                                                                             f=factor, stdFactor=stdFactor)
            spectrum.noiseLevel = positiveNoiseThreshold
            spectrum.negativeNoiseLevel = negativeNoiseThreshold
            #     positiveNoiseThreshold = _oldEstimateNoiseLevel1D(spectrum.intensities, factor=factor)
            #     if spectrum.noiseLevel is None:
            #         positiveNoiseThreshold = _oldEstimateNoiseLevel1D(spectrum.intensities, factor=factor)
            #         negativeNoiseThreshold = -positiveNoiseThreshold
            #
            # if negativeNoiseThreshold == 0.0 or negativeNoiseThreshold is None:
            #     negativeNoiseThreshold = _oldEstimateNoiseLevel1D(spectrum.intensities, factor=factor)
            #     if spectrum.noiseLevel is None:
            #         negativeNoiseThreshold = -positiveNoiseThreshold

            masks = []
            for region in excludeRegions:
                mask = (ppmValues > region[0]) | (ppmValues < region[1])
                masks.append(mask)
            fullmask = [all(mask) for mask in zip(*masks)]
            newArray2 = (np.ma.MaskedArray(data, mask=np.logical_not((fullmask, fullmask))))

            if (newArray2.size == 0) or (data.max() < positiveNoiseThreshold):
                return peaks

            posBoolsVal = newArray2[1] > positiveNoiseThreshold
            maxFilter = maximum_filter(newArray2[1], size=size, mode=mode)
            boolsMax = newArray2[1] == maxFilter
            boolsPeak = posBoolsVal & boolsMax
            indices = np.argwhere(boolsPeak)

            snr_ratios = []
            if negativePeaks:
                minFilter = minimum_filter(data[1], size=size, mode=mode)
                boolsMin = newArray2[1] == minFilter
                negBoolsVal = newArray2[1] < negativeNoiseThreshold
                negBoolsPeak = negBoolsVal & boolsMin
                indicesMin = np.argwhere(negBoolsPeak)
                indices = np.append(indices, indicesMin)

            for position in indices:
                peakPosition = [float(newArray2[0][position])]
                height = newArray2[1][position]
                peak = self.newPeak(height=float(height), ppmPositions=peakPosition)
                snr = peak._getSNRatio()
                snr_ratios.append(snr)
                peaks.append(peak)
            spectrum._snr = np.mean(snr_ratios)
        return peaks

    def _noiseLineWidth(self):
        from ccpn.core.IntegralList import _getPeaksLimits

        x, y = np.array(self.spectrum.positions), np.array(self.spectrum.intensities)
        x, y = x[:int(len(x) / 20)], y[:int(len(x) / 20)],
        noiseMean = np.mean(y)
        intersectingLine = [noiseMean] * len(x)
        limitsPairs = _getPeaksLimits(x, y, intersectingLine)
        widths = [0]
        for i in limitsPairs:
            lineWidth = abs(i[0] - i[1])
            widths.append(lineWidth)
        return np.std(widths)

    @logCommand(get='self')
    def estimateVolumes(self, volumeIntegralLimit=2.0):
        """Estimate the volumes for the peaks in this peakList
        The width of the volume integral in each dimension is the lineWidth * volumeIntegralLimit,
        the default is 2.0 * FWHM of the peak.
        :param volumeIntegralLimit: integral width as a multiple of lineWidth (FWHM)
        """
        with undoBlockWithoutSideBar():
            for pp in self.peaks:
                # estimate the volume for each peak
                height = pp.height
                lineWidths = pp.lineWidths
                if lineWidths and None not in lineWidths and height:
                    pp.estimateVolume(volumeIntegralLimit=volumeIntegralLimit)
                else:
                    getLogger().warning('Peak %s contains undefined height/lineWidths' % str(pp))

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
    #     x,y = np.array(self.spectrum.positions), np.array(self.spectrum.intensities)
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
    #     ratio = np.std(abs(filteredArray[1])) / noiseThreshold
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
    #     indices = np.argwhere(boolsPeak)
    #
    #     if negativePeaks:
    #       minFilter = minimum_filter(filteredArray[1], size=size, mode='wrap')
    #       boolsMin = filteredArray[1] == minFilter
    #       negBoolsVal = filteredArray[1] < -noiseThreshold
    #       negBoolsPeak = negBoolsVal & boolsMin
    #       indicesMin = np.argwhere(negBoolsPeak)
    #       indices = np.append(indices, indicesMin)
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
    #           region = np.where((x <= limits[0]) & (x >= limits[1]))
    #           integral = trapz(y[region])
    #           peak = self.newPeak(height=peakHeigh, ppmPositions=peakPos, volume=float(integral),
    #                               lineWidths=[lw,])
    #           newIntegral = integralList.newIntegral(limits=[[min(limits), max(limits)]])
    #           newIntegral.peak = peak
    #           newIntegral.baseline = noiseThreshold
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
    #         region = np.where((x <= newMax) & (x >= newMin))
    #         integral = trapz(region)
    #         peak = self.newPeak(height=peakHeight, ppmPositions=peakPos, volume=float(integral),
    #                             )
    #         newIntegral = integralList.newIntegral(limits=[[newMin,newMax]])
    #         newIntegral.peak = peak
    #         newIntegral.baseline = noiseThreshold
    #
    #     self.spectrum.signalToNoiseRatio = SNR
    #
    #   finally:
    #     self._endCommandEchoBlock()
    #
    #   return peaks

    # from ccpn.util.decorators import profile
    # @profile
    def peakFinder1D(self, maxNoiseLevel=None, minNoiseLevel=None,
                     ignoredRegions=[[20, 19]], negativePeaks=False,
                     eNoiseThresholdFactor=1.5,
                     recalculateSNR = True,
                     deltaPercent=10,
                     useXRange=10):
        from ccpn.core.lib.peakUtils import simple1DPeakPicker
        from ccpn.core.lib.ContextManagers import undoBlock, undoBlockWithoutSideBar, notificationEchoBlocking
        from ccpn.core.lib.SpectrumLib import _estimate1DSpectrumSNR
        peaks = []
        with undoBlockWithoutSideBar():
            with notificationEchoBlocking():
                spectrum = self.spectrum

                x, y = spectrum.positions, spectrum.intensities
                masked = _filtered1DArray(np.array([x, y]), ignoredRegions)
                filteredX, filteredY = masked[0].compressed(), masked[1].compressed()
                if maxNoiseLevel is None or minNoiseLevel is None:
                    maxNoiseLevel, minNoiseLevel = estimateNoiseLevel1D(y, f=useXRange, stdFactor=eNoiseThresholdFactor)
                    spectrum.noiseLevel = float(maxNoiseLevel)
                    spectrum.negativeNoiseLevel = float(minNoiseLevel)
                deltaAdjustment = percentage(deltaPercent, maxNoiseLevel)
                maxValues, minValues = simple1DPeakPicker(y=filteredY, x=filteredX, delta=maxNoiseLevel + deltaAdjustment, negDelta=minNoiseLevel + deltaAdjustment, negative=negativePeaks)
                spectrum.noiseLevel = float(maxNoiseLevel)
                spectrum.negativeNoiseLevel = float(minNoiseLevel)
                snr_ratios = []

                for position, height in maxValues:
                    peak = self.newPeak(ppmPositions=[position], height=height)
                    snr = peak._getSNRatio()
                    snr_ratios.append(snr)
                    peaks.append(peak)
                if negativePeaks:
                    for position, height in minValues:
                        peak = self.newPeak(ppmPositions=[position], height=height)
                        snr = peak._getSNRatio()
                        snr_ratios.append(snr)
                        peaks.append(peak)
                if recalculateSNR:
                    spectrum._snr = np.mean(snr_ratios)
                    if math.isnan(spectrum._snr):  #estimate from the std of all y points
                        print("SNR from Peaks is None. Using the STD of spectrum intensities" )
                        spectrum._snr = _estimate1DSpectrumSNR(spectrum)
        return peaks


    @logCommand(get='self')
    def copyTo(self, targetSpectrum: Spectrum, **kwargs) -> 'PeakList':
        """Make (and return) a copy of the PeakList attached to targetSpectrum.

        Peaklist attributes can be passed in as keyword arguments"""

        singleValueTags = ['isSimulated', 'symbolColour', 'symbolStyle', 'textColour', 'textColour',
                           'title', 'comment']

        targetSpectrum = self.project.getByPid(targetSpectrum) if isinstance(targetSpectrum, str) else targetSpectrum
        if not targetSpectrum:
            raise TypeError('targetSpectrum not defined')
        if not isinstance(targetSpectrum, Spectrum):
            raise TypeError('targetSpectrum is not of type Spectrum')

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

        with undoBlock():
            newPeakList = targetSpectrum.newPeakList(**params)
            # newPeakList.symbolColour = targetSpectrum.positiveContourColour
            # newPeakList.textColour = targetSpectrum.positiveContourColour
            for peak in self.peaks:
                peak.copyTo(newPeakList)
        #
        return newPeakList

    @logCommand(get='self')
    def subtractPeakLists(self, peakList: 'PeakList') -> 'PeakList':
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

        peakList = self.project.getByPid(peakList) if isinstance(peakList, str) else peakList
        if not peakList:
            raise TypeError('peakList not defined')
        if not isinstance(peakList, PeakList):
            raise TypeError('peakList is not of type PeakList')

        # with logCommandBlock(prefix='newPeakList=', get='self') as log:
        #     peakStr = '[' + ','.join(["'%s'" % peak.pid for peak in peakList2]) + ']'
        #     log('subtractPeakLists', peaks=peakStr)

        with undoBlock():
            spectrum = self.spectrum

            assert spectrum is peakList.spectrum, 'For now requires both peak lists to be in same spectrum'

            # dataDims = spectrum.sortedDataDims()
            tolerances = self.spectrum.assignmentTolerances

            peaks2 = peakList.peaks
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

    @logCommand(get='self')
    def restrictedPick(self, positionCodeDict, doPos, doNeg):

        codes = list(positionCodeDict.keys())
        positions = [positionCodeDict[code] for code in codes]

        # match the spectrum to the restricted codes, these are the only ones to update
        indices = commonUtil.getAxisCodeMatchIndices(self.spectrum.axisCodes, codes)

        # divide by 2 to get the double-width tolerance, i.e. the width of the region - CHECK WITH GEERTEN
        tolerances = tuple(tol / 2 for tol in self.spectrum.assignmentTolerances)

        limits = self.spectrum.spectrumLimits
        selectedRegion = []
        minDropFactor = self.project._appBase.preferences.general.peakDropFactor

        with undoBlock():
            for ii, ind in enumerate(indices):
                if ind is not None:
                    selectedRegion.insert(ii, [positions[ind] - tolerances[ii], positions[ind] + tolerances[ii]])
                else:
                    selectedRegion.insert(ii, [limits[ii][0], limits[ii][1]])

            # regionToPick = selectedRegion
            # peaks = self.pickPeaksNd(regionToPick, doPos=doPos, doNeg=doNeg, minDropFactor=minDropFactor)

            axisCodeDict = dict((code, selectedRegion[ii]) for ii, code in enumerate(self.spectrum.axisCodes))
            peaks = self.pickPeaksRegion(axisCodeDict, doPos=doPos, doNeg=doNeg, minDropFactor=minDropFactor)

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

    @logCommand(get='self')
    def pickPeaksRegion(self, regionToPick: dict = {},
                        doPos: bool = True, doNeg: bool = True,
                        minLinewidth=None, exclusionBuffer=None,
                        minDropFactor: float = 0.1, checkAllAdjacent: bool = True,
                        fitMethod: str = PARABOLICMETHOD, excludedRegions=None,
                        excludedDiagonalDims=None, excludedDiagonalTransform=None,
                        estimateLineWidths=True):

        with undoBlock():
            peaks = self._pickPeaksRegion(regionToPick=regionToPick,
                                          doPos=doPos, doNeg=doNeg,
                                          minLinewidth=minLinewidth, exclusionBuffer=exclusionBuffer,
                                          minDropFactor=minDropFactor, checkAllAdjacent=checkAllAdjacent,
                                          fitMethod=fitMethod, excludedRegions=excludedRegions,
                                          excludedDiagonalDims=excludedDiagonalDims, excludedDiagonalTransform=excludedDiagonalTransform,
                                          estimateLineWidths=estimateLineWidths)
        return peaks

    def _pickPeaksRegion(self, regionToPick: dict = {},
                         doPos: bool = True, doNeg: bool = True,
                         minLinewidth=None, exclusionBuffer=None,
                         minDropFactor: float = 0.1, checkAllAdjacent: bool = True,
                         fitMethod: str = PARABOLICMETHOD, excludedRegions=None,
                         excludedDiagonalDims=None, excludedDiagonalTransform=None,
                         estimateLineWidths=True):
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
        :param minDropFactor: float defined on [0.0, 1.0] default is 0.1
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
        assert (minDropFactor >= 0.0) and (minDropFactor <= 1.0), 'pickPeaksRegion: minDropFactor %f not in range [0.0, 1.0]' % minDropFactor
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

        # find the regions from the spectrum - sometimes returning None which gives an error
        foundRegions = self.spectrum.getRegionData(exclusionBuffer, **regionToPick)

        if not foundRegions:
            return peaks

        for region in foundRegions:
            if not region:
                continue

            dataArray, intRegion, \
            startPoints, endPoints, \
            startPointBufferActual, endPointBufferActual, \
            startPointIntActual, numPointInt, \
            startPointBuffer, endPointBuffer = region

            if dataArray.size:

                # # 20191004:ED testing - plot the dataArray during debugging
                # import np as np
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
                excludedRegionsList = [np.array(excludedRegion, dtype=np.float32) - startPointBuffer for excludedRegion in excludedRegions]
                excludedDiagonalDimsList = []
                excludedDiagonalTransformList = []
                for n in range(len(excludedDiagonalDims)):
                    dim1, dim2 = excludedDiagonalDims[n]
                    a1, a2, b12, d = excludedDiagonalTransform[n]
                    b12 += a1 * startPointBuffer[dim1] - a2 * startPointBuffer[dim2]
                    excludedDiagonalDimsList.append(np.array((dim1, dim2), dtype=np.int32))
                    excludedDiagonalTransformList.append(np.array((a1, a2, b12, d), dtype=np.float32))

                doPos = posLevel is not None
                doNeg = negLevel is not None
                posLevel = posLevel or 0.0
                negLevel = negLevel or 0.0

                # print('>>dataArray', dataArray)
                # Note: requires an exclusionBuffer of 1 in all axis directions
                peakPoints = CPeak.findPeaks(dataArray, doNeg, doPos,
                                             negLevel, posLevel, exclusionBuffer,
                                             nonAdj, minDropFactor, minLinewidth,
                                             excludedRegionsList, excludedDiagonalDimsList, excludedDiagonalTransformList)

                peakPoints = [(np.array(position), height) for position, height in peakPoints]

                # only keep those points which are inside original region, not extended region
                peakPoints = [(position, height) for position, height in peakPoints if
                              ((startPoints - startPointIntActual) <= position).all() and (position < (endPoints - startPointIntActual)).all()]

                # check new found positions against existing ones
                existingPositions = []
                for apiPeak in self._wrappedData.peaks:
                    position = np.array([peakDim.position for peakDim in apiPeak.sortedPeakDims()])  # ignores aliasing
                    existingPositions.append(position - 1)  # -1 because API position starts at 1

                # NB we can not overwrite exclusionBuffer, because it may be used as a parameter in redoing
                # and 'if not exclusionBuffer' does not work on np arrays.
                npExclusionBuffer = np.array(exclusionBuffer)

                validPeakPoints = []
                for thisPeak in peakPoints:

                    position, height = thisPeak

                    position += startPointBufferActual

                    for existingPosition in existingPositions:
                        delta = abs(existingPosition - position)

                        # TODO:ED changed to '<='
                        if (delta <= npExclusionBuffer).all():
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
                    firstArray = np.maximum(position - 2, 0)
                    lastArray = np.minimum(position + 3, numPointInt)
                    localRegionArray = np.array((firstArray, lastArray))
                    localRegionArray = localRegionArray.astype(np.int32)

                    # get the larger regionArray size containing all points so far
                    firstArray = np.maximum(position - 3, 0)
                    lastArray = np.minimum(position + 4, numPointInt)
                    if regionArray is not None:
                        firstArray = np.minimum(firstArray, regionArray[0])
                        lastArray = np.maximum(lastArray, regionArray[1])

                    peakArray = position.reshape((1, numDim))
                    peakArray = peakArray.astype(np.float32)
                    firstArray = firstArray.astype(np.int32)
                    lastArray = lastArray.astype(np.int32)
                    regionArray = np.array((firstArray, lastArray))

                    if allPeaksArray is None:
                        allPeaksArray = peakArray
                    else:
                        allPeaksArray = np.append(allPeaksArray, peakArray, axis=0)
                    allRegionArrays.append(localRegionArray)

                if allPeaksArray is not None:

                    # parabolic - generate all peaks in one operation
                    result = CPeak.fitParabolicPeaks(dataArray, regionArray, allPeaksArray)

                    for height, centerGuess, linewidth in result:
                        center = np.array(centerGuess)

                        position = center + startPointBufferActual
                        peak = self.newPickedPeak(pointPositions=position, height=height,
                                                  lineWidths=linewidth if estimateLineWidths else None,
                                                  fitMethod=fitMethod)
                        peaks.append(peak)

                    if fitMethod != PARABOLICMETHOD:
                        self.fitExistingPeaks(peaks, fitMethod=fitMethod, singularMode=True)

                    # # 20191004:ED testing - plotting scatterplot of data
                    # else:
                    #
                    # # result = CPeak.fitPeaks(dataArray, regionArray, allPeaksArray, method)
                    # result = CPeak.fitParabolicPeaks(dataArray, regionArray, allPeaksArray)
                    #
                    # for height, centerGuess, linewidth in result:
                    #
                    #     # clip the point to the exclusion area, to stop rogue peaks
                    #     # center = np.array(centerGuess).clip(min=position - npExclusionBuffer,
                    #     #                                        max=position + npExclusionBuffer)
                    #     center = np.array(centerGuess)
                    #
                    #     # outofPlaneMinTest = np.array([])
                    #     # outofPlaneMaxTest = np.array([])
                    #     # for ii in range(numDim):
                    #     #     outofPlaneMinTest = np.append(outofPlaneMinTest, 0.0)
                    #     #     outofPlaneMaxTest = np.append(outofPlaneMaxTest, dataArray.shape[numDim-ii-1]-1.0)
                    #     #
                    #     # # check whether the new peak is outside of the current plane
                    #     # outofPlaneCenter = np.array(centerGuess).clip(min=position - np.array(outofPlaneMinTest),
                    #     #                      max=position + np.array(outofPlaneMaxTest))
                    #     #
                    #     # print(">>>", center, outofPlaneCenter, not np.array_equal(center, outofPlaneCenter))
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
                    #     #     # have to float because API does not like np.float32
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

    def fitExistingPeaks(self, peaks: Sequence['Peak'], fitMethod: str = GAUSSIANMETHOD, singularMode: bool = True,
                         halfBoxSearchWidth: int = 2, halfBoxFitWidth: int = 2):
        """Refit the current selected peaks.
        Must be called with peaks that belong to this peakList
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

            # generate a np array with the position of the peak in points rounded to integers
            position = [peakDim.position - 1 for peakDim in peakDims]  # API position starts at 1

            # round up/down the position
            pLower = np.floor(position).astype(np.int32)
            pUpper = np.ceil(position).astype(np.int32)
            position = np.round(np.array(position))

            # generate a np array with the number of points per dimension
            numPoints = [peakDim.dataDim.numPoints for peakDim in peakDims]
            numPoints = np.array(numPoints)

            # consider for each dimension on the interval [point-3,point+4>, account for min and max
            # of each dimension
            if fitMethod == PARABOLICMETHOD or singularMode is True:
                firstArray = np.maximum(pLower - halfBoxSearchWidth, 0)
                lastArray = np.minimum(pUpper + halfBoxSearchWidth, numPoints)
            else:
                # extra plane in each direction increases accuracy of group fitting
                firstArray = np.maximum(pLower - halfBoxSearchWidth - 1, 0)
                lastArray = np.minimum(pUpper + halfBoxSearchWidth + 1, numPoints)

            # Cast to int for subsequent call
            firstArray = firstArray.astype(np.int32)
            lastArray = lastArray.astype(np.int32)
            localRegionArray = np.array((firstArray, lastArray), dtype=np.int32)

            if regionArray is not None:
                firstArray = np.minimum(firstArray, regionArray[0])
                lastArray = np.maximum(lastArray, regionArray[1])

            # requires reshaping of the array for use with CPeak.fitParabolicPeaks
            peakArray = position.reshape((1, numDim))
            peakArray = peakArray.astype(np.float32)
            regionArray = np.array((firstArray, lastArray), dtype=np.int32)

            if allPeaksArray is None:
                allPeaksArray = peakArray
            else:
                allPeaksArray = np.append(allPeaksArray, peakArray, axis=0)
            allRegionArrays.append(localRegionArray)

        if allPeaksArray is not None and allPeaksArray.size != 0:

            # map to (0, 0)
            regionArray = np.array((firstArray - firstArray, lastArray - firstArray))

            # Get the data; note that arguments has to be castable to int?
            dataArray, intRegion = dataSource.getRegionData(firstArray, lastArray)

            # update positions relative to the corner of the data array
            firstArray = firstArray.astype(np.float32)
            updatePeaksArray = None
            for pk in allPeaksArray:
                if updatePeaksArray is None:
                    updatePeaksArray = pk - firstArray
                    updatePeaksArray = updatePeaksArray.reshape((1, numDim))
                    updatePeaksArray = updatePeaksArray.astype(np.float32)
                else:
                    pk = pk - firstArray
                    pk = pk.reshape((1, numDim))
                    pk = pk.astype(np.float32)
                    updatePeaksArray = np.append(updatePeaksArray, pk, axis=0)

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
                            peakArray = peakArray.astype(np.float32)
                            localRegionArray = np.array((localRegionArray[0] - firstArray, localRegionArray[1] - firstArray), dtype=np.int32)

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

                    newPos = min(max(center[i], 0.5), dataArray.shape[i] - 1.5)

                    # ignore if out of range
                    if abs(newPos - center[i]) < 1e-9:
                        peakDim.position = center[i] + firstArray[i] + 1.0  # API position starts at 1
                    peakDim.lineWidth = dataDims[i].valuePerPoint * linewidth[i]

                peak.height = dataSource.scale * height

    def _getAliasingRange(self):
        """Return the min/max aliasing range for the peaks in the list, if there are no peaks, return None
        """
        if not self.peaks:
            return None

        # calculate the min/max aliasing values for the spectrum
        dims = self.spectrum.dimensionCount

        aliasMin = [0] * dims
        aliasMax = [0] * dims

        for peak in self.peaks:
            alias = peak.aliasing
            aliasMax = np.maximum(aliasMax, alias)
            aliasMin = np.minimum(aliasMin, alias)

        # set min/max in spectrum here if peaks have been found
        aliasRange = tuple((int(mn), int(mx)) for mn, mx in zip(aliasMin, aliasMax))

        return aliasRange

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

        # height now called explicitly after creating new peak
        # if height is None and ppmPositions:
        #     height = self.spectrum.getHeight(ppmPositions)
        return _newPeak(self, ppmPositions=ppmPositions, height=height, comment=comment, **kwds)

    @logCommand(get='self')
    def newPickedPeak(self, pointPositions: Sequence[float] = None, height: float = None,
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
                 symbolStyle: str = None, symbolColour: str = None,
                 textColour: str = None,
                 meritColour: str = None, meritEnabled: bool = False, meritThreshold: float = None,
                 lineColour: str = None,
                 isSimulated: bool = False, serial: int = None) -> PeakList:
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

    # set non-api attributes
    if meritColour is not None:
        result.meritColour = meritColour
    if meritEnabled is not None:
        result.meritEnabled = meritEnabled
    if meritThreshold is not None:
        result.meritThreshold = meritThreshold
    if lineColour is not None:
        result.lineColour = lineColour

    return result
