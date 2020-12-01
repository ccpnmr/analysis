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

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
from ccpnmodel.ccpncore.lib.spectrum.Spectrum import createBlockedMatrix

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
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
import os
import sys
from typing import Sequence, Tuple, Optional, Union
from functools import partial

import numpy


from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
from ccpnmodel.ccpncore.api.ccp.general import DataLocation
# Dimensions
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import FidDataDim as ApiFidDataDim
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import FreqDataDim as ApiFreqDataDim
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import SampledDataDim as ApiSampledDataDim

from ccpnmodel.ccpncore.lib.Io import Formats


from ccpn.framework import constants
from ccpn.framework.constants import CCPNMR_PREFIX

from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project

from ccpn.core.lib import Pid
from ccpn.core.lib.SpectrumLib import MagnetisationTransferTuple, _getProjection, \
                                      setContourLevelsFromNoise, getDefaultSpectrumColours
from ccpn.core.lib.Cache import cached
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, deleteObject, \
                                          undoStackBlocking, renameObject, undoBlock, notificationBlanking, \
                                          apiNotificationBlanking, ccpNmrV3CoreSetter, notificationEchoBlocking
from ccpn.core.lib.DataStore import DataStore
from ccpn.core.lib.Notifiers import Notifier

# 2019010:ED test new matching
# from ccpn.util.Common import axisCodeMapping
from ccpn.util.Common import getAxisCodeMatch as axisCodeMapping
from ccpn.util import Constants, Common
from ccpn.util.Logging import getLogger
from ccpn.util.Common import getAxisCodeMatchIndices
from ccpn.util.Path import Path, aPath
from ccpn.util.Common import isIterable



DIMENSIONFID = 'Fid'
DIMENSIONFREQUENCY = 'Frequency'
DIMENSIONFREQ = 'Freq'
DIMENSIONSAMPLED = 'Sampled'
DIMENSIONTYPES = [DIMENSIONFID, DIMENSIONFREQUENCY, DIMENSIONSAMPLED]
_DIMENSIONCLASSES = {DIMENSIONFID: ApiFidDataDim, DIMENSIONFREQUENCY: ApiFreqDataDim, DIMENSIONSAMPLED: ApiSampledDataDim}


INCLUDEPOSITIVECONTOURS = 'includePositiveContours'
INCLUDENEGATIVECONTOURS = 'includeNegativeContours'
SPECTRUMAXES = 'spectrumAxesOrdering'
SPECTRUMPREFERREDAXISORDERING = 'spectrumPreferredAxisOrdering'
SPECTRUMALIASING = 'spectrumAliasing'
VISIBLEALIASINGRANGE = 'visibleAliasingRange'
ALIASINGRANGE = 'aliasingRange'
UPDATEALIASINGRANGEFLAG = '_updateAliasingRangeFlag'
EXTENDALIASINGRANGEFLAG = 'extendAliasingRangeFlag'
DISPLAYFOLDEDCONTOURS = 'displayFoldedContours'
MAXALIASINGRANGE = 3
SPECTRUMSERIES = 'spectrumSeries'
SPECTRUMSERIESVALUES = 'spectrumSeriesValues'



def _cumulativeArray(array):
    """ get total size and strides array.
        NB assumes fastest moving index first
    """
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


#=========================================================================================
# Decorators to define the attributes to be copied
#=========================================================================================

import decorator
from ccpn.util.decorators import singleton

@singleton
class _includeInCopyList(list):
    """Singleton class to store the attributes to be included when making a copy of object.
    Attributes can be modified and can be either non-dimensional or dimension dependent,
    Dynamically filled by two decorators
    Stored as list of (attributeName, isMultiDimensional) tuples
    """

    def getNoneDimensional(self):
        "return a list of one-dimensional attribute names"
        return [attr for attr, isNd in self if isNd == False]

    def getMultiDimensional(self):
        "return a list of one-dimensional attribute names"
        return [attr for attr, isNd in self if isNd == True]

    def append(self, attribute, isMultidimensional):
        _t = (attribute, isMultidimensional)
        if _t not in self:
            super().append(_t)


def _includeInCopy(func):
    """Decorator to define that an non-dimensional attribute is to be included when making a copy of object
    """
    storage = _includeInCopyList()
    storage.append(func.__name__, False)
    return func


def _includeInDimensionalCopy(func):
    """Decorator to define that a dimensional attribute is to be included when making a copy of object
    """
    storage = _includeInCopyList()
    storage.append(func.__name__, True)
    return func


