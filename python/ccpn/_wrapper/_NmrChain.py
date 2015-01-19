"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
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

from ccpn._wrapper._AbstractWrapperObject import AbstractWrapperObject
from ccpn._wrapper._Project import Project
from ccpn._wrapper._Chain import Chain
from ccpncore.api.ccp.nmr.Nmr import NmrChain as Ccpn_NmrChain
from ccpncore.lib import pid as Pid


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
  def ccpnNmrChain(self) -> Ccpn_NmrChain:
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
  
  molecule = _parent
  
  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details
    
  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

  @property
  def chain(self) -> Chain:
    """Free-form text comment"""
    ccpnChain = self._wrappedData.chain
    if ccpnChain is None:
      return None

    return self._parent._data2Obj.get(ccpnChain)

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
    code = shortName
    ii = 0
    while nmrProject.findFirstNmrChain(code=code) is not None:
      ii += 1
      code = '@%s' % ii
    shortName = code
  
  newCcpnNmrChain = nmrProject.newNmrChain(code=shortName, details=comment)
  
  return parent._data2Obj.get(newCcpnNmrChain)
  
def fetchNmrChain(parent:Project, shortName:str=None) -> NmrChain:
  """Fetch chain with given shortName; If none exists call newNmrChain to make one first

  :param str shortName: shortName for new chain (optional)
  """

  nmrProject = parent.nmrProject
  ccpnNmrChain = nmrProject.findFirstNmrChain(code=shortName)
  if ccpnNmrChain is None:
    ccpnNmrChain = nmrProject.newNmrChain(code=shortName)
  return parent._data2Obj.get(ccpnNmrChain)

  
# Clean-up
    
# Connections to parents:
Project._childClasses.append(NmrChain)
Project.newNmrChain = newNmrChain
Project.fetchNmrChain = fetchNmrChain

# Notifiers:
className = Ccpn_NmrChain._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':NmrChain}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
