__author__ = 'rhf22'

from collections.abc import Sequence

from ccpn._AbstractWrapperClass import AbstractWrapperClass
from ccpn._Project import Project
from ccpncore.api.ccp.nmr.Nmr import DataSource as Ccpn_DataSource


class Spectrum(AbstractWrapperClass):
  """NMR spectrum."""

  # Short class name, for PID.
  shortClassName = 'SP'

  # Name of plural link to instances of class
  _pluralLinkName = 'spectra'

  # List of child classes.
  _childClasses = []

  # CCPN properties
  @property
  def ccpnSpectrum(self) -> Ccpn_DataSource:
    """ CCPN DataSource matching Spectrum"""
    return self._wrappedData


  @property
  def id(self) -> str:
    """short form of name, used for id"""

    dataSource = self._wrappedData
    ccpnExperiment = dataSource.experiment
    result = ccpnExperiment.name
    if dataSource is not ccpnExperiment.sortedDataSources()[0]:
      result = '%s_%s' % (result, dataSource.serial)

    return result

  name = id

  @property
  def _parent(self) -> Project:
    """Parent (containing) object."""
    return self._project

  # Attributes of DataSource and Experiment:

  @property
  def dimensionCount(self) -> str:
    """short form of name, used for id"""
    return self._wrappedData.numDim

  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details

  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

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

  @property
  def chemicalShiftList(self):
    """ChemicalShiftList associated with Spectrum."""
    return self._project._data2Obj.get(self._wrappedData.experiment.shiftList)

  @chemicalShiftList.setter
  def chemicalShiftList(self, value):
    self._wrappedData.experiment.shiftList = value._wrappedData

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
      for refExperiment in nmrExpPrototype.sortedrefExperiments():
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
  # NBNB TBD Should this be made modifiable? Would be a bit of work ...

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
    """Type of number stored ('int' or 'float')."""
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

  def _setDataDimValue(self, attributeName, value:Sequence):
    dataSource = self._wrappedData
    if len(value) == dataSource.numDim:
      for ii,dataDim in enumerate(dataSource.sortedDataDims()):
        if hasattr (dataDim, attributeName):
          setattr(dataDim, attributeName, value[ii])
        elif value[ii] is not None:
          raise ValueError("Attempt to set value for invalid attribute %s in dimension %s: %s" %
                           (attributeName, ii+1, value))
    else:
      raise ValueError("Value must have length %s, was %s" % (dataSource.numDim, value))

  @property
  def pointCount(self) -> tuple:
    """Tuple with number active of points per dimension.
    NB for FidDataDims more points than these may be stored (see totalPointCount)."""
    result = []
    for dataDim in self._wrappedData.sortedDataDims():
      if hasattr(dataDim, 'numPointsValid'):
        result.append(dataDim.numPointsValid)
      else:
        result.append(dataDim.numPoints)
    return tuple(result)

  @pointCount.setter
  def pointCount(self, value:Sequence):
    dataSource = self._wrappedData
    if len(value) == dataSource.numDim:
      for ii,dataDim in enumerate(dataSource.sortedDataDims()):
        if hasattr(dataDim, 'numPointsValid'):
          dataDim.numPointsValid = value[ii]
        else:
          dataDim.numPoints = value[ii]
    else:
      raise ValueError("pointCount value must have length %s, was %s" %
                       (dataSource.numDim, value))

  @property
  def totalPointCount(self) -> tuple:
    """Tuple with total number of points per dimension.
    NB for FidDataDims and SampledDataDims these are the stored points,
    for FreqDataDims these are the points after transformation before cutting down."""
    result = []
    for dataDim in self._wrappedData.sortedDataDims():
      if hasattr(dataDim, 'numPointsOrig'):
        result.append(dataDim.numPointsOrig)
      else:
        result.append(dataDim.numPoints)
    return tuple(result)

  @totalPointCount.setter
  def totalPointCount(self, value:Sequence):
    dataSource = self._wrappedData
    if len(value) == dataSource.numDim:
      for ii,dataDim in enumerate(dataSource.sortedDataDims()):
        if hasattr(dataDim, 'numPointsOrig'):
          dataDim.numPointsOrig = value[ii]
        else:
          dataDim.numPoints = value[ii]
    else:
      raise ValueError("totalPointCount value must have length %s, was %s" %
                       (dataSource.numDim, value))

  @property
  def pointOffset(self) -> tuple:
    """Tuple with point offset dimension - index of first active point relative to total points."""
    result = []
    for dataDim in self._wrappedData.sortedDataDims():
      if hasattr(dataDim, 'pointOffset'):
        result.append(dataDim.pointOffset)
      else:
        result.append(0)
    return tuple(result)

  @pointOffset.setter
  def pointOffset(self, value:Sequence):
    dataSource = self._wrappedData
    attributeName = 'pointOffset'
    if len(value) == dataSource.numDim:
      for ii,dataDim in enumerate(dataSource.sortedDataDims()):
        if hasattr (dataDim, attributeName):
          setattr(dataDim, attributeName, value[ii])
        elif value[ii]:
          raise ValueError("Attempt to set value for %s in dimension %s: %s" %
                           (attributeName, ii+1, value))
    else:
      raise ValueError("Value must have length %s, was %s" % (dataSource.numDim, value))

  @property
  def isComplex(self) -> tuple:
    """Tuple with isComplex Boolean per dimension."""
    return tuple(x.isComplex for x in self._wrappedData.sortedDataDims())

  @isComplex.setter
  def isComplex(self, value:Sequence):
    self._setDataDimValue('isComplex', value)

  @property
  def dimensionType(self) -> tuple:
    """Tuple with dimension types ('Fid' / 'Freq' / 'Sampled') per dimension."""
    return tuple(x.className[:-7] for x in self._wrappedData.sortedDataDims())

  @property
  def spectralWidthHz(self) -> tuple:
    """Tuple with spectral width before adjustment (generally in Hz) per dimension"""
    return tuple(x.spectralWidth for x in self._wrappedData.sortedDataDims()
                 if hasattr(x, 'spectralWidth'))

  @spectralWidthHz.setter
  def spectralWidthHz(self, value:Sequence):
    dataSource = self._wrappedData
    attributeName = 'spectralWidth'
    if len(value) == dataSource.numDim:
      for ii,dataDim in enumerate(dataSource.sortedDataDims()):
        val = value[ii]
        if hasattr(dataDim, attributeName):
          if val is None:
            raise ValueError("Attempt to set %s to None in dimension %s: %s"
                           % (attributeName, ii+1, value))
          else:
            # We assume that the number of points is constant, so setting SW changes valuePerPoint
            setattr(dataDim, attributeName, val/dataDim.numPoints)
        elif val is not None:
          raise ValueError("Attempt to set %s in sampled dimension %s: %s"
                           % (attributeName, ii+1, value))
    else:
      raise ValueError("SpectralWidth value must have length %s, was %s" %
                       (dataSource.numDim, value))


  @property
  def phase0(self) -> tuple:
    """Tuple with zero order phase correction (or None) per dimension
    (Always None for sampled dimensions)."""
    return tuple(x.phase0 for x in self._wrappedData.sortedDataDims()
                 if hasattr(x, 'phase0'))

  @phase0.setter
  def phase0(self, value:Sequence):
    self._setDataDimValue('phase0', value)

  @property
  def phase1(self) -> tuple:
    """Tuple with first order phase correction (or None) per dimension
    (Always None for sampled dimensions)."""
    return tuple(x.phase1 for x in self._wrappedData.sortedDataDims()
                 if hasattr(x, 'phase1'))

  @phase1.setter
  def phase1(self, value:Sequence):
    self._setDataDimValue('phase1', value)


  @property
  def sampledValues(self) -> tuple:
    """Tuple of lists of per-dimension sampled values (None except for Sampled dimensions"""
    return tuple(x.pointValues for x in self._wrappedData.sortedDataDims()
                 if hasattr(x, 'pointValues'))

  @sampledValues.setter
  def sampledValues(self, value:Sequence) -> tuple:
    self._setDataDimValue('pointValues', value)

  @property
  def sampledValueErrors(self) -> tuple:
    """Tuple of lists of per-dimension sampled value errors (None except for Sampled dimensions"""
    return tuple(x.pointErrors for x in self._wrappedData.sortedDataDims()
                 if hasattr(x, 'pointErrors'))

  @sampledValueErrors.setter
  def sampledValueErrors(self, value:Sequence) -> tuple:
    self._setDataDimValue('pointErrors', value)

  # Attributes belonging to ExpDimRef and DataDimRef

  def _mainExpDimRefs(self) -> list:
    """Get main ExpDimRef  for each dimension
    - uses first Shift-type ExpDimRef if there is more than one, otherwise first ExpDimRef"""
    result = []
    for expDim in self._wrappedData.experiment.sortedExpDims():
      expDimRefs = expDim.sortedExpDimRefs()
      if not expDimRefs:
        result.append(None)
      else:
        for expDimRef in expDimRefs:
          if expDimRef.measurementType == 'Shift':
            break
        else:
          expDimRef = expDimRefs[0]
        #
        result.append(expDimRef)
    #
        return result


  def _setExpDimRefAttribute(self, attributeName:str, value:Sequence, mandatory:bool=True):
    """Set main ExpDimRef attribute for each dimension
    - uses first Shift-type ExpDimRef if there is more than one, otherwise first ExpDimRef"""
    dataSource = self._wrappedData
    if len(value) == dataSource.numDim:
      for ii,expDim in enumerate(self._wrappedData.experiment.sortedExpDims()):
        expDimRefs = expDim.sortedExpDimRefs()
        if not expDimRefs:
          if value[ii] is not None:
            raise ValueError("Attempt to set value for invalid attribute %s in dimension %s: %s" %
                             (attributeName, ii+1, value))
        else:
          for expDimRef in expDimRefs:
            if expDimRef.measurementType == 'Shift':
              break
          else:
            expDimRef = expDimRefs[0]
          #
          if value is None and mandatory:
            raise ValueError(
              "Attempt to set value to None for mandatory attribute %s in dimension %s: %s" %
              (attributeName, ii+1, value))
          else:
            setattr(expDimRef, attributeName, value[ii])
    else:
      raise ValueError("Value must have length %s, was %s" % (dataSource.numDim, value))

  @property
  def spectrometerFrequency(self) -> tuple:
    """Tuple of spectrometer frequency for main dimensions reference """
    return tuple(x and x.sf for x in self._mainExpDimRefs())

  @spectrometerFrequency.setter
  def spectrometerFrequency(self, value):
    self._setExpDimRefAttribute('sf', value)

  @property
  def measurementType(self) -> tuple:
    """Tuple of measurement type string for main dimensions reference """
    return tuple(x and x.measurementType for x in self._mainExpDimRefs())

  @measurementType.setter
  def measurementType(self, value):
    self._setExpDimRefAttribute('measurementType', value)

  @property
  def maxAliasedFrequency(self) -> tuple:
    """Tuple of maximum possible frequency (in ppm) for main dimensions reference """
    return tuple(x and x.maxAliasedFrequency for x in self._mainExpDimRefs())

  @maxAliasedFrequency.setter
  def maxAliasedFrequency(self, value):
    self._setExpDimRefAttribute('maxAliasedFrequency', value, mandatory=False)

  @property
  def minAliasedFrequency(self) -> tuple:
    """Tuple of minimum possible frequency (in ppm) for main dimensions reference """
    return tuple(x and x.minAliasedFrequency for x in self._mainExpDimRefs())

  @minAliasedFrequency.setter
  def minAliasedFrequency(self, value):
    self._setExpDimRefAttribute('minAliasedFrequency', value, mandatory=False)


  @property
  def isotopeCode(self) -> tuple:
    """Tuple of main ExpDimRef isotopeCode for each dimension - None if no unique code
    - uses first Shift-type ExpDimRef if there is more than one, otherwise first ExpDimRef"""
    result = []
    for expDim in self._wrappedData.experiment.sortedExpDims():
      expDimRefs = expDim.sortedExpDimRefs()
      if not expDimRefs:
        result.append(None)
      else:
        for expDimRef in expDimRefs:
          if expDimRef.measurementType == 'Shift':
            break
        else:
          expDimRef = expDimRefs[0]
        #
        isotopeCodes = expDimRef.isotopeCodes
        if len(isotopeCodes) == 1:
          result.append(isotopeCodes[0])
        else:
          result.append(None)
    #
          return tuple(result)

  @isotopeCode.setter
  def isotopeCode(self, value:Sequence):
    """Set main ExpDimRef isotopeCode for each dimension
    - uses first Shift-type ExpDimRef if there is more than one, otherwise first ExpDimRef"""
    dataSource = self._wrappedData
    if len(value) == dataSource.numDim:
      for ii,expDim in enumerate(self._wrappedData.experiment.sortedExpDims()):
        expDimRefs = expDim.sortedExpDimRefs()
        if not expDimRefs:
          if value[ii] is not None:
            raise ValueError("Cannot set isotopeCode in dimension %s: %s" %
                             (ii+1, value))
        else:
          for expDimRef in expDimRefs:
            if expDimRef.measurementType == 'Shift':
              break
          else:
            expDimRef = expDimRefs[0]
          #
          if value[ii] is None:
            val = ()
          else:
            val = (value[ii],)
          expDimRef.isotopeCodes = val
    else:
      raise ValueError("Value must have length %s, was %s" % (dataSource.numDim, value))

  @property
  def foldingMode(self) -> tuple:
    """Tuple of main ExpDimRef folding mode per dimension (values: 'aliased', 'folded', None)"""
    dd = {True:'folded', False:'aliased', None:None}
    return tuple(dd[x and x.isFolded] for x in self._mainExpDimRefs())

  @foldingMode.setter
  def foldingMode(self, value):
    dd = {'aliased':False, 'folded':True, None:None}
    self._setExpDimRefAttribute('isFolded', [dd[x] for x in value])

  @property
  def axisCode(self) -> tuple:
    """Tuple of main ExpDimRef axisCode for each dimension - None if no unique code.
    Uses first Shift-type ExpDimRef if there is more than one, otherwise first ExpDimRef
    Axis code is used to identify the axis, how axes are linked, and how they map to
    window axes, experiment templates etc. The following codes are accepted:

    - Nucleus names (H, C, N, P, F, D, Na, Ca, ...)

    - HX groups (Hn, Hc, Ch, Nh) showing carbon or nitrogen bound to protons

    - Protein-specific groups (HA, Ca, CO)

    - Double quantum  axes ( DQ(C,C), DQ(H,C), ...

    - Coupling constants (J, J(H,H), J(H,C), ...

    - measurement types (time, temp, pH, conc, pressure, field, offset, ...

    - Duplicate codes are distinguished by suffixes (H, H2, H3, ...) (NB there is no H1)
      E.g. Hc is bound to Ch, but not to Ch2

    TBD codes match AtomSite.name, but NBNB NmrExpPrototypes must be updated to match system"""
    return tuple(x and x.name for x in self._mainExpDimRefs())

  @axisCode.setter
  def axisCode(self, value):
    self._setExpDimRefAttribute('name', value, mandatory=False)

  @property
  def axisUnit(self) -> tuple:
    """Tuple of main ExpDimRef axis unit (most commonly 'ppm') for each dimension -
    None if no unique code
    Uses first Shift-type ExpDimRef if there is more than one, otherwise first ExpDimRef"""
    return tuple(x and x.unit for x in self._mainExpDimRefs())

  @axisUnit.setter
  def axisUnit(self, value):
    self._setExpDimRefAttribute('unit', value, mandatory=False)

  # Attributes belonging to DataDimRef

  def _mainDataDimRefs(self) -> list:
    """ List of DataDimRef matching main ExpDimRef for each dimension"""
    result = []
    expDimRefs = self._mainExpDimRefs()
    for ii, dataDim in self._wrappedData.sortedDataDims():
      if hasattr(dataDim, 'dataDimRefs'):
        result.append(dataDim.findFirstDataDimRef(expDimRef=expDimRefs[ii]))
      else:
        result.append(None)
    #
        return result

  def _setDataDimRefAttribute(self, attributeName:str, value:Sequence, mandatory:bool=True):
    """Set main DataDimRef attribute for each dimension
    - uses first Shift-type ExpDimRef if there is more than one, otherwise first ExpDimRef"""
    dataSource = self._wrappedData
    if len(value) == dataSource.numDim:
      expDimRefs = self._mainExpDimRefs()
      for ii, dataDim in self._wrappedData.sortedDataDims():
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
      raise ValueError("Value must have length %s, was %s" % (dataSource.numDim, value))

  @property
  def referencePoint(self) -> tuple:
    """Tuple of point used for axis (chemical shift) referencing per dimension"""
    return tuple(x and x.refPoint for x in self._mainDataDimRefs())

  @referencePoint.setter
  def referencePoint(self, value):
    self._setDataDimRefAttribute('refPoint', value)

  @property
  def referenceValue(self) -> tuple:
    """Tuple of value used for axis (chemical shift) referencing per dimension"""
    return tuple(x and x.refValue for x in self._mainDataDimRefs())

  @referenceValue.setter
  def referenceValue(self, value):
    self._setDataDimRefAttribute('refValue', value)

  @property
  def spectralWidth(self) -> tuple:
    """Tuple with spectral width after adjustment (generally in ppm) per dimension """
    return tuple(x and x.spectralWidth for x in self._mainDataDimRefs())

  # NBNB TBD Do we want this parameter settable? and if so with what behaviour?

  # Implementation functions

  @classmethod
  def _getAllWrappedData(cls, parent: Project)-> list:
    """get wrappedData (Nmr.DataSources) for all Spectrum children of parent Project"""
    return tuple(x for y in parent._wrappedData.sortedExperiments()
                 for x in y.sortedDataSources())


def newSpectrum(parent:Project, name:str) -> Spectrum:
  """Create new child Atom"""
  project = parent

  raise NotImplementedError("Creation of new Spectra not yet implemented")

  # NBNB TBD
  # requires changing of descriptor and chemCompVar,
  # interaction with structure ensembles, ...


# Connections to parents:

Project._childClasses.append(Spectrum)

Project.newSpectrum = newSpectrum

# Notifiers:
className = Ccpn_DataSource._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':Spectrum}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)