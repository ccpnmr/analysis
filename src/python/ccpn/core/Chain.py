"""Module Documentation here

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

from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.Substance import Substance
from ccpn.core.SampleComponent import SampleComponent
from ccpnmodel.ccpncore.api.ccp.molecule.MolSystem import Chain as ApiChain
from ccpnmodel.ccpncore.api.ccp.molecule import Molecule
from ccpnmodel.ccpncore.api.ccp.lims import Sample
from ccpn.util import Pid
from typing import Tuple, Optional, Union, Sequence



class Chain(AbstractWrapperObject):
  """Molecular Chain."""
  
  #: Short class name, for PID.
  shortClassName = 'MC'
  # Attribute it necessary as subclasses must use superclass className
  className = 'Chain'

  #: Name of plural link to instances of class
  _pluralLinkName = 'chains'
  
  #: List of child classes.
  _childClasses = []

  # Qualified name of matching API class
  _apiClassQualifiedName = ApiChain._metaclass.qualifiedName()
  

  # CCPN properties  
  @property
  def _apiChain(self) -> ApiChain:
    """ CCPN chain matching Chain"""
    return self._wrappedData
    
  @property
  def _key(self) -> str:
    """short form of name, corrected to use for id"""
    return self._wrappedData.code.translate(Pid.remapSeparators)

  @property
  def shortName(self) -> str:
    """short form of name"""
    return self._wrappedData.code
    
  @property
  def compoundName(self) -> str:
    """Short name of chemical compound (e.g. 'Lysozyme') making up Chain"""
    return self._wrappedData.molecule.name
    
  @property
  def _parent(self) -> Project:
    """Parent (containing) object."""
    return self._project
  
  @property
  def role(self) -> str:
    """The role of the chain in a molecular complex or sample - free text. Could be 'free',
    ''bound', 'open', 'closed', 'minor form B', ..."""
    return self._wrappedData.role
    
  @role.setter
  def role(self, value:str):
    self._wrappedData.role = value

  @property
  def isCyclic(self) -> str:
    """Is this a cyclic polymer?"""
    return self._wrappedData.molecule.isCyclic
  
  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details
    
  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

  @property
  def substance(self) -> Optional[Substance]:
    """ccpn.Substance with sequence matching to ccpn.Chain

    If there are multiple matches, select labeling=='std'
    or, failing that, the first found (sorting alphabetically on labeling)"""
    compoundName = self.compoundName
    substances = [x for x in self.project.substances if x.name == compoundName]

    # Select 'std' labeling if present
    substances = [x for x in substances if x.labeling == 'std'] or substances

    return substances[0] if substances else None

    # apiMolecule = self._apiChain.molecule
    # apiRefComponentStore = self._project._apiNmrProject.sampleStore.refSampleComponentStore
    # apiComponent = (apiRefComponentStore.findFirstComponent(name=apiMolecule.name, labeling='std') or
    #                 apiRefComponentStore.findFirstComponent(name=apiMolecule.name))
    # if apiComponent is None:
    #   return None
    # else:
    #   return self._project._data2Obj[apiComponent]

  # CCPN functions
  def clone(self, shortName:str):
    """Make copy of chain."""

    molSystem = self._project._wrappedData.molSystem

    if molSystem.findFirstChain(code=shortName) is not None:
      raise ValueError("Project already hsa one Chain with shortNAme %s" % shortName)
    
    ccpnChain = self._wrappedData
    tags = ['molecule', 'role', 'magnEquivalenceCode', 'physicalState', 
            'conformationalIsomer', 'chemExchangeState', 'details']
    params = {tag:getattr(ccpnChain,tag) for tag in tags}
    params['code'] = shortName
    params['pdbOneLetterCode'] = shortName[0]
      
    newCcpnChain = molSystem.newChain(**params)
    
    #
    return self._project._data2Obj[newCcpnChain]
                                  

  def finalise(self):
    """Finalize chain so that it can no longer be modified, and add missing data."""
    self._wrappedData.molecule.isFinalised = True


  # Implementation functions

  def rename(self, value:str):
    """Rename Chain, changing its Id and Pid"""
    if not value:
      raise ValueError("Chain name must be set")
    elif Pid.altCharacter in value:
      raise ValueError("Character %s not allowed in Chain.shortName" % Pid.altCharacter)
    self._apiChain.renameChain(value)
    self._finaliseAction('rename')
    self._finaliseAction('change')


  @classmethod
  def _getAllWrappedData(cls, parent:Project)-> list:
    """get wrappedData (MolSystem.Chains) for all Chain children of parent NmrProject.molSystem"""
    molSystem =  parent._wrappedData.molSystem
    if molSystem is None:
      return []
    else:
      return parent._wrappedData.molSystem.sortedChains()



