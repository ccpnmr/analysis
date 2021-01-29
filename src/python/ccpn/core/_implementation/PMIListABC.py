"""
Module Documentation here
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
__dateModified__ = "$dateModified: 2021-01-29 14:41:18 +0000 (Fri, January 29, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2020-05-26 14:50:42 +0000 (Tue, May 26, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================


import re
from typing import Optional, Union
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Spectrum import Spectrum


MERITSETTINGS = 'meritSettings'
MERITCOLOUR = 'meritColour'
MERITENABLED = 'meritEnabled'
MERITTHRESHOLD = 'meritThreshold'
LINESETTINGS = 'lineSettings'
LINECOLOUR = 'lineColour'
SYMBOLCOLOUR = 'symbolColour'
TEXTCOLOUR = 'textColour'

COLOURCHECK = '#[a-fA-F0-9]{6}$'
INHERITCOLOUR = '#'


class PMIListABC(AbstractWrapperObject):
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
            raise TypeError("symbolColour must be a hex colour string (e.g. '#ABCDEF' or '%s')" % INHERITCOLOUR)
        if not (re.findall(COLOURCHECK, value) or value == INHERITCOLOUR):
            raise ValueError("symbolColour %s not defined correctly, must be a hex colour string (e.g. '#ABCDEF' or '%s')" % (value, INHERITCOLOUR))

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
            raise TypeError("textColour must be a hex colour string (e.g. '#ABCDEF' or '%s')" % INHERITCOLOUR)
        if not (re.findall(COLOURCHECK, value) or value == INHERITCOLOUR):
            raise ValueError("textColour %s not defined correctly, must be a hex colour string (e.g. '#ABCDEF' or '%s')" % (value, INHERITCOLOUR))

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
            raise TypeError("meritColour must be a hex colour string (e.g. '#ABCDEF' or '%s')" % INHERITCOLOUR)
        if not (re.findall(COLOURCHECK, value) or value == INHERITCOLOUR):
            raise ValueError("meritColour %s not defined correctly, must be a hex colour string (e.g. '#ABCDEF' or '%s')" % (value, INHERITCOLOUR))

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
    def meritThreshold(self) -> float:
        """Threshold to determine merit colouring for annotation display in all displays.
        Must be a float in the range [0.0, 1.0]
        """
        return self.getParameter(MERITSETTINGS, MERITTHRESHOLD)

    @meritThreshold.setter
    def meritThreshold(self, value: Union[float, int]):
        if not isinstance(value, (float, int)):
            raise TypeError("meritThreshold must be a float or integer")
        if not (0.0 <= value <= 1.0):
            raise ValueError("meritThreshold must be in the range [0.0, 1.0]")
        value = float(value)

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
            raise TypeError("lineColour must be a hex colour string (e.g. '#ABCDEF' or '%s')" % INHERITCOLOUR)
        if not (re.findall(COLOURCHECK, value) or value == INHERITCOLOUR):
            raise ValueError("lineColour %s not defined correctly, must be a hex colour string (e.g. '#ABCDEF' or '%s')" % (value, INHERITCOLOUR))

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
