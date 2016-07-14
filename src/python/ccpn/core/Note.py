"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

import collections

from ccpn.core.Project import Project
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import Note as ApiNote
from ccpnmodel.ccpncore.lib import Constants as coreConstants


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
  def text(self, value:str):
    self._wrappedData.text = value

  @property
  def created(self) -> str:
    """Note creation time"""
    return self._wrappedData.created.strftime(coreConstants.stdTimeFormat)

  @property
  def lastModified(self) -> str:
    """Note last modification time"""
    return self._wrappedData.lastModified.strftime(coreConstants.stdTimeFormat)

  @property
  def header(self) -> str:
    """Note header == first line of note"""
    text = self._wrappedData.text
    if text:
      ll = text.splitlines()
      if ll:
        return ll[0]
    #
    return None

  # Implementation functions
  def rename(self, value:str):
    """Rename Note, changing its Id and Pid"""
    if not value:
      raise ValueError("Note name must be set")

    elif Pid.altCharacter in value:
      raise ValueError("Character %s not allowed in ccpn.Note.name" % Pid.altCharacter)

    else:
      self._startFunctionCommandBlock('rename', value)
      try:
        self._wrappedData.name = value
      finally:
        self._project._appBase._endCommandBlock()


  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:Project)-> list:
    """get wrappedData for all Notes linked to NmrProject"""
    return parent._wrappedData.sortedNotes()


def _newNote(self:Project, name:str='Note', text:str=None) -> Note:
  """Create new Note"""

  defaults = collections.OrderedDict((('name', None), ('text', None)))

  if name and Pid.altCharacter in name:
    raise ValueError("Character %s not allowed in ccpn.Note.name" % Pid.altCharacter)

  self._startFunctionCommandBlock('newNote', values=locals(), defaults=defaults,
                                  parName='newNote')
  try:
    return self._data2Obj.get(self._wrappedData.newNote(text=text, name=name))
  finally:
    self._project._appBase._endCommandBlock()
    
    
# Connections to parents:
Project.newNote = _newNote
del _newNote

# Notifiers:
Project._apiNotifiers.append(('_finaliseApiRename', {},
                              ApiNote._metaclass.qualifiedName(), 'setName'))
