"""Spectrum View in a specific SpectrumDisplay

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
__dateModified__ = "$dateModified: 2020-11-02 17:47:52 +0000 (Mon, November 02, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import operator
from typing import Tuple
from functools import partial
from ccpn.core.Project import Project
from ccpn.core.Spectrum import Spectrum
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpn.ui._implementation.Strip import Strip
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import SpectrumView as ApiSpectrumView
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import StripSpectrumView as ApiStripSpectrumView
from ccpn.core.lib.ContextManagers import undoBlock, undoBlockWithoutSideBar, newObject, undoStackBlocking


class SpectrumView(AbstractWrapperObject):
    """Spectrum View for 1D or nD spectrum"""

    #: Short class name, for PID.
    shortClassName = 'GV'
    # Attribute it necessary as subclasses must use superclass className
    className = 'SpectrumView'

    _parentClass = Strip

    #: Name of plural link to instances of class
    _pluralLinkName = 'spectrumViews'

    #: List of child classes.
    _childClasses = []

    _isGuiClass = True

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiStripSpectrumView._metaclass.qualifiedName()

    # CCPN properties
    @property
    def _apiStripSpectrumView(self) -> ApiStripSpectrumView:
        """ CCPN SpectrumView matching SpectrumView"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """id string - spectrumName"""
        return self._wrappedData.spectrumView.spectrumName.translate(Pid.remapSeparators)

    @property
    def spectrumName(self) -> str:
        """Name of connected spectrum"""
        return self._wrappedData.spectrumView.spectrumName

    @property
    def _parent(self) -> Strip:
        """Strip containing stripSpectrumView."""
        return self._project._data2Obj.get(self._wrappedData.strip)

    strip = _parent

    # @deleteObject() - doesn't work here as works on _wrappedData.delete()
    def delete(self):
        """Delete SpectrumView for all strips.
        """
        with undoBlockWithoutSideBar():
            # self._finaliseAction('delete')
            # with notificationBlanking():

            index = self._parent.spectrumViews.index(self)
            parent = self._parent

            self._finaliseAction('delete')
            # with notificationBlanking():
            self._wrappedData.spectrumView.delete()

            parent._removeOrderedSpectrumViewIndex(index)

    #EJB 20181122: why????
    # @property
    # def experimentType(self) -> str:
    #     """Experiment type of attached experiment - used for reconnecting to correct spectrum"""
    #     return self._wrappedData.spectrumView.experimentType
    #
    # @experimentType.setter
    # def experimentType(self, value: str):
    #     self._wrappedData.spectrumView.experimentType = value

    @property
    def isDisplayed(self) -> bool:
        """True if this spectrum is displayed."""
        return self._wrappedData.spectrumView.isDisplayed

    @isDisplayed.setter
    def isDisplayed(self, value: bool):
        self._wrappedData.spectrumView.isDisplayed = value

    @property
    def positiveContourColour(self) -> str:
        """Colour identifier for positive contours.

        If not set for SpectrumView gives you the value for Spectrum.
        If set for SpectrumView overrides Spectrum value.
        Set SpectrumView value to None to return to non-local value"""
        wrappedData = self._wrappedData.spectrumView
        result = wrappedData.positiveContourColour
        if result is None:
            obj = wrappedData.dataSource
            result = obj and obj.positiveContourColour
        return result

    @positiveContourColour.setter
    def positiveContourColour(self, value: str):
        if not isinstance(value, (str, type(None))):
            raise ValueError("positiveContourColour must be a string/None.")

        with undoStackBlocking() as addUndoItem:
            # add undo/redo items to flag change of colour for the spectrumViews
            addUndoItem(redo=partial(setattr, self, '_guiChanged', True))

        self._guiChanged = True
        self._wrappedData.spectrumView.positiveContourColour = value

        with undoStackBlocking() as addUndoItem:
            addUndoItem(undo=partial(setattr, self, '_guiChanged', True))

    @property
    def positiveContourCount(self) -> int:
        """Number of positive contours.

        If not set for SpectrumView gives you the value for Spectrum.
        If set for SpectrumView overrides Spectrum value.
        Set SpectrumView value to None to return to non-local value"""
        wrappedData = self._wrappedData.spectrumView
        result = wrappedData.positiveContourCount
        if result is None:
            obj = wrappedData.dataSource
            result = obj and obj.positiveContourCount
        return result

    @positiveContourCount.setter
    def positiveContourCount(self, value: int):
        if self.positiveContourCount != value:
            self._wrappedData.spectrumView.positiveContourCount = value

    @property
    def positiveContourBase(self) -> float:
        """Base level for positive contours.

        If not set for SpectrumView gives you the value for Spectrum.
        If set for SpectrumView overrides Spectrum value.
        Set SpectrumView value to None to return to non-local value"""
        wrappedData = self._wrappedData.spectrumView
        result = wrappedData.positiveContourBase
        if result is None:
            obj = wrappedData.dataSource
            result = obj and obj.positiveContourBase
        return result

    @positiveContourBase.setter
    def positiveContourBase(self, value: float):
        if self.positiveContourBase != value:
            self._wrappedData.spectrumView.positiveContourBase = value

    @property
    def positiveContourFactor(self) -> float:
        """Level multiplication factor for positive contours.

        If not set for SpectrumView gives you the value for Spectrum.
        If set for SpectrumView overrides Spectrum value.
        Set SpectrumView value to None to return to non-local value"""
        wrappedData = self._wrappedData.spectrumView
        result = wrappedData.positiveContourFactor
        if result is None:
            obj = wrappedData.dataSource
            result = obj and obj.positiveContourFactor
        return result

    @positiveContourFactor.setter
    def positiveContourFactor(self, value: float):
        if self.positiveContourFactor != value:
            self._wrappedData.spectrumView.positiveContourFactor = value

    @property
    def displayPositiveContours(self) -> bool:
        """True if positive contours are displayed?"""
        return self._wrappedData.spectrumView.displayPositiveContours

    @displayPositiveContours.setter
    def displayPositiveContours(self, value: bool):
        self._wrappedData.spectrumView.displayPositiveContours = value

    @property
    def negativeContourColour(self) -> str:
        """Colour identifier for negative contours.

        If not set for SpectrumView gives you the value for Spectrum.
        If set for SpectrumView overrides Spectrum value.
        Set SpectrumView value to None to return to non-local value"""
        wrappedData = self._wrappedData.spectrumView
        result = wrappedData.negativeContourColour
        if result is None:
            obj = wrappedData.dataSource
            result = obj and obj.negativeContourColour
        return result

    @negativeContourColour.setter
    def negativeContourColour(self, value: str):
        if not isinstance(value, (str, type(None))):
            raise ValueError("negativeContourColour must be a string/None.")

        with undoStackBlocking() as addUndoItem:
            # add undo/redo items to flag change of colour for the spectrumViews
            addUndoItem(redo=partial(setattr, self, '_guiChanged', True))

        self._guiChanged = True
        self._wrappedData.spectrumView.negativeContourColour = value

        with undoStackBlocking() as addUndoItem:
            addUndoItem(undo=partial(setattr, self, '_guiChanged', True))

    @property
    def negativeContourCount(self) -> int:
        """Number of negative contours.

        If not set for SpectrumView gives you the value for Spectrum.
        If set for SpectrumView overrides Spectrum value.
        Set SpectrumView value to None to return to non-local value"""
        wrappedData = self._wrappedData.spectrumView
        result = wrappedData.negativeContourCount
        if result is None:
            obj = wrappedData.dataSource
            result = obj and obj.negativeContourCount
        return result

    @negativeContourCount.setter
    def negativeContourCount(self, value: int):
        if self.negativeContourCount != value:
            self._wrappedData.spectrumView.negativeContourCount = value

    @property
    def negativeContourBase(self) -> float:
        """Base level for negative contours.

        If not set for SpectrumView gives you the value for Spectrum.
        If set for SpectrumView overrides Spectrum value.
        Set SpectrumView value to None to return to non-local value"""
        wrappedData = self._wrappedData.spectrumView
        result = wrappedData.negativeContourBase
        if result is None:
            obj = wrappedData.dataSource
            result = obj and obj.negativeContourBase
        return result

    @negativeContourBase.setter
    def negativeContourBase(self, value: float):
        if self.negativeContourBase != value:
            self._wrappedData.spectrumView.negativeContourBase = value

    @property
    def negativeContourFactor(self) -> float:
        """Level multiplication factor for negative contours.

        If not set for SpectrumView gives you the value for Spectrum.
        If set for SpectrumView overrides Spectrum value.
        Set SpectrumView value to None to return to non-local value"""
        wrappedData = self._wrappedData.spectrumView
        result = wrappedData.negativeContourFactor
        if result is None:
            obj = wrappedData.dataSource
            result = obj and obj.negativeContourFactor
        return result

    @negativeContourFactor.setter
    def negativeContourFactor(self, value: float):
        if self.negativeContourFactor != value:
            self._wrappedData.spectrumView.negativeContourFactor = value

    @property
    def displayNegativeContours(self) -> bool:
        """True if negative contours are displayed?"""
        return self._wrappedData.spectrumView.displayNegativeContours

    @displayNegativeContours.setter
    def displayNegativeContours(self, value: bool):
        self._wrappedData.spectrumView.displayNegativeContours = value

    @property
    def positiveLevels(self) -> Tuple[float, ...]:
        """Positive contouring levels from lowest to highest"""
        number = self.positiveContourCount
        if number < 1:
            return tuple()
        else:
            result = [self.positiveContourBase]
            factor = self.positiveContourFactor
            for ii in range(1, number):
                result.append(factor * result[-1])
            #
            return tuple(result)

    @property
    def negativeLevels(self) -> Tuple[float, ...]:
        """Negative contouring levels from lowest to highest"""
        number = self.negativeContourCount
        if number < 1:
            return tuple()
        else:
            result = [self.negativeContourBase]
            factor = self.negativeContourFactor
            for ii in range(1, number):
                result.append(factor * result[-1])
            #
            return tuple(result)

    @property
    def sliceColour(self) -> str:
        """Colour for 1D slices and 1D spectra.

        If not set for SpectrumView gives you the value for Spectrum.
        If set for SpectrumView overrides Spectrum value.
        Set SpectrumView value to None to return to non-local value"""
        wrappedData = self._wrappedData.spectrumView
        result = wrappedData.sliceColour
        if result is None:
            obj = wrappedData.dataSource
            result = obj and obj.sliceColour
        return result

    @sliceColour.setter
    def sliceColour(self, value: str):
        if not isinstance(value, (str, type(None))):
            raise ValueError("sliceColour must be a string/None.")

        with undoStackBlocking() as addUndoItem:
            # add undo/redo items to flag change of colour for the spectrumViews
            addUndoItem(redo=partial(setattr, self, '_guiChanged', True))

        self._guiChanged = True
        self._wrappedData.spectrumView.sliceColour = value

        with undoStackBlocking() as addUndoItem:
            addUndoItem(undo=partial(setattr, self, '_guiChanged', True))

    @property
    def spectrum(self) -> Spectrum:
        """Spectrum that SpectrumView refers to"""
        return self._project._data2Obj.get(self._wrappedData.spectrumView.dataSource)

    @property
    def _displayOrderSpectrumDimensionIndices(self) -> Tuple[int, ...]:
        """Indices of spectrum dimensions in display order (x, y, Z1, ...)"""
        apiStripSpectrumView = self._wrappedData
        apiStrip = apiStripSpectrumView.strip

        axisCodes = apiStrip.axisCodes

        # DimensionOrdering is one-origin (first dim is dim 1)
        dimensionOrdering = apiStripSpectrumView.spectrumView.dimensionOrdering

        # Convert to zero-origin (for indices) and return
        ll = tuple(dimensionOrdering[axisCodes.index(x)] for x in apiStrip.axisOrder)
        return tuple(None if not x else x - 1 for x in ll)

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Strip) -> list:
        """get wrappedData (ccpnmr.gui.Task.SpectrumView) in serial number order
        """
        return sorted(parent._wrappedData.stripSpectrumViews,
                      key=operator.attrgetter('spectrumView.spectrumName'))

    def _finaliseAction(self, action: str):
        super(SpectrumView, self)._finaliseAction(action)

        # all are attached to the same click
        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

        GLSignals = GLNotifier(parent=self)
        GLSignals.emitPaintEvent()

#=========================================================================================
# Connections to parents:
#=========================================================================================

@newObject(SpectrumView)
def _newSpectrumView(display, spectrumName: str = None,
                        stripSerial: int = None, dataSource=None,
                        dimensionOrdering=None, **kwds):
    """Create new SpectrumView
    """
    # 20191113:ED testing - doesn't work yet, _data2Obj not created in correct place
    apiSpectrumView = display._wrappedData.newSpectrumView(spectrumName=spectrumName,
                                                 stripSerial=stripSerial, dataSource=dataSource,
                                                 dimensionOrdering=dimensionOrdering)

    result = display.project._data2Obj.get(apiSpectrumView)
    if result is None:
        raise RuntimeError('Unable to generate new SpectrumView item')

    return result

#=========================================================================================
# CCPN functions
#=========================================================================================


# newSpectrumView functions: None

# Spectrum.spectrumViews property
def getter(spectrum: Spectrum):
    return tuple(spectrum._project._data2Obj.get(y)
                 for x in spectrum._wrappedData.sortedSpectrumViews()
                 for y in x.sortedStripSpectrumViews())


Spectrum.spectrumViews = property(getter, None, None,
                                  "SpectrumViews showing Spectrum")


# Strip.spectrumViews property
def getter(strip: Strip):
    return tuple(strip._project._data2Obj.get(x)
                 for x in strip._wrappedData.sortedStripSpectrumViews())


Strip.spectrumViews = property(getter, None, None,
                               "SpectrumViews shown in Strip")
del getter


def _findSpectrumView(strip: Strip, spectrum: Spectrum) -> SpectrumView:
    """find Strip.spectrumView that matches spectrum"""
    dataSource = spectrum._wrappedData
    for stripSpectrumView in strip._wrappedData.sortedStripSpectrumViews():
        if stripSpectrumView.spectrumView.dataSource is dataSource:
            return strip._project._data2Obj.get(stripSpectrumView)
    #
    return None


Strip.findSpectrumView = _findSpectrumView
del _findSpectrumView

# Notifiers:
# Notify SpectrumView change when ApiSpectrumView changes (underlying object is StripSpectrumView)
# TODO change to calling _setupApiNotifier
Project._apiNotifiers.append(
        ('_notifyRelatedApiObject', {'pathToObject': 'stripSpectrumViews', 'action': 'change'},
         ApiSpectrumView._metaclass.qualifiedName(), '')
        )

#EJB 20181122: moved to Spectrum
# Notify SpectrumView change when Spectrum changes
# Bloody hell: as far as GWV understands the effect of this: a 'change' to a Spectrum object triggers
# a _finaliseAction('change') on each of the spectrum.spectrumViews objects, which then calls all
# ('SpectrumView','change') notifiers
# Spectrum._setupCoreNotifier('change', AbstractWrapperObject._finaliseRelatedObject,
#                             {'pathToObject': 'spectrumViews', 'action': 'change'})

# Links to SpectrumView and Spectrum are fixed after creation - any link notifiers should be put in
# create/destroy instead
