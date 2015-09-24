"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================

__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
from ccpncore.util.typing import Sequence

from ccpn import AbstractWrapperObject
from ccpn import Project
from ccpncore.api.ccp.molecule.MolSystem import Chain as ApiChain
from ccpncore.lib.molecule import MoleculeModify
from ccpncore.util import Pid



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
    """Change object id, modifying entire project to maintain consistency.
    NBNB TBD to be implemented"""
    raise NotImplementedError("Chain rename not implemented yet")

  @classmethod
  def _getAllWrappedData(cls, parent:Project)-> list:
    """get wrappedData (MolSystem.Chains) for all Chain children of parent NmrProject.molSystem"""
    molSystem =  parent._wrappedData.molSystem
    if molSystem is None:
      return []
    else:
      return parent._wrappedData.molSystem.sortedChains()

#
# def _makeChains(parent:Project, residueRecords) -> Chain:
#   """Make chains from sequence of  tuples
#
#   :param Sequence residueRecords: (chainCode, sequenceCode, residueType, linking, descriptor) tuples
#   sequenceCode defaults to the seqId of the residue;
#   descriptor defaults to give the default variant;
#   sequence records must be grouped by chainCode;
#   Only records between a start and and end linking are connected as linear polymers.
#   """
#
#   NBNB TBD refactor
#   NBNB Move somewhere else (currently used only for NEF)
#   NBNB Needs fixing before activation
#
#   ccpnRoot = parent._wrappedData.root
#   ccpnMolSystem = parent._wrappedData.molSystem
#   residueName2chemCompIds = parent._residueName2chemCompIds
#   code2Molecule = {}
#   ccpnMolecule = None
#   sequence = None
#   chains = []
#
#   currentChainCode = None
#   for oldRecord in residueRecords:
#     (chainCode, sequenceCode, residueType, linking, descriptor) = oldRecord
#     seqCode, seqInsertCode, junk = commonUtil.parseSequenceCode(sequenceCode)
#     tt = DataMapper.pickChemCompId(residueName2chemCompIds, residueType)
#     if tt is None:
#       print("WARNING Skipping - no ChemComp found for record: %s" % (oldRecord,))
#       continue
#     else:
#       molType, ccpCode = tt
#     newRecord = (molType, ccpCode, linking, descriptor, seqCode, seqInsertCode)
#
#     if ccpnMolecule is None or chainCode != currentChainCode:
#       if chainCode in code2Molecule:
#         raise ValueError("Sequence must have records for each chain contiguous")
#
#       if sequence:
#         raise ValueError("Chain %s ends with unfinished sequence" % chainCode)
#
#       currentChainCode = chainCode
#
#       # no molecule name. Invent one, and make molecule
#       compoundName = 'Molecule_1'
#       while ccpnRoot.findFirstMolecule(name=compoundName) is not None:
#         compoundName = commonUtil.incrementName(compoundName)
#       ccpnMolecule = ccpnRoot.newMolecule(name=compoundName, longName=compoundName)
#       code2Molecule[chainCode] = ccpnMolecule
#
#     if sequence is None:
#       if linking == 'start':
#         sequence = [newRecord]
#       elif linking == 'end':
#         raise ValueError("Illegal 'end' residue linking outside of sequence: %s" % (newRecord,))
#       else:
#         # Linking defaults to 'non' when not in a sequence
#         linking = linking or 'none'
#         ccpnMolecule.newMolResidue(seqCode=seqCode, seqInsertCode=seqInsertCode,
#                                    molType=molType, ccpCode=ccpCode, linking=linking,
#                                    descriptor=descriptor, code3Letter=residueType)
#     else:
#       if linking in  ('start', 'none'):
#         raise ValueError("Illegal residue linking in the middle of sequence: %s" % (oldRecord,))
#
#       sequence.append(newRecord)
#       if linking == 'end':
#         # Finish current sequence
#         seqCodeStart = sequence[0][4]
#         molResidues = MoleculeModify.addLinearSequence(ccpnMolecule,
#                                                         [tt[:2] for tt in sequence],
#                                                         seqCodeStart=seqCodeStart)
#         for ii,tt in enumerate(sequence):
#           molResidue = molResidues[ii]
#           molResidue.seqCode = tt[4]
#           molResidue.seqInsertCode = tt[5] or ' '
#
#         sequence = None
#
#   # Finished molecule. Make chains
#   for chainCode,ccpnMolecule in sorted(code2Molecule.items()):
#     useChainCode = chainCode
#     while ccpnMolSystem.findFirstChain(code=useChainCode):
#       useChainCode = commonUtil.incrementName(useChainCode)
#     chain = ccpnMolSystem.newChain(molecule=ccpnMolecule, code=useChainCode,
#                                    pdbOneLetterCode=useChainCode[0])
#     chains.append(chain)
#     ccpnMolecule.isFinalised = True
#
#   # NBNB TBD decriptors are not set.
#   # NBNB TBD no allowance for crosslinks
#
#   #
#   return chains

