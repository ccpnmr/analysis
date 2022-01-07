"""
GUI Display Strip class
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2022-01-07 15:27:00 +0000 (Fri, January 07, 2022) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Sequence, Tuple, List

from ccpn.core.Peak import Peak
from ccpn.core.Spectrum import Spectrum
from ccpn.core.PeakList import PeakList
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib.AxisCodeLib import _axisCodeMapIndices
from ccpn.ui._implementation.SpectrumDisplay import SpectrumDisplay

from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import BoundStrip as ApiBoundStrip
from ccpn.util.Logging import getLogger
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar, newObject

from ccpn.util.Constants import AXISUNIT_PPM, AXISUNIT_HZ, AXISUNIT_POINT

from ccpn.core._implementation.updates.update_3_0_4 import _updateStrip_3_0_4_to_3_1_0
from ccpn.core._implementation.Updater import updateObject, UPDATE_POST_OBJECT_INITIALISATION

@updateObject(fromVersion='3.0.4',
              toVersion='3.1.0',
              updateFunction=_updateStrip_3_0_4_to_3_1_0,
              updateMethod=UPDATE_POST_OBJECT_INITIALISATION)
class Strip(AbstractWrapperObject):
    """Display Strip for 1D or nD spectrum"""

    #: Short class name, for PID.
    shortClassName = 'GS'
    # Attribute it necessary as subclasses must use superclass className
    className = 'Strip'

    _parentClass = SpectrumDisplay

    #: Name of plural link to instances of class
    _pluralLinkName = 'strips'

    # the attribute name used by current
    _currentAttributeName = 'strip'

    #: List of child classes.
    _childClasses = []

    _isGuiClass = True

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiBoundStrip._metaclass.qualifiedName()

    # internal namespace
    _STRIPTILEPOSITION = '_stripTilePosition'

    #-----------------------------------------------------------------------------------------

    def __init__(self, project, wrappedData):
        super().__init__(project=project, wrappedData=wrappedData)

    # @classmethod
    # def _restoreObject(cls, project, apiObj):
    #     """Subclassed to allow for initialisations on restore
    #     """
    #     result = super()._restoreObject(project, apiObj)
    #     return result

    #-----------------------------------------------------------------------------------------
    # Attributes and methods related to the data structure
    #-----------------------------------------------------------------------------------------

    @property
    def spectrumDisplay(self) -> SpectrumDisplay:
        """SpectrumDisplay containing strip."""
        return self._project._data2Obj.get(self._wrappedData.spectrumDisplay)

    _parent = spectrumDisplay

    @property
    def spectrumViews(self) -> list:
        """SpectrumViews shown in Strip"""
        # STUB for now; hot-fixed later
        pass

    @property
    def axes(self) -> list:
        """The axes of Strip"""
        # STUB for now; hot-fixed later
        pass

    #GWV: moved here from _implementation/Axis.py
    @property
    def orderedAxes(self) -> Tuple:
        """Axes in display order (X, Y, Z1, Z2, ...) """
        apiStrip = self._wrappedData
        ff = self._project._data2Obj.get
        return tuple(ff(apiStrip.findFirstStripAxis(axis=x)) for x in apiStrip.orderedAxes)

    # GWV 23/12: There should not be a setter! Created by SpectrumDisplay/Strip
    # @orderedAxes.setter
    # def orderedAxes(self, value: Sequence):
    #     value = [self.getByPid(x) if isinstance(x, str) else x for x in value]
    #     #self._wrappedData.orderedAxes = tuple(x._wrappedData.axis for x in value)
    #     self._wrappedData.axisOrder = tuple(x.code for x in value)

    #-----------------------------------------------------------------------------------------
    # Functional attributes of the class
    #-----------------------------------------------------------------------------------------

    @property
    def axisCodes(self) -> Tuple[str, ...]:
        """Fixed string Axis codes in original display order (X, Y, Z1, Z2, ...)"""
        return self._wrappedData.axisCodes

    @property
    def axisOrder(self) -> Tuple[str, ...]:
        """String Axis codes in display order (X, Y, Z1, Z2, ...), determine axis display order"""
        return self._wrappedData.axisOrder

    @axisOrder.setter
    def axisOrder(self, value: Sequence):
        self._wrappedData.axisOrder = value

    @property
    def positions(self) -> Tuple[float, ...]:
        """Axis centre positions, in display order"""
        return self._wrappedData.positions

    @positions.setter
    def positions(self, value):
        self._wrappedData.positions = value

    @property
    def widths(self) -> Tuple[float, ...]:
        """Axis display widths, in display order"""
        return self._wrappedData.widths

    @widths.setter
    def widths(self, value):
        self._wrappedData.widths = value

    @property
    def units(self) -> Tuple[str, ...]:
        """Axis units, in display order"""
        # return self._wrappedData.units
        return tuple([ax.unit for ax in self.orderedAxes])

    @property
    def _unitIndices(self) -> Tuple[int, ...]:
        """Axis units indices, in display order"""
        return tuple([ax._unitIndex for ax in self.orderedAxes])

    @property
    def spectra(self) -> Tuple[Spectrum, ...]:
        """The spectra attached to the strip (whether display is currently turned on or not)"""
        return tuple(x.spectrum for x in self.spectrumViews)

    def getSpectra(self) -> Tuple[Spectrum, ...]:
        """The spectra attached to the strip (whether display is currently turned on or not) in displayed order"""
        return tuple(sv.spectrum for sv in self.getSpectrumViews())

    def getVisibleSpectra(self) -> Tuple[Spectrum, ...]:
        """Return a tuple of spectra currently visible in the strip in displayed order
        """
        return tuple(sv.spectrum for sv in self.getSpectrumViews() if sv.isDisplayed)

    def getSpectrumViews(self) -> Tuple['SpectrumView', ...]:
        """The spectrumViews attached to the strip (whether display is currently turned on or not) in display order"""
        dd = [(sv._index, sv) for sv in self.spectrumViews]
        return tuple(val[1] for val in sorted(dd))

    def _setSpectrumViews(self, spectrumViews):
        """Set the new ordering for the spectrumViews.
        Must be the original spectrumViews"""
        if set(self.getSpectrumViews()) != set(spectrumViews):
            raise ValueError('bad spectrumViews')
        with undoBlockWithoutSideBar():
            for ind, sv in enumerate(spectrumViews):
                # update the spectrumView indexing
                sv._index = ind

    @property
    def spectrumGroups(self) -> Tuple[Spectrum, ...]:
        """The spectra attached to the strip (whether display is currently turned on or not)"""
        pids = self.spectrumDisplay._getSpectrumGroups()
        return tuple(self.project.getByPid(x) for x in pids)

    #=========================================================================================
    # CCPN properties
    #=========================================================================================

    @property
    def _displayedSpectra(self) -> tuple:
        """Return a tuple of DisplayedSpectrum instances, in order of the spectrumDisplay
        toolbar, if currently visible
        """
        result = [DisplayedSpectrum(strip=self, spectrumView=specView) \
                  for specView in self.getSpectrumViews() if specView.isDisplayed]
        return tuple(result)

    @property
    def _minAxisLimitsByUnit(self) -> list:
        """:return a list of the min(axis-limits-by-type) (ie. depending on axis.unit) in display-axis order
        """
        _allSpecs = [DisplayedSpectrum(strip=self, spectrumView=sv)
                     for sv in self.spectrumViews
                    ]
        _valsPerSpecView = [ds.minAxisLimitsByUnit
                            for ds in _allSpecs]

        # now get the values per axis
        result = []
        for axisIndex, axis in enumerate(self.axes):
            _tmp = [val[axisIndex] for val in _valsPerSpecView
                        if val[axisIndex] is not None
                   ]
            _minVal = None if len(_tmp) == 0 else min(_tmp)
            result.append(_minVal)

        return result    \

    @property
    def _maxAxisLimitsByUnit(self) -> list:
        """:return a list of the max(axis-limits-by-unit) (ie. depending on axis.unit) in display-axis order
        """
        _allSpecs = [DisplayedSpectrum(strip=self, spectrumView=sv)
                     for sv in self.spectrumViews
                    ]
        _valsPerSpecView = [ds.maxAxisLimitsByUnit
                            for ds in _allSpecs]

        # now get the values per axis
        result = []
        for axisIndex, axis in enumerate(self.axes):
            _tmp = [val[axisIndex] for val in _valsPerSpecView
                        if val[axisIndex] is not None
                   ]
            _maxVal = None if len(_tmp) == 0 else max(_tmp)
            result.append(_maxVal)

        return result

    @property
    def _minAxisIncrementByUnit(self) -> list:
        """:return a list of the min(axis-increment-by-unit) (ie. depending on axis.unit) in display-axis order
        """
        _allSpecs = [DisplayedSpectrum(strip=self, spectrumView=sv)
                     for sv in self.spectrumViews
                    ]
        _valsPerSpecView = [ds.axisIncrementsByUnit
                            for ds in _allSpecs]

        # now get the values per axis
        result = []
        for axisIndex, axis in enumerate(self.axes):
            _tmp = [val[axisIndex] for val in _valsPerSpecView
                        if val[axisIndex] is not None
                   ]
            _minVal = None if len(_tmp) == 0 else min(_tmp)
            result.append(_minVal)

        return result

    #=========================================================================================
    # API-related properties
    #=========================================================================================

    @property
    def _apiStrip(self) -> ApiBoundStrip:
        """ CCPN Strip matching Strip"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """id string - serial number converted to string"""
        return str(self._wrappedData.serial)

    @property
    def serial(self) -> int:
        """serial number of Strip, used in Pid and to identify the Strip. """
        return self._wrappedData.serial

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: SpectrumDisplay) -> list:
        """Get wrappedData (ccpnmr.gui.Task.Strip) in serial number order.
        """
        return parent._wrappedData.sortedStrips()

    def _finaliseAction(self, action: str):
        """Spawn _finaliseAction notifiers for spectrumView tree attached to this strip.
        """
        if not super()._finaliseAction(action):
            return

        if action in ['create', 'delete']:
            for sv in self.spectrumViews:
                sv._finaliseAction(action)

                for plv in sv.peakListViews:
                    plv._finaliseAction(action)
                for ilv in sv.integralListViews:
                    ilv._finaliseAction(action)
                for mlv in sv.multipletListViews:
                    mlv._finaliseAction(action)

    # @deleteObject()         # - doesn't work here
    def _delete(self):
        """delete the wrappedData.
        CCPN Internal
        """
        self._wrappedData.delete()

    def _setStripIndex(self, index):
        """Set the index of the current strip in the wrapped data.
        CCPN Internal
        """
        ccpnStrip = self._wrappedData
        ccpnStrip.__dict__['index'] = index  # this is the api creation of orderedStrips

    def stripIndex(self):
        """Return the index of the current strip in the spectrumDisplay.
        """
        # original api indexing
        ccpnStrip = self._wrappedData
        indx = ccpnStrip.index
        # spectrumDisplay = self.spectrumDisplay
        # index = spectrumDisplay.strips.index(self)
        return indx

    # from ccpn.util.decorators import profile
    # @profile
    def _clear(self):
        for spectrumView in self.spectrumViews:
            spectrumView.delete()

    def delete(self):
        """trap this delete
        """
        raise RuntimeError('Please use spectrumDisplay.deleteStrip()')

    # def _removeOrderedSpectrumViewIndex(self, index):
    #     self.spectrumDisplay.removeOrderedSpectrumView(index)

    @property
    def tilePosition(self) -> Tuple[int, int]:
        """Returns a tuple of the tile coordinates (from top-left)
        tilePosition = (x, y)
        """
        tilePosition = self._getInternalParameter(self._STRIPTILEPOSITION) or (0, 0)
        return tilePosition

    @tilePosition.setter
    def tilePosition(self, value):
        """Setter for tilePosition
        tilePosition must be a tuple of int (x, y)
        """
        if not isinstance(value, tuple):
            raise ValueError('Expected a tuple for tilePosition')
        if len(value) != 2:
            raise ValueError('Tuple must be (x, y)')
        if any(type(vv) != int for vv in value):
            raise ValueError('Tuple must be of type int')

        self._setInternalParameter(self._STRIPTILEPOSITION, value)

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    def _clone(self):
        """create new strip that duplicates this one, appending it at the end
        """
        apiStrip = self._wrappedData.clone()
        result = self._project._data2Obj.get(apiStrip)
        if result is None:
            raise RuntimeError('Unable to generate new Strip item')

        return result

    @logCommand(get='self')
    def moveStrip(self, newIndex: int):
        """Move strip to index newIndex in orderedStrips
        """
        if not isinstance(newIndex, int):
            raise TypeError('newIndex %s is not of type Int' % str(newIndex))

        currentIndex = self._wrappedData.index
        if currentIndex == newIndex:
            return

        # get the current order
        stripCount = self.spectrumDisplay.stripCount

        if newIndex >= stripCount:
            # Put strip at the right, which means newIndex should be stripCount - 1
            if newIndex > stripCount:
                raise TypeError("Attempt to copy strip to position %s in display with only %s strips"
                                % (newIndex, stripCount))
            newIndex = stripCount - 1

        # move the strip
        self._wrappedData.moveTo(newIndex)

    # GWV 24/12/21: commented as not used
    # @logCommand(get='self')
    # def resetAxisOrder(self):
    #     """Reset display to original axis order"""
    #     with undoBlockWithoutSideBar():
    #         self._wrappedData.resetAxisOrder()

    # GWV 24/12/21: commented as not used
    # def findAxis(self, axisCode):
    #     """Find axis"""
    #     return self._project._data2Obj.get(self._wrappedData.findAxis(axisCode))

    # GWV 24/12/21: moved to GuiStrip
    # @logCommand(get='self')
    # def createPeak(self, ppmPositions: List[float]) -> Tuple[Tuple[Peak, ...], Tuple[PeakList, ...]]:
    #     """Create peak at position for all spectra currently displayed in strip.
    #     """
    #     result = []
    #     peakLists = []
    #
    #     with undoBlockWithoutSideBar():
    #         # create the axisDict for this spectrum
    #         axisDict = {axis: tuple(ppm) for axis, ppm in zip(self.axisCodes, ppmPositions)}
    #
    #         # loop through the visible spectra
    #         for spectrumView in (v for v in self.spectrumViews if v.isDisplayed):
    #
    #             spectrum = spectrumView.spectrum
    #             # get the list of visible peakLists
    #             validPeakListViews = [pp for pp in spectrumView.peakListViews if pp.isDisplayed]
    #             if not validPeakListViews:
    #                 continue
    #
    #             for thisPeakListView in validPeakListViews:
    #                 peakList = thisPeakListView.peakList
    #
    #                 # pick the peak in this peakList
    #                 pk = spectrum.createPeak(peakList, **axisDict)
    #                 if pk:
    #                     result.append(pk)
    #                     peakLists.append(peakList)
    #
    #         # set the current peaks
    #         self.current.peaks = result
    #
    #     return tuple(result), tuple(peakLists)
    #
    # GWV 24/12/21: moved to GuiStrip
    # @logCommand(get='self')
    # def pickPeaks(self, regions: List[Tuple[float,float]]) -> Tuple[Peak, ...]:
    #     """Peak-pick in regions for all spectra currently displayed in the strip.
    #     """
    #     from ccpn.core.lib.SpectrumLib import _pickPeaksByRegion
    #
    #     _displayedSpectra = self._displayedSpectra
    #     if len(_displayedSpectra) == 0:
    #         getLogger().warning('%s pickPeaks: no visible spectra' % self)
    #         return
    #
    #     result = []
    #     with undoBlockWithoutSideBar():
    #
    #         # loop through the visible spectra
    #         for _displayedSpectrum in _displayedSpectra:
    #             spectrum = _displayedSpectrum.spectrum
    #             spectrumView = _displayedSpectrum.spectrumView
    #
    #             _checkOutside = _displayedSpectrum.checkForRegionsOutsideLimits(regions)
    #             _skip = any(_checkOutside)
    #             if _skip:
    #                 getLogger().debug('Strip.pickPeaks: skipping %s; outside region %r' % (spectrum, regions))
    #                 continue
    #
    #             # get the list of visible peakLists
    #             validPeakListViews = [pp for pp in spectrumView.peakListViews if pp.isDisplayed]
    #             if not validPeakListViews:
    #                 continue
    #
    #             # get parameters to apply to peak picker
    #             _sliceTuples = _displayedSpectrum.getSliceTuples(regions)
    #             positiveThreshold = spectrum.positiveContourBase if spectrumView.displayPositiveContours else None
    #             negativeThreshold = spectrum.negativeContourBase if spectrumView.displayNegativeContours else None
    #
    #             for thisPeakListView in validPeakListViews:
    #                 peakList = thisPeakListView.peakList
    #                 # pick the peaks in this peakList
    #                 newPeaks = _pickPeaksByRegion(spectrum = spectrum,
    #                                               sliceTuples=_sliceTuples,
    #                                               peakList=peakList,
    #                                               positiveThreshold=positiveThreshold,
    #                                               negativeThreshold=negativeThreshold,
    #                                               )
    #                 if newPeaks is not None and len(newPeaks) > 0:
    #                     result.extend(newPeaks)
    #
    #     result = tuple(result)
    #     self.current.peaks = result
    #     return result
