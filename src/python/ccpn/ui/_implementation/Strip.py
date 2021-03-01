"""
GUI Display Strip class
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
__dateModified__ = "$dateModified: 2021-03-01 11:22:50 +0000 (Mon, March 01, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Sequence, Tuple, List
from ccpn.util import Common as commonUtil
from ccpn.core.Peak import Peak
from ccpn.core.Spectrum import Spectrum
from ccpn.core.PeakList import PeakList
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.ui._implementation.SpectrumDisplay import SpectrumDisplay
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import BoundStrip as ApiBoundStrip
from ccpn.util.Logging import getLogger
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import undoBlock, newObject


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

    # CCPN properties
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

    @property
    def _parent(self) -> SpectrumDisplay:
        """SpectrumDisplay containing strip."""
        return self._project._data2Obj.get(self._wrappedData.spectrumDisplay)

    spectrumDisplay = _parent

    @property
    def axisCodes(self) -> Tuple[str, ...]:
        """Fixed string Axis codes in original display order (X, Y, Z1, Z2, ...)"""
        # TODO axisCodes shold be unique, but I am not sure this is enforced
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
        "Axes in display order (X, Y, Z1, Z2, ...) "
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

    # def clone(self):
    #     """create new strip that duplicates this one, appending it at the end
    #     """
    #
    #     #EJB 20181212: I think this is already deprecated in the refactored branch
    #
    #     # with logCommandBlock(prefix='newStrip=', get='self') as log:
    #     #     log('clone')
    #
    #     result = _newStrip(self)
    #     # with undoStackBlocking() as addUndoItem:
    #     #     newStrip = self._project._data2Obj.get(self._wrappedData.clone())
    #     #
    #     #     addUndoItem(undo=partial(self.spectrumDisplay.deleteStrip, newStrip),
    #     #                 redo=partial(self.spectrumDisplay._unDelete, newStrip))
    #
    #     return result

    def _clone(self):
        """create new strip that duplicates this one, appending it at the end
        """
        apiStrip = self._wrappedData.clone()
        result = self._project._data2Obj.get(apiStrip)
        if result is None:
            raise RuntimeError('Unable to generate new Strip item')

        return result

    # @newObject(Strip)
    # def clone(self):
    #     """create new strip that duplicates this one, appending it at the end
    #     """
    #     apiStrip = self._wrappedData.clone()
    #     result = self._project._data2Obj.get(apiStrip)
    #     if result is None:
    #         raise RuntimeError('Unable to generate new Strip item')
    #
    #     return result

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
        with undoBlock():
            self._wrappedData.resetAxisOrder()

    def findAxis(self, axisCode):
        """Find axis"""
        return self._project._data2Obj.get(self._wrappedData.findAxis(axisCode))

    @logCommand(get='self')
    def displaySpectrum(self, spectrum: Spectrum, axisOrder: Sequence = ()):
        return self._displaySpectrum(spectrum, axisOrder)

    def _displaySpectrum(self, spectrum: Spectrum, axisOrder: Sequence = (), useUndoBlock=True):
        """Display additional spectrum on strip, with spectrum axes ordered according to axisOrder
        """
        getLogger().debug('Strip.displaySpectrum>>> %s' % spectrum)

        spectrum = self.getByPid(spectrum) if isinstance(spectrum, str) else spectrum
        if not isinstance(spectrum, Spectrum):
            raise TypeError('spectrum %s is not of type Spectrum' % str(spectrum))

        dataSource = spectrum._wrappedData
        apiStrip = self._wrappedData
        if apiStrip.findFirstSpectrumView(dataSource=dataSource) is not None:
            getLogger().debug('Strip.displaySpectrum>>> spectrumView is not None')
            return

        displayAxisCodes = apiStrip.axisCodes

        # make axis mapping indices
        if axisOrder and axisOrder != displayAxisCodes:
            # Map axes to axisOrder, and remap to original setting
            ll = commonUtil._axisCodeMapIndices(spectrum.axisCodes, axisOrder)
            mapIndices = [ll[axisOrder.index(x)] for x in displayAxisCodes]
        else:
            # Map axes to original display setting
            mapIndices = commonUtil._axisCodeMapIndices(spectrum.axisCodes, displayAxisCodes)

        if mapIndices is None:
            getLogger().debug('Strip.displaySpectrum>>> mapIndices is None')
            return

        # if None in mapIndices[:2]: # make sure that x/y always mapped
        #   return
        if mapIndices[0] is None or mapIndices[1] is None and displayAxisCodes[1] != 'intensity':
            getLogger().debug('Strip.displaySpectrum>>> mapIndices, x/y not mapped')
            return

        if mapIndices.count(None) + spectrum.dimensionCount != len(mapIndices):
            getLogger().debug('Strip.displaySpectrum>>> mapIndices, dimensionCount not matching')
            return

        # Make dimensionOrdering
        sortedDataDims = dataSource.sortedDataDims()
        dimensionOrdering = []
        for index in mapIndices:
            if index is None:
                dimensionOrdering.append(0)
            else:
                dimensionOrdering.append(sortedDataDims[index].dim)

        # Set stripSerial
        if 'Free' in apiStrip.className:
            # Independent strips
            stripSerial = apiStrip.serial
        else:
            stripSerial = 0

        if useUndoBlock:
            with undoBlock():
                # Make spectrumView
                obj = apiStrip.spectrumDisplay.newSpectrumView(spectrumName=dataSource.name,
                                                               stripSerial=stripSerial, dataSource=dataSource,
                                                               dimensionOrdering=dimensionOrdering)
                result = self._project._data2Obj[apiStrip.findFirstStripSpectrumView(spectrumView=obj)]

        else:
            obj = apiStrip.spectrumDisplay.newSpectrumView(spectrumName=dataSource.name,
                                                           stripSerial=stripSerial, dataSource=dataSource,
                                                           dimensionOrdering=dimensionOrdering)
            result = self._project._data2Obj[apiStrip.findFirstStripSpectrumView(spectrumView=obj)]

        return result

    @logCommand(get='self')
    def peakPickPosition(self, inPosition) -> Tuple[Tuple[Peak, ...], Tuple[PeakList, ...]]:
        """Pick peak at position for all spectra currently displayed in strip.
        """
        _preferences = self.application.preferences.general

        result = []
        peakLists = []

        with undoBlock():
            for spectrumView in (v for v in self.spectrumViews if v.isVisible()):

                validPeakListViews = [pp for pp in spectrumView.peakListViews if pp.isVisible()]

                for thisPeakListView in validPeakListViews:
                    peakList = thisPeakListView.peakList

                    height = None
                    position = inPosition
                    if spectrumView.spectrum.dimensionCount > 1:
                        # sortedSelectedRegion =[list(sorted(x)) for x in selectedRegion]
                        spectrumAxisCodes = spectrumView.spectrum.axisCodes
                        stripAxisCodes = self.axisCodes

                        # position = [0] * spectrumView.spectrum.dimensionCount
                        # remapIndices = commonUtil._axisCodeMapIndices(stripAxisCodes, spectrumAxisCodes)
                        # if remapIndices:
                        #     for n, axisCode in enumerate(spectrumAxisCodes):
                        #         # idx = stripAxisCodes.index(axisCode)
                        #
                        #         idx = remapIndices[n]
                        #         # sortedSpectrumRegion[n] = sortedSelectedRegion[idx]
                        #         position[n] = inPosition[idx]
                        # else:
                        #     position = inPosition

                        indices = commonUtil.getAxisCodeMatchIndices(spectrumAxisCodes, stripAxisCodes)

                        # skip if no valid mapping
                        if None in indices:
                            continue

                        # map position to the spectrum
                        position = [inPosition[ind] for ii, ind in enumerate(indices)]

                        _height = spectrumView.spectrum.getHeight(ppmPositions=position)
                        peak = peakList.newPeak(ppmPositions=position, height=_height)
                        # peak.height = spectrumView.spectrum.getHeight(ppmPositions=position)
                    else:
                        # 1d position with height
                        _height = position[-1] # Don't use the interp height, pick where you click like nD.
                        peak = peakList.newPeak(ppmPositions=position, height=_height)

                    result.append(peak)
                    peakLists.append(peakList)

            # add the new peak to the current.peaks
            self.current.peaks = result

        return tuple(result), tuple(peakLists)

    # 20190510: ED removd these routines as there are far too many different ways to map axis codes
    # def _getAxisCodeDict(self, spectrum, selectedRegion):
    #     """Generate axisCode dict from the given selectedRegion ordered by strip axes, matched to spectrum.
    #     """
    #     sortedSelectedRegion = [list(sorted(x)) for x in selectedRegion]
    #
    #     # map the limits to the correct axisCodes
    #     axisCodeDict = {}
    #     if spectrum.dimensionCount > 1:
    #         spectrumAxisCodes = spectrum.axisCodes
    #         stripAxisCodes = self.axisCodes
    #
    #         # get the ordering of the strip axisCodes in the spectrum
    #         try:
    #             indices = spectrum.getByAxisCodes('indices', stripAxisCodes)
    #         except Exception as es:
    #
    #             # spectrum possibly not compatible here, may be 2d overlaid onto Nd
    #             indices = spectrum.getByAxisCodes('indices', stripAxisCodes[0:2])
    #
    #         # sort the axis limits by spectrum axis order
    #         for ii, ind in enumerate(indices):
    #             axisCodeDict[spectrumAxisCodes[ind]] = sortedSelectedRegion[ii]
    #
    #     else:
    #         spectrumAxisCodes = spectrum.axisCodes
    #         stripAxisCodes = self.axisCodes
    #
    #         # get the ordering of the strip axisCodes in the spectrum
    #         indices = (0, 1)  #spectrum.getByAxisCodes('indices', stripAxisCodes)
    #
    #         # sort the axis limits by spectrum axis order
    #         for n, axisCode in enumerate(spectrumAxisCodes):
    #             axisCodeDict[axisCode] = sortedSelectedRegion[indices[n]]
    #
    #     return axisCodeDict

    # def _getAxisCodeIndices(self, spectrum):
    #     """Return axisCode indices matched to spectrum.
    #     """
    #     stripAxisCodes = self.axisCodes
    #     if spectrum.dimensionCount > 1:
    #         # get the ordering of the strip axisCodes in the spectrum
    #         try:
    #             indices = spectrum.getByAxisCodes('indices', stripAxisCodes)
    #         except Exception as es:
    #             # spectrum possibly not compatible here, may be 2d overlaid onto Nd
    #             # use another nested check and then use the code from settingsWidget
    #             try:
    #                 indices = spectrum.getByAxisCodes('indices', stripAxisCodes[0:2])
    #
    #             except Exception as es:
    #
    #                 # final try with the complicated method
    #                 indices = self._getSpectrumAxisCodeIndexing(spectrum)
    #
    #
    #     else:
    #         # get the ordering of the strip axisCodes in the spectrum
    #         indices = spectrum.getByAxisCodes('indices', stripAxisCodes)
    #
    #     return indices

    # def _getSpectrumAxisCodeIndexing(self, spectrum):
    #
    #     from ccpn.util.Common import _axisCodeMapIndices, axisCodeMapping
    #
    #     maxLen = 0
    #     refAxisCodes = None
    #
    #     if len(self.axisCodes) > maxLen:
    #         maxLen = len(self.axisCodes)
    #         refAxisCodes = list(self.axisCodes)
    #
    #     if not maxLen:
    #         return
    #
    #     axisLabels = [set() for ii in range(maxLen)]
    #
    #     mappings = {}
    #     matchAxisCodes = spectrum.axisCodes
    #
    #     mapping = axisCodeMapping(refAxisCodes, matchAxisCodes)
    #     for k, v in mapping.items():
    #         if v not in mappings:
    #             mappings[v] = set([k])
    #         else:
    #             mappings[v].add(k)
    #
    #     mapping = axisCodeMapping(matchAxisCodes, refAxisCodes)
    #     for k, v in mapping.items():
    #         if v not in mappings:
    #             mappings[v] = set([k])
    #         else:
    #             mappings[v].add(k)
    #
    #     # example of mappings dict
    #     # ('Hn', 'C', 'Nh')
    #     # {'Hn': {'Hn'}, 'Nh': {'Nh'}, 'C': {'C'}}
    #     # {'Hn': {'H', 'Hn'}, 'Nh': {'Nh'}, 'C': {'C'}}
    #     # {'CA': {'C'}, 'Hn': {'H', 'Hn'}, 'Nh': {'Nh'}, 'C': {'CA', 'C'}}
    #     # {'CA': {'C'}, 'Hn': {'H', 'Hn'}, 'Nh': {'Nh'}, 'C': {'CA', 'C'}}
    #
    #     axisIndexing = {}
    #
    #     axisIndexing[spectrum] = [0 for ii in range(len(spectrum.axisCodes))]
    #
    #     # get the spectrum dimension axisCode, and see if is already there
    #     for specDim, specAxis in enumerate(spectrum.axisCodes):
    #
    #         if specAxis in refAxisCodes:
    #             axisIndexing[spectrum][specDim] = refAxisCodes.index(specAxis)
    #             axisLabels[axisIndexing[spectrum][specDim]].add(specAxis)
    #
    #         else:
    #             # if the axisCode is not in the reference list then find the mapping from the dict
    #             for k, v in mappings.items():
    #                 if specAxis in v:
    #                     # refAxisCodes[dim] = k
    #                     axisIndexing[spectrum][specDim] = refAxisCodes.index(k)
    #                     axisLabels[refAxisCodes.index(k)].add(specAxis)
    #
    #     axisLabels = [', '.join(ax) for ax in axisLabels]
    #     return list(axisIndexing.values())[0] if axisIndexing else None

    @logCommand(get='self')
    def peakPickRegion(self, selectedRegion: List[List[float]]) -> Tuple[Peak]:
        """Peak pick all spectra currently displayed in strip in selectedRegion.
        """

        from collections import OrderedDict
        from ccpn.util.Common import getAxisCodeMatchIndices

        result = []

        project = self.project
        minDropFactor = self.application.preferences.general.peakDropFactor
        fitMethod = self.application.preferences.general.peakFittingMethod

        # sort each of the regions
        sortedSelectedRegion = [list(sorted(x)) for x in selectedRegion]

        with undoBlock():
            for spectrumView in (v for v in self.spectrumViews if v.isVisible()):

                # create a peakList if there isn't one
                if not spectrumView.spectrum.peakLists:
                    spectrumView.spectrum.newPeakList()

                validPeakListViews = (pp for pp in spectrumView.peakListViews if pp.isVisible())
                indices = getAxisCodeMatchIndices(spectrumView.spectrum.axisCodes, self.axisCodes)

                # map the spectrum selectedRegions to the strip
                axisCodeDict = OrderedDict((code, sortedSelectedRegion[indices[ii]])
                                           for ii, code in enumerate(spectrumView.spectrum.axisCodes) if indices[ii] is not None)

                for thisPeakListView in validPeakListViews:

                    peakList = thisPeakListView.peakList

                    if spectrumView.spectrum.dimensionCount > 1:
                        # axisCodeDict = self._getAxisCodeDict(spectrumView.spectrum, selectedRegion)

                        newPeaks = peakList.pickPeaksRegion(axisCodeDict,
                                                            doPos=spectrumView.displayPositiveContours,
                                                            doNeg=spectrumView.displayNegativeContours,
                                                            fitMethod=fitMethod, minDropFactor=minDropFactor)

                    else:
                        peakFactor1D = self.application.preferences.general.peakFactor1D
                        selectedRegion = [[min(ss), max(ss)] for ss in selectedRegion]
                        newPeaks = peakList.pickPeaks1d(*selectedRegion, peakFactor1D=peakFactor1D)

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
    with undoBlock():

        if strip.spectrumDisplay is self:
            # Within same display. Not that useful, but harmless
            # newStrip = strip.clone()

            # clone the last strip
            newStrip = strip.spectrumDisplay.addStrip(strip)

            if newIndex is not None:
                newStrip.moveTo(newIndex)

        else:
            mapIndices = commonUtil._axisCodeMapIndices(strip.axisOrder, self.axisOrder)
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
