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
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Sequence, Tuple, List, Optional
from PyQt5 import QtGui, QtWidgets, Qt, QtCore
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

    # Implementation functions
    @classmethod
    def _getAllWrappedData(cls, parent: SpectrumDisplay) -> list:
        """get wrappedData (ccpnmr.gui.Task.Strip) in serial number order"""
        return parent._wrappedData.sortedStrips()

    def _delete(self):
        """delete the wrappedData
        """
        # print("_implentation.stip>>> _delete")
        self._wrappedData.delete()

    def _storeStripDeleteDict(self, currentIndex):
        """Store the current strip index in the wrappedData
        CCPN Internal
        """
        _stripDeleteDict = {'currentIndex': currentIndex}
        # ccpnStrip = self._wrappedData
        # ccpnStrip.__dict__['_stripDeleteDict'] = _stripDeleteDict

        self._ccpnInternalData['_stripDeleteDict'] = _stripDeleteDict

    def _getStripDeleteDict(self):
        """retrieve the old strip index from the wrappedData
        CCPN Internal
        """
        # ccpnStrip = self._wrappedData
        # _stripDeleteDict = ccpnStrip.__dict__['_stripDeleteDict']

        _stripDeleteDict = self._ccpnInternalData['_stripDeleteDict']
        return _stripDeleteDict['currentIndex']

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

    def _storeStripDelete(self):
        """store the api delete info
        CCPN Internal
        """
        self._unDeleteCall, self._unDeleteArgs = self._recoverApiObject(self)

    def _storeStripUnDelete(self):
        """retrieve the api deleted object
        CCPN Internal
        """
        self._unDeleteCall(*self._unDeleteArgs)

    def delete(self):
        """trap this delete
        """
        raise RuntimeError('Please use spectrumDisplay.deleteStrip()')

    # def _getWidgetFromLayout(self):
    #     ccpnStrip = self._wrappedData
    #     n = len(ccpnStrip.spectrumDisplay.strips)
    #     if n > 1:
    #         index = ccpnStrip.index
    #         spectrumDisplay = self.spectrumDisplay
    #         layout = spectrumDisplay.stripFrame.layout()
    #
    #         if layout:
    #             lRows = layout.rowCount()
    #             currentStripItem = None
    #
    #             for r in range(layout.rowCount()):
    #                 items = []
    #                 if spectrumDisplay.stripDirection == 'Y':
    #                     currentStripItem = layout.itemAtPosition(r, index)
    #                 elif spectrumDisplay.stripDirection == 'X':
    #                     currentStripItem = layout.itemAtPosition(index, 0)
    #
    #             return currentStripItem
    #     else:
    #         raise ValueError("The last strip in a display cannot be deleted")

    # def _removeFromLayout(self):
    #
    #     ccpnStrip = self._wrappedData
    #     # n = len(ccpnStrip.spectrumDisplay.orderedStrips)
    #     index = ccpnStrip.index
    #     spectrumDisplay = self.spectrumDisplay
    #     layout = spectrumDisplay.stripFrame.layout()
    #     n = layout.count()
    #
    #     if n > 1 and layout:
    #         _undo = self.project._undo
    #         if _undo is not None:
    #             _undo.increaseBlocking()
    #
    #         currentStripItem = self
    #         currentRow = 0
    #         currentIndex = index
    #         currentParent = self.parent()
    #         currentStripDirection = spectrumDisplay.stripDirection
    #         currentWrapped = ccpnStrip
    #
    #         self._widgets = []
    #         while layout.count():  # clear the layout and store
    #             self._widgets.append(layout.takeAt(0).widget())
    #         self._widgets.remove(self)
    #         # print ('>>> removeFromLayout', self, ' >>> ', self._widgets)
    #
    #         if spectrumDisplay.stripDirection == 'Y':
    #             for m, widgStrip in enumerate(self._widgets):  # build layout again
    #                 layout.addWidget(widgStrip, 0, m)
    #                 layout.setColumnStretch(m, 1)
    #                 layout.setColumnStretch(m + 1, 0)
    #         elif spectrumDisplay.stripDirection == 'X':
    #             for m, widgStrip in enumerate(self._widgets):  # build layout again
    #                 layout.addWidget(widgStrip, m, 0)
    #             layout.setColumnStretch(0, 1)
    #
    #         # move to widget store
    #         self.mainWindow._UndoWidgetStorage.layout().addWidget(self)
    #
    #         self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
    #
    #         # # TODO:ED HACK HACK HACK HACK - put ccpnStrip back into strips - not sure if needed here
    #         # if self not in ccpnStrip.spectrumDisplay.orderedStrips:
    #         #   # childrenDict = ccpnStrip.spectrumDisplay.__dict__.get('strips')
    #         #   # childrenDict[n] = ccpnStrip
    #         #   for order, cStrip in enumerate(self._widgets):
    #         #     cStrip._wrappedData.__dict__['index'] = order
    #         #     # ccpnStrip.__dict__['index'] = currentIndex-1
    #
    #         # store the old information
    #         _stripDeleteDict = {'currentRow': currentRow,
    #                             'currentIndex': currentIndex,
    #                             'currentStripDirection': currentStripDirection,
    #                             'currentStripItem': currentStripItem,
    #                             'currentParent': currentParent,
    #                             'currentWrapped': currentWrapped}
    #         ccpnStrip.__dict__['_stripDeleteDict'] = _stripDeleteDict
    #
    #         _undo = self.project._undo
    #         if _undo is not None:
    #             _undo.decreaseBlocking()
    #         self.spectrumDisplay.showAxes()
    #
    #     else:
    #         raise ValueError("The last strip in a display cannot be deleted")
    #
    # def _restoreToLayout(self):
    #     ccpnStrip = self._wrappedData
    #     # n = len(ccpnStrip.spectrumDisplay.orderedStrips)
    #
    #     index = ccpnStrip.index
    #     spectrumDisplay = self.spectrumDisplay
    #     layout = spectrumDisplay.stripFrame.layout()
    #     n = layout.count()
    #
    #     if layout:
    #         _undo = self.project._undo
    #         if _undo is not None:
    #             _undo.increaseBlocking()
    #
    #         _stripDeleteDict = ccpnStrip.__dict__['_stripDeleteDict']
    #         currentStripItem = _stripDeleteDict['currentStripItem']
    #         currentStripDirection = _stripDeleteDict['currentStripDirection']
    #         currentRow = _stripDeleteDict['currentRow']
    #         currentIndex = _stripDeleteDict['currentIndex']
    #         currentParent = _stripDeleteDict['currentParent']
    #         currentWrapped = _stripDeleteDict['currentWrapped']
    #
    #         self.mainWindow._UndoWidgetStorage.layout().removeWidget(self)
    #         # self.setParent(currentParent)
    #         self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)
    #
    #         self._widgets = []
    #         while layout.count():  # clear the layout and store
    #             self._widgets.append(layout.takeAt(0).widget())
    #         self._widgets.insert(currentIndex, self)
    #         # print ('>>> restoreToLayout', self, ' >>> ', self._widgets)
    #
    #         if spectrumDisplay.stripDirection == 'Y':
    #             for m, widgStrip in enumerate(self._widgets):  # build layout again
    #                 layout.addWidget(widgStrip, 0, m)
    #                 layout.setColumnStretch(m, 1)
    #         elif spectrumDisplay.stripDirection == 'X':
    #             for m, widgStrip in enumerate(self._widgets):  # build layout again
    #                 layout.addWidget(widgStrip, m, 0)
    #             layout.setColumnStretch(0, 1)
    #
    #         count = ccpnStrip.spectrumDisplay.__dict__
    #         field = ccpnStrip.spectrumDisplay._fieldNames
    #         strippy = ccpnStrip.spectrumDisplay.getOrderedStrips()
    #         # ccpnStrip.spectrumDisplay.newBoundStrip = [appWidg._wrappedData for appWidg in self._widgets]
    #
    #         # TODO:ED HACK HACK HACK HACK - put ccpnStrip back into strips
    #         if self not in ccpnStrip.spectrumDisplay.orderedStrips:
    #             # childrenDict = ccpnStrip.spectrumDisplay.__dict__.get('strips')
    #             # childrenDict[n] = ccpnStrip
    #             for order, cStrip in enumerate(self._widgets):
    #                 cStrip._wrappedData.__dict__['index'] = order  # this is the api creation of orderedStrips
    #                 # ccpnStrip.__dict__['index'] = currentIndex-1
    #
    #         _undo = self.project._undo
    #         if _undo is not None:
    #             _undo.decreaseBlocking()
    #
    #         self.spectrumDisplay.showAxes()
    #
    # #TODO:RASMUS: most of this below belongs in the Gui class or even the GuiSpectrumDisplay class (like adding, removing strips)
    # #TODO:ED: confer with rasmus and me to refactor while writing tests
    # def delete(self):
    #     """Overrides normal delete"""
    #     # currentStripItem = self._getWidgetFromLayout()
    #     # self.setParent(None)
    #
    #     ccpnStrip = self._wrappedData
    #     n = len(ccpnStrip.spectrumDisplay.strips)
    #     if n > 1:
    #         spectrumDisplay = self.spectrumDisplay
    #         layout = spectrumDisplay.stripFrame.layout()
    #
    #         if layout:  # should always be the case but play safe
    #
    #             self._removeFromLayout()  # adds nothing to the undo stack, so add it below
    #
    #             _undo = self.project._undo
    #             if _undo is not None:
    #                 _undo.newItem(self._restoreToLayout, self._removeFromLayout)
    #             self._unDeleteCall, self._unDeleteArgs = self._recoverApiObject(ccpnStrip)
    #             ccpnStrip.delete()
    #
    #         self.current.strip = spectrumDisplay.strips[-1]
    #     else:
    #         raise ValueError("The last strip in a display cannot be deleted")
    #
    # def _unDelete(self):
    #     """Overrides normal delete"""
    #     # currentStripItem = self._getWidgetFromLayout()
    #     # self.setParent(None)
    #
    #     # TODO:ED check this cheeky code :)
    #     self._unDeleteCall(*self._unDeleteArgs)  # recover the deleted apiStrip
    #
    #     ccpnStrip = self._wrappedData
    #
    #     n = len(ccpnStrip.spectrumDisplay.strips)
    #     if n > 1:
    #         spectrumDisplay = self.spectrumDisplay
    #         layout = spectrumDisplay.stripFrame.layout()
    #
    #         if layout:  # should always be the case but play safe
    #
    #             self._restoreToLayout()  # adds nothing to the undo stack, so add it below
    #
    #             _undo = self.project._undo
    #             if _undo is not None:
    #                 _undo.newItem(self._removeFromLayout, self._restoreToLayout)
    #
    #         self.current.strip = spectrumDisplay.strips[-1]
    #
    #     else:
    #         raise ValueError("The last strip in a display cannot be deleted")

    def _removeOrderedSpectrumViewIndex(self, index):
        self.spectrumDisplay.removeOrderedSpectrumView(index)

    #CCPN functions
    def clone(self):
        """create new strip that duplicates this one, appending it at the end"""
        self._startCommandEchoBlock('cloneStrip')

        _undo = self.project._undo
        if _undo is not None:
            _undo.increaseBlocking()

        try:
            newStrip = self._project._data2Obj.get(self._wrappedData.clone())
        finally:
            self._endCommandEchoBlock()

        if _undo is not None:
            _undo.decreaseBlocking()
            # _undo.newItem(newStrip.delete, newStrip._unDelete)
            _undo.newItem(self.spectrumDisplay.removeStrip, self.spectrumDisplay._unDelete,
                          undoArgs=(newStrip,), redoArgs=(newStrip,))

        return newStrip

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

    # def moveTo(self, newIndex: int):
    #     """Move strip to index newIndex in orderedStrips"""
    #
    #     currentIndex = self._wrappedData.index
    #     if currentIndex == newIndex:
    #         return
    #
    #     stripCount = self.spectrumDisplay.stripCount
    #
    #     if newIndex >= stripCount:
    #         # Put strip at the right, which means newIndex should be stripCount - 1
    #         if newIndex > stripCount:
    #             # warning
    #             self._project._logger.warning(
    #                     "Attempt to copy strip to position %s in display with only %s strips"
    #                     % (newIndex, stripCount))
    #         newIndex = stripCount - 1
    #
    #     self._startCommandEchoBlock('moveTo', newIndex)
    #     try:
    #         # management of API objects
    #         self._wrappedData.moveTo(newIndex)
    #     finally:
    #         self._endCommandEchoBlock()
    #
    #     # NB - no echo blocking below, as none of the layout stuff is modeled (?)
    #
    #     # NBNB TODO - should the stuff below not be moved to the corresponding GUI class?
    #     # Is there always a layout, regardless of application?
    #
    #     # management of Qt layout
    #     # TBD: need to soup up below with extra loop when have tiles
    #     spectrumDisplay = self.spectrumDisplay
    #     layout = spectrumDisplay.stripFrame.layout()
    #     if not layout:  # should always exist but play safe:
    #         return
    #
    #     for r in range(layout.rowCount()):
    #         items = []
    #         if spectrumDisplay.stripDirection == 'Y':
    #             if currentIndex < newIndex:
    #                 for n in range(currentIndex, newIndex + 1):
    #                     item = layout.itemAtPosition(r, n)
    #                     items.append(item)
    #                     layout.removeItem(item)
    #                 items = items[1:] + [items[0]]
    #                 for m, item in enumerate(items):
    #                     layout.addItem(item, r, m + currentIndex, )
    #             else:
    #                 for n in range(newIndex, currentIndex + 1):
    #                     item = layout.itemAtPosition(r, n)
    #                     items.append(item)
    #                     layout.removeItem(item)
    #                 items = [items[-1]] + items[:-1]
    #                 for m, item in enumerate(items):
    #                     layout.addItem(item, r, m + newIndex, )
    #
    #         elif spectrumDisplay.stripDirection == 'X':
    #             if currentIndex < newIndex:
    #                 for n in range(currentIndex, newIndex + 1):
    #                     item = layout.itemAtPosition(n, 0)
    #                     items.append(item)
    #                     layout.removeItem(item)
    #                 items = items[1:] + [items[0]]
    #                 for m, item in enumerate(items):
    #                     layout.addItem(item, m + currentIndex, 0)
    #             else:
    #                 for n in range(newIndex, currentIndex + 1):
    #                     item = layout.itemAtPosition(n, 0)
    #                     items.append(item)
    #                     layout.removeItem(item)
    #                 items = [items[-1]] + items[:-1]
    #                 for m, item in enumerate(items):
    #                     layout.addItem(item, m + newIndex, 0)

    def resetAxisOrder(self):
        """Reset display to original axis order"""
        self._startCommandEchoBlock('resetAxisOrder')
        try:
            self._wrappedData.resetAxisOrder()
        finally:
            self._endCommandEchoBlock()

    def findAxis(self, axisCode):
        """Find axis"""
        return self._project._data2Obj.get(self._wrappedData.findAxis(axisCode))

    def displaySpectrum(self, spectrum: Spectrum, axisOrder: Sequence = ()):
        """
        Display additional spectrum on strip, with spectrum axes ordered according to axisOrder
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

        self._startCommandEchoBlock('displaySpectrum', spectrum, values=locals(),
                                    defaults={'axisOrder': ()})
        try:
            # Make spectrumView
            obj = apiStrip.spectrumDisplay.newSpectrumView(spectrumName=dataSource.name,
                                                           stripSerial=stripSerial, dataSource=dataSource,
                                                           dimensionOrdering=dimensionOrdering)
        finally:
            self._endCommandEchoBlock()
        result = self._project._data2Obj[apiStrip.findFirstStripSpectrumView(spectrumView=obj)]
        #
        return result

    def peakIsInPlane(self, peak: Peak) -> bool:
        """is peak in currently displayed planes for strip?"""

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
        #
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
        """is peak in planes flanking currently displayed planes for strip?"""

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
        #
        return False

    def peakPickPosition_OLDplotWidget(self, position: List[float]) -> Tuple[Peak]:
        """Pick peak at position for all spectra currently displayed in strip"""

        result = []

        self._startCommandEchoBlock('peakPickPosition_OLD', position)
        self._project.blankNotification()
        try:
            for spectrumView in self.spectrumViews:
                if not spectrumView.peakListViews:  # this can happen if no peakLists, so create one
                    self._project.unblankNotification()  # need this otherwise SideBar does not get updated
                    spectrumView.spectrum.newPeakList()
                    self._project.blankNotification()
                peakListView = spectrumView.peakListViews[0]
                # TODO: is there some way of specifying which peakListView
                if not peakListView.isVisible():
                    continue
                peakList = peakListView.peakList

                peak = peakList.newPeak(position=position)
                # note, the height below is not derived from any fitting
                # but is a weighted average of the values at the neighbouring grid points
                peak.height = spectrumView.spectrum.getPositionValue(peak.pointPosition)
                result.append(peak)
        finally:
            self._endCommandEchoBlock()
            self._project.unblankNotification()

        for peak in result:
            peak._finaliseAction('create')
        #
        return tuple(result)

    def peakPickPosition(self, inPosition) -> Tuple[Peak]:
        """
        Pick peak at position for all spectra currently displayed in strip
        """
        _preferences = self.application.preferences.general

        result = []
        peakLists = []

        self._startCommandEchoBlock('peakPickPosition', inPosition)  #Dict)
        self._project.blankNotification()
        try:
            for spectrumView in self.spectrumViews:

                # check whether there any peakLists attached to the spectrumView - could be peakLists or integralLists
                numPeakLists = [pp for pp in spectrumView.peakListViews if isinstance(pp.peakList, PeakList)]
                if not numPeakLists:  # this can happen if no peakLists, so create one
                    # if not spectrumView.peakListViews:    # this can happen if no peakLists, so create one
                    self._project.unblankNotification()  # need this otherwise SideBar does not get updated
                    spectrumView.spectrum.newPeakList()
                    self._project.blankNotification()

                validPeakListViews = [pp for pp in spectrumView.peakListViews if isinstance(pp.peakList, PeakList)
                                      and pp.isVisible()
                                      and spectrumView.isVisible()]
                for thisPeakListView in validPeakListViews:
                    # find the first visible peakList
                    peakList = thisPeakListView.peakList

                    # for peakListView in spectrumView.peakListViews:
                    # find the first visible peakList
                    # if not peakListView.isVisible() or not spectrumView.isVisible():
                    #   continue

                    # peakList = peakListView.peakList

                    # if isinstance(peakList, PeakList):
                    peak = peakList.newPeak()

                    # change dict to position
                    # position = [0.0] * len(peak.axisCodes)
                    # for n, axis in enumerate(peak.axisCodes):
                    #   if _preferences.matchAxisCode == 0:  # default - match atom type
                    #     for ax in positionDict.keys():
                    #       if ax and axis and ax[0] == axis[0]:
                    #         position[n] = positionDict[ax]
                    #         break
                    #
                    #   elif _preferences.matchAxisCode == 1:  # match full code
                    #     if axis in positionDict.keys():
                    #       position[n] = positionDict[axis]

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

                    if peak.peakList.spectrum.dimensionCount == 1:
                        if len(position) > 1:
                            peak.position = (position[0],)
                            peak.height = position[1]
                    else:
                        peak.position = position
                        # note, the height below is not derived from any fitting
                        # but is a weighted average of the values at the neighbouring grid points
                        peak.height = spectrumView.spectrum.getPositionValue(peak.pointPosition)
                    result.append(peak)
                    peakLists.append(peakList)

        except Exception as es:
            pass

        finally:
            self._endCommandEchoBlock()
            self._project.unblankNotification()

        for peak in result:
            peak._finaliseAction('create')

        return tuple(result), tuple(peakLists)

    def peakPickRegion_OLD(self, selectedRegion: List[List[float]]) -> Tuple[Peak]:
        """Peak pick all spectra currently displayed in strip in selectedRegion """

        result = []

        project = self.project
        minDropfactor = self.application.preferences.general.peakDropFactor

        self._startCommandEchoBlock('peakPickRegion_OLD', selectedRegion)
        self._project.blankNotification()
        try:

            for spectrumView in self.spectrumViews:
                if not spectrumView.isVisible():
                    continue
                if not spectrumView.peakListViews:  # this can happen if no peakLists, so create one
                    self._project.unblankNotification()  # need this otherwise SideBar does not get updated
                    spectrumView.spectrum.newPeakList()
                    self._project.blankNotification()
                peakListView = spectrumView.peakListViews[0]
                # TODO: is there some way of specifying which peakListView
                if not peakListView.isVisible():
                    continue
                peakList = peakListView.peakList

                if spectrumView.spectrum.dimensionCount > 1:
                    sortedSelectedRegion = [list(sorted(x)) for x in selectedRegion]
                    spectrumAxisCodes = spectrumView.spectrum.axisCodes
                    stripAxisCodes = self.axisCodes
                    sortedSpectrumRegion = [0] * spectrumView.spectrum.dimensionCount

                    remapIndices = commonUtil._axisCodeMapIndices(stripAxisCodes, spectrumAxisCodes)
                    for n, axisCode in enumerate(spectrumAxisCodes):
                        # idx = stripAxisCodes.index(axisCode)
                        idx = remapIndices[n]
                        sortedSpectrumRegion[n] = sortedSelectedRegion[idx]
                    newPeaks = peakList.pickPeaksNd(sortedSpectrumRegion,
                                                    doPos=spectrumView.displayPositiveContours,
                                                    doNeg=spectrumView.displayNegativeContours,
                                                    fitMethod='gaussian', minDropfactor=minDropfactor)
                else:
                    # 1D's
                    # NBNB This is a change - valuea are now rounded to three decimal places. RHF April 2017
                    newPeaks = peakList.pickPeaks1d(selectedRegion[0], sorted(selectedRegion[1]))
                    # y0 = startPosition.y()
                    # y1 = endPosition.y()
                    # y0, y1 = min(y0, y1), max(y0, y1)
                    # newPeaks = peakList.pickPeaks1d([startPosition.x(), endPosition.x()], [y0, y1])

                result.extend(newPeaks)

                # # Add the new peaks to selection
                # for peak in newPeaks:
                #   # peak.isSelected = True
                #   self.current.addPeak(peak)

                # for window in project.windows:
                #   for spectrumDisplay in window.spectrumDisplays:
                #     for strip in spectrumDisplay.strips:
                #       spectra = [spectrumView.spectrum for spectrumView in strip.spectrumViews]
                #       if peakList.spectrum in spectra:
                #               strip.showPeaks(peakList)

        finally:
            self._endCommandEchoBlock()
            self._project.unblankNotification()

        for peak in result:
            peak._finaliseAction('create')
        #
        return tuple(result)

    def peakPickRegion(self, selectedRegion: List[List[float]]) -> Tuple[Peak]:
        """Peak pick all spectra currently displayed in strip in selectedRegion """

        result = []

        project = self.project
        minDropfactor = self.application.preferences.general.peakDropFactor

        self._startCommandEchoBlock('peakPickRegion', selectedRegion)
        self._project.blankNotification()
        try:

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
                        # y0 = startPosition.y()
                        # y1 = endPosition.y()
                        # y0, y1 = min(y0, y1), max(y0, y1)
                        # newPeaks = peakList.pickPeaks1d([startPosition.x(), endPosition.x()], [y0, y1])

                    result.extend(newPeaks)
                    # break

                # # Add the new peaks to selection
                # for peak in newPeaks:
                #   # peak.isSelected = True
                #   self.current.addPeak(peak)

                # for window in project.windows:
                #   for spectrumDisplay in window.spectrumDisplays:
                #     for strip in spectrumDisplay.strips:
                #       spectra = [spectrumView.spectrum for spectrumView in strip.spectrumViews]
                #       if peakList.spectrum in spectra:
                #               strip.showPeaks(peakList)

        finally:
            self._endCommandEchoBlock()
            self._project.unblankNotification()

        for peak in result:
            peak._finaliseAction('create')
        #
        return tuple(result)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ejb - orderedSpectrumViews, orderedSpectra
    # store the current orderedSpectrumViews in the internal data store
    # so it is hidden from external users
    # def orderedSpectrumViews(self, spectrumList, includeDeleted=False) -> Optional[Tuple]:
    #   """
    #   The spectrumViews attached to the strip (ordered)
    #   :return tuple of SpectrumViews:
    #   """
    #   return self.spectrumDisplay.orderedSpectrumViews(spectrumList)

    # def setOrderedSpectrumViews(self, spectrumViews: Tuple):
    #   """
    #   Set the ordering of the spectrumViews attached to the strip/spectrumDisplay
    #   :param spectrumViews - tuple of SpectrumView objects:
    #   """
    #   if not self._orderedSpectrumViews:
    #     self._orderedSpectrumViews = OrderedSpectrumViews(parent=self)
    #   self._orderedSpectrumViews.setOrderedSpectrumViews(spectrumViews)
    #
    # def _indexOrderedSpectrumViews(self, newIndex: Tuple[int]):
    #   """
    #   Set the new indexing of the spectrumViews attached to the strip/spectrumDisplay
    #   :param newIndex - tuple of int:
    #   """
    #   if not self._orderedSpectrumViews:
    #     self._orderedSpectrumViews = OrderedSpectrumViews(parent=self)
    #
    #   specViews = self._orderedSpectrumViews.orderedSpectrumViews()
    #   if len(set(newIndex)) != len(newIndex):
    #     raise ValueError('List contains duplicates')
    #   notDeletedViews = [spec for spec in specViews if not spec.isDeleted]
    #   if len(newIndex) != len(notDeletedViews):
    #     raise ValueError('List is not the correct length')
    #
    #   newSpecViews = [specViews[ii] for ii in newIndex]
    #   self._orderedSpectrumViews.setOrderedSpectrumViews(newSpecViews)
    #
    # def appendSpectrumView(self, spectrumView):
    #   """
    #   Append a SpectrumView to the end of the ordered spectrumviews
    #   :param spectrumView - new SpectrumView:
    #   """
    #   if not self._orderedSpectrumViews:
    #     self._orderedSpectrumViews = OrderedSpectrumViews(parent=self)
    #   self._orderedSpectrumViews.appendSpectrumView(spectrumView)
    #
    # def removeSpectrumView(self, spectrumView):
    #   """
    #   Remove a SpectrumView from the ordered spectrumviews
    #   :param spectrumView - SpectrumView to be removed:
    #   """
    #   if not self._orderedSpectrumViews:
    #     self._orderedSpectrumViews = OrderedSpectrumViews(parent=self)
    #   self._orderedSpectrumViews.removeSpectrumView(spectrumView)
    #
    # def copyOrderedSpectrumViews(self, fromStrip):
    #   """
    #   Copy the strip order from an adjacent strip
    #   :param fromStrip - source strip
    #   """
    #   if not self._orderedSpectrumViews:
    #     self._orderedSpectrumViews = OrderedSpectrumViews(parent=self)
    #   self._orderedSpectrumViews.copyOrderedSpectrumViews(fromStrip)

    # def orderedSpectra(self) -> Optional[Tuple[Spectrum, ...]]:
    #   """
    #   The spectra attached to the strip (ordered)
    #   :return tuple of spectra:
    #   """
    #   return self.spectrumDisplay.orderedSpectra()
    #
    # def orderedSpectrumViews(self, includeDeleted=False) -> Optional[Tuple]:
    #   """
    #   The spectrumViews attached to the strip (ordered)
    #   :return tuple of SpectrumViews:
    #   """
    #   return self.spectrumDisplay.orderedSpectrumViews()
    #
    # def setOrderedSpectrumViews(self, spectrumViews: Tuple):
    #   """
    #   Set the ordering of the spectrumViews attached to the strip/spectrumDisplay
    #   :param spectrumViews - tuple of SpectrumView objects:
    #   """
    #   self.spectrumDisplay.setOrderedSpectrumViews(spectrumViews)
    #
    # def appendSpectrumView(self, spectrumView):
    #   """
    #   Append a SpectrumView to the end of the ordered spectrumviews
    #   :param spectrumView - new SpectrumView:
    #   """
    #   self.spectrumDisplay.appendSpectrumView(spectrumView)
    #
    # def removeSpectrumView(self, spectrumView):
    #   """
    #   Remove a SpectrumView from the ordered spectrumviews
    #   :param spectrumView - SpectrumView to be removed:
    #   """
    #   self.spectrumDisplay.removeSpectrumView(spectrumView)

    @staticmethod
    def _recoverApiObject(strip):
        """recover the deleted api object by using the auto-generated code from the Model
        CCPN Internal
        """
        self = strip._wrappedData
        dataDict = self.__dict__
        topObject = dataDict.get('topObject')
        notInConstructor = not (dataDict.get('inConstructor'))

        root = dataDict.get('topObject').__dict__.get('memopsRoot')
        notOverride = not (root.__dict__.get('override'))
        notIsReading = not (topObject.__dict__.get('isReading'))
        notOverride = (notOverride and notIsReading)

        # objects to be deleted
        # This implementation could be greatly improve, but meanwhile this should work
        from ccpn.util.OrderedSet import OrderedSet
        from ccpnmodel.ccpncore.memops.ApiError import ApiError

        objsToBeDeleted = OrderedSet()
        # objects still to be checked for cascading delete (each object to be deleted gets checked)
        objsToBeChecked = list()
        # counter keyed on (obj, roleName) for how many objects at other end of link are to be deleted
        linkCounter = {}

        # topObjects to check if modifiable
        topObjectsToCheck = set()
        objsToBeChecked = list()
        # counter keyed on (obj, roleName) for how many objects at other end of link are to be deleted
        linkCounter = {}

        # topObjects to check if modifiable
        topObjectsToCheck = set()

        objsToBeChecked.append(self)
        while len(objsToBeChecked) > 0:
            obj = objsToBeChecked.pop()
            obj._checkDelete(objsToBeDeleted, objsToBeChecked, linkCounter, topObjectsToCheck)

        if (notInConstructor):
            for topObjectToCheck in topObjectsToCheck:
                if (not (topObjectToCheck.__dict__.get('isModifiable'))):
                    raise ApiError("""%s.delete:
           Storage not modifiable""" % self.qualifiedName
                                   + ": %s" % (topObjectToCheck,)
                                   )

        if (dataDict.get('isDeleted')):
            raise ApiError("""%s.delete:
       called on deleted object""" % self.qualifiedName
                           )

        # if ((notInConstructor and notOverride)):
        #
        #   for notify in self.__class__._notifies.get('startDeleteBlock', ()):
        #     notify(self)
        #
        #   for obj in reversed(objsToBeDeleted):
        #     for notify in obj.__class__._notifies.get('preDelete', ()):
        #       notify(obj)
        #
        # for obj in reversed(objsToBeDeleted):
        #   obj._singleDelete(objsToBeDeleted)

        # doNotifies

        # if ((notInConstructor and notOverride)):
        #
        #   for obj in reversed(objsToBeDeleted):
        #     for notify in obj.__class__._notifies.get('delete', ()):
        #       notify(obj)
        #
        #   for notify in self.__class__._notifies.get('endDeleteBlock', ()):
        #     notify(self)
        #

        # if ((not (dataDict.get('inConstructor')) and notIsReading)):
        #   # register Undo functions
        #
        #   _undo = root._undo
        #   if _undo is not None:

        # _undo.newItem(root._unDelete, self.delete, undoArgs=(objsToBeDeleted, topObjectsToCheck))
        return (root._unDelete, (objsToBeDeleted, topObjectsToCheck))


