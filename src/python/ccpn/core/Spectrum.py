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
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-12-10 14:55:13 +0000 (Fri, December 10, 2021) $"
__version__ = "$Revision: 3.0.4 $"
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
from itertools import permutations
import decorator
from ccpn.util import Constants
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
from ccpnmodel.ccpncore.api.ccp.general import DataLocation
from ccpn.core.lib import Pid
from ccpn.core.lib.SpectrumLib import MagnetisationTransferTuple, _getProjection
from ccpn.core.lib.Cache import cached
from ccpn.util.decorators import logCommand
from ccpn.framework.constants import CCPNMR_PREFIX
from ccpn.core.lib.ContextManagers import newObject, deleteObject, ccpNmrV3CoreSimple, \
    undoStackBlocking, renameObject, undoBlock, notificationBlanking, ccpNmrV3CoreSetter
from ccpn.util.Common import getAxisCodeMatchIndices, _validateName
from ccpn.util.Path import Path, aPath
from ccpn.util.Common import isIterable, incrementName, _getObjectsByPids
from ccpn.util.Constants import SCALETOLERANCE

# 2019010:ED test new matching
# from ccpn.util.Common import axisCodeMapping
from ccpn.util.Common import getAxisCodeMatch as axisCodeMapping

from ccpn.util.Logging import getLogger

from ccpnmodel.ccpncore.lib.Io import Formats
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import FidDataDim as ApiFidDataDim
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import FreqDataDim as ApiFreqDataDim
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import SampledDataDim as ApiSampledDataDim


INCLUDEPOSITIVECONTOURS = 'includePositiveContours'
INCLUDENEGATIVECONTOURS = 'includeNegativeContours'
SPECTRUMAXES = 'spectrumAxesOrdering'
SPECTRUMPREFERREDAXISORDERING = 'spectrumPreferredAxisOrdering'
SPECTRUMALIASING = 'spectrumAliasing'
DISPLAYFOLDEDCONTOURS = 'displayFoldedContours'
MAXALIASINGRANGE = 3
SPECTRUMSERIES = 'spectrumSeries'
SPECTRUMSERIESITEMS = 'spectrumSeriesItems'

DIMENSIONFID = 'Fid'
DIMENSIONFREQUENCY = 'Frequency'
DIMENSIONFREQ = 'Freq'
DIMENSIONSAMPLED = 'Sampled'
DIMENSIONTYPES = [DIMENSIONFID, DIMENSIONFREQUENCY, DIMENSIONSAMPLED]
_DIMENSIONCLASSES = {DIMENSIONFID: ApiFidDataDim, DIMENSIONFREQUENCY: ApiFreqDataDim, DIMENSIONSAMPLED: ApiSampledDataDim}


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


#=========================================================================================
# Decorators to define the attributes to be copied
#=========================================================================================

from ccpn.util.decorators import singleton


