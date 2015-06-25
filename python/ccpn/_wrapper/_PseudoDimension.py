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

from collections.abc import Sequence
from ccpn import AbstractWrapperObject
from ccpn import Project
from ccpn import Spectrum
from ccpncore.api.ccp.nmr.Nmr import SampledDataDim as ApiSampledDataDim


class PseudoDimension(AbstractWrapperObject):
  """ADVANCED. PsudoDimension - Sampled dimension with non-gridded values"""

  #: Short class name, for PID.
  shortClassName = 'SD'

  # Type of dimension. Always 'Freq' for frequency (Fourier transformed) dimension
  dimensionType = 'Sampled'

  #: Name of plural link to instances of class
  _pluralLinkName = 'pseudoDimensions'

  #: List of child classes.
  _childClasses = []

  # CCPN properties
  @property
  def apiSampledDataDim(self) -> ApiSampledDataDim:
    """ CCPN DataSource matching Spectrum"""
    return self._wrappedData


  @property
  def _key(self) -> str:
    """object identifier, used for id"""

    dataDim = self._wrappedData
    result = str(dataDim.dim)

    return result

  @property
  def _parent(self) -> Spectrum:
    """Spectrum containing spectrumReference."""
    return self._project._data2Obj[self._wrappedData.dataDim.dataSource]

  spectrum = _parent

  @property
  def dimension(self) -> int:
    """dimension number"""
    return self._wrappedData.dataDim.dim

  @property
  def pointCount(self) -> int:
    """dimension number"""
    return self._wrappedData.numPoints

  @property
  def axisCode(self) -> str:
    """\- (*str,*), *settable*

    ExpDimRef axisCode """

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
    """unit for transformed data using thei reference (most commonly 'ppm')"""
    expDimRef =  self._wrappedData.expDim.findFirstExpDimRef(serial=1)
    if expDimRef is not None:
      return expDimRef.unit

  @axisUnit.setter
  def axisUnit(self, value:str):
    expDimRef =  self._wrappedData.expDim.findFirstExpDimRef(serial=1)
    if expDimRef is not None:
      expDimRef.unit = value

  @property
  def pointValues(self) -> tuple:
    """\- *((float)\*)*, *settable*
    point values for PseudoDimension)."""
    return tuple(self._wrappedData.pointValues)

  @pointValues.setter
  def pointValues(self, value:Sequence) -> tuple:
    self._wrappedData.pointValues = value

  @property
  def pointErrors(self) -> tuple:
    """\- *((float)\*)*, *settable*
    point errors for PseudoDimension)."""
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
        result.add(ddim)
    #
    return tuple(result)


# Connections to parents:

Spectrum._childClasses.append(PseudoDimension)

# Notifiers:
className = ApiSampledDataDim._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':PseudoDimension}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)