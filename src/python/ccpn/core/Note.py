"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:29 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import typing
from ccpn.util import Constants as utilConstants
from functools import partial
from ccpn.core.Project import Project
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import Note as ApiNote
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, renameObject
from ccpn.util.Logging import getLogger
from ccpn.util import Common as commonUtil


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
        # return Pid.IDSEP.join((str(self._wrappedData.serial),
        #                        self._wrappedData.name.translate(Pid.remapSeparators), 'HELP'))
        # return str(self.name)+'_'+str(self.serial)
        return self._wrappedData.name.translate(Pid.remapSeparators)

    @property
    def serial(self) -> int:
        """serial number of note - immutable, part of identifier"""
        return self._wrappedData.serial

    @property
    def name(self) -> str:
        """Name of note, part of identifier"""
        return self._wrappedData.name

    @name.setter
    def name(self, value: str):
        """set Name of note, part of identifier"""
        self.rename(value)

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
        if value is not None:
            if not isinstance(value, str):
                raise TypeError("Note text must be a string")
        self._wrappedData.text = value

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

    @logCommand(get='self')
    def rename(self, value: str):
        """Rename Note, changing its name and Pid.

        NB, the serial remains immutable."""
        self._validateName(value=value, allowWhitespace=False)

        with renameObject(self) as addUndoItem:
            oldName = self.name
            self._wrappedData.name = value

            addUndoItem(undo=partial(self.rename, oldName),
                        redo=partial(self.rename, value))

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
def _newNote(self: Project, name: str = None, text: str = None, serial: int = None) -> Note:
    """Create new Note.

    See the Note class for details.

    :param name: name for the note.
    :param text: contents of the note.
    :param serial: optional serial number.
    :return: a new Note instance.
    """

    if not name:
        # Make default name
        nextNumber = len(self.notes)
        noteName = self._defaultName(Note)
        name = '%s_%s' % (noteName, nextNumber) if nextNumber > 0 else noteName
    names = [d.name for d in self.notes]
    while name in names:
        name = commonUtil.incrementName(name)

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


#EJB 20181205: moved to Project
# Project.newNote = _newNote
# del _newNote

# Notifiers:
Project._apiNotifiers.append(('_finaliseApiRename', {},
                              ApiNote._metaclass.qualifiedName(), 'setName'))
