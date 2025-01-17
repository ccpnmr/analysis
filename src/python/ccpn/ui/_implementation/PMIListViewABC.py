"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2023-05-18 18:49:15 +0100 (Thu, May 18, 2023) $"
__version__ = "$Revision: 3.1.1 $"
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
from ccpn.core._implementation.PMIListABC import COLOURCHECK, INHERITCOLOUR
from ccpn.core.lib.ContextManagers import ccpNmrV3CoreUndoBlock
from ccpn.ui._implementation.SpectrumView import SpectrumView
from ccpn.util.decorators import logCommand


class PMIListViewABC(AbstractWrapperObject):
    """ListView for 1D or nD List"""

    #: Short class name, for PID.
    shortClassName = 'Undefined'
    # Attribute it necessary as subclasses must use superclass className
    className = 'Undefined'

    _parentClass = SpectrumView
    _parentClassName = SpectrumView.__class__.__name__

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

    # internal namespace
    _MERITCOLOUR = 'meritColour'
    _MERITENABLED = 'meritEnabled'
    _MERITTHRESHOLD = 'meritThreshold'
    _LINECOLOUR = 'lineColour'
    _SYMBOLCOLOUR = 'symbolColour'
    _TEXTCOLOUR = 'textColour'
    _ARROWCOLOUR = 'arrowColour'
    
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
        raise RuntimeError(f"{str(self._pluralLinkName)} cannot be deleted directly")

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
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreUndoBlock()
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
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreUndoBlock()
    def symbolColour(self, value: typing.Optional[str]):
        # ccpnInternal - changes this to '#' for non-valid colour check to validate in model
        if not isinstance(value, (str, type(None))):
            raise TypeError(f"symbolColour must be a hex colour string (e.g. '#ABCDEF' or '{INHERITCOLOUR}') or None")

        if value:
            # a non-empty string
            if not (re.findall(COLOURCHECK, value) or value == INHERITCOLOUR):
                raise ValueError(f"symbolColour {value} not defined correctly, must be a hex colour string (e.g. '#ABCDEF' or '{INHERITCOLOUR}')")

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
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreUndoBlock()
    def textColour(self, value: typing.Optional[str]):
        # ccpnInternal - changes this to '#' for non-valid colour check to validate in model
        if not isinstance(value, (str, type(None))):
            raise TypeError(f"textColour must be a hex colour string (e.g. '#ABCDEF' or '{INHERITCOLOUR}') or None")

        if value:
            # a non-empty string
            if not (re.findall(COLOURCHECK, value) or value == INHERITCOLOUR):
                raise ValueError(f"textColour {value} not defined correctly, must be a hex colour string (e.g. '#ABCDEF' or '{INHERITCOLOUR}')")

            value = value.upper()

        self._apiListView.textColour = value or INHERITCOLOUR

    @property
    def isSymbolDisplayed(self) -> bool:
        """True if the marker symbol is displayed"""
        return self._apiListView.isSymbolDisplayed

    @isSymbolDisplayed.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreUndoBlock()
    def isSymbolDisplayed(self, value: bool):
        self._apiListView.isSymbolDisplayed = value

    @property
    def isTextDisplayed(self) -> bool:
        """True if the annotation is displayed"""
        return self._apiListView.isTextDisplayed

    @isTextDisplayed.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreUndoBlock()
    def isTextDisplayed(self, value: bool):
        self._apiListView.isTextDisplayed = value

    @property
    def isDisplayed(self) -> bool:
        """True if symbols and text displayed"""
        return self._apiListView.isSymbolDisplayed and self._apiListView.isTextDisplayed

    @isDisplayed.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreUndoBlock()
    def isDisplayed(self, value: bool):
        self._apiListView.isSymbolDisplayed = value
        self._apiListView.isTextDisplayed = value

    @property
    def meritColour(self) -> str:
        """Merit colour for displayed markers.

        meritColour must be a valid hex colour string '#ABCDEF' or '#' to denote an auto-colour (take colour from spectrum).
        Can also be None or ''. Lowercase will be changed to uppercase.

        If not set for ListView gives you the value for List.
        If set for ListView overrides List value.
        Set ListView value to None to return to non-local value"""
        result = self._getInternalParameter(self._MERITCOLOUR)
        if result in (INHERITCOLOUR, None):
            obj = self._childClass
            result = obj and obj.meritColour
        return result

    @meritColour.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreUndoBlock()
    def meritColour(self, value: typing.Optional[str]):
        if not isinstance(value, (str, type(None))):
            raise TypeError(f"meritColour must be a hex colour string (e.g. '#ABCDEF' or '{INHERITCOLOUR}') or None")

        if value:
            # a non-empty string
            if not (re.findall(COLOURCHECK, value) or value == INHERITCOLOUR):
                raise ValueError(f"meritColour {value} not defined correctly, must be a hex colour string (e.g. '#ABCDEF' or '{INHERITCOLOUR}')")

            value = value.upper()

        self._setInternalParameter(self._MERITCOLOUR, value or INHERITCOLOUR)

    @property
    def meritEnabled(self) -> typing.Optional[bool]:
        """Flag to enable merit threshold for annotation display in all displays.

        If not set for ListView gives you the value for List.
        If set for ListView overrides List value.
        Set ListView value to None to return to non-local value"""
        result = self._getInternalParameter(self._MERITENABLED)
        if result is None:
            obj = self._childClass
            result = obj and obj.meritEnabled
        return result

    @meritEnabled.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreUndoBlock()
    def meritEnabled(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError("meritEnabled must be True/False.")

        self._setInternalParameter(self._MERITENABLED, value)

    @property
    def meritThreshold(self) -> typing.Optional[float]:
        """Threshold to determine merit colouring for annotation display in all displays.

        If not set for ListView gives you the value for List.
        If set for ListView overrides List value.
        Set ListView value to None to return to non-local value"""
        result = self._getInternalParameter(self._MERITTHRESHOLD)
        if result is None:
            obj = self._childClass
            result = obj and obj.meritThreshold
        return result

    @meritThreshold.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreUndoBlock()
    def meritThreshold(self, value: typing.Union[float, int]):
        if not isinstance(value, (float, int)):
            raise TypeError("meritThreshold must be a float or integer")
        if not (0.0 <= value <= 1.0):
            raise ValueError("meritThreshold must be in the range [0.0, 1.0]")
        value = float(value)

        self._setInternalParameter(self._MERITTHRESHOLD, value)

    @property
    def lineColour(self) -> str:
        """Line colour for displayed markers.

        lineColour must be a valid hex colour string '#ABCDEF' or '#' to denote an auto-colour (take colour from spectrum).
        Can also be None or ''. Lowercase will be changed to uppercase.

        If not set for ListView gives you the value for List.
        If set for ListView overrides List value.
        Set ListView value to None to return to non-local value"""
        result = self._getInternalParameter(self._LINECOLOUR)
        if result in (INHERITCOLOUR, None):
            obj = self._childClass
            result = obj and obj.lineColour
        return result

    @lineColour.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreUndoBlock()
    def lineColour(self, value: typing.Optional[str]):
        if not isinstance(value, (str, type(None))):
            raise TypeError(f"lineColour must be a hex colour string (e.g. '#ABCDEF' or '{INHERITCOLOUR}') or None")

        if value:
            # a non-empty string
            if not (re.findall(COLOURCHECK, value) or value == INHERITCOLOUR):
                raise ValueError(f"lineColour {value} not defined correctly, must be a hex colour string (e.g. '#ABCDEF' or '{INHERITCOLOUR}')")

            value = value.upper()

        self._setInternalParameter(self._LINECOLOUR, value or INHERITCOLOUR)

    @property
    def arrowColour(self) -> str:
        """Arrow colour for displayed markers.

        arrowColour must be a valid hex colour string '#ABCDEF' or '#' to denote an auto-colour (take colour from spectrum).
        Can also be None or ''. Lowercase will be changed to uppercase.

        If not set for ListView gives you the value for List.
        If set for ListView overrides List value.
        Set ListView value to None to return to non-local value"""
        result = self._getInternalParameter(self._ARROWCOLOUR)
        if result in (INHERITCOLOUR, None):
            obj = self._childClass
            result = obj and obj.arrowColour
        return result

    @arrowColour.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreUndoBlock()
    def arrowColour(self, value: typing.Optional[str]):
        if not isinstance(value, (str, type(None))):
            raise TypeError(f"arrowColour must be a hex colour string (e.g. '#ABCDEF' or '{INHERITCOLOUR}') or None")

        if value:
            # a non-empty string
            if not (re.findall(COLOURCHECK, value) or value == INHERITCOLOUR):
                raise ValueError(f"arrowColour {value} not defined correctly, must be a hex colour string (e.g. '#ABCDEF' or '{INHERITCOLOUR}')")

            value = value.upper()

        self._setInternalParameter(self._ARROWCOLOUR, value or INHERITCOLOUR)

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _restoreObject(cls, project, apiObj):
        """Restore the object and update ccpnInternalData
        """
        MERITSETTINGS = 'meritSettings'
        MERITCOLOUR = 'meritColour'
        MERITENABLED = 'meritEnabled'
        MERITTHRESHOLD = 'meritThreshold'
        LINESETTINGS = 'lineSettings'
        LINECOLOUR = 'lineColour'
        SYMBOLCOLOUR = 'symbolColour'
        TEXTCOLOUR = 'textColour'

        result = super()._restoreObject(project, apiObj)

        for namespace, param, newVar in [(MERITSETTINGS, MERITCOLOUR, cls._MERITCOLOUR),
                                         (MERITSETTINGS, MERITENABLED, cls._MERITENABLED),
                                         (MERITSETTINGS, MERITTHRESHOLD, cls._MERITTHRESHOLD),
                                         (LINESETTINGS, LINECOLOUR, cls._LINECOLOUR),
                                         (LINESETTINGS, SYMBOLCOLOUR, cls._SYMBOLCOLOUR),
                                         (LINESETTINGS, TEXTCOLOUR, cls._TEXTCOLOUR),
                                         ]:
            if result.hasParameter(namespace, param):
                # move the internal parameter to the correct namespace
                value = result.getParameter(namespace, param)
                result.deleteParameter(namespace, param)
                result._setInternalParameter(newVar, value)

        return result

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    # None
