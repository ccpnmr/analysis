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

# from typing import Sequence
from ccpn import AbstractWrapperObject
from ccpn import Project
from ccpn import Chain
from ccpn import Residue
from ccpn.util import Pid
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

  # Qualified name of matching API class
  _apiClassQualifiedName = ApiNmrChain._metaclass.qualifiedName()
  

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
    """short form of name, used in Pid and to identify the NmrChain
    Names of the form '\@ijk' and '#ijk' (where ijk is an integers)
    are reserved and cannot be set. They can be obtained by the deassign command.
    Connected NmrChains (isConnected == True) always have canonical names of the form '#ijk'"""
    return self._wrappedData.code

  @property
  def label(self) -> str:
    """Identifying label of NmrChain.

    Defaults to the canonical name '@ijk' (for unconnected) or '#ijk' (for connected) NmrChains
    (ijk is an integer.), but freely changeable."""
    return self._wrappedData.label

  @label.setter
  def label(self, value:str):
    self._wrappedData.label = value

  @property
  def _parent(self) -> Project:
    """Parent (containing) object."""
    return self._project
  
  @property
  def isConnected(self) -> bool:
    """Is this NmrChain a connected stretch
    (in which case the mainNmrResidues are sequentially connected"""
    return self._wrappedData.isConnected

  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details

  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value


  @property
  def chain(self) -> Chain:
    """Chain to which NmrChain is assigned"""
    chain = self._wrappedData.chain
    return None if chain is None else self._project._data2Obj.get(chain)

  @chain.setter
  def chain(self, value:Chain):
    if value is None:
      if self.chain is None:
        return
      else:
        self.deassign()
    else:
      # NB The API code will throw ValueError if there is already an NmrChain with that code
      self.rename(value._wrappedData.code)

  def rename(self, value:str):
    """Rename NmrChain, changing its Id and Pid.
    Use the 'deassign' function if you want to revert to the canonical name"""
    wrappedData = self._apiNmrChain
    if self._wrappedData.isConnected:
      raise ValueError("Connected NmrChain cannot be renamed")
    elif not value:
      raise ValueError("NmrChain name must be set")
    elif value == wrappedData.code:
      return
    elif wrappedData.code == Constants.defaultNmrChainCode:
      raise ValueError("NmrChain:%s cannot be renamed" % Constants.defaultNmrChainCode)
    elif Pid.altCharacter in value:
      raise ValueError("Character %s not allowed in ccpn.NmrChain.shortName" % Pid.altCharacter)
    else:
      # NB names that clash with existing NmrChains cause ValueError at the API level.
      wrappedData.code = value

  def deassign(self):
    """Reset NmrChain back to its originalName, cutting all assignment links"""
    self._wrappedData.code = None

  def assignConnectedResidues(self, firstResidue:Residue):
    """Assign all NmrResidues in connected NmrChain sequentially,
    with the first NmrResidue assigned to firstResidue.

    Returns ValueError if NmrChain is not connected,
    or if any of the Residues are missing or already assigned"""

    apiNmrChain = self._wrappedData

    if not self.isConnected:
      raise ValueError("assignConnectedResidues only allowed for connected NmrChains")

    apiStretch = apiNmrChain.mainResonanceGroups
    if firstResidue.nmrResidue is not None:
      raise ValueError("Cannot assign %s NmrResidue stretch: First Residue %s is already assigned"
      % (len(apiStretch), firstResidue.id))

    residues = [firstResidue]
    for ii in range(len(apiStretch) - 1):
      res = residues[ii]
      next = res.nextResidue
      if next is None:
        raise ValueError("Cannot assign %s NmrResidues to %s Residues from Chain"
                         % (len(apiStretch), len(residues)))
      elif next.nmrResidue is not None:
        raise ValueError("Cannot assign %s NmrResidue stretch: Residue %s is already assigned"
        % (len(apiStretch), next.id))

      else:
        residues.append(next)

    # If we get here we are OK - assign residues and delete NmrChain
    for ii,res in enumerate(residues):
      apiStretch[ii].assignedResidue = res._wrappedData
    apiNmrChain.delete()


  @classmethod
  def _getAllWrappedData(cls, parent: Project)-> list:
    """get wrappedData (Nmr.DataSources) for all Spectrum children of parent Project"""
    return parent._wrappedData.sortedNmrChains()


def getter(self:Chain) -> NmrChain:
  obj = self._project._wrappedData.findFirstNmrChain(code=self._wrappedData.code)
  return None if obj is None else self._project._data2Obj.get(obj)

def setter(self:Chain, value:NmrChain):
  if value is None:
     raise ValueError("nmrChain cannot be set to None")
  else:
     value.chain = self
Chain.nmrChain = property(getter, setter, None, "NmrChain to which Chain is assigned")

del getter
del setter

def _newNmrChain(self:Project, shortName:str=None, isConnected:bool=False, label:str='?',
                 comment:str=None) -> NmrChain:
  """Create new ccpn.NmrChain. Set isConnected=True to get connected NmrChain.

  :param str shortName: shortName for new nmrChain (optional, defaults to '@ijk' or '#ijk',  ijk positive integer
  :param bool isConnected: (default to False) If true the NmrChain is a connected stretch. This can NOT be changed later
  :param str label: Modifiable NmrChain identifier that does not change with reassignment. Defaults to '@ijk'/'#ijk'
  :param str comment: comment for new nmrChain (optional)"""
  
  nmrProject = self._apiNmrProject
  
  if shortName:
    if Pid.altCharacter in shortName:
      raise ValueError("Character %s not allowed in ccpn.NmrChain.shortName" % Pid.altCharacter)
  else:
    shortName = None

  newApiNmrChain = nmrProject.newNmrChain(code=shortName, isConnected=isConnected, label=label,
                                          details=comment)
  
  return self._data2Obj.get(newApiNmrChain)
  
def fetchNmrChain(self:Project, shortName:str=None) -> NmrChain:
  """Fetch chain with given shortName; If none exists call newNmrChain to make one first
  """

  if shortName and Pid.altCharacter in shortName:
    raise ValueError("Character %s not allowed in ccpn.NmrChain.shortName" % Pid.altCharacter)

  nmrProject = self._apiNmrProject
  apiNmrChain = nmrProject.findFirstNmrChain(code=shortName)
  if apiNmrChain is None:
    if shortName and shortName[0] in '@#' and shortName[1:].isdigit():
      raise ValueError("Cannot create new NmrChain with reserved name %s" % shortName)
    else:
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
  ( ('_finaliseApiRename', {}, className, 'setImplCode'),
  )
)
Chain.setupCoreNotifier('rename', AbstractWrapperObject._finaliseRelatedObjectFromRename,
                          {'pathToObject':'nmrChain', 'action':'rename'})

# NB Chain<->NmrChain link depends solely on the NmrChain name.
# So no notifiers on the link - notify on the NmrChain rename instead.
