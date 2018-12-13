"""
GUI Display Strip class
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:41 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Sequence, Tuple, List
from functools import partial
from ccpn.util import Common as commonUtil
from ccpn.core.Peak import Peak
from ccpn.core.Spectrum import Spectrum
from ccpn.core.PeakList import PeakList
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.ui._implementation.SpectrumDisplay import SpectrumDisplay
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import BoundStrip as ApiBoundStrip
from ccpn.util.Logging import getLogger
from collections import OrderedDict
from ccpn.core.lib.OrderedSpectrumViews import OrderedSpectrumViews
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import undoBlock, logCommandBlock, undoStackBlocking, notificationBlanking, \
    newObject, deleteObject


# SV_TITLE = '_Strip'


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

    # def _retrieveOrderedSpectrumViews(self, pid):
    #   for dd in self.project.dataSets:
    #     if dd.title == SV_TITLE:
    #       for dt in dd.data:
    #         if dt.name == SV_SPECTRA:
    #           if pid in dt.parameters:
    #             return dt.parameters[self.pid]
    #   return None
    #
    # def _storeOrderedSpectrumViews(self, spectra):
    #   for dd in self.project.dataSets:
    #     if dd.title == SV_TITLE:
    #       for dt in dd.data:
    #         if dt.name == SV_SPECTRA:
    #           dt.setParameter(self.pid, spectra)
    #           setattr(self, SV_SPECTRA, spectra)
    #           return
    #       dt = dd.newData(name=SV_SPECTRA)
    #       dt.setParameter(self.pid, spectra)
    #       setattr(self, SV_SPECTRA, spectra)
    #       return
    #   dd = self.project.newDataSet(title=SV_TITLE)
    #   dt = dd.newData(name=SV_SPECTRA)
    #   dt.setParameter(self.pid, spectra)
    #   setattr(self, SV_SPECTRA, spectra)
    #
    #   self.spectrumDisplay._ccpnInternalData[SV_SPECTRA] = spectra
    #
    # def orderedSpectra(self) -> Optional[Tuple[Spectrum, ...]]:
    #   """The spectra attached to the strip (ordered)"""
    #
    #   if hasattr(self, SV_SPECTRA):
    #     return tuple(x.spectrum for x in getattr(self, SV_SPECTRA) if 'Deleted' not in x.pid)
    #   else:
    #     # create a dataset with the spectrumViews attached (will be alphabetical) if doesn't exist
    #     # store by pids
    #
    #     values = self._retrieveOrderedSpectrumViews(self.pid)
    #     if values is None:
    #       self._storeOrderedSpectrumViews(tuple(x.pid for x in self.spectrumViews))
    #       values = tuple(x for x in self.spectrumViews)
    #     else:
    #       values = tuple(self.project.getByPid(x) for x in values if self.project.getByPid(x))
    #
    #     setattr(self, SV_SPECTRA, values)
    #     return tuple(x.spectrum for x in values)
    #
    # def orderedSpectrumViews(self, includeDeleted=False) -> Optional[Tuple]:
    #   """The spectra attached to the strip (ordered)"""
    #
    #   if hasattr(self, SV_SPECTRA):
    #     return getattr(self, SV_SPECTRA)
    #   else:
    #     # create a dataset with the spectrumViews attached (will be alphabetical) if doesn't exist
    #     # store by pid
    #     values = self._retrieveOrderedSpectrumViews(self.pid)
    #     if values is None:
    #       self._storeOrderedSpectrumViews(tuple(x.pid for x in self.spectrumViews))
    #       values = tuple(x for x in self.spectrumViews)
    #     else:
    #       values = tuple(self.project.getByPid(x) for x in values if self.project.getByPid(x))
    #
    #     setattr(self, SV_SPECTRA, values)
    #     return values
    #
    # def appendSpectrumView(self, spectrumView):
    #   # retrieve the list from the dataset
    #   # append to the end
    #   # write back to the dataset
    #   if hasattr(self, SV_SPECTRA):
    #     spectra = (getattr(self, SV_SPECTRA), (spectrumView,))
    #     spectra = tuple(j for i in spectra for j in i)
    #   else:
    #     spectra = tuple(spectrumView,)
    #
    #   self._storeOrderedSpectrumViews(tuple(x.pid for x in spectra))
    #   self.spectrumDisplay._ccpnInternalData[SV_SPECTRA] = tuple(x.pid for x in spectra)
    #
    #   values = tuple(x for x in spectra)
    #   setattr(self, SV_SPECTRA, values)
    #
    # def removeSpectrumView(self, spectrumView):
    #   # TODO:ED handle deletion - may not need anything here
    #   pass

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: SpectrumDisplay) -> list:
        """Get wrappedData (ccpnmr.gui.Task.Strip) in serial number order"""
        return parent._wrappedData.sortedStrips()

    def _finaliseAction(self, action: str):
        super()._finaliseAction(action)

        if action in ['create']:
            for sv in self.spectrumViews:
                sv._finaliseAction(action)

                for plv in sv.peakListViews:
                    plv._finaliseAction(action)
                for ilv in sv.integralListViews:
                    plv._finaliseAction(action)
                for mlv in sv.multipletListViews:
                    mlv._finaliseAction(action)

    # @deleteObject()         # - doesn't work here
    def _delete(self):
        """delete the wrappedData.
        CCPN Internal
        """
        self._wrappedData.delete()

    def _setStripIndex(self, index):
        """Set the index of the current strip in the wrapped data
        CCPN Internal
        """
        ccpnStrip = self._wrappedData
        ccpnStrip.__dict__['index'] = index  # this is the api creation of orderedStrips

    def stripIndex(self):
        """return the index of the current strip in the spectrumDisplay
        """
        # original api indexing
        ccpnStrip = self._wrappedData
        index = ccpnStrip.index
        # spectrumDisplay = self.spectrumDisplay
        # index = spectrumDisplay.strips.index(self)
        return index

    def delete(self):
        """trap this delete
        """
        raise RuntimeError('Please use spectrumDisplay.deleteStrip()')

    def _removeOrderedSpectrumViewIndex(self, index):
        self.spectrumDisplay.removeOrderedSpectrumView(index)

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
    def moveStrip(self, newIndex):
        """Move strip to index newIndex in orderedStrips
        """
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

    def resetAxisOrder(self):
        """Reset display to original axis order"""
        with logCommandBlock(get='self') as log:
            log('resetAxisOrder')
            self._wrappedData.resetAxisOrder()

    def findAxis(self, axisCode):
        """Find axis"""
        return self._project._data2Obj.get(self._wrappedData.findAxis(axisCode))

    def displaySpectrum(self, spectrum: Spectrum, axisOrder: Sequence = ()):
        """Display additional spectrum on strip, with spectrum axes ordered according to axisOrder
        """
        getLogger().debug('Strip.displaySpectrum>>> %s' % spectrum)

        spectrum = self.getByPid(spectrum) if isinstance(spectrum, str) else spectrum

        # TODO:ED fix the ordering of the spectra
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

        with logCommandBlock(get='self') as log:
            log('displaySpectrum', spectrum=repr(spectrum.pid))

            # Make spectrumView
            obj = apiStrip.spectrumDisplay.newSpectrumView(spectrumName=dataSource.name,
                                                           stripSerial=stripSerial, dataSource=dataSource,
                                                           dimensionOrdering=dimensionOrdering)
        result = self._project._data2Obj[apiStrip.findFirstStripSpectrumView(spectrumView=obj)]

        return result

    def peakIsInPlane(self, peak: Peak) -> bool:
        """Is peak in currently displayed planes for strip?
        """
        spectrumView = self.findSpectrumView(peak.peakList.spectrum)
        if spectrumView is None:
            return False
        displayIndices = spectrumView._displayOrderSpectrumDimensionIndices
        orderedAxes = self.orderedAxes[2:]

        for ii, displayIndex in enumerate(displayIndices[2:]):
            if displayIndex is not None:
                # If no axis matches the index may be None
                zPosition = peak.position[displayIndex]
                if not zPosition:
                    return False
                zPlaneSize = 0.
                zRegion = orderedAxes[ii].region
                if zPosition < zRegion[0] - zPlaneSize or zPosition > zRegion[1] + zPlaneSize:
                    return False

        return True

        # apiSpectrumView = self._wrappedData.findFirstSpectrumView(
        #   dataSource=peak._wrappedData.peakList.dataSource)
        #
        # if apiSpectrumView is None:
        #   return False
        #
        #
        # orderedAxes = self.orderedAxes
        # for ii,zDataDim in enumerate(apiSpectrumView.orderedDataDims[2:]):
        #   if zDataDim:
        #     zPosition = peak.position[zDataDim.dimensionIndex]
        #     # NBNB W3e do not think this should add anything - the region should be set correctly.
        #     # RHF, WB
        #     # zPlaneSize = zDataDim.getDefaultPlaneSize()
        #     zPlaneSize = 0.
        #     zRegion = orderedAxes[2+ii].region
        #     if zPosition < zRegion[0]-zPlaneSize or zPosition > zRegion[1]+zPlaneSize:
        #       return False
        # #
        # return True

    def peakIsInFlankingPlane(self, peak: Peak) -> bool:
        """Is peak in planes flanking currently displayed planes for strip?
        """
        spectrumView = self.findSpectrumView(peak.peakList.spectrum)
        if spectrumView is None:
            return False
        displayIndices = spectrumView._displayOrderSpectrumDimensionIndices
        orderedAxes = self.orderedAxes[2:]

        for ii, displayIndex in enumerate(displayIndices[2:]):
            if displayIndex is not None:
                # If no axis matches the index may be None
                zPosition = peak.position[displayIndex]
                if not zPosition:
                    return False
                zRegion = orderedAxes[ii].region
                zWidth = orderedAxes[ii].width
                if zRegion[0] - zWidth < zPosition < zRegion[0] or zRegion[1] < zPosition < zRegion[1] + zWidth:
                    return True

        return False

    @logCommand(get='self')
    def peakPickPosition(self, inPosition) -> Tuple[Peak]:
        """Pick peak at position for all spectra currently displayed in strip.
        """
        _preferences = self.application.preferences.general

        result = []
        peakLists = []

        with undoBlock():
            for spectrumView in (v for v in self.spectrumViews if v.isVisible()):

                validPeakListViews = [pp for pp in spectrumView.peakListViews if isinstance(pp.peakList, PeakList)
                                      and pp.isVisible()
                                      and spectrumView.isVisible()]

                for thisPeakListView in validPeakListViews:
                    # find the first visible peakList
                    peakList = thisPeakListView.peakList

                    position = inPosition
                    if spectrumView.spectrum.dimensionCount > 1:
                        # sortedSelectedRegion =[list(sorted(x)) for x in selectedRegion]
                        spectrumAxisCodes = spectrumView.spectrum.axisCodes
                        stripAxisCodes = self.axisCodes
                        position = [0] * spectrumView.spectrum.dimensionCount

                        remapIndices = commonUtil._axisCodeMapIndices(stripAxisCodes, spectrumAxisCodes)
                        if remapIndices:
                            for n, axisCode in enumerate(spectrumAxisCodes):
                                # idx = stripAxisCodes.index(axisCode)

                                idx = remapIndices[n]
                                # sortedSpectrumRegion[n] = sortedSelectedRegion[idx]
                                position[n] = inPosition[idx]
                        else:
                            position = inPosition

                    peak = peakList.newPeak(ppmPositions=position)

                    result.append(peak)
                    peakLists.append(peakList)

            self.current.peaks = result

        return tuple(result), tuple(peakLists)

    def peakPickRegion(self, selectedRegion: List[List[float]]) -> Tuple[Peak]:
        """Peak pick all spectra currently displayed in strip in selectedRegion.
        """
        result = []

        project = self.project
        minDropfactor = self.application.preferences.general.peakDropFactor

        with logCommandBlock(get='self') as log:
            log('peakPickRegion')
            with notificationBlanking():

                for spectrumView in self.spectrumViews:

                    numPeakLists = [pp for pp in spectrumView.peakListViews if isinstance(pp.peakList, PeakList)]
                    if not numPeakLists:  # this can happen if no peakLists, so create one
                        self._project.unblankNotification()  # need this otherwise SideBar does not get updated
                        spectrumView.spectrum.newPeakList()
                        self._project.blankNotification()

                    validPeakListViews = [pp for pp in spectrumView.peakListViews if isinstance(pp.peakList, PeakList)
                                          and pp.isVisible()
                                          and spectrumView.isVisible()]
                    # if numPeakLists:
                    for thisPeakListView in validPeakListViews:
                        # find the first visible peakList
                        peakList = thisPeakListView.peakList

                        # peakList = spectrumView.spectrum.peakLists[0]

                        if spectrumView.spectrum.dimensionCount > 1:
                            sortedSelectedRegion = [list(sorted(x)) for x in selectedRegion]
                            spectrumAxisCodes = spectrumView.spectrum.axisCodes
                            stripAxisCodes = self.axisCodes
                            sortedSpectrumRegion = [0] * spectrumView.spectrum.dimensionCount

                            remapIndices = commonUtil._axisCodeMapIndices(stripAxisCodes, spectrumAxisCodes)
                            if remapIndices:
                                for n, axisCode in enumerate(spectrumAxisCodes):
                                    # idx = stripAxisCodes.index(axisCode)
                                    idx = remapIndices[n]
                                    sortedSpectrumRegion[n] = sortedSelectedRegion[idx]
                            else:
                                sortedSpectrumRegion = sortedSelectedRegion

                            newPeaks = peakList.pickPeaksNd(sortedSpectrumRegion,
                                                            doPos=spectrumView.displayPositiveContours,
                                                            doNeg=spectrumView.displayNegativeContours,
                                                            fitMethod='gaussian', minDropfactor=minDropfactor)
                        else:
                            # 1D's
                            # NBNB This is a change - valuea are now rounded to three decimal places. RHF April 2017
                            newPeaks = peakList.pickPeaks1d(selectedRegion[0], sorted(selectedRegion[1]), size=minDropfactor * 100)

                        result.extend(newPeaks)

        for peak in result:
            peak._finaliseAction('create')

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

    stripCount = self.stripCount
    if newIndex and newIndex >= stripCount:
        # Put strip at the right, which means newIndex should be None
        if newIndex > stripCount:
            # warning
            self._project._logger.warning(
                    "Attempt to copy strip to position %s in display with only %s strips"
                    % (newIndex, stripCount))
        newIndex = None

    with logCommandBlock(prefix='newStrip=', get='self') as log:
        log('copyStrip', strip=repr(strip.pid))

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


# #TODO:RASMUS: if this is a SpectrumDisplay thing, it should not be here
# # SpectrumDisplay.orderedStrips property
# def getter(self) -> Tuple[Strip, ...]:
#     ff = self._project._data2Obj.get
#     return tuple(ff(x) for x in self._wrappedData.orderedStrips)
#
#
# def setter(self, value: Sequence):
#     value = [self.getByPid(x) if isinstance(x, str) else x for x in value]
#     self._wrappedData.orderedStrips = tuple(x._wrappedData for x in value)
#
#
# SpectrumDisplay.orderedStrips = property(getter, setter, None,
#                                          "ccpn.Strips in displayed order ")
# del getter
# del setter

# SHOULD NOT BE HERE like this
# Drag-n-drop functions:
#Strip.processSpectrum = Strip.displaySpectrum
