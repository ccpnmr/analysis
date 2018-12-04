"""
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:29 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import collections
import typing  # ejb - added for 'header'
from ccpn.util import Constants as utilConstants

from ccpn.core.Project import Project
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import Note as ApiNote
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, deleteObject, ccpNmrV3CoreSetter, logCommandBlock
from ccpn.util.Logging import getLogger


class Note(AbstractWrapperObject):
    """Project note."""

    #: Short class name, for PID.
    shortClassName = 'NO'
    # Attribute it necessary as subclasses must use superclass className
    className = 'Note'

    _parentClass = Project

    #: Name of plural link to instances of class
    _pluralLinkName = 'notes'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiNote._metaclass.qualifiedName()

    # CCPN properties
    @property
    def _apiNote(self) -> ApiNote:
        """ CCPN Project Note"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """Residue local ID"""
        return Pid.IDSEP.join((str(self._wrappedData.serial),
                               self._wrappedData.name.translate(Pid.remapSeparators)))

    @property
    def serial(self) -> int:
        """serial number of note - immutable, part of identifier"""
        return self._wrappedData.serial

    @property
    def name(self) -> str:
        """Name of note, part of identifier"""
        return self._wrappedData.name

    @property
    def _parent(self) -> Project:
        """Parent (containing) object."""
        return self._project

    @property
    def text(self) -> str:
        """Free-form text comment"""
        return self._wrappedData.text

    @text.setter
    def text(self, value: str):
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb
        # self._wrappedData.text = value
        #
        if value is not None:
            if not isinstance(value, str):
                raise TypeError("Note text must be a string")  # ejb catch non-string
        self._wrappedData.text = value
        #
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb

    @property
    def created(self) -> typing.Optional[str]:
        """Note creation time"""
        return self._wrappedData.created.strftime(utilConstants.stdTimeFormat)

    @property
    def lastModified(self) -> str:
        """Note last modification time"""
        return self._wrappedData.lastModified.strftime(utilConstants.stdTimeFormat)

    @property
    def header(self) -> typing.Optional[str]:  # ejb - changed from str
        """Note header == first line of note"""
        text = self._wrappedData.text
        if text:
            ll = text.splitlines()
            if ll:
                return ll[0]
        #
        return None

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Project) -> list:
        """get wrappedData for all Notes linked to NmrProject"""
        return parent._wrappedData.sortedNotes()

    def rename(self, value: str):
        """Rename Note, changing its name and Pid.

        NB, the serial remains immutable."""

        if not isinstance(value, str):
            raise TypeError("Note name must be a string")  # ejb catch non-string
        if not value:
            raise ValueError("Note name must be set")  # ejb catch empty string
        if Pid.altCharacter in value:
            raise ValueError("Character %s not allowed in ccpn.Note.name" % Pid.altCharacter)
        #
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb

        self._startCommandEchoBlock('rename', value)
        try:
            self._wrappedData.name = value
        finally:
            self._endCommandEchoBlock()

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    #===========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================


#=========================================================================================
# Connections to parents:
#=========================================================================================

@newObject(Note)
def _newNote(self: Project, name: str = 'Note', text: str = None, serial: int = None) -> Note:
    """Create new Note.

    See the Note class for details.

    :param name:
    :param text:
    :param serial: optional serial number.
    :return: a new Note instance.
    """

    if not isinstance(name, str):
        raise TypeError("Note name must be a string")
    if not name:
        raise ValueError("Note name must be set")
    if Pid.altCharacter in name:
        raise ValueError("Character %s not allowed in ccpn.Note.name" % Pid.altCharacter)
    if text is not None:
        if not isinstance(text, str):
            raise TypeError("Note text must be a string")

    apiNote = self._wrappedData.newNote(text=text, name=name)
    result = self._data2Obj.get(apiNote)
    if result is None:
        raise RuntimeError('Unable to generate new Note item')

    if serial is not None:
        try:
            result.resetSerial(serial)
        except ValueError:
            getLogger().warning("Could not reset serial of %s to %s - keeping original value"
                                % (result, serial))

    return result


# Connections to parents:
Project.newNote = _newNote
del _newNote

# Notifiers:
Project._apiNotifiers.append(('_finaliseApiRename', {},
                              ApiNote._metaclass.qualifiedName(), 'setName'))
