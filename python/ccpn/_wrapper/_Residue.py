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
from ccpncore.util import Pid
from ccpncore.util import Common as commonUtil
from ccpn import AbstractWrapperObject
from ccpn import Project
from ccpn import Chain
from ccpncore.api.ccp.molecule.MolSystem import Residue as ApiResidue


class Residue(AbstractWrapperObject):
  """Molecular Residue."""
  
  #: Short class name, for PID.
  shortClassName = 'MR'
  # Attribute it necessary as subclasses must use superclass className
  className = 'Residue'

  #: Name of plural link to instances of class
  _pluralLinkName = 'residues'
  
  #: List of child classes.
  _childClasses = []
  

  # CCPN properties  
  @property
  def _apiResidue(self) -> ApiResidue:
    """ API residue matching Residue"""
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
  def _key(self) -> str:
    """Residue ID. Identical to sequenceCode.residueType. Characters translated for pid"""
    return Pid.createId(self.sequenceCode, self.residueType)
    
  @property
  def _parent(self) -> Chain:
    """Chain containing residue."""
    return self._project._data2Obj[self._wrappedData.chain]
  
  chain = _parent
    
  @property
  def residueType(self) -> str:
    """Residue type name string (e.g. 'ALA')"""
    return self._wrappedData.code3Letter or ''

  @property
  def shortName(self) -> str:
    return self._wrappedData.chemCompVar.chemComp.code1Letter or '?'

  # @name.setter
  # def name(self, value:str):
  #   self._wrappedData.code3Letter = value
  #   molType, ccpCode = self._project._residueName2chemCompId.get(value, (None,None))
  #   # NBNB TBD reorganise model so that code3Letter is used throughout, and change this
  #   self._wrappedData.molType = molType
  #   self._wrappedData.ccpCode = ccpCode

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

  # CCPN functions
  # def linkToResidue(self, targetResidue, fromLinkCode, toLinkCode=None):
  #   """Link residue to targetResidue, using linkCodes given
  #   NBNB TBD currently function only set Molecule-level links and assumes that
  #   ChemCompVar fits. Expand later"""
  #   linkCodeMap = {'prev':'next', 'next':'prev'}
  #   if toLinkCode is None:
  #     toLinkCode = linkCodeMap.get(fromLinkCode)
  #   if toLinkCode is None:
  #     raise ValueError("toLinkCode missing for link type: %s" % fromLinkCode)
  #
  #   fromMolResidue = self._wrappedData.molResidue
  #   toMolResidue = targetResidue._wrappedData.molResidue
  #   linkEnds = (fromMolResidue.findFirstMolResLinkEnd(linkCode=fromLinkCode),
  #               toMolResidue.findFirstMolResLinkEnd(linkCode=toLinkCode))
  #   fromLinkCode.molecule.newMolResLink(molResLinkEnds=linkEnds)

  # Implementation functions

  def rename(self, value:str):
    """Change object id, modifying entire project to maintain consistency.
    NBNB TBD to be implemented"""
    raise NotImplementedError("Chain rename not implemented yet")

  @classmethod
  def _getAllWrappedData(cls, parent: Chain)-> list:
    """get wrappedData (MolSystem.Residues) for all Residue children of parent Chain"""
    func = commonUtil.numericStringSortKey
    ll = [(func(x.seqCode), x.seqInsertCode, x) for x in parent._apiChain.residues]
    return [tt[-1] for tt in sorted(ll)]

def getter(self:Residue) -> Residue:
  apiResidue = self._wrappedData
  nextApiMolResidue = apiResidue.molResidue.nextMolResidue
  if nextApiMolResidue is None:
    return None
  else:
    return self._project._data2Obj.get(
      apiResidue.chain.findFirstResidue(seqId=nextApiMolResidue.serial))
Residue.nextResidue = property(getter, None, None, "Next sequentially connected Residue")

def getter(self:Residue) -> Residue:
  apiResidue = self._wrappedData
  previousApiMolResidue = apiResidue.molResidue.previousMolResidue
  if previousApiMolResidue is None:
    return None
  else:
    return self._project._data2Obj.get(
      apiResidue.chain.findFirstResidue(seqId=previousApiMolResidue.serial))
Residue.previousResidue = property(getter, None, None, "Previous sequentially connected Residue")

del getter
    
# Connections to parents:
Chain._childClasses.append(Residue)

# No 'new' function - chains are made elsewhere

# Notifiers:
className = ApiResidue._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':Residue}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete'),
    ('_finaliseUnDelete', {}, className, 'undelete'),
  )
)
