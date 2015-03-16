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

from ccpncore.lib.molecule.DataMapper import DataMapper
from ccpncore.util import pid
from ccpn._wrapper._AbstractWrapperObject import AbstractWrapperObject
from ccpn._wrapper._Project import Project
from ccpn._wrapper._Chain import Chain
from ccpncore.api.ccp.molecule.MolSystem import Residue as ApiResidue


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
  def apiResidue(self) -> ApiResidue:
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
    return pid.makeId(self.sequenceCode, self.name)
    
  @property
  def _parent(self) -> Chain:
    """Chain containing residue."""
    return self._project._data2Obj[self._wrappedData.chain]
  
  chain = _parent
    
  @property
  def name(self) -> str:
    """Residue type name string (e.g. 'ALA')"""
    return self._wrappedData.code3Letter or ''

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
  @classmethod
  def _getAllWrappedData(cls, parent: Chain)-> list:
    """get wrappedData (MolSystem.Residues) for all Residue children of parent Chain"""
    return parent._wrappedData.sortedResidues()

    
# Connections to parents:
Chain._childClasses.append(Residue)

# Chain.newResidue = newResidue

# Notifiers:
className = ApiResidue._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':Residue}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
