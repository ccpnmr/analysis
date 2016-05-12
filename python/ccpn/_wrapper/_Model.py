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
from ccpncore.api.ccp.molecule.MolStructure import Model as ApiModel
from typing import Sequence
from ccpncore.util import Common as commonUtil
from ccpn import AbstractWrapperObject
from ccpn import Project
from ccpn import StructureEnsemble
# from ccpncore.util import Pid


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

  # Qualified name of matching API class
  _apiClassQualifiedName = ApiModel._metaclass.qualifiedName()

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
    """ID number of Model, used in Pid and to identify the Model. """
    return self._wrappedData.serial
    
  @property
  def _parent(self) -> StructureEnsemble:
    """ccpn.StructureEnsemble containing ccpn.Model."""
    return  self._project._data2Obj[self._wrappedData.structureEnsemble]
  
  structureEnsemble = _parent
  
  @property
  def title(self) -> str:
    """title of Model"""
    return self._wrappedData.name

  @title.setter
  def title(self, value):
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
  """Create new Model

  CoordinateData can be a numpy.ndarray of the right shape,
  or any nested list or tuple representation that contains the right number of elements"""

  structureEnsemble = self._wrappedData

  if coordinateData:
    atomCount = structureEnsemble.nAtoms
    # Sanity check - filter out (most?) wrongly shaped arrays
    if hasattr(coordinateData, 'shape'):
      if coordinateData.shape != (atomCount,3):
        raise ValueError("numpy.ndarray input not of correct shape (%s,3)" % atomCount)
    else:
      if len(coordinateData) not in (atomCount, 3*atomCount):
        raise ValueError("nested sequence input does not match %s*3 array" % atomCount)

    coordinateData = commonUtil.flattenIfNumpy(coordinateData, shape=(atomCount,3))

  newApiModel = structureEnsemble.newModel(name=name, details=comment)
  if coordinateData:
    newApiModel.setSubmatrixData('coordinates', coordinateData)
  if occupancyData:
    newApiModel.setSubmatrixData('occupancies', occupancyData)
  if bFactorData:
    newApiModel.setSubmatrixData('bFactors', bFactorData)
  # remove cached matrices, which are now out of date:
  for tag in ('_coordinateData', '_occupancyData', '_bFactorData'):
    if hasattr(self, tag):
      delattr(self, tag)
  #
  return self._project._data2Obj.get(newApiModel)


# Connections to parents:
StructureEnsemble._childClasses.append(Model)
StructureEnsemble.newModel = _newModel
del _newModel

# NBNB TBD add New function

# Notifiers:

# Must be done with API notifiers as it rewuires a predelete notifier.
def _flushCachedData(project:Project, apiModel:ApiModel):
  """Flush cached data to ensure up-to-date data are saved"""
  structureEnsemble = project._data2Obj[apiModel].structureEnsemble
  structureEnsemble._flushCachedData()
Project._apiNotifiers.append(
  ('_flushCachedData', {},  ApiModel._metaclass.qualifiedName(), 'preDelete'),
)