"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
from ccpncore.util import pid as Pid

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

from collections.abc import Sequence

from ccpn._wrapper._AbstractWrapperObject import AbstractWrapperObject
from ccpn._wrapper._Project import Project
from ccpn._wrapper._Spectrum import Spectrum
from ccpncore.api.ccp.nmr.Nmr import DataDimRef as ApiDataDimRef


class SpectrumReference(AbstractWrapperObject):
  """ADVANCED. NMR spectrum reference. Can only exist for Fourier transformed dimensions
  (CCPN: FreqDataDim). Required for experiments with assignable splittings (e.g. J-coupling, RDC),
  reduced-dimensionality, more than one nucleus per axis, o
  r multi-atom parameters (J-dimensions, MQ dimensions)."""

  #: Short class name, for PID.
  shortClassName = 'SR'

  # Type of dimension. Always 'Freq' for frequency (Fourier transformed) dimension
  dimensionType = 'Freq'

  #: Name of plural link to instances of class
  _pluralLinkName = 'spectrumReferences'

  #: List of child classes.
  _childClasses = []

  # CCPN properties
  @property
  def apiSpectrumReference(self) -> ApiDataDimRef:
    """ CCPN DataSource matching Spectrum"""
    return self._wrappedData


  @property
  def _key(self) -> str:
    """object identifier, used for id"""

    dataDimRef = self._wrappedData
    result = '%s%s%s' % (dataDimRef.dataDim.dim, Pid.IDSEP, dataDimRef.expDimRef.serial)

    return result

  @property
  def _parent(self) -> Spectrum:
    """Parent (containing) object."""
    return self._project._data2Obj[self._wrappedData.dataDim.dataSource]

  # Attributes of DataSource and Experiment:

  @property
  def dimension(self) -> int:
    """dimension number"""
    return self._wrappedData.dataDim.dim

  @property
  def referenceSerial(self) -> int:
    """Spectrum reference serial number"""
    return self._wrappedData.expDimRef.serial


  # Attributes belonging to ExpDimRef and DataDimRef

  @property
  def spectrometerFrequency(self) -> float:
    """Absolute frequency at carrier (or at splitting 0.0). In MHz or dimensionless."""
    return self._wrappedData.expDimRef.sf

  @spectrometerFrequency.setter
  def spectrometerFrequency(self, value):
     self._wrappedData.expDimRef.sf = value

  @property
  def measurementType(self) -> str:
    """Type of NMR measurement referred to by this reference. Legal values are:
    'Shift','ShiftAnisotropy','JCoupling','Rdc','TROESY','DipolarCoupling',
    'MQShift','T1','T2','T1rho','T1zz'"""
    return self._wrappedData.expDimRef.measurementType

  @measurementType.setter
  def measurementType(self, value):
     self._wrappedData.expDimRef.measurementType = value

  @property
  def maxAliasedFrequency(self) -> float:
    """maximum possible peak frequency (in ppm) for this reference """
    return self._wrappedData.expDimRef.maxAliasedFreq

  @maxAliasedFrequency.setter
  def maxAliasedFrequency(self, value):
     self._wrappedData.expDimRef.maxAliasedFreq = value

  @property
  def minAliasedFrequency(self) -> float:
    """minimum possible peak frequency (in ppm) for this reference """
    return self._wrappedData.expDimRef.minAliasedFreq

  @minAliasedFrequency.setter
  def minAliasedFrequency(self, value):
     self._wrappedData.expDimRef.minAliasedFreq = value


  @property
  def isotopeCodes(self) -> tuple:
    """Type: (*str,*)\*, *settable*

    Isotope identification strings for isotopes.
    NB there can be several isotopes for e.g. J-coupling or multiple quantum coherence."""

    return self._wrappedData.expDimRef.isotopeCodes

  @isotopeCodes.setter
  def isotopeCodes(self, value:Sequence):
      self._wrappedData.expDimRef.isotopeCodes = value

  @property
  def foldingMode(self) -> bool:
    """folding mode matching reference (values: 'aliased', 'folded', None)"""
    dd = {True:'folded', False:'aliased', None:None}
    return dd[self._wrappedData.expDimRef.isFolded]

  @foldingMode.setter
  def foldingMode(self, value):
    dd = {'aliased':False, 'folded':True, None:None}
    self._wrappedData.expDimRef.isFolded = dd[value]

  @property
  def axisCode(self) -> str:
    """Type: (*str,*)\*dimensionCount, *settable*

    Main ExpDimRef axisCode for each dimension - None if no main ExpDimRef

    If the axisCode is set, each will be unique and match the RefExpDimRef.axisCode
    If it is not set, axisCodes may not be unique. They will be the element symbol
    for shift and TROESY, comma-separated element symbols for MQ magnetisation,
    'missing' for a shift, TROESY or MQ without isotope indication, the measurement
    or 'unknown' otherwise.

    TBD codes match AtomSite.name, but NBNB NmrExpPrototypes must be updated to match system"""
    return self._wrappedData.expDimRef.useAxisCode

  @axisCode.setter
  def axisCode(self, value:str):
      self._wrappedData.expDimRef.axisCode = value

  @property
  def axisUnit(self) -> str:
    """unit for transformed data using thei reference (most commonly 'ppm')"""
    return self._wrappedData.expDimRef.unit

  @axisUnit.setter
  def axisUnit(self, value:str):
      self._wrappedData.expDimRef.unit = value

  # Attributes belonging to DataDimRef


  @property
  def referencePoint(self) -> float:
    """point used for axis (chemical shift) referencing."""
    return self._wrappedData.refPoint

  @referencePoint.setter
  def referencePoint(self, value):
    self._wrappedData.refPoint = value

  @property
  def referenceValue(self) -> float:
    """value used for axis (chemical shift) referencing."""
    return self._wrappedData.refValue

  @referenceValue.setter
  def referenceValue(self, value:float):
    self._wrappedData.refValue = value

  @property
  def spectralWidth(self) -> float:
    """spectral width after processing (generally in ppm) """
    return self._wrappedData.spectralWidth

  @spectralWidth.setter
  def spectralWidth(self, value:float):
    if not value:
      raise ValueError("Attempt to set spectralWidth to %s"
                     % value)
    else:
      # We assume that the number of points is constant, so setting SW changes valuePerPoint
      dataDimRef = self._wrappedData
      swold = dataDimRef.spectralWidth
      if dataDimRef.localValuePerPoint:
        dataDimRef.localValuePerPoint *= (value/swold)
      else:
        dataDimRef.dataDim.valuePerPoint *= (value/swold)

  # Implementation functions

  @classmethod
  def _getAllWrappedData(cls, parent: Spectrum)-> list:
    """get wrappedData (Nmr.DataDimRefs) for all Spectrum children of parent Spectrum"""
    result = []
    for ddim in parent._wrappedData.sortedDataDims():
      if hasattr(ddim, 'dataDimRef'):
        result.extend(ddim.sortedDataDimRefs())
    #
    return tuple(result)


