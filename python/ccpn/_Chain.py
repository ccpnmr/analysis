
from ccpn._AbstractWrapperClass import AbstractWrapperClass
from ccpn._Molecule import Molecule
from ccpn._Project import Project
from ccpncore.api.ccp.molecule.MolSystem import Chain as Ccpn_Chain

from ccpncore.lib import MoleculeModify
from ccpncore.lib.DataMapper import DataMapper
from ccpncore.util import Common as commonUtil


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
                                  

  def finalize(self):
    """Finalize chain so that it can no longer be modified"""
    self._wrappedData.molecule.isFinalized = True
  
  def addResidues(self, sequence:"iterable", startNumber:int=None,
                     preferredMolType=None):
    """Add sequence to chain, without setting bonds to pre-existing residues  
    
    sequence:: a sequence of CCPN residue type codes or one-letter codes
    if sequence contains more than one residue, it is assumed that the residues
    form a linear polymer
    startNumber:: residue number of first residue in sequence.
    If not given, is it one  more than the last
    preferredMolType:: MolType to use in case of ambiguity (one of 'protein',
                       'DNA', 'RNA', 'carbohydrate', 'other'"""



    ccpnChain = self._wrappedData
    ccpnMolecule = ccpnChain.molecule
    
    if ccpnMolecule.isFinalized or ccpnMolecule.sortedChains != [ccpnChain]:
      raise ValueError("Chain {} can no longer be modified".format(self))

    if not sequence:
      msg = "No residues given to add to chain"
      self._project.logger.error(msg)
      return

    # get startNumber for new sequence
    if startNumber is None:
      ll = ccpnMolecule.sortedMolResidues()
      if ll:
        startNumber = ll[-1].serial + 1
      else:
        startNumber = 1

    getccId = DataMapper.selectChemCompId
    dd = self._project._residueName2chemCompIds

    if len(sequence) == 1:
      # Single residue. Add it
      tt = getccId(sequence[0])
      if tt:
        molType, ccpCode = tt
      else:
        msg = "No ChemComp ID found for %s" % sequence
        self._project.logger.error(msg)
        raise ValueError(msg)

      chemComp = ccpnMolecule.root.findFirstChemComp(molType=molType, ccpCode=ccpCode)
      chemCompVar = (chemComp.findFirstChemCompVar(linking='none', isDefaultVar=True) or
                     chemComp.findFirstChemCompVar(linking='none'))
      molResidues = [ccpnMolecule.newMolResidue(chemCompVar=chemCompVar, seqCode=startNumber)]

    else:
      # multiple residues, add as linear polumer

      molResidues = MoleculeModify.makeLinearSequence(ccpnMolecule,
        [getccId(dd, resType, prefMolType=preferredMolType) for resType in sequence],
        seqCodeStart=startNumber
      )

    # make MolSystem Residues
    for molResidue in molResidues:
      ccpnChain.newResidue(self, seqId=molResidue.serial,seqCode=molResidue.seqCode,
                           seqInsertCode=molResidue.seqInsertCode, linking=molResidue.linking,
                           descriptor=molResidue.descriptor )

    # make ChainFragments
    ccpnChain.createChainFragments()


  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent: Molecule)-> list:
    """get wrappedData (MolSystem.Chains) for all Chain children of parent Molecule"""
    return parent._wrappedData.sortedChains()

def newChain(parent:Molecule, compoundName:str, shortName:str=None, 
             role:str=None, comment:str=None) -> Chain:
  """Create new child Chain, empty or matrching existing molecule
  
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
  
def makeChain(parent:Molecule, sequence, compoundName:str,
              startNumber:int=1, preferredMolType:str=None, 
              shortName:str=None, role:str=None, comment:str=None) -> Chain:
  """Make new chain from sequence of residue codes
  
  sequence:: string of one-letter or sequence of three-residue type codes
  if empty uses existing molecule (if any)
  compoundName:: name of new CCPN_Molecule (e.g. 'Lysozyme')
  preferredMolType:: preferred molType to use for ambiguous codes (mainly 
                     one-letter codes). Normal preference order is: 
                     'protein','DNA', 'RNA', 'carbohydrate', 'other'.
  startNumber:: number of first residue in sequence
  shortName:: shortName for new chain (optional)
  role:: role for new chain (optional)
  comment:: comment for new chain (optional)"""

  if not sequence:
    msg = "makeChain requires non-empty sequence"
    parent._project.logger.error(msg)
    raise ValueError(msg)

  # rename compoundName if necessary
  ccpnRoot = parent._wrappedData.root
  oldName = compoundName
  while ccpnRoot.findFirstMolecule(name=compoundName):
    compoundName = commonUtil.incrementName(compoundName)
  if oldName != compoundName:
    parent._project.logger.warning(
      "CCPN molecule named %s already exists. New molecule has been named %s" %
      (oldName,compoundName))

  chain = parent.newChain(compoundName=compoundName, shortName=shortName,
                             role=role, comment=comment)

  chain.addResidues(sequence=sequence, startNumber=startNumber,
                    preferredMolType=preferredMolType)
  chain.finalize()
  
  #
  return chain


  
# Clean-up
    
Chain.copy.__annotations__['return'] = Chain
    
    
# Connections to parents:
Molecule._childClasses.append(Chain)
Molecule.chains = Chain._wrappedChildProperty()
Molecule.newChain = newChain
Molecule.makeChain = makeChain

# Notifiers:
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':Chain}, Ccpn_Chain.qualifiedName, '__init__'),
    ('_finaliseDelete', {}, Ccpn_Chain.qualifiedName, 'delete')
  )
)
