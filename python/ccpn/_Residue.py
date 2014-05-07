
from ccpn._AbstractWrapperClass import AbstractWrapperClass
from ccpn._Project import Project
from ccpn._Chain import Chain
from ccpncore.api.ccp.molecule.MolSystem import Residue as Ccpn_Residue
from ccpncore.lib.DataMapper import DataMapper
from ccpncore.util import Common as commonUtil

class Residue(AbstractWrapperClass):
  """Molecular Residue."""
  
  # Short class name, for PID.
  shortClassName = 'MR'

  # Name of plural link to instances of class
  _pluralLinkName = 'residues'
  
  # List of child classes. 
  _childClasses = []
  

  # CCPN properties  
  @property
  def ccpnResidue(self) -> Ccpn_Residue:
    """ CCPN residue matching Residue"""
    return self._wrappedData
  
  
  @property
  def seqCode(self) -> str:
    """Residue sequence code and id (e.g. '1', '127B') """
    obj = self._wrappedData
    return str(obj.seqCode) + obj.seqInsertCode.strip()
  
  id = seqCode
    
  @property
  def _parent(self) -> Chain:
    """Parent (containing) object."""
    return self._project._data2Obj[self._wrappedData.chain]
  
  chain = _parent
    
  @property
  def name(self) -> str:
    """Residue type name string (e.g. 'Ala')"""
    return self._wrappedData.ccpCode
    
  @property
  def molType(self) -> str:
    """Molecule type string ('protein', 'DNA', 'RNA', 'carbohydrate', or 'other')"""
    return self._wrappedData.molType
  
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
    
  @linking.setter
  def linking(self, value:str):
    self._wrappedData.descriptor = value
  
  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details
    
  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value
    
    
  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent: Chain)-> list:
    """get wrappedData (MolSystem.Residues) for all Residue children of parent Chain"""
    return parent._wrappedData.sortedResidues()
    
    
def newResidue(parent:Chain, name:str, seqCode:str=None, linking:str=None,
               descriptor:str=None, molType:str=None, comment:str=None) -> Residue:
  """Create new child Residue"""
  project = parent._project
  ccpnChain = parent._wrappedData
  ccpnMolecule = ccpnChain.molecule

  if ccpnMolecule.isFinalized:
    raise Exception("Chain {} can no longer be extended".format(parent))

  # get chem comp ID strings from residue name
  molType, ccpCode = DataMapper.selectChemCompId(project._residueName2chemCompIds,
                                                 name, prefMolType=molType)

  # split seqCode in number+string
  intCode, seqInsertCode = commonUtil.splitIntFromChars(seqCode)
  if len(seqInsertCode) > 1:
    raise Exception(
      "Only one non-numerical character suffix allowed for seqCode {}".format(seqCode)
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
