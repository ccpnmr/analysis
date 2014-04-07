
import functools

from ccpcode._AbstractWrapperClass import AbstractWrapperClass
from ccpcode._Molecule import Molecule
from ccpncore.api.ccp..molecule.MolSystem import Chain as Ccpn_Chain
from ccp.lib import MoleculeModify
from ccpnmr.dataIo.DataMapper import DataMapper


class Chain(AbstractWrapperClass):
  """Molecular Chain."""
  
  # Short class name, for PID.
  shortClassName = 'MC'
  
  # List of child classes. 
  _childClasses = []
  

  # CCPN properties  
  @property
  def ccpnChain(self) -> Ccpn_Chain:
    """ CCPN chain matching Chain"""
    return self._wrappedData
  
  
  @property
  def id(self) -> str:
    """Molecule id: shortName"""
    return self._wrappedData.code
    
  @property
  def shortName(self) -> str:
    """short form of name, used for id"""
    return self._wrappedData.code
    
  @property
  def compoundName(self) -> str:
    """Short name of chemical compound (e.g. 'Lysozyme') making up Chain"""
    return self._wrappedData.molecule.name
    
  @property
  def _parent(self) -> Molecule:
    """Parent (containing) object."""
    return self._project._data2Obj[self._wrappedData.molSystem]
  
  molecule = _parent
  
  @property
  def role(self) -> str:
    """role of chain in Molecule"""
    return self._wrappedData.role
    
  @role.setter
  def role(self, value:str):
    self._wrappedData.role = value
  
  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details
    
  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

  # CCPN functions
  def copy(self, newMolecule:Molecule=None, shortName=None):
    """Make copy of chain."""
    
    if newMolecule is None and shortName is None:
      raise Exception("Chain.copy must have newMolecule or shortName given")
    
    parent = (newMolecule or self.molecule)._wrappedData
    
    ccpnChain = self._wrappedData
    tags = ['molecule', 'role', 'magnEquivalenceCode', 'physicalState', 
            'conformationalIsomer', 'chemExchangeState', 'details']
    params = {tag:getattr(ccpnChain,tag) for tag in tags}
    if shortName is None:
      params['code'] = ccpnChain.code
      params['pdbOneLetterCode'] = ccpnChain.pdbOneLetterCode
    else:
      params['code'] = shortName
      params['pdbOneLetterCode'] = shortName[0]
      
    newCcpnChain = parent.newChain(**params)
    
    #
    return self._project._data2Obj[newCcpnChain]
                                  

  def finalizeChain(self):
    """Finalize chain so that it can no longer be modified"""
    self._wrappedData.molecule.isFinalized = True
  
  def extendSequence(self, sequence:"iterable", startNumber:int=None,
                     preferredMolType=None):
    """Add sequence to chain, without setting bonds to pre-existing residues  
    
    sequence:: a sequence of CCPN residue type codes or one-letter codes
    startNumber:: residue number of first residue in sequence
    preferredMolType:: MolType to use in case of ambiguity (one of 'protein',
                       'DNA', 'RNA', 'carbohydrate', 'other'"""
    
    ccpnChain = self._wrappedData
    ccpnMolecule = ccpnChain.molecule
    
    if ccpnMolecule.isFinalized:
      raise Exception("Chain {} can no longer be extended".format(self))
    
    ff = DataMapper.selectChemCompId
    dd = self._project.residueName2chemCompIds
    MoleculeModify.addMixedResidues(ccpnMolecule,
      [ff(dd, resType, prefMolType=preferredMolType) for resType in sequence],
      startNumber=startNumber
    )
    
    
  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent: Molecule)-> list:
    """get wrappedData (MolSystem.Chains) for all Chain children of parent Molecule"""
    return parent._wrappedData.sortedChains()
  
    
  @classmethod
  def _getNotifiers(cls, project) -> list:
    """Get list of (className,funcName,notifier) tuples"""
    
    # NBNB TBD we should likely have som system of deleteAfter, createAfter
    
    #
    className = Ccpn_Chain.qualifiedName
    result = [(className, 'delete', self.delete),
              (className, '__init__', functools.partial(cls,project=project))]
    return result
    
def newChain(parent:Molecule, compoundName:str, shortName:str=None, 
             role:str=None, comment:str=None) -> Chain:
  """Create new child Chain
  
  compoundName:: Name of new CCPN_Molecule matching chain; 
                 will use matching molecule if one exists.
  shortName:: shortName for new chain (optional)
  role:: role for new chain (optional)
  comment:: comment for new chain (optional)"""
  
  ccpnMolSystem = parent.ccpnMolSystem
  ccpnRoot = ccpnMolSystem.root
  
  if shortName is None:
    shortName = MoleculeModify.nextChainCode(ccpnMolSystem)
  
  ccpnMolecule = ccpnRoot.findFirstMolecule(name=compoundName)
  if ccpnMolecule is None:
    ccpnMolecule = ccpnRoot.newMolecule(name=compoundName, 
                                        longName=compoundName)
  
  newCcpnChain = ccpnMolSystem.newChain(molecule=ccpnMolecule,
                                        code=shortName, 
                                        pdbOneLetterCode=shortName[0],
                                        role=role,
                                        details=comment)
  
  return parent._project._data2Obj.get(newCcpnChain)
  
def makeChain(parent:Molecule, sequence:str, compoundName:str, 
              startNumber:int=1, preferredMolType:str=None, 
              shortName:str=None, role:str=None, comment:str=None) -> Chain:
  """Make new chain from sequence of residue codes
  
  sequence:: string of one- or three-letter residue type codes
  compoundName:: name of new CCPN_Molecule (e.g. 'Lysozyme')
  preferredMolType:: preferred molType to use for ambiguous codes (mainly 
                     one-letter codes). Normal preference order is: 
                     'protein','DNA', 'RNA', 'carbohydrate', 'other'.
  startNumber:: number of first residue in sequence
  shortName:: shortName for new chain (optional)
  role:: role for new chain (optional)
  comment:: comment for new chain (optional)"""
  
  ccpnRoot = parent._wrappedData.root
  if ccpnRoot.findFirstMolecule(name=compoundName):
    raise Exception("CCPN_Molecule named {} already exists")
  
  newChain = parent.newChain(compoundName=compoundName, shortName=shortName, 
                             role=role, comment=comment)
                      
  newChain.extendSequence(sequence=sequence, startNumber=startNumber,
                          preferredMolType=preferredMolType)
  
  newChain.finalize()
  
  #
  return newChain


  
# Clean-up
    
Chain.copy.__annotations__['return'] = Chain
    
    
# Connections to parents:

Molecule._childClasses.append(Chain)
Molecule.chains = Chain._wrappedChildProperty()

# NBNB the below may not be inserted correctly as a method
Molecule.newChain = newChain
Molecule.makeChain = makeChain