@singleton
class _includeInCopyList(list):
    """Singleton class to store the attributes to be included when making a copy of object.
    Attributes can be modified and can be either non-dimensional or dimension dependent,
    Dynamically filled by two decorators
    Stored as list of (attributeName, isMultiDimensional) tuples
    """

    def getNoneDimensional(self):
        "return a list of one-dimensional attributes"
        return [attr for attr, isNd in self if isNd == False]

    def getMultiDimensional(self):
        "return a list of one-dimensional attributes"
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
    _ReferenceSubstancesPids = '_ReferenceSubstancesPids'

    MAXDIM = 4  # Maximum dimensionality

    _PLANEDATACACHE = '_planeDataCache'  # Attribute name for the planeData cache
    _SLICEDATACACHE = '_sliceDataCache'  # Attribute name for the slicedata cache
    _SLICE1DDATACACHE = '_slice1DDataCache'  # Attribute name for the 1D slicedata cache
    _REGIONDATACACHE = '_regionDataCache'  # Attribute name for the regionData cache
    _REFERENCESUBSTANCESCACHE = '_referenceSubstances'
    _dataCaches = [_PLANEDATACACHE, _SLICEDATACACHE, _SLICE1DDATACACHE, _REGIONDATACACHE]

    def __init__(self, project: Project, wrappedData: Nmr.ShiftList):

        self._intensities = None
        self._positions = None

        super().__init__(project, wrappedData)

        self.doubleCrosshairOffsets = self.dimensionCount * [0]  # TBD: do we need this to be a property?
        self.showDoubleCrosshair = False
        self._scaleChanged = False

    def _infoString(self, includeDimensions=False):
        """Return info string about self, optionally including dimensional
        parameters
        """
        string = '================= %s =================\n' % self
        string += 'path = %s\n' % self.filePath
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

    def printInfoString(self, includeDimensions=False):
        "Print the info string"
        print(self._infoString(includeDimensions))

    # CCPN properties
    @property
    def _apiDataSource(self) -> Nmr.DataSource:
        """CCPN DataSource matching Spectrum"""
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
    def _apiDataStore(self):
        """DataStore attached to the spectrum"""
        return self._wrappedData.dataStore

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
    def axes(self) -> tuple:
        """Convenience: tuple of length dimensionCount with axes integers (0-based); e.g. (0,1,2,3).
        Useful for mapping axisCodes: eg: self.getByAxisCodes('axes', ['N','C','H'])
        """
        return tuple(range(0, self.dimensionCount))

    @property
    def axisTriples(self) -> tuple:
        """Convenience: return a tuple of triples (axis, axisCode, dimension) for each dimension

        Useful for iterating over axis codes; eg in an H-N-CO ordered spectrum
            for axis, axisCode, dimension in self.getByAxisCodes('axisTriples', ('N','C','H'), exactMatch=False)

            would yield:
                (1, 'N', 2)
                (2, 'CO', 3)
                (0, 'H', 1)
        """
        return tuple(z for z in zip(self.axes, self.axisCodes, self.dimensions))

    @property
    @_includeInCopy
    def positiveContourCount(self) -> int:
        """number of positive contours to draw"""
        return self._wrappedData.positiveContourCount

    @positiveContourCount.setter
    @logCommand(get='self', isProperty=True)
    def positiveContourCount(self, value):
        self._wrappedData.positiveContourCount = value

    @property
    @_includeInCopy
    def positiveContourBase(self) -> float:
        """base level of positive contours"""
        return self._wrappedData.positiveContourBase

    @positiveContourBase.setter
    @logCommand(get='self', isProperty=True)
    def positiveContourBase(self, value):
        self._wrappedData.positiveContourBase = value

    @property
    @_includeInCopy
    def positiveContourFactor(self) -> float:
        """level multiplier for positive contours"""
        return self._wrappedData.positiveContourFactor

    @positiveContourFactor.setter
    @logCommand(get='self', isProperty=True)
    def positiveContourFactor(self, value):
        self._wrappedData.positiveContourFactor = value

    @property
    @_includeInCopy
    def positiveContourColour(self) -> str:
        """colour of positive contours"""
        return self._wrappedData.positiveContourColour

    @positiveContourColour.setter
    @logCommand(get='self', isProperty=True)
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
    @logCommand(get='self', isProperty=True)
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
    @logCommand(get='self', isProperty=True)
    def negativeContourCount(self, value):
        self._wrappedData.negativeContourCount = value

    @property
    @_includeInCopy
    def negativeContourBase(self) -> float:
        """base level of negative contours"""
        return self._wrappedData.negativeContourBase

    @negativeContourBase.setter
    @logCommand(get='self', isProperty=True)
    def negativeContourBase(self, value):
        self._wrappedData.negativeContourBase = value

    @property
    @_includeInCopy
    def negativeContourFactor(self) -> float:
        """level multiplier for negative contours"""
        return self._wrappedData.negativeContourFactor

    @negativeContourFactor.setter
    @logCommand(get='self', isProperty=True)
    def negativeContourFactor(self, value):
        self._wrappedData.negativeContourFactor = value

    @property
    @_includeInCopy
    def negativeContourColour(self) -> str:
        """colour of negative contours"""
        return self._wrappedData.negativeContourColour

    @negativeContourColour.setter
    @logCommand(get='self', isProperty=True)
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
    @logCommand(get='self', isProperty=True)
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
    @_includeInCopy
    def sliceColour(self) -> str:
        """colour of 1D slices"""
        return self._wrappedData.sliceColour

    @sliceColour.setter
    @logCommand(get='self', isProperty=True)
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
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSimple()
    def scale(self, value: Union[float, int, None]):
        if not isinstance(value, (float, int, type(None))):
            raise TypeError('Spectrum.scale {} must be a float, integer or None'.format(self))
        if value is not None and -SCALETOLERANCE < value < SCALETOLERANCE:
            # Display a warning, but allow to be set
            getLogger().warning('Scaling {} by minimum tolerance (±{})'.format(self, SCALETOLERANCE))

        self._scaleChanged = True
        if value is None:
            self._wrappedData.scale = None
        else:
            self._wrappedData.scale = float(value)

        if self.dimensionCount == 1:
            # update the intensities as the scale has changed
            self._intensities = self.getSliceData()

    @property
    @_includeInCopy
    def spinningRate(self) -> float:
        """NMR tube spinning rate (in Hz)."""
        return self._wrappedData.experiment.spinningRate

    @spinningRate.setter
    @logCommand(get='self', isProperty=True)
    def spinningRate(self, value: float):
        self._wrappedData.experiment.spinningRate = value

    @property
    @_includeInCopy
    def noiseLevel(self) -> float:
        """Estimated noise level for the spectrum,
        defined as the estimated standard deviation of the points from the baseplane/baseline"""
        return self._wrappedData.noiseLevel

    @noiseLevel.setter
    @logCommand(get='self', isProperty=True)
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
    @logCommand(get='self', isProperty=True)
    def negativeNoiseLevel(self, value):
        """Stored in Internal """
        propertyName = sys._getframe().f_code.co_name
        self.setParameter(self._AdditionalAttribute, propertyName, value)

    @property
    def synonym(self) -> Optional[str]:
        """Systematic experiment type descriptor (CCPN system)."""
        refExperiment = self._wrappedData.experiment.refExperiment
        if refExperiment is None:
            return None
        else:
            return refExperiment.synonym

    @property
    @_includeInCopy
    def experimentType(self) -> Optional[str]:
        """Systematic experiment type descriptor (CCPN system)."""
        refExperiment = self._wrappedData.experiment.refExperiment
        if refExperiment is None:
            return None
        else:
            return refExperiment.name

    @experimentType.setter
    @logCommand(get='self', isProperty=True)
    def experimentType(self, value: str):
        from ccpn.core.lib.SpectrumLib import _setApiExpTransfers, _setApiRefExperiment, _clearLinkToRefExp

        if value is None:
            self._wrappedData.experiment.refExperiment = None
            self.experimentName = None
            _clearLinkToRefExp(self._wrappedData.experiment)
            return
        # nmrExpPrototype = self._wrappedData.root.findFirstNmrExpPrototype(name=value) # Why not findFirst instead of looping all sortedNmrExpPrototypes
        for nmrExpPrototype in self._wrappedData.root.sortedNmrExpPrototypes():
            for refExperiment in nmrExpPrototype.sortedRefExperiments():
                if refExperiment.name == value:
                    # set API RefExperiment and ExpTransfer
                    _setApiRefExperiment(self._wrappedData.experiment, refExperiment)
                    _setApiExpTransfers(self._wrappedData.experiment)
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
    @_includeInCopy
    def experimentName(self) -> str:
        """Common experiment type descriptor (May not be unique)."""
        return self._wrappedData.experiment.name

    @experimentName.setter
    @logCommand(get='self', isProperty=True)
    def experimentName(self, value):
        # force to a string
        # because: reading from .nef files extracts the name from the end of the experiment_type in nef reader
        #           which is not wrapped with quotes, so defaults to an int if it can?
        self._wrappedData.experiment.name = str(value)

    @property
    def filePath(self) -> Optional[str]:
        """Absolute path to NMR data file."""
        xx = self._wrappedData.dataStore
        if xx:
            return xx.fullPath
        else:
            return None

    @filePath.setter
    @logCommand(get='self', isProperty=True)
    def filePath(self, value: str):

        apiDataStore = self._wrappedData.dataStore
        if apiDataStore is None:

            # # the spectrum does not have an attached file
            # numPoints = [x.numPoints for x in self._wrappedData.sortedDataDims()]
            # self._wrappedData.addDataStore(value, numPoints=numPoints)
            #
            # # need to save the file
            # from ccpn.util.Hdf5 import convertDataToHdf5
            # convertDataToHdf5(self, value)
            getLogger().warning("Spectrum is not stored, cannot change file path")
            # raise ValueError("Spectrum is not stored, cannot change file path")

        elif not value:
            getLogger().warning("Spectrum file path cannot be set to None")
            # raise ValueError("Spectrum file path cannot be set to None")

        else:
            # # NOTE:ED - original method
            # dataUrl = self._project._wrappedData.root.fetchDataUrl(value)
            # apiDataStore.repointToDataUrl(dataUrl)
            # apiDataStore.path = value[len(dataUrl.url.path) + 1:]
            # self._clearCache()
            # return

            oldName = apiDataStore.dataUrl.name
            newName = incrementName(oldName)
            dataUrl = self._project._wrappedData.root.fetchDataUrl(value, name=newName)
            apiDataStore.repointToDataUrl(dataUrl)
            apiDataStore.path = value[len(dataUrl.url.path) + 1:]
            self._clearCache()

    @property
    def path(self):
        """return a Path instance defining the absolute path of filePath
        """
        if self.filePath is None:
            # why do we need to raise a Runtime Error! path can be None. What about simulated spectra?
            # raise RuntimeError('filePath is not defined')
            self.filePath = ''
        return aPath(self.filePath)

    @property
    def isValidPath(self) -> bool:
        """Return true if the spectrum currently points to an existent file.
        (contents of the file are not checked)
        """
        if self.filePath is None:
            return False
        return aPath(self.filePath).exists() and aPath(self.filePath).is_file()

    @property
    def dataFormat(self):
        """Return the spectrum data-format identifier (e.g. Hdf5, NMRPipe)
        """
        xx = self._wrappedData.dataStore
        if xx:
            return xx.fileType
        else:
            return None

    @property
    def headerSize(self) -> Optional[int]:
        """File header size in bytes."""
        xx = self._wrappedData.dataStore
        if xx:
            return xx.headerSize
        else:
            return None

    @property
    def numberType(self) -> Optional[str]:
        """Data type of numbers stored in data matrix ('int' or 'float')."""
        xx = self._wrappedData.dataStore
        if xx:
            return xx.numberType
        else:
            return None

    @property
    def complexStoredBy(self) -> Optional[str]:
        """Hypercomplex numbers are stored by ('timepoint', 'quadrant', or 'dimension')."""
        xx = self._wrappedData.dataStore
        if xx:
            return xx.complexStoredBy
        else:
            return None

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
    @logCommand(get='self', isProperty=True)
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
    @_includeInDimensionalCopy
    def pointOffsets(self) -> Tuple[int, ...]:
        """index of first active point relative to total points, per dimension"""
        return tuple(x.pointOffset if x.className != 'SampledDataDim' else None
                     for x in self._wrappedData.sortedDataDims())

    @pointOffsets.setter
    def pointOffsets(self, value: Sequence):
        self._setStdDataDimValue('pointOffset', value)

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

    @property
    @_includeInDimensionalCopy
    def blockSizes(self) -> Tuple[int, ...]:
        """BlockSizes -  per dimension"""
        return tuple(self._apiDataStore.blockSizes)

    @blockSizes.setter
    def blockSizes(self, value: Sequence):
        apiDataSource = self._wrappedData
        if len(value) == apiDataSource.numDim:
            self._apiDataStore.blockSizes = value
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
    #     apiDataSource = self._wrappedData
    #     if len(value) == apiDataSource.numDim:
    #
    #         for dimValue in value:
    #             if dimValue not in DIMENSION_TYPES:
    #                 raise ValueError("DimensionType %s not recognised" % dimValue)
    #
    #         for n, dataDimVal in enumerate(self._wrappedData.sortedDataDims()):
    #             pass
    #
    #         # from NMR.Experiment - createDataSource
    #
    #         # self: 'Experiment', name: str, numPoints: Sequence[int], sw: Sequence[float],
    #         # refppm: Sequence[float], refpt: Sequence[float], dataStore: 'DataStore' = None,
    #         # scale: float = 1.0, details:str = None, numPointsOrig:Sequence[int] = None,
    #         # pointOffset: Sequence[int] = None, isComplex:Sequence[bool] = None,
    #         # sampledValues: Sequence[Sequence[float]] = None,
    #         # sampledErrors: Sequence[Sequence[float]] = None,
    #         # ** additionalParameters) -> 'DataSource':
    #
    #         # if not numPointsOrig:
    #         #     numPointsOrig = numPoints
    #         #
    #         # if not pointOffset:
    #         #     pointOffset = (0,) * numDim
    #         #
    #         # if not isComplex:
    #         #     isComplex = (False,) * numDim
    #         #
    #         # for n, expDim in enumerate(self.sortedExpDims()):
    #         #
    #         #     numPointsOrig = expDim.numPointsOrig
    #         #     pointOffset = expDim
    #         #     values = sampledValues[n] if sampledValues else None
    #         #     if values:
    #         #         errors = sampledErrors[n] if sampledErrors else None
    #         #         sampledDataDim = spectrum.newSampledDataDim(dim=n + 1, numPoints=numPoints[n], expDim=expDim,
    #         #                                                     isComplex=isComplex[n], pointValues=values, pointErrors=errors)
    #         #     else:
    #         #         freqDataDim = spectrum.newFreqDataDim(dim=n + 1, numPoints=numPoints[n],
    #         #                                               isComplex=isComplex[n], numPointsOrig=numPointsOrig[n],
    #         #                                               pointOffset=pointOffset[n],
    #         #                                               valuePerPoint=sw[n] / float(numPoints[n]), expDim=expDim)
    #         #         expDimRef = (expDim.findFirstExpDimRef(measurementType='Shift') or expDim.findFirstExpDimRef())
    #         #         if expDimRef:
    #         #             freqDataDim.newDataDimRef(refPoint=refpt[n], refValue=refppm[n], expDimRef=expDimRef)
    #
    #
    #             # dataDim classnames are FidDataDim, FreqDataDim, SampledDataDim
    #     else:
    #         raise ValueError("DimensionTypes must have length %s, was %s" % (apiDataSource.numDim, value))

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
    @logCommand(get='self', isProperty=True)
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
            raise ValueError("isotopeCodes must have length %s, was %s" % (apiDataSource.numDim, value))

    @property
    @_includeInDimensionalCopy
    def referenceExperimentDimensions(self) -> Tuple[Optional[str], ...]:
        """dimensions of reference experiment - None if no code"""
        result = []
        for dataDim in self._wrappedData.sortedDataDims():
            expDim = dataDim.expDim
            if expDim is None:
                result.append(None)
            else:
                referenceExperimentDimension = (expDim.ccpnInternalData and expDim.ccpnInternalData.get('expDimToRefExpDim')) or None
                result.append(referenceExperimentDimension)

        return tuple(result)

    @referenceExperimentDimensions.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def referenceExperimentDimensions(self, values: Sequence):
        apiDataSource = self._wrappedData

        if not isinstance(values, (tuple, list)):
            raise ValueError('referenceExperimentDimensions must be a list or tuple')
        if len(values) != apiDataSource.numDim:
            raise ValueError('referenceExperimentDimensions must have length %s, was %s' % (apiDataSource.numDim, values))
        if not all(isinstance(dimVal, (str, type(None))) for dimVal in values):
            raise ValueError('referenceExperimentDimensions must be str, None')
        _vals = [val for val in values if val is not None]
        if len(_vals) != len(set(_vals)):
            raise ValueError('referenceExperimentDimensions must be unique')

        for ii, (dataDim, val) in enumerate(zip(apiDataSource.sortedDataDims(), values)):
            expDim = dataDim.expDim
            if expDim is None and val is not None:
                raise ValueError('Cannot set referenceExperimentDimension %s in dimension %s' % (val, ii + 1))
            else:
                _update = {'expDimToRefExpDim': val}
                _ccpnInt = expDim.ccpnInternalData
                if _ccpnInt is None:
                    expDim.ccpnInternalData = _update
                else:
                    _expDimCID = expDim.ccpnInternalData.copy()
                    _ccpnInt.update(_update)
                    expDim.ccpnInternalData = _ccpnInt

    def getAvailableReferenceExperimentDimensions(self, _experimentType=None) -> tuple:
        """Return list of available reference experiment dimensions based on spectrum isotopeCodes
        """
        _refExperiment = None
        if _experimentType is not None:
            # search for the named reference experiment
            _refExperiment = self.project._getReferenceExperimentFromType(_experimentType)

        # get the nucleus codes from the current isotope codes
        nCodes = tuple(val.strip('0123456789') for val in self.isotopeCodes)

        # match against the current reference experiment or passed in value
        apiExperiment = self._wrappedData.experiment
        apiRefExperiment = _refExperiment or apiExperiment.refExperiment

        if apiRefExperiment:
            # get the permutations of the axisCodes and nucleusCodes
            axisCodePerms = permutations(apiRefExperiment.axisCodes)
            nucleusPerms = permutations(apiRefExperiment.nucleusCodes)

            # return only those that match the current nucleusCodes (from isotopeCodes)
            result = tuple(ac for ac, nc in zip(axisCodePerms, nucleusPerms) if nCodes == nc)
            return result

        else:
            return ()

    @property
    @_includeInDimensionalCopy
    def foldingModes(self) -> Tuple[Optional[str], ...]:
        """folding mode (values: 'circular', 'mirror', None), per dimension"""
        dd = {True: 'mirror', False: 'circular', None: None}
        return tuple(dd[x and x.isFolded] for x in self._mainExpDimRefs())

    @foldingModes.setter
    @logCommand(get='self', isProperty=True)
    def foldingModes(self, values):

        # TODO For NEF we should support both True, False, and None
        # That requires an API change

        dd = {'circular': False, 'mirror': True, None: False}

        if len(values) != self.dimensionCount:
            raise ValueError("Length of %s does not match number of dimensions." % str(values))
        if not all(isinstance(dimVal, (str, type(None))) and dimVal in dd.keys() for dimVal in values):
            raise ValueError("Folding modes must be 'circular', 'mirror', None")

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
    @cached(_REFERENCESUBSTANCESCACHE, maxItems=5000, debug=False)
    def referenceSubstances(self):
        """
        :return: a list of substances
        """
        pids = self._ccpnInternalData.get(self._ReferenceSubstancesPids) or []
        objs = _getObjectsByPids(self.project, pids)
        return objs

    @referenceSubstances.setter
    def referenceSubstances(self, substances):
        """
        """
        from ccpn.core.Substance import Substance

        pids = [su.pid for su in substances if isinstance(su, Substance)]
        if isinstance(self._ccpnInternalData, dict):
            tempCcpn = self._ccpnInternalData.copy()
            tempCcpn[self._ReferenceSubstancesPids] = pids
            self._ccpnInternalData = tempCcpn
        else:
            raise ValueError("Substance linked spectra CCPN internal must be a dictionary")

    @property
    def referenceSubstance(self):
        """
        Deprecated. See referenceSubstances
        """
        getLogger().warning('spectrum.referenceSubstance is deprecated. Use referenceSubstances instead. ')
        substance = None
        if len(self.referenceSubstances) > 0:
            substance = self.referenceSubstances[-1]
        return substance

    @referenceSubstance.setter
    def referenceSubstance(self, substance):
        getLogger().warning('spectrum.referenceSubstance is deprecated. Use referenceSubstances instead. ')
        self.referenceSubstances = [substance]

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

        tuple of tuples of (lowerAliasingLimit, higherAliasingLimit) for spectrum
        """
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
    @logCommand(get='self', isProperty=True)
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

        tuple of tuples of (ppmPoint(1), ppmPoint(n+1)) for each spectrum axis
        direction of axis is preserved
        """
        ll = []
        for ii, ddr in enumerate(self._mainDataDimRefs()):
            if ddr is None:
                ll.append((None, None))
            else:
                ll.append((ddr.pointToValue(1), ddr.pointToValue(ddr.dataDim.numPoints + 1)))
        return tuple(ll)

    @property
    def axesReversed(self) -> Tuple[Optional[bool], ...]:
        """Return whether any of the axes are reversed
        May contain None for undefined axes
        """
        return tuple((x and x.isAxisReversed) for x in self._mainExpDimRefs())

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
            getLogger().warning(
                    """An attempt to set Spectrum.magnetisationTransfers directly was ignored
                  because the spectrum experimentType was defined.
                  Use axisCodes to set magnetisation transfers instead.""")

    @property
    def intensities(self) -> np.ndarray:
        """ spectral intensities as NumPy array for 1D spectra
        """

        if self.dimensionCount != 1:
            getLogger().warning('Currently this method only works for 1D spectra')
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

        # NOTE:ED - temporary hack for showing straight the result of intensities change
        for spectrumView in self.spectrumViews:
            spectrumView.refreshData()

    @property
    def positions(self) -> np.array:
        """ spectral region in ppm as NumPy array for 1D spectra """

        if self.dimensionCount != 1:
            getLogger().warning('Currently this method only works for 1D spectra')
            return np.array([])

        if self._positions is None:
            self._positions = self.getPpmArray(dimension=1)

        return self._positions

    @positions.setter
    def positions(self, value):
        # self._scaleChanged = True
        self._positions = value

        # NOTE:ED - temporary hack for showing straight the result of intensities change
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
    def aliasingValues(self) -> Optional[Tuple[Tuple, ...]]:
        """Return a tuple of the aliasing values in each dimension, as multiples of the spectral width.
        This is a derived property from the aliasingLimits.
        """
        _alias = self.aliasingLimits
        _limits = self.spectrumLimits

        values = []
        for alias, lim in zip(_alias, _limits):
            width = abs(max(lim) - min(lim))
            minA, maxA = min(alias), max(alias)
            minLim, maxLim = min(lim), max(lim)
            values.append((int((minA - minLim + width / 2) // width), int((maxA - maxLim + width / 2) // width)))

        return tuple(values)

    @property
    def _seriesItems(self):
        """Return a tuple of the series items for the spectrumGroups
        """
        items = self.getParameter(SPECTRUMSERIES, SPECTRUMSERIESITEMS)
        if items is not None:
            series = ()
            for sg in self.spectrumGroups:
                if sg.pid in items:
                    series += (items[sg.pid],)
                else:
                    series += (None,)
            return series

    @_seriesItems.setter
    @ccpNmrV3CoreSetter()
    def _seriesItems(self, items):
        """Set the series items for all spectrumGroups that spectrum is attached to.
        Must be of the form ( <item1>,
                              <item2>,
                              ...
                              <itemN>
                            )
            where <itemsN> are of the same type (or None)
        """
        if not items:
            raise ValueError('items is not defined')
        if not isinstance(items, (tuple, list, type(None))):
            raise TypeError('items is not of type tuple/None')
        if len(items) != len(self.spectrumGroups):
            raise ValueError('Number of items does not match number of spectrumGroups')

        if isinstance(items, tuple):
            diffItems = set(type(item) for item in items)
            if len(diffItems) > 2 or (len(diffItems) == 2 and type(None) not in diffItems):
                raise ValueError('Items must be of the same type (or None)')

            seriesItems = self.getParameter(SPECTRUMSERIES, SPECTRUMSERIESITEMS)
            for sg, item in zip(self.spectrumGroups, items):
                if seriesItems:
                    seriesItems[sg.pid] = item
                else:
                    seriesItems = {sg.pid: item}
            self.setParameter(SPECTRUMSERIES, SPECTRUMSERIESITEMS, seriesItems)

        else:
            self.setParameter(SPECTRUMSERIES, SPECTRUMSERIESITEMS, None)

    def _getSeriesItem(self, spectrumGroup):
        """Return the series item for the current spectrum for the selected spectrumGroup
        """
        from ccpn.core.SpectrumGroup import SpectrumGroup

        spectrumGroup = self.project.getByPid(spectrumGroup) if isinstance(spectrumGroup, str) else spectrumGroup
        if not isinstance(spectrumGroup, SpectrumGroup):
            raise TypeError('%s is not a spectrumGroup' % str(spectrumGroup))
        if self not in spectrumGroup.spectra:
            raise ValueError('Spectrum %s does not belong to spectrumGroup %s' % (str(self), str(spectrumGroup)))

        seriesItems = self.getParameter(SPECTRUMSERIES, SPECTRUMSERIESITEMS)
        if seriesItems and spectrumGroup.pid in seriesItems:
            return seriesItems[spectrumGroup.pid]

    def _setSeriesItem(self, spectrumGroup, item):
        """Set the series item for the current spectrum for the selected spectrumGroup
        MUST be called from spectrumGroup - error checking for item types is handled there
        """
        from ccpn.core.SpectrumGroup import SpectrumGroup

        # check that the spectrumGroup and spectrum are valid
        spectrumGroup = self.project.getByPid(spectrumGroup) if isinstance(spectrumGroup, str) else spectrumGroup
        if not isinstance(spectrumGroup, SpectrumGroup):
            raise TypeError('%s is not a spectrumGroup', spectrumGroup)
        if self not in spectrumGroup.spectra:
            raise ValueError('Spectrum %s does not belong to spectrumGroup %s' % (str(self), str(spectrumGroup)))

        seriesItems = self.getParameter(SPECTRUMSERIES, SPECTRUMSERIESITEMS)

        if seriesItems:
            seriesItems[spectrumGroup.pid] = item
        else:
            seriesItems = {spectrumGroup.pid: item}
        self.setParameter(SPECTRUMSERIES, SPECTRUMSERIESITEMS, seriesItems)

    def _renameSeriesItems(self, spectrumGroup, oldPid):
        """rename the keys in the seriesItems to reflect the updated spectrumGroup name
        """
        seriesItems = self.getParameter(SPECTRUMSERIES, SPECTRUMSERIESITEMS)
        if oldPid in (seriesItems if seriesItems else ()):
            # insert new items with the new pid
            oldItems = seriesItems[oldPid]
            del seriesItems[oldPid]
            seriesItems[spectrumGroup.pid] = oldItems
            self.setParameter(SPECTRUMSERIES, SPECTRUMSERIESITEMS, seriesItems)

    def _getSeriesItemsById(self, id):
        """Return the series item for the current spectrum by 'id'
        CCPNINTERNAL: used in creating new spectrumGroups - not for external use
        """
        seriesItems = self.getParameter(SPECTRUMSERIES, SPECTRUMSERIESITEMS)
        if seriesItems and id in seriesItems:
            return seriesItems[id]

    def _setSeriesItemsById(self, id, item):
        """Set the series item for the current spectrum by 'id'
        CCPNINTERNAL: used in creating new spectrumGroups - not for external use
        """
        seriesItems = self.getParameter(SPECTRUMSERIES, SPECTRUMSERIESITEMS)
        if seriesItems:
            seriesItems[id] = item
        else:
            seriesItems = {id: item}
        self.setParameter(SPECTRUMSERIES, SPECTRUMSERIESITEMS, seriesItems)

    def _removeSeriesItemsById(self, spectrumGroup, id):
        """Remove the keys in the seriesItems allocated to 'id'
        CCPNINTERNAL: used in creating new spectrumGroups - not for external use
        """
        # useful for storing an item
        seriesItems = self.getParameter(SPECTRUMSERIES, SPECTRUMSERIESITEMS)
        if id in seriesItems:
            del seriesItems[id]
            self.setParameter(SPECTRUMSERIES, SPECTRUMSERIESITEMS, seriesItems)

    #=========================================================================================
    # Library functions
    #-----------------------------------------------------------------------------------------

    def ppm2point(self, value, axisCode=None, dimension=None):
        """Convert ppm value to point value for axis corresponding to either axisCode or
        dimension (1-based)
        """
        if dimension is None and axisCode is None:
            raise ValueError('Spectrum.ppm2point: either axisCode or dimension needs to be defined')
        if dimension is not None and axisCode is not None:
            raise ValueError('Spectrum.ppm2point: axisCode and dimension cannot be both defined')

        if axisCode is not None:
            dimension = self.getByAxisCodes('dimensions', [axisCode], exactMatch=False)[0]

        if dimension is None or dimension < 1 or dimension > self.dimensionCount:
            raise RuntimeError('Invalid dimension (%s)' % (dimension,))

        return self.spectrumReferences[dimension - 1].valueToPoint(value)

    def point2ppm(self, value, axisCode=None, dimension=None):
        """Convert point value to ppm for axis corresponding to to either axisCode or
        dimension (1-based)
        """
        if dimension is None and axisCode is None:
            raise ValueError('Spectrum.point2ppm: either axisCode or dimension needs to be defined')
        if dimension is not None and axisCode is not None:
            raise ValueError('Spectrum.point2ppm: axisCode and dimension cannot be both defined')

        if axisCode is not None:
            dimension = self.getByAxisCodes('dimensions', [axisCode], exactMatch=False)[0]

        if dimension is None or dimension < 1 or dimension > self.dimensionCount:
            raise RuntimeError('Invalid dimension (%s)' % (dimension,))

        return self.spectrumReferences[dimension - 1].pointToValue(value)

    def getPpmArray(self, axisCode=None, dimension=None):
        """Return a numpy array with ppm values of the grid points along axisCode or dimension
        """
        if dimension is None and axisCode is None:
            raise ValueError('Spectrum.getPpmArray: either axisCode or dimension needs to be defined')
        if dimension is not None and axisCode is not None:
            raise ValueError('Spectrum.getPpmArray: axisCode and dimension cannot be both defined')

        if axisCode is not None:
            dimension = self.getByAxisCodes('dimensions', [axisCode], exactMatch=False)[0]

        if dimension is None or dimension < 1 or dimension > self.dimensionCount:
            raise RuntimeError('Invalid dimension (%s)' % (dimension,))

        spectrumLimits = self.spectrumLimits[dimension - 1]
        axisReversed = self.axesReversed[dimension - 1]
        valuePerPoint = self.valuesPerPoint[dimension - 1] * (-1.0 if axisReversed else 1.0)

        result = np.linspace(spectrumLimits[0], spectrumLimits[1] - valuePerPoint, self.pointCounts[dimension - 1])

        return result

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
        return self._apiDataSource.estimateNoise()

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
        if not self.isValidPath:
            return

        startPoint = []
        endPoint = []

        # fill with the spectrum limits first
        regionToPick = sorted(self.spectrumLimits)

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
        """Clone 1D spectrum to a new spectrum."""
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

    # in baseclass
    # @deleteObject()
    # def _delete(self):
    #     """Delete the spectrum wrapped data.
    #     """
    #     self._wrappedData.delete()

    @cached.clear(_PLANEDATACACHE)  # Check if there was a planedata cache, and if so, clear it
    @cached.clear(_SLICEDATACACHE)  # Check if there was a slicedata cache, and if so, clear it
    @cached.clear(_SLICE1DDATACACHE)  # Check if there was a slice1ddata cache, and if so, clear it
    @cached.clear(_REGIONDATACACHE)  # Check if there was a regiondata cache, and if so, clear it
    @cached.clear(_REFERENCESUBSTANCESCACHE)
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
    @logCommand(get='self', isProperty=True)
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
            return tuple(order)

        # # set default ordering
        # self.setParameter(SPECTRUMAXES, SPECTRUMPREFERREDAXISORDERING, None)
        # return None

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

    def getPeakAliasingRanges(self):
        """Return the min/max aliasing Values for the peakLists in the spectrum, if there are no peakLists with peaks, return None
        """
        # get the aliasingRanges for non-empty peakLists
        aliasRanges = [peakList.getPeakAliasingRanges() for peakList in self.peakLists if peakList.peaks]

        if aliasRanges:
            # if there is only one then return it (for clarity)
            if len(aliasRanges) == 1:
                return aliasRanges[0]

            # get the value from all the peakLists
            newRanges = list(aliasRanges[0])
            for ii, alias in enumerate(aliasRanges[1:]):
                if alias is not None:
                    newRanges = tuple((min(minL, minR), max(maxL, maxR)) for (minL, maxL), (minR, maxR) in zip(alias, newRanges))

            return newRanges

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
        refs = self.mainSpectrumReferences
        if self.dimensionCount == 1:
            pp = refs[0].valueToPoint(ppmPositions[0])
            hs = self._intensities
            try:
                height = hs[int(pp) - 1] + (pp % 1) * (hs[int(pp)] - hs[int(pp) - 1])
            except IndexError:
                getLogger().warning('Height not found found at ppm position: (%s)' % ', '.join(map(str, ppmPositions)))
                height = None  # should it be None?
            return height

        if len(ppmPositions) != self.dimensionCount:
            raise ValueError('Length of %s does not match number of dimensions.' % str(ppmPositions))
        if not all(isinstance(dimVal, (int, float)) for dimVal in ppmPositions):
            raise ValueError('ppmPositions values must be floats.')

        pointPosition = tuple(refs[dim].valueToPoint(ppm) for dim, ppm in enumerate(ppmPositions))
        return self.getPositionValue(pointPosition)

    @logCommand(get='self')
    def getPositionValue(self, pointPosition):
        """Return the value nearest to the position given in points.
        """
        if len(pointPosition) != self.dimensionCount:
            raise ValueError('Length of %s does not match number of dimensions.' % str(pointPosition))
        if not all(isinstance(dimVal, (int, float)) for dimVal in pointPosition):
            raise ValueError('position values must be floats.')

        scale = self.scale if self.scale is not None else 1.0
        if -SCALETOLERANCE < scale < SCALETOLERANCE:
            getLogger().warning('Scaling {} by minimum tolerance (±{})'.format(self, SCALETOLERANCE))

        pointPosition = self._apiDataSource.getPositionValue(pointPosition)
        return pointPosition * scale if pointPosition else None

    @cached(_SLICE1DDATACACHE, maxItems=1, debug=False)
    def _get1DSliceData(self, position, sliceDim: int):
        """Internal routine to get 1D sliceData;
        """
        return self._apiDataSource.getSliceData(position=position, sliceDim=sliceDim)

    @cached(_SLICEDATACACHE, maxItems=1024, debug=False)
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
        if -SCALETOLERANCE < scale < SCALETOLERANCE:
            getLogger().warning('Scaling {} by minimum tolerance (±{})'.format(self, SCALETOLERANCE))

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

    @cached(_PLANEDATACACHE, maxItems=64, debug=False)
    def _getPlaneData(self, position, xDim: int, yDim: int):
        "Internal routine to improve caching: Calling routine set the positions of xDim, yDim to 1 "
        return self._apiDataSource.getPlaneData(position=position, xDim=xDim, yDim=yDim)

    @logCommand(get='self')
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

        scale = self.scale if self.scale is not None else 1.0
        if -SCALETOLERANCE < scale < SCALETOLERANCE:
            getLogger().warning('Scaling {} by minimum tolerance (±{})'.format(self, SCALETOLERANCE))

        result = self._getPlaneData(position=position, xDim=xDim, yDim=yDim)
        # Make a copy in order to preserve the original data and apply scaling
        result = result.copy(order='K') * scale

        # check if we have something valid to return
        if result is None:
            raise RuntimeError('Failed to get plane data along dimensions (%s,%s) at position %s' %
                               (xDim, yDim, position))

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

    @logCommand(get='self')
    def extractPlaneToFile(self, axisCodes: tuple, position=None, path=None):
        """Save plane defined by a tuple of two axisCodes and position
        to file. Save to path (auto-generated if None).

        :returns plane as Spectrum instance
        """
        if self.dimensionCount < 2:
            raise RuntimeError('Cannot extract plane from 1D data (%s)' % self)

        if position is None:
            position = [1] * 2

        if path is None:
            path = self._getDefaultPlanePath(axisCodes, position)

        planeData = self.getPlane(axisCodes=axisCodes, position=position)
        from ccpnmodel.ccpncore.lib._ccp.nmr.Nmr.DataSource import _saveNmrPipe2DHeader

        with open(path, 'wb') as fp:
            #TODO: remove dependency on filestorage on apiLayer
            xDim, yDim = self.getByAxisCodes('dimensions', axisCodes)[0:2]
            _saveNmrPipe2DHeader(self._wrappedData, fp, xDim, yDim)
            planeData.tofile(fp)

        newSpectrum = self.project.loadSpectrum(path, subType=Formats.NMRPIPE)[0]
        newSpectrum.axisCodes = axisCodes  # to override the loadSpectrum routine
        self.copyParameters(axisCodes=axisCodes, target=newSpectrum)
        return newSpectrum

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

        from ccpnmodel.ccpncore.lib._ccp.nmr.Nmr.DataSource import _saveNmrPipe2DHeader

        with open(path, 'wb') as fp:
            #TODO: remove dependency on filestorage on apiLayer
            xDim, yDim = self.getByAxisCodes('dimensions', axisCodes)[0:2]
            _saveNmrPipe2DHeader(self._wrappedData, fp, xDim, yDim)
            projectedData.tofile(fp)

        _spectraLoaded = self.project.loadSpectrum(path, subType=Formats.NMRPIPE)
        if _spectraLoaded and len(_spectraLoaded) == 1:
            newSpectrum = _spectraLoaded[0]
            newSpectrum.axisCodes = axisCodes  # to override the loadSpectrum routine
            self.copyParameters(axisCodes=axisCodes, target=newSpectrum)
            return newSpectrum
        else:
            raise TypeError('No spectra created')

    def _addDataStore(self, filePath, **kwds):
        """Add a new dataStore to the spectrum
        """
        self._wrappedData.addDataStore(filePath, **kwds)

    # GWV 20190731: not used
    # def get1dSpectrumData(self):
    #     """Get position,scaledData numpy array for 1D spectrum.
    #     Yields first 1D slice for nD"""
    #     return self._apiDataSource.get1dSpectrumData()

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _restoreObject(cls, project, apiObj):
        """Subclassed to allow for initialisations on restore, not on creation via newSpectrum
        """
        from ccpn.core._implementation.patches.patch_3_0_4 import scaleBrukerSpectrum, NC_PROC
        spectrum = super()._restoreObject(project, apiObj)

        # # For Bruker spectra: Set a NC_proc derived correction to spectrum.scale
        # if spectrum.dataFormat == 'Bruker' and not spectrum._hasInternalParameter(NC_PROC):
        #     scaleBrukerSpectrum(spectrum)

        return spectrum

    @classmethod
    def _getAllWrappedData(cls, parent: Project) -> list:
        """get wrappedData (Nmr.DataSources) for all Spectrum children of parent Project"""
        return list(x for y in parent._wrappedData.sortedExperiments() for x in y.sortedDataSources())

    @renameObject()
    @logCommand(get='self')
    def rename(self, value: str):
        """Rename Spectrum, changing its name and Pid.
        """
        return self._rename(value)

    def _finaliseAction(self, action: str):
        """Subclassed to handle associated spectrumViews instances
        """
        if not super()._finaliseAction(action):
            return

        # notify peak/integral/multiplet list
        if action in ['create', 'delete']:
            for peakList in self.peakLists:
                peakList._finaliseAction(action)
            for multipletList in self.multipletLists:
                multipletList._finaliseAction(action)
            for integralList in self.integralLists:
                integralList._finaliseAction(action)

        # propagate the rename to associated spectrumViews
        if action in ['change']:
            for specView in self.spectrumViews:
                if specView:
                    if self._scaleChanged:
                        # force a rebuild of the contours/etc.
                        specView.buildContoursOnly = True
                    specView._finaliseAction(action)

            if self._scaleChanged:
                self._scaleChanged = False

                # notify peaks/multiplets/integrals that the scale has changed
                for peakList in self.peakLists:
                    for peak in peakList.peaks:
                        peak._finaliseAction(action)
                for multipletList in self.multipletLists:
                    for multiplet in multipletList.multiplets:
                        multiplet._finaliseAction(action)
                for integralList in self.integralLists:
                    for integral in integralList.integrals:
                        integral._finaliseAction(action)

            # from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier
            #
            # GLSignals = GLNotifier(parent=self)
            # GLSignals.emitPaintEvent()

    @logCommand(get='self')
    def delete(self):
        """Delete Spectrum"""
        with undoBlock():
            self._clearCache()

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
                obj._delete()

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

    def _deleteChild(self, child):
        """Delete child object
        child is Pid or V3 object
        If child exists and is a valid child then delete otherwise log a warning
        """
        child = self.project.getByPid(child) if isinstance(child, str) else child

        if child and child in self._getChildrenByClass(child):
            # only delete objects that are valid children - calls private _delete
            # so now infinite loop with baseclass delete
            child._delete()
        elif child:
            getLogger().warning(f'{child} not deleted - not child of {self}')
        else:
            getLogger().warning(f'{child} not deleted')

    def _deletePeakList(self, child):
        """Delete child object and ensure that there always exists at least one peakList
        """
        with undoBlock():
            self._deleteChild(child)
            if not self.peakLists:
                # if there are no peakLists then create another (there must always be one)
                self.newPeakList()

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    def _resetPeakLists(self):
        """Delete autocreated peaklists and reset
        CCPN Internal - not for general use
        required by nef importer
        """
        for peakList in list(self.peakLists):
            # overrides spectrum contains at least one peakList
            self._deleteChild(peakList)
        self._wrappedData.__dict__['_serialDict']['peakLists'] = 0

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
                         multipletAveraging=None,
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
