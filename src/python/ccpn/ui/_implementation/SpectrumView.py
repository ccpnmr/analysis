"""Spectrum View in a specific SpectrumDisplay

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
__dateModified__ = "$dateModified: 2021-10-25 18:29:04 +0100 (Mon, October 25, 2021) $"
__version__ = "$Revision: 3.0.4 $"
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
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import SpectrumView as ApiSpectrumView
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import StripSpectrumView as ApiStripSpectrumView
from ccpn.core.Project import Project
from ccpn.core.Spectrum import Spectrum
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpn.core.lib.ContextManagers import newObject, deleteWrapperWithoutSideBar, \
    ccpNmrV3CoreUndoBlock, ccpNmrV3CoreSetter
from ccpn.ui._implementation.Strip import Strip
from ccpn.util.decorators import logCommand


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

    _CONTOURATTRIBUTELIST = '''negativeContourBase negativeContourCount negativeContourFactor
                            displayNegativeContours negativeContourColour
                            positiveContourBase positiveContourCount positiveContourFactor
                            displayPositiveContours positiveContourColour
                            sliceColour
                            '''

    #=========================================================================================
    # CCPN properties
    #=========================================================================================

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

    def delete(self):
        """trap this delete
        """
        raise RuntimeError('Please use spectrumDisplay.removeSpectrum()')

    @deleteWrapperWithoutSideBar()
    def _delete(self):
        """Delete SpectrumView from strip, should be unique.
        """
        self._wrappedData.spectrumView.delete()

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
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def positiveContourColour(self, value: str):
        if not isinstance(value, (str, type(None))):
            raise ValueError("positiveContourColour must be a string/None.")

        self._guiChanged = True
        self._wrappedData.spectrumView.positiveContourColour = value

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
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def negativeContourColour(self, value: str):
        if not isinstance(value, (str, type(None))):
            raise ValueError("negativeContourColour must be a string/None.")

        self._guiChanged = True
        self._wrappedData.spectrumView.negativeContourColour = value

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
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def sliceColour(self, value: str):
        if not isinstance(value, (str, type(None))):
            raise ValueError("sliceColour must be a string/None.")

        self._guiChanged = True
        self._wrappedData.spectrumView.sliceColour = value

    @property
    def spectrum(self) -> Spectrum:
        """Spectrum that SpectrumView refers to"""
        return self._project._data2Obj.get(self._wrappedData.spectrumView.dataSource)

    # @property
    # def dimensionOrdering(self) -> Tuple[int, ...]:
    #     """Axes Indices (zero-based) of spectrum dimensions in display order (x, y, Z1, ...)"""
    #     apiStripSpectrumView = self._wrappedData
    #     axisCodes = self.strip.axisCodes
    #     axisOrder = self.strip.axisOrder
    #
    #     # DimensionOrdering is one-origin (first dim is dim 1)
    #     dimensionOrdering = apiStripSpectrumView.spectrumView.dimensionOrdering
    #
    #     # Convert to zero-origin (for indices) and return
    #     ll = tuple(dimensionOrdering[axisCodes.index(x)] for x in axisOrder)
    #     return tuple((x or None) and x - 1 for x in ll)

    #=========================================================================================
    # Spectrum properties in displayOrder; convenience methods
    #=========================================================================================

    @property
    def dimensions(self) -> tuple:
        """Spectrum dimensions in display order"""
        return tuple(self._wrappedData.spectrumView.dimensionOrdering)

    @property
    def axes(self) -> tuple:
        """Spectrum axes in display order"""
        return tuple([dim - 1 for dim in self._wrappedData.spectrumView.dimensionOrdering])

    # deprecated
    dimensionOrdering = axes

    @property
    def axisCodes(self) -> list:
        """Spectrum axisCodes in display order"""
        return [self.spectrum.axisCodes[idx] for idx in self.axes if idx >= 0]

    @property
    def spectrumLimits(self) -> list:
        """Spectrum limits in display order"""
        _tmp = self.spectrum.spectrumLimits
        return [_tmp[idx] for idx in self.axes if idx >= 0]

    @property
    def aliasingLimits(self) -> list:
        """Spectrum aliasing limits in display order"""
        _tmp = self.spectrum.aliasingLimits
        return [_tmp[idx] for idx in self.axes if idx >= 0]

    @property
    def foldingLimits(self) -> list:
        """Spectrum folding limits in display order"""
        _tmp = self.spectrum.foldingLimits
        return [_tmp[idx] for idx in self.axes if idx >= 0]

    @property
    def valuesPerPoint(self) -> list:
        """Spectrum valuesPerPoint in display order"""
        _tmp = self.spectrum.valuesPerPoint
        return [_tmp[idx] for idx in self.axes if idx >= 0]

    def _getByDisplayOrder(self, parameterName) -> list:
        """Return parameter in displayOrder"""
        dims = [d for d in self.dimensions if d > 0]  # Filter the '0' dimension of 1D
        return list(self.spectrum.getByDimensions(parameterName=parameterName, dimensions=dims))

    def _getPointPosition(self, ppmPostions) -> tuple:
        """Convert the ppm-positions vector (in display order) to a position (1-based) vector
        in spectrum-dimension order, suitable to be used with getPlaneData
        """
        position = [1] * self.spectrum.dimensionCount
        for dim, ppmValue in zip(self.dimensions, ppmPostions):
            if dim > 0:
                # Intensity dimensions have dim=0, or axis=-1;
                p = self.spectrum.ppm2point(value=ppmValue, dimension=dim)
                position[dim - 1] = int(p + 0.5)

        return tuple(position)

    def _extractXYplaneToFile(self, ppmPositions):
        """Extract an XY (display order) plane
        :return Spectrum instance
        """
        position = self._getPointPosition(ppmPositions)
        axisCodes = self.axisCodes[0:2]
        plane = self.spectrum.extractPlaneToFile(axisCodes=axisCodes, position=position)
        return plane

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Strip) -> list:
        """get wrappedData (ccpnmr.gui.Task.SpectrumView) in serial number order
        """
        return sorted(parent._wrappedData.stripSpectrumViews,
                      key=operator.attrgetter('spectrumView.spectrumName'))

    @ccpNmrV3CoreUndoBlock()
    def clearContourAttributes(self):
        """Clear all the contour attributes associated with the spectrumView
        Attributes will revert to the spectrum values
        """
        _spectrum = self.spectrum
        for param in self._CONTOURATTRIBUTELIST.split():
            if hasattr(_spectrum, param):
                setattr(self, param, None)

    @ccpNmrV3CoreUndoBlock()
    def copyContourAttributesFromSpectrum(self):
        """Copy all the contour attributes associated with the spectrumView.spectrum
        to the spectrumView
        """
        _spectrum = self.spectrum
        for param in self._CONTOURATTRIBUTELIST.split():
            if hasattr(_spectrum, param):
                value = getattr(_spectrum, param)
                setattr(self, param, value)


#=========================================================================================
# New method
#=========================================================================================

# @newObject(SpectrumView)
# Cannot use the decorator
# """
#   File "/Users/geerten/Code/CCPNv3/CcpNmr/src/python/ccpn/core/lib/ContextManagers.py", line 638, in theDecorator
#     apiObjectsCreated = result._getApiObjectTree()
#   File "/Users/geerten/Code/CCPNv3/CcpNmr/src/python/ccpn/core/_implementation/AbstractWrapperObject.py", line 683, in _getApiObjectTree
#     obj._checkDelete(apiObjectlist, objsToBeChecked, linkCounter, topObjectsToCheck)  # This builds the list/set
#   File "/Users/geerten/Code/CCPNv3/CcpNmr/src/python/ccpnmodel/ccpncore/api/ccpnmr/gui/Task.py", line 28366, in _checkDelete
#     raise ApiError("StripSpectrumView %s: StripSpectrumViews can only be deleted when the SpectrumView or Strip is deleted." % self)
# ccpnmodel.ccpncore.memops.ApiError.ApiError: StripSpectrumView <ccpnmr.gui.Task.StripSpectrumView ['user', 'View', '1D_H', 1, <ccpnmr.gui.Task.SpectrumView ['user', 'View', '1D_H', 'AcetatePE', 0]>]>: StripSpectrumViews can only be deleted when the SpectrumView or Strip is deleted.
# """

