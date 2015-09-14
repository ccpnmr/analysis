"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================
# from ccpncore.lib.typing import Sequence

import datetime
from ccpncore.lib import Constants as coreConstants
from ccpn import AbstractWrapperObject
from ccpn import Project
from ccpncore.api.ccp.nmr.Nmr import Note as ApiNote


class Note(AbstractWrapperObject):
  """Project note."""
  
  #: Short class name, for PID.
  shortClassName = 'NO'
  # Attribute it necessary as subclasses must use superclass className
  className = 'Note'

  #: Name of plural link to instances of class
  _pluralLinkName = 'notes'
  
  #: List of child classes.
  _childClasses = []
  

  # CCPN properties  
  @property
  def _apiNote(self) -> ApiNote:
    """ CCPN Project Note"""
    return self._wrappedData

    
  @property
  def _key(self) -> str:
    """id string - serial number converted to string"""
    return str(self._wrappedData.serial)

  @property
  def serial(self) -> int:
    """serial number, key attribute for RestraintSet"""
    return self._wrappedData.serial

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
  @classmethod
  def _getAllWrappedData(cls, parent:Project)-> list:
    """get wrappedData for all Notes linked to NmrProject"""
    return parent._wrappedData.sortedNotes()


def newNote(parent:Project, text:str=None) -> Note:
  """Create new  Note

  :param str text: Note text"""

  return parent._data2Obj.get(parent._wrappedData.newNote(text=text))

    
    
# Connections to parents:
Project._childClasses.append(Note)
Project.newNote = newNote

# Notifiers:
className = ApiNote._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':Note}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
