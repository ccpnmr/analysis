
import functools

from ccpn._AbstractWrapperClass import AbstractWrapperClass
from ccpn._Chain import Chain
from ccpcore.api.molecule.MolSystem import Residue as Ccpn_Residue
from ccpnmr.dataIo.DataMapper import DataMapper

def splitIntFromChars(value:str):
  """convert a string with a leading integer optionally followed by characters
  into an (integer,string) tuple"""
  
  #NBNB TODO should be moved to a Util library
  
  value = value.strip()
  
  for ii in reversed(range(1,len(value)+1)):
    try:
      number = int(value[:ii])
      chars = value[ii:]
      break
    except ValueError:
      continue
  else:
    number = None
    chars = value
      
    
  return number,chars



class Residue(AbstractWrapperClass):
  """Molecular Residue."""
  
  # Short class name, for PID.
  shortClassName = 'MR'
  
  # List of child classes. 
  _childClasses = []
  

  # CCPN properties  
  @property
  def ccpnResidue(self) -> Ccpn_Residue:
    """ CCPN residue matching Residue"""
    return self._wrappedData
  
  
  @property
  def id(self) -> str:
    """Residue sequence code and id (e.g. '1', '127B') """
    obj = self._wrappedData
    return str(obj.seqCode) + obj.seqInsertCode.strip()
  
  seqCode = id
    
  @property
  def _parent(self) -> Chain:
    """Parent (containing) object."""
    return self._project._data2Obj[self._wrappedData.chain]
  
  molecule = _parent
    
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
  
    
  @classmethod
  def _getNotifiers(cls, project) -> list:
    """Get list of (className,funcName,notifier) tuples"""
    
    # NBNB TBD we should likely have som system of deleteAfter, createAfter
    
    #
    className = Ccpn_Residue.qualifiedName
    result = [(className, 'delete', self.delete), 
              (className, '__init__', functools.partial(cls,project=project))]
    return result
    
    
def newResidue(parent:Chain, name:str, seqCode:str=None, linking:str=None,
               descriptor:str=None, molType:str=None, comment:str=None) -> Chain:
  """Create new child Residue"""
  project = parent._project
  ccpnChain = parent._wrappedData
  ccpnMolecule = ccpnChain.molecule

  if ccpnMolecule.isFinalized:
    raise Exception("Chain {} can no longer be extended".format(parent))

  # get chem comp ID strings from residue name
  molType, ccpCode = DataMapper.selectChemCompId(project.residueName2chemCompIds,
                                                 name, prefMolType=molType)

  # split seqCode in number+string
  intCode, seqInsertCode = splitIntFromChars(seqCode)
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
Chain.residues = Residue._wrappedChildProperty()
#Molecule.residues = Residue._wrappedChildProperty()
# NBNB TODO fix grandchild link, currentl not working

# NBNB the below may not be inserted correctly as a method
Chain.newResidue = newResidue