def _newSpectrumView(display, spectrum, dimensionOrdering):
    """Create new SpectrumView
    """

    # # Set stripSerial
    # if 'Free' in apiStrip.className:
    #     # Independent strips
    #     stripSerial = apiStrip.serial
    # else:
    #     stripSerial = 0

    if not isinstance(spectrum, Spectrum):
        raise ValueError('invlaid spectrum; got %r' % spectrum)

    if not isinstance(dimensionOrdering, (list, tuple)) or len(dimensionOrdering) < 2:
        raise ValueError('invalid dimensionOrdering; got %r' % dimensionOrdering)

    obj = display._wrappedData.newSpectrumView(spectrumName=spectrum.name, stripSerial=0, dataSource=spectrum._wrappedData,
                                               dimensionOrdering=dimensionOrdering)

    # 20191113:ED testing - doesn't work yet, _data2Obj not created in correct place
    # GWV: don't know why, but only querying via the FindFirstStripSpectrumView seems to allows to yield the V2 object
    apiSpectrumView = display.strips[0]._wrappedData.findFirstStripSpectrumView(spectrumView=obj)
    newSpecView = display.project._data2Obj.get(apiSpectrumView)

    if newSpecView is None:
        raise RuntimeError('Failed to generate new SpectrumView instance')

    # NOTE:ED - 2021oct25 - @GWV not sure why this is here as overrides the .getter logic
    #   replaced with method
    # newSpecView.copyContourAttributesFromSpectrum()
    #
    # for param in '''negativeContourBase negativeContourCount negativeContourFactor
    #                 displayNegativeContours negativeContourColour
    #                 positiveContourBase positiveContourCount positiveContourFactor
    #                 displayPositiveContours positiveContourColour
    #                 sliceColour
    #              '''.split():
    #     if hasattr(spectrum, param):
    #         value = getattr(spectrum, param)
    #         setattr(newSpecView, param, value)

    return newSpecView


#=========================================================================================
# Notifiers:
#=========================================================================================

# Notify SpectrumView change when ApiSpectrumView changes (underlying object is StripSpectrumView)
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
