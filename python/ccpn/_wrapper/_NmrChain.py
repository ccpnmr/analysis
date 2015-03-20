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

from ccpn import AbstractWrapperObject
from ccpn import Project
from ccpn import Chain
from ccpncore.util import Pid
from ccpncore.api.ccp.nmr.Nmr import NmrChain as ApiNmrChain


class NmrChain(AbstractWrapperObject):
  """Nmr Assignment Chain."""
  
  #: Short class name, for PID.
  shortClassName = 'NC'

  #: Name of plural link to instances of class
  _pluralLinkName = 'nmrChains'
  
  #: List of child classes.
  _childClasses = []
  

  # CCPN properties  
  @property
  def apiNmrChain(self) -> ApiNmrChain:
    """ CCPN NmrChain matching NmrChain"""
    return self._wrappedData
    
  @property
  def _key(self) -> str:
    """short form of name, as used for id with illegal characters replaced by Pid.altCharacter"""
    return self._wrappedData.code.translate(Pid.remapSeparators)

  @property
  def shortName(self) -> str:
    """short form of name, key attribute"""
    return self._wrappedData.code
    
  @property
  def _parent(self) -> Project:
    """Parent (containing) object."""
    return self._project
  
  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details
    
  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

  @property
  def chain(self) -> Chain:
    """Molecule chain matching NmrChain"""
    apiChain = self._wrappedData.chain
    if apiChain is None:
      return None

    return self._parent._data2Obj.get(apiChain)

  @classmethod
  def _getAllWrappedData(cls, parent: Project)-> list:
    """get wrappedData (Nmr.DataSources) for all Spectrum children of parent Project"""
    return parent._wrappedData.sortedNmrChains()


def newNmrChain(parent:Project, shortName:str=None, comment:str=None) -> NmrChain:
  """Create new child NmrChain

  :param str shortName: shortName for new nmrChain (optional, defaults to '@n' n positive integer
  :param str comment: comment for new nmrChain (optional)"""
  
  nmrProject = parent.nmrProject
  
  if shortName is None:
    code = "@1"
    ii = 1
    while nmrProject.findFirstNmrChain(code=code) is not None:
      ii += 1
      code = '@%s' % ii
    shortName = code

  newApiNmrChain = nmrProject.newNmrChain(code=shortName, details=comment)
  
  return parent._data2Obj.get(newApiNmrChain)
  
def fetchNmrChain(parent:Project, shortName:str=None) -> NmrChain:
  """Fetch chain with given shortName; If none exists call newNmrChain to make one first

  :param str shortName: shortName for new chain (optional)
  """

  nmrProject = parent.nmrProject
  apiNmrChain = nmrProject.findFirstNmrChain(code=shortName)
  if apiNmrChain is None:
    apiNmrChain = nmrProject.newNmrChain(code=shortName)
  return parent._data2Obj.get(apiNmrChain)

  
# Clean-up
    
# Connections to parents:
Project._childClasses.append(NmrChain)
Project.newNmrChain = newNmrChain
Project.fetchNmrChain = fetchNmrChain

# Notifiers:
className = ApiNmrChain._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':NmrChain}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
