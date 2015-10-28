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

from ccpncore.util.Types import Sequence
from ccpn import AbstractWrapperObject
from ccpn import Project
from ccpn import Chain
from ccpncore.util import Pid
from ccpncore.lib import Constants
from ccpncore.api.ccp.nmr.Nmr import NmrChain as ApiNmrChain


class NmrChain(AbstractWrapperObject):
  """Nmr Assignment Chain."""
  
  #: Short class name, for PID.
  shortClassName = 'NC'
  # Attribute it necessary as subclasses must use superclass className
  className = 'NmrChain'

  #: Name of plural link to instances of class
  _pluralLinkName = 'nmrChains'
  
  #: List of child classes.
  _childClasses = []
  

  # CCPN properties  
  @property
  def _apiNmrChain(self) -> ApiNmrChain:
    """ CCPN NmrChain matching NmrChain"""
    return self._wrappedData
    
  @property
  def _key(self) -> str:
    """short form of name, as used for id with illegal characters replaced by Pid.altCharacter"""
    return self._wrappedData.code.translate(Pid.remapSeparators)

  @property
  def shortName(self) -> str:
    """short form of name, key attribute.
    NB changing this attribute will rename the NmrChain"""
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
  def connectedNmrResidues(self) -> tuple:
    """stretch of connected NmrResidues within NmrChain - there can only be one
    Does not include NmrResidues defined as satellites (sequenceCodes that end in '+1', '-1', etc.
    If NmrChain matches a proper Chain, there will be an NmrResidue for each residue,
    with None for unassigned residues. NBNB TBD draft - needs checking"""

    apiNmrChain = self._wrappedData
    apiChain = apiNmrChain.chain
    if apiChain is None:
      apiStretch = apiNmrChain.connectedStretch
      if apiStretch is None:
        apiResGroups = ()
      else:
        apiResGroups = apiStretch.activeResonanceGroups
    else:
      func1 = apiNmrChain.nmrProject.findFirstResonanceGroup
      apiResGroups = [func1(seqCode=x.seqCode, seqInsertCode=x.seqInsertCode, relativeOffset=None)
                      for x in apiChain.sortedResidues()]
    #
    func2 =  self._parent._data2Obj.get
    return tuple(None if x is None else func2(x) for x in apiResGroups)

  @connectedNmrResidues.setter
  def connectedNmrResidues(self, value:Sequence):
    # NBNB TBD Check validity of code.
    apiNmrChain = self._wrappedData
    apiChain = apiNmrChain.chain
    if apiChain is None:
      apiStretch = apiNmrChain.connectedStretch
      if apiStretch is None:
        if value:
          apiStretch = apiNmrChain.nmrProject.newConnectedStretch(
            activeResonanceGroups= [x._wrappedData for x in value],
            sequentialAssignment=apiNmrChain.nmrProject.activeSequentialAssignment
          )
      else:
        if value:
          apiStretch.activeResonanceGroups = [x._wrappedData for x in value]
        else:
          apiStretch.delete()
    else:
      raise ValueError("Cannot set connectedNmrResidues for NmrChain assigned to actual Chain")


  @property
  def chain(self) -> Chain:
    """Chain to which NmrChain is assigned"""
    chain = self._wrappedData.assignedResidue
    return None if chain is None else self._project._data2Obj.get(chain)

  @chain.setter
  def chain(self, value:Chain):
    self._wrappedData.chain = None if value is None else value._wrappedData

  def rename(self, value:str):
    """Rename NmrChain, changing its Id and Pid"""
    wrappedData = self._apiNmrChain
    if not value:
      raise ValueError("NmrChain name must be set")
    elif wrappedData.code == Constants.defaultNmrChainCode:
      raise ValueError("NmrChain:%s cannot be renamed" % Constants.defaultNmrChainCode)
    elif Pid.altCharacter in value:
      raise ValueError("Character %s not allowed in ccpn.NmrChain.shortName" % Pid.altCharacter)
    else:
      wrappedData.code = value

  @classmethod
  def _getAllWrappedData(cls, parent: Project)-> list:
    """get wrappedData (Nmr.DataSources) for all Spectrum children of parent Project"""
    return parent._wrappedData.sortedNmrChains()


def getter(self:Chain) -> NmrChain:
  obj = self._project._wrappedData.findFirstNmrChain(code=self._wrappedData.code)
  return None if obj is None else self._project._data2Obj.get(obj)

def setter(self:Chain, value:NmrChain):
  oldValue = self.nmrChain
  if oldValue is value:
    return
  elif oldValue is not None:
    oldValue.chain = None

  if value is not None:
    value.chain = self
Chain.nmrChain = property(getter, setter, None, "NmrChain to which Chain is assigned")

del getter
del setter

def _newNmrChain(self:Project, shortName:str=None, comment:str=None) -> NmrChain:
  """Create new ccpn.NmrChain

  :param str shortName: shortName for new nmrChain (optional, defaults to '@n' n positive integer
  :param str comment: comment for new nmrChain (optional)"""
  
  nmrProject = self._apiNmrProject
  
  if shortName is None:
    code = "@1"
    ii = 1
    while nmrProject.findFirstNmrChain(code=code) is not None:
      ii += 1
      code = '@%s' % ii
    shortName = code

  if Pid.altCharacter in shortName:
    raise ValueError("Character %s not allowed in ccpn.NmrChain.shortName" % Pid.altCharacter)


  newApiNmrChain = nmrProject.newNmrChain(code=shortName, details=comment)
  
  return self._data2Obj.get(newApiNmrChain)
  
def fetchNmrChain(self:Project, shortName:str=None) -> NmrChain:
  """Fetch chain with given shortName; If none exists call newNmrChain to make one first

  :param str shortName: shortName for new chain (optional)
  """

  if shortName and Pid.altCharacter in shortName:
    raise ValueError("Character %s not allowed in ccpn.NmrChain.shortName" % Pid.altCharacter)

  nmrProject = self._apiNmrProject
  apiNmrChain = nmrProject.findFirstNmrChain(code=shortName)
  if apiNmrChain is None:
    return self._project.newNmrChain(shortName=shortName)
  else:
    return self._data2Obj.get(apiNmrChain)

  
# Clean-up
    
# Connections to parents:
Project._childClasses.append(NmrChain)
Project.newNmrChain = _newNmrChain
del _newNmrChain
Project.fetchNmrChain = fetchNmrChain

# Notifiers:
className = ApiNmrChain._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':NmrChain}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete'),
    ('_resetPid', {}, className, 'setCode'),
    ('_finaliseUnDelete', {}, className, 'undelete'),
  )
)