#=========================================================================================
# Spectrum class
#=========================================================================================

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

    # Internal NameSpace
    _AdditionalAttribute = 'AdditionalAttribute'

    _referenceSpectrumHit = None
    _snr = None

    MAXDIM = 8  # Maximum dimensionality

    _PLANEDATACACHE = '_planeDataCache'  # Attribute name for the planeData cache
    _SLICEDATACACHE = '_sliceDataCache'  # Attribute name for the slicedata cache
    _SLICE1DDATACACHE = '_slice1DDataCache'  # Attribute name for the 1D slicedata cache
    _REGIONDATACACHE = '_regionDataCache'  # Attribute name for the regionData cache
    _dataCaches = [_PLANEDATACACHE, _SLICEDATACACHE, _SLICE1DDATACACHE, _REGIONDATACACHE]

    _DATASTORE_KEY = '_dataStore'    # Key for storing the dataStore info in the Ccpn internal parameter store of the
                                    # Spectrum instance

    def __init__(self, project: Project, wrappedData: Nmr.DataSource):

        super().__init__(project, wrappedData)

        # 1D data references
        self._intensities = None
        self._positions = None

        # References to DataStore / DataSource instances for filePath manipulation and data reading;
        self._dataStore = None
        self._dataSource = None

        self.doubleCrosshairOffsets = self.dimensionCount * [0]  # TBD: do we need this to be a property?
        self.showDoubleCrosshair = False

        # GWV: This does not work (yet!?), as de __init__ is called by callbacks from the api before the children are
        #      restored, resulting in multiplication
        # with notificationBlanking():
        #     # Assure at least one peakList
        #     if len(self.peakLists) == 0:
        #         self.newPeakList()

    @classmethod
    def _restoreObject(cls, project, apiObj):
        "Subclassed to allow for initialisations on restore, not on creation vis newSpectrum"

        spectrum = super()._restoreObject(project, apiObj)

        spectrum._dataStore = DataStore(spectrum=spectrum)
        spectrum._dataSource = spectrum._getDataSource(spectrum._dataStore, reportWarnings=True)

        return spectrum

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
        """Local sorting key, in context of parent.
        """
        return (self._wrappedData.experiment.serial, self._wrappedData.serial)

    @property
    def name(self) -> str:
        """short form of name, used for id"""
        return self._wrappedData.name

    @name.setter
    def name(self, value: str):
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

    @property
    def comment(self) -> str:
        """Free-form text comment"""
        return self._wrappedData.details

    @comment.setter
    def comment(self, value: str):
        self._wrappedData.details = value

    @property
    @_includeInCopy
    def positiveContourCount(self) -> int:
        """number of positive contours to draw"""
        return self._wrappedData.positiveContourCount

    @positiveContourCount.setter
    def positiveContourCount(self, value):
        self._wrappedData.positiveContourCount = value

    @property
    @_includeInCopy
    def positiveContourBase(self) -> float:
        """base level of positive contours"""
        return self._wrappedData.positiveContourBase

    @positiveContourBase.setter
    def positiveContourBase(self, value):
        self._wrappedData.positiveContourBase = value

    @property
    @_includeInCopy
    def positiveContourFactor(self) -> float:
        """level multiplier for positive contours"""
        return self._wrappedData.positiveContourFactor

    @positiveContourFactor.setter
    def positiveContourFactor(self, value):
        self._wrappedData.positiveContourFactor = value

    @property
    @_includeInCopy
    def positiveContourColour(self) -> str:
        """colour of positive contours"""
        return self._wrappedData.positiveContourColour

    @positiveContourColour.setter
    def positiveContourColour(self, value):
        self._wrappedData.positiveContourColour = value

    @property
    @_includeInCopy
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
    @_includeInCopy
    def negativeContourCount(self) -> int:
        """number of negative contours to draw"""
        return self._wrappedData.negativeContourCount

    @negativeContourCount.setter
    def negativeContourCount(self, value):
        self._wrappedData.negativeContourCount = value

    @property
    @_includeInCopy
    def negativeContourBase(self) -> float:
        """base level of negative contours"""
        return self._wrappedData.negativeContourBase

    @negativeContourBase.setter
    def negativeContourBase(self, value):
        self._wrappedData.negativeContourBase = value

    @property
    @_includeInCopy
    def negativeContourFactor(self) -> float:
        """level multiplier for negative contours"""
        return self._wrappedData.negativeContourFactor

    @negativeContourFactor.setter
    def negativeContourFactor(self, value):
        self._wrappedData.negativeContourFactor = value

    @property
    @_includeInCopy
    def negativeContourColour(self) -> str:
        """colour of negative contours"""
        return self._wrappedData.negativeContourColour

    @negativeContourColour.setter
    def negativeContourColour(self, value):
        self._wrappedData.negativeContourColour = value

    @property
    @_includeInCopy
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

    def _setContourDefaultValues(self, base=None, multiplier=1.3, count=10):
        """Set some default values and colours for contours
        """
        if base is None:
            base = self.noiseLevel *1.5
        self.positiveContourBase = base
        self.positiveContourFactor = 1.3
        self.positiveContourCount = 10
        self.negativeContourBase = -1.0 * base
        self.negativeContourFactor = 1.3
        self.negativeContourCount = 10
        (self.positiveContourColour, self.negativeContourColour) = getDefaultSpectrumColours(self)

    @property
    @_includeInCopy
    def sliceColour(self) -> str:
        """colour of 1D slices"""
        return self._wrappedData.sliceColour

    @sliceColour.setter
    def sliceColour(self, value):
        self._wrappedData.sliceColour = value
        # for spectrumView in self.spectrumViews:
        #     spectrumView.setSliceColour()  # ejb - update colour here

    @property
    @_includeInCopy
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
    @_includeInCopy
    def spinningRate(self) -> float:
        """NMR tube spinning rate (in Hz)."""
        return self._wrappedData.experiment.spinningRate

    @spinningRate.setter
    def spinningRate(self, value: float):
        self._wrappedData.experiment.spinningRate = value

    @property
    @_includeInCopy
    def noiseLevel(self) -> float:
        """Estimated noise level for the spectrum,
        defined as the estimated standard deviation of the points from the baseplane/baseline
        """
        noise = self._wrappedData.noiseLevel
        if noise is None:
            noise = self.estimateNoise()
            self._wrappedData.noiseLevel = noise
        return noise

    @noiseLevel.setter
    def noiseLevel(self, value: float):
        self._wrappedData.noiseLevel = value

    @property
    @_includeInCopy
    def negativeNoiseLevel(self) -> float:
        """ Negative noise level value. Stored in Internal"""
        propertyName = sys._getframe().f_code.co_name
        value = self.getParameter(self._AdditionalAttribute, propertyName)
        return value

    @negativeNoiseLevel.setter
    def negativeNoiseLevel(self, value):
        """Stored in Internal """
        propertyName = sys._getframe().f_code.co_name
        self.setParameter(self._AdditionalAttribute, propertyName, value)

    @property
    def synonym(self) -> str:
        """Systematic experiment type descriptor (CCPN system)."""
        refExperiment = self._wrappedData.experiment.refExperiment
        if refExperiment is None:
            return None
        else:
            return refExperiment.synonym

    @property
    @_includeInCopy
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

    # @property
    # def _numDim(self):
    #     """Return the _wrappedData numDim
    #     CCPN Internal
    #     """
    #     return self._wrappedData.numDim

    @property
    def experiment(self):
        """Return the experiment assigned to the spectrum
        """
        return self._wrappedData.experiment

    @property
    @_includeInCopy
    def experimentName(self) -> str:
        """Common experiment type descriptor (May not be unique).
        """
        return self._wrappedData.experiment.name

    @experimentName.setter
    def experimentName(self, value):
        # force to a string
        # because: reading from .nef files extracts the name from the end of the experiment_type in nef reader
        #           which is not wrapped with quotes, so defaults to an int if it can?
        self._wrappedData.experiment.name = str(value)

    def _getDataSource(self, dataStore, reportWarnings=False):
        """Check the validity of the file defined by dataStore;
        returns DataSource instance or None when filePath and/or dataFormat of the dataStore instance are incorrect
        Optionally report warnings
        """
        from sandbox.Geerten.SpectrumDataSources.SpectrumDataSourceABC import getSpectrumDataSource
        from sandbox.Geerten.SpectrumDataSources.EmptySpectrumDataSource import EmptySpectrumDataSource

        if dataStore is None:
            raise RuntimeError('dataStore not defined')

        if dataStore.dataFormat == EmptySpectrumDataSource.dataFormat:
            # Special case, empty spectrum
            dataSource = EmptySpectrumDataSource(spectrum=self)

        else:
            if not dataStore.exists():
                if reportWarnings:
                    dataStore.warningMessage()
                return None
            dataSource = getSpectrumDataSource(dataStore.aPath(), dataStore.dataFormat)

        if dataSource is None and reportWarnings:
            getLogger().warning('data format "%s" is incompatible with path "%s"' %
                                (dataStore.dataFormat, dataStore.path))

        return dataSource

    @property
    def filePath(self) -> Optional[str]:
        """Path to NMR data file; can contain redirections (e.g. $DATA)
        """
        if self._dataStore is None:
            raise RuntimeError('dataStore not defined')
        return str(self._dataStore.path)

    @filePath.setter
    @ccpNmrV3CoreSetter()
    def filePath(self, value: str):

        if self._dataStore is None:
            raise RuntimeError('dataStore not defined')
        if value is None:
            self._dataStore.path = None
            self._dataSource = None
            self._clearCache()
            return

        oldPath = self._dataStore.path
        self._dataStore.path = value
        if not self._dataStore.exists():
            self._dataStore.errorMessage()
            self._dataStore.path = oldPath
            raise ValueError('Setting Spectrum.filePath to "%s"' % value)

        newDataSource = self._getDataSource(self._dataStore, reportWarnings=True)
        if newDataSource is None:
            self._dataStore.path = oldPath
            raise ValueError('Spectrum.filePath: incompatible "%s"' % value)

        else:
            # check some fundamental parameters
            # check dataFormat
            if newDataSource.dataFormat != self.dataFormat:
                raise ValueError('Spectrum.filePath: incompatible dataFormat (%s) of "%s"' %
                                 (newDataSource.dataFormat,value))

            if self.dimensionCount != newDataSource.dimensionCount:
                self._dataStore.path = oldPath
                raise ValueError('Spectrum.filePath: incompatible dimensionCount = %s of "%s"' %
                                 (newDataSource.dimensionCount,value))

            for idx, np in enumerate(self.pointCounts):
                if newDataSource.pointCounts[idx] != np:
                    self._dataStore.path = oldPath
                    raise ValueError('Spectrum.filePath: incompatible pointsCount[%s] = %s of "%s"' %
                                     (idx, newDataSource.pointCounts[idx], value))

        self._dataSource = newDataSource
        self._dataStore._saveInternal()
        self._clearCache()

    @property
    def path(self):
        """return a Path instance defining the absolute path of filePath
        """
        if self._dataStore is None:
            raise RuntimeError('dataStore not defined')
        return self._dataStore.aPath()

    def hasValidPath(self) -> bool:
        """Return true if the spectrum currently points to an valid dataSource object.
        """
        return (self._dataSource is not None)

    def isEmptySpectrum(self):
        """Return True if instance refers to an empty spectrum; i.e. as in without actual spectral data"
        """
        # local import to avoid cycles
        from sandbox.Geerten.SpectrumDataSources.EmptySpectrumDataSource import EmptySpectrumDataSource
        if self._dataStore is None:
            raise RuntimeError('dataStore not defined')
        return self._dataStore.dataFormat == EmptySpectrumDataSource.dataFormat

    @property
    def dataFormat(self):
        """Return the spectrum data-format identifier (e.g. HDF5, NMRPipe)
        """
        if self._dataStore is None:
            raise RuntimeError('dataStore not defined')

        return self._dataStore.dataFormat

        # if self._wrappedData is None or self._wrappedData.dataStore is None:
        #     return None
        # return self._wrappedData.dataStore.fileType

    # @dataFormat.setter
    # def dataFormat(self, value):
    #     self._wrappedData.dataStore.fileType = value

    # @property
    # def headerSize(self) -> Optional[int]:
    #     """File header size in bytes."""
    #     xx = self._wrappedData.dataStore
    #     if xx:
    #         return xx.headerSize
    #     else:
    #         return None
    #
    # @property
    # def numberType(self) -> Optional[str]:
    #     """Data type of numbers stored in data matrix ('int' or 'float')."""
    #     xx = self._wrappedData.dataStore
    #     if xx:
    #         return xx.numberType
    #     else:
    #         return None
    #
    # # NBNB TBD Should this be made modifiable? Would be a bit of work ...
    #
    # @property
    # def complexStoredBy(self) -> str:
    #     """Hypercomplex numbers are stored by ('timepoint', 'quadrant', or 'dimension')."""
    #     xx = self._wrappedData.dataStore
    #     if xx:
    #         return xx.complexStoredBy
    #     else:
    #         return None
    #
    # # NBNB TBD Should this be made modifiable? Would be a bit of work ...

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
    @_includeInDimensionalCopy
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
    @_includeInDimensionalCopy
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
    @_includeInDimensionalCopy
    def totalPointCounts(self) -> Tuple[int, ...]:
        """Total number of points per dimension

        NB for FidDataDims and SampledDataDims these are the stored points,
        for FreqDataDims these are the points after transformation before cutting down.

        NB, changing the totalPointCount will *not* modify the resolution (or dwell time),
        so the implied total width will change.
        """
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

    # @property
    # @_includeInDimensionalCopy
    # def pointOffsets(self) -> Tuple[int, ...]:
    #     """index of first active point relative to total points, per dimension"""
    #     return tuple(x.pointOffset if x.className != 'SampledDataDim' else None
    #                  for x in self._wrappedData.sortedDataDims())
    #
    # @pointOffsets.setter
    # def pointOffsets(self, value: Sequence):
    #     self._setStdDataDimValue('pointOffset', value)

    @property
    @_includeInDimensionalCopy
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

    #TODO: add setter for dimensionTypes
    @property
    def dimensionTypes(self) -> Tuple[str, ...]:
        """dimension types ('Fid' / 'Frequency' / 'Sampled'),  per dimension
        """
        ll = [x.className[:-7] for x in self._wrappedData.sortedDataDims()]
        return tuple(DIMENSIONFREQUENCY if x == DIMENSIONFREQ else x for x in ll)

    # @dimensionTypes.setter
    # def dimensionTypes(self, value: Sequence):
    #
    #     if len(value) != self.dimensionCount:
    #         raise ValueError("DimensionTypes must have length %s, was %s" % (self.dimensionCount, value))
    #
    #     for dimType in value:
    #         if dimType not in DIMENSIONTYPES:
    #             raise ValueError("DimensionType %s not recognised" % dimType)
    #
    #     values = [i for i in zip(self.pointCounts, self.pointOffsets, self.isComplex, self.valuesPerPoint)]
    #
    #     for n, dataDimVal in enumerate(self._wrappedData.sortedDataDims()):
    #         pass

    @property
    @_includeInDimensionalCopy
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
    @_includeInDimensionalCopy
    def phases0(self) -> tuple:
        """zero order phase correction (or None), per dimension. Always None for sampled dimensions."""
        return tuple(x.phase0 if x.className != 'SampledDataDim' else None
                     for x in self._wrappedData.sortedDataDims())

    @phases0.setter
    def phases0(self, value: Sequence):
        self._setStdDataDimValue('phase0', value)

    @property
    @_includeInDimensionalCopy
    def phases1(self) -> Tuple[Optional[float], ...]:
        """first order phase correction (or None) per dimension. Always None for sampled dimensions."""
        return tuple(x.phase1 if x.className != 'SampledDataDim' else None
                     for x in self._wrappedData.sortedDataDims())

    @phases1.setter
    def phases1(self, value: Sequence):
        self._setStdDataDimValue('phase1', value)

    @property
    @_includeInDimensionalCopy
    def windowFunctions(self) -> Tuple[Optional[str], ...]:
        """Window function name (or None) per dimension - e.g. 'EM', 'GM', 'SINE', 'QSINE', ....
        Always None for sampled dimensions."""
        return tuple(x.windowFunction if x.className != 'SampledDataDim' else None
                     for x in self._wrappedData.sortedDataDims())

    @windowFunctions.setter
    def windowFunctions(self, value: Sequence):
        self._setStdDataDimValue('windowFunction', value)

    @property
    @_includeInDimensionalCopy
    def lorentzianBroadenings(self) -> Tuple[Optional[float], ...]:
        """Lorenzian broadening in Hz per dimension. Always None for sampled dimensions."""
        return tuple(x.lorentzianBroadening if x.className != 'SampledDataDim' else None
                     for x in self._wrappedData.sortedDataDims())

    @lorentzianBroadenings.setter
    def lorentzianBroadenings(self, value: Sequence):
        self._setStdDataDimValue('lorentzianBroadening', value)

    @property
    @_includeInDimensionalCopy
    def gaussianBroadenings(self) -> Tuple[Optional[float], ...]:
        """Gaussian broadening per dimension. Always None for sampled dimensions."""
        return tuple(x.gaussianBroadening if x.className != 'SampledDataDim' else None
                     for x in self._wrappedData.sortedDataDims())

    @gaussianBroadenings.setter
    def gaussianBroadenings(self, value: Sequence):
        self._setStdDataDimValue('gaussianBroadening', value)

    @property
    @_includeInDimensionalCopy
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
    @_includeInDimensionalCopy
    def spectrometerFrequencies(self) -> Tuple[Optional[float], ...]:
        """Tuple of spectrometer frequency for main dimensions reference """
        return tuple(x and x.sf for x in self._mainExpDimRefs())

    @spectrometerFrequencies.setter
    def spectrometerFrequencies(self, value):
        self._setExpDimRefAttribute('sf', value)

    @property
    @_includeInDimensionalCopy
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
    @_includeInDimensionalCopy
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
    @_includeInDimensionalCopy
    def foldingModes(self) -> Tuple[Optional[str], ...]:
        """folding mode (values: 'circular', 'mirror', None), per dimension"""
        dd = {True: 'mirror', False: 'circular', None: None}
        return tuple(dd[x and x.isFolded] for x in self._mainExpDimRefs())

    @foldingModes.setter
    def foldingModes(self, values):

        # TODO For NEF we should support both True, False, and None
        # That requires an API change

        dd = {'circular': False, 'mirror': True, None: False}

        if len(values) != self.dimensionCount:
            raise ValueError("Length of %s does not match number of dimensions." % str(values))
        if not all(isinstance(dimVal, str) and dimVal in dd.keys() for dimVal in values):
            raise ValueError("Folding modes must be 'circular', 'mirror'")

        self._setExpDimRefAttribute('isFolded', [dd[x] for x in values])

    @property
    @_includeInCopy
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
    @_includeInDimensionalCopy
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
    @_includeInDimensionalCopy
    def referencePoints(self) -> Tuple[Optional[float], ...]:
        """point used for axis (chemical shift) referencing, per dimension."""
        return tuple(x and x.refPoint for x in self._mainDataDimRefs())

    @referencePoints.setter
    def referencePoints(self, value):
        self._setDataDimRefAttribute('refPoint', value)

    @property
    @_includeInDimensionalCopy
    def referenceValues(self) -> Tuple[Optional[float], ...]:
        """value used for axis (chemical shift) referencing, per dimension."""
        return tuple(x and x.refValue for x in self._mainDataDimRefs())

    @referenceValues.setter
    def referenceValues(self, value):
        self._setDataDimRefAttribute('refValue', value)

    @property
    @_includeInDimensionalCopy
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
    @_includeInDimensionalCopy
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
    @_includeInDimensionalCopy
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
            getLogger().warn('Currently this method only works for 1D spectra')
            return np.array([])

        if self._intensities is None:
            self._intensities = self.getSliceData()  # Assignment is Redundant as getSliceData does that;

            # Nevertheless for clarity
            if self._intensities is None:
                getLogger().warning('Unable to get 1D slice data for %s' % self)
                return np.array([])
        return self._intensities

    @intensities.setter
    def intensities(self, value: np.ndarray):
        self._intensities = value
        # temporary hack for showing straight the result of intensities change
        for spectrumView in self.spectrumViews:
            spectrumView.refreshData()

    @property
    def positions(self) -> np.array:
        """ spectral region in ppm as NumPy array for 1D spectra """

        if self.dimensionCount != 1:
            getLogger().warn('Currently this method only works for 1D spectra')
            return np.array([])

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

    @property
    @_includeInCopy
    def displayFoldedContours(self):
        """Return whether the folded spectrum contours are to be displayed
        """
        alias = self.getParameter(SPECTRUMALIASING, DISPLAYFOLDEDCONTOURS)
        if alias is not None:
            return alias

        # set default values in the ccpnInternal store
        alias = True

        # don't need to notify this - it can be set every time if needed
        with notificationBlanking():
            self.setParameter(SPECTRUMALIASING, DISPLAYFOLDEDCONTOURS, alias)
        return alias

    @displayFoldedContours.setter
    def displayFoldedContours(self, value):
        """Set whether the folded spectrum contours are to be displayed
        """
        if not isinstance(value, bool):
            raise ValueError("displayFoldedContours must be True/False.")

        self.setParameter(SPECTRUMALIASING, DISPLAYFOLDEDCONTOURS, value)

    @property
    def _updateAliasingRangeFlag(self):
        """Return whether the aliasingRange needs to be updated when aliasing
        of peaks has changed - from spectrumProperties popup
        """
        alias = self.getParameter(SPECTRUMALIASING, UPDATEALIASINGRANGEFLAG)
        if alias is not None:
            return alias

        # set default values in the ccpnInternal store
        alias = True

        # don't need to notify this - it can be set every time if needed
        with notificationBlanking():
            self.setParameter(SPECTRUMALIASING, UPDATEALIASINGRANGEFLAG, alias)
        return alias

    @_updateAliasingRangeFlag.setter
    def _updateAliasingRangeFlag(self, value):
        """Set whether the aliasingRange needs to be updated when aliasing
        of peaks has changed
        """
        if not isinstance(value, bool):
            raise ValueError("_updateAliasingRangeFlag must be True/False.")

        self.setParameter(SPECTRUMALIASING, UPDATEALIASINGRANGEFLAG, value)

    @property
    def extendAliasingRangeFlag(self):
        """Return whether the aliasingRange needs to be extended when aliasing
        of peaks has changed - from spectrumProperties popup
        """
        alias = self.getParameter(SPECTRUMALIASING, EXTENDALIASINGRANGEFLAG)
        if alias is not None:
            return alias

        # set default values in the ccpnInternal store
        alias = True

        # don't need to notify this - it can be set every time if needed
        with notificationBlanking():
            self.setParameter(SPECTRUMALIASING, EXTENDALIASINGRANGEFLAG, alias)
        return alias

    @extendAliasingRangeFlag.setter
    def extendAliasingRangeFlag(self, value):
        """Set whether the aliasingRange needs to be extendd when aliasing
        of peaks has changed
        """
        if not isinstance(value, bool):
            raise ValueError("extendAliasingRangeFlag must be True/False.")

        self.setParameter(SPECTRUMALIASING, EXTENDALIASINGRANGEFLAG, value)

    @property
    def visibleAliasingRange(self) -> Optional[Tuple[Tuple, ...]]:
        """Return a tuple of the aliasing range in each dimension, or None of not set
        """
        alias = self.getParameter(SPECTRUMALIASING, VISIBLEALIASINGRANGE)
        if alias is not None:
            return tuple(tuple(rr) for rr in alias)

        # set default values in the ccpnInternal store
        alias = ((0, 0),) * self.dimensionCount

        # don't need to notify this - it can be set every time if needed
        with notificationBlanking():
            self.setParameter(SPECTRUMALIASING, VISIBLEALIASINGRANGE, alias)
        return alias

    @visibleAliasingRange.setter
    def visibleAliasingRange(self, values: Tuple[Tuple, ...]):
        """Set the aliasing range for each of the spectrum dimensions
        Must be a tuple matching the number of dimension.
        Each element is a tuple of the form (min, max)
        where min/max are integer in the range -3 -> +3

            e.g. visibleAliasingRange = ((0, 0), (-1, 1), ...)
        """

        # error checking that the tuples are correctly defined
        if len(values) != self.dimensionCount:
            raise ValueError("Length of %s does not match number of dimensions." % str(values))
        if not all(isinstance(dimVal, Tuple) and len(dimVal) == 2 for dimVal in values):
            raise ValueError("Visible aliasing values must be tuple(min, max).")

        for alias in values:
            if not (isinstance(alias[0], int) and isinstance(alias[1], int)
                    and alias[0] >= -MAXALIASINGRANGE and alias[1] <= MAXALIASINGRANGE and alias[0] <= alias[1]):
                raise ValueError("Visible aliasing values must be tuple(min >= -%i, max <= %i) of integer." % \
                                 (MAXALIASINGRANGE, MAXALIASINGRANGE))

        self.setParameter(SPECTRUMALIASING, VISIBLEALIASINGRANGE, values)

    @property
    @_includeInDimensionalCopy
    def aliasingRange(self) -> Optional[Tuple[Tuple, ...]]:
        """Return a tuple of the aliasing range in each dimension, or None of not set
        Note, this is an attribute, not a property;
        to get the property use spectrum._getAliasingRange, or peakList._getAliasingRange
        """
        alias = self.getParameter(SPECTRUMALIASING, ALIASINGRANGE)
        if alias is not None:
            return tuple(tuple(rr) for rr in alias)

        # set default values in the ccpnInternal store
        alias = ((0, 0),) * self.dimensionCount

        # don't need to notify this - it can be set every time if needed
        with notificationBlanking():
            self.setParameter(SPECTRUMALIASING, ALIASINGRANGE, alias)
        return alias

    @aliasingRange.setter
    def aliasingRange(self, values: Tuple[Tuple, ...]):
        """Set the currentAliasingRange for each of the spectrum dimensions
        Must be a tuple matching the number of dimension.
        Each element is a tuple of the form (min, max)
        where min/max are integer in the range -3 -> +3

            e.g. aliasingRange = ((0, 0), (-1, 1), ...)
        """

        # error checking that the tuples are correctly defined
        if len(values) != self.dimensionCount:
            raise ValueError("Length of %s does not match number of dimensions." % str(values))
        if not all(isinstance(dimVal, Tuple) and len(dimVal) == 2 for dimVal in values):
            raise ValueError("Aliasing values must be tuple(min, max).")

        for alias in values:
            if not (isinstance(alias[0], int) and isinstance(alias[1], int)
                    and alias[0] >= -MAXALIASINGRANGE and alias[1] <= MAXALIASINGRANGE and alias[0] <= alias[1]):
                raise ValueError("Aliasing values must be tuple(min >= -%i, max <= %i) of integer." % \
                                 (MAXALIASINGRANGE, MAXALIASINGRANGE))

        self.setParameter(SPECTRUMALIASING, ALIASINGRANGE, values)

    @property
    def _seriesValues(self):
        """Return a tuple of the series values for the spectrumGroups
        """
        values = self.getParameter(SPECTRUMSERIES, SPECTRUMSERIESVALUES)
        if values is not None:
            series = ()
            for sg in self.spectrumGroups:
                if sg.pid in values:
                    series += (values[sg.pid],)
                else:
                    series += (None, )
            return series

    @_seriesValues.setter
    @ccpNmrV3CoreSetter()
    def _seriesValues(self, values):
        """Set the series values for all spectrumGroups that spectrum is attached to.
        Must be of the form ( <values1>,
                              <values2>,
                              ...
                              <valuesN>
                            )
            where SGN are spectrumGroups and <valuesN> is a dict
        """
        if not values:
            raise ValueError('values is not defined')
        if not isinstance(values, (tuple, type(None))):
            raise TypeError('values is not of type tuple/None')
        if len(values) != len(self.spectrumGroups):
            raise ValueError('Number of values does not match number of spectrumGroups')
        for ll in values:
            if not isinstance(ll, (dict, type(None))):
                raise ValueError('Values must be of type dict/None: %s' % ll)

        if isinstance(values, tuple):
            seriesValues = self.getParameter(SPECTRUMSERIES, SPECTRUMSERIESVALUES)
            for sg, value in zip(self.spectrumGroups, values):
                if seriesValues:
                    seriesValues[sg.pid] = value
                else:
                    seriesValues = {sg.pid: value}
            self.setParameter(SPECTRUMSERIES, SPECTRUMSERIESVALUES, seriesValues)

        else:
            self.setParameter(SPECTRUMSERIES, SPECTRUMSERIESVALUES, None)

    def _getSeriesValues(self, spectrumGroup):
        """Return the series values for the current spectrum for the selected spectrumGroup
        """
        from ccpn.core.SpectrumGroup import SpectrumGroup

        spectrumGroup = self.project.getByPid(spectrumGroup) if isinstance(spectrumGroup, str) else spectrumGroup
        if not isinstance(spectrumGroup, SpectrumGroup):
            raise TypeError('%s is not a spectrumGroup' % str(spectrumGroup))
        if self not in spectrumGroup.spectra:
            raise ValueError('Spectrum %s does not belong to spectrumGroup %s' % (str(self), str(spectrumGroup)))

        seriesValues = self.getParameter(SPECTRUMSERIES, SPECTRUMSERIESVALUES)
        if seriesValues and spectrumGroup.pid in seriesValues:
            return seriesValues[spectrumGroup.pid]

    def _setSeriesValues(self, spectrumGroup, values):
        """Set the preferred ordering for the axis codes when opening a new spectrumDisplay
        """
        from ccpn.core.SpectrumGroup import SpectrumGroup

        spectrumGroup = self.project.getByPid(spectrumGroup) if isinstance(spectrumGroup, str) else spectrumGroup
        if not isinstance(spectrumGroup, SpectrumGroup):
            raise TypeError('%s is not a spectrumGroup', spectrumGroup)
        if self not in spectrumGroup.spectra:
            raise ValueError('Spectrum %s does not belong to spectrumGroup %s' % (str(self), str(spectrumGroup)))

        seriesValues = self.getParameter(SPECTRUMSERIES, SPECTRUMSERIESVALUES)
        if seriesValues:
            seriesValues[spectrumGroup.pid] = values
        else:
            seriesValues = {spectrumGroup.pid: values}
        self.setParameter(SPECTRUMSERIES, SPECTRUMSERIESVALUES, seriesValues)

    def _renameSeriesValues(self, spectrumGroup, oldPid, value):
        """rename the keys in the seriesValues top reflect the updated spectrumGroup name
        """
        seriesValues = self.getParameter(SPECTRUMSERIES, SPECTRUMSERIESVALUES)
        if oldPid in seriesValues:
            oldValues = seriesValues[oldPid]
            del seriesValues[oldPid]
            seriesValues[spectrumGroup.pid] = oldValues
            self.setParameter(SPECTRUMSERIES, SPECTRUMSERIESVALUES, seriesValues)

    # @property
    # def folding(self) -> Tuple:
    #     """return a tuple of folding values for dimensions
    #     """
    #     result = ()
    #     for dataDim in self._wrappedData.sortedDataDims():
    #         expDimRef = dataDim.expDim.findFirstExpDimRef(serial=1)
    #         if expDimRef is None:
    #             result += (None,)
    #         else:
    #             result += (expDimRef.isFolded,)
    #
    #     return result
    #
    # @folding.setter
    # def folding(self, values):
    #     if len(values) != len(self._wrappedData.sortedPeakDims()):
    #         raise ValueError("Length of %s does not match number of dimensions." % str(values))
    #     if not all(isinstance(dimVal, bool) for dimVal in values):
    #         raise ValueError("Folding values must be True/False.")

    #=========================================================================================
    # Library functions
    #=========================================================================================

    def getDefaultOrdering(self, axisOrder):
        if not axisOrder:
            axisOption = self.project.application.preferences.general.axisOrderingOptions

            preferredAxisOrder = self.preferredAxisOrdering
            if preferredAxisOrder is not None:

                specAxisOrder = self.axisCodes
                axisOrder = [specAxisOrder[ii] for ii in preferredAxisOrder]

            else:

                # sets an Nd default to HCN (or possibly 2d to HC)
                specAxisOrder = self.axisCodes
                pOrder = self.searchAxisCodePermutations(('H', 'C', 'N'))
                if pOrder:
                    self.preferredAxisOrdering = pOrder
                    axisOrder = [specAxisOrder[ii] for ii in pOrder]
                    getLogger().debug('setting default axisOrdering: ', str(axisOrder))

                else:

                    # just set to the normal ordering
                    self.preferredAxisOrdering = tuple(ii for ii in range(self.dimensionCount))
                    axisOrder = specAxisOrder

                    # try permutations of repeated codes
                    duplicates = [('H', 'H'), ('C', 'C'), ('N', 'N')]
                    for dCode in duplicates:
                        pOrder = self.searchAxisCodePermutations(dCode)

                        # if permutation found and matches first axis
                        if pOrder and pOrder[0] == 0:
                            self.preferredAxisOrdering = pOrder
                            axisOrder = [specAxisOrder[ii] for ii in pOrder]
                            getLogger().debug('setting duplicate axisOrdering: ', str(axisOrder))
                            break

        return axisOrder

    def automaticIntegration(self, spectralData):
        return self._apiDataSource.automaticIntegration(spectralData)

    def estimateNoise(self):
        """Estimate and set the noiseLevel
        """
        if self._dataSource is not None:
            self.noiseLevel = self._dataSource.estimateNoise()
        else:
            getLogger().warning('No valid access to spectral data, setting noiseLevel to 1e6')
            self.noiseLevel = 1.0e6
        return self.noiseLevel

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

    @cached(_REGIONDATACACHE, maxItems=16, debug=False)
    def getRegionData(self, exclusionBuffer: Optional[Sequence] = None, minimumDimensionSize: int = 3, **axisDict):
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

            and

            regionData = spectrum.getRegionData()           to get all the data, this may be very large!

        exclusionBuffer: defines the size to extend the region by in index units, e.g. [1, 1, 1] for a 3d array,
                            extends the region by 1 index point in all axes.
                            Default is 1 in all axis directions.
                            Must be the correct length for the number of dimensions

        minimumDimensionSize:   defines the minimum number of elements in each dimension that are needed
                                for the region to be valid.

                                default is 3, as mostly used for parabolic curve fitting which
                                requires 3 points in any given dimension

        The returned regionData is a tuple of regions, each of the form:

                single region = (dataArray,                 numpy array containing the data
                                intRegion,
                                startPoints,
                                endPoints,
                                startPointBufferActual,
                                endPointBufferActual,
                                startPointIntActual,
                                numPointInt,
                                startPointBuffer,
                                endPointBuffer)

        :param exclusionBuffer: array of int
        :param minimumDimensionSize: int
        :param axisDict: dict of axis limits
        :return: tuple of regions
        """
        if not self.hasValidPath():
            return

        startPoint = []
        endPoint = []

        # fill with the spectrum limits first
        regionToPick = list(self.spectrumLimits)

        codes = axisDict.keys()
        limits = tuple(axisDict.values())

        # map from input codes to self, done this way as MAY (but shouldn't) contain any Nones
        indices = getAxisCodeMatchIndices(self.axisCodes, codes)
        # for n, ind in enumerate(indices):
        #     if ind is not None:
        #         regionToPick[n] = limits[ind]

        indices = getAxisCodeMatchIndices(codes, self.axisCodes)
        for n, ind in enumerate(indices):
            if ind is not None:
                regionToPick[ind] = limits[n]

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

                # OR find aliasing offsets and change values to inside aliasing limits

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
                # npts[n] = dataSource.findFirstDataDim(dim=n + 1).numPointsOrig
                npts[n] = spectrumReferences[n].numPointsOrig
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

                # both None implies that the dataSource is not defined
                if dataArray is None and intRegion is None:
                    continue

                # include extra exclusion buffer information
                startPointInt, endPointInt = intRegion
                startPointInt = np.array(startPointInt)
                endPointInt = np.array(endPointInt)
                startPointIntActual = np.array([startPointInt[i] + tile[i] * npts[i] for i in range(numDim)])
                numPointInt = endPointInt - startPointInt
                startPointBuffer = np.maximum(startPointBuffer, startPointInt)
                endPointBuffer = np.minimum(endPointBuffer, endPointInt)

                # check that the number of elements in each dimension, skip if too small
                if np.any(numPointInt < minimumDimensionSize):
                    continue

                result += ((dataArray, intRegion,
                            startPoints, endPoints,
                            startPointBufferActual, endPointBufferActual,
                            startPointIntActual, numPointInt,
                            startPointBuffer, endPointBuffer),)

            return result  #dataArray, intRegion

        # for loop fails so return empty arrays in the first element
        return None

    def getByAxisCodes(self, attributeName: str, axisCodes: Sequence[str] = None, exactMatch: bool = False):
        """Return values defined by attributeName in order defined by axisCodes:
        (default order if None).

        Perform a mapping if exactMatch=False (eg. 'H' to 'Hn')

        NB: Use getByDimensions for dimensions (1..dimensionCount) based access
        """
        if not hasattr(self, attributeName):
            raise AttributeError('Object %s does not have attribute "%s"' %
                                 (self, attributeName)
                                 )

        if not isIterable(axisCodes):
            raise ValueError('axisCodes is not iterable "%s"; expected list or tuple' %
                             axisCodes
                             )

        if axisCodes is not None and not exactMatch:
            axisCodes = self._mapAxisCodes(axisCodes)

        try:
            values = getattr(self, attributeName)
        except AttributeError:
            raise AttributeError('Error getting attribute "%s" from object %s' %
                                 (attributeName, self)
                                 )
        if not isIterable(values):
            raise ValueError('Attribute "%s" of object %s is not iterable; "%s"' %
                             (attributeName, self, values)
                             )
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
            raise AttributeError('Object %s does not have attribute "%s"' %
                                 (self, attributeName)
                                 )

        if not isIterable(values):
            raise ValueError('Values "%s" is not iterable' % (values)
                             )

        if not isIterable(axisCodes):
            raise ValueError('axisCodes is not iterable "%s"; expected list or tuple' %
                             axisCodes
                             )

        if axisCodes is not None and not exactMatch:
            axisCodes = self._mapAxisCodes(axisCodes)

        if axisCodes is not None:
            # change values to the order appropriate for spectrum
            values = self._reorderValues(values, axisCodes)
        try:
            setattr(self, attributeName, values)
        except AttributeError:
            raise AttributeError('Unable to set attribute "%s" of object %s to "%s"' %
                                 (attributeName, self, values)
                                 )

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

    @cached.clear(_PLANEDATACACHE)  # Check if there was a planedata cache, and if so, clear it
    @cached.clear(_SLICEDATACACHE)  # Check if there was a slicedata cache, and if so, clear it
    @cached.clear(_SLICE1DDATACACHE)  # Check if there was a slice1ddata cache, and if so, clear it
    @cached.clear(_REGIONDATACACHE)  # Check if there was a regiondata cache, and if so, clear it
    def _clearCache(self):
        """Convenience to clear the cache; all action done by the decorators
        """
        pass

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

    @property
    def preferredAxisOrdering(self):
        """Return the preferred ordering for the axis codes when opening a new spectrumDisplay
        """
        order = self.getParameter(SPECTRUMAXES, SPECTRUMPREFERREDAXISORDERING)
        if order is not None:
            return order

        # set default ordering
        self.setParameter(SPECTRUMAXES, SPECTRUMPREFERREDAXISORDERING, None)
        return None

    @preferredAxisOrdering.setter
    def preferredAxisOrdering(self, order):
        """Set the preferred ordering for the axis codes when opening a new spectrumDisplay
        """
        if not order:
            raise ValueError('order is not defined')
        if not isinstance(order, tuple):
            raise TypeError('order is not a tuple')
        if len(order) != self.dimensionCount:
            raise TypeError('order is not the correct length')
        if not all(isinstance(ss, int) and ss >= 0 and ss < self.dimensionCount for ss in order):
            raise TypeError('order elements must be integer and in (0 .. %d)' % (self.dimensionCount - 1))
        if len(set(order)) != len(order):
            raise ValueError('order must contain unique elements')

        self.setParameter(SPECTRUMAXES, SPECTRUMPREFERREDAXISORDERING, order)

    def searchAxisCodePermutations(self, checkCodes: Tuple[str, ...]) -> Optional[Tuple[int]]:
        """Generate the permutations of the current axisCodes
        """
        if not checkCodes:
            raise ValueError('checkCodes is not defined')
        if not isinstance(checkCodes, (tuple, list)):
            raise TypeError('checkCodes is not a list/tuple')
        if not all(isinstance(ss, str) for ss in checkCodes):
            raise TypeError('checkCodes elements must be strings')

        from itertools import permutations

        # add permutations for the axes
        axisPerms = tuple(permutations([axisCode for axisCode in self.axisCodes]))
        axisOrder = tuple(permutations(list(range(len(self.axisCodes)))))

        for ii, perm in enumerate(axisPerms):
            n = min(len(checkCodes), len(perm))
            if n and all(pCode[0] == cCode[0] for pCode, cCode in zip(perm[:n], checkCodes[:n])):
                return axisOrder[ii]

    def _getAliasingRange(self):
        """Return the min/max aliasing range for the peakLists in the spectrum, if there are no peakLists with peaks, return None
        """
        # get the aliasingRanges for non-empty peakLists
        aliasRanges = [peakList._getAliasingRange() for peakList in self.peakLists if peakList.peaks]

        if aliasRanges:
            # if there is only one then return it (for clarity)
            if len(aliasRanges) == 1:
                return aliasRanges[0]

            # get the range from all the peakLists
            newRange = list(aliasRanges[0])
            for ii, alias in enumerate(aliasRanges[1:]):
                if alias is not None:
                    newRange = tuple((min(minL, minR), max(maxL, maxR)) for (minL, maxL), (minR, maxR) in zip(alias, newRange))

            return newRange

    def _copyDimensionalParameters(self, axisCodes, target):
        """Copy dimensional parameters for axisCodes from self to target
        """
        for attr in _includeInCopyList().getMultiDimensional():
            try:
                values = self.getByAxisCodes(attr, axisCodes, exactMatch=True)
                target.setByAxisCodes(attr, values, axisCodes, exactMatch=True)
            except Exception as es:
                getLogger().error('Copying "%s" from %s to %s for axisCodes %s: %s' %
                                  (attr, self, target, axisCodes, es)
                                  )

    def _copyNonDimensionalParameters(self, target):
        """Copy non-dimensional parameters from self to target
        """
        for attr in _includeInCopyList().getNoneDimensional():
            try:
                value = getattr(self, attr)
                setattr(target, attr, value)
            except Exception as es:
                getLogger().error('Copying "%s" from %s to %s: %s' %
                                  (attr, self, target, es)
                                  )

    def copyParameters(self, axisCodes, target):
        """Copy non-dimensional and dimensional parameters for axisCodes from self to target
        """
        self._copyNonDimensionalParameters(target)
        self._copyDimensionalParameters(axisCodes, target)

    #=========================================================================================
    # data access functions
    #=========================================================================================

    @logCommand(get='self')
    def getHeight(self, ppmPositions):
        """Returns the interpolated height at the ppm position
        """
        ref = self.mainSpectrumReferences

        if len(ppmPositions) != self.dimensionCount:
            raise ValueError("Length of %s does not match number of dimensions." % str(ppmPositions))
        if not all(isinstance(dimVal, (int, float)) for dimVal in ppmPositions):
            raise ValueError("ppmPositions values must be floats.")

        pointPosition = tuple(ref[dim].valueToPoint(ppm) for dim, ppm in enumerate(ppmPositions))
        return self.getPositionValue(pointPosition)

    @logCommand(get='self')
    def getPositionValue(self, pointPosition):
        """Return the value nearest to the position given in points.
        """
        if len(pointPosition) != self.dimensionCount:
            raise ValueError("Length of %s does not match number of dimensions." % str(pointPosition))
        if not all(isinstance(dimVal, (int, float)) for dimVal in pointPosition):
            raise ValueError("position values must be floats.")

        scale = self.scale if self.scale is not None else 1.0
        if self.scale == 0.0:
            getLogger().warning('Scaling "%s" by 0.0!' % self)

        pointPosition = self._apiDataSource.getPositionValue(pointPosition)
        return pointPosition * scale if pointPosition else None

    @cached(_SLICE1DDATACACHE, maxItems=1, debug=False)
    def _get1DSliceData(self, position, sliceDim: int):
        """Internal routine to get 1D sliceData;
        """
        if self._dataSource is None:
            # data = self._apiDataSource.getSliceData(position=position, sliceDim=sliceDim)
            getLogger().warning('No proper (filePath, dataFormat) set for %s; Returning zeros only' % self)
            data = numpy.zeros( (self.pointCounts[sliceDim-1], ), dtype=numpy.float32)
        else:
            data = self._dataSource.getSliceData(position=position, sliceDim=sliceDim)
        return data

    @cached(_SLICEDATACACHE, maxItems=1024, debug=False)
    def _getSliceDataFromPlane(self, position, xDim: int, yDim: int, sliceDim: int):
        """Internal routine to get sliceData; optimised to use (buffered) getPlaneData
        CCPNINTERNAL: used in CcpnOpenGL
        """
        if not (sliceDim == xDim or sliceDim == yDim):
            raise RuntimeError('sliceDim (%s) not in plane (%s,%s)' % (sliceDim, xDim, yDim))

        # Improve caching,
        position[xDim-1] = 1
        position[yDim-1] = 1

        data = self._getPlaneData(position, xDim, yDim)

        if sliceDim == xDim:
            slice = position[yDim - 1] - 1  # position amd dimensions are 1-based
            return data[slice, 0:]
        elif sliceDim == yDim:
            slice = position[xDim - 1] - 1  # position amd dimensions are 1-based
            return data[0:, slice]

    @logCommand(get='self')
    def getSliceData(self, position=None, sliceDim: int = 1):
        """
        Get a slice through position along sliceDim from the Spectrum
        :param position: An optional list/tuple of point positions (1-based);
                         defaults to [1,1,1,1]
        :param sliceDim: Dimension of the slice (1-based)
        :return: numpy data array
        """
        if position is None:
            position = [1] * self.dimensionCount
        else:
            position = list(position)

        if not isIterable(position) or len(position) < self.dimensionCount:
            raise ValueError('sliceDim should be a iterable with length %d; got "%s"' %
                             (self.dimensionCount, position)
                             )

        if isIterable(sliceDim) or sliceDim < 1 or sliceDim > self.dimensionCount:
            raise ValueError('sliceDim should be a scalar in range [1-%d]; got "%s"' %
                             (self.dimensionCount, sliceDim)
                             )

        result = None
        scale = self.scale if self.scale is not None else 1.0
        if self.scale == 0.0:
            getLogger().warning('Scaling "%s" by 0.0!' % self)

        if self.dimensionCount == 1:
            # 1D data
            result = self._get1DSliceData(position=position, sliceDim=sliceDim)
            # Make a copy in order to preserve the original data and apply scaling
            if result is not None:
                result = result.copy(order='K') * scale
        else:
            # nD data; get slice via appropriate plane
            position[sliceDim - 1] = 1  # To improve caching; position, dimensions are 1-based
            if sliceDim > 1:
                result = self._getSliceDataFromPlane(position=position, xDim=1, yDim=sliceDim,
                                                     sliceDim=sliceDim)
            else:
                result = self._getSliceDataFromPlane(position=position, xDim=sliceDim, yDim=sliceDim + 1,
                                                     sliceDim=sliceDim)

            # Make a copy in order to preserve the original data; do not apply scaling, as this was already done
            # by the _getSliceDataFromPlane routine which calls getPlaneData
            if result is not None:
                result = result.copy(order='K')

        # check if we have something valid to return
        if result is None:
            getLogger().warning('Failed to get slice data along dimension "%s" at position %s' %
                                (sliceDim, position))

        # For 1D, save as intensities attribute
        self._intensities = result
        return result

    @logCommand(get='self')
    def getSlice(self, axisCode, position, exactMatch=True):
        """Get 1D slice along axisCode through position; sets the intensities attribute
        :return: 1D NumPy data array
        """
        sliceDim = self.getByAxisCodes('dimensions', [axisCode], exactMatch=exactMatch)
        return self.getSliceData(position=position, sliceDim=sliceDim[0])

    def _getDefaultSlicePath(self, axisCode, position):
        "Return a default path for slice"
        from ccpn.util.Hdf5 import HDF5_EXTENSION

        slice = self.name + '_slice_%s_' % axisCode + '_'.join((str(p) for p in position))
        _p = aPath(self.filePath)
        return str(_p.parent / slice + HDF5_EXTENSION)

    @logCommand(get='self')
    def allSlices(self, axisCode, exactMatch=True):
        """An iterator over all slices defined by axisCode, yielding (position, data-array) tuples
        positions are one-based
        """

        sliceDim = self.getByAxisCodes('dimensions', [axisCode], exactMatch=exactMatch)[0]

        # get dimensions to interate over
        dims = (sliceDim,)
        iterDims = list(set(self.dimensions) - set(dims))
        # get relevant iteration parameters
        points = [self.pointCounts[dim-1] for dim in iterDims]
        indices = [dim-1 for dim in iterDims]
        iterData = list(zip(iterDims, points, indices))

        def _nextPosition(currentPosition):
            "Return a (done, position) tuple derived from currentPosition"
            for dim, point, idx in iterData:
                if currentPosition[idx] + 1 <= point:  # still an increment to make in this dimension
                    currentPosition[idx] += 1
                    return (False, currentPosition)
                else:  # reset this dimension
                    currentPosition[idx] = 1
            return (True, None)  # reached the end

        # loop over all slices
        position = [1] * self.dimensionCount
        done = False
        while not done:
            with notificationEchoBlocking(self.project.application):
                sliceData = self.getSliceData(position=position, sliceDim=sliceDim)
                yield (tuple(position), sliceData)
            done, position = _nextPosition(position)

    @logCommand(get='self')
    def extractSliceToFile(self, axisCode, position, path=None):
        """Extract 1d slice from self as new Spectrum; saved to path
        (auto-generated if not given)
        if 1D it effectively yields a copy of self

        :param axisCode: axiscode of slice to extract
        :param position: position vector (1-based)
        :param path: optional path; constructed from current filePath and name of instance
        :return: Spectrum instance
        """

        if axisCode not in self.axisCodes:
            raise ValueError('Invalid axisCode "%s"' % axisCode)
        if len(position) != self.dimensionCount:
            raise ValueError('Invalid position "%s"' % position)

        if path is None:
            path = self._getDefaultSlicePath(axisCode, position)

        # Due to implementation limitations, we have to hack this:
        # first create a dummy spectrum; read the data and store with dummy
        # Save the data into hdf5 and reload to create a new Spectrum instance.
        # To alleviate: we would need a newSpectrum() method, without the need for an actual
        # spectrum, but with the option to set path, sizes etc in the model (which
        # createDummy does not do
        _dummy = self.project.createDummySpectrum(axisCodes=[axisCode], name='_dummy')
        _dummy._intensities = self.getSlice(axisCode, position, exactMatch=True)
        # copy relevant attributes
        self.copyParameters(axisCodes=[axisCode], target=_dummy)

        # save as hdf5 file
        from ccpn.util.Hdf5 import convertDataToHdf5

        convertDataToHdf5(_dummy, path)

        # create the api storage by destroying _dummy and re-loading the data
        from ccpnmodel.ccpncore.lib.spectrum.formats.Hdf5 import FILE_TYPE as HDF5_TYPE

        self.project.deleteObjects(_dummy)
        newSpectrum = self.project.loadSpectrum(path=path, subType=HDF5_TYPE)[0]  # load yields a list
        newSpectrum.axisCodes = [axisCode]  # to overRide the loadData
        # Copy relevant attributes again
        self.copyParameters(axisCodes=[axisCode], target=newSpectrum)
        return newSpectrum

    # @cached(_PLANEDATACACHE, maxItems=64, debug=False)
    def _getPlaneData(self, position, xDim: int, yDim: int):
        "Internal routine to improve caching: Calling routine set the positions of xDim, yDim to 1 "
        # Calls Nmr.DataSource.getPlaneData"
        if self._dataSource is None:
            # data = self._apiDataSource.getPlaneData(position=position, xDim=xDim, yDim=yDim)
            getLogger().warning('No proper (filePath, dataFormat) set for %s; Returning zeros only' % self)
            data = numpy.zeros( (self.pointCounts[yDim-1], self.pointCounts[xDim-1]), dtype=numpy.float32)
        else:
            data = self._dataSource.getPlaneData(position=position, xDim=xDim, yDim=yDim)
        return data

    @logCommand(get='self')
    def getPlaneData(self, position=None, xDim: int = 1, yDim: int = 2):
        """Get a plane defined by by xDim and yDim ('1'-based), and a position vector ('1'-based)
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

        result = None
        scale = self.scale if self.scale is not None else 1.0
        if self.scale == 0.0:
            getLogger().warning('Scaling "%s" by 0.0!' % self)

        result = self._getPlaneData(position=position, xDim=xDim, yDim=yDim)
        # Make a copy in order to preserve the original data and apply scaling
        result = result.copy(order='K') * scale

        # check if we have something valid to return
        if result is None:
            raise RuntimeError('%s: Failed to get plane data along dimensions (%s,%s) at position %s' %
                               (self, xDim, yDim, position))

        return result

    @logCommand(get='self')
    def getPlane(self, axisCodes: tuple, position=None, exactMatch=True):
        """Get a plane defined by a tuple of two axisCodes, and a position vector ('1' based, defaults to first point)
        Expand axisCodes if exactMatch=False
        returns np-data array
        NB: use getPlaneData method for dimension based access
        """
        if len(axisCodes) != 2:
            raise ValueError('Invalid axisCodes %s, len should be 2' % axisCodes)
        xDim, yDim = self.getByAxisCodes('dimensions', axisCodes, exactMatch=exactMatch)
        return self.getPlaneData(position=position, xDim=xDim, yDim=yDim)

    def _getDefaultPlanePath(self, axisCodes, position):
        "Construct a default path for plane"
        planeStr = '_plane_' + '_'.join(axisCodes) + '_' + '_'.join([str(p) for p in position])
        _p = aPath(self.filePath)
        return os.path.join(str(_p.parent), _p.basename) + planeStr + '.dat'

    def _savePlaneToNmrPipe(self, planeData, xDim, yDim, path):
        "Save planeData as xDim,yDim) as NmrPipe path file"
        from ccpnmodel.ccpncore.lib.spectrum.formats.NmrPipe import _makeNmrPipe2DHeader
        with open(path, 'wb') as fp:
            #TODO: remove dependency on filestorage on apiLayer
            header = _makeNmrPipe2DHeader(self._wrappedData, xDim, yDim)
            header.tofile(fp)
            planeData.tofile(fp)

    @logCommand(get='self')
    def extractPlaneToFile(self, axisCodes: tuple, position=None, path=None):
        """Save plane defined by a tuple of two axisCodes and position
        to file. Save to path (auto-generated if None).

        :returns plane as Spectrum instance
        """
        if self.dimensionCount < 2:
            raise RuntimeError('Cannot extract plane from 1D data (%s)' % self)

        if position is None:
            position = [1] * self.dimensionCount

        if path is None:
            path = self._getDefaultPlanePath(axisCodes, position)

        xDim, yDim = self.getByAxisCodes('dimensions', axisCodes)[0:2]
        planeData = self.getPlaneData(position=position, xDim=xDim, yDim=yDim)
        self._savePlaneToNmrPipe(planeData, xDim=xDim, yDim=yDim, path=path)

        newSpectrum = self.project.loadSpectrum(path, subType=Formats.NMRPIPE)[0]
        newSpectrum.axisCodes = axisCodes  # to override the loadSpectrum routine
        self.copyParameters(axisCodes=axisCodes, target=newSpectrum)
        return newSpectrum

    @logCommand(get='self')
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
            with notificationEchoBlocking(self.project.application):
                planeData = self._apiDataSource.getPlaneData(position=position, xDim=xDim, yDim=yDim)
                yield (tuple(position), planeData)
            done, position = _nextPosition(position)

    @logCommand(get='self')
    def getProjection(self, axisCodes: tuple, method: str = 'max', threshold=None):
        """Get projected plane defined by a tuple of two axisCodes, using method and an optional threshold
        return projected spectrum data as NumPy data array
        """
        projectedData = _getProjection(self, axisCodes=axisCodes, method=method, threshold=threshold)
        return projectedData

    def _getDefaultProjectionPath(self, axisCodes):
        "Construct a default path for projection"
        planeStr = '_projection_' + '_'.join(axisCodes)
        _p = aPath(self.filePath)
        return os.path.join(str(_p.parent), _p.basename) + planeStr + '.dat'

    @logCommand(get='self')
    def extractProjectionToFile(self, axisCodes: tuple, method: str = 'max', threshold=None, path=None):
        """Save projected plane defined by a tuple of two axisCodes, using method and an optional threshold
        to file. Save to path (auto-generated if None) using format
        return projected spectrum as Spectrum instance
        """
        if path is None:
            path = self._getDefaultProjectionPath(axisCodes)

        projectedData = self.getProjection(axisCodes=axisCodes, method=method, threshold=threshold)
        xDim, yDim = self.getByAxisCodes('dimensions', axisCodes)[0:2]
        self._savePlaneToNmrPipe(projectedData, xDim=xDim, yDim=yDim, path=path)

        newSpectrum = self.project.loadSpectrum(path, subType=Formats.NMRPIPE)[0]
        newSpectrum.axisCodes = axisCodes  # to override the loadSpectrum routine
        self.copyParameters(axisCodes=axisCodes, target=newSpectrum)
        return newSpectrum

    # GWV 20190731: not used
    # def get1dSpectrumData(self):
    #     """Get position,scaledData numpy array for 1D spectrum.
    #     Yields first 1D slice for nD"""
    #     return self._apiDataSource.get1dSpectrumData()

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

        # notify peak/integral/multiplet list
        if action in ['create', 'delete']:
            for peakList in self.peakLists:
                peakList._finaliseAction(action=action)
        if action in ['create', 'delete']:
            for multipletList in self.multipletLists:
                multipletList._finaliseAction(action=action)
        if action in ['create', 'delete']:
            for integralList in self.integralLists:
                integralList._finaliseAction(action=action)

    @logCommand(get='self')
    def delete(self):
        """Delete Spectrum"""
        with undoBlock():
            self._clearCache()
            self.deleteAllNotifiers()

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
                         comment: str = None, multiplets: Sequence[Union['Multiplet', str]] = None, **kwds):
        """Create new MultipletList within Spectrum.

        See the MultipletList class for details.

        Optional keyword arguments can be passed in; see MultipletList._newMultipletList for details.

        :param title: title string
        :param symbolColour:
        :param textColour:
        :param lineColour:
        :param multipletAveraging:
        :param comment: optional comment string
        :param multiplets: optional list of multiplets as objects or pids
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
    # Output, printing, etc
    #=========================================================================================
    def _infoString(self, includeDimensions=False):
        """Return info string about self, optionally including dimensional
        parameters
        """
        string = '================= %s =================\n' % self
        string += 'path = %s\n' % self.filePath
        string += 'dataFormat = %s\n' % self.dataFormat
        for cache in self._dataCaches:
            if hasattr(self, cache):
                string += str(getattr(self, cache)) + '\n'
        string += 'dimensions = %s\n' % self.dimensionCount
        string += 'sizes = (%s)\n' % ' x '.join([str(d) for d in self.pointCounts])
        for attr in """
                scale 
                noiseLevel 
                experimentName
                """.split():
            value = getattr(self, attr)
            string += '%s = %s\n' % (attr, value)

        if includeDimensions:
            string += '\n'
            for attr in """
                dimensions
                axisCodes
                pointCounts
                isComplex
                dimensionTypes
                isotopeCodes
                measurementTypes
                spectralWidths
                spectralWidthsHz
                spectrometerFrequencies
                referencePoints
                referenceValues
                axisUnits
                foldingModes
                windowFunctions
                lorentzianBroadenings
                gaussianBroadenings
                phases0
                phases1
                assignmentTolerances
                """.split():
                values = getattr(self, attr)
                string += '%-25s: %s\n' % (attr,
                                           ' '.join(['%-20s' % str(v) for v in values])
                                           )
        return string

    def print(self, includeDimensions=True):
        "Print the info string"
        print(self._infoString(includeDimensions))


#=========================================================================================
# New and empty spectra
#=========================================================================================

# Hack; remove the api notifier on create
# _notifiers = [nf for nf in Project._apiNotifiers if nf[3] == '__init__' and 'cls' in nf[1] and nf[1]['cls'] == Spectrum]
# if len(_notifiers) == 1:
#     Project._apiNotifiers.remove(_notifiers[0])




@newObject(Spectrum)
def _newSpectrum(self: Project, path: str, name: str) -> Spectrum:
    """Creation of new Spectrum;
    :return: Spectrum instance or None on error
    """

    # Local  to prevent circular import
    from sandbox.Geerten.SpectrumDataSources.SpectrumDataSourceABC import checkPathForSpectrumFormats

    logger = getLogger()
    application = self.application

    dataStore = DataStore.newFromPath(path)
    if not dataStore.exists():
        dataStore.errorMessage()
        return None

    _path = dataStore.aPath()
    dir, base, ext = _path.split3()

    if name is None:
        name = base

    # assure unique name
    names = [sp.name for sp in self.spectra]
    if name in names:
        i = 1
        while '%s_%s' % (name, i) in names:
            i += 1
        name = '%s_%s' % (name, i)

    # Try to determine data format from the path and intialise a dataSource instance with parsed parameters
    dataSource = checkPathForSpectrumFormats(path=_path)
    if dataSource is None:
        logger.warning('Invalid spectrum path "%s"' % path) # report the argument given
        return None
    dataStore.dataFormat = dataSource.dataFormat

# Consolidating previous API calls:
#   NmrProject.createExperiment
#   spectrum.Spectrum.createBlockedMatrix
#   Nmr.Expertiment.createDataSource
#
# First creating the api data structures with minimal parameters and once in place updating all values from a
# SpectrumDataSource instance

    apiProject = self._wrappedData
    apiExperiment = apiProject.newExperiment(name=name,
                                             numDim=dataSource.dimensionCount,
                                            )

    # apiUrl = apiProject.root.fetchDataUrl(dir)
    # urlPath = aPath(apiUrl.url.path)
    # relPath = _path.relative_to(urlPath)

    # apiDataStore =  apiUrl.dataLocationStore.newBlockedBinaryMatrix(
    #                            dataUrl=apiUrl,
    #                            path=str(relPath),
    #                            numPoints=dataSource.pointCounts,
    #                            isComplex=dataSource.isComplex,
    #                            blockSizes=dataSource.blockSizes,
    #                            fileType=dataSource.dataFormat,
    #                           )

    apiDataSource = apiExperiment.newDataSource(name=name,
                                                dataStore=None,  #apiDataStore,
                                                numDim=dataSource.dimensionCount,
                                                dataType='processed'
                                                )

    # Intialise the freq/time dimensions; This seems a very complicated datastructure! (GWV)
    # dataDim classnames are FidDataDim, FreqDataDim, SampledDataDim
    for n, expDim in enumerate(apiExperiment.sortedExpDims()):
        expDim.isAcquisition = False  #(dataSource.aquisitionAxisCode == dataSource.axisCodes[n]),
        expDimRef = expDim.newExpDimRef(
                            isotopeCodes=(dataSource.isotopeCodes[n],),
                            axisCode=dataSource.axisCodes[n],
                            sf=dataSource.spectrometerFrequencies[n],
                            unit='ppm'
                           )

        _nPoints = dataSource.pointCounts[n]
        freqDataDim = apiDataSource.newFreqDataDim(dim=n+1, expDim=expDim,
                                                   numPoints=_nPoints,
                                                   numPointsOrig=_nPoints,
                                                   pointOffset=0,
                                                   isComplex=dataSource.isComplex[n],
                                                   valuePerPoint=dataSource.spectralWidthsHz[n]/float(_nPoints)
                                                   )
        # expDimRef = (expDim.findFirstExpDimRef(measurementType='Shift') or expDim.findFirstExpDimRef())
        if expDimRef:
            freqDataDim.newDataDimRef(expDimRef=expDimRef)

    # Done with api generation; Create the Spectrum object

    # Agggh, cannot do
    #   spectrum = Spectrum(self, apiDataSource)
    # as the object was magically already created
    # This was done by Project_newApiObject, called from Nmr.DataSource.__init__ through an api notifier.
    # This notifier is set in the AbstractWrapper class and is part of the machinery generation; i.e.
    # _linkWrapperClasses (needs overhaul!!)

    spectrum = self._data2Obj.get(apiDataSource)
    if spectrum is None:
        raise RuntimeError("something went wrong creating a new Spectrum instance")
    spectrum._apiExperiment = apiExperiment
    # spectrum._apiDataStore = apiDataStore

    # Set the references between spectrum and dataStore
    dataStore.spectrum = spectrum
    dataStore._saveInternal()
    spectrum._dataStore = dataStore

    # Update all parameters from the dataSource to the Spectrum instance; retain the dataSource instance
    dataSource.exportToSpectrum(spectrum, includePath=False)
    spectrum._dataSource = dataSource

    # Link to default (i.e. first) chemicalShiftList
    spectrum.chemicalShiftList = self.chemicalShiftLists[0]

    # # Assure at least one peakList
    if len(spectrum.peakLists) == 0:
        spectrum.newPeakList()

    # Set noiseLevel, contourLevels, contourColours
    spectrum.noiseLevel = spectrum._dataSource.estimateNoise()
    # this crashes (sometimes), deep in the bowles of the v2-code
    # setContourLevelsFromNoise(spectrum, setNoiseLevel=True,
    #                                     setPositiveContours=True, setNegativeContours=True,
    #                                     useSameMultiplier=True)
    spectrum._setContourDefaultValues()
    spectrum.sliceColour = spectrum.positiveContourColour

    return spectrum


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
# GWV: not needed?
            # ('_finaliseApiRename', {}, Nmr.DataSource._metaclass.qualifiedName(), 'setName'),
            #
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


# Experiment:
# dataDict['applicationData'] = list()
# dataDict['details'] = None
# dataDict['endDate'] = None
# dataDict['isLocked'] = None
# dataDict['lastEditedDate'] = None
# dataDict['name'] = None
# dataDict['serial'] = None
# dataDict['startDate'] = None
# dataDict['status'] = None
# dataDict['access'] = None
# dataDict['annotations'] = set()
# dataDict['blueprintStatuss'] = set()
# dataDict['creator'] = None
# dataDict['expBlueprint'] = None
# dataDict['experimentGroup'] = None
# dataDict['experimentType'] = None
# dataDict['group'] = None
# dataDict['instrument'] = None
# dataDict['lastEditor'] = None
# dataDict['method'] = None
# dataDict['next'] = set()
# dataDict['outputSamples'] = {}
# dataDict['parameters'] = {}
# dataDict['previous'] = set()
# dataDict['protocol'] = None
# dataDict['sampleIos'] = {}

# apiExperiment = apiProject.createExperiment(name=name,
#                                             numDim=dataSource.dimensionCount,
#                                             sf=dataSource.spectrometerFrequencies,
#                                             isotopeCodes=dataSource.isotopeCodes
#                                             )

# BlockedBinaryMatrix
# dataDict['_ID'] = None
# dataDict['applicationData'] = list()
# dataDict['blockHeaderSize'] = 0
# dataDict['blockSizes'] = list()
# dataDict['ccpnInternalData'] = None
# dataDict['complexStoredBy'] = 'dimension'
# dataDict['details'] = None
# dataDict['fileType'] = None
# dataDict['hasBlockPadding'] = True
# dataDict['headerSize'] = 0
# dataDict['isBigEndian'] = True
# dataDict['isComplex'] = list()
# dataDict['nByte'] = 4
# dataDict['numPoints'] = list()
# dataDict['numRecords'] = 1
# dataDict['numberType'] = 'float'
# dataDict['path'] = None
# dataDict['scaleFactor'] = 1.0
# dataDict['serial'] = None
# dataDict['dataUrl'] = None
# dataDict['nmrDataSources'] = set()
#     dataStore =  createBlockedMatrix(
#                                dataUrl=apiUrl,
#                                path=path,
#                                numPoints=dataSource.pointCounts,
#                                blockSizes=dataSource.blockSizes,
#                                fileType=dataSource.dataFormat,
#                               isComplex=[False]*dataSource.dimensionCount,
#                               complexStoredBy=['timepoint']*dataSource.dimensionCount
#                               )

# apiDataSource = apiExperiment.createDataSource(
#                                                name=name,
#                                                dataStore = apiDataStore,
#                                                numPoints=dataSource.pointCounts,
#                                                sw=dataSource.spectralWidthsHz,
#                                                refppm=dataSource.referenceValues,
#                                                refpt=dataSource.referencePoints,
#                                                sampledValues=dataSource.sampledValues,
#                                                sampledErrors=dataSource.sampledSigmas,
#                                                # notOverRide=False, # prevent callback to create Spectrum instance
#                                                )
