"""Spectrum  class. Gives spectrum values, including per-dimension values as tuples.
Values that are not defined for a given dimension (e.g. sampled dimensions) are given as None.
Reference-related values apply only to the first Reference given (which is sufficient for
all common cases).
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

import os

from ccpncore.util.typing import Sequence
from ccpn import AbstractWrapperObject
from ccpn import Project
from ccpn import Sample
from ccpn import ChemicalShiftList
from ccpncore.api.ccp.nmr.Nmr import DataSource as ApiDataSource
from ccpncore.api.memops.Implementation import Url
from ccpncore.util import Path
from ccpncore.util import Pid


class Spectrum(AbstractWrapperObject):
  """NMR spectrum."""

  #: Short class name, for PID.
  shortClassName = 'SP'
  # Attribute it necessary as subclasses must use superclass className
  className = 'Spectrum'

  #: Name of plural link to instances of class
  _pluralLinkName = 'spectra'

  #: List of child classes.
  _childClasses = []

  # CCPN properties
  @property
  def _apiDataSource(self) -> ApiDataSource:
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

  @property
  def chemicalShiftList(self) -> ChemicalShiftList:
    """ChemicalShiftList associated with Spectrum."""
    return self._project._data2Obj.get(self._wrappedData.experiment.shiftList)

  @chemicalShiftList.setter
  def chemicalShiftList(self, value:ChemicalShiftList):

    value = self.getByPid(value) if isinstance(value, str) else value
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
    #  NBNB TBD, the way of handling file paths, DataUrls, and stores ABSOLUTELY need improving

    apiDataStore = self._wrappedData.dataStore
    if apiDataStore is None:
      raise ValueError("Spectrum is not stored, cannot change file path")

    if not value:
      raise ValueError("Spectrum file path cannot be set to None")

    # NBNB TBD this is silly - no reuse of DataUrls.
    dirName, fileName = os.path.split(Path.normalisePath(value, makeAbsolute=True))
    apiDataLocationStore = apiDataStore.dataLocationStore
    dataUrl = apiDataLocationStore.newDataUrl(url=Url(path=dirName))
    apiDataStore.dataUrl = dataUrl
    apiDataStore.path = fileName

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
    apiDataSource = self._wrappedData
    if len(value) == apiDataSource.numDim:
      for ii,dataDim in enumerate(apiDataSource.sortedDataDims()):
        if hasattr (dataDim, attributeName):
          setattr(dataDim, attributeName, value[ii])
        elif value[ii] is not None:
          raise ValueError("Attempt to set value for invalid attribute %s in dimension %s: %s" %
                           (attributeName, ii+1, value))
    else:
      raise ValueError("Value must have length %s, was %s" % (apiDataSource.numDim, value))

  @property
  def pointCounts(self) -> tuple:
    """\- (*int,*)\*dimensionCount, *settable*

    Number active of points

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
  def totalPointCounts(self) -> tuple:
    """\- (*int,*)\*dimensionCount, *settable*

    Total number of points

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
  def pointOffsets(self) -> tuple:
    """\- (*int,*)\*dimensionCount, *settable*

     index of first active point relative to total points."""
    result = []
    for dataDim in self._wrappedData.sortedDataDims():
      if hasattr(dataDim, 'pointOffset'):
        result.append(dataDim.pointOffset)
      else:
        result.append(0)
    return tuple(result)

  @pointOffsets.setter
  def pointOffsets(self, value:Sequence):
    apiDataSource = self._wrappedData
    attributeName = 'pointOffset'
    if len(value) == apiDataSource.numDim:
      for ii,dataDim in enumerate(apiDataSource.sortedDataDims()):
        if hasattr (dataDim, attributeName):
          setattr(dataDim, attributeName, value[ii])
        elif value[ii]:
          raise ValueError("Attempt to set value for %s in dimension %s: %s" %
                           (attributeName, ii+1, value))
    else:
      raise ValueError("Value must have length %s, was %s" % (apiDataSource.numDim, value))

  @property
  def isComplex(self) -> tuple:
    """\- (*bool,*)\*dimensionCount, *settable*

    Is dimension complex?"""
    return tuple(x.isComplex for x in self._wrappedData.sortedDataDims())

  @isComplex.setter
  def isComplex(self, value:Sequence):
    self._setDataDimValue('isComplex', value)

  @property
  def dimensionTypes(self) -> tuple:
    """\- (*str,*)\*dimensionCount

    dimension types ('Fid' / 'Freq' / 'Sampled')."""
    return tuple(x.className[:-7] for x in self._wrappedData.sortedDataDims())

  @property
  def spectralWidthsHz(self) -> tuple:
    """\- (*float,*)\*dimensionCount, *settable*

    spectral width before correcting for spectrometer frequency (generally in Hz)."""
    return tuple(x.spectralWidth for x in self._wrappedData.sortedDataDims()
                 if hasattr(x, 'spectralWidth'))

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
    """\- (*float,*)\*dimensionCount, *settable*

    zero order phase correction (or None). Always None for sampled dimensions."""
    return tuple(x.phase0 for x in self._wrappedData.sortedDataDims()
                 if hasattr(x, 'phase0'))

  @phases0.setter
  def phases0(self, value:Sequence):
    self._setDataDimValue('phase0', value)

  @property
  def phases1(self) -> tuple:
    """\- (*float,*)\*dimensionCount, *settable*

    first order phase correction (or None). Always None for sampled dimensions."""
    return tuple(x.phase1 for x in self._wrappedData.sortedDataDims()
                 if hasattr(x, 'phase1'))

  @phases1.setter
  def phases1(self, value:Sequence):
    self._setDataDimValue('phase1', value)

  # Attributes belonging to ExpDimRef and DataDimRef

  def _mainExpDimRefs(self) -> list:
    """Get main ExpDimRef (serial=1) for each dimension"""

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
  def spectrometerFrequencies(self) -> tuple:
    """Tuple of spectrometer frequency for main dimensions reference """
    return tuple(x and x.sf for x in self._mainExpDimRefs())

  @spectrometerFrequencies.setter
  def spectrometerFrequencies(self, value):
    self._setExpDimRefAttribute('sf', value)

  @property
  def measurementTypes(self) -> tuple:
    """\- (*str,*)\*dimensionCount, *settable*

    measurement type for main dimensions reference """
    return tuple(x and x.measurementType for x in self._mainExpDimRefs())

  @measurementTypes.setter
  def measurementTypes(self, value):
    self._setExpDimRefAttribute('measurementType', value)
  #
  # @property
  # def maxAliasedFrequencies(self) -> tuple:
  #   """\- (*float,*)\*dimensionCount, *settable*
  #
  #    maximum possible peak frequency (in ppm) for main dimensions reference """
  #   return tuple(x and x.maxAliasedFreq for x in self._mainExpDimRefs())
  #
  # @maxAliasedFrequencies.setter
  # def maxAliasedFrequencies(self, value):
  #   self._setExpDimRefAttribute('maxAliasedFreq', value, mandatory=False)
  #
  # @property
  # def minAliasedFrequencies(self) -> tuple:
  #   """\- (*str,*)\*dimensionCount, *settable*
  #
  #    minimum possible peak frequency (in ppm) for main dimensions reference """
  #   return tuple(x and x.minAliasedFreq for x in self._mainExpDimRefs())
  #
  # @minAliasedFrequencies.setter
  # def minAliasedFrequencies(self, value):
  #   self._setExpDimRefAttribute('minAliasedFreq', value, mandatory=False)


  @property
  def isotopeCodes(self) -> tuple:
    """\- (*str,*)\*dimensionCount, *settable*

    main ExpDimRef (serial=1) isotopeCode - None if no unique code"""
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
    """Set main ExpDimRef (serial=1) isotopeCode for each dimension"""
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
  def foldingModes(self) -> tuple:
    """\- (*str,*)\*dimensionCount, *settable*

    main ExpDimRef folding mode (values: 'circular', 'mirror', None)"""
    dd = {True:'mirror', False:'circular', None:None}
    return tuple(dd[x and x.isFolded] for x in self._mainExpDimRefs())

  @foldingModes.setter
  def foldingModes(self, value):
    dd = {'circular':False, 'mirror':True, None:None}
    self._setExpDimRefAttribute('isFolded', [dd[x] for x in value])

  @property
  def axisCodes(self) -> tuple:
    """\- (*str,*)\*dimensionCount, *settable*

    Main ExpDimRef axisCode for each dimension - None if no main ExpDimRef
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
  def axisUnits(self) -> tuple:
    """\- (*str,*)\*dimensionCount, *settable*

    Main ExpDimRef axis unit (most commonly 'ppm') - None if no unique code

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
  def referencePoints(self) -> tuple:
    """\- (*float,*)\*dimensionCount, *settable*

    point used for axis (chemical shift) referencing."""
    return tuple(x and x.refPoint for x in self._mainDataDimRefs())

  @referencePoints.setter
  def referencePoints(self, value):
    self._setDataDimRefAttribute('refPoint', value)

  @property
  def referenceValues(self) -> tuple:
    """\- (*str,*)\*dimensionCount, *settable*

    value used for axis (chemical shift) referencing."""
    return tuple(x and x.refValue for x in self._mainDataDimRefs())

  @referenceValues.setter
  def referenceValues(self, value):
    self._setDataDimRefAttribute('refValue', value)

  @property
  def assignmentTolerances(self) -> tuple:
    """\- (*str,*)\*dimensionCount, *settable*

    Assignment tolerance in axis unit (ppm)."""
    return tuple(x and x.assignmentTolerance for x in self._mainDataDimRefs())

  @assignmentTolerances.setter
  def assignmentTolerances(self, value):
    self._setDataDimRefAttribute('assignmentTolerance', value)

  @property
  def spectralWidths(self) -> tuple:
    """\- (*float,*)\*dimensionCount, *settable*

    spectral width after processing (generally in ppm) """
    return tuple(x and x.spectralWidth for x in self._mainDataDimRefs())

  @spectralWidths.setter
  def spectralWidths(self, value):
    for ii,dataDimRef in enumerate(self._mainDataDimRefs()):
      if dataDimRef is not None:
        oldsw = dataDimRef[ii]
        sw = value[ii]
        localValuePerPoint = dataDimRef.localValuePerPoint
        if localValuePerPoint:
          dataDimRef.localValuePerPoint = localValuePerPoint*sw/oldsw
        else:
          dataDimRef.dataDim.valuePerPoint *= (sw/oldsw)

  @property
  def aliasingLimits(self) -> tuple:
    """\- (*(float,float)*)\*dimensionCount

    tuple of tuples of (lowerAliasingLimit, higherAliasingLimit) for spectrum """
    result = [(x and x.minAliasedFreq, x and x.maxAliasedFreq) for x in self._mainExpDimRefs()]

    if any(None in tt for tt in result):
      # Some values not set, or missing. Try to get them as spectrum limits
      for ii,dataDimRef in enumerate(self._mainDataDimRefs()):
        if None in result[ii]:
          dataDim = dataDimRef.dataDim
          ff = dataDimRef.pointToValue
          point1 = 1 - dataDim.pointOffset
          result[ii] = tuple(sorted((ff(point1), ff(point1 + dataDim.numPointsOrig))))
    #
    return tuple(result)

  @aliasingLimits.setter
  def aliasingLimits(self, value:tuple):
    if len(value) != self.dimensionCount:
      raise ValueError("length of alisingLimits must match spectrum dimension, was %s" % value)

    expDimRefs = self._mainExpDimRefs()
    for ii,tt in enumerate(value):
      expDimRef = expDimRefs[ii]
      if expDimRef:
        if len(tt) != 2:
          raise ValueError("Aliasing limits must have two value (min,max), was %s" % tt)
        expDimRef.minAliasedFreq = tt[0]
        expDimRef.maxAliasedFreq = tt[1]


  @property
  def spectrumLimits(self) -> tuple:
    """\- (*(float,float)*)\*dimensionCount

    tuple of tuples of (lowerLimit, higherLimit) for spectrum """
    ll = []
    for ii,ddr in enumerate(self._mainDataDimRefs()):
      if ddr is None:
        ll.append((None,None))
      else:
        ll.append((ddr.pointToValue(1), ddr.pointToValue(ddr.dataDim.numPoints+1)))
    return tuple(tuple(sorted(x)) for x in ll)

  @property
  def sample(self) -> Sample:
    """Sample used to acquire Spectrum"""
    return self._project._data2Obj.get(self._wrappedData.experiment.sample)

  @sample.setter
  def sample(self, value:Sample):
    self._wrappedData.experiment.sample = None if value is None else value._wrappedData

  # Implementation functions

  def rename(self, value):
    """Rename Spectrum, changing Id and Pid"""
    if value:
      self._wrappedData.name = value
    else:
      raise ValueError("Spectrum name must be set")

  @classmethod
  def _getAllWrappedData(cls, parent: Project)-> list:
    """get wrappedData (Nmr.DataSources) for all Spectrum children of parent Project"""
    return [x for y in parent._wrappedData.sortedExperiments()
            for x in y.sortedDataSources()]


