"""Spectrum  class. Gives spectrum values, including per-dimension values as tuples.
Values that are not defined for a given dimension (e.g. sampled dimensions) are given as None.
Reference-related values apply only to the first Reference given (which is sufficient for
all common cases).

Dimension identifiers run from 1 to the number of dimensions (e.g. 1,2,3 for a 3D).
Per-dimension values are given in the order data are stored in the spectrum file - for
CCPN data the preferred convention is to have the acquisition dimension as dimension 1.

The axisCodes are used as an alternative axis identifier. They are unique strings (so they can
b recognised even if the axes are reordered in display). The axisCodes reflect the isotope
on the relevant axis, and match the dimension identifiers in the reference experiment templates,
linking a dimension to the correct reference experiment dimension. They are also used to map
automatically spectrum axes to display axes and to other spectra. By default the axis name
is the name of the atom being measured. Axes that are linked by a onebond
magnetisation transfer are given a lower-case suffix to show the nucleus bound to.
Duplicate axis names are distinguished by a
numerical suffix. The rules are best shown by example:

Experiment                 axisCodes

1D Bromine NMR             Br

3D proton NOESY-TOCSY      H, H1, H2

19F-13C-HSQC               Fc, Cf

15N-NOESY-HSQC OR
15N-HSQC-NOESY:            Hn, Nh, H

4D HCCH-TOCSY              Hc, Ch, Hc1, Ch1

HNCA/CB                    H. N. C

HNCO                       Hn, Nh, CO     *(CO is treated as a separate type)*

HCACO                      Hca, CAh, CO    *(CA is treated as a separate type)*

"""
# TODO double check axis codes for HCACO, HNCO, and use of Hcn axiscodes

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:30 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
import operator
from typing import Sequence, Tuple, Optional
from functools import partial
from ccpn.util import Common as commonUtil
from ccpn.util import Constants
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
from ccpnmodel.ccpncore.api.ccp.general import DataLocation
from ccpn.core.lib import Pid
from ccpn.core.lib.SpectrumLib import MagnetisationTransferTuple, _getProjection
from ccpn.core.lib.Cache import cached
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, deleteObject, ccpNmrV3CoreSetter, \
    logCommandBlock, undoStackBlocking, renameObject
from ccpn.util.Logging import getLogger
from ccpn.util.Common import axisCodeMapping
from ccpn.util.Logging import getLogger

from ccpnmodel.ccpncore.lib.Io import Formats


INCLUDEPOSITIVECONTOURS = 'includePositiveContours'
INCLUDENEGATIVECONTOURS = 'includeNegativeContours'


def _cumulativeArray(array):
    """ get total size and strides array.
        NB assumes fastest moving index first """

    ndim = len(array)
    cumul = ndim * [0]
    n = 1
    for i, size in enumerate(array):
        cumul[i] = n
        n = n * size

    return (n, cumul)


def _arrayOfIndex(index, cumul):
    """ Get from 1D index to point address tuple
    NB assumes fastest moving index first
    """

    ndim = len(cumul)
    array = ndim * [0]
    for i in range(ndim - 1, -1, -1):
        c = cumul[i]
        array[i], index = divmod(index, c)

    return np.array(array)


