"""
This file contains the ABC wrapper around the model datasource stuff (fail to define a better name)

it serves as an interface between the V3 Spectrum class and the actual spectral data formats
of different flavours (e.g. Bruker, NmrPipe, Azara, Felix, Varian/Agilent, Hdf5 (internal), etc)

the core methods are:

checkForValidFormat()       classmethod; check if valid format corresponding to dataFormat;
                            returns True/False

readParameters()            read paramters from spectral data format
                            (to be subclassed; call super().readParameters() before returning)
writeParameters()           write parameters to spectral data format (currently hdf5 and NmrPipe only)
                            (to be subclassed)

copyParametersTo()          copy parameters from self to a target SpectrumDataSource instance
copyDataTo()                copy data from self to target SpectrumDataSource instance

copyParametersFrom()        copy parameters from a source to self
copyDataFrom()              copy data from self a source to self

importFromSpectrum()        import parameters (and optionally path) from a Spectrum instance
exportToSpectrum()          export parameters (and optionally path) to a Spectrum instance

getByDimension()            Get specific parameter in dimension order
setByDimension()            Set specific parameter in dimension order

getSliceData()              get 1D slice (to be subclassed)
setSliceData()              set 1D slice (to be subclassed; specific formats only)

getPlaneData()              get 2D plane (to be subclassed)
setPlaneData()              set 2D plane (to be subclassed; specific formats only)

getPointData()              Get value defined by position (1-based, integer values)
getPointValue()             Get interpolated value defined by position (1-based, float values)

getRegionData()             Return an numpy array containing the points defined by
                            sliceTuples=[(start_1,stop_1), (start_2,stop_2), ...], (1, based, optional aliasing)

setPath                     define valid path to a (binary) data file, if needed appends or substitutes the suffix (if defined);
                            use path attribute to obtain Path instance to the absolute path of the data file

openExistingFile()          opens an existing file; used in "with" statement; yields the instance
openNewFile()               opens a new file; used in "with" statement; yields the instance
closeFile()                 closes file

allPlanes()                 yields a (position, planeData) tuple iterator over all planes
allSlices()                 yields a (position, sliceData) tuple iterator over all slices
allPoints()                 yields a (position, point) tuple iterator over all points


Example 1 (No Spectrum instance used):

    with AzaraSpectrumDataSource().openExistingFile(inputPath) as input:

        output = Hdf5SpectrumDataSource().copyParametersFrom(input)

        with output.openNewFile(outputPath):
            for position, data in input.allPlanes(xDim=1, yDim=2):
                output.setPlaneData(data, position=position, xDim=1, yDim=2)


Example 2 (with Spectrum instance):

    sp = get('SP:hnca')
    axes = ('H','N')
    xDim, yDim = sp.getByAxisCode('dimensions', axes)

    with Hdf5SpectrumDataSource(spectrum=sp).openNewFile(outputPath) as output:
        for position, data in sp.allPlanes(axes, exactMatch=False):
            output.setPlaneData(data, position=position, xDim=xDim, yDim=yDim)

Example 3 (using Spectrum instance to make a hdf5 duplicate):

    sp = get('SP:hnca')
    outputPath = 'myCopiedHNCA.hdf5'

    with Hdf5SpectrumDataSource(spectrum=sp).openNewFile(outputPath) as output:
        output.copyDataFrom(sp._dataSource)
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-02-05 17:08:23 +0000 (Fri, February 05, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2020-11-20 10:28:48 +0000 (Fri, November 20, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys
from typing import Sequence
from contextlib import contextmanager
from collections import OrderedDict

import tempfile

import numpy

from ccpn.util.Common import isIterable
from ccpn.util.Path import aPath
from ccpn.util.Logging import getLogger
from ccpn.core.Spectrum import Spectrum, DIMENSIONFREQUENCY, DIMENSIONFID
from ccpn.core.lib.ContextManagers import notificationEchoBlocking
from ccpn.util.isotopes import findNucleiFromSpectrometerFrequencies, Nucleus
from ccpn.core.lib.Cache import cached, Cache
from ccpn.util.traits.CcpNmrTraits import CFloat, CInt, CBool, Bool, List, \
    CString, CList
from ccpn.util.traits.CcpNmrJson import CcpNmrJson

from ccpn.framework.constants import CCPNMR_PREFIX

_BLOCK_CACHE = CCPNMR_PREFIX + 'block_cache'
# _BLOCK_CACHE_MAXITEMS = 128
MB = 1024*1024


def getDataFormats() -> OrderedDict:
    """Get spectrum datasource formats

    :return: a dictonary of (format-identifier-strings, SpectrumDataSource classes) as (key, value) pairs
    """
    # The following imports are just to assure that all the classes have been imported
    # It is local to prevent circular imports
    from ccpn.core.lib.SpectrumDataSources.Hdf5SpectrumDataSource import Hdf5SpectrumDataSource
    from ccpn.core.lib.SpectrumDataSources.AzaraSpectrumDataSource import AzaraSpectrumDataSource
    from ccpn.core.lib.SpectrumDataSources.FelixSpectrumDataSource import FelixSpectrumDataSource
    from ccpn.core.lib.SpectrumDataSources.BrukerSpectrumDataSource import BrukerSpectrumDataSource
    from ccpn.core.lib.SpectrumDataSources.UcsfSpectrumDataSource import UcsfSpectrumDataSource
    from ccpn.core.lib.SpectrumDataSources.XeasySpectrumDataSource import XeasySpectrumDataSource
    from ccpn.core.lib.SpectrumDataSources.NmrViewSpectrumDataSource import NmrViewSpectrumDataSource
    from ccpn.core.lib.SpectrumDataSources.NmrPipeSpectrumDataSource import NmrPipeSpectrumDataSource
    from ccpn.core.lib.SpectrumDataSources.EmptySpectrumDataSource import EmptySpectrumDataSource
    return SpectrumDataSourceABC._dataFormats


def getSpectrumDataSource(path, dataFormat):
    """Get a SpectrumDataSource instance of type format for path or None if incorrect
    """
    dataFormats = getDataFormats()
    cls = dataFormats.get(dataFormat)
    if cls is None:
        raise ValueError('getSpectrumDataSource: invalid format "%s"; must be one of %s' %
                         (dataFormat, [k for k in dataFormats.keys()])
                        )
    instance = cls.checkForValidFormat(path)
    return instance


def checkPathForSpectrumFormats(path):
    """Check path if it corresponds to any spectrum data format

    return a SpectrumDataSource instance with parameters read
           or None if there was no match
    """
    for fmt, cls in getDataFormats().items():
        instance = cls.checkForValidFormat(path)
        if instance is not None:
            return instance  # we found a valid format for path
    return None


class SpectrumDataSourceABC(CcpNmrJson):
    """
    ABC for NMR spectral data sources reading/writing
    """

    MAXDIM = Spectrum.MAXDIM  # currently set to 8

    X_AXIS = Spectrum.X_AXIS
    Y_AXIS = Spectrum.Y_AXIS
    Z_AXIS = Spectrum.Z_AXIS
    A_AXIS = Spectrum.A_AXIS
    B_AXIS = Spectrum.B_AXIS
    C_AXIS = Spectrum.C_AXIS
    D_AXIS = Spectrum.D_AXIS
    E_AXIS = Spectrum.E_AXIS
    UNDEFINED_AXIS = Spectrum.UNDEFINED_AXIS
    axisNames = Spectrum.axisNames

    X_DIM = Spectrum.X_DIM
    Y_DIM = Spectrum.Y_DIM
    Z_DIM = Spectrum.Z_DIM
    A_DIM = Spectrum.A_DIM
    B_DIM = Spectrum.B_DIM
    C_DIM = Spectrum.C_DIM
    D_DIM = Spectrum.D_DIM
    E_DIM = Spectrum.E_DIM

    dataType = numpy.float32   # numpy data format of the resulting slice, plane, region data

    #=========================================================================================
    # to be subclassed
    #=========================================================================================
    dataFormat = None  # string defining format type

    isBlocked = None  # flag defining if data are blocked
    hasBlockCached = True  # Flag indicating if block data are cached
    maxCacheSize = 64*MB  # Max cache size in Bytes

    wordSize = 4
    headerSize = 0
    blockHeaderSize = 0
    isFloatData = True
    hasWritingAbility = False  # flag that defines if dataFormat implements writing methods

    suffixes = []  # potential suffixes of data file; first is taken as default; [None] is defined as no suffix
    openMethod = None  # method to open the file as openMethod(path, mode)
    defaultOpenReadMode = 'r+'
    defaultOpenWriteMode = 'w'

    #=========================================================================================
    # data formats
    #=========================================================================================
    # A dict of registered dataFormat: filled by _registerFormat classmethod, called once after
    # each definition of a new derived class (e.g. Hdf5SpectrumDataSource)
    _dataFormats = OrderedDict()

    @classmethod
    def _registerFormat(cls):
        "register cls.dataFormat"
        if cls.dataFormat in SpectrumDataSourceABC._dataFormats:
            raise RuntimeError('dataFormat "%s" was already registered' % cls.dataFormat)
        SpectrumDataSourceABC._dataFormats[cls.dataFormat] = cls

    #=========================================================================================
    # parameter definitions and mappings onto the Spectrum class
    #=========================================================================================
    keysInOrder = True  # maintain the definition order

    _bigEndian = (sys.byteorder == 'big')


    saveAllTraitsToJson = True

    date = CString(allow_none=True, default_value=None).tag(
                                                                isDimensional=False,
                                                                doCopy=True,
                                                                spectrumAttribute=None,
                                                                hasSetterInSpectrumClass=False
                                                                )
    comment = CString(allow_none=True, default_value=None).tag(
                                                                isDimensional=False,
                                                                doCopy=True,
                                                                spectrumAttribute='comment',
                                                                hasSetterInSpectrumClass=True
                                                                )
    pulseProgram = CString(allow_none=True, default_value=None).tag(
                                                                isDimensional=False,
                                                                doCopy=True,
                                                                spectrumAttribute=None,
                                                                hasSetterInSpectrumClass=False
                                                                )
    temperature = CFloat(allow_none=True, default_value=None).tag(
                                                                isDimensional=False,
                                                                doCopy=True,
                                                                spectrumAttribute='temperature',
                                                                hasSetterInSpectrumClass=True
                                                                )
    isBigEndian = Bool(default_value=_bigEndian).tag(           isDimensional=False,
                                                                doCopy=True,
                                                                spectrumAttribute=None,
                                                                hasSetterInSpectrumClass=False
                                                                )
    dataScale = CFloat(default_value=1.0).tag(                  isDimensional=False,
                                                                doCopy=True,
                                                                spectrumAttribute='scale',
                                                                hasSetterInSpectrumClass=True
                                                                )
    sampledValues = List(default_value=[]).tag(                 isDimensional=False,
                                                                doCopy=True,
                                                                spectrumAttribute=None,
                                                                hasSetterInSpectrumClass=False
                                                                )
    sampledSigmas = List(default_value=[]).tag(                 isDimensional=False,
                                                                doCopy=True,
                                                                spectrumAttribute=None,
                                                                hasSetterInSpectrumClass=False
                                                                )
    dimensionCount = CInt(default_value=0).tag(                 isDimensional=False,
                                                                doCopy=True,
                                                                spectrumAttribute='dimensionCount',
                                                                hasSetterInSpectrumClass=False
                                                                )

    # dimension order mappings e.g. used by NmrPipe, Xeasy
    dimensionOrder = CList(trait=CInt(), default_value=[dim for dim in range(0,MAXDIM)], maxlen=MAXDIM).tag(
                                                                info='A (optional) mapping index into the dimensional data',
                                                                isDimensional=True,
                                                                doCopy=True,
                                                                spectrumAttribute=None,
                                                                hasSetterInSpectrumClass=False
                                                                )

    pointCounts = CList(trait=CInt(allow_none=False), default_value=[0]*MAXDIM, maxlen=MAXDIM).tag(
                                                                isDimensional=True,
                                                                doCopy=True,
                                                                spectrumAttribute='pointCounts',
                                                                hasSetterInSpectrumClass=True
                                                                )
    blockSizes = CList(trait=CInt(allow_none=True), default_value=[None]*MAXDIM, maxlen=MAXDIM).tag(
                                                                isDimensional=True,
                                                                doCopy=False,
                                                                spectrumAttribute=None,
                                                                hasSetterInSpectrumClass=False
                                                                )
    #TODO dimensionTypes needs setting in Spectrum class
    dimensionTypes = CList(trait=CString(allow_none=False), default_value=[DIMENSIONFREQUENCY]*MAXDIM, maxlen=MAXDIM).tag(
                                                                isDimensional=True,
                                                                doCopy=True,
                                                                spectrumAttribute='dimensionTypes',
                                                                hasSetterInSpectrumClass=False
                                                                )
    isComplex = CList(trait=CBool(), default_value=[False]*MAXDIM, maxlen=MAXDIM).tag(
                                                                isDimensional=True,
                                                                doCopy=True,
                                                                spectrumAttribute='isComplex',
                                                                hasSetterInSpectrumClass=True
                                                                )
    isotopeCodes = CList(trait=CString(allow_none=True), default_value=[None]*MAXDIM, maxlen=MAXDIM).tag(
                                                                isDimensional=True,
                                                                doCopy=True,
                                                                spectrumAttribute='isotopeCodes',
                                                                hasSetterInSpectrumClass=True
                                                                )
    axisCodes = CList(trait=CString(allow_none=True), default_value=[None]*MAXDIM, maxlen=MAXDIM).tag(
                                                                isDimensional=True,
                                                                doCopy=True,
                                                                spectrumAttribute='axisCodes',
                                                                hasSetterInSpectrumClass=True
                                                                )
    acquisitionAxisCode = CString(allow_none=True, default_value=None).tag(
                                                                isDimensional=False,
                                                                doCopy=True,
                                                                spectrumAttribute='acquisitionAxisCode',
                                                                hasSetterInSpectrumClass=True
                                                                )
    axisLabels = CList(trait=CString(allow_none=True), default_value=[None]*MAXDIM, maxlen=MAXDIM).tag(
                                                                isDimensional=True,
                                                                doCopy=True,
                                                                spectrumAttribute=None,
                                                                hasSetterInSpectrumClass=False,
                                                                info='per dimension: labels, as e.g. present in Felix or NmrPipe',
                                                                )
    measurementTypes = CList(trait=CString(allow_none=True), default_value=['shift']*MAXDIM, maxlen=MAXDIM).tag(
                                                                isDimensional=True,
                                                                doCopy=True,
                                                                spectrumAttribute='measurementTypes',
                                                                hasSetterInSpectrumClass=True,
                                                                )
    spectrometerFrequencies = CList(trait=CFloat(allow_none=False), default_value=[1.0]*MAXDIM, maxlen=MAXDIM).tag(
                                                                isDimensional=True,
                                                                doCopy=True,
                                                                spectrumAttribute='spectrometerFrequencies',
                                                                hasSetterInSpectrumClass=True,
                                                                )
    spectralWidthsHz = CList(trait=CFloat(allow_none=False), default_value=[1.0]*MAXDIM, maxlen=MAXDIM).tag(
                                                                isDimensional=True,
                                                                doCopy=True,
                                                                spectrumAttribute='spectralWidthsHz',
                                                                hasSetterInSpectrumClass=True,
                                                                )
    referencePoints = CList(trait=CFloat(allow_none=False), default_value=[1.0]*MAXDIM, maxlen=MAXDIM).tag(
                                                                isDimensional=True,
                                                                doCopy=True,
                                                                spectrumAttribute='referencePoints',
                                                                hasSetterInSpectrumClass=True,
                                                                )
    referenceValues = CList(trait=CFloat(allow_none=False), default_value=[1.0]*MAXDIM, maxlen=MAXDIM).tag(
                                                                isDimensional=True,
                                                                doCopy=True,
                                                                spectrumAttribute='referenceValues',
                                                                hasSetterInSpectrumClass=True,
                                                                )
    phases0 = CList(trait=CFloat(allow_none=True), default_value=[None]*MAXDIM, maxlen=MAXDIM).tag(
                                                                isDimensional=True,
                                                                doCopy=True,
                                                                spectrumAttribute='phases0',
                                                                hasSetterInSpectrumClass=True,
                                                                )
    phases1 = CList(trait=CFloat(allow_none=True), default_value=[None]*MAXDIM, maxlen=MAXDIM).tag(
                                                                isDimensional=True,
                                                                doCopy=True,
                                                                spectrumAttribute='phases1',
                                                                hasSetterInSpectrumClass=True,
                                                                )
    windowFunctions = CList(trait=CString(allow_none=True), default_value=[None]*MAXDIM, maxlen=MAXDIM).tag(
                                                                isDimensional=True,
                                                                doCopy=True,
                                                                spectrumAttribute='windowFunctions',
                                                                hasSetterInSpectrumClass=True,
                                                                info='per dimension: Window function name (or None) - e.g. "EM", "GM", "SINE", "QSINE"'
                                                                )
    lorentzianBroadenings = CList(trait=CFloat(allow_none=True), default_value=[None]*MAXDIM, maxlen=MAXDIM).tag(
                                                                isDimensional=True,
                                                                doCopy=True,
                                                                spectrumAttribute='lorentzianBroadenings',
                                                                hasSetterInSpectrumClass=True,
                                                                info='per dimension: Lorenzian broadening in Hz'
                                                                )
    gaussianBroadenings = CList(trait=CFloat(allow_none=True), default_value=[None]*MAXDIM, maxlen=MAXDIM).tag(
                                                                isDimensional=True,
                                                                doCopy=True,
                                                                spectrumAttribute='gaussianBroadenings',
                                                                hasSetterInSpectrumClass=True,
                                                                info='per dimension: Gaussian broadening in Hz'
                                                                )
    assignmentTolerances = CList(trait=CFloat(allow_none=True), default_value=[None]*MAXDIM, maxlen=MAXDIM).tag(
                                                                isDimensional=True,
                                                                doCopy=True,
                                                                spectrumAttribute='assignmentTolerances',
                                                                hasSetterInSpectrumClass=True,
                                                                info='per dimension: Assignment tolerance in ppm'
                                                                )

    #=========================================================================================
    # Convenience properties and methods
    #=========================================================================================

    def isDimensionalParameter(self, parameterName) -> bool:
        ":return True if parameterName is dimensional"
        return self.getMetadata(parameterName, 'isDimensional')

    def getDimensionalParameters(self) -> OrderedDict:
        "Return a OrderedDict of (parameterName, values) for dimensional parameters"
        items = [i for i in self.items(isDimensional=lambda i:i)]
        return OrderedDict(items)

    def getNonDimensionalParameters(self) -> OrderedDict:
        "Return a OrderedDict of (parameterName, values) for non-dimensional parameters"
        items = [i for i in self.items(isDimensional=lambda i: not i)]
        return OrderedDict(items)

    @property
    def dimensions(self):
        """A one-based list of dimensions [1,dimensionCount]
        """
        return range(1, self.dimensionCount+1)

    @property
    def axes(self):
        """A zero-based list of axes [0,dimensionCount-1]
        """
        return [i for i in range(0, self.dimensionCount)]

    @property
    def totalNumberOfPoints(self):
        "Total number of points of the data"
        result = self.pointCounts[0]
        for axis in self.axes[1:]:
            result *= self.pointCounts[axis]
        return result

    @property
    def expectedFileSizeInBytes(self):
        "The expected file size in Bytes"
        if self.dimensionCount == 0:
            raise RuntimeError('%s: Undefined parameters' % self)

        if self.isBlocked:
            result = (self.headerSize + self._totalBlockSize * self._totalBlocks) * self.wordSize
        else:
            result = (self.headerSize + self.totalNumberOfPoints) * self.wordSize

        return result

    #=========================================================================================
    # start of methods
    #=========================================================================================

    def __init__(self, path=None, spectrum=None, dimensionCount=None):
        """initialise instance; optionally set path or associate with and import from
        a Spectrum instance or set dimensionCount

        :param path: optional, path of the (binary) spectral data
        :param spectrum: associate instance with spectrum and import spectrum's parameters
        :param dimensionCount: limit instance to dimensionCount dimensions
        """
        if self.dataFormat is None:
            raise RuntimeError('Subclassed attribute "dataFormat" of class "%s" needs to be defined' % self.__class__.__name__)
        if self.isBlocked is None:
            raise RuntimeError('Subclassed attribute "isBlocked" of class "%s" needs to be defined' % self.__class__.__name__)
        if len(self.suffixes) == 0:
            raise RuntimeError('Subclassed attribute "suffixes" of class "%s" needs to be defined' % self.__class__.__name__)
        if self.openMethod is None:
            raise RuntimeError('Subclassed attribute "openMethod" of class "%s" needs to be defined' % self.__class__.__name__)

        super().__init__()

        self.dataFile = None  # Absolute path of the binary data; set by setPath method
        self.fp = None  # File pointer; None indicates closed
        self.mode = None  # Open mode

        self.hdf5buffer = None  # Hdf5SpectrumBuffer instance; None indicates no Hdf5 buffer used
        self.spectrum = None  # Spectrum instance

        self.setDefaultParameters()

        if path is not None:
            self.setPath(path)
        if spectrum is not None:
            self.importFromSpectrum(spectrum, includePath=False)
        if dimensionCount is not None:
            self.setDimensionCount(dimensionCount)

        # initiate the block cache
        self._initBlockCache()  # This wil initiate the cache instance
        if not self.hasBlockCached:
            self.disableCache()

    def setDefaultParameters(self, nDim=MAXDIM):
        """Set default values for all parameters
        """
        for par in self.keys():
            self.setTraitDefaultValue(par)

    def _assureProperDimensionality(self):
        """Assure proper dimensionality for all relevant parameters
        """
        for par, values in self.getDimensionalParameters().items():
            values = list(values)
            if len(values) < self.dimensionCount:
                values += self.getTraitDefaultValue(par)
            values = values[0:self.dimensionCount]
            self.setTraitValue(par,values)

    @property
    def path(self) -> aPath:
        "Return an absolute path of datapath as a Path instance"
        return (None if self.dataFile is None else aPath(self.dataFile))

    def setPath(self, path, substituteSuffix=False):
        """define valid path to a (binary) data file, if needed appends or substitutes the suffix (if defined).

        return self or None on error
        """
        if path is None:
            self.dataFile = None  # A reset essentially

        else:
            _p = aPath(path)
            if self.suffixes[0] is not None and _p.suffix not in self.suffixes:
                if substituteSuffix:
                    _p = _p.with_suffix(self.suffixes[0])
                else:
                    _p = _p + self.suffixes[0]
            self.dataFile = str(_p)
        return self

    def checkPath(self, path, mode='r') -> bool:
        """Check if path exists (mode='r') or parent of path exists (not mode='r');
        return True if ok; False otherwise
        """
        _p = aPath(path)

        if _p is None:
            return False

        # read-mode: check if it exists
        if mode.startswith('r') and _p.exists():
            return True

        # write-mode: check if parent exists
        if not mode.startswith('r') and _p.parent.exists():
            return True

        return False

    def getByDimensions(self, parameterName: str, dimensions: Sequence[int]):
        """Return values defined by parameterName in order defined by dimensions (1..dimensionCount).
        """
        if not self.hasTrait(parameterName):
            raise ValueError('%s: no parameter %r' % (self.__class__.__name__, parameterName))
        if not self.isDimensionalParameter(parameterName):
            raise ValueError('%s: parameter %r is not dimensional' % (self.__class__.__name__, parameterName))
        for dim in dimensions:
            if dim < 1 or dim > self.dimensionCount:
                raise ValueError('invalid dimension "%s" in %r' % (dim, dimensions))
        values = self.getTraitValue(parameterName)
        return [values[dim-1] for dim in dimensions]

    def setByDimensions(self, parameterName: str, values: Sequence, dimensions: Sequence[int]):
        """Set values defined by parameterName in order defined by dimensions (1..dimensionCount).
        """
        if not self.hasTrait(parameterName):
            raise ValueError('%s: no parameter %r' % (self.__class__.__name__, parameterName))
        if not self.isDimensionalParameter(parameterName):
            raise ValueError('%s: parameter %r is not dimensional' % (self.__class__.__name__, parameterName))
        for dim in dimensions:
            if dim < 1 or dim > self.dimensionCount:
                raise ValueError('invalid dimension "%s" in %r' % (dim, dimensions))
        newValues = values[:]
        for idx, dim in enumerate(dimensions):
            newValues[dim-1] = values[idx]
        self.setTraitValue(parameterName, newValues)

    def _copyParametersFromSpectrum(self, spectrum):
        """Copy parameters values from a Spectrum instance
        """
        for param in self.keys():
            doCopy = self.getMetadata(param, 'doCopy')
            spectrumAttribute = self.getMetadata(param, 'spectrumAttribute')
            if spectrumAttribute is not None and doCopy:
                values = getattr(spectrum, spectrumAttribute)
                self.setTraitValue(param, values)

    def _copyParametersToSpectrum(self, spectrum):
        """Copy parameter values to a Spectrum instance
        """
        for param in self.keys():
            doCopy = self.getMetadata(param, 'doCopy')
            spectrumAttribute = self.getMetadata(param, 'spectrumAttribute')
            hasSetter = self.getMetadata(param, 'hasSetterInSpectrumClass')
            if spectrumAttribute is not None and doCopy and hasSetter:
                values = self.getTraitValue(param)
                setattr(spectrum, spectrumAttribute, values)

    def importFromSpectrum(self, spectrum, includePath=True):
        """copy parameters & path (optionally) from spectrum, set spectrum attribute and return self
        """
        if spectrum is None:
            raise ValueError('Undefined spectrum; cannot import parameters')

        if not isinstance(spectrum, Spectrum):
            raise TypeError('%s.importFromSpectrum: Wrong spectrum class type; got %s' %
                            (self.__class__.__name__, spectrum))

        self._copyParametersFromSpectrum(spectrum)
        self._assureProperDimensionality()
        if spectrum.filePath is not None and includePath:
            self.setPath(spectrum.filePath, substituteSuffix=True)
        self.spectrum = spectrum
        return self

    def exportToSpectrum(self, spectrum, includePath=True):
        """copy parameters & path (optionally) to spectrum, set spectrum attribute, and return self
        """
        if spectrum is None:
            raise ValueError('Undefined spectrum; cannot export parameters')

        if not isinstance(spectrum, Spectrum):
            raise TypeError('%s.exportSpectrum: Wrong spectrum class type; got %s' %
                            (self.__class__.__name__, spectrum))

        self._copyParametersToSpectrum(spectrum)
        if self.dataFile is not None and includePath:
            spectrum.filePath = self.dataFile
        self.spectrum = spectrum
        return self

    def importFromDataSource(self, dataSource):
        """copy parameters & path from dataSource, return self
        """
        if dataSource is None:
            raise ValueError('Undefined dataSource; cannot import parameters')
        if not isinstance(dataSource, SpectrumDataSourceABC):
            raise TypeError('%s.copyDataTo: Wrong dataSource class type; got %s' %
                            (self.__class__.__name__, dataSource))

        self.copyParametersFrom(dataSource)
        self._assureProperDimensionality()
        if dataSource.path is not None:
            self.setPath(dataSource.path, substituteSuffix=True)
        return self

    def copyParametersTo(self, target):
        """Copy parameters from self to target;
        return self
        """
        if not isinstance(target, SpectrumDataSourceABC):
            raise TypeError('%s.copyDataTo: Wrong target class type; got %s' %
                            (self.__class__.__name__, target))

        for param in self.keys():
            doCopy = self.getMetadata(param, 'doCopy') and target.hasTrait(param)
            if doCopy:
                values = self.getTraitValue(param)
                target.setTraitValue(param, values)

        return self

    def copyParametersFrom(self, source):
        """Copy parameters from source to self
        """
        if not isinstance(source, SpectrumDataSourceABC):
            raise TypeError('%s.copyDataTo: Wrong source class type; got %s' %
                            (self.__class__.__name__, source))
        source.copyParametersTo(self)
        return self

    def copyDataTo(self, target):
        """Copy data from self to target;
        return self
        """
        if not isinstance(target, SpectrumDataSourceABC):
            raise TypeError('%s.copyDataTo: Wrong target class type; got %s' %
                            (self.__class__.__name__, target))

        if self.dimensionCount != target.dimensionCount:
            raise RuntimeError('%s.copyDataTo: incompatible dimensionCount with target' %
                               self.__class__.__name__)

        if self.dimensionCount == 1:
            # 1D's
            data = self.getSliceData()
            target.setSliceData(data)

        else:
            # nD's'
            for position, data in self.allPlanes(xDim=1, yDim=2):
                target.setPlaneData(data=data, position=position, xDim=1, yDim=2)

        return self

    def copyDataFrom(self, source):
        """Copy data from source to self;
        return self
        """
        if not isinstance(source, SpectrumDataSourceABC):
            raise TypeError('%s.copyDataFrom: Wrong source class type; got %s' %
                            (self.__class__.__name__, source))
        if self.dimensionCount != source.dimensionCount:
            raise RuntimeError('%s.copyDataFrom: incompatible dimensionCount with source' %
                               self.__class__.__name__)
        source.copyParametersTo(self)
        return self

    def _mapDimensionalParameters(self, dimensionsMap: dict):
        """map dimensional parameters according to dimensionsMap dict comprised of
        (sourceDim, desinationDim) key, value pairs (1-based)
        """
        if  dimensionsMap is None or \
            not isinstance(dimensionsMap, dict) or \
            len(dimensionsMap) != self.dimensionCount or \
            len(set(dimensionsMap.keys())) != self.dimensionCount or \
            len(set(dimensionsMap.items())) != self.dimensionCount:
            raise ValueError('invalid dimensionsMap %r' % dimensionsMap)

        sourceDims = []
        targetDims = []
        for k,v in dimensionsMap.items():
            if k < 1 or k > self.dimensionCount or v < 1 or v > self.dimensionCount:
                raise ValueError('invalid (%s,%s) pair in dimensionsMap %r' % (k, v, dimensionsMap))
            sourceDims.append(k)
            targetDims.append(v)

        for parName in self.getDimensionalParameters().keys():
            values = self.getByDimensions(parName, sourceDims)
            self.setByDimensions(parName, values, targetDims)

    def transposeParameters(self, dimension1, dimension2):
        """Transpose parameters of dimension1 and dimenson2 (1-based)
        """
        dimTuples = [(dim,dim) for dim in self.dimensions]  # identity map
        dimTuples[dimension1 - 1] = (dimension2, dimension1)
        dimTuples[dimension2 - 1] = (dimension1, dimension2)
        self._mapDimensionalParameters(dict(dimTuples))

    def _setIsotopeCodes(self):
        """Set the isotope codes from frequencies if not defined; make best possible guess
        """
        nuclei = findNucleiFromSpectrometerFrequencies(self.spectrometerFrequencies)
        for idx, isotopeCode in enumerate(self.isotopeCodes):
            if isotopeCode is None:
                # we did not have an isotopeCode definition, see if we found the a Nucleus automatically
                nuc = nuclei[idx] if nuclei is not None else None
                if nuc is None:
                    # We have neither isotopeCode nor Nucleus
                    getLogger().warning('%s: unable to set isotopeCode[%d] automatically, assuming "1H"' % (self, idx))
                    self.isotopeCodes[idx] = '1H'
                else:
                    self.isotopeCodes[idx] = nuc.isotopeCode

    def _setAxisCodes(self):
        """Set the axisCodes, based on dimensionType and isotopeCode
        """
        for idx, isotopeCode in enumerate(self.isotopeCodes):

            if self.dimensionTypes[idx] == DIMENSIONFID:
                self.axisCodes[idx] = 'Time'

            elif isotopeCode is None:
                getLogger().warning('%s: unable to set axisCode[%d] automatically' % (self, idx))
                self.axisCodes[idx] = 'Unknown'

            else:
                # we had an isotopeCode definition, find the Nucleus definition
                nuc = Nucleus(isotopeCode)
                if nuc.isotopeRecord is None:
                    getLogger().warning('%s: isotopeCode[%d] = %s not known; unable to set axisCode[%d] automatically'
                                        % (self, isotopeCode, idx, idx))
                    self.axisCodes[idx] = 'Unknown'
                else:
                    # we found the a Nucleus
                    self.axisCodes[idx] = nuc.axisCode

            # Make axisCode unique by optionally adding dimension suffix
            acode = self.axisCodes[idx]
            if acode in self.axisCodes[0:idx]:
                acode = '%s_%d' % (acode, idx+1)
                self.axisCodes[idx] = acode

        self.acquisitionAxisCode =self.axisCodes[self.X_AXIS]

    def setDimensionCount(self, dimensionCount):
        "Change the dimensionality, assuring proper values of the dimensional parameters"
        if dimensionCount < 1 or dimensionCount > self.MAXDIM:
            raise ValueError('dimensionCount must be in the range 1, %s' % self.MAXDIM)

        self.dimensionCount = dimensionCount
        self._assureProperDimensionality()

    #=========================================================================================
    # access to cache
    #=========================================================================================

    def _initBlockCache(self):
        "Intialise the cache"
        cache = Cache(maxItems=0, name=_BLOCK_CACHE)
        setattr(self, _BLOCK_CACHE, cache)

    @property
    def cache(self):
        "Returns the Block cache instance"
        if not hasattr(self, _BLOCK_CACHE):
            self._initBlockCache()
        cache = getattr(self, _BLOCK_CACHE)
        return cache

    def disableCache(self):
        "Disable the caching of blockdata"
        self.cache.resize(0)

    def clearCache(self):
        "Clear the cache"
        self.cache.clear()

    def _setMaxCacheSize(self, sizeInBytes):
        """Set the maximum cache size (in Bytes) over all cached blocks
        """
        blockSizeInBytes = self._totalBlockSize * self.wordSize
        maxItems = int(sizeInBytes / blockSizeInBytes)
        self.cache.resize(maxItems)

    #=========================================================================================
    # blocked access related functions
    #=========================================================================================
    @property
    def _totalBlockSize(self):
        "Return total number of words in one block"
        result = self.blockSizes[0]
        for points in self.blockSizes[1:]:
            result *= points
        result += self.blockHeaderSize
        return result

    @property
    def _totalBlocks(self):
        "Return total number of blocks in the file"
        numBlocks = self._numBlocksPerDimension
        tBlocks = numBlocks[0]
        for bn in numBlocks[1:]:
            tBlocks *= bn
        return tBlocks

    @property
    def _numBlocksPerDimension(self):
        "number of blocks per dimension"
        nBlocks = [1 + (self.pointCounts[dim] - 1) // self.blockSizes[dim] for dim in range(self.dimensionCount)]
        return nBlocks

    def _pointsToBlocksPerDimension(self, zPoints):
        "returns list of (block-index, block-offset) tuples (zero-based) corresponding to zPoints (zero-based)"
        return [(p // self.blockSizes[i],
                 p %  self.blockSizes[i]
                ) for i, p in enumerate(zPoints)]

    def _pointsToAbsoluteBlockIndex(self, points):
        """Returns absolute block index corresponding to points (zero-based)

            absIndex =   Ia * Nz * Ny * Nx  +  Iz * Ny * Nx  +  Iy * Nx  +  Ix
                     = ((Ia * Nz + Iz) * Ny + Iy) * Nx + Ix
        where:
            Ix,y,z,a is the blockindex along x, y, z, a
            Nx,y,z,a is number of blocks along x, y, z, a

        """
        blockIndex = [idx for idx, _t in self._pointsToBlocksPerDimension(points)]
        numBlocks = self._numBlocksPerDimension
        # start at the highest dimension
        dim = self.dimensionCount - 1
        absIndex = blockIndex[dim]
        dim -= 1
        while dim >= 0:
            absIndex = absIndex*numBlocks[dim] + blockIndex[dim]
            dim -= 1
        return absIndex

    def _convertBlockData(self, blockdata):
        """Convert the blockdata array if dtype is not self.dataType (ie. currently float32)
        """
        if blockdata.dtype != self.dataType:
            blockdata = numpy.array(blockdata, self.dataType)
        return blockdata

    @property
    def dtype(self):
        "return the numpy dtype string based on settings"
        return '%s%s%s' % (self.isBigEndian and '>' or '<', self.isFloatData and 'f' or 'i', self.wordSize)

    @cached(_BLOCK_CACHE, debug=False, doSignatureExpansion=False)
    def _readBlockFromFile(self, absoluteBlockIndex):
        """Read block at absoluteBlockIndex; separate routine for caching reasons
        Return NumPy array
        """
        offset = (self.headerSize +
                  self._totalBlockSize * absoluteBlockIndex
                  ) * self.wordSize  # offset in bytes
        self.fp.seek(offset, 0)
        # dtype = '%s%s%s' % (self.isBigEndian and '>' or '<', self.isFloatData and 'f' or 'i', self.wordSize)
        blockdata = numpy.fromfile(file=self.fp, dtype=self.dtype, count=self._totalBlockSize)
        return self._convertBlockData(blockdata)

    def _readBlock(self, points):
        """read and return NumPy data-array of block corresponding to points (zero-based)
        """
        if not self.isBlocked:
            raise RuntimeError('%s is not a blocked format' % self)

        if not self.hasOpenFile():
            raise RuntimeError('Invalid file pointer fp (None)')

        absBlockIndex = self._pointsToAbsoluteBlockIndex(points)
        try:
            _data = self._readBlockFromFile(absBlockIndex)
            if _data.size < self._totalBlockSize:
                _data = numpy.pad(_data, pad_width= (0, self._totalBlockSize - _data.size), mode='constant')
            data = _data.reshape(self.blockSizes[::-1]) # nD numpy arrays are array[z][y][x] (i.e. reversed indexing)

        except Exception as es:
            getLogger().error('Reading %s (zero-based; absBlockIndex %s) from %s' % (points, absBlockIndex, self))
            raise es

        return data

    def _readBlockedPoint(self, position=()) -> float:
        """Read value at position (1-based)
        Return float value
        """
        if not self.isBlocked:
            raise RuntimeError('%s is not a blocked format' % self)

        position = self.checkForValidPosition(position)

        # converts to zero-based
        points = [p-1 for p in position]

        # we are reading nD blocks; need to slice across these with depth of 1)
        blockOffsets = [offset for _tmp, offset in self._pointsToBlocksPerDimension(points)]
        slices = [slice(offset, offset+1) for offset in blockOffsets]

        blockdata = self._readBlock(points)
        _tmp = blockdata[ tuple(slices[::-1]) ].flatten() # invert the slices as multi-d numpy arrays are array[z][y][x] (i.e. reversed indexing)
        return float(_tmp[0])

    def _readBlockedSlice(self, sliceDim=1, position=None):
        """Read slice along sliceDim (1-based) through position (1-based)

        :type position: list/tuple of length dimensionCount
        :return Numpy data array
        """
        if not self.isBlocked:
            raise RuntimeError('%s is not a blocked format' % self)

        # converts to zero-based
        sliceDim -= 1
        points = [p-1 for p in position]

        # create the array with zeros
        data = numpy.zeros(self.pointCounts[sliceDim], dtype=self.dataType)

        # we are reading nD blocks; need to slice across these with depth of 1 in non-slice dims and a
        # size of blockSizes[sliceDim] along the sliceDim (set dynamically during the looping)
        blockOffsets = [offset for _tmp, offset in self._pointsToBlocksPerDimension(points)]
        slices = [slice(offset, offset+1) for offset in blockOffsets]

        if not self.hasOpenFile():
            self.openFile(mode=self.defaultOpenReadMode)

        # loop through the points p of sliceDim in steps blockSize[sliceDim]
        for p in range(0, self.pointCounts[sliceDim], self.blockSizes[sliceDim]):
            points[sliceDim] = p
            blockdata = self._readBlock(points)
            # The actual size along sliceDim may not be an integer times the blockSize of sliceDim
            pStop = min(p+self.blockSizes[sliceDim], self.pointCounts[sliceDim])
            slices[sliceDim] = slice(0, pStop-p) # truncate if necessary
            _tmp = blockdata[ tuple(slices[::-1]) ].flatten() # invert the slices as multi-d numpy arrays are array[z][y][x] (i.e. reversed indexing)
            data[p:pStop] = _tmp
        return data

    def _readBlockedPlane(self, xDim=1, yDim=2, position=None):
        """Read plane along xDim,yDim (1-based) through position (1-based)

        :type position: list/tuple of length dimensionCount
        :return Numpy data array[y][x]
        """
        if not self.isBlocked:
            raise RuntimeError('%s is not a blocked format' % self)

        # convert to zero-based
        xDim -= 1
        yDim -= 1
        points = [p-1 for p in position]

        # create the array with zeros
        pointCounts = (self.pointCounts[yDim], self.pointCounts[xDim])  # y,x ordering
        data = numpy.zeros(pointCounts, dtype=self.dataType)

        # we are reading nD blocks; need to slice across these with depth of 1 in non-plane dims and a
        # size of blockSizes[xDim], blockSizes[yDim] along the xDim,yDim (set dynamically during the looping)
        blockOffsets = [offset for _tmp, offset in self._pointsToBlocksPerDimension(points)]
        slices = [slice(offset, offset+1) for offset in blockOffsets]

        if not self.hasOpenFile():
            self.openFile(mode=self.defaultOpenReadMode)

        # loop through the y points of yDim in steps blockSize[yDim]
        for y in range(0, self.pointCounts[yDim], self.blockSizes[yDim]):

            points[yDim] = y
            # The actual size along yDim may not be an integer times the blockSize of yDim
            yStop = min(y+self.blockSizes[yDim], self.pointCounts[yDim])
            slices[yDim] = slice(0, yStop-y) # truncate if necessary

            # loop through the x points of xDim in steps blockSize[xDim]
            for x in range(0, self.pointCounts[xDim], self.blockSizes[xDim]):

                points[xDim] = x
                # The actual size along xDim may not be an integer times the blockSize of xDim
                xStop = min(x+self.blockSizes[xDim], self.pointCounts[xDim])
                slices[xDim] = slice(0, xStop-x) # truncate if necessary  --> slices are x,y,z,... ordered

                blockData = self._readBlock(points)  #  --> z,y,x ordered
                blockPlane = blockData[ tuple(slices[::-1]) ] # invert the slices --> blockPlane inverse ordered
                # The blockdata are z,y,x;
                if xDim > yDim:
                    # Example: assume xDim=3='z', yDim=1='x'; i.e. an (3,1)=(z,x) plane is asked for
                    # The resulting plane data will be (inverse) x,z ordered
                    # blockPlane is (inverse) z,x ordered --> need to transpose to get an (inverse-ordered) x,z plane
                    blockPlane = blockPlane.transpose()
                blockPlane = blockPlane.reshape((yStop-y, xStop-x))

                data[y:yStop, x:xStop] = blockPlane

        return data

    #=========================================================================================
    # data access functions
    #=========================================================================================

    @classmethod
    def checkForValidFormat(cls, path):
        """check if valid format corresponding to dataFormat by:
        - creating an instance of the class
        - setting and checking path
        - reading (and checking dimensionCount) parameters

        :return: None or instance of the class
        """
        logger = getLogger()

        instance = cls()

        # checking path
        if instance.setPath(path, substituteSuffix=False) is None:
            logger.debug('%s.checkForValidFormat: setting path "%s" yielded None' %
                         (instance.__class__.__name__, path))
            return None

        if not instance.checkPath(instance.path, mode=instance.defaultOpenReadMode):
            logger.debug('%s.checkForValidFormat: path "%s" not valid for data format "%s"' %
                         (instance.__class__.__name__, path, instance.dataFormat))
            return None

        # checking opening file and reading parameters
        try:
            with instance.openExistingFile():  # This will also read the parameters
                pass
                # instance.readParameters()
        except RuntimeError as es:
            logger.debug('%s.checkForValidFormat: bailing on reading with error: "%s"' %
                         (instance.__class__.__name__, es))
            return None

        # Check dimensionality; should be > 0
        if instance.dimensionCount == 0:
            logger.debug('%s.checkForValidFormat: reading parameters from "%s" yielded dimensionCount=0' %
                         (instance.__class__.__name__, path))
            return None

        elif instance.dimensionCount > 0:
            logger.debug('%s.checkForValidFormat: path "%s" is valid for data format "%s"' %
                         (instance.__class__.__name__, path, instance.dataFormat))
            return instance  # found the file with right attributes

        return None

    def openFile(self, mode, **kwds):
        """open self.path, set self.fp, return self.fp
        """
        if mode is None:
            raise ValueError('%s.openFile: Undefined open mode' % self.__class__.__name__)

        try:
            if self.hasOpenFile():
                self.closeFile()

            if not self.checkPath(self.path, mode=mode):
                raise FileNotFoundError('Invalid %s' % self)

            self.fp = self.openMethod(str(self.path), mode, **kwds)
            self.mode = mode

        except Exception as es:
            self.closeFile()
            text = '%s.openFile(mode=%r): %s' % (self.__class__.__name__, mode, str(es))
            getLogger().error(text)
            raise es

        if mode.startswith('r'):
            self.readParameters()  # need to read to have blocksizes defined
            if self.hasBlockCached:
                self._setMaxCacheSize(self.maxCacheSize)
        else:
            self.disableCache()  # No caching on writing; that creates sync issues

        return self.fp

    @contextmanager
    def openExistingFile(self, path=None, mode=None):
        """Open file, read parameters, check isotopes and close
        if mode is None it defaults to self.defaultOpenReadMode

        Yields self; i.e. one can do:
            with SpectrumDataSource().openExistingFile(path) as ds:
                data = ds.getSliceData()
        """
        if path is not None:
            self.setPath(path)

        if mode is None:
            mode = self.defaultOpenReadMode

        self.closeFile() # Wil close if open, do nothing otherwise
        self.openFile(mode=mode)  # also reads parameters
        # self.readParameters()
        try:
            yield self

        except Exception as es:
            self.closeFile()
            getLogger().error('%s.openExistingFile: "%s"' % (self.__class__.__name__, str(es)))
            raise es

        finally:
            self.closeFile()

    @contextmanager
    def openNewFile(self, path=None, mode=None):
        """Open new file, write parameters, and close at the end
        Yields self; i.e. one can do:

        with SpectrumDataSource(spectrum=sp).openNewFile(path) as ds:
            ds.writeSliceData(data)
        """
        if path is not None:
            self.setPath(path, substituteSuffix=True)

        if mode is None:
            mode = self.defaultOpenWriteMode

        try:
            self.closeFile() # Will close if open disgarding everything, do nothing otherwise
            getLogger().debug('%s.openNewFile: calling openFile' % self.__class__.__name__)
            self.openFile(mode=mode)
            yield self

        except Exception as es:
            self.closeFile()
            getLogger().error('%s.openNewFile: "%s"' % (self.__class__.__name__, str(es)))
            raise es

        finally:
            getLogger().debug('%s.openNewFile: writing parameters and calling closeFile' %
                               self.__class__.__name__)
            self.writeParameters()
            self.closeFile()

    def closeFile(self):
        """Close the file and clear the cache
        """
        if self.hasOpenFile():
            self.fp.close()
            self.fp = None
            self.mode = None

        # Close optional non-temporary hdf5 buffer
        if self.hdf5buffer is not None and not self.temporaryBuffer:
            self.hdf5buffer.closeFile()

        self.cache.clear()

    def hasOpenFile(self):
        """Return True if dataSoure has active open file pointer
        """
        return self.fp is not None

    def readParameters(self):
        """Read the parameters from the format-specific dataFile into the data structure;

        to be subclassed; super needs to be called at the end to clean up
        """
        self._assureProperDimensionality()
        self._setIsotopeCodes()
        self._setAxisCodes()
        return self

    def writeParameters(self):
        "to be subclassed"
        raise NotImplementedError('Not implemented')

    def checkForValidPosition(self, position):
        """Checks if position (1-based) is valid, expand if None and append if necessay
        Return valid position
        """
        if self.dimensionCount == 0:
            raise RuntimeError('%s: Undefined parameters' % self)

        if position is None:
            position = [1]*self.dimensionCount

        if not isIterable(position):
            raise ValueError('position must be an tuple or list')

        if len(position) < self.dimensionCount:
            position += [1]*self.dimensionCount - len(position)
        position = position[0:self.dimensionCount]

        for idx, p in enumerate(position):
            if not (1 <= p <= self.pointCounts[idx]):
                raise ValueError('dimension %d: value must be in [1,%d]: got "%d"' % \
                                 (idx+1, self.pointCounts[idx], p))
        return position

    def checkForValidPlane(self, position, xDim, yDim):
        """Asserts if position, xDim, yDim are valid
        Return valid position
        """
        if self.dimensionCount == 0:
            raise RuntimeError('%s: Undefined parameters' % self)

        if self.dimensionCount < 2:
            raise RuntimeError('%s: number of dimensions must be >= 2' % self)

        position = self.checkForValidPosition(position)

        if not (1 <= xDim <= self.dimensionCount):
            raise ValueError('invalid xDim (%d), should be in range [1,%d]' % (xDim, self.dimensionCount))
        if not (1 <= yDim <= self.dimensionCount):
            raise ValueError('invalid yDim (%d), should be in range [1,%d]' % (yDim, self.dimensionCount))
        if xDim == yDim:
            raise ValueError('xDim = %d; yDim = %d' % (xDim, yDim))

        return position

    def getPlaneData(self, position: Sequence = None, xDim: int = 1, yDim: int = 2):
        """Get plane defined by xDim, yDim and position (all 1-based)
        Check for hdf5buffer first, then blocked format
        Optionally to be subclassed

        :return NumPy data array
        """
        if self.hdf5buffer is not None:
            return self.hdf5buffer.getPlaneData(position=position, xDim=xDim, yDim=yDim)

        elif self.isBlocked:
            position = self.checkForValidPlane(position=position, xDim=xDim, yDim=yDim)
            return self._readBlockedPlane(xDim=xDim, yDim=yDim, position=position)

        else:
            raise NotImplementedError('Not implemented')

    def setPlaneData(self, data, position: Sequence = None, xDim: int = 1, yDim: int = 2):
        """Set the plane defined by xDim, yDim and position (all 1-based)
        from NumPy data array

        to be subclassed
        """
        raise NotImplementedError('Not implemented')

    def checkForValidSlice(self, position, sliceDim):
        """Checks that sliceDim is valid, returns valid (expanded) position if None
        """
        if self.dimensionCount == 0:
            raise RuntimeError('%s: Undefined parameters' % self)

        position = self.checkForValidPosition(position)

        if not (1 <= sliceDim <= self.dimensionCount):
            raise ValueError('invalid sliceDim (%d), should be in range [1,%d]' % (sliceDim, self.dimensionCount))

        return position

    def getSliceData(self, position:Sequence=None, sliceDim:int=1):
        """Get slice defined by sliceDim and position (all 1-based)
        Check for hdf5buffer first, then blocked format
        Optionally to be subclassed

        :return NumPy data array
        """
        if self.hdf5buffer is not None:
            return self.hdf5buffer.getSliceData(position=position, sliceDim=sliceDim)

        elif self.isBlocked:
            position = self.checkForValidSlice(position=position, sliceDim=sliceDim)
            return self._readBlockedSlice(sliceDim=sliceDim, position=position)

        else:
            raise NotImplementedError('Not implemented')

    def setSliceData(self, data, position:Sequence=None, sliceDim:int=1):
        """Set data as slice defined by sliceDim and position (all 1-based)

        to be subclassed
        """
        raise NotImplementedError('Not implemented')

    def getSliceDataFromPlane(self, position, xDim: int, yDim: int, sliceDim: int):
        """Routine to get sliceData using getPlaneData
        """
        # adapted from earlier Spectrum-class method

        if not (sliceDim == xDim or sliceDim == yDim):
            raise ValueError('sliceDim (%s) not in plane (%s,%s)' % (sliceDim, xDim, yDim))

        position = self.checkForValidPlane(position, xDim, yDim)

        sliceIdx = position[yDim - 1] - 1 if sliceDim == xDim else position[xDim - 1] - 1  # position amd dimensions are 1-based

        # Improve caching,
        position[xDim-1] = 1
        position[yDim-1] = 1
        planeData = self.getPlaneData(position, xDim, yDim)

        if sliceDim == xDim:
            data = planeData[sliceIdx, 0:]
        else:
            # sliceDim == yDim:
            data = planeData[0:, sliceIdx]

        return data

    def getPointData(self, position:Sequence=None) -> float:
        """Get value defined by position (1-based, integer values)
        Use getPointValue() for an interpolated value
        """
        if self.hdf5buffer is not None:
            return self.hdf5buffer.getPointData(position=position)

        elif self.isBlocked:
            position = self.checkForValidPosition(position)
            return self._readBlockedPoint(position)

        else:
            # piggyback on getSliceData
            data = self.getSliceData(position=position, sliceDim=1)
            return float(data[position[0]-1])

    def getPointValue(self, position, aliaisingFlags=None):
        """Get interpolated value defined by position (1-based, float values), optionally aliased
        The result is calculated from a weighted average of the two values at the neighbouring
        grid points for each dimension

        aliaisingFlags: Optionally allow for aliasing per dimension:
            0: No aliasing
            1: aliasing with positive sign
           -1: aliasing with negative sign

        Use getPointData() for a method using an integer-based grid position argument
        """

        def interpolate(data, factor):
            """Reduce dimenionality by one, interpolating between successive points along
            the collapsed axis
            :param data: N-dimensional Numpy array with sizes 2 along each dimension
            :param factor: interpolation factor between succesive points [0.0, 1.0];
                            along (-1) dimension: newValue = value[0] + factor * (value[1]-value[0])
            :returns: (N-1)-dimensional Numpy array with sizes 2 along each dimension
            """
            diffs = factor*numpy.diff(data, axis=-1)
            slices = [slice(0, n) for n in diffs.shape]
            result = numpy.add(data[tuple(slices)], diffs)
            result = numpy.squeeze(result, axis=-1)
            # print('result>\n', result,  '\nshape: ', result.shape, '\n')
            return result

        # get the fractions of position; i.e. if position=(324.4, 120.9, 33.7),
        # get ( 0.4, 0.9, 0.7 )
        fractions = [p-float(int(p)) for p in position]
        # get the nD slice data around position; i.e. if position=(324.4, 120.9, 33.7),
        # get ( (324,325), (120,121), (33,34) )
        sliceTuples = [(int(p), int(p)+1) for p in position]
        pointData = self.getRegionData(sliceTuples=sliceTuples, aliasingFlags=aliaisingFlags)

        for f in fractions:
            pointData = interpolate(pointData, factor=f)

        return pointData.item()

    def checkForValidRegion(self, sliceTuples, aliasingFlags):
        """Checks if slicesTuples are valid

        aliaisingFlags: Optionally allow for aliasing per dimension:
            0: No aliasing
            1: aliasing with positive sign
           -1: aliasing with negative sign
        """
        if len(sliceTuples) != self.dimensionCount:
            raise ValueError('invalid sliceTuples argument; dimensionality mismatch')

        if aliasingFlags is None:
            raise ValueError('invalid aliasing argument; None value')

        if len(aliasingFlags) != self.dimensionCount:
            raise ValueError('invalid aliasing argument; dimensionality mismatch')

        for idx, sTuple in enumerate(sliceTuples):  # do not call this slice! as it override the python slice object
            if sTuple is None:
                sTuple = (1, self.pointCounts[idx])
            start, stop = sTuple

            if aliasingFlags[idx] == 0:
                if start < 1:
                    raise ValueError('invalid sliceTuple for dimension %s; start < 1 (%s)' % (idx+1, start))

                if stop > self.pointCounts[idx]:
                    raise ValueError('invalid sliceTuple for dimension %s; stop > %s (%s)'
                                     % (idx+1, self.pointCounts[idx], stop))

            if start > stop:
                raise ValueError('invalid sliceTuple for dimension %s; start (%s) > stop (%s)' % (idx+1, start,stop))

    def _getRegionData(self, sliceTuples, aliasingFlags=None):
        """Return an numpy array containing the region data; see getRegionData description
        implementation based upon getSliceData method
        """
        sizes = [(stop-start+1) for start,stop in sliceTuples]
        starts = [start-1 for start,stop in sliceTuples] # 0-based
        stops = [stop for start,stop in sliceTuples] # 0-based, non-inclusive
        sliceDim = 1
        sliceAxis = sliceDim - 1  # 0-based axis of sliceDim

        # The result being assembled
        regionData = numpy.zeros(sizes[::-1], dtype=self.dataType) # ...,z,y,x numpy ordering

        # temp buffer for unpacking aliased data along sliceDim
        sliceData2 = numpy.zeros(sizes[sliceAxis], dtype=self.dataType)
        nPoints = self.pointCounts[sliceAxis]

        for position, aliased in self._selectedPointsIterator(sliceTuples, excludeDimensions=[sliceDim]):

            position[sliceAxis] = 1  # position is 1-based
            aliased[sliceAxis] = (starts[sliceAxis] < 0 or stops[sliceAxis] >= nPoints)
            with notificationEchoBlocking():
                sliceData = self.getSliceData(position=position, sliceDim=sliceDim)

            # define the data slicing objects
            dataSlices = [slice((p-1)-starts[idx], (p-1)-starts[idx]+1) for idx,p in enumerate(position)]
            dataSlices[sliceAxis] = slice(0,sizes[sliceAxis])
            # FutureWarning: Using a non-tuple sequence for multidimensional indexing is deprecated;
            # use `arr[tuple(seq)]` instead of `arr[seq]`. In the future this will be interpreted as
            # an array index, `arr[np.array(seq)]`, which will result either in an error or a different result.
            dataSlices = tuple(dataSlices)

            # get aliasing factor determined by dimensions other than sliceDim
            factor = 1.0
            for axis, fac, aliase in zip(self.axes, aliasingFlags, aliased):
                if axis != sliceAxis and aliase:
                    factor *= fac

            if not aliased[sliceAxis]:
                # There are no aliased points along sliceDim
                # copy the relevant section of the sliceData into the (nD) data array
                regionData[dataSlices[::-1]] = factor * sliceData[starts[sliceAxis]:stops[sliceAxis]] # dimensions run in ..,z,y,x order
            else:
                # copy the relevant points from sliceData to sliceData2 array; aliasing where needed
                for idx, p in zip( range(0,sizes[sliceAxis]), range(starts[sliceAxis],stops[sliceAxis]) ):
                    pointFactor = aliasingFlags[sliceAxis] if (p < 0 or p >= nPoints) else 1.0
                    while p<0:
                        p += nPoints
                    while p >= nPoints:
                        p -= nPoints
                    sliceData2[idx] = factor * pointFactor * sliceData[p]
                # copy the sliceData2 into the (nD) data array
                regionData[dataSlices[::-1]] = sliceData2[:] # dimensions run in ..,z,y,x order

        return regionData

    def getRegionData(self, sliceTuples, aliasingFlags=None):
        """Return an numpy array containing the points defined by
                sliceTuples=[(start_1,stop_1), (start_2,stop_2), ...],

        sliceTuples are 1-based; sliceTuple stop values are inclusive (i.e. different
        from the python slice object)

        aliaisingFlags: Optionally allow for aliasing per dimension:
            0: No aliasing
            1: aliasing with positive sign
           -1: aliasing with negative sign
        """
        if aliasingFlags is None:
            aliasingFlags = [0] * self.dimensionCount

        if self.hdf5buffer is not None:
            regionData =  self.hdf5buffer.getRegionData(sliceTuples=sliceTuples, aliasingFlags=aliasingFlags)

        else:
            self.checkForValidRegion(sliceTuples, aliasingFlags)
            regionData = self._getRegionData(sliceTuples=sliceTuples, aliasingFlags=aliasingFlags)

        return regionData

    def estimateNoise(self):
        """Estimate and return a noise level
        Use mean of abs of dataPlane or dataSlice
        """

        if self.dimensionCount == 1:
            data = self.getSliceData()
        else:
            data = self.getPlaneData()
            data = data.flatten()

        absData = numpy.array([v for v in map(abs, data)])
        median = numpy.median(absData)
        std = numpy.std(absData)
        noiseLevel = median + 1.0*std
        return noiseLevel

    #=========================================================================================
    # Iterators
    #=========================================================================================

    def _selectedPointsIterator(self, sliceTuples, excludeDimensions=()):
        """Get an iterator points defined by sliceTuples=[(start_1,stop_1), (start_2,stop_2), ...],
        iterating along dimensions perpendicular to any excludeDims

        sliceTuples and excludeDimensions are 1-based; sliceTuple stop values are inclusive
        (i.e. different from the python slice object)
        Looping aliases back (ie. when start,stop < 1 and > pointCounts) in all dimensions.
        It is the task of the calling routine to prevent that if not desired

        return a (position, aliased) tuple of lists
        """

        if len(sliceTuples) != self.dimensionCount:
            raise ValueError('invalid sliceTuples argument; dimensionality mismatch')

        for dim in excludeDimensions:
            if dim < 1 or dim > self.dimensionCount:
                raise ValueError('invalid dimension "%s" in excludeDimensions' % dim)

        # get dimensions to interate over
        iterDims = list(set(self.dimensions) - set(excludeDimensions))

        # get relevant iteration parameters
        slices = [sliceTuples[dim-1] for dim in iterDims]
        indices = [dim-1 for dim in iterDims]
        iterData = list(zip(iterDims, slices, indices))

        def _nextPosition(currentPosition):
            "Return a (done, position) tuple derived from currentPosition"
            for dim, sliceTuple, idx in iterData:
                start = sliceTuple[0]
                stop = sliceTuple[1]
                if currentPosition[idx] + 1 <= stop:  # still an increment to make in this dimension
                    currentPosition[idx] += 1
                    return (False, currentPosition)
                else:  # reset this dimension
                    currentPosition[idx] = start
            return (True, None)  # reached the end

        # loop over selected slices
        loopPosition = [start for start,stop in sliceTuples]
        done = False
        while not done:
            # get position list within the [1,pointCounts] range and an aliased True/False list
            position = []
            aliased = []
            for idx, p in enumerate(loopPosition):
                aliased.append( (p<1) or p>self.pointCounts[idx] )
                # Aliase onto 1, pointCounts range
                while p < 1:
                    p += self.pointCounts[idx]
                while p > self.pointCounts[idx]:
                    p -= self.pointCounts[idx]
                position.append(p)

            yield position, aliased
            done, loopPosition = _nextPosition(loopPosition)

    def allPlanes(self, xDim=1, yDim=2):
        """An iterator over all planes defined by xDim, yDim, yielding (position, data-array) tuples
        dims and positions are one-based
        """
        self.checkForValidPlane(position=None, xDim=xDim, yDim=yDim)

        sliceTuples = [(1, p) for p in self.pointCounts]
        with notificationEchoBlocking():
            for position, aliased in self._selectedPointsIterator(sliceTuples, excludeDimensions=[xDim, yDim]):
                position[xDim-1] = 1
                position[yDim-1] = 1
                planeData = self.getPlaneData(position=position, xDim=xDim, yDim=yDim)
                yield (position, planeData)

    def allSlices(self, sliceDim=1):
        """An iterator over all slices defined by sliceDim, yielding (position, data-array) tuples
        dims and positions are one-based
        """
        self.checkForValidSlice(position=None, sliceDim=sliceDim)

        sliceTuples = [(1, p) for p in self.pointCounts]
        with notificationEchoBlocking():
            for position, aliased in self._selectedPointsIterator(sliceTuples, excludeDimensions=[sliceDim]):
                position[sliceDim-1] = 1
                sliceData = self.getSliceData(position=position, sliceDim=sliceDim)
                yield (position, sliceData)

    def allPoints(self):
        """An iterator over all points, yielding (position, data-array) tuples
        positions are one-based
        """
        sliceTuples = [(1, p) for p in self.pointCounts]
        with notificationEchoBlocking():
            for position, aliased in self._selectedPointsIterator(sliceTuples, excludeDimensions=[]):
                pointData = self.getPointData(position=position)
                yield (position, pointData)

    #=========================================================================================
    # Hdf5 buffer
    #=========================================================================================

    def initialiseHdf5Buffer(self, temporaryBuffer=True, path=None):
        """Initialise a Hdf5SpectrumBuffer instance and fill with data from self

        :param temporaryBuffer: flag indicating to create a temporary file, discarded upon closing
        :param path: explicit path or derived from self.path if None and temporary=False
        :return: Hdf5SpectrumBuffer instance
        """
        from ccpn.core.lib.SpectrumDataSources.Hdf5SpectrumDataSource import Hdf5SpectrumDataSource

        if self.hdf5buffer is not None:
            getLogger().debug('Closing %s' % self.hdf5buffer)
            self.hdf5buffer.closeFile()
            self.hdf5buffer = None

        self.temporaryBuffer = temporaryBuffer
        if self.temporaryBuffer:
            name = 'CcpNmr_hdf5buffer_%s_' % self.path.basename
            tFile = tempfile.NamedTemporaryFile(prefix=name, suffix=Hdf5SpectrumDataSource.suffixes[0])
            path = tFile.name

        if not self.temporaryBuffer:
            if path is None:
                path = self.path.withSuffix(Hdf5SpectrumDataSource.suffixes[0]).uniqueVersion()

        # create a hdf5 buffer file instance
        hdf5buffer = Hdf5SpectrumDataSource().copyParametersFrom(self)
        hdf5buffer._dataSource = self # link back to self
        hdf5buffer.setPath(path=path, substituteSuffix=True)
        # do not use openNewFile as it has to remain open after filling the buffer
        hdf5buffer.openFile(mode=Hdf5SpectrumDataSource.defaultOpenWriteMode)
        self.fillHdf5Buffer(hdf5buffer)
        # buffer is filled now; associate with self so that future reads will use it to retrieve data
        self.hdf5buffer = hdf5buffer
        return hdf5buffer

    def fillHdf5Buffer(self, hdf5buffer):
        """Fill hdf5Buffer with data from self;
        this routine will be subclassed in the more problematic cases such as NmrPipe
        """
        self.copyDataTo(hdf5buffer)

    def duplicateDataToHdf5(self, path=None):
        """Make a duplicate from self to a Hdf5 file;
        return an Hdf5SpectrumDataSource instance
        """
        from ccpn.core.lib.SpectrumDataSources.Hdf5SpectrumDataSource import Hdf5SpectrumDataSource

        if path is None:
            path = self.path.withSuffix(Hdf5SpectrumDataSource.suffixes[0]).uniqueVersion()

        hdf5 = Hdf5SpectrumDataSource().copyParametersFrom(self)
        with hdf5.openNewFile(path=path):
            self.copyDataTo(hdf5)
        return hdf5

    #=========================================================================================
    # Others
    #=========================================================================================

    def printParameters(self, path=sys.stdout):
        "Print all to path"
        path.write(str(self) + '\n')
        for param, value in self.getNonDimensionalParameters().items():
            path.write('%-24s: %s\n' % (param, value))
        for param, values in self.getDimensionalParameters().items():
            path.write('%-24s: ' % param)
            for val in values:
                if isinstance(val, float):
                    path.write('%15.6g ' % val)
                else:
                    path.write('%15s ' % val)
            path.write('\n')

    def __str__(self):
        if self.dimensionCount == 0:
            return '<%s: _D (), path=%s>' % (self.__class__.__name__, self.path)
        else:
            if self.hdf5buffer is not None:
                fpStatus = '%r' % 'buffered'
                path = self.hdf5buffer.path
            elif self.fp is not None:
                fpStatus = '%r' % self.mode
                path = self.path
            else:
                fpStatus = '%r' % 'closed'
                path = self.path

            return '<%s: %dD (%s), %s: path=%s>' % (self.__class__.__name__,
                                                self.dimensionCount,
                                                'x'.join([str(p) for p in self.pointCounts]),
                                                fpStatus,
                                                path
                                               )
#end class