#end class


# newStrip functions
# Rasmus: We should NOT have any newStrip function, except possibly for FreeStrips

# @newObject(Strip)
# def _newStrip(self):
#     """Create new strip that duplicates this one, appending it at the end
#     Does not handle any gui updating.
#     """
#     apiStrip = self._wrappedData.clone()
#     result = self._project._data2Obj.get(apiStrip)
#     if result is None:
#         raise RuntimeError('Unable to generate new Strip item')
#
#     return result


def _copyStrip(self: SpectrumDisplay, strip: Strip, newIndex=None) -> Strip:
    """Make copy of strip in self, at position newIndex - or rightmost.
    """
    strip = self.getByPid(strip) if isinstance(strip, str) else strip
    if not isinstance(strip, Strip):
        raise TypeError('strip is not of type Strip')

    stripCount = self.stripCount
    if newIndex and newIndex >= stripCount:
        # Put strip at the right, which means newIndex should be None
        if newIndex > stripCount:
            # warning
            self._project._logger.warning(
                    "Attempt to copy strip to position %s in display with only %s strips"
                    % (newIndex, stripCount))
        newIndex = None

    # with logCommandBlock(prefix='newStrip=', get='self') as log:
    #     log('copyStrip', strip=repr(strip.pid))
    with undoBlockWithoutSideBar():

        if strip.spectrumDisplay is self:
            # Within same display. Not that useful, but harmless
            # newStrip = strip.clone()

            # clone the last strip
            newStrip = strip.spectrumDisplay.addStrip(strip)

            if newIndex is not None:
                newStrip.moveTo(newIndex)

        else:
            mapIndices = _axisCodeMapIndices(strip.axisOrder, self.axisOrder)
            if mapIndices is None:
                raise ValueError("Strip %s not compatible with window %s" % (strip.pid, self.pid))
            else:
                positions = strip.positions
                widths = strip.widths
                # newStrip = self.orderedStrips[0].clone()

                # clone the first strip
                newStrip = strip.spectrumDisplay.addStrip(self.orderedStrips[0])

                if newIndex is not None:
                    newStrip.moveTo(newIndex)
                for ii, axis in enumerate(newStrip.orderedAxes):
                    ind = mapIndices[ii]
                    if ind is not None and axis._wrappedData.axis.stripSerial != 0:
                        # Override if there is a mapping and axis is not shared for all strips
                        axis.position = positions[ind]
                        axis.widths = widths[ind]

    return newStrip