def getter(self:ChemicalShiftList) -> tuple:
  ff = self._project._data2Obj.get
  return tuple(ff(y) for x in self._wrappedData.sortedExperiments()
               for y in x.sortedDataSources())
def setter(self:ChemicalShiftList, value:Sequence):
  self._wrappedData.experiments =  set(x._wrappedData.experiment for x in value)
ChemicalShiftList.spectra = property(getter, setter, None,
                          "Spectra using ChemicalShiftList")

def getter(self:Sample) -> tuple:
  ff = self._project._data2Obj.get
  return tuple(ff(y) for x in self._wrappedData.sortedNmrExperiments()
               for y in x.sortedDataSources())
def setter(self:Sample, value:Sequence):
  self._wrappedData.nmrExperiments =  set(x._wrappedData.experiment for x in value)
Sample.spectra = property(getter, setter, None,
                          "Spectra acquired using Sample (excluding multiSample spectra)")
del getter
del setter


def newSpectrum(self:Project, name:str) -> Spectrum:
  """Create new child Spectrum"""

  raise NotImplementedError("Not implemented. Use loadSpectrum function instead")

def createDummySpectrum(self:Project, axisCodes:Sequence[str], name=None) -> Spectrum:
  """Make dummy spectrum from isotopeCodes list - without data and with default parameters """
  return self._data2Obj[self._wrappedData.createDummySpectrum(axisCodes, name=name)]

# Connections to parents:

Project._childClasses.append(Spectrum)

Project.newSpectrum = newSpectrum
Project.createDummySpectrum = createDummySpectrum

# Notifiers:
className = ApiDataSource._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':Spectrum}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete'),
    ('_resetPid', {}, className, 'setName'),
  )
)
