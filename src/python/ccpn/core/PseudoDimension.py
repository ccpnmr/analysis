"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

from typing import Sequence, Tuple
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.Spectrum import Spectrum
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import SampledDataDim as ApiSampledDataDim
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import ExpDimRef as ApiExpDimRef


class PseudoDimension(AbstractWrapperObject):
  """ADVANCED. PsudoDimension - Sampled dimension with non-gridded values"""

  #: Short class name, for PID.
  shortClassName = 'SD'
  # Attribute it necessary as subclasses must use superclass className
  className = 'PseudoDimension'

  _parentClass = Spectrum

  # Type of dimension. Always 'Freq' for frequency (Fourier transformed) dimension
  dimensionType = 'Sampled'

  #: Name of plural link to instances of class
  _pluralLinkName = 'pseudoDimensions'

  #: List of child classes.
  _childClasses = []

  # Qualified name of matching API class
  _apiClassQualifiedName = ApiSampledDataDim._metaclass.qualifiedName()

  # CCPN properties
  @property
  def _apiSampledDataDim(self) -> ApiSampledDataDim:
    """ CCPN DataSource matching Spectrum"""
    return self._wrappedData

  @property
  def _key(self) -> str:
    """object identifier, used for id"""

    return str(self._wrappedData.dim)

  @property
  def _parent(self) -> Spectrum:
    """Spectrum containing PseudoDimension."""
    return self._project._data2Obj[self._wrappedData.dataSource]

  spectrum = _parent

  @property
  def dimension(self) -> int:
    """dimension number"""
    return self._wrappedData.dim

  @property
  def pointCount(self) -> int:
    """dimension number"""
    return self._wrappedData.numPoints

  @property
  def axisCode(self) -> str:
    """PseudoDimension axisCode """

    expDimRef =  self._wrappedData.expDim.findFirstExpDimRef(serial=1)
    return expDimRef and expDimRef.axisCode

  @axisCode.setter
  def axisCode(self, value:str):
    expDimRef =  self._wrappedData.expDim.findFirstExpDimRef(serial=1)
    if expDimRef is not None:
      expDimRef.axisCode = value

  @property
  def axisParameter(self) -> str:
    """Name of the condition or parameter that is varied along the axis.
    Use 'sample' if samples are different for each point on the dimension"""
    return  self._wrappedData.conditionVaried

  @axisParameter.setter
  def axisParameter(self, value:str):
    self._wrappedData.conditionVaried = value

  @property
  def axisUnit(self) -> str:
    """unit for transformed data using the reference (most commonly 'ppm')"""
    expDimRef =  self._wrappedData.expDim.findFirstExpDimRef(serial=1)
    if expDimRef is not None:
      return expDimRef.unit

  @axisUnit.setter
  def axisUnit(self, value:str):
    expDimRef =  self._wrappedData.expDim.findFirstExpDimRef(serial=1)
    if expDimRef is not None:
      expDimRef.unit = value

  @property
  def pointValues(self) -> Tuple[float, ...]:
    """point values for PseudoDimension)."""
    return tuple(self._wrappedData.pointValues)

  @pointValues.setter
  def pointValues(self, value:Sequence) -> tuple:
    self._wrappedData.pointValues = value

  @property
  def pointErrors(self) -> Tuple[float, ...]:
    """point errors for PseudoDimension)."""
    return tuple(self._wrappedData.pointErrors)

  @pointErrors.setter
  def pointErrors(self, value:Sequence) -> tuple:
    self._wrappedData.pointErrors = value

  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details

  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

  # Implementation functions

  @classmethod
  def _getAllWrappedData(cls, parent: Spectrum)-> list:
    """get wrappedData (Nmr.SampledDataDims) for all DataDim children of parent Spectrum"""
    result = []
    for ddim in parent._wrappedData.sortedDataDims():
      if ddim.className == 'SampledDataDim':
        result.append(ddim)
    #
    return result

# No 'new' function - PseudoDimensions are made on spectrum load

# Connections to parents:

# Notifiers:
def _expDimRefHasChanged(project:Project, apiExpDimRef:ApiExpDimRef):
  """Refresh PseudoDimension when ExpDimRef has changed"""
  for dataDim in apiExpDimRef.expDim.dataDims:
    if isinstance(dataDim, ApiSampledDataDim):
      project._modifiedApiObject(dataDim)
Project._setupApiNotifier(_expDimRefHasChanged, ApiExpDimRef, '')
del _expDimRefHasChanged