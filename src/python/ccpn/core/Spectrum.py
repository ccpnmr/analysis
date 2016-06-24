"""Spectrum  class. Gives spectrum values, including per-dimension values as tuples.
Values that are not defined for a given dimension (e.g. sampled dimensions) are given as None.
Reference-related values apply only to the first Reference given (which is sufficient for
all common cases).
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

import numpy
import operator
import collections
from typing import Sequence, Tuple, Optional
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
from ccpnmodel.ccpncore.api.ccp.general import DataLocation
from ccpn.util import Pid

from ccpnmodel.ccpncore.lib.Io import Formats

# MagnetisationTransferTuple
MagnetisationTransferTuple = collections.namedtuple('MagnetisationTransferTuple',
  ['dimension1', 'dimension2', 'transferType', 'isIndirect']
)

class Spectrum(AbstractWrapperObject):
  """NMR spectrum."""

  #: Short class name, for PID.
  shortClassName = 'SP'
  # Attribute it necessary as subclasses must use superclass className
  className = 'Spectrum'

  _parentClass = Project

  #: Name of plural link to instances of class
  _pluralLinkName = 'spectra'

  #: List of child classes.
  _childClasses = []

  # Qualified name of matching API class
  _apiClassQualifiedName = Nmr.DataSource._metaclass.qualifiedName()

  def __init__(self, project:Project, wrappedData:Nmr.ShiftList):

    self._intensities = None
    self._positions = None

    super().__init__(project, wrappedData)

  # CCPN properties
  @property
  def _apiDataSource(self) -> Nmr.DataSource:
    """ CCPN DataSource matching Spectrum"""
    return self._wrappedData


  @property
  def _key(self) -> str:
    """name, regularised as used for id"""
    return self._wrappedData.name.translate(Pid.remapSeparators)


  @property
  def name(self) -> str:
    """short form of name, used for id"""

    return self._wrappedData.name

  @property
  def _parent(self) -> Project:
    """Parent (containing) object."""
    return self._project

  # Attributes of DataSource and Experiment:

  @property
  def dimensionCount(self) -> int:
    """Number of dimensions in spectrum"""
    return self._wrappedData.numDim

  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details

  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

  @property
  def positiveContourCount(self) -> int:
    """number of positive contours to draw"""
    return self._wrappedData.positiveContourCount

  @positiveContourCount.setter
  def positiveContourCount(self, value):
    self._wrappedData.positiveContourCount  = value

  @property
  def positiveContourBase(self) -> float:
    """base level of positive contours"""
    return self._wrappedData.positiveContourBase

  @positiveContourBase.setter
  def positiveContourBase(self, value):
    self._wrappedData.positiveContourBase  = value

  @property
  def positiveContourFactor(self) -> float:
    """level multiplier for positive contours"""
    return self._wrappedData.positiveContourFactor

  @positiveContourFactor.setter
  def positiveContourFactor(self, value):
    self._wrappedData.positiveContourFactor  = value

  @property
  def positiveContourColour(self) -> str:
    """colour of positive contours"""
    return self._wrappedData.positiveContourColour

  @positiveContourColour.setter
  def positiveContourColour(self, value):
    self._wrappedData.positiveContourColour  = value

  @property
  def negativeContourCount(self) -> int:
    """number of negative contours to draw"""
    return self._wrappedData.negativeContourCount

  @negativeContourCount.setter
  def negativeContourCount(self, value):
    self._wrappedData.negativeContourCount  = value

  @property
  def negativeContourBase(self) -> float:
    """base level of negative contours"""
    return self._wrappedData.negativeContourBase

  @negativeContourBase.setter
  def negativeContourBase(self, value):
    self._wrappedData.negativeContourBase  = value

  @property
  def negativeContourFactor(self) -> float:
    """level multiplier for negative contours"""
    return self._wrappedData.negativeContourFactor

  @negativeContourFactor.setter
  def negativeContourFactor(self, value):
    self._wrappedData.negativeContourFactor  = value

  @property
  def negativeContourColour(self) -> str:
    """colour of negative contours"""
    return self._wrappedData.negativeContourColour

  @negativeContourColour.setter
  def negativeContourColour(self, value):
    self._wrappedData.negativeContourColour  = value

  @property
  def sliceColour(self) -> str:
    """colour of 1D slices"""
    return self._wrappedData.sliceColour

  @sliceColour.setter
  def sliceColour(self, value):
    self._wrappedData.sliceColour  = value

  @property
  def scale(self) -> float:
    """Scaling factor for intensities and volumes.
    Intensities and volumes should be *multiplied* by scale before comparison."""
    return self._wrappedData.scale

  @scale.setter
  def scale(self, value:float):
    self._wrappedData.scale = value

  @property
  def spinningRate(self) -> float:
    """NMR tube spinning rate (in Hz)."""
    return self._wrappedData.experiment.spinningRate

  @spinningRate.setter
  def spinningRate(self, value:float):
    self._wrappedData.experiment.spinningRate = value

  # @property
  # def chemicalShiftList(self) -> ChemicalShiftList:
  #   """ChemicalShiftList associated with Spectrum."""
  #   return self._project._data2Obj.get(self._wrappedData.experiment.shiftList)
  #
  # @chemicalShiftList.setter
  # def chemicalShiftList(self, value:ChemicalShiftList):
  #
  #   value = self.getByPid(value) if isinstance(value, str) else value
  #   self._wrappedData.experiment.shiftList = value._wrappedData

  @property
  def experimentType(self) -> str:
    """Systematic experiment type descriptor (CCPN system)."""
    refExperiment = self._wrappedData.experiment.refExperiment
    if refExperiment is None:
      return None
    else:
      return refExperiment.name

  @experimentType.setter
  def experimentType(self, value:str):
    for nmrExpPrototype in self._wrappedData.root.sortedNmrExpPrototypes():
      for refExperiment in nmrExpPrototype.sortedRefExperiments():
        if value == refExperiment.name:
          # refExperiment matches name string - set it
          self._wrappedData.experiment.refExperiment = refExperiment
          return
    # nothing found - error:
    raise ValueError("No reference experiment matches name '%s'" % value)

  @property
  def experimentName(self) -> str:
    """Common experiment type descriptor (May not be unique)."""
    refExperiment = self._wrappedData.experiment.refExperiment
    if refExperiment is None:
      return None
    else:
      return refExperiment.synonym

  @property
  def filePath(self) -> str:
    """Absolute path to NMR data file."""
    xx = self._wrappedData.dataStore
    if xx:
      return xx.fullPath
    else:
      return None

  @filePath.setter
  def filePath(self, value:str):

    apiDataStore = self._wrappedData.dataStore
    if apiDataStore is None:
      raise ValueError("Spectrum is not stored, cannot change file path")

    elif not value:
      raise ValueError("Spectrum file path cannot be set to None")

    else:
      dataUrl = self._project._wrappedData.root.fetchDataUrl(value)
      apiDataStore.repointToDataUrl(dataUrl)
      apiDataStore.path = value[len(dataUrl.url.path)+1:]

      # # NBNB TBD this is silly - no reuse of DataUrls.
      # dirName, fileName = os.path.split(Path.normalisePath(value, makeAbsolute=True))
      # apiDataLocationStore = apiDataStore.dataLocationStore
      # dataUrl = apiDataLocationStore.newDataUrl(url=Url(path=dirName))
      # apiDataStore.dataUrl = dataUrl
      # apiDataStore.path = fileName

  @property
  def headerSize(self) -> int:
    """File header size in bytes."""
    xx = self._wrappedData.dataStore
    if xx:
      return xx.headerSize
    else:
      return None
  # NBNB TBD Should this be made modifiable? Would be a bit of work ...

  @property
  def numberType(self) -> str:
    """Data type of numbers stored in data matrix ('int' or 'float')."""
    xx = self._wrappedData.dataStore
    if xx:
      return xx.numberType
    else:
      return None
  # NBNB TBD Should this be made modifiable? Would be a bit of work ...

  @property
  def complexStoredBy(self) -> str:
    """Hypercomplex numbers are stored by ('timepoint', 'quadrant', or 'dimension')."""
    xx = self._wrappedData.dataStore
    if xx:
      return xx.complexStoredBy
    else:
      return None
  # NBNB TBD Should this be made modifiable? Would be a bit of work ...

  # Attributes belonging to AbstractDataDim

  def _setStdDataDimValue(self, attributeName, value:Sequence):
    """Set value for non-Sampled DataDims only"""
    apiDataSource = self._wrappedData
    if len(value) == apiDataSource.numDim:
      for ii,dataDim in enumerate(apiDataSource.sortedDataDims()):
        if dataDim.className != 'SampledDataDim':
          setattr(dataDim, attributeName, value[ii])
        elif value[ii] is not None:
          raise ValueError("Attempt to set value for invalid attribute %s in dimension %s: %s" %
                           (attributeName, ii+1, value))
    else:
      raise ValueError("Value must have length %s, was %s" % (apiDataSource.numDim, value))

  @property
  def pointCounts(self) -> Tuple[int, ...]:
    """Number active of points per dimension

    NB for FidDataDims more points than these may be stored (see totalPointCount)."""
    result = []
    for dataDim in self._wrappedData.sortedDataDims():
      if hasattr(dataDim, 'numPointsValid'):
        result.append(dataDim.numPointsValid)
      else:
        result.append(dataDim.numPoints)
    return tuple(result)

  @pointCounts.setter
  def pointCounts(self, value:Sequence):
    apiDataSource = self._wrappedData
    if len(value) == apiDataSource.numDim:
      for ii,dataDim in enumerate(apiDataSource.sortedDataDims()):
        if hasattr(dataDim, 'numPointsValid'):
          dataDim.numPointsValid = value[ii]
        else:
          dataDim.numPoints = value[ii]
    else:
      raise ValueError("pointCount value must have length %s, was %s" %
                       (apiDataSource.numDim, value))

  @property
  def totalPointCounts(self) -> Tuple[int, ...]:
    """Total number of points per dimension

    NB for FidDataDims and SampledDataDims these are the stored points,
    for FreqDataDims these are the points after transformation before cutting down."""
    result = []
    for dataDim in self._wrappedData.sortedDataDims():
      if hasattr(dataDim, 'numPointsOrig'):
        result.append(dataDim.numPointsOrig)
      else:
        result.append(dataDim.numPoints)
    return tuple(result)

  @totalPointCounts.setter
  def totalPointCounts(self, value:Sequence):
    apiDataSource = self._wrappedData
    if len(value) == apiDataSource.numDim:
      for ii,dataDim in enumerate(apiDataSource.sortedDataDims()):
        if hasattr(dataDim, 'numPointsOrig'):
          dataDim.numPointsOrig = value[ii]
        else:
          dataDim.numPoints = value[ii]
    else:
      raise ValueError("totalPointCount value must have length %s, was %s" %
                       (apiDataSource.numDim, value))

  @property
  def pointOffsets(self) -> Tuple[int, ...]:
    """index of first active point relative to total points, per dimension"""
    return tuple(x.pointOffset if x.className != 'SampledDataDim' else None
             for x in self._wrappedData.sortedDataDims())

  @pointOffsets.setter
  def pointOffsets(self, value:Sequence):
    self._setStdDataDimValue('pointOffset', value)

  @property
  def isComplex(self) -> Tuple[bool, ...]:
    """Is dimension complex? -  per dimension"""
    return tuple(x.isComplex for x in self._wrappedData.sortedDataDims())

  @isComplex.setter
  def isComplex(self, value:Sequence):
    apiDataSource = self._wrappedData
    if len(value) == apiDataSource.numDim:
      for ii,dataDim in enumerate(apiDataSource.sortedDataDims()):
        dataDim.isComplex = value[ii]
    else:
      raise ValueError("Value must have length %s, was %s" % (apiDataSource.numDim, value))

  @property
  def dimensionTypes(self) -> Tuple[str, ...]:
    """dimension types ('Fid' / 'Frequency' / 'Sampled'),  per dimension"""
    ll = [x.className[:-7] for x in self._wrappedData.sortedDataDims()]
    return tuple('Frequency' if x == 'Freq' else x for x in ll)

  @property
  def spectralWidthsHz(self) -> Tuple[Optional[float], ...]:
    """spectral width (in Hz) before dividing by spectrometer frequency, per dimension"""
    return tuple(x.spectralWidth if hasattr(x, 'spectralWidth') else None
                 for x in self._wrappedData.sortedDataDims())

  @spectralWidthsHz.setter
  def spectralWidthsHz(self, value:Sequence):
    apiDataSource = self._wrappedData
    attributeName = 'spectralWidth'
    if len(value) == apiDataSource.numDim:
      for ii,dataDim in enumerate(apiDataSource.sortedDataDims()):
        val = value[ii]
        if hasattr(dataDim, attributeName):
          if not val:
            raise ValueError("Attempt to set %s to %s in dimension %s: %s"
                           % (attributeName, val, ii+1, value))
          else:
            # We assume that the number of points is constant, so setting SW changes valuePerPoint
            swold = getattr(dataDim, attributeName)
            dataDim.valuePerPoint *= (val/swold)
        elif val is not None:
          raise ValueError("Attempt to set %s in sampled dimension %s: %s"
                           % (attributeName, ii+1, value))
    else:
      raise ValueError("SpectralWidth value must have length %s, was %s" %
                       (apiDataSource.numDim, value))


  @property
  def phases0(self) -> tuple:
    """zero order phase correction (or None), per dimension. Always None for sampled dimensions."""
    return tuple(x.phase0 if x.className != 'SampledDataDim' else None
                 for x in self._wrappedData.sortedDataDims())

  @phases0.setter
  def phases0(self, value:Sequence):
    self._setStdDataDimValue('phase0', value)

  @property
  def phases1(self) -> Tuple[Optional[float], ...]:
    """first order phase correction (or None) per dimension. Always None for sampled dimensions."""
    return tuple(x.phase1 if x.className != 'SampledDataDim' else None
                 for x in self._wrappedData.sortedDataDims())

  @phases1.setter
  def phases1(self, value:Sequence):
    self._setStdDataDimValue('phase1', value)

  @property
  def windowFunctions(self) -> Tuple[Optional[str], ...]:
    """Window function name (or None) per dimension - e.g. 'EM', 'GM', 'SINE', 'QSINE', ....
    Always None for sampled dimensions."""
    return tuple(x.windowFunction if x.className != 'SampledDataDim' else None
                 for x in self._wrappedData.sortedDataDims())

  @windowFunctions.setter
  def windowFunctions(self, value:Sequence):
    self._setStdDataDimValue('windowFunction', value)

  @property
  def lorentzianBroadenings(self) -> Tuple[Optional[float], ...]:
    """Lorenzian broadening in Hz per dimension. Always None for sampled dimensions."""
    return tuple(x.lorentzianBroadening if x.className != 'SampledDataDim' else None
                 for x in self._wrappedData.sortedDataDims())

  @lorentzianBroadenings.setter
  def lorentzianBroadenings(self, value:Sequence):
    self._setStdDataDimValue('lorentzianBroadening', value)

  @property
  def gaussianBroadenings(self) -> Tuple[Optional[float], ...]:
    """Gaussian broadening per dimension. Always None for sampled dimensions."""
    return tuple(x.gaussianBroadening if x.className != 'SampledDataDim' else None
                 for x in self._wrappedData.sortedDataDims())

  @gaussianBroadenings.setter
  def gaussianBroadenings(self, value:Sequence):
    self._setStdDataDimValue('gaussianBroadening', value)

  @property
  def sineWindowShifts(self) -> Tuple[Optional[float], ...]:
    """Shift of sine/sine-square window function in degrees. Always None for sampled dimensions."""
    return tuple(x.sineWindowShift if x.className != 'SampledDataDim' else None
                 for x in self._wrappedData.sortedDataDims())

  @sineWindowShifts.setter
  def sineWindowShifts(self, value:Sequence):
    self._setStdDataDimValue('sineWindowShift', value)

  # Attributes belonging to ExpDimRef and DataDimRef

  def _mainExpDimRefs(self) -> list:
    """Get main API ExpDimRef (serial=1) for each dimension"""

    result = []
    for ii,dataDim in enumerate(self._wrappedData.sortedDataDims()):
      # NB MUST loop over dataDims, in case of projection spectra
      result.append(dataDim.expDim.findFirstExpDimRef(serial=1))
    #
    return tuple(result)


  def _setExpDimRefAttribute(self, attributeName:str, value:Sequence, mandatory:bool=True):
    """Set main ExpDimRef attribute (serial=1) for each dimension"""
    apiDataSource = self._wrappedData
    if len(value) == apiDataSource.numDim:
      for ii,dataDim in enumerate(self._wrappedData.sortedDataDims()):
        # NB MUST loop over dataDims, in case of projection spectra
        expDimRef = dataDim.expDim.findFirstExpDimRef(serial=1)
        val = value[ii]
        if expDimRef is None and val is not None:
          raise ValueError("Attempt to set attribute %s in dimension %s to %s - must be None" %
                             (attributeName, ii+1, val))
        elif val is None and mandatory:
          raise ValueError(
            "Attempt to set mandatory attribute %s to None in dimension %s: %s" %
            (attributeName, ii+1, val))
        else:
          setattr(expDimRef, attributeName, val)

  @property
  def spectrometerFrequencies(self) -> Tuple[Optional[float], ...]:
    """Tuple of spectrometer frequency for main dimensions reference """
    return tuple(x and x.sf for x in self._mainExpDimRefs())

  @spectrometerFrequencies.setter
  def spectrometerFrequencies(self, value):
    self._setExpDimRefAttribute('sf', value)

  @property
  def measurementTypes(self) -> Tuple[Optional[str], ...]:
    """Type of value being measured, per dimension.

    In normal cases the measurementType will be 'Shift', but other values might be
    'MQSHift' (for multiple quantum axes), JCoupling (for J-resolved experiments),
    'T1', 'T2', ..."""
    return tuple(x and x.measurementType for x in self._mainExpDimRefs())

  @measurementTypes.setter
  def measurementTypes(self, value):
    self._setExpDimRefAttribute('measurementType', value)
  #
  # @property
  # def maxAliasedFrequencies(self) -> Tuple[Optional[float], ...]:
  #   """maximum possible peak frequency (in ppm) for main dimensions reference, per dimension """
  #   return tuple(x and x.maxAliasedFreq for x in self._mainExpDimRefs())
  #
  # @maxAliasedFrequencies.setter
  # def maxAliasedFrequencies(self, value):
  #   self._setExpDimRefAttribute('maxAliasedFreq', value, mandatory=False)
  #
  # @property
  # def minAliasedFrequencies(self) -> Tuple[Optional[float], ...]:
  #   """minimum possible peak frequency (in ppm) for main dimensions reference, per dimension"""
  #   return tuple(x and x.minAliasedFreq for x in self._mainExpDimRefs())
  #
  # @minAliasedFrequencies.setter
  # def minAliasedFrequencies(self, value):
  #   self._setExpDimRefAttribute('minAliasedFreq', value, mandatory=False)


  @property
  def isotopeCodes(self) -> Tuple[Optional[str], ...]:
    """isotopeCode of isotope being measured, per dimension - None if no unique code"""
    result = []
    for dataDim in self._wrappedData.sortedDataDims():
      expDimRef = dataDim.expDim.findFirstExpDimRef(serial=1)
      if expDimRef is None:
        result.append(None)
      else:
        isotopeCodes = expDimRef.isotopeCodes
        if len(isotopeCodes) == 1:
          result.append(isotopeCodes[0])
        else:
          result.append(None)
    #
    return tuple(result)

  @isotopeCodes.setter
  def isotopeCodes(self, value:Sequence):
    apiDataSource = self._wrappedData
    if len(value) == apiDataSource.numDim:
      for ii,dataDim in enumerate(apiDataSource.sortedDataDims()):
        expDimRef = dataDim.expDim.findFirstExpDimRef(serial=1)
        val = value[ii]
        if expDimRef is None:
          if val is not None:
            raise ValueError("Cannot set isotopeCode %s in dimension %s" % (val, ii+1))
        elif val is None:
          expDimRef.isotopeCodes = ()
        else:
          expDimRef.isotopeCodes = (val,)
    else:
      raise ValueError("Value must have length %s, was %s" % (apiDataSource.numDim, value))

  @property
  def foldingModes(self) -> Tuple[Optional[str], ...]:
    """folding mode (values: 'circular', 'mirror', None), per dimension"""
    dd = {True:'mirror', False:'circular', None:None}
    return tuple(dd[x and x.isFolded] for x in self._mainExpDimRefs())

  @foldingModes.setter
  def foldingModes(self, value):
    dd = {'circular':False, 'mirror':True, None:None}
    self._setExpDimRefAttribute('isFolded', [dd[x] for x in value])

  @property
  def axisCodes(self) -> Tuple[Optional[str], ...]:
    """axisCode, per dimension - None if no main ExpDimRef
    """

    # See if axis codes are set
    for expDim in self._wrappedData.experiment.expDims:
      if expDim.findFirstExpDimRef(axisCode=None) is not None:
        self._wrappedData.experiment.resetAxisCodes()
        break

    result = []
    for dataDim in self._wrappedData.sortedDataDims():
      expDimRef = dataDim.expDim.findFirstExpDimRef(serial=1)
      if expDimRef is None:
        result.append(None)
      else:
        axisCode = expDimRef.axisCode
        result.append(axisCode)

    return tuple(result)

  @axisCodes.setter
  def axisCodes(self, value):
    self._setExpDimRefAttribute('axisCode', value, mandatory=False)

  @property
  def acquisitionAxisCode(self) -> Optional[str]:
    """Axis code of acquisition axis - None if not known"""
    for dataDim in self._wrappedData.sortedDataDims():
      expDim = dataDim.expDim
      if expDim.isAcquisition:
        expDimRef = expDim.findFirstExpDimRef(serial=1)
        axisCode = expDimRef.axisCode
        if axisCode is None:
          self._wrappedData.experiment.resetAxisCodes()
          axisCode = expDimRef.axisCode
        return axisCode
    #
    return None

  @acquisitionAxisCode.setter
  def acquisitionAxisCode(self, value):
    if value is None:
      index = None
    else:
      index = self.axisCodes.index(value)

    for ii,dataDim in enumerate( self._wrappedData.sortedDataDims()):
      dataDim.expDim.isAcquisition = (ii == index)

  @property
  def axisUnits(self) -> Tuple[Optional[str], ...]:
    """Main axis unit (most commonly 'ppm'), per dimension - None if no unique code

    Uses first Shift-type ExpDimRef if there is more than one, otherwise first ExpDimRef"""
    return tuple(x and x.unit for x in self._mainExpDimRefs())

  @axisUnits.setter
  def axisUnits(self, value):
    self._setExpDimRefAttribute('unit', value, mandatory=False)

  # Attributes belonging to DataDimRef

  def _mainDataDimRefs(self) -> list:
    """ List of DataDimRef matching main ExpDimRef for each dimension"""
    result = []
    expDimRefs = self._mainExpDimRefs()
    for ii, dataDim in enumerate(self._wrappedData.sortedDataDims()):
      if hasattr(dataDim, 'dataDimRefs'):
        result.append(dataDim.findFirstDataDimRef(expDimRef=expDimRefs[ii]))
      else:
        result.append(None)
    #
    return result

  def _setDataDimRefAttribute(self, attributeName:str, value:Sequence, mandatory:bool=True):
    """Set main DataDimRef attribute for each dimension
    - uses first ExpDimRef with serial=1"""
    apiDataSource = self._wrappedData
    if len(value) == apiDataSource.numDim:
      expDimRefs = self._mainExpDimRefs()
      for ii, dataDim in  enumerate(self._wrappedData.sortedDataDims()):
        if hasattr(dataDim, 'dataDimRefs'):
          dataDimRef = dataDim.findFirstDataDimRef(expDimRef=expDimRefs[ii])
        else:
          dataDimRef = None

        if dataDimRef is None:
          if value[ii] is not None:
            raise ValueError("Cannot set value for attribute %s in dimension %s: %s" %
                             (attributeName, ii+1, value))
        elif value is None and mandatory:
          raise ValueError(
            "Attempt to set value to None for mandatory attribute %s in dimension %s: %s" %
            (attributeName, ii+1, value))
        else:
          setattr(dataDimRef, attributeName, value[ii])
    else:
      raise ValueError("Value must have length %s, was %s" % (apiDataSource.numDim, value))

  @property
  def referencePoints(self) -> Tuple[Optional[float], ...]:
    """point used for axis (chemical shift) referencing, per dimension."""
    return tuple(x and x.refPoint for x in self._mainDataDimRefs())

  @referencePoints.setter
  def referencePoints(self, value):
    self._setDataDimRefAttribute('refPoint', value)

  @property
  def referenceValues(self) -> Tuple[Optional[float], ...]:
    """value used for axis (chemical shift) referencing, per dimension."""
    return tuple(x and x.refValue for x in self._mainDataDimRefs())

  @referenceValues.setter
  def referenceValues(self, value):
    self._setDataDimRefAttribute('refValue', value)

  @property
  def assignmentTolerances(self) -> Tuple[Optional[float], ...]:
    """Assignment tolerance in axis unit (ppm), per dimension."""
    return tuple(x and x.assignmentTolerance for x in self._mainDataDimRefs())

  @assignmentTolerances.setter
  def assignmentTolerances(self, value):
    self._setDataDimRefAttribute('assignmentTolerance', value)

  @property
  def spectralWidths(self) -> Tuple[Optional[float], ...]:
    """spectral width after processing in axis unit (ppm), per dimension """
    return tuple(x and x.spectralWidth for x in self._mainDataDimRefs())

  @spectralWidths.setter
  def spectralWidths(self, value):
    oldValues = self.spectralWidths
    for ii,dataDimRef in enumerate(self._mainDataDimRefs()):
      if dataDimRef is not None:
        oldsw = oldValues[ii]
        sw = value[ii]
        localValuePerPoint = dataDimRef.localValuePerPoint
        if localValuePerPoint:
          dataDimRef.localValuePerPoint = localValuePerPoint*sw/oldsw
        else:
          dataDimRef.dataDim.valuePerPoint *= (sw/oldsw)

  @property
  def aliasingLimits(self) -> Tuple[Tuple[Optional[float], Optional[float]], ...]:
    """\- (*(float,float)*)\*dimensionCount

    tuple of tuples of (lowerAliasingLimit, higherAliasingLimit) for spectrum """
    result = [(x and x.minAliasedFreq, x and x.maxAliasedFreq) for x in self._mainExpDimRefs()]

    if any(None in tt for tt in result):
      # Some values not set, or missing. Try to get them as spectrum limits
      for ii,dataDimRef in enumerate(self._mainDataDimRefs()):
        if None in result[ii] and dataDimRef is not None:
          dataDim = dataDimRef.dataDim
          ff = dataDimRef.pointToValue
          point1 = 1 - dataDim.pointOffset
          result[ii] = tuple(sorted((ff(point1), ff(point1 + dataDim.numPointsOrig))))
    #
    return tuple(result)

  @aliasingLimits.setter
  def aliasingLimits(self, value):
    if len(value) != self.dimensionCount:
      raise ValueError("length of aliasingLimits must match spectrum dimension, was %s" % value)

    expDimRefs = self._mainExpDimRefs()
    for ii,tt in enumerate(value):
      expDimRef = expDimRefs[ii]
      if expDimRef:
        if len(tt) != 2:
          raise ValueError("Aliasing limits must have two value (min,max), was %s" % tt)
        expDimRef.minAliasedFreq = tt[0]
        expDimRef.maxAliasedFreq = tt[1]


  @property
  def spectrumLimits(self) -> Tuple[Tuple[Optional[float], Optional[float]], ...]:
    """\- (*(float,float)*)\*dimensionCount

    tuple of tuples of (lowerLimit, higherLimit) for spectrum """
    ll = []
    for ii,ddr in enumerate(self._mainDataDimRefs()):
      if ddr is None:
        ll.append((None,None))
      else:
        ll.append(tuple(sorted((ddr.pointToValue(1), ddr.pointToValue(ddr.dataDim.numPoints+1)))))
    return tuple(ll)

  @property
  def magnetisationTransfers(self) -> Tuple[MagnetisationTransferTuple, ...]:
    """tuple of MagnetisationTransferTuple describing magnetisation transfer between
    the spectrum dimensions.

    MagnetisationTransferTuple is a namedtuple with the fields
    ['dimension1', 'dimension2', 'transferType', 'isIndirect'] of types [int, int, str, bool]
    The dimensions are dimension numbers (one-origin]
    transfertype is one of (in order of increasing priority):
    'onebond', 'Jcoupling', 'Jmultibond', 'relayed', 'relayed-alternate', 'through-space'
    isIndirect is used where there is more than one successive transfer step;
     it is combined with the highest-priority transferType in the transfer path.
    """

    result = []
    apiRefExperiment = self._wrappedData.experiment.refExperiment
    if apiRefExperiment:
      magnetisationTransferDict = apiRefExperiment.magnetisationTransferDict()
      refExpDimRefs = [x if x is None else x.refExpDimRef for x in self._mainExpDimRefs()]
      for ii, rxdr in enumerate(refExpDimRefs):
        dim1 = ii + 1
        if rxdr is not None:
          for jj in range(dim1, len(refExpDimRefs)):
            rxdr2 = refExpDimRefs[jj]
            if rxdr2 is not None:
              tt = magnetisationTransferDict.get(frozenset((rxdr, rxdr2)))
              if tt:
                result.append(MagnetisationTransferTuple(dim1, jj+1, tt[0], tt[1]))
    #
    return tuple(result)

  @property
  def intensities(self) -> numpy.ndarray:
    """ spectral intensities as NumPy array for 1D spectra """
    
    if self.dimensionCount != 1:
      raise Exception('Currently this method only works for 1D spectra')
      
    if self._intensities is None:
      self._intensities = self.scale * self.getSliceData()
      
    return self._intensities

  @property
  def positions(self) -> numpy.ndarray:
    """ spectral region in ppm as NumPy array for 1D spectra """
    
    if self.dimensionCount != 1:
      raise Exception('Currently this method only works for 1D spectra')
      
    if self._positions is None:
      spectrumLimits = self.spectrumLimits[0]
      pointCount = self.pointCounts[0]
      # WARNING: below assumes that spectrumLimits are "backwards" (as is true for ppm)
      scale = (spectrumLimits[0] - spectrumLimits[1]) / pointCount
      self._positions = spectrumLimits[1] + scale*numpy.arange(pointCount, dtype='float32')
      
    return self._positions

  # Implementation functions

  def rename(self, value:str):
    """Rename Spectrum, changing Id and Pid"""
    if value:
      self._startFunctionCommandBlock('rename', value)
      try:
        self._wrappedData.name = value
      finally:
        self._project._appBase._endCommandBlock()
    else:
      raise ValueError("Spectrum name must be set")

  @classmethod
  def _getAllWrappedData(cls, parent: Project)-> list:
    """get wrappedData (Nmr.DataSources) for all Spectrum children of parent Project"""
    return sorted((x for y in parent._wrappedData.sortedExperiments()
                   for x in y.sortedDataSources()), key=operator.attrgetter('name'))

  # Library functions

  def resetAssignmentTolerances(self):
    """Reset assignment tolerances to default values"""

    self._startFunctionCommandBlock('resetAssignmentTolerances')
    try:
      tolerances = [[]] * self.dimensionCount
      for ii, isotopeCode in enumerate(self.isotopeCodes):
        if isotopeCode == '1H':
          tolerance = max([0.02, self.spectralWidths[ii]/self.pointCounts[ii]])
          tolerances[ii] = tolerance
        elif isotopeCode == '13C' or isotopeCode == '15N':
          tolerance = max([0.2, self.spectralWidths[ii]/self.pointCounts[ii]])
          tolerances[ii] = tolerance
        else:
          tolerance = max([0.2, self.spectralWidths[ii]/self.pointCounts[ii]])
          tolerances[ii] = tolerance

      self.assignmentTolerances = tolerances
    finally:
      self._project._appBase._endCommandBlock()

  def getPlaneData(self, position:Sequence=None, xDim:int=1, yDim:int=2):

    return self._apiDataSource.getPlaneData(position=position, xDim=xDim, yDim=yDim)

  def getSliceData(self, position:Sequence=None, sliceDim:int=1):

    return self._apiDataSource.getSliceData(position=position, sliceDim=sliceDim)

  def automaticIntegration(self, spectralData):

    return self._apiDataSource.automaticIntegration(spectralData)

  def estimateNoise(self):
    return self._apiDataSource.estimateNoise()

  def projectedPlaneData(self, xDim:int=1, yDim:int=2, method:str='max'):
    return self._apiDataSource.projectedPlaneData(xDim, yDim, method)

  def projectedToFile(self, path:str, xDim:int=1, yDim:int=2, method:str='max', format:str=Formats.NMRPIPE):
    return self._apiDataSource.projectedToFile(path, xDim, yDim, method, format)


def _newSpectrum(self:Project, name:str) -> Spectrum:
  """Creation of new ccpn.Spectrum NOT IMPLEMENTED.
  Use ccpn.Project.loadData or ccpn.Project.createDummySpectrum instead"""

  raise NotImplementedError("Not implemented. Use loadSpectrum function instead")

def _createDummySpectrum(self:Project, axisCodes:Sequence[str], name=None) -> Spectrum:
  """Make dummy spectrum from isotopeCodes list - without data and with default parameters """

  if name:
    if Pid.altCharacter in name:
      raise ValueError("Character %s not allowed in ccpn.Spectrum.name" % Pid.altCharacter)
    values = {'name':name}
  else:
    values = {}

  self._startFunctionCommandBlock('_createDummySpectrum', axisCodes, values=values,
                                  parName='newSpectrum')
  try:
    result = self._data2Obj[self._wrappedData.createDummySpectrum(axisCodes, name=name)]
  finally:
    self._project._appBase._endCommandBlock()
  return result

def _spectrumMakeFirstPeakList(project:Project, dataSource:Nmr.DataSource):
  """Add PeakList if none is present. For notifiers."""
  if not dataSource.findFirstPeakList(dataType='Peak'):
    dataSource.newPeakList()
Project._setupApiNotifier(_spectrumMakeFirstPeakList, Nmr.DataSource, 'postInit')
del _spectrumMakeFirstPeakList

# Connections to parents:

Project.newSpectrum = _newSpectrum
del _newSpectrum
Project.createDummySpectrum = _createDummySpectrum
del _createDummySpectrum

# Additional Notifiers:
Project._apiNotifiers.extend(
  (
    ('_finaliseApiRename', {}, Nmr.DataSource._metaclass.qualifiedName(), 'setName'),
    ('_notifyRelatedApiObject', {'pathToObject':'dataSources', 'action':'change'},
     Nmr.Experiment._metaclass.qualifiedName(), ''),
    ('_notifyRelatedApiObject', {'pathToObject':'dataSource', 'action':'change'},
     Nmr.AbstractDataDim._metaclass.qualifiedName(), ''),
    ('_notifyRelatedApiObject', {'pathToObject':'dataDim.dataSource', 'action':'change'},
     Nmr.DataDimRef._metaclass.qualifiedName(), ''),
    ('_notifyRelatedApiObject', {'pathToObject':'experiment.dataSources', 'action':'change'},
     Nmr.ExpDim._metaclass.qualifiedName(), ''),
    ('_notifyRelatedApiObject', {'pathToObject':'expDim.experiment.dataSources', 'action':'change'},
     Nmr.ExpDimRef._metaclass.qualifiedName(), ''),
    ('_notifyRelatedApiObject', {'pathToObject':'nmrDataSources', 'action':'change'},
     DataLocation.AbstractDataStore._metaclass.qualifiedName(), ''),
  )
)