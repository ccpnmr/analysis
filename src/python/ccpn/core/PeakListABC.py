"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================


# import numpy as np
# import math

import re
from typing import Sequence, List, Optional

# from ccpn.util.Common import percentage
# from scipy.ndimage import maximum_filter, minimum_filter
# from ccpn.util import Common as commonUtil

from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Spectrum import Spectrum


# from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import PeakList as ApiPeakList
# from ccpn.core.lib.SpectrumLib import _oldEstimateNoiseLevel1D
# from ccpnmodel.ccpncore.lib._ccp.nmr.Nmr.PeakList import pickNewPeaks
# from ccpn.util.decorators import logCommand
# from ccpn.core.lib.ContextManagers import newObject, undoBlock, undoBlockWithoutSideBar
# from ccpn.util.Logging import getLogger


MERITSETTINGS = 'meritSettings'
MERITCOLOUR = 'meritColour'
MERITENABLED = 'meritEnabled'
MERITTHRESHOLD = 'meritThreshold'
LINESETTINGS = 'lineSettings'
LINECOLOUR = 'lineColour'
SYMBOLCOLOUR = 'symbolColour'
TEXTCOLOUR = 'textColour'

COLOURCHECK = '#[a-fA-F0-9]{6}$'


class PeakListABC(AbstractWrapperObject):
    """An ABC object containing Peaks/Multiplets/Integrals.
    Note: the object is not a (subtype of a) Python list.
    To access all List objects, use List.items."""

    # The following attributes must be subclassed - change to traits?

    #: Short class name, for PID.
    shortClassName = 'Undefined'
    # Attribute it necessary as subclasses must use superclass className
    className = 'Undefined'

    _parentClass = Spectrum
    _primaryChildClass = None

    #: Name of plural link to instances of class
    _pluralLinkName = 'Undefined'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = None

    # Special error-raising functions as this is a container for a list
    def __iter__(self):
        raise TypeError("'%s object is not iterable - for a list of %s use %s.%s" % (self.className,
                                                                                     self._primaryChildClass._pluralLinkName,
                                                                                     self.className,
                                                                                     self._primaryChildClass._pluralLinkName))

    def __getitem__(self, index):
        raise TypeError("'%s object does not support indexing - for a list of %s use %s.%s" % (self.className,
                                                                                               self._primaryChildClass._pluralLinkName,
                                                                                               self.className,
                                                                                               self._primaryChildClass._pluralLinkName))

    def __len__(self):
        raise TypeError("'%s object has no length - for a list of %s use %s.%s" % (self.className,
                                                                                   self._primaryChildClass._pluralLinkName,
                                                                                   self.className,
                                                                                   self._primaryChildClass._pluralLinkName))

    def _setPrimaryChildClass(self):
        """Set the primary classType for the child list attached to this container
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self._setPrimaryChildClass()

    #=========================================================================================
    # CCPN properties
    #=========================================================================================

    @property
    def _key(self) -> str:
        """id string - serial number converted to string."""
        return str(self._wrappedData.serial)

    @property
    def serial(self) -> int:
        """serial number of List, used in Pid and to identify the List."""
        return self._wrappedData.serial

    @property
    def _parent(self) -> Spectrum:
        """Spectrum containing list."""
        return self._project._data2Obj[self._wrappedData.dataSource]

    spectrum = _parent

    @property
    def title(self) -> str:
        """title of List (not used in PID)."""
        return self._wrappedData.name

    @title.setter
    def title(self, value: str):
        self._wrappedData.name = value

    # @property
    # def comment(self) -> str:
    #     """Free-form text comment"""
    #     return self._wrappedData.details
    #
    # @comment.setter
    # def comment(self, value: str):
    #     self._wrappedData.details = value

    @property
    def symbolStyle(self) -> str:
        """Symbol style for annotation display in all displays."""
        return self._wrappedData.symbolStyle

    @symbolStyle.setter
    def symbolStyle(self, value: str):
        self._wrappedData.symbolStyle = value

    @property
    def symbolColour(self) -> str:
        """Symbol colour for annotation display in all displays.
        symbolColour must be a valid hex colour string '#ABCDEF' or '#' to denote an auto-colour (take colour from spectrum).
        Lowercase will be changed to uppercase.
        """
        return self._wrappedData.symbolColour

    @symbolColour.setter
    def symbolColour(self, value: str):
        if not isinstance(value, str):
            raise TypeError("symbolColour must be a hex colour string (e.g. '#ABCDEF' or '#')")
        if not (re.findall(COLOURCHECK, value) or value == '#'):
            raise ValueError("symbolColour %s not defined correctly, must be a hex colour string (e.g. '#ABCDEF' or '#')" % value)

        value = value.upper()
        self._wrappedData.symbolColour = value

    @property
    def textColour(self) -> str:
        """Text colour for annotation display in all displays.
        textColour must be a valid hex colour string '#ABCDEF' or '#' to denote an auto-colour (take colour from spectrum).
        Lowercase will be changed to uppercase.
        """
        return self._wrappedData.textColour

    @textColour.setter
    def textColour(self, value: str):
        if not isinstance(value, str):
            raise TypeError("textColour must be a hex colour string (e.g. '#ABCDEF' or '#')")
        if not (re.findall(COLOURCHECK, value) or value == '#'):
            raise ValueError("textColour %s not defined correctly, must be a hex colour string (e.g. '#ABCDEF' or '#')" % value)

        value = value.upper()
        self._wrappedData.textColour = value

    @property
    def isSimulated(self) -> bool:
        """True if this List is simulated."""
        return self._wrappedData.isSimulated

    @isSimulated.setter
    def isSimulated(self, value: bool):
        self._wrappedData.isSimulated = value

    @property
    def meritColour(self) -> Optional[str]:
        """merit colour for annotation display in all displays.
        meritColour must be a valid hex colour string '#ABCDEF' or '#' to denote an auto-colour (take colour from spectrum).
        Lowercase will be changed to uppercase.
        """
        return self.getParameter(MERITSETTINGS, MERITCOLOUR)

    @meritColour.setter
    def meritColour(self, value: str):
        if not isinstance(value, str):
            raise TypeError("meritColour must be a hex colour string (e.g. '#ABCDEF' or '#')")
        if not (re.findall(COLOURCHECK, value) or value == '#'):
            raise ValueError("meritColour %s not defined correctly, must be a hex colour string (e.g. '#ABCDEF' or '#')" % value)

        value = value.upper()
        self.setParameter(MERITSETTINGS, MERITCOLOUR, value)

    @property
    def meritEnabled(self) -> Optional[bool]:
        """Flag to enable merit threshold for annotation display in all displays.
        Must be True/False.
        """
        return self.getParameter(MERITSETTINGS, MERITENABLED)

    @meritEnabled.setter
    def meritEnabled(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError("meritEnabled must be True/False.")

        self.setParameter(MERITSETTINGS, MERITENABLED, value)

    @property
    def meritThreshold(self) -> Optional[float]:
        """Threshold to determine merit colouring for annotation display in all displays.
        Must be a float in the range [0.0, 1.0]
        """
        return self.getParameter(MERITSETTINGS, MERITTHRESHOLD)

    @meritThreshold.setter
    def meritThreshold(self, value: float):
        if not isinstance(value, float):
            raise TypeError("meritThreshold must be a float")
        if not (0.0 <= value <= 1.0):
            raise ValueError("meritThreshold must be in the range [0.0, 1.0]")

        self.setParameter(MERITSETTINGS, MERITTHRESHOLD, value)

    @property
    def lineColour(self) -> str:
        """line colour for annotation display in all displays.
        lineColour must be a valid hex colour string '#ABCDEF' or '#' to denote an auto-colour (take colour from spectrum).
        Lowercase will be changed to uppercase.
        """
        return self.getParameter(LINESETTINGS, LINECOLOUR)

    @lineColour.setter
    def lineColour(self, value: str):
        if not isinstance(value, str):
            raise TypeError("lineColour must be a hex colour string (e.g. '#ABCDEF' or '#')")
        if not (re.findall(COLOURCHECK, value) or value == '#'):
            raise ValueError("lineColour %s not defined correctly, must be a hex colour string (e.g. '#ABCDEF' or '#')" % value)

        value = value.upper()
        self.setParameter(LINESETTINGS, LINECOLOUR, value)

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    # None

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    # None