def _createChain(self:Project, sequence:Union[str,Sequence[str]], compoundName:str='Molecule_1',
              startNumber:int=1, molType:str=None, isCyclic:bool=False,
              shortName:str=None, role:str=None, comment:str=None) -> Chain:
  """Create new chain from sequence of residue codes

  Automatically creates the corresponding polymer Substance if the compoundName is not already taken

  :param Sequence sequence: string of one-letter codes or sequence of residue types
  :param str compoundName: name of new Substance (e.g. 'Lysozyme') Defaults to 'Molecule_n
  :param str molType: molType ('protein','DNA', 'RNA'). Needed only if sequence is a string.
  :param int startNumber: number of first residue in sequence
  :param str shortName: shortName for new chain (optional)
  :param str role: role for new chain (optional)
  :param str comment: comment for new chain (optional)

  """

  apiMolSystem = self._wrappedData.molSystem
  if shortName is None:
    shortName = apiMolSystem.nextChainCode()

  if Pid.altCharacter in shortName:
    raise ValueError("Character %s not allowed in ccpn.Chain.shortName" % Pid.altCharacter)

  apiRefComponentStore = self._apiNmrProject.sampleStore.refSampleComponentStore
  if compoundName is None:
    name = self._uniqueSubstanceName()
  elif apiRefComponentStore.findFirstComponent(name=compoundName) is None:
    name = compoundName
  else:
    raise ValueError(
      "Substance named %s already exists. Try Substance.createChain function instead?"
      % compoundName)

  if apiMolSystem.findFirstChain(code=shortName) is not None:
    raise ValueError("Chain names %s already exists" % shortName)

  substance = self.createPolymerSubstance(sequence=sequence, name=name,
                                          startNumber=startNumber, molType=molType,
                                          isCyclic=isCyclic, comment=comment)

  apiMolecule = substance._apiSubstance.molecule
  apiMolecule.isFinalised = True
  # fetch to ensure creation of Substance
  newApiChain = apiMolSystem.newChain(molecule=apiMolecule, code=shortName, role=role,
                                      details=comment)
  #
  return  self._project._data2Obj[newApiChain]
Project.createChain = _createChain


def _createChainFromSubstance(self:Substance, shortName:str=None, role:str=None,
                             comment:str=None) -> Chain:
  """Create new ccpn.Chain that matches ccpn.Substance"""

  if self.substanceType != 'Molecule':
    raise ValueError("Only Molecule Substances can be used to create chains")

  apiMolecule = self._apiSubstance.molecule
  if apiMolecule is None:
    raise ValueError("API MolComponent must have attached ApiMolecule in order to create chains")

  apiMolSystem = self._project._apiNmrProject.molSystem
  if shortName is None:
    shortName = apiMolSystem.nextChainCode()

  if Pid.altCharacter in shortName:
    raise ValueError("Character %s not allowed in ccpn.Chain.shortName" % Pid.altCharacter)


  newApiChain = apiMolSystem.newChain(molecule=apiMolecule, code=shortName, role=role,
                                       details=comment)
  #
  return  self._project._data2Obj[newApiChain]
Substance.createChain = _createChainFromSubstance
del _createChainFromSubstance


def getter(self:Substance) -> Tuple[Chain, ...]:

  apiSubstance = self._apiSubstance
  apiMolecule = apiSubstance.molecule if hasattr(apiSubstance, 'molecule') else None
  if apiMolecule is None:
    return ()
  else:
    data2Obj = self._project._data2Obj
    return tuple(data2Obj[x]
                 for x in self._project._wrappedData.molSystem.sortedChains()
                 if x.molecule is apiMolecule)
Substance.chains = property(getter, None, None,
  "ccpn.Chains that correspond to the sequence of ccpn.Substance (if defined)"
)

del getter

# Clean-up
    
Chain.clone.__annotations__['return'] = Chain

# No 'new' function - chains are made elsewhere
    
# Connections to parents:
Project._childClasses.append(Chain)
# Project._makeChains = _makeChains

# Notifiers:
# Crosslinks: substance
className = Molecule.Molecule._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_modifiedLink', {'classNames':('Chain','Substance')}, className, 'create'),
    ('_modifiedLink', {'classNames':('Chain','Substance')}, className, 'delete'),
  )
)
# Crosslinks: sampleComponent
className = Sample.SampleComponent._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_modifiedLink', {'classNames':('Chain','SampleComponent')}, className, 'addChainCode'),
    ('_modifiedLink', {'classNames':('Chain','SampleComponent')}, className, 'removeChainCode'),
    ('_modifiedLink', {'classNames':('Chain','SampleComponent')}, className, 'setChainCodes'),
  )
)
