"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
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
from collections.abc import Sequence

from ccpn._wrapper._AbstractWrapperObject import AbstractWrapperObject
from ccpn._wrapper._Project import Project
from ccpncore.api.ccp.molecule.MolSystem import Chain as ApiChain
from ccpncore.lib import MoleculeModify
from ccpncore.lib.DataMapper import DataMapper
from ccpncore.util import Common as commonUtil
from ccpncore.lib import pid as Pid


class Chain(AbstractWrapperObject):
  """Molecular Chain."""
  
  #: Short class name, for PID.
  shortClassName = 'MC'

  #: Name of plural link to instances of class
  _pluralLinkName = 'chains'
  
  #: List of child classes.
  _childClasses = []
  

  # CCPN properties  
  @property
  def apiChain(self) -> ApiChain:
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
                                  

  def finalize(self):
    """Finalize chain so that it can no longer be modified, and add missing data."""
    self._wrappedData.molecule.isFinalised = True
  
  # def addResidues(self, sequence:Sequence, startNumber:int=None,
  #                    preferredMolType:str=None):
  #   """Add sequence to chain, without setting bonds to pre-existing residues
  #
  #   :param Sequence sequence: a sequence of three-letter-codes, CCPN residue type codes\
  #   or one-letter codes if sequence contains more than one residue, it is assumed that\
  #   the residues form a linear polymer
  #
  #   :param int startNumber: residue number of first residue in sequence. \
  #   If not given, is it one  more than the last
  #
  #   :param str preferredMolType: MolType to use in case of ambiguity (one of 'protein', \
  #   'DNA', 'RNA', 'carbohydrate', 'other'"""
  #
  #   ccpnChain = self._wrappedData
  #   ccpnMolecule = ccpnChain.molecule
  #
  #   if ccpnMolecule.isFinalised or ccpnMolecule.sortedChains != [ccpnChain]:
  #     raise ValueError("Chain {} can no longer be modified".format(self))
  #
  #   if not sequence:
  #     msg = "No residues given to add to chain"
  #     self._project._logger.warning(msg)
  #     return
  #
  #   # get startNumber for new sequence
  #   if startNumber is None:
  #     ll = ccpnMolecule.sortedMolResidues()
  #     if ll:
  #       startNumber = ll[-1].serial + 1
  #     else:
  #       startNumber = 1
  #
  #   dd = self._project._residueName2chemCompIds
  #   ccSequence = [DataMapper.pickChemCompId(dd, x, prefMolType=preferredMolType)
  #                 for x in sequence]
  #   if None in ccSequence:
  #     ii = ccSequence.index(None)
  #     msg = "Residue %s in sequence: %s not recognised" % (ii, sequence[ii])
  #     self._project._logger.warning(msg)
  #     return
  #
  #   if len(sequence) == 1:
  #     # Single residue. Add it
  #     tt = ccSequence[0]
  #     if tt:
  #       molType, ccpCode = tt
  #     else:
  #       msg = "No ChemComp ID found for %s" % sequence
  #       self._project._logger.error(msg)
  #       raise ValueError(msg)
  #
  #     chemComp = ccpnMolecule.root.findFirstChemComp(molType=molType, ccpCode=ccpCode)
  #     chemCompVar = (chemComp.findFirstChemCompVar(linking='none', isDefaultVar=True) or
  #                    chemComp.findFirstChemCompVar(linking='none'))
  #     molResidues = [ccpnMolecule.newMolResidue(chemCompVar=chemCompVar, seqCode=startNumber)]
  #
  #   else:
  #     # multiple residues, add as linear polymer
  #
  #     molResidues = MoleculeModify.makeLinearSequence(ccpnMolecule, ccSequence,
  #                                                     seqCodeStart=startNumber)
  #
  #   # make MolSystem Residues
  #   for molResidue in molResidues:
  #     ccpnChain.newResidue(self, seqId=molResidue.serial,seqCode=molResidue.seqCode,
  #                          seqInsertCode=molResidue.seqInsertCode, linking=molResidue.linking,
  #                          descriptor=molResidue.descriptor )
  #
  #   # make ChainFragments
  #   ccpnChain.createChainFragments()

  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:Project)-> list:
    """get wrappedData (MolSystem.Chains) for all Chain children of parent NmrProject.molSystem"""
    molSystem =  parent._wrappedData.molSystem
    if molSystem is None:
      return []
    else:
      return parent._wrappedData.molSystem.sortedChains()