def createChainFromSubstance(self:Project, substance:"Substance", shortName:str=None, role:str=None,
                             comment:str=None) -> Chain:
  """Create new chain that matches Substance - throws error is Substance is not of valid type"""

  if substance.substanceType != 'MolComponent':
    raise ValueError("Only MolComponent Substances can be used to create chains")

  apiMolecule = substance._apiSubstance.molecule
  if apiMolecule is None:
    raise ValueError("MolComponent miust have attaehed ApiMolecule in order to create chains")

  apiMolSystem = self._wrappedData.molSystem
  if shortName is None:
    shortName = apiMolSystem.nextChainCode()

  newApiChain = apiMolSystem.newChain(molecule=apiMolecule, code=shortName, role=role,
                                       details=comment)
  #
  return  self._project._data2Obj[newApiChain]



def _createSimpleChain(self:Project, sequence:(str,tuple), compoundName:str='Molecule_1',
              startNumber:int=1, molType:str=None, isCyclic:bool=False,
              shortName:str=None, role:str=None, comment:str=None) -> Chain:
  """Make new chain from sequence of residue codes, using default linking and variants

  Automatically creates the corresponding Substance if the name is not already taken

  :param Sequence sequence: string of one-letter codes or sequence of str residueNames
  :param str compoundName: name of new CCPN_Molecule (e.g. 'Lysozyme')
  :param str molType: molType ('protein','DNA', 'RNA'). Required only if sequence is a string.
  :param int startNumber: number of first residue in sequence
  :param str shortName: shortName for new chain (optional)
  :param str role: role for new chain (optional)
  :param str comment: comment for new chain (optional)

  """
  apiMolSystem = self._wrappedData.molSystem
  if shortName is None:
    shortName = apiMolSystem.nextChainCode()

  if not sequence:
    raise ValueError("createSimpleChain requires non-empty sequence")

  elif apiMolSystem.findFirstChain(code=shortName) is not None:
    raise ValueError("Chain names %s already exists" % shortName)

  name = self.uniqueSubstanceName(compoundName)

  apiMolecule = MoleculeModify.createMolecule(apiMolSystem.root, sequence, molType=molType,
                                             name=name, startNumber=startNumber,
                                             isCyclic=isCyclic)
  apiMolecule.isFinalised = True
  # fetch to ensure creation of Substance
  self._wrappedData.sampleStore.refSampleComponentStore.fetchMolComponent(apiMolecule)
  newApiChain = apiMolSystem.newChain(molecule=apiMolecule, code=shortName, role=role,
                                      details=comment)
  #
  return  self._project._data2Obj[newApiChain]

  
# Clean-up
    
Chain.clone.__annotations__['return'] = Chain
    
    
# Connections to parents:
Project._childClasses.append(Chain)
# Project.newChain = newChain
Project.createSimpleChain = _createSimpleChain
# Project._makeChains = _makeChains

# Notifiers:
className = ApiChain._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':Chain}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
