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

from ccpn._wrapper._AbstractWrapperObject import AbstractWrapperObject
from ccpn._wrapper._AbstractWrapperObject import ResidueAssignment
from ccpn._wrapper._Project import Project
from ccpn._wrapper._Chain import Chain
from ccpncore.api.ccp.molecule.MolSystem import Residue as Ccpn_Residue
from ccpncore.lib.DataMapper import DataMapper
from ccpncore.util import Common as commonUtil

class Residue(AbstractWrapperObject):
  """Molecular Residue."""
  
  #: Short class name, for PID.
  shortClassName = 'MR'

  #: Name of plural link to instances of class
  _pluralLinkName = 'residues'
  
  #: List of child classes.
  _childClasses = []
  

  # CCPN properties  
  @property
  def ccpnResidue(self) -> Ccpn_Residue:
    """ CCPN residue matching Residue"""
    return self._wrappedData
  
  
  @property
  def sequenceCode(self) -> str:
    """Residue sequence code and id (e.g. '1', '127B') """
    obj = self._wrappedData
    objSeqCode = obj.seqCode
    result = (obj.seqInsertCode or '').strip()
    if objSeqCode is not None:
      result = str(objSeqCode) + result
    return result

  @property
  def id(self) -> str:
    """Residue ID. Identical to sequenceCode, with '.' and ':' replaced by '_'"""
    return self.sequenceCode.replace('.','_').replace(':','_')
    
  @property
  def _parent(self) -> Chain:
    """Parent (containing) object."""
    return self._project._data2Obj[self._wrappedData.chain]
  
  chain = _parent
    
  @property
  def name(self) -> str:
    """Residue type name string (e.g. 'ALA')"""
    return self._wrappedData.code3Letter

  @name.setter
  def name(self, value:str):
    self._wrappedData.code3Letter = value
    molType, ccpCode = DataMapper.pickChemCompId(self._project._residueName2chemCompIds,
                                                 value)
    # NBNB TBD reorganise model so that code3Letter is used throughout, and change this
    self._wrappedData.molType = molType
    self._wrappedData.ccpCode = ccpCode

  # @property
  # def molType(self) -> str:
  #   """Molecule type string ('protein', 'DNA', 'RNA', 'carbohydrate', or 'other')"""
  #   return self._wrappedData.molType
  
  @property
  def linking(self) -> str:
    """linking (substitution pattern) code for residue"""
    return self._wrappedData.linking
    
  @linking.setter
  def linking(self, value:str):
    self._wrappedData.linking = value
  
  @property
  def descriptor(self) -> str:
    """variant descriptor (protonation state etc.) for residue"""
    return self._wrappedData.descriptor
    
  @descriptor.setter
  def descriptor(self, value:str):
    self._wrappedData.descriptor = value
  
  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details
    
  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

  @property
  def assignment(self) -> str:
    """ResidueAssignment named tuple (chainCode, sequenceCode, residueType)"""
    obj = self._wrappedData
    return ResidueAssignment(obj.chain.code, self.sequenceCode, obj.code3Letter)
    
    
  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent: Chain)-> list:
    """get wrappedData (MolSystem.Residues) for all Residue children of parent Chain"""
    return parent._wrappedData.sortedResidues()
    
    
def newResidue(parent:Chain, name:str, sequenceCode:str=None, linking:str=None,
               descriptor:str=None, molType:str=None, comment:str=None) -> Residue:
  """Create new child Residue"""
  project = parent._project
  ccpnChain = parent._wrappedData
  ccpnMolecule = ccpnChain.molecule

  if ccpnMolecule.isFinalized:
    raise Exception("Chain {} can no longer be extended".format(parent))

  # get chem comp ID strings from residue name
  molType, ccpCode = DataMapper.pickChemCompId(project._residueName2chemCompIds,
                                               name, prefMolType=molType)

  # split sequenceCode in number+string
  intCode, seqInsertCode = commonUtil.splitIntFromChars(sequenceCode)
  if len(seqInsertCode) > 1:
    raise Exception(
      "Only one non-numerical character suffix allowed for sequenceCode {}".format(sequenceCode)
    )

  # make residue
  ccpnResidue = ccpnChain.newResidue(molType=molType, ccpCode=ccpCode,
                                     linking=linking, descriptor=descriptor,
                                     details=comment)

  if intCode is None:
    ccpnResidue.seqCode = ccpnResidue.seqId
  else:
    ccpnResidue.seqCode = intCode
    ccpnResidue.seqInsertCode = seqInsertCode

  return parent._project._data2Obj.get(ccpnResidue)
    
    
    
# Connections to parents:
Chain._childClasses.append(Residue)

Chain.newResidue = newResidue

# Notifiers:
className = Ccpn_Residue._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':Residue}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