def newSpectrumReference(parent:Spectrum, dimension:int, spectrometerFrequency:float,
                       isotopeCodes:Sequence, axisCode:str=None, measurementType:str='Shift',
                       maxAliasedFrequency:float=None, minAliasedFrequency:float=None,
                       foldingMode:str=None, axisUnit:str=None, referencePoint:float=0.0,
                       referenceValue:float=0.0) -> SpectrumReference:
  """Create new child Atom"""
  dataSource = parent._wrappedData
  dataDim = dataSource.findFirstDataDim(dim=dimension)
  if dataDim is None:
    raise ValueError("Cannot create SpectrumReference for non-existent dimension: %s" % dimension)

  expDimRef = dataDim.expDim.newExpDimRef(sf=spectrometerFrequency, isotopeCodes=isotopeCodes,
                                          measurementType=measurementType,
                                          isFolded=(foldingMode!='folded'), name=axisCode,
                                          unit=axisUnit, minAliasedFreq=minAliasedFrequency,
                                          maxAliasedFreq=maxAliasedFrequency,)

  dataDimRef = dataDim.newDataDimRef(expDimRef=expDimRef, refPoint=referencePoint,
                                     refValue=referenceValue)

  return parent.project._data2Obj[dataDimRef]


# Connections to parents:

Spectrum._childClasses.append(SpectrumReference)

Spectrum.newSpectrumReference = newSpectrumReference

# Notifiers:
className = ApiDataDimRef._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':SpectrumReference}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)