# newStrip functions
# We should NOT have any newStrip function, except possibly for FreeStrips
def _copyStrip(self: SpectrumDisplay, strip: Strip, newIndex=None) -> Strip:
    """Make copy of strip in self, at position newIndex - or rightmost"""

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

    self._startCommandEchoBlock('copyStrip', strip, values=locals(), defaults={'newIndex': None},
                                parName='newStrip')
    try:
        if strip.spectrumDisplay is self:
            # Within same display. Not that useful, but harmless
            newStrip = strip.clone()
            if newIndex is not None:
                newStrip.moveTo(newIndex)

        else:
            mapIndices = commonUtil._axisCodeMapIndices(strip.axisOrder, self.axisOrder)
            if mapIndices is None:
                raise ValueError("Strip %s not compatible with window %s" % (strip.pid, self.pid))
            else:
                positions = strip.positions
                widths = strip.widths
                newStrip = self.orderedStrips[0].clone()
                if newIndex is not None:
                    newStrip.moveTo(newIndex)
                for ii, axis in enumerate(newStrip.orderedAxes):
                    ind = mapIndices[ii]
                    if ind is not None and axis._wrappedData.axis.stripSerial != 0:
                        # Override if there is a mapping and axis is not shared for all strips
                        axis.position = positions[ind]
                        axis.widths = widths[ind]
    finally:
        self._endCommandEchoBlock()
    #
    return newStrip


SpectrumDisplay.copyStrip = _copyStrip
del _copyStrip


#TODO:RASMUS: if this is a SpectrumDisplay thing, it should not be here
# SpectrumDisplay.orderedStrips property
def getter(self) -> Tuple[Strip, ...]:
    ff = self._project._data2Obj.get
    return tuple(ff(x) for x in self._wrappedData.orderedStrips)


def setter(self, value: Sequence):
    value = [self.getByPid(x) if isinstance(x, str) else x for x in value]
    self._wrappedData.orderedStrips = tuple(x._wrappedData for x in value)


SpectrumDisplay.orderedStrips = property(getter, setter, None,
                                         "ccpn.Strips in displayed order ")
del getter
del setter

# SHOULD NOT BE HERE like this
# Drag-n-drop functions:
#Strip.processSpectrum = Strip.displaySpectrum
