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
import typing

from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.Substance import Substance
from ccpn.core.Substance import SampleComponent
from ccpnmodel.ccpncore.api.ccp.molecule.MolSystem import Chain as ApiChain
from ccpnmodel.ccpncore.api.ccp.molecule import Molecule
from ccpnmodel.ccpncore.api.ccp.lims import Sample
from ccpn.core.lib import Pid
from typing import Tuple, Optional, Union, Sequence



class Chain(AbstractWrapperObject):
  """A molecular Chain, containing one or more Residues."""
  
  #: Short class name, for PID.
  shortClassName = 'MC'
  # Attribute it necessary as subclasses must use superclass className
  className = 'Chain'

  _parentClass = Project

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
  def isCyclic(self) -> bool:
    """True if this is a cyclic polymer."""
    return self._wrappedData.molecule.isStdCyclic
  
  @property
  def comment(self) -> str:
    """Free-form text comment."""
    return self._wrappedData.details
    
  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

  @property
  def substances(self) -> Tuple[Substance, ...]:
    """Substances matching to Chain (based on chain.compoundName)"""
    compoundName = self.compoundName
    return tuple(x for x in self.project.substances if x.name == compoundName)

    # # Select 'std' labelling if present
    # substances = [x for x in substances if x.labelling is None] or substances
    #
    # return substances[0] if substances else None

  @property
  def sampleComponents(self) -> Tuple[SampleComponent, ...]:
    """SampleComponents matching to Chain (based on chain.compoundName)"""
    compoundName = self.compoundName
    return tuple(x for x in self.project.sampleComponents if x.name == compoundName)

  # CCPN functions
  def clone(self, shortName:str=None):
    """Make copy of chain."""

    # Imported here to avoid circular imports
    from ccpn.core.lib import MoleculeLib

    apiMolSystem = self._project._wrappedData.molSystem

    if shortName is None:
      shortName = apiMolSystem.nextChainCode()

    if apiMolSystem.findFirstChain(code=shortName) is not None:
      raise ValueError("Project already has one Chain with shortName %s" % shortName)
    
    ccpnChain = self._wrappedData
    tags = ['molecule', 'role', 'magnEquivalenceCode', 'physicalState', 
            'conformationalIsomer', 'chemExchangeState', 'details']
    params = {tag:getattr(ccpnChain,tag) for tag in tags}
    params['code'] = shortName
    params['pdbOneLetterCode'] = shortName[0]
    self._startFunctionCommandBlock('clone', shortName, parName='newChain')
    try:
      newCcpnChain = apiMolSystem.newChain(**params)
      result = self._project._data2Obj[newCcpnChain]
      MoleculeLib.duplicateAtomBonds({self:result})
    finally:
      self._project._appBase._endCommandBlock()
    #
    return result
                                  

  def _lock(self):
    """Finalize chain so that it can no longer be modified, and add missing data."""
    self._startFunctionCommandBlock('_lock')
    try:
      self._wrappedData.molecule.isFinalised = True
    finally:
      self._project._appBase._endCommandBlock()


  # Implementation functions

  def rename(self, value:str):
    """Rename Chain, changing its shortName and Pid."""
    if value:
      previous = self._project.getChain(value.translate(Pid.remapSeparators))
      if previous not in (None, self):
        raise ValueError("%s already exists" % previous.longPid)
    else:
      raise ValueError("Chain name must be set")

    self._startFunctionCommandBlock('rename', value)
    try:
      self._apiChain.renameChain(value)
      self._finaliseAction('rename')
      self._finaliseAction('change')
    finally:
      self._project._appBase._endCommandBlock()


  @classmethod
  def _getAllWrappedData(cls, parent:Project)-> list:
    """get wrappedData (MolSystem.Chains) for all Chain children of parent NmrProject.molSystem"""
    molSystem =  parent._wrappedData.molSystem
    if molSystem is None:
      return []
    else:
      return molSystem.sortedChains()



