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

from ccpn._wrapper._AbstractWrapperClass import AbstractWrapperClass
from ccpn._wrapper._Project import Project
from ccpncore.api.ccp.molecule.MolSystem import Chain as Ccpn_Chain
from ccpncore.lib import MoleculeModify
from ccpncore.lib.DataMapper import DataMapper
from ccpncore.util import Common as commonUtil


class Chain(AbstractWrapperClass):
  """Molecular Chain."""
  
  #: Short class name, for PID.
  shortClassName = 'MC'

  #: Name of plural link to instances of class
  _pluralLinkName = 'chains'
  
  #: List of child classes.
  _childClasses = []
  

  # CCPN properties  
  @property
  def ccpnChain(self) -> Ccpn_Chain:
    """ CCPN chain matching Chain"""
    return self._wrappedData
  
  
  # @property
  # def id(self) -> str:
  #   """Molecule id: shortName"""
  #   return self._wrappedData.code
    
  @property
  def id(self) -> str:
    """short form of name, used for id"""
    return self._wrappedData.code.replace('.','_').replace(':','_')

  shortName = id
    
  @property
  def compoundName(self) -> str:
    """Short name of chemical compound (e.g. 'Lysozyme') making up Chain"""
    return self._wrappedData.molecule.name
    
  @property
  def _parent(self) -> Project:
    """Parent (containing) object."""
    return self._project
  
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
  def copy(self, shortName:str):
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
    """Finalize chain so that it can no longer be modified"""
    self._wrappedData.molecule.isFinalized = True
  
  def addResidues(self, sequence:Sequence, startNumber:int=None,
                     preferredMolType:str=None):
    """Add sequence to chain, without setting bonds to pre-existing residues

    :param Sequence sequence: a sequence of three-letter-codes, CCPN residue type codes\
    or one-letter codes if sequence contains more than one residue, it is assumed that\
    the residues form a linear polymer

    :param int startNumber: residue number of first residue in sequence. \
    If not given, is it one  more than the last

    :param str preferredMolType: MolType to use in case of ambiguity (one of 'protein', \
    'DNA', 'RNA', 'carbohydrate', 'other'"""

    ccpnChain = self._wrappedData
    ccpnMolecule = ccpnChain.molecule
    
    if ccpnMolecule.isFinalized or ccpnMolecule.sortedChains != [ccpnChain]:
      raise ValueError("Chain {} can no longer be modified".format(self))

    if not sequence:
      msg = "No residues given to add to chain"
      self._project._logger.warning(msg)
      return

    # get startNumber for new sequence
    if startNumber is None:
      ll = ccpnMolecule.sortedMolResidues()
      if ll:
        startNumber = ll[-1].serial + 1
      else:
        startNumber = 1

    dd = self._project._residueName2chemCompIds
    ccSequence = [DataMapper.pickChemCompId(dd, x, prefMolType=preferredMolType)
                  for x in sequence]
    if None in ccSequence:
      ii = ccSequence.index(None)
      msg = "Residue %s in sequence: %s not recognised" % (ii, sequence[ii])
      self._project._logger.warning(msg)
      return

    if len(sequence) == 1:
      # Single residue. Add it
      tt = ccSequence[0]
      if tt:
        molType, ccpCode = tt
      else:
        msg = "No ChemComp ID found for %s" % sequence
        self._project._logger.error(msg)
        raise ValueError(msg)

      chemComp = ccpnMolecule.root.findFirstChemComp(molType=molType, ccpCode=ccpCode)
      chemCompVar = (chemComp.findFirstChemCompVar(linking='none', isDefaultVar=True) or
                     chemComp.findFirstChemCompVar(linking='none'))
      molResidues = [ccpnMolecule.newMolResidue(chemCompVar=chemCompVar, seqCode=startNumber)]

    else:
      # multiple residues, add as linear polymer

      molResidues = MoleculeModify.makeLinearSequence(ccpnMolecule, ccSequence,
                                                      seqCodeStart=startNumber)

    # make MolSystem Residues
    for molResidue in molResidues:
      ccpnChain.newResidue(self, seqId=molResidue.serial,seqCode=molResidue.seqCode,
                           seqInsertCode=molResidue.seqInsertCode, linking=molResidue.linking,
                           descriptor=molResidue.descriptor )

    # make ChainFragments
    ccpnChain.createChainFragments()


  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:Project)-> list:
    """get wrappedData (MolSystem.Chains) for all Chain children of parent NmrProject.molSystem"""
    return parent._wrappedData.molSystem.sortedChains()


def newChain(parent:Project, compoundName:str, shortName:str=None,
             role:str=None, comment:str=None) -> Chain:
  """Create new child Chain, empty or matching existing compound
  
  :param str compoundName: Name of new compound (CCPN_Molecule) matching chain, \
      Will use matching molecule if one exists.
  :param str shortName: shortName for new chain (optional)
  :param str role: role for new chain (optional)
  :param str comment: comment for new chain (optional)"""
  
  ccpnMolSystem = parent.nmrProject.molSystem
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
  
def makeChain(parent:Project, sequence, compoundName:str,
              startNumber:int=1, preferredMolType:str=None, 
              shortName:str=None, role:str=None, comment:str=None) -> Chain:
  """Make new chain from sequence of residue codes
  
  :param Sequence sequence: string of one-letter or sequence of three-residue type codes \
  if empty uses existing molecule (if any)

  :param str compoundName: name of new CCPN_Molecule (e.g. 'Lysozyme')
  :param str preferredMolType: preferred molType to use for ambiguous codes (mainly \
  one-letter codes). Normal preference order is: \
  'protein','DNA', 'RNA', 'carbohydrate', 'other'. \
  :param int startNumber: number of first residue in sequence
  :param str shortName: shortName for new chain (optional)
  :param str role: role for new chain (optional)
  :param str4 comment: comment for new chain (optional)

  """

  if not sequence:
    msg = "makeChain requires non-empty sequence"
    parent._project._logger.error(msg)
    raise ValueError(msg)

  # rename compoundName if necessary
  ccpnRoot = parent._wrappedData.root
  oldName = compoundName
  while ccpnRoot.findFirstMolecule(name=compoundName):
    compoundName = commonUtil.incrementName(compoundName)
  if oldName != compoundName:
    parent._project._logger.warning(
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
Project._childClasses.append(Chain)
Project.newChain = newChain
Project.makeChain = makeChain

# Notifiers:
className = Ccpn_Chain._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':Chain}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
