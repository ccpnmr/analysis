"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
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

import numpy
from ccpncore.util.Types import Tuple
from ccpncore.util import Pid
from ccpn import AbstractWrapperObject
from ccpn import Project
from ccpncore.api.ccp.molecule.MolStructure import StructureEnsemble as ApiStructureEnsemble


class StructureEnsemble(AbstractWrapperObject):
  """Ensemble of coordinate structures."""
  
  #: Short class name, for PID.
  shortClassName = 'SE'
  # Attribute is necessary as subclasses must use superclass className
  className = 'StructureEnsemble'

  #: Name of plural link to instances of class
  _pluralLinkName = 'structureEnsembles'
  
  #: List of child classes.
  _childClasses = []
  

  # CCPN properties  
  @property
  def _apiStructureEnsemble(self) -> ApiStructureEnsemble:
    """ CCPN api StructureEnsemble matching ccpn.StructureEnsemble"""
    return self._wrappedData
    
  @property
  def _key(self) -> str:
    """id string - ID number converted to string"""
    return str(self._wrappedData.ensembleId)

  @property
  def ensembleId(self) -> int:
    """ID number, key attribute for ccpn.StructureEnsemble"""
    return self._wrappedData.ensembleId

  @property
  def _parent(self) -> Project:
    """Parent (containing) object."""
    return self._project

  @property
  def atomIds(self) -> Tuple[str, ...]:
    """Tuple of atom id ('chainCode.sequenceCode.atomName' for atoms making up structure ensemble
    The atom IDs and their order is the same for all ccpn.Models in the ensemble."""
    IDSEP = Pid.IDSEP
    result = [''.join((x.residue.chain.code,  IDSEP, str(x.residue.seqCode),
                       x.residue.seqInsertCode.strip(), IDSEP, x.name))
              for x in self._wrappedData.orderedAtoms]
    #
    return result

  @property
  def coordinateData(self) -> numpy.ndarray:
    """modelCount * atomCount * 3 numpy array of coordinates.
    NB the coordinateData array is a cached copy.
    It can be  modified, but modifications will be kept in cache till the attribute is
    set or the project is saved."""
    if hasattr(self, '_coordinateData'):
      return self._coordinateData
    else:
      apiDataMatrix = self._apiStructureEnsemble.findFirstDataMatrix(name='coordinates')
      if apiDataMatrix is None:
        return None
      data = apiDataMatrix.data
      if not data:
        return None
      # We have the data. make cached copy, and return it
      shape = apiDataMatrix.shape
      result = self._coordinateData = numpy.reshape(data, shape)
      return result

  @property
  def occupancyData(self) -> numpy.ndarray:
    """modelCount * atomCount  numpy array of atom occupancies.
    NB the occupancyData array is a cached copy.
    It can be  modified, but modifications will be kept in cache till the attribute is
    set or the project is saved."""
    if hasattr(self, '_occupancyData'):
      return self._occupancyData
    else:
      apiDataMatrix = self._apiStructureEnsemble.findFirstDataMatrix(name='occupancies')
      if apiDataMatrix is None:
        return None
      data = apiDataMatrix.data
      if not data:
        return None
      # We have the data. make cached copy, and return it
      shape = apiDataMatrix.shape
      result = self._occupancyData = numpy.reshape(data, shape)
      return result

  @property
  def bFactorData(self) -> numpy.ndarray:
    """modelCount * atomCount  numpy array of atom B factors.
    NB the occupancyData array is a cached copy.
    It can be  modified, but modifications will be kept in cache till the attribute is
    set or the project is saved."""
    if hasattr(self, '_bFactorData'):
      return self._occupancyData
    else:
      apiDataMatrix = self._apiStructureEnsemble.findFirstDataMatrix(name='bFactors')
      if apiDataMatrix is None:
        return None
      data = apiDataMatrix.data
      if not data:
        return None
      # We have the data. make cached copy, and return it
      shape = apiDataMatrix.shape
      result = self._bFactorData = numpy.reshape(data, shape)
      return result


  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details
    
  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value


  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:Project)-> list:
    """get wrappedData for all NmrConstraintStores linked to NmrProject"""
    return parent._wrappedData.molSystem.sortedStructureEnsembles()

def newStructureEnsemble(self:Project, ensembleId:int, comment:str=None) -> StructureEnsemble:
  """Create new, empty ccpn.StructureEnsemble"""
  
  nmrProject = self._wrappedData
  newApiStructureEnsemble = nmrProject.root.newStructureEnsemble(molSystem=nmrProject.molSystem,
                                                         ensembleId=ensembleId, details=comment)
  return self._data2Obj.get(newApiStructureEnsemble)
    
    
# Connections to parents:
Project._childClasses.append(StructureEnsemble)
Project.newStructureEnsemble = newStructureEnsemble

# Notifiers:
className = ApiStructureEnsemble._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':StructureEnsemble}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete'),
    ('_finaliseUnDelete', {}, className, 'undelete'),
  )
)