class Spectrum(AbstractWrapperObject):
    """A Spectrum object contains all the stored properties of an NMR spectrum, as well as the
    path to the stored NMR data file."""

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

    _referenceSpectrumHit = None

    MAXDIM = 4  # Maximum dimensionality

    PLANEDATACACHE = '_planeDataCache'  # Attribute name for the planeData cache
    SLICEDATACACHE = '_sliceDataCache'  # Attribute name for the slicedata cache
    SLICE1DDATACACHE = '_slice1DDataCache'  # Attribute name for the 1D slicedata cache

    def __init__(self, project: Project, wrappedData: Nmr.ShiftList):

        self._intensities = None
        self._positions = None

        super().__init__(project, wrappedData)

        self.doubleCrosshairOffsets = self.dimensionCount * [0]  # TBD: do we need this to be a property?
        self.showDoubleCrosshair = False

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
    def _localCcpnSortKey(self) -> Tuple:
        """Local sorting key, in context of parent."""
        dataSource = self._wrappedData
        return (dataSource.experiment.serial, dataSource.serial)

    @property
    def name(self) -> str:
        """short form of name, used for id"""
        return self._wrappedData.name

    @name.setter
    def name(self, value:str):
        """set name of Spectrum."""
        self.rename(value)

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
    def dimensions(self) -> tuple:
        """tuple of length dimensionCount with dimesnion integers; ie. (1,2,3,..).
        Useful for mapping axisCodes: eg: self.getByAxisCodes('dimensions', ['N','C','H']
        """
        return tuple(range(1, self.dimensionCount + 1))

    @property
    def indices(self) -> tuple:
        """tuple of length dimensionCount with indices integers; ie. (0,1,2,3).
        Useful for mapping axisCodes: eg: self.getByAxisCodes('indices', ['N','C','H']
        """
        return tuple(range(0, self.dimensionCount))

    # @property
    # def comment(self) -> str:
    #     """Free-form text comment"""
    #     return self._wrappedData.details
    #
    # @comment.setter
    # def comment(self, value: str):
    #     self._wrappedData.details = value

    @property
    def positiveContourCount(self) -> int:
        """number of positive contours to draw"""
        return self._wrappedData.positiveContourCount

    @positiveContourCount.setter
    def positiveContourCount(self, value):
        self._wrappedData.positiveContourCount = value

    @property
    def positiveContourBase(self) -> float:
        """base level of positive contours"""
        return self._wrappedData.positiveContourBase

    @positiveContourBase.setter
    def positiveContourBase(self, value):
        value = max(value, 1e-6)
        self._wrappedData.positiveContourBase = value

    @property
    def positiveContourFactor(self) -> float:
        """level multiplier for positive contours"""
        return self._wrappedData.positiveContourFactor

    @positiveContourFactor.setter
    def positiveContourFactor(self, value):
        self._wrappedData.positiveContourFactor = value

    @property
    def positiveContourColour(self) -> str:
        """colour of positive contours"""
        return self._wrappedData.positiveContourColour

    @positiveContourColour.setter
    def positiveContourColour(self, value):
        self._wrappedData.positiveContourColour = value

    @property
    def includePositiveContours(self):
        """Include flag for the positive contours
        """
        result = self._ccpnInternalData.get(INCLUDEPOSITIVECONTOURS)
        if result is None:
            tempCcpn = self._ccpnInternalData.copy()
            result = tempCcpn[INCLUDEPOSITIVECONTOURS] = True
            self._ccpnInternalData = tempCcpn
        return result

    @includePositiveContours.setter
    def includePositiveContours(self, value: bool):
        """Include flag for the positive contours
        """
        if not isinstance(self._ccpnInternalData, dict):
            raise ValueError("Spectrum.includePositiveContours: CCPN internal must be a dictionary")

        # copy needed to ensure that the v2 registers the change, and marks instance for save.
        tempCcpn = self._ccpnInternalData.copy()
        tempCcpn[INCLUDEPOSITIVECONTOURS] = value
        self._ccpnInternalData = tempCcpn

    @property
    def negativeContourCount(self) -> int:
        """number of negative contours to draw"""
        return self._wrappedData.negativeContourCount

    @negativeContourCount.setter
    def negativeContourCount(self, value):
        self._wrappedData.negativeContourCount = value

    @property
    def negativeContourBase(self) -> float:
        """base level of negative contours"""
        return self._wrappedData.negativeContourBase

    @negativeContourBase.setter
    def negativeContourBase(self, value):
        value = min(value, -1e-6)
        self._wrappedData.negativeContourBase = value

    @property
    def negativeContourFactor(self) -> float:
        """level multiplier for negative contours"""
        return self._wrappedData.negativeContourFactor

    @negativeContourFactor.setter
    def negativeContourFactor(self, value):
        self._wrappedData.negativeContourFactor = value

    @property
    def negativeContourColour(self) -> str:
        """colour of negative contours"""
        return self._wrappedData.negativeContourColour

    @negativeContourColour.setter
    def negativeContourColour(self, value):
        self._wrappedData.negativeContourColour = value

    @property
    def includeNegativeContours(self):
        """Include flag for the negative contours
        """
        result = self._ccpnInternalData.get(INCLUDENEGATIVECONTOURS)
        if result is None:
            tempCcpn = self._ccpnInternalData.copy()
            result = tempCcpn[INCLUDENEGATIVECONTOURS] = True
            self._ccpnInternalData = tempCcpn
        return result

    @includeNegativeContours.setter
    def includeNegativeContours(self, value: bool):
        """Include flag for the negative contours
        """
        if not isinstance(self._ccpnInternalData, dict):
            raise ValueError("Spectrum.includeNegativeContours: CCPN internal must be a dictionary")

        # copy needed to ensure that the v2 registers the change, and marks instance for save.
        tempCcpn = self._ccpnInternalData.copy()
        tempCcpn[INCLUDENEGATIVECONTOURS] = value
        self._ccpnInternalData = tempCcpn

    @property
    def sliceColour(self) -> str:
        """colour of 1D slices"""
        return self._wrappedData.sliceColour

    @sliceColour.setter
    def sliceColour(self, value):
        self._wrappedData.sliceColour = value
        # for spectrumView in self.spectrumViews:
        #     spectrumView.setSliceColour()  # ejb - update colour here

    @property
    def scale(self) -> float:
        """Scaling factor for intensities and volumes.
        Intensities and volumes should be *multiplied* by scale before comparison."""
        return self._wrappedData.scale

    @scale.setter
    def scale(self, value: float):
        self._wrappedData.scale = value

        # # update the intensities as the scale has changed
        # self._intensities = self.getSliceData()

        # for spectrumView in self.spectrumViews:
        #     spectrumView.refreshData()

    @property
    def spinningRate(self) -> float:
        """NMR tube spinning rate (in Hz)."""
        return self._wrappedData.experiment.spinningRate

    @spinningRate.setter
    def spinningRate(self, value: float):
        self._wrappedData.experiment.spinningRate = value

    @property
    def noiseLevel(self) -> float:
        """Estimated noise level for the spectrum,
        defined as the estimated standard deviation of the points from the baseplane/baseline"""
        return self._wrappedData.noiseLevel

    @noiseLevel.setter
    def noiseLevel(self, value: float):
        self._wrappedData.noiseLevel = value

    @property
    def synonym(self) -> str:
        """Systematic experiment type descriptor (CCPN system)."""
        refExperiment = self._wrappedData.experiment.refExperiment
        if refExperiment is None:
            return None
        else:
            return refExperiment.synonym

    @property
    def experimentType(self) -> str:
        """Systematic experiment type descriptor (CCPN system)."""
        refExperiment = self._wrappedData.experiment.refExperiment
        if refExperiment is None:
            return None
        else:
            return refExperiment.name

    @experimentType.setter
    def experimentType(self, value: str):
        for nmrExpPrototype in self._wrappedData.root.sortedNmrExpPrototypes():
            for refExperiment in nmrExpPrototype.sortedRefExperiments():
                if value == refExperiment.name:
                    # refExperiment matches name string - set it
                    self._wrappedData.experiment.refExperiment = refExperiment
                    synonym = refExperiment.synonym
                    if synonym:
                        self.experimentName = synonym
                    return
        # nothing found - error:
        raise ValueError("No reference experiment matches name '%s'" % value)

    @property
    def _serial(self):
        """Return the _wrappedData serial
        CCPN Internal
        """
        return self._wrappedData.serial

    @property
    def _numDim(self):
        """Return the _wrappedData numDim
        CCPN Internal
        """
        return self._wrappedData.numDim

    @property
    def experiment(self):
        """Return the experiment assigned to the spectrum
        """
        return self._wrappedData.experiment

    @property
    def experimentName(self) -> str:
        """Common experiment type descriptor (May not be unique)."""
        return self._wrappedData.experiment.name

    @experimentName.setter
    def experimentName(self, value):
        self._wrappedData.experiment.name = value

    @property
    def filePath(self) -> str:
        """Absolute path to NMR data file."""
        xx = self._wrappedData.dataStore
        if xx:
            return xx.fullPath
        else:
            return None

    @filePath.setter
    def filePath(self, value: str):

        apiDataStore = self._wrappedData.dataStore
        if apiDataStore is None:
            raise ValueError("Spectrum is not stored, cannot change file path")

        elif not value:
            raise ValueError("Spectrum file path cannot be set to None")

        else:
            dataUrl = self._project._wrappedData.root.fetchDataUrl(value)
            apiDataStore.repointToDataUrl(dataUrl)
            apiDataStore.path = value[len(dataUrl.url.path) + 1:]

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

    def _setStdDataDimValue(self, attributeName, value: Sequence):
        """Set value for non-Sampled DataDims only"""
        apiDataSource = self._wrappedData
        if len(value) == apiDataSource.numDim:
            for ii, dataDim in enumerate(apiDataSource.sortedDataDims()):
                if dataDim.className != 'SampledDataDim':
                    setattr(dataDim, attributeName, value[ii])
                elif value[ii] is not None:
                    raise ValueError("Attempt to set value for invalid attribute %s in dimension %s: %s" %
                                     (attributeName, ii + 1, value))
        else:
            raise ValueError("Value must have length %s, was %s" % (apiDataSource.numDim, value))

    @property
    def pointCounts(self) -> Tuple[int, ...]:
        """Number active of points per dimension

        NB, Changing the pointCounts will keep the spectralWidths (after Fourier transformation)
        constant.

        NB for FidDataDims more points than these may be stored (see totalPointCount)."""
        result = []
        for dataDim in self._wrappedData.sortedDataDims():
            if hasattr(dataDim, 'numPointsValid'):
                result.append(dataDim.numPointsValid)
            else:
                result.append(dataDim.numPoints)
        return tuple(result)

    @pointCounts.setter
    def pointCounts(self, value: Sequence):
        apiDataSource = self._wrappedData
        if len(value) == apiDataSource.numDim:
            dataDimRefs = self._mainDataDimRefs()
            for ii, dataDim in enumerate(apiDataSource.sortedDataDims()):
                val = value[ii]
                className = dataDim.className
                if className == 'SampledDataDim':
                    # No sweep width to worry about. Up to programmer to make sure sampled values match.
                    dataDim.numPoints = val
                elif className == 'FidDataDim':
                    #Number of points refers to time domain, independent of sweep width
                    dataDim.numPointsValid = val
                elif className == 'FreqDataDim':
                    # Changing the number of points may NOT change the spectralWidth
                    relativeVal = val / dataDim.numPoints
                    dataDim.numPoints = val
                    dataDim.valuePerPoint /= relativeVal
                    dataDimRef = dataDimRefs[ii]
                    if dataDimRef is not None:
                        # This will work if we are changing to a different factor of two in pointCount.
                        # If we are making an arbitrary change, the referencing is not reliable anyway.
                        dataDimRef.refPoint = ((dataDimRef.refPoint - 1) * relativeVal) + 1
                else:
                    raise TypeError("API DataDim object with unknown className:", className)
        else:
            raise ValueError("pointCounts value must have length %s, was %s" %
                             (apiDataSource.numDim, value))

    @property
    def totalPointCounts(self) -> Tuple[int, ...]:
        """Total number of points per dimension

        NB for FidDataDims and SampledDataDims these are the stored points,
        for FreqDataDims these are the points after transformation before cutting down.

        NB, changing the totalPointCount will *not* modify the resolution (or dwell time),
        so the implied total width will change."""
        result = []
        for dataDim in self._wrappedData.sortedDataDims():
            if hasattr(dataDim, 'numPointsOrig'):
                result.append(dataDim.numPointsOrig)
            else:
                result.append(dataDim.numPoints)
        return tuple(result)

    @totalPointCounts.setter
    def totalPointCounts(self, value: Sequence):
        apiDataSource = self._wrappedData
        if len(value) == apiDataSource.numDim:
            for ii, dataDim in enumerate(apiDataSource.sortedDataDims()):
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
    def pointOffsets(self, value: Sequence):
        self._setStdDataDimValue('pointOffset', value)

    @property
    def isComplex(self) -> Tuple[bool, ...]:
        """Is dimension complex? -  per dimension"""
        return tuple(x.isComplex for x in self._wrappedData.sortedDataDims())

    @isComplex.setter
    def isComplex(self, value: Sequence):
        apiDataSource = self._wrappedData
        if len(value) == apiDataSource.numDim:
            for ii, dataDim in enumerate(apiDataSource.sortedDataDims()):
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
    def spectralWidthsHz(self, value: Sequence):
        apiDataSource = self._wrappedData
        attributeName = 'spectralWidth'
        if len(value) == apiDataSource.numDim:
            for ii, dataDim in enumerate(apiDataSource.sortedDataDims()):
                val = value[ii]
                if hasattr(dataDim, attributeName):
                    if not val:
                        raise ValueError("Attempt to set %s to %s in dimension %s: %s"
                                         % (attributeName, val, ii + 1, value))
                    else:
                        # We assume that the number of points is constant, so setting SW changes valuePerPoint
                        swold = getattr(dataDim, attributeName)
                        dataDim.valuePerPoint *= (val / swold)
                elif val is not None:
                    raise ValueError("Attempt to set %s in sampled dimension %s: %s"
                                     % (attributeName, ii + 1, value))
        else:
            raise ValueError("SpectralWidth value must have length %s, was %s" %
                             (apiDataSource.numDim, value))

        @property
        def valuesPerPoint(self) -> Tuple[Optional[float], ...]:
            """valuePerPoint for each dimension

            in ppm for Frequency dimensions with a single, well-defined reference

            None for Frequency dimensions without a single, well-defined reference

            in time units (seconds) for FId dimensions

            None for sampled dimensions"""

            result = []
            for dataDim in self._wrappedData.sortedDataDims():
                if hasattr(dataDim, 'primaryDataDimRef'):
                    # FreqDataDim - get ppm valuePerPoint
                    ddr = dataDim.primaryDataDimRef
                    valuePerPoint = ddr and ddr.valuePerPoint
                elif hasattr(dataDim, 'valuePerPoint'):
                    # FidDataDim - get time valuePerPoint
                    valuePerPoint = dataDim.valuePerPoint
                else:
                    # Sampled DataDim - return None
                    valuePerPoint = None
                #
                result.append(valuePerPoint)
            #
            return tuple(result)

    @property
    def phases0(self) -> tuple:
        """zero order phase correction (or None), per dimension. Always None for sampled dimensions."""
        return tuple(x.phase0 if x.className != 'SampledDataDim' else None
                     for x in self._wrappedData.sortedDataDims())

    @phases0.setter
    def phases0(self, value: Sequence):
        self._setStdDataDimValue('phase0', value)

    @property
    def phases1(self) -> Tuple[Optional[float], ...]:
        """first order phase correction (or None) per dimension. Always None for sampled dimensions."""
        return tuple(x.phase1 if x.className != 'SampledDataDim' else None
                     for x in self._wrappedData.sortedDataDims())

    @phases1.setter
    def phases1(self, value: Sequence):
        self._setStdDataDimValue('phase1', value)

    @property
    def windowFunctions(self) -> Tuple[Optional[str], ...]:
        """Window function name (or None) per dimension - e.g. 'EM', 'GM', 'SINE', 'QSINE', ....
        Always None for sampled dimensions."""
        return tuple(x.windowFunction if x.className != 'SampledDataDim' else None
                     for x in self._wrappedData.sortedDataDims())

    @windowFunctions.setter
    def windowFunctions(self, value: Sequence):
        self._setStdDataDimValue('windowFunction', value)

    @property
    def lorentzianBroadenings(self) -> Tuple[Optional[float], ...]:
        """Lorenzian broadening in Hz per dimension. Always None for sampled dimensions."""
        return tuple(x.lorentzianBroadening if x.className != 'SampledDataDim' else None
                     for x in self._wrappedData.sortedDataDims())

    @lorentzianBroadenings.setter
    def lorentzianBroadenings(self, value: Sequence):
        self._setStdDataDimValue('lorentzianBroadening', value)

    @property
    def gaussianBroadenings(self) -> Tuple[Optional[float], ...]:
        """Gaussian broadening per dimension. Always None for sampled dimensions."""
        return tuple(x.gaussianBroadening if x.className != 'SampledDataDim' else None
                     for x in self._wrappedData.sortedDataDims())

    @gaussianBroadenings.setter
    def gaussianBroadenings(self, value: Sequence):
        self._setStdDataDimValue('gaussianBroadening', value)

    @property
    def sineWindowShifts(self) -> Tuple[Optional[float], ...]:
        """Shift of sine/sine-square window function in degrees. Always None for sampled dimensions."""
        return tuple(x.sineWindowShift if x.className != 'SampledDataDim' else None
                     for x in self._wrappedData.sortedDataDims())

    @sineWindowShifts.setter
    def sineWindowShifts(self, value: Sequence):
        self._setStdDataDimValue('sineWindowShift', value)

    # Attributes belonging to ExpDimRef and DataDimRef

    def _mainExpDimRefs(self) -> list:
        """Get main API ExpDimRef (serial=1) for each dimension"""

        result = []
        for ii, dataDim in enumerate(self._wrappedData.sortedDataDims()):
            # NB MUST loop over dataDims, in case of projection spectra
            result.append(dataDim.expDim.findFirstExpDimRef(serial=1))
        #
        return tuple(result)

    def _setExpDimRefAttribute(self, attributeName: str, value: Sequence, mandatory: bool = True):
        """Set main ExpDimRef attribute (serial=1) for each dimension"""
        apiDataSource = self._wrappedData
        if len(value) == apiDataSource.numDim:
            for ii, dataDim in enumerate(self._wrappedData.sortedDataDims()):
                # NB MUST loop over dataDims, in case of projection spectra
                expDimRef = dataDim.expDim.findFirstExpDimRef(serial=1)
                val = value[ii]
                if expDimRef is None and val is not None:
                    raise ValueError("Attempt to set attribute %s in dimension %s to %s - must be None" %
                                     (attributeName, ii + 1, val))
                elif val is None and mandatory:
                    raise ValueError(
                            "Attempt to set mandatory attribute %s to None in dimension %s: %s" %
                            (attributeName, ii + 1, val))
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
    def isotopeCodes(self, value: Sequence):
        apiDataSource = self._wrappedData
        if len(value) == apiDataSource.numDim:
            #GWV 28/8/18: commented as cannot see the reason for this, while prevented correction of errors
            # if value != self.isotopeCodes and self.peaks:
            #   raise ValueError("Cannot reset isotopeCodes in a Spectrum that contains peaks")
            for ii, dataDim in enumerate(apiDataSource.sortedDataDims()):
                expDimRef = dataDim.expDim.findFirstExpDimRef(serial=1)
                val = value[ii]
                if expDimRef is None:
                    if val is not None:
                        raise ValueError("Cannot set isotopeCode %s in dimension %s" % (val, ii + 1))
                elif val is None:
                    expDimRef.isotopeCodes = ()
                else:
                    expDimRef.isotopeCodes = (val,)
        else:
            raise ValueError("Value must have length %s, was %s" % (apiDataSource.numDim, value))

    @property
    def foldingModes(self) -> Tuple[Optional[str], ...]:
        """folding mode (values: 'circular', 'mirror', None), per dimension"""
        dd = {True: 'mirror', False: 'circular', None: None}
        return tuple(dd[x and x.isFolded] for x in self._mainExpDimRefs())

    @foldingModes.setter
    def foldingModes(self, value):

        # TODO For NEF we should support both True, False, and None
        # That requires an API change

        dd = {'circular': False, 'mirror': True, None: False}
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
    def axisCodes(self, values):
        check = {}
        for i, v in enumerate(values):
            if v in check:
                raise ValueError('axisCodes should be an unique sequence of strings; got duplicate entry axisCodes[%s]="%s"'
                                 % (i, v))
            else:
                check[v] = i
        self._setExpDimRefAttribute('axisCode', values, mandatory=False)

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

        for ii, dataDim in enumerate(self._wrappedData.sortedDataDims()):
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

    def _setDataDimRefAttribute(self, attributeName: str, value: Sequence, mandatory: bool = True):
        """Set main DataDimRef attribute for each dimension
        - uses first ExpDimRef with serial=1"""
        apiDataSource = self._wrappedData
        if len(value) == apiDataSource.numDim:
            expDimRefs = self._mainExpDimRefs()
            for ii, dataDim in enumerate(self._wrappedData.sortedDataDims()):
                if hasattr(dataDim, 'dataDimRefs'):
                    dataDimRef = dataDim.findFirstDataDimRef(expDimRef=expDimRefs[ii])
                else:
                    dataDimRef = None

                if dataDimRef is None:
                    if value[ii] is not None:
                        raise ValueError("Cannot set value for attribute %s in dimension %s: %s" %
                                         (attributeName, ii + 1, value))
                elif value is None and mandatory:
                    raise ValueError(
                            "Attempt to set value to None for mandatory attribute %s in dimension %s: %s" %
                            (attributeName, ii + 1, value))
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
    def defaultAssignmentTolerances(self):
        """Default assignment tolerances, per dimension.

        NB for Fid or Sampled dimensions value will be None
        """
        tolerances = [None] * self.dimensionCount
        for ii, dimensionType in enumerate(self.dimensionTypes):
            if dimensionType == 'Frequency':
                tolerance = Constants.isotope2Tolerance.get(self.isotopeCodes[ii],
                                                            Constants.defaultAssignmentTolerance)
                tolerances[ii] = max(tolerance, self.spectralWidths[ii] / self.pointCounts[ii])
        #
        return tolerances

    @property
    def spectralWidths(self) -> Tuple[Optional[float], ...]:
        """spectral width after processing in axis unit (ppm), per dimension """
        return tuple(x and x.spectralWidth for x in self._mainDataDimRefs())

    @spectralWidths.setter
    def spectralWidths(self, value):
        oldValues = self.spectralWidths
        for ii, dataDimRef in enumerate(self._mainDataDimRefs()):
            if dataDimRef is not None:
                oldsw = oldValues[ii]
                sw = value[ii]
                localValuePerPoint = dataDimRef.localValuePerPoint
                if localValuePerPoint:
                    dataDimRef.localValuePerPoint = localValuePerPoint * sw / oldsw
                else:
                    dataDimRef.dataDim.valuePerPoint *= (sw / oldsw)

    @property
    def aliasingLimits(self) -> Tuple[Tuple[Optional[float], Optional[float]], ...]:
        """\- (*(float,float)*)\*dimensionCount

        tuple of tuples of (lowerAliasingLimit, higherAliasingLimit) for spectrum """
        result = [(x and x.minAliasedFreq, x and x.maxAliasedFreq) for x in self._mainExpDimRefs()]

        if any(None in tt for tt in result):
            # Some values not set, or missing. Try to get them as spectrum limits
            for ii, dataDimRef in enumerate(self._mainDataDimRefs()):
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
        for ii, tt in enumerate(value):
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
        for ii, ddr in enumerate(self._mainDataDimRefs()):
            if ddr is None:
                ll.append((None, None))
            else:
                ll.append(tuple(sorted((ddr.pointToValue(1), ddr.pointToValue(ddr.dataDim.numPoints + 1)))))
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

        The magnetisationTransfers are deduced from the experimentType and axisCodes.
        Only when the experimentType is unset or does not match any known reference experiment
        magnetisationTransfers are kept separately in the API layer.
        """

        result = []
        apiExperiment = self._wrappedData.experiment
        apiRefExperiment = apiExperiment.refExperiment

        if apiRefExperiment:
            # We should use the refExperiment - if present
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
                                result.append(MagnetisationTransferTuple(dim1, jj + 1, tt[0], tt[1]))

        else:
            # Without a refExperiment use parameters stored in the API (for reproducibility)
            ll = []
            for apiExpTransfer in apiExperiment.expTransfers:
                item = [x.expDim.dim for x in apiExpTransfer.expDimRefs]
                item.sort()
                item.append(apiExpTransfer.transferType)
                item.append(not (apiExpTransfer.isDirect))
                ll.append(item)
            for item in sorted(ll):
                result.append(MagnetisationTransferTuple(*item))

        #
        return tuple(result)

    def _setMagnetisationTransfers(self, value: Tuple[MagnetisationTransferTuple, ...]):
        """Setter for magnetisation transfers.


        The magnetisationTransfers are deduced from the experimentType and axisCodes.
        When the experimentType is set this function is a No-op.
        Only when the experimentType is unset or does not match any known reference experiment
        does this function set the magnetisation transfers, and the corresponding values are
        ignored if the experimentType is later set."""

        apiExperiment = self._wrappedData.experiment
        apiRefExperiment = apiExperiment.refExperiment
        if apiRefExperiment is None:
            for et in apiExperiment.expTransfers:
                et.delete()
            mainExpDimRefs = self._mainExpDimRefs()
            for tt in value:
                try:
                    dim1, dim2, transferType, isIndirect = tt
                    expDimRefs = (mainExpDimRefs[dim1 - 1], mainExpDimRefs[dim2 - 1])
                except:
                    raise ValueError(
                            "Attempt to set incorrect magnetisationTransfer value %s in spectrum %s"
                            % (tt, self.pid)
                            )
                apiExperiment.newExpTransfer(expDimRefs=expDimRefs, transferType=transferType,
                                             isDirect=(not isIndirect))
        else:
            apiRefExperiment.root._logger.warning(
                    """An attempt to set Spectrum.magnetisationTransfers directly was ignored
                  because the spectrum experimentType was defined.
                  Use axisCodes to set magnetisation transfers instead.""")

    @property
    def intensities(self) -> np.ndarray:
        """ spectral intensities as NumPy array for 1D spectra
        """
        if self.dimensionCount != 1:
            raise RuntimeError('Currently this method only works for 1D spectra')

        if self._intensities is None:
            self.getSliceData()

        if self._intensities is None:
            getLogger().warning('Unable to get 1D slice data for %s' % self)

        # # store the unscaled value internally so need to multiply the return value again
        # if self.getSliceData() is  None:
        #     return np.array([0]*len(self.positions))
        # else:
        #     self._intensities = self.getSliceData() / self.scale
        #
        #
        # # OLD - below not needed any more since now scaled in getSliceData()
        # # if self._intensities is not None:
        # #   self._intensities *= self.scale

        return self._intensities

    @intensities.setter
    def intensities(self, value: np.ndarray):
        self._intensities = value
        # temporary hack for showing straight the result of intensities change
        for spectrumView in self.spectrumViews:
            spectrumView.refreshData()

    @property
    def positions(self) -> np.ndarray:
        """ spectral region in ppm as NumPy array for 1D spectra """

        if self.dimensionCount != 1:
            raise Exception('Currently this method only works for 1D spectra')

        if self._positions is None:
            spectrumLimits = self.spectrumLimits[0]
            pointCount = self.pointCounts[0]
            # WARNING: below assumes that spectrumLimits are "backwards" (as is true for ppm)
            scale = (spectrumLimits[0] - spectrumLimits[1]) / pointCount
            self._positions = spectrumLimits[1] + scale * np.arange(pointCount, dtype='float32')

        return self._positions

    @positions.setter
    def positions(self, value):
        self._positions = value
        # temporary hack for showing straight the result of intensities change
        for spectrumView in self.spectrumViews:
            spectrumView.refreshData()

    #=========================================================================================
    # Library functions
    #=========================================================================================

    def getHeight(self, ppmPositions):
        """returns the interpolated height at the ppm position
        """
        #TODO: Urgently needs fixing
        return 10

    def getPositionValue(self, position):
        return self._apiDataSource.getPositionValue(position)

    @cached(SLICE1DDATACACHE, maxItems=1, debug=False)
    def _get1DSliceData(self, position, sliceDim: int):
        """Internal routine to get 1D sliceData;
        """
        return self._apiDataSource.getSliceData(position=position, sliceDim=sliceDim)

    @cached(SLICEDATACACHE, maxItems=1024, debug=False)
    def _getSliceDataFromPlane(self, position, xDim: int, yDim: int, sliceDim: int):
        """Internal routine to get sliceData; optimised to use (buffered) getPlaneData
        CCPNINTERNAL: used in CcpnOpenGL
        """
        if not (sliceDim == xDim or sliceDim == yDim):
            raise RuntimeError('sliceDim (%s) not in plane (%s,%s)' % (sliceDim, xDim, yDim))
        data = self.getPlaneData(position, xDim, yDim)
        if sliceDim == xDim:
            slice = position[yDim - 1] - 1  # position amd dimensions are 1-based
            return data[slice, 0:]
        elif sliceDim == yDim:
            slice = position[xDim - 1] - 1  # position amd dimensions are 1-based
            return data[0:, slice]

    def getSliceData(self, position=None, sliceDim: int = 1):
        """
        Get a slice through position along sliceDim from the Spectrum
        :param position: A list/tuple of positions (1-based)
        :param sliceDim: Dimension of the slice (1-based)
        :return: numpy data array
        """
        if position is None:
            position = [1] * self.dimensionCount

        if self.dimensionCount == 1:
            result = self._get1DSliceData(position=position, sliceDim=sliceDim)
        else:
            position[sliceDim - 1] = 1  # To improve caching; position, dimensions are 1-based
            if sliceDim > 1:
                result = self._getSliceDataFromPlane(position=position, xDim=1, yDim=sliceDim,
                                                     sliceDim=sliceDim)
            else:
                result = self._getSliceDataFromPlane(position=position, xDim=sliceDim, yDim=sliceDim + 1,
                                                     sliceDim=sliceDim)

        if result is not None and result.size != 0:
            # Optionally scale data depending on self.scale
            if self.scale is not None:
                if self.scale == 0.0:
                    getLogger().warning('Scaling "%s" by 0.0!' % self)
                result *= self.scale
            # For 1D, save as intensities attribute
            self._intensities = result
            return result

    @cached(PLANEDATACACHE, maxItems=64, debug=False)
    def _getPlaneData(self, position, xDim: int, yDim: int):
        "Internal routine to improve caching: Calling routine set the positions of xDim, yDim to 1 "
        return self._apiDataSource.getPlaneData(position=position, xDim=xDim, yDim=yDim)

    def getPlaneData(self, position=None, xDim: int = 1, yDim: int = 2):
        """Get a plane defined by by xDim and yDim, and a position vector ('1' based)
        Dimensionality must be >= 2

        :param position: A list/tuple of positions (1-based)
        :param xDim: Dimension of the first dimension (1-based)
        :param yDim: Dimension of the second dimension (1-based)
        :return: 2D float32 NumPy array in order (yDim, xDim)

        NB: use getPlane method for axisCode based access
        """
        if self.dimensionCount < 2:
            raise ValueError('Spectrum.getPlaneData; dimensionCount must be >= 2')
        if xDim == yDim:
            raise ValueError('Spectrum.getPlaneData; must have xDim != yDim')
        dims = self.dimensions
        if xDim not in dims:
            raise ValueError('Spectrum.getPlaneData; invalid xDim "%s"; must one of %s' %
                             (xDim, dims))
        if yDim not in dims:
            raise ValueError('Spectrum.getPlaneData; invalid yDim "%s"; must one of %s' %
                             (yDim, dims))
        if position is None:
            position = [1] * self.dimensionCount

        for idx, p in enumerate(position):
            if not (1 <= p <= self.pointCounts[idx]):
                raise ValueError('Spectrum.getPlaneData; invalid position[%d] "%d"; should be in range (%d,%d)' %
                                 (idx, p, 1, self.pointCounts[idx]))

        position = list(position)  # assure we have a list so we can assign below
        # set the points of xDim, yDim to 1 as these do not matter (to improve caching)
        position[xDim - 1] = 1  # position is 1-based
        position[yDim - 1] = 1
        result = self._getPlaneData(position=position, xDim=xDim, yDim=yDim)
        # Optionally scale data depending on self.scale
        if self.scale is not None:
            if self.scale == 0.0:
                getLogger().warning('Scaling "%s" by 0.0!' % self)
            result *= self.scale
        return result

    def getPlane(self, axisCodes: tuple, position=None, exactMatch=True):
        """Get a plane defined by a tuple of two axisCodes, and a position vector ('1' based, defaults to first point)
        Expand axisCodes if exactMatch=False
        return data array
        NB: use getPlaneData method for dimension based access
        """
        if len(axisCodes) != 2:
            raise ValueError('Invalid axisCodes %s, len should be 2' % axisCodes)
        xDim, yDim = self.getByAxisCodes('dimensions', axisCodes, exactMatch=exactMatch)
        return self.getPlaneData(position=position, xDim=xDim, yDim=yDim)

    def allPlanes(self, axisCodes: tuple, exactMatch=True):
        """An iterator over all planes defined by axisCodes, yielding (position, data-array) tuples
        Expand axisCodes if exactMatch=False
        """

        if len(axisCodes) != 2:
            raise ValueError('Invalid axisCodes %s, len should be 2' % axisCodes)
        axisCodes = self.getByAxisCodes('axisCodes', axisCodes, exactMatch=exactMatch)  # check and optionally expand axisCodes
        if axisCodes[0] == axisCodes[1]:
            raise ValueError('Invalid axisCodes %s; identical' % axisCodes)

        # get axisCodes of dimensions to interate over
        iterAxisCodes = list(set(self.axisCodes) - set(axisCodes))
        # get relevant iteration parameters
        points = self.getByAxisCodes('pointCounts', iterAxisCodes)
        indices = [idx - 1 for idx in self.getByAxisCodes('dimensions', iterAxisCodes)]
        iterData = list(zip(iterAxisCodes, points, indices))

        def _nextPosition(currentPosition):
            "Return a (done, position) tuple derived from currentPosition"
            for axisCode, point, idx in iterData:
                if currentPosition[idx] + 1 <= point:  # still an increment to make in this dimension
                    currentPosition[idx] += 1
                    return (False, currentPosition)
                else:  # reset this dimension
                    currentPosition[idx] = 1
            return (True, None)  # reached the end

        # loop over all planes
        position = [1] * self.dimensionCount
        done = False
        xDim, yDim = self.getByAxisCodes('dimensions', axisCodes, exactMatch=True)
        while not done:
            # Using direct api getPlaneData call to reduce overhead; (all parameters have been checked)
            # By-passes the caching
            planeData = self._apiDataSource.getPlaneData(position=position, xDim=xDim, yDim=yDim)
            yield (position, planeData)
            done, position = _nextPosition(position)

    def getProjection(self, axisCodes: tuple, method: str = 'max', threshold=None, path=None, format: str = Formats.NMRPIPE):
        """Get projected plane defined by a tuple of two axisCodes, using method and an optional threshold
        optionally save to path as format
        return projected spectrum data array
        """
        if path is not None and format != Formats.NMRPIPE:
            raise ValueError('Can only save spectrum projection to %s format currently' % Formats.NMRPIPE)

        projectedData = _getProjection(self, axisCodes=axisCodes, method=method, threshold=threshold)

        if path is not None:
            from ccpnmodel.ccpncore.lib._ccp.nmr.Nmr.DataSource import _saveNmrPipe2DHeader

            with open(path, 'wb') as fp:
                #TODO: remove dependency on filestorage on apiLayer
                xDim, yDim = self.getByAxisCodes('dimensions', axisCodes)[0:2]
                _saveNmrPipe2DHeader(self._wrappedData, fp, xDim, yDim)
                projectedData.tofile(fp)

        return projectedData

    def automaticIntegration(self, spectralData):
        return self._apiDataSource.automaticIntegration(spectralData)

    def estimateNoise(self):
        return self._apiDataSource.estimateNoise()

    def get1dSpectrumData(self):
        """Get position,scaledData numpy array for 1D spectrum.
        Yields first 1D slice for nD"""
        return self._apiDataSource.get1dSpectrumData()

    def _mapAxisCodes(self, axisCodes: Sequence[str]):
        """Map axisCodes on self.axisCodes
        return mapped axisCodes as list
        """
        # find the map of newAxisCodeOrder to self.axisCodes; eg. 'H' to 'Hn'
        axisCodeMap = axisCodeMapping(axisCodes, self.axisCodes)
        if len(axisCodeMap) == 0:
            raise ValueError('axisCodes %s contains an invalid element' % str(axisCodes))
        return [axisCodeMap[a] for a in axisCodes]

    def _reorderValues(self, values: Sequence, newAxisCodeOrder: Sequence[str]):
        """Reorder values in spectrum dimension order to newAxisCodeOrder
        """
        mapping = dict((axisCode, i) for i, axisCode in enumerate(self.axisCodes))
        # assemble the newValues in order
        newValues = []
        for axisCode in newAxisCodeOrder:
            if axisCode in mapping:
                newValues.append(values[mapping[axisCode]])
            else:
                raise ValueError('Invalid axisCode "%s" in %s; should be one of %s' %
                                 (axisCode, newAxisCodeOrder, self.axisCodes))
        return newValues

    def getRegionData(self, exclusionBuffer=None, **axisDict):
        """Return the region of the spectrum data defined by the axis limits.

        Axis limits are passed in as a dict containing the axis codes and the required limits.
        Each limit is defined as a key, value pair: (str, tuple),
        with the tuple supplied as (min,max) axis limits in ppm.

        For axisCodes that are not included, the limits will by taken from the aliasingLimits of the spectrum.

        Illegal axisCodes will raise an error.

        Example dict:

        ::

            {'Hn': (7.0, 9.0),
             'Nh': (110, 130)
             }

        Example calling function:

        ::

            regionData = spectrum.getRegionData(**limitsDict)
            regionData = spectrum.getRegionData(Hn=(7.0, 9.0), Nh=(110, 130))

        exclusionBuffer: defines the size to extend the region by in index units, e.g. [1, 1, 1]
                            extends the region by 1 index point in all axes.
                            Default is 1 in all axis directions.

        :param exclusionBuffer: array of int
        :param axisDict: dict of axis limits
        :return: numpy data array
        """
        startPoint = []
        endPoint = []
        # spectrum = self.spectrum

        # fill with the spectrum limits first
        regionToPick = list(self.spectrumLimits)

        # insert axis regions into the limits list based on axisCode
        for axis, region in axisDict.items():
            for specAxis in self.axisCodes:
                mapAxis = axisCodeMapping([axis], [specAxis])
                if mapAxis:
                    regionToPick[self.axisCodes.index(mapAxis[axis])] = region
                    break
            else:
                raise ValueError('Invalid axis: %s' % axis)

        # convert the region limits to point coordinates with the dataSource
        dataDims = self._apiDataSource.sortedDataDims()
        aliasingLimits = self.aliasingLimits
        apiPeaks = []
        # for ii, dataDim in enumerate(dataDims):
        spectrumReferences = self.mainSpectrumReferences
        if None in spectrumReferences:
            raise ValueError("getRegionData() only works for Frequency dimensions"
                             " with defined primary SpectrumReferences ")
        if regionToPick is None:
            regionToPick = self.aliasingLimits

        for ii, spectrumReference in enumerate(spectrumReferences):
            aliasingLimit0, aliasingLimit1 = aliasingLimits[ii]
            value0 = regionToPick[ii][0]
            value1 = regionToPick[ii][1]
            value0, value1 = min(value0, value1), max(value0, value1)

            if value1 < aliasingLimit0 or value0 > aliasingLimit1:
                # completely outside limits
                break

            value0 = max(value0, aliasingLimit0)
            value1 = min(value1, aliasingLimit1)

            position0 = spectrumReference.valueToPoint(value0) - 1
            position1 = spectrumReference.valueToPoint(value1) - 1
            position0, position1 = min(position0, position1), max(position0, position1)

            # not always perfect for the plane depth region
            position0 = int(position0) + 1
            position1 = int(position1) + 1

            startPoint.append((spectrumReference.dimension, position0))
            endPoint.append((spectrumReference.dimension, position1))

        else:

            # this is a for..else, completes only if all limits are within spectrum bounds
            startPoints = [point[1] for point in sorted(startPoint)]
            endPoints = [point[1] for point in sorted(endPoint)]

            # originally from the PeakList dataSource which should be the same as the spectrum _apiDataSource
            # dataSource = self.dataSource
            dataSource = self._apiDataSource
            numDim = dataSource.numDim

            minLinewidth = [0.0] * numDim

            # if not exclusionBuffer:
            #     exclusionBuffer = [1] * numDim
            # else:
            #     if len(exclusionBuffer) != numDim:
            #         raise ValueError('Error: getRegionData, exclusion buffer length must match dimension of spectrum')
            #     for nDim in range(numDim):
            #         if exclusionBuffer[nDim] < 1:
            #             raise ValueError('Error: getRegionData, exclusion buffer must contain values >= 1')

            nonAdj = 0
            excludedRegions = []
            excludedDiagonalDims = []
            excludedDiagonalTransform = []

            startPoint = np.array(startPoints)
            endPoint = np.array(endPoints)
            startPoint, endPoint = np.minimum(startPoint, endPoint), np.maximum(startPoint, endPoint)

            if not exclusionBuffer:
                startPointBuffer = startPoint
                endPointBuffer = endPoint
            else:
                if len(exclusionBuffer) != numDim:
                    raise ValueError('Error: getRegionData, exclusion buffer length must match dimension of spectrum')
                for nDim in range(numDim):
                    if exclusionBuffer[nDim] < 0:
                        raise ValueError('Error: getRegionData, exclusion buffer must contain values >= 0')

                # extend region by exclusionBuffer
                bufferArray = np.array(exclusionBuffer)
                startPointBuffer = startPoint - bufferArray
                endPointBuffer = endPoint + bufferArray

            regions = numDim * [0]
            npts = numDim * [0]
            for n in range(numDim):
                start = startPointBuffer[n]
                end = endPointBuffer[n]
                npts[n] = dataSource.findFirstDataDim(dim=n + 1).numPointsOrig
                tile0 = start // npts[n]
                tile1 = (end - 1) // npts[n]
                region = regions[n] = []
                if tile0 == tile1:
                    region.append((start, end, tile0))
                else:
                    region.append((start, (tile0 + 1) * npts[n], tile0))
                    region.append((tile1 * npts[n], end, tile1))
                for tile in range(tile0 + 1, tile1):
                    region.append((tile * npts[n], (tile + 1) * npts[n], tile))

            peaks = []
            objectsCreated = []

            nregions = [len(region) for region in regions]

            # # force there to be only one region which is the central tile containing the spectrum
            # nregions = numDim * [1]

            nregionsTotal, cumulRegions = _cumulativeArray(nregions)

            # # allows there to be a repeating pattern of the spectrum tiled across the display
            result = ()
            for n in range(nregionsTotal):

                # fix to just the first tile
                # n = 0

                array = _arrayOfIndex(n, cumulRegions)
                chosenRegion = [regions[i][array[i]] for i in range(numDim)]
                startPointBufferActual = np.array([cr[0] for cr in chosenRegion])
                endPointBufferActual = np.array([cr[1] for cr in chosenRegion])
                tile = np.array([cr[2] for cr in chosenRegion])
                startPointBuffer = np.array([startPointBufferActual[i] - tile[i] * npts[i] for i in range(numDim)])
                endPointBuffer = np.array([endPointBufferActual[i] - tile[i] * npts[i] for i in range(numDim)])

                dataArray, intRegion = dataSource.getRegionData(startPointBuffer, endPointBuffer)

                # include extra exclusion buffer information
                startPointInt, endPointInt = intRegion
                startPointInt = np.array(startPointInt)
                endPointInt = np.array(endPointInt)
                startPointIntActual = np.array([startPointInt[i] + tile[i] * npts[i] for i in range(numDim)])
                numPointInt = endPointInt - startPointInt
                startPointBuffer = np.maximum(startPointBuffer, startPointInt)
                endPointBuffer = np.minimum(endPointBuffer, endPointInt)
                if np.any(numPointInt <= 2):  # return if any of the dimensions has <= 2 points
                    continue

                result += ((dataArray, intRegion,
                            startPoints, endPoints,
                            startPointBufferActual, endPointBufferActual,
                            startPointIntActual, numPointInt,
                            startPointBuffer, endPointBuffer),)

            return result  #dataArray, intRegion

        # for loop fails so return empty arrays in the first element
        return None

    def _getByValidAxisCodes(self, attributeName: str, axisCodes: Sequence[str] = None, exactMatch: bool = False):
        """Return values defined by attributeName in order defined by axisCodes :
           (default order if None)
            perform a mapping if exactMatch=False (eg. 'H' to 'Hn')
           NB: Use getByDimensions for dimensions (1..dimensionCount) based access
        """
        if not hasattr(self, attributeName):
            raise AttributeError('Spectrum object does not have attribute "%s"' % attributeName)

        mappings = []
        for ind, axis in enumerate(axisCodes):
            for specAxis in self.axisCodes:
                mapAxis = axisCodeMapping([axis], [specAxis])
                if mapAxis:
                    mappings.append(mapAxis[axis])  #[self.axisCodes.index(mapAxis[axis])] = ind
                    break
            else:
                # raise ValueError('Invalid axis: %s' % axis)
                pass

        values = getattr(self, attributeName)
        if mappings is not None:
            # change to order defined by axisCodes
            values = self._reorderValues(values, mappings)
        return values

    def getByAxisCodes(self, attributeName: str, axisCodes: Sequence[str] = None, exactMatch: bool = False):
        """Return values defined by attributeName in order defined by axisCodes:
        (default order if None).

        Perform a mapping if exactMatch=False (eg. 'H' to 'Hn')

        NB: Use getByDimensions for dimensions (1..dimensionCount) based access
        """
        if not hasattr(self, attributeName):
            raise AttributeError('Spectrum object does not have attribute "%s"' % attributeName)

        if axisCodes is not None and not exactMatch:
            axisCodes = self._mapAxisCodes(axisCodes)

        values = getattr(self, attributeName)
        if axisCodes is not None:
            # change to order defined by axisCodes
            values = self._reorderValues(values, axisCodes)
        return values

    def setByAxisCodes(self, attributeName: str, values: Sequence, axisCodes: Sequence[str] = None, exactMatch: bool = False):
        """Set attributeName to values in order defined by axisCodes:
        (default order if None)

        Perform a mapping if exactMatch=False (eg. 'H' to 'Hn')

        NB: Use setByDimensions for dimensions (1..dimensionCount) based access
        """
        if not hasattr(self, attributeName):
            raise AttributeError('Spectrum object does not have attribute "%s"' % attributeName)

        if axisCodes is not None and not exactMatch:
            axisCodes = self._mapAxisCodes(axisCodes)

        if axisCodes is not None:
            # change values to the order appropriate for spectrum
            values = self._reorderValues(values, axisCodes)
        setattr(self, attributeName, values)

    def getByDimensions(self, attributeName: str, dimensions: Sequence[int] = None):
        """Return values defined by attributeName in order defined by dimensions (1..dimensionCount).
           (default order if None)
           NB: Use getByAxisCodes for axisCode based access
        """
        if not hasattr(self, attributeName):
            raise AttributeError('Spectrum object does not have attribute "%s"' % attributeName)
        values = getattr(self, attributeName)

        if dimensions is None:
            return values

        newValues = []
        for dim in dimensions:
            if not (1 <= dim <= self.dimensionCount):
                raise ValueError('Invalid dimension "%d"; should be one of %s' % (dim, self.dimensions))
            else:
                newValues.append(values[dim - 1])
        return newValues

    def setByDimensions(self, attributeName: str, values: Sequence, dimensions: Sequence[int] = None):
        """Set attributeName to values in order defined by dimensions (1..dimensionCount).
           (default order if None)
           NB: Use setByAxisCodes for axisCode based access
        """
        if not hasattr(self, attributeName):
            raise AttributeError('Spectrum object does not have attribute "%s"' % attributeName)

        if dimensions is None:
            setattr(self, attributeName, values)
            return

        newValues = []
        for dim in dimensions:
            if not (1 <= dim <= self.dimensionCount):
                raise ValueError('Invalid dimension "%d"; should be one of %s' % (dim, self.dimensions))
            else:
                newValues.append(values[dim - 1])
        setattr(self, attributeName, newValues)

    def _clone1D(self):
        'Clone 1D spectrum to a new spectrum.'
        #FIXME Crude approach / hack

        newSpectrum = self.project.createDummySpectrum(name=self.name, axisCodes=self.axisCodes)
        newSpectrum._positions = self.positions
        newSpectrum._intensities = self.intensities
        for peakList in self.peakLists:
            peakList.copyTo(newSpectrum)

        import inspect

        attr = inspect.getmembers(self, lambda a: not (inspect.isroutine(a)))
        filteredAttr = [a for a in attr if not (a[0].startswith('__') and a[0].endswith('__')) and not a[0].startswith('_')]
        for i in filteredAttr:
            att, val = i
            try:
                setattr(newSpectrum, att, val)
            except Exception as e:
                # print(e, att)
                pass
        return newSpectrum

    @deleteObject()
    def _delete(self):
        """Delete the spectrum wrapped data.
        """
        self._wrappedData.delete()

    @cached.clear(PLANEDATACACHE)  # Check if there was a planedata cache, and if so, clear it
    @cached.clear(SLICEDATACACHE)  # Check if there was a slicedata cache, and if so, clear it
    def delete(self):
        """Delete Spectrum"""
        with logCommandBlock(get='self') as log:
            log('delete')

            # handle spectrumView ordering - this should be moved to spectrumView or spectrumDisplay via notifier?
            specDisplays = []
            specViews = []
            for sp in self.spectrumViews:
                if sp._parent.spectrumDisplay not in specDisplays:
                    specDisplays.append(sp._parent.spectrumDisplay)
                    specViews.append((sp._parent, sp._parent.spectrumViews.index(sp)))

            listsToDelete = tuple(self.peakLists)
            listsToDelete += tuple(self.integralLists)
            listsToDelete += tuple(self.multipletLists)

            # delete the connected lists, should undo in the correct order
            for obj in listsToDelete:
                obj.delete()

            with undoStackBlocking() as addUndoItem:
                # notify spectrumViews of delete/create
                addUndoItem(undo=partial(self._notifySpectrumViews, 'create'),
                            redo=partial(self._notifySpectrumViews, 'delete'))

            # delete the _wrappedData
            self._delete()

            # with undoStackBlocking() as addUndoItem:
            #     # notify spectrumViews of delete
            #     addUndoItem(redo=self._finaliseSpectrumViews, '')

            for sd in specViews:
                sd[0]._removeOrderedSpectrumViewIndex(sd[1])

    def _notifySpectrumViews(self, action):
        for sv in self.spectrumViews:
            sv._finaliseAction(action)

    @property
    def temperature(self):
        """The temperature of the spectrometer when the spectrum was recorded
        """
        if self._wrappedData.experiment:
            return self._wrappedData.experiment.temperature

    @temperature.setter
    def temperature(self, value):
        """The temperature of the spectrometer when the spectrum was recorded
        """
        if self._wrappedData.experiment:
            self._wrappedData.experiment.temperature = value

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Project) -> list:
        """get wrappedData (Nmr.DataSources) for all Spectrum children of parent Project"""
        return list(x for y in parent._wrappedData.sortedExperiments() for x in y.sortedDataSources())

    @logCommand(get='self')
    def rename(self, value: str):
        """Rename Spectrum, changing its name and Pid.
        """
        self._validateName(value=value, allowWhitespace=False)

        with renameObject(self) as addUndoItem:
            oldName = self.name
            self._wrappedData.name = value

            addUndoItem(undo=partial(self.rename, oldName),
                        redo=partial(self.rename, value))

    def _finaliseAction(self, action: str):
        """Subclassed to handle associated spectrumViews instances
        """
        super()._finaliseAction(action=action)
        # propagate the rename to associated spectrumViews
        if action in ['change']:
            for specView in self.spectrumViews:
                specView._finaliseAction(action=action)
        if action in ['create', 'delete']:
            for peakList in self.peakLists:
                peakList._finaliseAction(action=action)

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    #===========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================

    @logCommand(get='self')
    def newPeakList(self, title: str = None, comment: str = None,
                    isSimulated: bool = False, symbolStyle: str = None, symbolColour: str = None,
                    textColour: str = None, **kwds):
        """Create new empty PeakList within Spectrum

        See the PeakList class for details.

        Optional keyword arguments can be passed in; see PeakList._newPeakList for details.

        :param title:
        :param comment:
        :param isSimulated:
        :param symbolStyle:
        :param symbolColour:
        :param textColour:
        :return: a new PeakList attached to the spectrum.
        """
        from ccpn.core.PeakList import _newPeakList

        return _newPeakList(self, title=title, comment=comment, isSimulated=isSimulated,
                            symbolStyle=symbolStyle, symbolColour=symbolColour, textColour=textColour,
                            **kwds)

    @logCommand(get='self')
    def newIntegralList(self, title: str = None, symbolColour: str = None,
                        textColour: str = None, comment: str = None, **kwds):
        """Create new IntegralList within Spectrum.

        See the IntegralList class for details.

        Optional keyword arguments can be passed in; see IntegralList._newIntegralList for details.

        :param self:
        :param title:
        :param symbolColour:
        :param textColour:
        :param comment:
        :return: a new IntegralList attached to the spectrum.
        """
        from ccpn.core.IntegralList import _newIntegralList

        return _newIntegralList(self, title=title, comment=comment,
                                symbolColour=symbolColour, textColour=textColour,
                                **kwds)

    @logCommand(get='self')
    def newMultipletList(self, title: str = None,
                         symbolColour: str = None, textColour: str = None, lineColour: str = None,
                         multipletAveraging=0,
                         comment: str = None, multiplets: ['Multiplet'] = None, **kwds):
        """Create new MultipletList within Spectrum

        See the MultipletList class for details.

        Optional keyword arguments can be passed in; see MultipletList._newMultipletList for details.

        :param self:
        :param title:
        :param symbolColour:
        :param textColour:
        :param lineColour:
        :param multipletAveraging:
        :param comment:
        :param multiplets:
        :return: a new MultipletList attached to the Spectrum.
        """
        from ccpn.core.MultipletList import _newMultipletList

        return _newMultipletList(self, title=title, comment=comment,
                                 lineColour=lineColour, symbolColour=symbolColour, textColour=textColour,
                                 multipletAveraging=multipletAveraging,
                                 multiplets=multiplets,
                                 **kwds)

    @logCommand(get='self')
    def newSpectrumHit(self, substanceName: str, pointNumber: int = 0,
                       pseudoDimensionNumber: int = 0, pseudoDimension=None,
                       figureOfMerit: float = None, meritCode: str = None, normalisedChange: float = None,
                       isConfirmed: bool = None, concentration: float = None, concentrationError: float = None,
                       concentrationUnit: str = None, comment: str = None, **kwds):
        """Create new SpectrumHit within Spectrum.

        See the SpectrumHit class for details.

        Optional keyword arguments can be passed in; see SpectrumHit._newSpectrumHit for details.

        :param substanceName:
        :param pointNumber:
        :param pseudoDimensionNumber:
        :param pseudoDimension:
        :param figureOfMerit:
        :param meritCode:
        :param normalisedChange:
        :param isConfirmed:
        :param concentration:
        :param concentrationError:
        :param concentrationUnit:
        :param comment: optional comment string
        :return: a new SpectrumHit instance.
        """
        from ccpn.core.SpectrumHit import _newSpectrumHit

        return _newSpectrumHit(self, substanceName=substanceName, pointNumber=pointNumber,
                               pseudoDimensionNumber=pseudoDimensionNumber, pseudoDimension=pseudoDimension,
                               figureOfMerit=figureOfMerit, meritCode=meritCode, normalisedChange=normalisedChange,
                               isConfirmed=isConfirmed, concentration=concentration, concentrationError=concentrationError,
                               concentrationUnit=concentrationUnit, comment=comment, **kwds)

    @logCommand(get='self')
    def newSpectrumReference(self, dimension: int, spectrometerFrequency: float,
                             isotopeCodes: Sequence[str], axisCode: str = None, measurementType: str = 'Shift',
                             maxAliasedFrequency: float = None, minAliasedFrequency: float = None,
                             foldingMode: str = None, axisUnit: str = None, referencePoint: float = 0.0,
                             referenceValue: float = 0.0, **kwds):
        """Create new SpectrumReference.

        See the SpectrumReference class for details.

        Optional keyword arguments can be passed in; see SpectrumReference._newSpectrumReference for details.

        :param dimension:
        :param spectrometerFrequency:
        :param isotopeCodes:
        :param axisCode:
        :param measurementType:
        :param maxAliasedFrequency:
        :param minAliasedFrequency:
        :param foldingMode:
        :param axisUnit:
        :param referencePoint:
        :param referenceValue:
        :return: a new SpectrumReference instance.
        """
        from ccpn.core.SpectrumReference import _newSpectrumReference

        return _newSpectrumReference(self, dimension=dimension, spectrometerFrequency=spectrometerFrequency,
                                     isotopeCodes=isotopeCodes, axisCode=axisCode, measurementType=measurementType,
                                     maxAliasedFrequency=maxAliasedFrequency, minAliasedFrequency=minAliasedFrequency,
                                     foldingMode=foldingMode, axisUnit=axisUnit, referencePoint=referencePoint,
                                     referenceValue=referenceValue, **kwds)


#=========================================================================================
# Connections to parents:
#=========================================================================================

@newObject(Spectrum)
def _newSpectrum(self: Project, name: str, serial: int = None) -> Spectrum:
    """Creation of new Spectrum NOT IMPLEMENTED.
    Use Project.loadData or Project.createDummySpectrum instead"""

    raise NotImplementedError("Not implemented. Use loadSpectrum instead")


@newObject(Spectrum)
def _createDummySpectrum(self: Project, axisCodes: Sequence[str], name=None,
                         chemicalShiftList=None, serial: int = None) -> Spectrum:
    """Make dummy Spectrum from isotopeCodes list - without data and with default parameters.

    See the Spectrum class for details.

    :param self:
    :param axisCodes:
    :param name:
    :param chemicalShiftList:
    :return: a new Spectrum instance.
    """
    # TODO - change so isotopeCodes can be passed in instead of axisCodes

    apiShiftList = chemicalShiftList._wrappedData if chemicalShiftList else None

    if name:
        if Pid.altCharacter in name:
            raise ValueError("Character %s not allowed in ccpn.Spectrum.name" % Pid.altCharacter)

    apiSpectrum = self._wrappedData.createDummySpectrum(axisCodes, name=name,
                                                        shiftList=apiShiftList)
    result = self._project._data2Obj[apiSpectrum]
    if result is None:
        raise RuntimeError('Unable to generate new Spectrum item')

    # newly created spectra require a peaklist
    if not result.peakLists:
        result.newPeakList()

    return result


# EJB 20181130: not sure what do with this...
# EJB 20181210: Moved to Project.loadSpectrum, and _createDummySpectrum
# def _spectrumMakeFirstPeakList(project: Project, dataSource: Nmr.DataSource):
#     """Add PeakList if none is present - also IntegralList for 1D. For notifiers."""
#     if not dataSource.findFirstPeakList(dataType='Peak'):
#         dataSource.newPeakList()
#
#
# Project._setupApiNotifier(_spectrumMakeFirstPeakList, Nmr.DataSource, 'postInit')
# del _spectrumMakeFirstPeakList

# Connections to parents:

# EJB 20181128: moved to Project
# Project.newSpectrum = _newSpectrum
# del _newSpectrum
# Project.createDummySpectrum = _createDummySpectrum
# del _createDummySpectrum

# Additional Notifiers:
Project._apiNotifiers.extend(
        (
            ('_finaliseApiRename', {}, Nmr.DataSource._metaclass.qualifiedName(), 'setName'),
            ('_notifyRelatedApiObject', {'pathToObject': 'dataSources', 'action': 'change'},
             Nmr.Experiment._metaclass.qualifiedName(), ''),
            ('_notifyRelatedApiObject', {'pathToObject': 'dataSource', 'action': 'change'},
             Nmr.AbstractDataDim._metaclass.qualifiedName(), ''),
            ('_notifyRelatedApiObject', {'pathToObject': 'dataDim.dataSource', 'action': 'change'},
             Nmr.DataDimRef._metaclass.qualifiedName(), ''),
            ('_notifyRelatedApiObject', {'pathToObject': 'experiment.dataSources', 'action': 'change'},
             Nmr.ExpDim._metaclass.qualifiedName(), ''),
            ('_notifyRelatedApiObject', {'pathToObject': 'expDim.experiment.dataSources', 'action': 'change'},
             Nmr.ExpDimRef._metaclass.qualifiedName(), ''),
            ('_notifyRelatedApiObject', {'pathToObject': 'nmrDataSources', 'action': 'change'},
             DataLocation.AbstractDataStore._metaclass.qualifiedName(), ''),
            )
        )
