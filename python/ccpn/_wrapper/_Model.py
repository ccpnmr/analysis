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
from ccpn import AbstractWrapperObject
from ccpn import Project
from ccpn import StructureEnsemble
# from ccpncore.util import Pid
from ccpncore.api.ccp.molecule.MolStructure import Model as ApiModel
from ccpncore.util.Types import Sequence


class Model(AbstractWrapperObject):
  """ ccpn.Model - Structural Model, or one member of the structure ensemble."""
  
  #: Short class name, for PID.
  shortClassName = 'MD'

  # Attribute it necessary as subclasses must use superclass className
  className = 'Model'

  #: Name of plural link to instances of class
  _pluralLinkName = 'models'

  #: List of child classes.
  _childClasses = []

  # CCPN properties
  @property
  def _apiModel(self) -> ApiModel:
    """ API Model matching ccpn.Model"""
    return self._wrappedData

  @property
  def _key(self) -> str:
    """id string - ID number converted to string"""
    return str(self._wrappedData.serial)

  @property
  def serial(self) -> int:
    """ID number, key attribute for ccpn.Model"""
    return self._wrappedData.serial
    
  @property
  def _parent(self) -> StructureEnsemble:
    """ccpn.StructureEnsemble containing ccpn.Model."""
    return  self._project._data2Obj[self._wrappedData.structureEnsemble]
  
  restraintSet = _parent
  
  @property
  def name(self) -> str:
    """name of Restraint List"""
    return self._wrappedData.name

  @name.setter
  def name(self, value):
    """name of Model"""
    self._wrappedData.name = value

  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details
    
  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

  @property
  def coordinateData(self) -> numpy.ndarray:
    """ atomCount * 3 numpy array of coordinates.
    """
    data = self.structureEnsemble.coordinateData
    return data[self._wrappedData.index]

  @coordinateData.setter
  def coordinateData(self, value):
    data = self.structureEnsemble.coordinateData
    data[self._wrappedData.index] = value

  @property
  def occupancyData(self) -> numpy.ndarray:
    """ atomCount length numpy array of occupancies.
    """
    data = self.structureEnsemble.occupancyData
    return data[self._wrappedData.index]

  @occupancyData.setter
  def occupancyData(self, value):
    data = self.structureEnsemble.occupancyData
    data[self._wrappedData.index] = value

  @property
  def bFactorData(self) -> numpy.ndarray:
    """ atomCount length numpy array of B factors.
    """
    data = self.structureEnsemble.bFactorData
    return data[self._wrappedData.index]

  @bFactorData.setter
  def bFactorData(self, value):
    data = self.structureEnsemble.bFactorData
    data[self._wrappedData.index] = value

  @property
  def atomNameData(self) -> numpy.ndarray:
    """atomCount length numpy array of model-specific atom names."""
    raise NotImplementedError("atomNameData not implemented yet")

  @atomNameData.setter
  def atomNameData(self, value):
    raise NotImplementedError("atomNameData not implemented yet")

  @classmethod
  def _getAllWrappedData(cls, parent: StructureEnsemble)-> list:
    """get wrappedData - all Model children of parent StructureEnsemble"""
    return parent._wrappedData.sortedModels()


def _newModel(self:StructureEnsemble, name:str=None, comment:str=None,
              coordinateData:numpy.ndarray=None,
              bFactorData:Sequence[float]=None,
              occupancyData:Sequence[float]=None) -> Model:
  """Create new Model"""

  structureEnaemble = self._wrappedData
  newApiModel = structureEnaemble.newModel(name=name, details=comment)
  if coordinateData:
    newApiModel.setSubmatrixData('coordinates', coordinateData.flat)
  if occupancyData:
    newApiModel.setSubmatrixData('occupancies', occupancyData)
  if bFactorData:
    newApiModel.setSubmatrixData('bFactors', bFactorData)
  # remove cached matrices, which are now out of date:
  for tag in ('_coordinateData', '_occupancyData', '_bFactorData'):
    if hasattr(self, tag):
      delattr(self, tag)
  #
  return self._data2Obj.get(newApiModel)


# Connections to parents:
StructureEnsemble._childClasses.append(Model)
StructureEnsemble.newModel = _newModel
del _newModel

# NBNB TBD add New function

# Notifiers:
className = ApiModel._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':Model}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete'),
  ('_finaliseUnDelete', {}, className, 'undelete')
  )
)
