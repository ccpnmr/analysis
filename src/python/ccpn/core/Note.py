"""
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
__dateModified__ = "$dateModified: 2021-10-27 17:42:09 +0100 (Wed, October 27, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import typing
from datetime import datetime

from ccpn.util import Constants as utilConstants
from ccpn.core.Project import Project
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import Note as ApiNote
from ccpn.core.lib.ContextManagers import newObject, renameObject, ccpNmrV3CoreSetter
from ccpn.util.decorators import logCommand


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

    # Internal NameSpace
    _COMMENT = 'comment'

    #=========================================================================================
    # CCPN properties
    #=========================================================================================

    @property
    def _apiNote(self) -> ApiNote:
        """ CCPN Project Note"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """Note local ID"""
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
    @logCommand(get='self', isProperty=True)
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
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def text(self, value: str):
        if value is not None:
            if not isinstance(value, str):
                raise TypeError("Note text must be a string")
        self._wrappedData.text = value

    @property
    def created(self) -> typing.Optional[str]:
        """Note creation time"""
        return self._wrappedData.created.strftime(utilConstants.stdTimeFormat)

    @created.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def created(self, value):
        # bypass the api because frozen
        for timeFormat in (utilConstants.stdTimeFormat, utilConstants.isoTimeFormat):
            try:
                # loop until the correct format is found
                self._wrappedData.__dict__['created'] = datetime.strptime(value, timeFormat)
                break
            except:
                continue
        else:
            raise TypeError("time created is not the correct format")

    @property
    def lastModified(self) -> str:
        """Note last modification time"""
        return self._wrappedData.lastModified.strftime(utilConstants.stdTimeFormat)

    @lastModified.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def lastModified(self, value):
        # bypass the api because frozen
        for timeFormat in (utilConstants.stdTimeFormat, utilConstants.isoTimeFormat):
            try:
                # loop until the correct format is found
                self._wrappedData.__dict__['lastModified'] = datetime.strptime(value, timeFormat)
                break
            except:
                continue
        else:
            raise TypeError("time created is not the correct format")

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

    @property
    def comment(self) -> str:
        """Free-form text comment"""
        comment = self._getInternalParameter(self._COMMENT)
        return comment

    @comment.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def comment(self, value: str):
        """set optional comment of note."""
        if not isinstance(value, (str, type(None))):
            raise ValueError("comment must be a string/None.")

        self._setInternalParameter(self._COMMENT, value)

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Project) -> list:
        """get wrappedData for all Notes linked to NmrProject"""
        return parent._wrappedData.sortedNotes()

    @renameObject()
    @logCommand(get='self')
    def rename(self, value: str):
        """Rename Note, changing its name and Pid.
        """
        return self._rename(value)

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
def _newNote(self: Project, name: str = None, text: str = None, comment: str = None) -> Note:
    """Create new Note.

    See the Note class for details.

    :param name: name for the note.
    :param text: contents of the note.
    :return: a new Note instance.
    """

    name = Note._uniqueName(project=self, name=name)

    if text is not None:
        if not isinstance(text, str):
            raise TypeError("Note text must be a string")

    apiNote = self._wrappedData.newNote(text=text, name=name)
    result = self._data2Obj.get(apiNote)
    if result is None:
        raise RuntimeError('Unable to generate new Note item')

    result.comment = comment

    return result


#EJB 20181205: moved to Project
# Project.newNote = _newNote
# del _newNote

# Notifiers:
Project._apiNotifiers.append(('_finaliseApiRename', {},
                              ApiNote._metaclass.qualifiedName(), 'setName'))