# def newChain(parent:Project, compoundName:str, shortName:str=None,
#              role:str=None, comment:str=None) -> Chain:
#   """Create new child Chain, empty or matching existing compound
#
#   :param str compoundName: Name of new compound (CCPN_Molecule) matching chain, \
#       Will use matching molecule if one exists. If None will create dummy name.
#   :param str shortName: shortName for new chain (optional)
#   :param str role: role for new chain (optional)
#   :param str comment: comment for new chain (optional)"""
#
#   ccpnMolSystem = parent.nmrProject.molSystem
#   ccpnRoot = ccpnMolSystem.root
#
#   if shortName is None:
#     shortName = MoleculeModify.nextChainCode(ccpnMolSystem)
#
#   ccpnMolecule = ccpnRoot.findFirstMolecule(name=compoundName)
#   if ccpnMolecule is None:
#     ccpnMolecule = ccpnRoot.newMolecule(name=compoundName,
#                                         longName=compoundName)
#
#   newCcpnChain = ccpnMolSystem.newChain(molecule=ccpnMolecule,
#                                         code=shortName,
#                                         pdbOneLetterCode=shortName[0],
#                                         role=role,
#                                         details=comment)
#
#   return parent._project._data2Obj.get(newCcpnChain)
  
def makeChains(parent:Project, residueRecords) -> Chain:
  """Make chains from sequence of  tuples
  
  :param Sequence residueRecords: (chainCode, sequenceCode, residueType, linking, descriptor) tuples
  sequenceCode defaults to the seqId of the residue;
  descriptor defaults to give the default variant;
  sequence records must be grouped by chainCode;
  Only records between a start and and end linking are connected as linear polymers.
  """

  ccpnRoot = parent._wrappedData.root
  ccpnMolSystem = parent._wrappedData.molSystem
  residueName2chemCompIds = parent._residueName2chemCompIds
  code2Molecule = {}
  ccpnMolecule = None
  sequence = None
  chains = []

  currentChainCode = None
  for oldRecord in residueRecords:
    (chainCode, sequenceCode, residueType, linking, descriptor) = oldRecord
    seqCode, seqInsertCode, junk = commonUtil.parseSequenceCode(sequenceCode)
    tt = DataMapper.pickChemCompId(residueName2chemCompIds, residueType)
    if tt is None:
      print("WARNING Skipping - no ChemComp found for record: %s" % (oldRecord,))
      continue
    else:
      molType, ccpCode = DataMapper.pickChemCompId(residueName2chemCompIds, residueType)
    newRecord = (molType, ccpCode, linking, descriptor, seqCode, seqInsertCode)

    if ccpnMolecule is None or chainCode != currentChainCode:
      if chainCode in code2Molecule:
        raise ValueError("Sequence must have records for each chain contiguous")

      if sequence:
        raise ValueError("Chain %s ends with unfinished sequence" % chainCode)

      currentChainCode = chainCode

      # no molecule name. Invent one, and make molecule
      compoundName = 'Molecule_1'
      while ccpnRoot.findFirstMolecule(name=compoundName) is not None:
        compoundName = commonUtil.incrementName(compoundName)
      ccpnMolecule = ccpnRoot.newMolecule(name=compoundName, longName=compoundName)
      code2Molecule[chainCode] = ccpnMolecule

    if sequence is None:
      if linking == 'start':
        sequence = [newRecord]
      elif linking == 'end':
        raise ValueError("Illegal 'end' residue linking outside of sequence: %s" % newRecord)
      else:
        # Linking defaults to 'non' when not in a sequence
        linking = linking or 'none'
        ccpnMolecule.newMolResidue(seqCode=seqCode, seqInsertCode=seqInsertCode,
                                   molType=molType, ccpCode=ccpCode, linking=linking,
                                   descriptor=descriptor, code3Letter=residueType)
    else:
      if linking in  ('start', 'none'):
        raise ValueError("Illegal residue linking in the middle of sequence: %s" % (oldRecord,))

      sequence.append(newRecord)
      if linking == 'end':
        # Finish current sequence
        seqCodeStart = sequence[0][4]
        molResidues = MoleculeModify.makeLinearSequence(ccpnMolecule,
                                                        [tt[:2] for tt in sequence],
                                                        seqCodeStart=seqCodeStart)
        for ii,tt in enumerate(sequence):
          molResidue = molResidues[ii]
          molResidue.seqCode = tt[4]
          molResidue.seqInsertCode = tt[5] or ' '

        sequence = None

  # Finished molecule. Make chains
  for chainCode,ccpnMolecule in sorted(code2Molecule.items()):
    useChainCode = chainCode
    while ccpnMolSystem.findFirstChain(code=useChainCode):
      useChainCode = commonUtil.incrementName(useChainCode)
    chain = ccpnMolSystem.newChain(molecule=ccpnMolecule, code=useChainCode,
                                   pdbOneLetterCode=useChainCode[0])
    chains.append(chain)
    ccpnMolecule.isFinalised = True

  # NBNB TBD decriptors are not set.
  # NBNB TBD no allowance for crosslinks

  #
  return chains

