"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

from ccpn._wrapper._AbstractWrapperClass import AbstractWrapperClass
from ccpn._wrapper._Project import Project
from ccpn._wrapper._NmrChain import NmrChain
from ccpncore.api.ccp.nmr.Nmr import ResonanceGroup
from ccpncore.lib.DataMapper import DataMapper
from ccpncore.util import Common as commonUtil

class NmrResidue(AbstractWrapperClass):
  """Nmr Residue, for assignment."""
  
  #: Short class name, for PID.
  shortClassName = 'NR'

  #: Name of plural link to instances of class
  _pluralLinkName = 'nmrResidues'
  
  #: List of child classes.
  _childClasses = []
  

  # CCPN properties  
  @property
  def resonanceGroup(self) -> ResonanceGroup:
    """ CCPN resonanceGroup matching Residue"""
    return self._wrappedData
  
  
  @property
  def sequenceCode(self) -> str:
    """Residue sequence code and id (e.g. '1', '127B', '@157+1) """
    return self._wrappedData.sequenceCode

  # NBNB TBD we need rename function to set this

  @property
  def id(self) -> str:
    """Residue ID. Identical to seqCode, with '.' and ':' replaced by '_'"""
    return self._wrappedData.sequenceCode.replace('.','_').replace(':','_')
    
  @property
  def _parent(self) -> NmrChain:
    """Parent (containing) object."""
    return self._project._data2Obj[self._wrappedData.chain]
  
  nmrChain = _parent

  @property
  def name(self) -> str:
    """Residue type name string (e.g. 'Ala')"""
    return self._wrappedData.code3Letter

  @name.setter
  def name(self, value:str):
    ccpnNmrResidue = self._wrappedData
    ccpnNmrResiduea.code3Letter = value

    # get chem comp ID strings from residue name
    tt = DataMapper.pickChemCompId(self._project._residueName2chemCompIds, value)
    if tt is not None:
      ccpnNmrResidue.molType, ccpnNmrResidue.ccpCode = tt
  
  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details
    
  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value
    
    
  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent: NmrChain)-> list:
    """get wrappedData (MolSystem.Residues) for all Residue children of parent Chain"""
    return parent._wrappedData.sortedResonanceGroups()
    
    
def newNmrResidue(parent:NmrChain, name:str, sequenceCode:str=None, comment:str=None) -> NmrResidue:
  """Create new child Residue"""
  nmrProject = parent._project._wrappedData

  nmrProject.newResonanceGroup
  ccpnChain = parent._wrappedData
  ccpnMolecule = ccpnChain.molecule

  if ccpnMolecule.isFinalized:
    raise Exception("Chain {} can no longer be extended".format(parent))

  # get chem comp ID strings from residue name
  molType, ccpCode = DataMapper.pickChemCompId(project._residueName2chemCompIds,
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
