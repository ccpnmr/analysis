"""
GUI Display Strip class
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
__dateModified__ = "$dateModified: 2021-06-28 19:12:27 +0100 (Mon, June 28, 2021) $"
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


STRIPTILING = 'stripTiling'
STRIPTILEPOSITION = 'stripTilePosition'


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

    # store the list of ordered spectrumViews
    _orderedSpectrumViews = None

    #-----------------------------------------------------------------------------------------
    # Attributes and methods related to the data structure
    #-----------------------------------------------------------------------------------------

    @property
    def spectrumDisplay(self) -> SpectrumDisplay:
        """SpectrumDisplay containing strip."""
        return self._project._data2Obj.get(self._wrappedData.spectrumDisplay)

    _parent = spectrumDisplay

    @property
    def spectrumViews(self) -> tuple:
        "SpectrumViews shown in Strip"
        pass
        # STUB for now; hot-fixed later
        # return tuple(self._project._data2Obj.get(x)
        #      for x in self._wrappedData.sortedStripSpectrumViews())

    # GWV 20/7/2021: not used
    # def findSpectrumView(self, spectrum):
    #     """find Strip.spectrumView that matches spectrum, or None if not present"""
    #     sViews = [sv for sv in self.spectrumViews if sv.spectrum == spectrum]
    #     return sViews[0] if len(sViews) == 1 else None

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

    #GWV: moved here from _implementation/Axis.py
    @property
    def orderedAxes(self) -> Tuple:
        """Axes in display order (X, Y, Z1, Z2, ...) """
        apiStrip = self._wrappedData
        ff = self._project._data2Obj.get
        return tuple(ff(apiStrip.findFirstStripAxis(axis=x)) for x in apiStrip.orderedAxes)

        # # NOTE: ED new code to read axes ignoring stripDirection
        # # All strips will return their own axes
        # stripSerial = apiStrip.stripSerial
        # apiSpectrumDisplay = apiStrip.spectrumDisplay
        # return tuple(ff(apiSpectrumDisplay.findFirstAxis(code=x, stripSerial=stripSerial)) for x in apiSpectrumDisplay.axisOrder)

    @orderedAxes.setter
    def orderedAxes(self, value: Sequence):
        value = [self.getByPid(x) if isinstance(x, str) else x for x in value]
        #self._wrappedData.orderedAxes = tuple(x._wrappedData.axis for x in value)
        self._wrappedData.axisOrder = tuple(x.code for x in value)

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
        return self._wrappedData.units

    @property
    def spectra(self) -> Tuple[Spectrum, ...]:
        """The spectra attached to the strip (whether display is currently turned on  or not)"""
        return tuple(x.spectrum for x in self.spectrumViews)

    @property
    def spectrumGroups(self) -> Tuple[Spectrum, ...]:
        """The spectra attached to the strip (whether display is currently turned on  or not)"""
        pids = self.spectrumDisplay._getSpectrumGroups()
        return tuple(self.project.getByPid(x) for x in pids)

    #=========================================================================================
    # CCPN properties
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
        index = ccpnStrip.index
        # spectrumDisplay = self.spectrumDisplay
        # index = spectrumDisplay.strips.index(self)
        return index

    # from ccpn.util.decorators import profile
    # @profile
    def _clear(self):
        for spectrumView in self.spectrumViews:
            spectrumView.delete()

    def delete(self):
        """trap this delete
        """
        raise RuntimeError('Please use spectrumDisplay.deleteStrip()')

    def _removeOrderedSpectrumViewIndex(self, index):
        self.spectrumDisplay.removeOrderedSpectrumView(index)

    @property
    def tilePosition(self) -> Tuple[int, int]:
        """Returns a tuple of the tile coordinates (from top-left)
        tilePosition = (x, y)
        """
        tilePosition = self.getParameter(STRIPTILING, STRIPTILEPOSITION)
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

        self.setParameter(STRIPTILING, STRIPTILEPOSITION, value)

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

    @logCommand(get='self')
    def resetAxisOrder(self):
        """Reset display to original axis order"""
        with undoBlockWithoutSideBar():
            self._wrappedData.resetAxisOrder()

    def findAxis(self, axisCode):
        """Find axis"""
        return self._project._data2Obj.get(self._wrappedData.findAxis(axisCode))

    # @logCommand(get='self')
    # def displaySpectrum(self, spectrum: Spectrum, axisOrder: Sequence = ()):
    #     """Display additional spectrum on strip, with spectrum axes ordered according to axisOrder
    #     :return SpectrumView instance
    #     """
    #     return self._displaySpectrum(spectrum, axisOrder)

    # def _displaySpectrum(self, spectrum: Spectrum, axisOrder: Sequence = (), useUndoBlock=True):
    #     """Display additional spectrum on strip, with spectrum axes ordered according to axisOrder
    #     :return SpectrumView instance
    #     CCPNINTERNAL: also used in GuiSpectrumDisplay.displaySpectrum
    #     """
    #     from ccpn.ui._implementation.SpectrumView import _newSpectrumView
    #
    #     getLogger().debug('Strip._displaySpectrum>>> %s' % spectrum)
    #
    #     spectrum = self.getByPid(spectrum) if isinstance(spectrum, str) else spectrum
    #     if not isinstance(spectrum, Spectrum):
    #         raise ValueError('Expected Spectrum instance; got %s ' % str(spectrum))
    #
    #     dataSource = spectrum._wrappedData
    #     # if self._apiStrip.findFirstSpectrumView(dataSource=dataSource) is not None:
    #     #     getLogger().debug('Strip.displaySpectrum>>> spectrumView already displayed on %s' % self)
    #     #     return
    #
    #
    #
    #     displayAxisCodes = self.axisCodes
    #
    #     # # make axis mapping indices
    #     # if axisOrder and axisOrder != displayAxisCodes:
    #     #     # Map axes to axisOrder, and remap to original setting
    #     #     ll = _axisCodeMapIndices(spectrum.axisCodes, axisOrder)
    #     #     mapIndices = [ll[axisOrder.index(x)] for x in displayAxisCodes]
    #     # else:
    #     #     # Map axes to original display setting
    #     #     mapIndices = _axisCodeMapIndices(spectrum.axisCodes, displayAxisCodes)
    #     #
    #     # if mapIndices is None:
    #     #     getLogger().debug('Strip.displaySpectrum>>> mapIndices is None')
    #     #     return
    #     #
    #     # # if None in mapIndices[:2]: # make sure that x/y always mapped
    #     # #   return
    #     # if mapIndices[0] is None or mapIndices[1] is None and displayAxisCodes[1] != 'intensity':
    #     #     getLogger().debug('Strip.displaySpectrum>>> mapIndices, x/y not mapped')
    #     #     return
    #     #
    #     # if mapIndices.count(None) + spectrum.dimensionCount != len(mapIndices):
    #     #     getLogger().debug('Strip.displaySpectrum>>> mapIndices, dimensionCount not matching')
    #     #     return
    #
    #     # # Make dimensionOrdering
    #     # sortedDataDims = dataSource.sortedDataDims()
    #     # dimensionOrdering = []
    #     # for index in mapIndices:
    #     #     if index is None:
    #     #         dimensionOrdering.append(0)
    #     #     else:
    #     #         dimensionOrdering.append(sortedDataDims[index].dim)
    #
    #     if self.spectrumDisplay.is1D:
    #         dimensionOrdering = [1, 0]
    #     else:
    #         dimensionOrdering = spectrum.getByAxisCodes('dimensions', self.axisCodes, exactMatch=False)
    #
    #     # Make spectrumView
    #     if useUndoBlock:
    #         with undoBlockWithoutSideBar():
    #             result = _newSpectrumView(self.spectrumDisplay, spectrum, dimensionOrdering=dimensionOrdering)
    #     else:
    #         result = _newSpectrumView(self.spectrumDisplay, spectrum, dimensionOrdering=dimensionOrdering)
    #
    #     return result

    @logCommand(get='self')
    def createPeak(self, ppmPositions: List[float]) -> Tuple[Tuple[Peak, ...], Tuple[PeakList, ...]]:
        """Create peak at position for all spectra currently displayed in strip.
        """
        result = []
        peakLists = []

        with undoBlockWithoutSideBar():
            # create the axisDict for this spectrum
            axisDict = {axis: ppm for axis, ppm in zip(self.axisCodes, ppmPositions)}

            # loop through the visible spectra
            for spectrumView in (v for v in self.spectrumViews if v.isVisible()):

                spectrum = spectrumView.spectrum
                # get the list of visible peakLists
                validPeakListViews = [pp for pp in spectrumView.peakListViews if pp.isVisible()]
                if not validPeakListViews:
                    continue

                for thisPeakListView in validPeakListViews:
                    peakList = thisPeakListView.peakList

                    # pick the peak in this peakList
                    pk = spectrum.createPeak(peakList, **axisDict)
                    if pk:
                        result.append(pk)
                        peakLists.append(peakList)

            # set the current peaks
            self.current.peaks = result

        return tuple(result), tuple(peakLists)

    @logCommand(get='self')
    def pickPeaks(self, ppmRegions: List[List[float]]) -> Tuple[Peak, ...]:
        """Peak pick all spectra currently displayed in strip in selectedRegion.
        """
        # selectedRegion is rounded before-hand to 3 dp.
        result = []

        # get settings from preferences
        minDropFactor = self.application.preferences.general.peakDropFactor
        fitMethod = self.application.preferences.general.peakFittingMethod

        with undoBlockWithoutSideBar():
            # create the axisDict for this spectrum
            axisDict = {axis: ppms for axis, ppms in zip(self.axisCodes, ppmRegions)}

            # loop through the visible spectra
            for spectrumView in (v for v in self.spectrumViews if v.isVisible()):

                spectrum = spectrumView.spectrum

                # get the list of visible peakLists
                validPeakListViews = [pp for pp in spectrumView.peakListViews if pp.isVisible()]
                if not validPeakListViews:
                    continue

                myPeakPicker = spectrum.peakPicker
                if not myPeakPicker:
                    getLogger().warning(f'peakPicker not defined for {spectrum}')
                    continue

                # get parameters to apply to peak picker
                positiveThreshold = spectrum.positiveContourBase if spectrumView.displayPositiveContours else None
                negativeThreshold = spectrum.negativeContourBase if spectrumView.displayNegativeContours else None

                # set any additional parameters
                myPeakPicker.setParameters(dropFactor=minDropFactor,
                                           fitMethod=fitMethod,
                                           setLineWidths=True
                                           )

                for thisPeakListView in validPeakListViews:
                    peakList = thisPeakListView.peakList

                    # pick the peak in this peakList
                    newPeaks = spectrum.pickPeaks(peakList, positiveThreshold, negativeThreshold, **axisDict)
                    if newPeaks:
                        result.extend(newPeaks)

            return tuple(result)


@newObject(Strip)
def _newStrip(self):
    """Create new strip that duplicates this one, appending it at the end
    Does not handle any gui updating.
    """
    apiStrip = self._wrappedData.clone()
    result = self._project._data2Obj.get(apiStrip)
    if result is None:
        raise RuntimeError('Unable to generate new Strip item')

    return result


# newStrip functions
# We should NOT have any newStrip function, except possibly for FreeStrips
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


SpectrumDisplay.copyStrip = _copyStrip
del _copyStrip
