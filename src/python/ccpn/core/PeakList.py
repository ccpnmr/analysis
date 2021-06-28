"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-06-28 19:12:26 +0100 (Mon, June 28, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
from typing import Sequence, List, Optional

from ccpn.core.lib.AxisCodeLib import getAxisCodeMatchIndices
from ccpn.util.Common import percentage
from scipy.ndimage import maximum_filter, minimum_filter
from ccpn.util import Common as commonUtil
from ccpn.core.Spectrum import Spectrum
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import PeakList as ApiPeakList
from ccpn.core.lib.SpectrumLib import estimateNoiseLevel1D, _filtered1DArray
# from ccpnmodel.ccpncore.lib._ccp.nmr.Nmr.PeakList import pickNewPeaks
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, undoBlock, undoBlockWithoutSideBar, notificationEchoBlocking
from ccpn.util.Logging import getLogger
from ccpn.core._implementation.PMIListABC import PMIListABC


GAUSSIANMETHOD = 'gaussian'
LORENTZIANMETHOD = 'lorentzian'
PARABOLICMETHOD = 'parabolic'
PICKINGMETHODS = (GAUSSIANMETHOD, LORENTZIANMETHOD, PARABOLICMETHOD)


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
        if not super()._finaliseAction(action):
            return

        # this is a can-of-worms for undelete at the minute
        try:
            if action in ['change']:
                for plv in self.peakListViews:
                    plv._finaliseAction(action)
        except Exception as es:
            raise RuntimeError('Error _finalising peakListViews: %s' % str(es))

    def delete(self):
        """Delete peakList
        """
        # call the delete method from the parent class
        self._parent._deletePeakList(self)

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    def pickPeaksNd(self, regionToPick: Sequence[float] = None,
                    doPos: bool = True, doNeg: bool = True,
                    fitMethod: str = GAUSSIANMETHOD, excludedRegions=None,
                    excludedDiagonalDims=None, excludedDiagonalTransform=None,
                    minDropFactor: float = 0.1):

        from ccpn.core.lib.PeakListLib import _pickPeaksNd

        return _pickPeaksNd(self, regionToPick=regionToPick,
                            doPos=doPos, doNeg=doNeg,
                            fitMethod=fitMethod,
                            excludedRegions=excludedRegions,
                            excludedDiagonalDims=excludedDiagonalDims,
                            excludedDiagonalTransform=excludedDiagonalTransform,
                            minDropFactor=minDropFactor)

    def pickPeaks1d(self, dataRange, intensityRange, peakFactor1D=1) -> List['Peak']:
        """
        Pick 1D peaks from a dataRange
        """
        from ccpn.core.lib.PeakListLib import _pickPeaks1d

        return _pickPeaks1d(self, dataRange, intensityRange, peakFactor1D=peakFactor1D)

    def pickPeaks1d_(self, dataRange, intensityRange=None, size: int = 3, mode: str = 'wrap') -> List['Peak']:
        """
        Pick 1D peaks from a dataRange
        """
        from ccpn.core.lib.PeakListLib import _pickPeaks1d_

        return _pickPeaks1d_(self, dataRange, intensityRange=intensityRange, size=size, mode=mode)

    @logCommand(get='self')
    def pickPeaks1dFiltered(self, size: int = 9, mode: str = 'wrap', factor=10, excludeRegions=None,
                            positiveNoiseThreshold=None, negativeNoiseThreshold=None, negativePeaks=True, stdFactor=0.5):
        """
        Pick 1D peaks from data in self.spectrum.
        """
        from ccpn.core.lib.PeakListLib import _pickPeaks1dFiltered

        return _pickPeaks1dFiltered(self, size=size,
                                    mode=mode,
                                    factor=factor,
                                    excludeRegions=excludeRegions,
                                    positiveNoiseThreshold=positiveNoiseThreshold,
                                    negativeNoiseThreshold=negativeNoiseThreshold,
                                    negativePeaks=negativePeaks,
                                    stdFactor=stdFactor)

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

    def _pick1DsingleMaximum(self, maxNoiseLevel=None,
                             minNoiseLevel=None,
                             ignoredRegions=[[20, 19]],
                             eNoiseThresholdFactor=1.5,
                             useXRange=10):
        """
        :param maxNoiseLevel:
        :param minNoiseLevel:
        :param ignoredRegions:
        :param eNoiseThresholdFactor:
        :param useXRange:
        :return: Used for spectra where only one observable is expected. E.g. 19F reference spectra for screening.
        """
        peaks = []
        spectrum = self.spectrum
        x, y = spectrum.positions, spectrum.intensities
        masked = _filtered1DArray(np.array([x, y]), ignoredRegions)
        filteredX, filteredY = masked[0].compressed(), masked[1].compressed()
        if maxNoiseLevel is None and minNoiseLevel is None:
            maxNoiseLevel, minNoiseLevel = estimateNoiseLevel1D(y, f=useXRange, stdFactor=eNoiseThresholdFactor)
        maxValue = np.argmax(filteredY)
        spectrum.noiseLevel = float(maxNoiseLevel)
        spectrum.negativeNoiseLevel = float(minNoiseLevel)
        if maxValue:
            peak = self.newPeak(ppmPositions=[float(x[maxValue]), ], height=float(y[maxValue]))
            snr = peak.signalToNoiseRatio
            peaks.append(peak)
        return peaks

    def peakFinder1D(self, maxNoiseLevel=None, minNoiseLevel=None,
                     ignoredRegions=[[20, 19]], negativePeaks=False,
                     eNoiseThresholdFactor=1.5,
                     recalculateSNR=True,
                     deltaPercent=10,
                     useXRange=1):

        from ccpn.core.lib.PeakListLib import _peakFinder1D

        return _peakFinder1D(self, maxNoiseLevel=maxNoiseLevel,
                             minNoiseLevel=minNoiseLevel,
                             ignoredRegions=ignoredRegions,
                             negativePeaks=negativePeaks,
                             eNoiseThresholdFactor=eNoiseThresholdFactor,
                             recalculateSNR=recalculateSNR,
                             deltaPercent=deltaPercent,
                             useXRange=useXRange)

    @logCommand(get='self')
    def copyTo(self, targetSpectrum: Spectrum, **kwargs) -> 'PeakList':
        """Make (and return) a copy of the PeakList attached to targetSpectrum.

        Peaklist attributes can be passed in as keyword arguments"""

        singleValueTags = ['isSimulated', 'symbolColour', 'symbolStyle', 'textColour', 'textColour',
                           'title', 'comment', 'meritThreshold', 'meritEnabled', 'meritColour']

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

        with undoBlockWithoutSideBar():
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

        with undoBlockWithoutSideBar():
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
                                      pointPositions=peak1.pointPositions)

        return peakList3

    # def refit(self, method: str = GAUSSIANMETHOD):
    #     fitExistingPeakList(self._apiPeakList, method)

    @logCommand(get='self')
    def restrictedPick(self, positionCodeDict, doPos, doNeg):

        codes = list(positionCodeDict.keys())
        positions = [positionCodeDict[code] for code in codes]

        # match the spectrum to the restricted codes, these are the only ones to update
        indices = getAxisCodeMatchIndices(self.spectrum.axisCodes, codes)

        # divide by 2 to get the double-width tolerance, i.e. the width of the region - CHECK WITH GEERTEN
        tolerances = tuple(tol / 2 for tol in self.spectrum.assignmentTolerances)

        limits = [sorted(lims) for lims in self.spectrum.spectrumLimits]
        selectedRegion = []
        minDropFactor = self.project._appBase.preferences.general.peakDropFactor

        with undoBlockWithoutSideBar():
            for ii, ind in enumerate(indices):
                if ind is not None:
                    selectedRegion.insert(ii, [positions[ind] - tolerances[ii], positions[ind] + tolerances[ii]])
                else:
                    selectedRegion.insert(ii, [limits[ii][0], limits[ii][1]])

            # regionToPick = selectedRegion
            # peaks = self.pickPeaksNd(regionToPick, doPos=doPos, doNeg=doNeg, minDropFactor=minDropFactor)

            axisCodeDict = dict((code, selectedRegion[ii]) for ii, code in enumerate(self.spectrum.axisCodes))

            _spectrum = self.spectrum
            # may create a peakPicker instance if not defined, subject to settings in preferences
            _peakPicker = _spectrum.peakPicker
            if _peakPicker:
                _peakPicker.dropFactor = minDropFactor
                _peakPicker.setLineWidths = True
                peaks = _spectrum.pickPeaks(self, _spectrum.positiveContourBase if doPos else None,
                                            _spectrum.negativeContourBase if doNeg else None,
                                            **axisCodeDict)
                return peaks

        return []

    def reorderValues(self, values, newAxisCodeOrder):
        """Reorder values in spectrum dimension order to newAxisCodeOrder
        by matching newAxisCodeOrder to spectrum axis code order"""
        return commonUtil.reorder(values, self._parent.axisCodes, newAxisCodeOrder)

    # def __str__(self):
    #   """Readable string representation"""
    #   return "<%s; #peaks:%d (isSimulated=%s)>" % (self.pid, len(self.peaks), self.isSimulated)

    @logCommand(get='self')
    def pickPeaksRegion(self, regionToPick: dict = {},
                        doPos: bool = True, doNeg: bool = True,
                        minLinewidth=None, exclusionBuffer=None,
                        minDropFactor: float = 0.1, checkAllAdjacent: bool = True,
                        fitMethod: str = PARABOLICMETHOD, excludedRegions=None,
                        excludedDiagonalDims=None, excludedDiagonalTransform=None,
                        estimateLineWidths=True):

        getLogger().warning('Deprecated, please use spectrum.pickPeaks()')

        from ccpn.core.lib.PeakListLib import _pickPeaksRegion

        with undoBlockWithoutSideBar():
            peaks = _pickPeaksRegion(self, regionToPick=regionToPick,
                                          doPos=doPos, doNeg=doNeg,
                                          minLinewidth=minLinewidth, exclusionBuffer=exclusionBuffer,
                                          minDropFactor=minDropFactor, checkAllAdjacent=checkAllAdjacent,
                                          fitMethod=fitMethod, excludedRegions=excludedRegions,
                                          excludedDiagonalDims=excludedDiagonalDims, excludedDiagonalTransform=excludedDiagonalTransform,
                                          estimateLineWidths=estimateLineWidths)
        return peaks

    def fitExistingPeaks(self, peaks: Sequence['Peak'], fitMethod: str = GAUSSIANMETHOD, singularMode: bool = True,
                         halfBoxSearchWidth: int = 2, halfBoxFitWidth: int = 2):
        """Refit the current selected peaks.
        Must be called with peaks that belong to this peakList
        """
        from ccpn.core.lib.PeakListLib import _fitExistingPeaks

        getLogger().warning('Deprecated, please use spectrum.fitExistingPeaks()')

        return _fitExistingPeaks(self,
                                 peaks=peaks,
                                 fitMethod=fitMethod,
                                 singularMode=singularMode,
                                 halfBoxSearchWidth=halfBoxSearchWidth,
                                 halfBoxFitWidth=halfBoxFitWidth)

    def getPeakAliasingRanges(self):
        """Return the min/max aliasing values for the peaks in the list, if there are no peaks, return None
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
        aliasRanges = tuple((int(mn), int(mx)) for mn, mx in zip(aliasMin, aliasMax))

        return aliasRanges

    @logCommand(get='self')
    def reorderPeakListAxes(self, newAxisOrder):
        """Reorder the peak position according to the newAxisOrder
        """
        dims = self.spectrum.dimensionCount

        if not isinstance(newAxisOrder, (list, tuple)):
            raise TypeError('newAxisOrder must be a list/tuple')
        if len(newAxisOrder) != dims:
            raise ValueError('newAxisOrder is the wrong length, must match spectrum dimensions')
        if len(set(newAxisOrder)) != len(newAxisOrder):
            raise ValueError('newAxisOrder contains duplicated elements')
        if not all(isinstance(ii, int) for ii in newAxisOrder):
            raise ValueError('newAxisOrder must be ints')
        if not all(0 <= ii < dims for ii in newAxisOrder):
            raise ValueError('newAxisOrder elements must be in range 0-%i', dims - 1)

        with undoBlockWithoutSideBar():
            # reorder all peaks in the peakList
            for peak in self.peaks:
                pos = peak.position
                newPos = []
                for ii in newAxisOrder:
                    newPos.append(pos[ii])
                peak.position = newPos

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

        :param ppmPositions: peak position in ppm for each dimension (related attributes: positionError, pointPositions)
        :param height: height of the peak (related attributes: volume, volumeError, lineWidths)
        :param comment: optional comment string
        :return: a new Peak instance.
        """
        from ccpn.core.Peak import _newPeak  # imported here to avoid circular imports

        return _newPeak(self, ppmPositions=ppmPositions, height=height, comment=comment, **kwds)

    @logCommand(get='self')
    def newPickedPeak(self, pointPositions: Sequence[float] = None, height: float = None,
                      lineWidths: Sequence[float] = (), fitMethod: str = PARABOLICMETHOD, **kwds):
        """Create a new Peak within a peakList from a picked peak

        See the Peak class for details.

        Optional keyword arguments can be passed in; see Peak._newPickedPeak for details.

        :param height: height of the peak (related attributes: volume, volumeError, lineWidths)
        :param pointPositions: peak position in points for each dimension (related attributes: positionError, pointPositions)
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
                 isSimulated: bool = False) -> PeakList:
    """Create new empty PeakList within Spectrum

    See the PeakList class for details.

    :param title:
    :param comment:
    :param isSimulated:
    :param symbolStyle:
    :param symbolColour:
    :param textColour:
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

# for sp in project.spectra:
#     c = sp.positiveContourColour
#     sp.peakLists[-1].symbolColour = c