# GWV 10/12/21: in SpectrumDisplay
# SpectrumDisplay.copyStrip = _copyStrip
# del _copyStrip


class DisplayedSpectrum(object):
    """GWV; a class to hold SpectrumView and strip objects
    Used to map any data/axis/parameter actions in a SpectrumView dependent fashion
    Only to be used internally
    """
    def __init__(self, strip, spectrumView):
        self.strip = strip
        self.spectrumView = spectrumView

    @property
    def spectrum(self):
        return self.spectrumView.spectrum

    @property
    def spectrumDimensions(self):
        """Return a tuple of spectrumDimensions in axis display order
        Assure that the len always is dimensionCount of the spectrumDisplay
        by adding None's if necessary. This compensates for lower dimensional
        spectra (e.g. a 2D mapped onto a 3D)
        """
        result = self.spectrumView.spectrumDimensions
        for idx in range(len(result), self.strip.spectrumDisplay.dimensionCount):
            result.append(None)
        return tuple(result)

    @property
    def ppmPerPoints(self) -> tuple:
        """Return tuple of ppm-per-point values in axis display order.
        Assure that the len always is dimensionCount of the spectrumDisplay
        by adding None's if necessary. This compensates for lower dimensional
        spectra (e.g. a 2D mapped onto a 3D)
        """
        result = self.spectrumView.ppmPerPoints
        for idx in range(len(result), self.strip.spectrumDisplay.dimensionCount):
            result.append(None)
        return tuple(result)

    @property
    def currentPositionsInPpm(self) -> tuple:
        """Return a tuple of current positions (i.e. the centres) for axes
        in display order.
        The length is always dimensionCount of the spectrumDisplay
        """
        axes = self.strip.orderedAxes
        result = [ax.position for ax in axes]
        for idx in range(len(result), self.strip.spectrumDisplay.dimensionCount):
            result.append(None)
        return tuple(result)

    @property
    def currentWidthsInPpm(self) -> tuple:
        """Return a tuple of the current widths for axes in display order.
        The length is always dimensionCount of the spectrumDisplay
        """
        axes = self.strip.orderedAxes
        result = [ax.width for ax in axes]
        for idx in range(len(result), self.strip.spectrumDisplay.dimensionCount):
            result.append(None)
        return tuple(result)

    @property
    def currentRegionsInPpm(self) -> tuple:
        """Return a tuple of (leftPpm,rightPpm) for current regions for axes
        in display order.
        """
        axes = self.strip.orderedAxes
        result = [ax.region for ax in axes]
        for idx in range(len(result), self.strip.spectrumDisplay.dimensionCount):
            result.append( (None, None) )
        return tuple(result)

    def _getRegionsInPoints(self, regions):
        """Helper function"""
        spectrumDimensions = self.spectrumView.spectrumDimensions
        result = []
        for indx, specDim in enumerate(spectrumDimensions):
            minPpm, maxPpm = regions[indx]
            minPoint = specDim.ppmToPoint(minPpm)
            maxPoint = specDim.ppmToPoint(maxPpm)
            result.append( tuple(sorted((minPoint,maxPoint))) )
        for idx in range(len(result), self.strip.spectrumDisplay.dimensionCount):
            result.append( (None, None) )
        return tuple(result)

    @property
    def currentRegionsInPoints(self) -> tuple:
        """Return a tuple of (minPoint,maxPoint) tuples corresponding to
        current regions for axes in display order.
        Assure that the len always is dimensionCount of the spectrumDisplay
        by adding None's if necessary. This compensates for lower dimensional
        spectra (e.g. a 2D mapped onto a 3D)
        """
        return self._getRegionsInPoints(self.currentRegionsInPpm)

    @property
    def axisIncrementsByUnit(self) -> tuple:
        """Return axis increments by unit for axes in display order.
        Assure that the len always is dimensionCount of the spectrumDisplay
        by adding None's if necessary. This compensates for lower dimensional
        spectra (e.g. a 2D mapped onto a 3D)
        """
        result = []
        for axis, ppmPerPoint, specFreq, points in \
                zip(self.strip.orderedAxes,
                    self.spectrumView.ppmPerPoints,
                    self.spectrumView.spectrometerFrequencies,
                    self.spectrumView.pointCounts
                   ):

            if axis.unit == AXISUNIT_PPM:
                result.append(ppmPerPoint)

            elif axis.unit == AXISUNIT_POINT:
                result.append(1.0)

            elif axis.unit == AXISUNIT_HZ:
                result.append(ppmPerPoint*specFreq)

            else:
                raise RuntimeError('axisIncrementsByUnit: undefined axis unit "%s"' % axis.unit)

        for idx in range(len(result), self.strip.spectrumDisplay.dimensionCount):
            result.append( None )
        return tuple(result)

    @property
    def axisLimitsByUnit(self) -> tuple:
        """Return a tuple of (minVal,maxVal) tuples corresponding to the
        limits by unit for axes in display order.
        Assure that the len always is dimensionCount of the spectrumDisplay
        by adding None's if necessary. This compensates for lower dimensional
        spectra (e.g. a 2D mapped onto a 3D)
        """
        result = []
        for axis, specDim, limits, specFreq, points in \
                zip(self.strip.orderedAxes,
                    self.spectrumView.spectrumDimensions,
                    self.spectrumView.aliasingLimits,
                    self.spectrumView.spectrometerFrequencies,
                    self.spectrumView.pointCounts
                   ):

            if axis.unit == AXISUNIT_PPM:
                result.append((min(limits), max(limits)))

            elif axis.unit == AXISUNIT_POINT:
                result.append((1.0, float(points)))

            elif axis.unit == AXISUNIT_HZ:
                limits = [val*specFreq for val in limits]
                result.append((min(limits), max(limits)))

            else:
                raise RuntimeError('axisLimitsByUnit: undefined axis unit "%s"' % axis.unit)

        for idx in range(len(result), self.strip.spectrumDisplay.dimensionCount):
            result.append( (None, None) )
        return tuple(result)

    @property
    def minAxisLimitsByUnit(self) -> tuple:
        """Return a tuple corresponding to the minimum limits by type for axes in
        display order.
        Assure that the len always is dimensionCount of the spectrumDisplay
        by adding None's if necessary. This compensates for lower dimensional
        spectra (e.g. a 2D mapped onto a 3D)
        """
        result = [val[0] for val in self.axisLimitsByUnit]
        return tuple(result)

    @property
    def maxAxisLimitsByUnit(self) -> tuple:
        """Return a tuple corresponding to the maximum limits by unit for axes in
        display order.
        Assure that the len always is dimensionCount of the spectrumDisplay
        by adding None's if necessary. This compensates for lower dimensional
        spectra (e.g. a 2D mapped onto a 3D)
        """
        result = [val[1] for val in self.axisLimitsByUnit]
        return tuple(result)

    @property
    def aliasingLimits(self) -> tuple:
        """Return a tuple of aliasingLimits (in ppm) in display order.
        Assure that the len always is dimensionCount of the spectrumDisplay
        by adding None's if necessary. This compensates for lower dimensional
        spectra (e.g. a 2D mapped onto a 3D).
        """
        result = self.spectrumView.aliasingLimits
        for idx in range(len(result), self.strip.spectrumDisplay.dimensionCount):
            result.append( (None, None) )

    def getSliceTuples(self, regions) -> list:
        """Return a list of (startPoint,endPoint) slice tuples for regions in spectrum order.
        """
        regionInPoints = [list(rp) for rp in self._getRegionsInPoints(regions)]
        # first assemble the result in display order
        result = []
        for points in regionInPoints[:self.spectrumView.dimensionCount]:
            for i in (0,1):
                points[i] = int(points[i] + 0.5)
            result.append(tuple(points))

        # create a mapping dict to reorder in spectrum order
        mapping = dict([(dimIdx, idx) for idx, dimIdx in enumerate(self.spectrumView.dimensionIndices)])
        sliceTuples = [result[mapping[idx]] for idx in self.spectrumView.spectrum.dimensionIndices]

        return sliceTuples

    def checkForRegionsOutsideLimits(self, regions) -> tuple:
        """check if regions are fully outside the aliasing limits of spectrum.
        :return a tuple of booleans in display order
        """
        result = []
        for region, limits in zip(regions, self.spectrumView.aliasingLimits):
            # to not be dependent on order of low,high values in region or limits:
            minVal = min(region)
            maxVal = max(region)
            minLimit = min(limits)
            maxLimit = max(limits)
            if maxVal < minLimit or minVal > maxLimit:
                result.append(True)
            else:
                result.append(False)

        return tuple(result)


    def __str__(self):
        return "<DisplayedSpectrum: strip: %s; spectrumView: %s>" % (
            self.strip.pid, self.spectrumView.pid
        )

    __repr__ = __str__
