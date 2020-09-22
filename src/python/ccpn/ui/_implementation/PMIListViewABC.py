"""
Module Documentation here
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
__dateModified__ = "$dateModified: 2020-09-22 12:46:44 +0100 (Tue, September 22, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2020-05-26 14:50:42 +0000 (Tue, May 26, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

import re
import typing
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.ui._implementation.SpectrumView import SpectrumView
from ccpn.core.PMIListABC import MERITCOLOUR, MERITTHRESHOLD, MERITENABLED, MERITSETTINGS, \
    COLOURCHECK, LINECOLOUR, LINESETTINGS, INHERITCOLOUR


class PMIListViewABC(AbstractWrapperObject):
    """ListView for 1D or nD List"""

    #: Short class name, for PID.
    shortClassName = 'Undefined'
    # Attribute it necessary as subclasses must use superclass className
    className = 'Undefined'

    _parentClass = SpectrumView

    #: Name of plural link to instances of class
    _pluralLinkName = 'Undefined'

    #: List of child classes.
    _childClasses = []

    _isGuiClass = True

    # Qualified name of matching API class
    _apiClassQualifiedName = None

    # attributes required to be set for subclasses
    _apiListView = None
    _apiListSerial = None
    _apiList = None

    def _setListClasses(self):
        """Set the primary classType for the child list attached to this container
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    def _init(self):
        """Required to be called by the class constructor
        """
        self._setListClasses()

    #=========================================================================================
    # CCPN properties
    #=========================================================================================

    @property
    def _parent(self) -> SpectrumView:
        """SpectrumView containing ListView."""
        return self._project._data2Obj.get(self._wrappedData.stripSpectrumView)

    spectrumView = _parent

    def delete(self):
        """ListViews cannot be deleted, except as a byproduct of deleting other things"""
        raise Exception("%s cannot be deleted directly" % str(self._pluralLinkName))

    # @property
    # def _key(self) -> str:
    #     """id string - """
    #     return str(self._apiListSerial)
    #
    # @property
    # def _localCcpnSortKey(self) -> typing.Tuple:
    #     """Local sorting key, in context of parent."""
    #     return (self._apiListSerial,)

    @property
    def symbolStyle(self) -> str:
        """Symbol style for displayed markers.

        If not set for ListView gives you the value for List.
        If set for ListView overrides List value.
        Set ListView value to None to return to non-local value"""
        wrappedData = self._apiListView
        result = wrappedData.symbolStyle
        if result is None:
            obj = self._apiList
            result = obj and obj.symbolStyle
        return result

    @symbolStyle.setter
    def symbolStyle(self, value: str):
        if self.symbolStyle != value:
            self._apiListView.symbolStyle = value

    @property
    def symbolColour(self) -> str:
        """Symbol colour for displayed markers.

        symbolColour must be a valid hex colour string '#ABCDEF' or '#' to denote an auto-colour (take colour from spectrum).
        Can also be None or ''. Lowercase will be changed to uppercase.

        If not set for ListView gives you the value for List.
        If set for ListView overrides List value.
        Set ListView value to None to return to non-local value"""
        wrappedData = self._apiListView
        result = wrappedData.symbolColour
        if result in (INHERITCOLOUR, None):
            obj = self._apiList
            result = obj and obj.symbolColour
        return result

    @symbolColour.setter
    def symbolColour(self, value: typing.Optional[str]):
        # ccpnInternal - changes this to '#' for non-valid colour check to validate in model
        if not isinstance(value, (str, type(None))):
            raise TypeError("symbolColour must be a hex colour string (e.g. '#ABCDEF' or '%s') or None" % INHERITCOLOUR)
        if value:
            # a non-empty string
            if not (re.findall(COLOURCHECK, value) or value == INHERITCOLOUR):
                raise ValueError("symbolColour %s not defined correctly, must be a hex colour string (e.g. '#ABCDEF' or '%s')" % (value, INHERITCOLOUR))
            value = value.upper()

        self._apiListView.symbolColour = value or INHERITCOLOUR

    @property
    def textColour(self) -> str:
        """Text colour for displayed markers.

        textColour must be a valid hex colour string '#ABCDEF' or '#' to denote an auto-colour (take colour from spectrum).
        Can also be None or ''. Lowercase will be changed to uppercase.

        If not set for ListView gives you the value for List.
        If set for ListView overrides List value.
        Set ListView value to None to return to non-local value"""
        wrappedData = self._apiListView
        result = wrappedData.textColour
        if result in (INHERITCOLOUR, None):
            obj = self._apiList
            result = obj and obj.textColour
        return result

    @textColour.setter
    def textColour(self, value: typing.Optional[str]):
        # ccpnInternal - changes this to '#' for non-valid colour check to validate in model
        if not isinstance(value, (str, type(None))):
            raise TypeError("textColour must be a hex colour string (e.g. '#ABCDEF' or '%s') or None" % INHERITCOLOUR)
        if value:
            # a non-empty string
            if not (re.findall(COLOURCHECK, value) or value == INHERITCOLOUR):
                raise ValueError("textColour %s not defined correctly, must be a hex colour string (e.g. '#ABCDEF' or '%s')" % (value, INHERITCOLOUR))
            value = value.upper()

        self._apiListView.textColour = value or INHERITCOLOUR

    @property
    def isSymbolDisplayed(self) -> bool:
        """True if the marker symbol is displayed."""
        return self._apiListView.isSymbolDisplayed

    @isSymbolDisplayed.setter
    def isSymbolDisplayed(self, value: bool):
        self._apiListView.isSymbolDisplayed = value

    @property
    def isTextDisplayed(self) -> bool:
        """True if the annotation is displayed?"""
        return self._apiListView.isTextDisplayed

    @isTextDisplayed.setter
    def isTextDisplayed(self, value: bool):
        self._apiListView.isTextDisplayed = value

    @property
    def meritColour(self) -> str:
        """Merit colour for displayed markers.

        meritColour must be a valid hex colour string '#ABCDEF' or '#' to denote an auto-colour (take colour from spectrum).
        Can also be None or ''. Lowercase will be changed to uppercase.

        If not set for ListView gives you the value for List.
        If set for ListView overrides List value.
        Set ListView value to None to return to non-local value"""
        result = self.getParameter(MERITSETTINGS, MERITCOLOUR)
        if result in (INHERITCOLOUR, None):
            obj = self._childClass
            result = obj and obj.meritColour
        return result

    @meritColour.setter
    def meritColour(self, value: typing.Optional[str]):
        if not isinstance(value, (str, type(None))):
            raise TypeError("meritColour must be a hex colour string (e.g. '#ABCDEF' or '%s') or None" % INHERITCOLOUR)
        if value:
            # a non-empty string
            if not (re.findall(COLOURCHECK, value) or value == INHERITCOLOUR):
                raise ValueError("meritColour %s not defined correctly, must be a hex colour string (e.g. '#ABCDEF' or '%s')" % (value, INHERITCOLOUR))
            value = value.upper()

        self.setParameter(MERITSETTINGS, MERITCOLOUR, value or INHERITCOLOUR)

    @property
    def meritEnabled(self) -> typing.Optional[bool]:
        """Flag to enable merit threshold for annotation display in all displays.

        If not set for ListView gives you the value for List.
        If set for ListView overrides List value.
        Set ListView value to None to return to non-local value"""
        result = self.getParameter(MERITSETTINGS, MERITENABLED)
        if result is None:
            obj = self._childClass
            result = obj and obj.meritEnabled
        return result

    @meritEnabled.setter
    def meritEnabled(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError("meritEnabled must be True/False.")

        self.setParameter(MERITSETTINGS, MERITENABLED, value)

    @property
    def meritThreshold(self) -> typing.Optional[float]:
        """Threshold to determine merit colouring for annotation display in all displays.

        If not set for ListView gives you the value for List.
        If set for ListView overrides List value.
        Set ListView value to None to return to non-local value"""
        result = self.getParameter(MERITSETTINGS, MERITTHRESHOLD)
        if result is None:
            obj = self._childClass
            result = obj and obj.meritThreshold
        return result

    @meritThreshold.setter
    def meritThreshold(self, value: typing.Union[float, int]):
        if not isinstance(value, (float, int)):
            raise TypeError("meritThreshold must be a float or integer")
        if not (0.0 <= value <= 1.0):
            raise ValueError("meritThreshold must be in the range [0.0, 1.0]")
        value = float(value)

        self.setParameter(MERITSETTINGS, MERITTHRESHOLD, value)

    @property
    def lineColour(self) -> str:
        """Line colour for displayed markers.

        lineColour must be a valid hex colour string '#ABCDEF' or '#' to denote an auto-colour (take colour from spectrum).
        Can also be None or ''. Lowercase will be changed to uppercase.

        If not set for ListView gives you the value for List.
        If set for ListView overrides List value.
        Set ListView value to None to return to non-local value"""
        result = self.getParameter(LINESETTINGS, LINECOLOUR)
        if result in (INHERITCOLOUR, None):
            obj = self._childClass
            result = obj and obj.lineColour
        return result

    @lineColour.setter
    def lineColour(self, value: typing.Optional[str]):
        if not isinstance(value, (str, type(None))):
            raise TypeError("lineColour must be a hex colour string (e.g. '#ABCDEF' or '%s') or None" % INHERITCOLOUR)
        if value:
            # a non-empty string
            if not (re.findall(COLOURCHECK, value) or value == INHERITCOLOUR):
                raise ValueError("lineColour %s not defined correctly, must be a hex colour string (e.g. '#ABCDEF' or '%s')" % (value, INHERITCOLOUR))
            value = value.upper()

        self.setParameter(LINESETTINGS, LINECOLOUR, value or INHERITCOLOUR)

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    # None

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    # None