def _createChain(self:Project, sequence:Union[str,Sequence[str]], compoundName:str=None,
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

  defaults = collections.OrderedDict(
    (('compoundName', None), ('startNumber', 1), ('molType', None), ('isCyclic', False),
     ('shortName', None), ('role', None), ('comment', None)
    )
  )

  apiMolSystem = self._wrappedData.molSystem
  if not shortName:
    shortName = apiMolSystem.nextChainCode()

  previous = self._project.getChain(shortName.translate(Pid.remapSeparators))
  if previous is not None:
    raise ValueError("%s already exists" % previous.longPid)

  apiRefComponentStore = self._apiNmrProject.sampleStore.refSampleComponentStore
  if compoundName is None:
    name = self._uniqueSubstanceName()
  elif apiRefComponentStore.findFirstComponent(name=compoundName) is None:
    name = compoundName
  else:
    raise ValueError(
      "Substance named %s already exists. Try Substance.createChain function instead?"
      % compoundName)

  self._startFunctionCommandBlock('createChain', sequence, values=locals(), defaults=defaults,
                                  parName='newChain')
  try:
    substance = self.createPolymerSubstance(sequence=sequence, name=name,
                                            startNumber=startNumber, molType=molType,
                                            isCyclic=isCyclic, comment=comment)

    apiMolecule = substance._apiSubstance.molecule
    apiMolecule.isFinalised = True
    # fetch to ensure creation of Substance
    newApiChain = apiMolSystem.newChain(molecule=apiMolecule, code=shortName, role=role,
                                        details=comment)
  finally:
    self._project._appBase._endCommandBlock()
  return self._project._data2Obj[newApiChain]
Project.createChain = _createChain
del _createChain


def _createChainFromSubstance(self:Substance, shortName:str=None, role:str=None,
                             comment:str=None) -> Chain:
  """Create new Chain that matches Substance"""
  defaults = collections.OrderedDict((('shortName', None), ('role', None), ('comment', None)))

  if self.substanceType != 'Molecule':
    raise ValueError("Only Molecule Substances can be used to create chains")

  apiMolecule = self._apiSubstance.molecule
  if apiMolecule is None:
    raise ValueError("API MolComponent must have attached ApiMolecule in order to create chains")

  apiMolSystem = self._project._apiNmrProject.molSystem
  if shortName is None:
    shortName = apiMolSystem.nextChainCode()

  previous = self._project.getChain(shortName.translate(Pid.remapSeparators))
  if previous is not None:
    raise ValueError("%s already exists" % previous.longPid)

  self._startFunctionCommandBlock('createChain', values=locals(), defaults=defaults,
                                  parName='newChain')
  try:
    newApiChain = apiMolSystem.newChain(molecule=apiMolecule, code=shortName, role=role,
                                         details=comment)
    #
    result = self._project._data2Obj[newApiChain]
  finally:
    self._project._appBase._endCommandBlock()

  return result
Substance.createChain = _createChainFromSubstance
del _createChainFromSubstance


def getter(self:Substance) -> Tuple[Chain, ...]:

  name = self.name
  return tuple(x for x in self._project.chains if x.compoundName == name)

  # apiSubstance = self._apiSubstance
  # apiMolecule = apiSubstance.molecule if hasattr(apiSubstance, 'molecule') else None
  # if apiMolecule is None:
  #   return ()
  # else:
  #   data2Obj = self._project._data2Obj
  #   return tuple(data2Obj[x]
  #                for x in self._project._wrappedData.molSystem.sortedChains()
  #                if x.molecule is apiMolecule)
Substance.chains = property(getter, None, None,
  "ccpn.Chains that correspond to ccpn.Substance (if defined)"
)

def getter(self:SampleComponent) -> Tuple[Chain, ...]:
  name = self.name
  return tuple(x for x in self._project.chains if x.compoundName == name)
SampleComponent.chains = property(getter, None, None,
  "ccpn.Chains that correspond to ccpn.SampleComponent (if defined)"
)

del getter

# Clean-up
    
Chain.clone.__annotations__['return'] = Chain

# Connections to parents:
# No 'new' function - chains are made elsewhere


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