def makeSimpleChain(parent:Project, sequence, compoundName:str='Molecule_1',
              startNumber:int=1, preferredMolType:str=None,
              shortName:str=None, role:str=None, comment:str=None) -> Chain:
  """Make new chain from sequence of residue codes, using default linking and variants

  :param Sequence sequence: string of one-letter or sequence of three-residue type codes

  :param str compoundName: name of new CCPN_Molecule (e.g. 'Lysozyme')
  :param str preferredMolType: preferred molType to use for ambiguous codes (mainly \
  one-letter codes). Normal preference order is: \
  'protein','DNA', 'RNA', 'carbohydrate', 'other'. \
  :param int startNumber: number of first residue in sequence
  :param str shortName: shortName for new chain (optional)
  :param str role: role for new chain (optional)
  :param str comment: comment for new chain (optional)

  """
  project = parent._project
  ccpnRoot = parent._wrappedData.root
  ccpnMolSystem = parent._wrappedData.molSystem
  if shortName is None:
    shortName = MoleculeModify.nextChainCode(ccpnMolSystem)
  elif ccpnMolSystem.findFirstChain(code=shortName) is not None:
    raise ValueError("Chain names %s already exists" % shortName)

  if not sequence:
    raise ValueError("makeChain requires non-empty sequence")

  # rename compoundName if necessary
  oldName = compoundName
  while ccpnRoot.findFirstMolecule(name=compoundName):
    compoundName = commonUtil.incrementName(compoundName)
  if oldName != compoundName:
    project._logger.warning(
      "CCPN molecule named %s already exists. New molecule has been named %s" %
      (oldName,compoundName))
  ccpnMolecule = ccpnRoot.newMolecule(name=compoundName, longName=oldName)

  dd = project._residueName2chemCompIds
  ccSequence = [DataMapper.pickChemCompId(dd, x, prefMolType=preferredMolType)
                for x in sequence]
  if None in ccSequence:
    ii = ccSequence.index(None)
    msg = "Residue %s in sequence: %s not recognised" % (ii, sequence[ii])
    project._logger.warning(msg)
    return

  if len(sequence) == 1:
    # Single residue. Add it
    tt = ccSequence[0]
    if tt:
      molType, ccpCode = tt
    else:
      msg = "No ChemComp ID found for %s" % sequence
      parent._project._logger.error(msg)
      raise ValueError(msg)

    chemComp = ccpnMolecule.root.findFirstChemComp(molType=molType, ccpCode=ccpCode)
    chemCompVar = (chemComp.findFirstChemCompVar(linking='none', isDefaultVar=True) or
                   chemComp.findFirstChemCompVar(linking='none'))
    ccpnMolecule.newMolResidue(chemCompVar=chemCompVar, seqCode=startNumber)

  else:
    # multiple residues, add as linear polymer
    MoleculeModify.makeLinearSequence(ccpnMolecule, ccSequence, seqCodeStart=startNumber)

  newCcpnChain = ccpnMolSystem.newChain(molecule=ccpnMolecule, role=role, details=comment)
  #
  return project._data2Obj[newCcpnChain]


  
# Clean-up
    
Chain.clone.__annotations__['return'] = Chain
    
    
# Connections to parents:
Project._childClasses.append(Chain)
# Project.newChain = newChain
Project.makeSimpleChain = makeSimpleChain
Project.makeChains = makeChains

# Notifiers:
className = ApiChain._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':Chain}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
