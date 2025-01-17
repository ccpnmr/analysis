"""
This file contains the ABC wrapper around the model datasource stuff (fail to define a better name)

it serves as an interface between the V3 Spectrum class and the actual spectral data formats
of different flavours (e.g. Bruker, NmrPipe, Azara, Felix, Varian/Agilent, Hdf5 (internal), etc)

the core methods are:

checkValid()                check if valid corresponding to dataFormat;
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
        output.copyDataFrom(sp.dataSource)
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2024-08-07 17:36:07 +0100 (Wed, August 07, 2024) $"
__version__ = "$Revision: 3.2.5 $"
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
from collections import OrderedDict, defaultdict
from itertools import product

import tempfile
import numpy
import numpy as np

import ccpn.core.lib.SpectrumLib as specLib
from ccpn.core._implementation.SpectrumData import SliceData, PlaneData, RegionData
from ccpn.core.lib.ContextManagers import notificationEchoBlocking
from ccpn.core.lib.Cache import cached, Cache

from ccpn.util.Common import isIterable
from ccpn.util.Path import aPath
from ccpn.util.Logging import getLogger
from ccpn.util.decorators import singleton

from ccpn.util.isotopes import findNucleiFromSpectrometerFrequencies, Nucleus
from ccpn.util.traits.CcpNmrTraits import CFloat, CInt, CBool, Bool, List, \
    CString, CList, CPath
from ccpn.util.traits.CcpNmrJson import CcpNmrJson

from ccpn.framework.constants import CCPNMR_PREFIX, NO_SUFFIX, ANY_SUFFIX


_BLOCK_CACHE = CCPNMR_PREFIX + 'block_cache'
# _BLOCK_CACHE_MAXITEMS = 128
MB = 1024 * 1024


def getDataFormats() -> OrderedDict:
    """Get spectrum datasource formats

    :return: a dictionary of (format-identifier-strings, SpectrumDataSource classes) as (key, value) pairs
    """
    # The following imports are just to assure that all the classes have been imported
    # It is local to prevent circular imports
    from ccpn.core.lib.SpectrumDataSources.BrukerSpectrumDataSource import BrukerSpectrumDataSource
    from ccpn.core.lib.SpectrumDataSources.NmrPipeSpectrumDataSource import NmrPipeSpectrumDataSource
    from ccpn.core.lib.SpectrumDataSources.Hdf5SpectrumDataSource import Hdf5SpectrumDataSource
    from ccpn.core.lib.SpectrumDataSources.UcsfSpectrumDataSource import UcsfSpectrumDataSource
    from ccpn.core.lib.SpectrumDataSources.AzaraSpectrumDataSource import AzaraSpectrumDataSource
    from ccpn.core.lib.SpectrumDataSources.FelixSpectrumDataSource import FelixSpectrumDataSource
    from ccpn.core.lib.SpectrumDataSources.XeasySpectrumDataSource import XeasySpectrumDataSource
    from ccpn.core.lib.SpectrumDataSources.NmrViewSpectrumDataSource import NmrViewSpectrumDataSource
    from ccpn.core.lib.SpectrumDataSources.JcampSpectrumDataSource import JcampSpectrumDataSource
    from ccpn.core.lib.SpectrumDataSources.EmptySpectrumDataSource import EmptySpectrumDataSource

    return SpectrumDataSourceABC._spectrumDataFormats


@singleton
class SpectrumDataSourceSuffixDict(dict):
    """A class to contain a dict of (suffix, [SpectrumDataSource class]-list)
    (key, value) pairs; exclude EmptySpectrum

    The get(suffix) returns a list of klasses for suffix; its maps None or zero-length to NO_SUFFIX
    and any non-existing suffix in the dict to ANY_SUFFIX

    NB: Only to be used internally
    """

    def __init__(self):
        # local import to avoid cycles
        # from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import getDataFormats
        from ccpn.core.lib.SpectrumDataSources.EmptySpectrumDataSource import EmptySpectrumDataSource

        super().__init__(self)

        # Fill the dict
        for dataFormat, klass in getDataFormats().items():
            if dataFormat != EmptySpectrumDataSource.dataFormat:
                suffixes = [NO_SUFFIX, ANY_SUFFIX] if len(klass.suffixes) == 0 else klass.suffixes
                for suffix in suffixes:
                    suffix = NO_SUFFIX if suffix is None else suffix
                    self[suffix].append(klass)

    def __getitem__(self, item):
        """Can't get subclassed defaultdict to work
        Always assure a list for item
        """
        if not item in self:
            super().__setitem__(item, [])
        return super().__getitem__(item)

    def get(self, suffix) -> list:
        """get a list of klasses for suffix;
        map None or zero-length to NO_SUFFIX and
        map non existing suffix to ANY_SUFFIX
        """
        if suffix is None or len(suffix) == 0:
            return self[NO_SUFFIX]
        elif suffix not in self:
            return self[ANY_SUFFIX]
        else:
            return self[suffix]


def getDataSourceClass(dataFormat):
    """Get a dataSource class from the dataFormat string;
    Implements the name mapping issue; e.g. the 'NmrView'
    :param dataFormat: a (valid) dataFormat string
    :return a class corresponding to dataFormat, or None if invalid
    """
    # Test for optional mapping of the dataFormat name (e.g. for the 'NmrView') issue
    dataFormatDict = SpectrumDataSourceABC._dataFormatDict
    dataFormat = dataFormatDict.get(dataFormat, None)
    if dataFormat is None:
        return None
    else:
        return getDataFormats()[dataFormat]


class SpectrumDataSourceABC(CcpNmrJson):
    """
    ABC for NMR spectral data sources reading/writing
    """

    classVersion = 1.0  # For json saving
    saveAllTraitsToJson = True
    keysInOrder = True  # maintain the definition order

    # 'local' definition of MAXDIM; defining defs in SpectrumLib to prevent circular imports
    MAXDIM = specLib.MAXDIM  # 8  # Maximum dimensionality

    #=========================================================================================
    # to be subclassed
    #=========================================================================================
    dataFormat = None  # string defining format type
    alternateDataFormatNames = []  # list with optional alternate names; e.g. for NmrView->NMRView

    isBlocked = False  # flag defining if data are blocked
    hasBlockCached = True  # Flag indicating if block data are cached
    maxCacheSize = 64 * MB  # Max cache size in Bytes

    wordSize = 4
    headerSize = 0
    blockHeaderSize = 0
    isFloatData = True
    hasWritingAbility = False  # flag that defines if dataFormat implements writing methods

    suffixes = []  # potential suffixes of data file; first is taken as default;
    # NO_SUFFIX defines that no suffix is allowed
    # ANY_SUFFIX defines that any suffix is allowed
    allowDirectory = False  # Can/Can't open a directory
    openMethod = None  # method to open the file as openMethod(path, mode)
    defaultOpenReadMode = 'r+'
    defaultOpenReadWriteMode = 'r+'
    defaultOpenWriteMode = 'w'
    defaultAppendMode = 'a'

    #=========================================================================================
    # data formats
    #=========================================================================================
    _dtype = numpy.float32  # numpy data format of the resulting slice, plane, region data

    # A dict of registered spectrum data formats: filled by _registerFormat classmethod, called
    # once after each definition of a new derived class (e.g. Hdf5SpectrumDataSource)
    _spectrumDataFormats = OrderedDict()
    # dict with dataFormat name mappings; for older, alternative definitions
    _dataFormatDict = {}

    @classmethod
    def _registerFormat(cls):
        """register cls.dataFormat
        """
        if cls.dataFormat in cls._spectrumDataFormats:
            raise RuntimeError('dataFormat "%s" was already registered' % cls.dataFormat)
        cls._spectrumDataFormats[cls.dataFormat] = cls
        # add dataFormat names to the _dataFormatDict
        for name in [cls.dataFormat] + cls.alternateDataFormatNames:
            cls._dataFormatDict[name] = cls.dataFormat

        # Also register the class for json restoring
        cls.register()

    #=========================================================================================
    # parameter definitions and mappings onto the Spectrum class
    #=========================================================================================

    _bigEndian = (sys.byteorder == 'big')

    # isDimensional: bool: defines a spectral parameter, either as dimensional or not
    # doCopy: bool: copy parameter to/from spectra and between dataSource instances
    # spectrumAttribute: name of corresponding attribute in Spectrum class
    # hasSetterInSpectrumClass: bool: corresponding attribute in Spectrum class can be set
    date = CString(allow_none=True, default_value=None).tag(isDimensional=False,
                                                            doCopy=True,
                                                            spectrumAttribute=None,
                                                            hasSetterInSpectrumClass=False
                                                            )
    comment = CString(allow_none=True, default_value=None).tag(isDimensional=False,
                                                               doCopy=True,
                                                               spectrumAttribute='comment',
                                                               hasSetterInSpectrumClass=True
                                                               )
    pulseProgram = CString(allow_none=True, default_value=None).tag(isDimensional=False,
                                                                    doCopy=True,
                                                                    spectrumAttribute=None,
                                                                    hasSetterInSpectrumClass=False
                                                                    )
    temperature = CFloat(allow_none=True, default_value=None).tag(isDimensional=False,
                                                                  doCopy=True,
                                                                  spectrumAttribute='temperature',
                                                                  hasSetterInSpectrumClass=True
                                                                  )
    noiseLevel = CFloat(allow_none=True, default_value=None).tag(isDimensional=False,
                                                                 doCopy=True,
                                                                 spectrumAttribute='noiseLevel',
                                                                 hasSetterInSpectrumClass=True
                                                                 )
    isBigEndian = Bool(default_value=_bigEndian).tag(isDimensional=False,
                                                     doCopy=True,
                                                     spectrumAttribute=None,
                                                     hasSetterInSpectrumClass=False
                                                     )
    # internal data scale (e.g. as used by Bruker)
    dataScale = CFloat(default_value=1.0).tag(isDimensional=False,
                                              doCopy=True,
                                              spectrumAttribute=None,
                                              hasSetterInSpectrumClass=False
                                              )
    sampledValues = List(default_value=[None for dim in range(0, MAXDIM)]).tag(
            isDimensional=True,
            doCopy=True,
            spectrumAttribute=None,
            hasSetterInSpectrumClass=False
            )
    sampledSigmas = List(default_value=[None for dim in range(0, MAXDIM)]).tag(
            isDimensional=True,
            doCopy=True,
            spectrumAttribute=None,
            hasSetterInSpectrumClass=False
            )
    dimensionCount = CInt(default_value=0).tag(isDimensional=False,
                                               doCopy=True,
                                               spectrumAttribute='dimensionCount',
                                               hasSetterInSpectrumClass=False
                                               )

    # dimension order mappings e.g. used by NmrPipe, Xeasy
    dimensionOrder = CList(trait=CInt(), default_value=[dim for dim in range(0, MAXDIM)], maxlen=MAXDIM).tag(
            info='A (optional) mapping index into the dimensional data',
            isDimensional=True,
            doCopy=True,
            spectrumAttribute=None,
            hasSetterInSpectrumClass=False
            )
    pointCounts = CList(trait=CInt(allow_none=False), default_value=[0] * MAXDIM, maxlen=MAXDIM).tag(
            info='Total number of data points along each dimension',
            isDimensional=True,
            doCopy=True,
            spectrumAttribute='pointCounts',
            hasSetterInSpectrumClass=True
            )
    blockSizes = CList(trait=CInt(allow_none=True), default_value=[None] * MAXDIM, maxlen=MAXDIM).tag(
            info='Sub-matrix number of points along each dimension',
            isDimensional=True,
            doCopy=False,
            spectrumAttribute=None,
            hasSetterInSpectrumClass=False
            )
    dimensionTypes = CList(trait=CString(allow_none=True), default_value=[specLib.DIMENSION_FREQUENCY] * MAXDIM, maxlen=MAXDIM).tag(
            info='Dimension type (Frequency or Time) identifier along each dimension',
            isDimensional=True,
            doCopy=True,
            spectrumAttribute='dimensionTypes',
            hasSetterInSpectrumClass=True
            )
    dataTypes = CList(trait=CString(), default_value=[specLib.DATA_TYPE_REAL] * MAXDIM, maxlen=MAXDIM).tag(
            info='Data type identifier (nR, (nR)(nI), n(RI), n(PN)) along each dimension',
            isDimensional=True,
            doCopy=True,
            spectrumAttribute=None,
            hasSetterInSpectrumClass=False
            )
    isComplex = CList(trait=CBool(), default_value=[False] * MAXDIM, maxlen=MAXDIM).tag(
            isDimensional=True,
            doCopy=True,
            spectrumAttribute='isComplex',
            hasSetterInSpectrumClass=True
            )
    _tmp = [False] * MAXDIM;
    _tmp[0] = True
    isAcquisition = CList(trait=CBool(), default_value=_tmp, maxlen=MAXDIM).tag(
            isDimensional=True,
            doCopy=True,
            spectrumAttribute='isAcquisition',
            hasSetterInSpectrumClass=True
            )
    isotopeCodes = CList(trait=CString(allow_none=True), default_value=[None] * MAXDIM, maxlen=MAXDIM).tag(
            isDimensional=True,
            doCopy=True,
            spectrumAttribute='isotopeCodes',
            hasSetterInSpectrumClass=True
            )
    axisCodes = CList(trait=CString(allow_none=True), default_value=[None] * MAXDIM, maxlen=MAXDIM).tag(
            isDimensional=True,
            doCopy=True,
            spectrumAttribute='axisCodes',
            hasSetterInSpectrumClass=True
            )
    axisLabels = CList(trait=CString(allow_none=True), default_value=[None] * MAXDIM, maxlen=MAXDIM).tag(
            isDimensional=True,
            doCopy=True,
            spectrumAttribute=None,
            hasSetterInSpectrumClass=False,
            info='per dimension: labels, as e.g. present in Felix or NmrPipe',
            )
    measurementTypes = CList(trait=CString(allow_none=True), default_value=['Shift'] * MAXDIM, maxlen=MAXDIM).tag(
            isDimensional=True,
            doCopy=True,
            spectrumAttribute='measurementTypes',
            hasSetterInSpectrumClass=True,
            )
    foldingModes = CList(trait=CString(allow_none=True), default_value=[specLib.FOLDING_MODE_CIRCULAR] * MAXDIM, maxlen=MAXDIM).tag(
            isDimensional=True,
            doCopy=True,
            spectrumAttribute='foldingModes',
            hasSetterInSpectrumClass=True,
            )
    spectrometerFrequencies = CList(trait=CFloat(allow_none=False), default_value=[1.0] * MAXDIM, maxlen=MAXDIM).tag(
            isDimensional=True,
            doCopy=True,
            spectrumAttribute='spectrometerFrequencies',
            hasSetterInSpectrumClass=True,
            )
    spectralWidthsHz = CList(trait=CFloat(allow_none=False), default_value=[1.0] * MAXDIM, maxlen=MAXDIM).tag(
            isDimensional=True,
            doCopy=True,
            spectrumAttribute='spectralWidthsHz',
            hasSetterInSpectrumClass=True,
            )
    referencePoints = CList(trait=CFloat(allow_none=False), default_value=[1.0] * MAXDIM, maxlen=MAXDIM).tag(
            isDimensional=True,
            doCopy=True,
            spectrumAttribute='referencePoints',
            hasSetterInSpectrumClass=True,
            )
    referenceValues = CList(trait=CFloat(allow_none=False), default_value=[1.0] * MAXDIM, maxlen=MAXDIM).tag(
            isDimensional=True,
            doCopy=True,
            spectrumAttribute='referenceValues',
            hasSetterInSpectrumClass=True,
            )
    phases0 = CList(trait=CFloat(allow_none=True), default_value=[None] * MAXDIM, maxlen=MAXDIM).tag(
            isDimensional=True,
            doCopy=True,
            spectrumAttribute='phases0',
            hasSetterInSpectrumClass=True,
            )
    phases1 = CList(trait=CFloat(allow_none=True), default_value=[None] * MAXDIM, maxlen=MAXDIM).tag(
            isDimensional=True,
            doCopy=True,
            spectrumAttribute='phases1',
            hasSetterInSpectrumClass=True,
            )
    windowFunctions = CList(trait=CString(allow_none=True), default_value=[None] * MAXDIM, maxlen=MAXDIM).tag(
            isDimensional=True,
            doCopy=True,
            spectrumAttribute='windowFunctions',
            hasSetterInSpectrumClass=True,
            info='per dimension: Window function name (or None) - e.g. "EM", "GM", "SINE", "QSINE"'
            )
    lorentzianBroadenings = CList(trait=CFloat(allow_none=True), default_value=[None] * MAXDIM, maxlen=MAXDIM).tag(
            isDimensional=True,
            doCopy=True,
            spectrumAttribute='lorentzianBroadenings',
            hasSetterInSpectrumClass=True,
            info='per dimension: Lorenzian broadening in Hz'
            )
    gaussianBroadenings = CList(trait=CFloat(allow_none=True), default_value=[None] * MAXDIM, maxlen=MAXDIM).tag(
            isDimensional=True,
            doCopy=True,
            spectrumAttribute='gaussianBroadenings',
            hasSetterInSpectrumClass=True,
            info='per dimension: Gaussian broadening in Hz'
            )
    assignmentTolerances = CList(trait=CFloat(allow_none=True), default_value=[None] * MAXDIM, maxlen=MAXDIM).tag(
            isDimensional=True,
            doCopy=True,
            spectrumAttribute='assignmentTolerances',
            hasSetterInSpectrumClass=True,
            info='per dimension: Assignment tolerance in ppm'
            )

    #=========================================================================================
    # new implementation, using newFromPath method and validity testing later on
    #=========================================================================================
    isValid = Bool(default_value=False).tag(info='flag to indicate if path denotes a valid dataType')
    shouldBeValid = Bool(default_value=False).tag(info='flag to indicate that path should denotes a valid dataType, but some elements are missing')
    errorString = CString(default_value='').tag(info='error description for validity testing')

    #=========================================================================================
    # Attributes for more complicated dataFormats that have separate binaries and parameter
    # files; e.g. Azara, Bruker, Xeasy
    #=========================================================================================
    _parameterFile = CPath(default_value=None, allow_none=True).tag(info=
                                                                    'an attribute to store the (parsed) path to a parameter file'
                                                                    )
    _binaryFile = CPath(default_value=None, allow_none=True).tag(info=
                                                                 'an attribute to store the path to a binary file; used during parsing'
                                                                 )
    _path = CPath(default_value=None, allow_none=True).tag(info=
                                                           'an attribute to store the initial path used to define binary/parameter files; used during parsing'
                                                           )

    #=========================================================================================
    # some default data
    #=========================================================================================

    isotopeDefaultDataDict = defaultdict(
            lambda: {'spectralRange': (15.0, -2.0), 'pointCount': 512},
            [
                ('1H', {'spectralRange': (15.0, -2.0), 'pointCount': 512}),
                ('15N', {'spectralRange': (150.0, 90.0), 'pointCount': 256}),
                ('13C', {'spectralRange': (150.0, -10.0), 'pointCount': 256}),
                ('19F', {'spectralRange': (250.0, 40.0), 'pointCount': 512}),
                ]
            )

    #=========================================================================================
    # Convenience properties and methods
    #=========================================================================================

    @property
    def isNotValid(self) -> bool:
        """:return not self.isValid
        """
        return not self.isValid

    @classmethod
    def _documentClass(cls) -> str:
        """:return a documentation string comprised of __doc__ and some class attributes
        This method mimics the identical one in the DataLoader's classes
        """

        _newProject = 'Never'

        result = f'{cls.dataFormat} spectrum binary data format.\n' + \
                 cls.__doc__ + \
                 f'\n' + \
                 f'    Valid suffixes:      {cls.suffixes}\n' + \
                 f'    Allows directory:    {cls.allowDirectory}\n' + \
                 f'    Creates new project: {_newProject}\n' + \
                 f'    Has writing ability: {cls.hasWritingAbility}'

        return result

    def isDimensionalParameter(self, parameterName) -> bool:
        """:return True if parameterName is dimensional"""
        return self.getMetadata(parameterName, 'isDimensional')

    def getDimensionalParameters(self) -> OrderedDict:
        """Return a OrderedDict of (parameterName, values) for dimensional parameters"""
        items = [i for i in self.items(isDimensional=lambda i: i)]
        return OrderedDict(items)

    def getNonDimensionalParameters(self) -> OrderedDict:
        """Return a OrderedDict of (parameterName, values) for non-dimensional parameters"""
        items = [i for i in self.items(isDimensional=lambda i: not i)]
        return OrderedDict(items)

    def parameterKeys(self):
        """Those keys that define the spectrum parameters
        """
        return self.keys(isDimensional=False) + self.keys(isDimensional=True)

    @property
    def dimensions(self) -> tuple:
        """A one-based tuple of dimensions [1,dimensionCount]
        """
        return tuple(range(1, self.dimensionCount + 1))

    @property
    def dimensionIndices(self) -> tuple:
        """A zero-based tuple of dimension indices [0,dimensionCount-1]
        """
        return tuple([i for i in range(0, self.dimensionCount)])

    @property
    def totalNumberOfPoints(self) -> int:
        """Total number of points of the data"""
        result = self.pointCounts[0]
        for axis in self.dimensionIndices[1:]:
            result *= self.pointCounts[axis]
        return result

    @property
    def expectedFileSizeInBytes(self) -> int:
        """The expected file size in Bytes"""
        if self.dimensionCount == 0:
            raise RuntimeError('%s: Undefined parameters' % self)

        if self.isBlocked:
            result = (self.headerSize + self._totalBlockSize * self._totalBlocks) * self.wordSize
        else:
            result = (self.headerSize + self.totalNumberOfPoints) * self.wordSize

        return result

    @property
    def realPointCounts(self) -> list:
        """Conveniance to yield the number of real points along each dimension
        """
        result = []
        for isComplex, p in zip(self.isComplex, self.pointCounts):
            _p = p // 2 if isComplex else p
            result.append(_p)
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

        # hdf5Buffer related attributes
        self._isBuffered = False  # Flag to indicate the spectrumDataSource object to have buffered read/writes;
        self.hdf5buffer = None  # Hdf5SpectrumBuffer instance; None indicates no Hdf5 buffer used
        self._bufferFilled = False
        self._bufferIsTemporary = True
        self._bufferPath = None

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
        # if not self.hasBlockCached:
        #     self.disableCache()

        self.checkValid()

    def setDefaultParameters(self, nDim=MAXDIM):
        """Set default values for all parameters
        """
        for par in self.parameterKeys():
            self.setTraitDefaultValue(par)

    def _assureProperDimensionality(self):
        """Assure proper dimensionality for all relevant parameters
        """
        for par, values in self.getDimensionalParameters().items():
            values = list(values)
            if len(values) < self.dimensionCount:
                values += self.getTraitDefaultValue(par)
            values = values[0:self.dimensionCount]
            self.setTraitValue(par, values)

    @property
    def path(self) -> aPath:
        """Return an absolute path of datapath as a Path instance or None when dataFile is
        not defined.
        """
        return (None if self.dataFile is None else aPath(self.dataFile))

    @property
    def parentPath(self) -> aPath:
        """Return an absolute path of parent of self.dataFile as a Path instance or None
        when dataFile is not defined.
        For subclassing; e.g. in case of Bruker
        """
        return (None if self.dataFile is None else self.path.parent)

    @classmethod
    def checkSuffix(cls, path) -> bool:
        """Check if suffix of path confirms to settings of class attribute suffixes.
        :returns True or False
        """
        _path = aPath(path)
        if len(_path.suffixes) == 0 and NO_SUFFIX in cls.suffixes:
            return True
        if len(_path.suffixes) > 0 and ANY_SUFFIX in cls.suffixes:
            return True
        if len(_path.suffixes) > 0 and _path.suffix in cls.suffixes:
            return True
        return False

    def setPath(self, path, checkSuffix=False):
        """define valid path to a (binary) data file, if needed appends or substitutes
        the suffix (if defined).

        :return self or None on error
        """
        if path is None:
            self.dataFile = None  # A reset essentially
            return self

        _p = aPath(path)
        validSuffix = self.checkSuffix(path)

        if not validSuffix and checkSuffix:
            _p = _p.with_suffix(self.suffixes[0])

        self.dataFile = str(_p)
        return self

    def hasValidPath(self) -> bool:
        """Return true if the path is valid
        """
        path = self.path
        return path is not None and path.exists()

    def nameFromPath(self) -> str:
        """Return a name derived from path (to be subclassed for specific cases; e.g. Bruker)
        """
        return self.path.stem

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
        return [values[dim - 1] for dim in dimensions]

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
        newValues = self.getTraitValue(parameterName)
        for dim, val in zip(dimensions, values):
            newValues[dim - 1] = val
        self.setTraitValue(parameterName, newValues)

    def _copyParametersFromSpectrum(self, spectrum):
        """Copy parameters values from a Spectrum instance
        """
        for param in self.parameterKeys():
            doCopy = self.getMetadata(param, 'doCopy')
            spectrumAttribute = self.getMetadata(param, 'spectrumAttribute')
            if spectrumAttribute is not None and doCopy:
                values = getattr(spectrum, spectrumAttribute)
                self.setTraitValue(param, values)

    def _copyParametersToSpectrum(self, spectrum):
        """Copy parameter values to a Spectrum instance
        """
        for param in self.parameterKeys():
            doCopy = self.getMetadata(param, 'doCopy')
            spectrumAttribute = self.getMetadata(param, 'spectrumAttribute')
            hasSetter = self.getMetadata(param, 'hasSetterInSpectrumClass')
            if spectrumAttribute is not None and doCopy and hasSetter:
                values = self.getTraitValue(param)
                setattr(spectrum, spectrumAttribute, values)

    def importFromSpectrum(self, spectrum, includePath=True):
        """copy parameters & path (optionally) from spectrum, set spectrum attribute and return self
        """
        # local import to avoid cycles
        from ccpn.core.Spectrum import Spectrum

        if spectrum is None:
            raise ValueError('Undefined spectrum; cannot import parameters')

        if not isinstance(spectrum, Spectrum):
            raise TypeError('%s.importFromSpectrum: Wrong spectrum class type; got %s' %
                            (self.__class__.__name__, spectrum))

        self._copyParametersFromSpectrum(spectrum)
        self._assureProperDimensionality()
        if spectrum.filePath is not None and includePath:
            self.setPath(spectrum.filePath, checkSuffix=True)
        self.spectrum = spectrum
        return self

    def exportToSpectrum(self, spectrum, includePath=True):
        """copy parameters & path (optionally) to spectrum, set spectrum attribute, and return self
        """
        # local import to avoid cycles
        from ccpn.core.Spectrum import Spectrum

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
            self.setPath(dataSource.path, checkSuffix=True)
        return self

    def copyParametersTo(self, target):
        """Copy parameters from self to target;
        return self
        """
        if not isinstance(target, SpectrumDataSourceABC):
            raise TypeError('%s.copyDataTo: Wrong target class type; got %s' %
                            (self.__class__.__name__, target))

        for param in self.parameterKeys():
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
        source.copyDataTo(self)
        return self

    def _mapDimensionalParameters(self, dimensionsMap: dict):
        """map dimensional parameters according to dimensionsMap dict comprised of
        (sourceDim, desinationDim) key, value pairs (1-based)
        """
        if dimensionsMap is None or \
                not isinstance(dimensionsMap, dict) or \
                len(dimensionsMap) != self.dimensionCount or \
                len(set(dimensionsMap.keys())) != self.dimensionCount or \
                len(set(dimensionsMap.items())) != self.dimensionCount:
            raise ValueError('invalid dimensionsMap %r' % dimensionsMap)

        sourceDims = []
        targetDims = []
        for k, v in dimensionsMap.items():
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
        dimTuples = [(dim, dim) for dim in self.dimensions]  # identity map
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

            if self.dimensionTypes[idx] == specLib.DIMENSION_TIME:
                self.axisCodes[idx] = 'Time'

            elif isotopeCode is None:
                getLogger().warning('%s: unable to set axisCode[%d] automatically' % (self, idx))
                self.axisCodes[idx] = 'Unknown'

            else:
                # we had an isotopeCode definition, find the Nucleus definition
                nuc = Nucleus(isotopeCode)
                if nuc.isotopeRecord is None:
                    getLogger().warning('%s: isotopeCode[%d] = %s not known; unable to set axisCode[%d] automatically'
                                        % (self, idx, isotopeCode, idx))
                    self.axisCodes[idx] = 'Unknown'
                else:
                    # we found the a Nucleus
                    self.axisCodes[idx] = nuc.axisCode

            # Make axisCode unique by optionally adding dimension suffix
            acode = self.axisCodes[idx]
            if acode in self.axisCodes[0:idx]:
                acode = '%s_%d' % (acode, idx + 1)
                self.axisCodes[idx] = acode

    def setDimensionCount(self, dimensionCount):
        """Change the dimensionality, assuring proper values of the dimensional parameters"""
        if dimensionCount < 1 or dimensionCount > self.MAXDIM:
            raise ValueError('dimensionCount must be in the range 1, %s' % self.MAXDIM)

        self.dimensionCount = dimensionCount
        self._assureProperDimensionality()

    def _setDefaultIsotopeValues(self, isotopeCode, dimension, field=18.8):
        """ Set the default spectrometerFrequencies, spectralWidth, referencePoints, referenceValues
        and axisCode values derived from isotopeCode and field for dimension (1-based)
        """

        if isotopeCode is not None:

            idx = dimension - 1
            nuc = Nucleus(isotopeCode)
            defaultValues = self.isotopeDefaultDataDict[isotopeCode]

            if nuc is not None:
                self.isotopeCodes[idx] = isotopeCode
                self.spectrometerFrequencies[idx] = nuc.frequencyAtField(field)

                high, low = defaultValues['spectralRange']
                self.spectralWidthsHz[idx] = (high - low) * self.spectrometerFrequencies[idx]

                self.referencePoints[idx] = 1.0
                self.referenceValues[idx] = high

                _count = self.axisCodes.count(nuc.axisCode)
                self.axisCodes[idx] = nuc.axisCode + (str(_count) if _count else '')

                self.pointCounts[idx] = defaultValues['pointCount']

    def _setSpectralParametersFromIsotopeCodes(self, field=18.8):
        """Set spectral parameters at field
        """
        for idx, isotopeCode in enumerate(self.isotopeCodes):
            self._setDefaultIsotopeValues(isotopeCode, dimension=idx + 1, field=field)

    #=========================================================================================
    # access to cache
    #=========================================================================================

    def _initBlockCache(self):
        """Intialise the cache"""
        cache = Cache(maxItems=0, name=_BLOCK_CACHE)
        setattr(self, _BLOCK_CACHE, cache)

    @property
    def cache(self):
        """Returns the Block cache instance"""
        if not hasattr(self, _BLOCK_CACHE):
            self._initBlockCache()
        cache = getattr(self, _BLOCK_CACHE)
        return cache

    def disableCache(self):
        """Disable the caching of blockdata"""
        self.cache.resize(0)

    def clearCache(self):
        """Clear the cache"""
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
        """Return total number of words in one block"""
        result = self.blockSizes[0]
        for points in self.blockSizes[1:]:
            result *= points
        result += self.blockHeaderSize
        return result

    @property
    def _totalBlocks(self):
        """Return total number of blocks in the file"""
        numBlocks = self._numBlocksPerDimension
        tBlocks = numBlocks[0]
        for bn in numBlocks[1:]:
            tBlocks *= bn
        return tBlocks

    @property
    def _numBlocksPerDimension(self):
        """number of blocks per dimension"""
        nBlocks = [1 + (self.pointCounts[dim] - 1) // self.blockSizes[dim] for dim in range(self.dimensionCount)]
        return nBlocks

    def _pointsToBlocksPerDimension(self, zPoints):
        """returns list of (block-index, block-offset) tuples (zero-based) corresponding to zPoints (zero-based)"""
        return [(p // self.blockSizes[i],
                 p % self.blockSizes[i]
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
            absIndex = absIndex * numBlocks[dim] + blockIndex[dim]
            dim -= 1
        return absIndex

    def _convertBlockData(self, blockdata):
        """Convert the blockdata array if dtype is not self.dataType (ie. currently float32)
        """
        if blockdata.dtype != self._dtype:
            blockdata = numpy.array(blockdata, self._dtype)
        return blockdata

    @property
    def dtype(self):
        """return the numpy dtype string based on settings"""
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
                _data = numpy.pad(_data, pad_width=(0, self._totalBlockSize - _data.size), mode='constant')
            data = _data.reshape(self.blockSizes[::-1])  # nD numpy arrays are array[z][y][x] (i.e. reversed indexing)

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
        points = [p - 1 for p in position]

        # we are reading nD blocks; need to slice across these with depth of 1)
        blockOffsets = [offset for _tmp, offset in self._pointsToBlocksPerDimension(points)]
        slices = [slice(offset, offset + 1) for offset in blockOffsets]

        blockdata = self._readBlock(points)
        _tmp = blockdata[tuple(slices[::-1])].flatten()  # invert the slices as multi-d numpy arrays are array[z][y][x] (i.e. reversed indexing)
        return float(_tmp[0])

    def _readBlockedSlice(self, sliceDim=1, position=None):
        """Read slice along sliceDim (1-based) through position (1-based)

        :type position: list/tuple of length dimensionCount
        :return Numpy data array
        """
        if not self.isBlocked:
            raise RuntimeError('%s is not a blocked format' % self)

        # converts to zero-based
        sliceIdx = sliceDim - 1
        points = [p - 1 for p in position]

        # create the array with zeros
        # data = numpy.zeros(self.pointCounts[sliceIdx], dtype=self.dataType)
        data = SliceData(dataSource=self, dimensions=(sliceDim,), position=position)

        # we are reading nD blocks; need to slice across these with depth of 1 in non-slice dims and a
        # size of blockSizes[sliceIdx] along the sliceDim (set dynamically during the looping)
        blockOffsets = [offset for _tmp, offset in self._pointsToBlocksPerDimension(points)]
        slices = [slice(offset, offset + 1) for offset in blockOffsets]

        if not self.hasOpenFile():
            self.openFile(mode=self.defaultOpenReadMode)

        # loop through the points p of sliceDim in steps blockSize[sliceIdx]
        for p in range(0, self.pointCounts[sliceIdx], self.blockSizes[sliceIdx]):
            points[sliceIdx] = p
            blockdata = self._readBlock(points)
            # The actual size along sliceDim may not be an integer times the blockSize of sliceDim
            pStop = min(p + self.blockSizes[sliceIdx], self.pointCounts[sliceIdx])
            slices[sliceIdx] = slice(0, pStop - p)  # truncate if necessary
            _tmp = blockdata[tuple(slices[::-1])].flatten()  # invert the slices as multi-d numpy arrays are array[z][y][x] (i.e. reversed indexing)
            data[p:pStop] = _tmp
        # return data
        return data

    def _readBlockedPlane(self, xDim=1, yDim=2, position=None):
        """Read plane along xDim,yDim (1-based) through position (1-based)

        :type position: list/tuple of length dimensionCount
        :return Numpy data array[y][x]
        """
        if not self.isBlocked:
            raise RuntimeError('%s is not a blocked format' % self)

        # create the array with zeros
        data = PlaneData(dataSource=self, dimensions=(xDim, yDim), position=position)

        # convert to zero-based
        xDim -= 1
        yDim -= 1
        points = [p - 1 for p in position]

        # # create the array with zeros
        # pointCounts = (self.pointCounts[yDim], self.pointCounts[xDim])  # y,x ordering
        # # data = numpy.zeros(pointCounts, dtype=self.dataType)
        # data = PlaneData(dataSource=self, dimensions=dimensions, position=position)

        # we are reading nD blocks; need to slice across these with depth of 1 in non-plane dims and a
        # size of blockSizes[xDim], blockSizes[yDim] along the xDim,yDim (set dynamically during the looping)
        blockOffsets = [offset for _tmp, offset in self._pointsToBlocksPerDimension(points)]
        slices = [slice(offset, offset + 1) for offset in blockOffsets]

        if not self.hasOpenFile():
            self.openFile(mode=self.defaultOpenReadMode)

        # loop through the y points of yDim in steps blockSize[yDim]
        for y in range(0, self.pointCounts[yDim], self.blockSizes[yDim]):

            points[yDim] = y
            # The actual size along yDim may not be an integer times the blockSize of yDim
            yStop = min(y + self.blockSizes[yDim], self.pointCounts[yDim])
            slices[yDim] = slice(0, yStop - y)  # truncate if necessary

            # loop through the x points of xDim in steps blockSize[xDim]
            for x in range(0, self.pointCounts[xDim], self.blockSizes[xDim]):

                points[xDim] = x
                # The actual size along xDim may not be an integer times the blockSize of xDim
                xStop = min(x + self.blockSizes[xDim], self.pointCounts[xDim])
                slices[xDim] = slice(0, xStop - x)  # truncate if necessary  --> slices are x,y,z,... ordered

                blockData = self._readBlock(points)  #  --> z,y,x ordered
                blockPlane = blockData[tuple(slices[::-1])]  # invert the slices --> blockPlane inverse ordered
                # The blockdata are z,y,x;
                if xDim > yDim:
                    # Example: assume xDim=3='z', yDim=1='x'; i.e. an (3,1)=(z,x) plane is asked for
                    # The resulting plane data will be (inverse) x,z ordered
                    # blockPlane is (inverse) z,x ordered --> need to transpose to get an (inverse-ordered) x,z plane
                    blockPlane = blockPlane.transpose()
                blockPlane = blockPlane.reshape((yStop - y, xStop - x))

                data[y:yStop, x:xStop] = blockPlane

        return data

    #=========================================================================================
    # data access functions
    #=========================================================================================

    def _returnFalse(self, errMsg) -> False:
        """
        Helper function to set self.errorString, write to debug2 and return False
        :param errMsg:
        :return: False
        """
        getLogger().debug2(errMsg)
        self.errorString = errMsg
        return False

    def _checkValidExtra(self) -> bool:
        """Helper code to avoid code duplication:
        check the extra attributes _path, _binaryFile, and_parameterFile.
        Used for Azara, Bruker, Xeasy
        """
        self.isValid = False
        self.errorString = 'Checking validity'

        _iniTxt = f'{self.dataFormat} spectrum, path "{self._path}"'
        # checking original path and its suffix
        if self._path is None or not self._path.exists():
            errorMsg = f'{_iniTxt}: does not exist'
            return self._returnFalse(errorMsg)

        if not self.checkSuffix(self._path):
            txt = f'{_iniTxt}: invalid suffix for {self.dataFormat}'
            return self._returnFalse(txt)

        # checking parameter file
        if self._parameterFile is None:
            errorMsg = f'{_iniTxt}: parameter file is undefined'
            return self._returnFalse(errorMsg)

        if not self._parameterFile.exists():
            errorMsg = f'{_iniTxt}: parameter file does not exist'
            return self._returnFalse(errorMsg)

        if not self._parameterFile.is_file():
            errorMsg = f'{_iniTxt}: parameter file is not a file'
            return self._returnFalse(errorMsg)

        if self._binaryFile is None:
            errorMsg = f'{_iniTxt}: binary file is undefined'
            return self._returnFalse(errorMsg)

        if not self._binaryFile.exists():
            errorMsg = f'{_iniTxt}: binary file does not exist'
            return self._returnFalse(errorMsg)

        if not self._binaryFile.is_file():
            errorMsg = f'{_iniTxt}: binary file is not a file'
            return self._returnFalse(errorMsg)

        # if not self.shouldBeValid:
        #     errorMsg = f'{_iniTxt}: should have defined a valid {self.dataFormat} file, but did not'
        #     return self._returnFalse(errorMsg)

        self.isValid = True
        self.errorString = ''

        return True

    def checkValid(self) -> bool:
        """check if valid format corresponding to dataFormat by:
        - checking suffix and existence of path
        - reading (and checking dimensionCount) parameters

        :return: True if ok, False otherwise
        """
        self.isValid = False
        self.errorString = 'Checking validity'

        # checking path
        _p = self.path
        _iniTxt = f'{self.dataFormat} spectrum, path "{_p}"'

        if _p is None:
            txt = f'{_iniTxt}: undefined'
            return self._returnFalse(txt)

        if not self.checkSuffix(_p):
            txt = f'{_iniTxt}: invalid suffix'
            return self._returnFalse(txt)

        if not self.hasValidPath():
            txt = f'{_iniTxt}: does not exist'
            return self._returnFalse(txt)

        if not self.allowDirectory and self.path.is_dir():
            txt = f'{_iniTxt}: is directory and not valid'
            return self._returnFalse(txt)

        # checking opening file and reading parameters
        try:
            with self.openExistingFile():  # This will also read the parameters
                pass
                # self.readParameters()
        except RuntimeError as es:
            txt = f'{_iniTxt}: Reading parameters failed with error: "{es}"'
            return self._returnFalse(txt)

        # Check dimensionality; should be > 0
        if self.dimensionCount == 0:
            txt = f'{_iniTxt}: dimensionCount = 0'
            return self._returnFalse(txt)

        self.isValid = True
        self.errorString = ''
        return True

    def checkParameters(self, spectrum) -> bool:
        """Check parameters of self to establish if it matches with spectrum
        :param spectrum: a Spectrum instance
        :return True if matches
        """
        _p = self.path
        _iniTxt = f'{self.dataFormat} spectrum, path "{_p}"'

        # check some fundamental parameters
        if self.dimensionCount != spectrum.dimensionCount:
            txt = f'{_iniTxt}: Incompatible dimensionCounts (spectrum: {spectrum.dimensionCount}, dataSource: {self.dimensionCount})'
            return self._returnFalse(txt)

        for np_spectrum, np_dataSource in zip(spectrum.pointCounts, self.pointCounts):
            if np_spectrum != np_dataSource:
                txt = f'{_iniTxt}: Incompatible pointCounts (spectrum: {spectrum.pointCounts}, dataSource: {self.pointCounts})'
                return self._returnFalse(txt)

        for isC_spectrum, isC_dataSource in zip(spectrum.isComplex, self.isComplex):
            if isC_spectrum != isC_dataSource:
                txt = f'{_iniTxt}: Incompatible isComplex definitions (spectrum: {spectrum.isComplex}, dataSource: {self.isComplex})'
                return self._returnFalse(txt)

        return True

    @classmethod
    def checkForValidFormat(cls, path):
        """check if valid format corresponding to dataFormat by:
        - creating an instance of the class
        - calling checkValid method

        :return: None or instance of the class

        depricated: initate an instance and use the isValid attribute
        """
        instance = cls(path=path)
        if not instance.isValid:
            return None
        else:
            return instance

    def _checkFilePath(self, newFile, mode, overwrite=False):
        """Helper function to do checks on path"""

        _path = self.path
        if _path is None:
            raise RuntimeError('openFile: no path defined for %s' % self)

        if not newFile and not _path.exists():
            raise FileNotFoundError('path "%s" does not exist' % _path)

        if newFile and not _path.parent.exists():
            raise FileNotFoundError(f'parent path "{_path.parent}" does not exist')

        if newFile and _path.exists() and not overwrite and mode != self.defaultAppendMode:
            raise FileExistsError('path "%s" exists (mode=%s)' % (_path, mode))

    def getAllFilePaths(self) -> list:
        """
        Get all the files handles by this dataSource. Generally, this will be the path that
        the dataSource represents, but sometimes there might be more; i.e. for certain spectrum
        dataFormats that handle more files; like a binary and a parameter file.
        To be subclassed for those instances

        :return: list of Path instances
        """
        return [self.path]

    def openFile(self, mode, **kwds):
        """open self.path, set self.fp,
        Raise RunTimeError on opening errors
        :return self.fp
        """
        if mode is None:
            raise ValueError('%s.openFile: Undefined open mode' % self.__class__.__name__)
        newFile = not mode.startswith('r')

        if self.hasOpenFile():
            self.closeFile()

        try:
            self._checkFilePath(newFile, mode)
            self.fp = self.openMethod(str(self.path), mode, **kwds)
            self.mode = mode

        except Exception as es:
            self.closeFile()
            text = '%s.openFile: %s' % (self.__class__.__name__, str(es))
            getLogger().error(text)
            raise RuntimeError(text)

        if not newFile:
            # cache will be defined after parameters are read
            pass
        else:
            self.disableCache()  # No caching on writing; that creates sync issues

        # getLogger().debug('openFile: %s' % self)

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

        self.closeFile()  # Wil close if open, do nothing otherwise
        self.openFile(mode=mode)
        self.readParameters()
        try:
            yield self

        except Exception as es:
            self.closeFile()
            getLogger().error('%s.openExistingFile: "%s"' % (self.__class__.__name__, str(es)))
            raise es

        finally:
            self.closeFile()

    @contextmanager
    def openNewFile(self, path=None, mode=None, overwrite=False):
        """Open new file, write parameters, and close at the end
        Yields self; i.e. one can do:

        with SpectrumDataSource(spectrum=sp).openNewFile(path) as ds:
            ds.writeSliceData(data)
        """
        if path is not None:
            self.setPath(path, checkSuffix=True)

        if mode is None:
            mode = self.defaultOpenWriteMode

        try:
            self.closeFile()  # Will close if open disgarding everything, do nothing otherwise
            getLogger().debug('%s.openNewFile: calling openFile' % self.__class__.__name__)
            self.openFile(mode=mode, overwrite=overwrite)
            yield self

        except Exception as es:
            self.closeFile()
            txt = f'openNewFile: {es}'
            self.isValid = False
            self.errorString = txt
            getLogger().error(txt)
            raise es

        getLogger().debug('%s.openNewFile: writing parameters and calling closeFile' %
                          self.__class__.__name__)
        self.isValid = True
        self.errorString = ''
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
        if self.isBuffered:
            self.closeHdf5Buffer()

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

        if self.mode.startswith('r') and self.isBlocked and self.hasBlockCached:
            self._setMaxCacheSize(self.maxCacheSize)
        else:
            self.disableCache()  # No caching on writing; that creates sync issues

        return self

    def writeParameters(self):
        """to be subclassed"""
        raise NotImplementedError('Not implemented')

    def copyFiles(self, destinationDirectory, overwrite=False) -> list:
        """Copy all data files to a new destination directory
        :param destinationDirectory: a string or Path instance defining the destination directory
        :param overwrite: Overwrite any existing files
        :return A list of files copied
        """
        import shutil

        _destination = aPath(destinationDirectory)
        if not _destination.is_dir():
            raise ValueError(f'"{_destination}" is not a valid directory')

        result = []
        for _p in self.getAllFilePaths():
            _newPath = _p.copyFile(_destination, overwrite=overwrite)
            result.append(_newPath)

        return result

    #=========================================================================================
    # Data access methods
    #=========================================================================================

    def checkForValidPosition(self, position):
        """Checks if position (1-based) is valid, expand if None and append if necessay
        Return valid position
        """
        if self.dimensionCount == 0:
            raise RuntimeError('%s: Undefined parameters' % self)

        if position is None:
            position = [1] * self.dimensionCount

        if not isIterable(position):
            raise ValueError('checkForValidPosition: position must be an tuple or list')
        position = list(position)

        if len(position) < self.dimensionCount:
            position += [1] * (self.dimensionCount - len(position))
        position = position[0:self.dimensionCount]

        for idx, p in enumerate(position):
            if not (1 <= p <= self.pointCounts[idx]):
                raise ValueError('checkForValidPosition: dimension %d: value must be in [1,%d]: got "%d"' % \
                                 (idx + 1, self.pointCounts[idx], p))
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
            raise ValueError('checkForValidPlane: invalid xDim (%d), should be in range [1,%d]' % (xDim, self.dimensionCount))
        if not (1 <= yDim <= self.dimensionCount):
            raise ValueError('checkForValidPlane: invalid yDim (%d), should be in range [1,%d]' % (yDim, self.dimensionCount))
        if xDim == yDim:
            raise ValueError('checkForValidPlane: xDim == yDim = %d' % (xDim,))

        # set position of xDim, yDim to 1; to assure compatibilty with SpectrumData
        # classes
        position[xDim - 1] = 1
        position[yDim - 1] = 1

        return position

    def getPlaneData(self, position: Sequence = None, xDim: int = 1, yDim: int = 2) -> PlaneData:
        """Get plane defined by xDim, yDim and position (all 1-based)
        Check for hdf5buffer first, then blocked format
        Optionally to be subclassed

        :return PlaneData (i.e. numpy.ndarray) object.
        """

        if self.isBuffered:
            self._checkBuffer()
            return self.hdf5buffer.getPlaneData(position=position, xDim=xDim, yDim=yDim)

        position = self.checkForValidPlane(position=position, xDim=xDim, yDim=yDim)
        if self.isBlocked:
            data = self._readBlockedPlane(xDim=xDim, yDim=yDim, position=position)
            data *= self.dataScale
            return data

        else:
            raise NotImplementedError('Not implemented')

    def setPlaneData(self, data, position: Sequence = None, xDim: int = 1, yDim: int = 2):
        """Set the plane data defined by xDim, yDim and position (all 1-based)
        from NumPy data array

        Can be subclassed
        """
        if self.isBuffered:
            self._checkBuffer()
            self.hdf5buffer.setPlaneData(data=data, position=position, xDim=xDim, yDim=yDim)
            return
        else:
            raise RuntimeError('setPlaneData: not buffered and no valid implementation')

    def checkForValidSlice(self, position, sliceDim):
        """Checks that sliceDim is valid, returns valid (expanded) position if None
        """
        if self.dimensionCount == 0:
            raise RuntimeError('%s: Undefined parameters' % self)

        position = self.checkForValidPosition(position)

        if not (1 <= sliceDim <= self.dimensionCount):
            raise ValueError('invalid sliceDim (%d), should be in range [1,%d]' % (sliceDim, self.dimensionCount))

        # set position of sliceDim to 1; to assure compatibility with SpectrumData
        # classes
        position[sliceDim - 1] = 1

        return position

    def getSliceData(self, position: Sequence = None, sliceDim: int = 1) -> SliceData:
        """Get slice defined by sliceDim and position (all 1-based)
        Check for hdf5buffer first, then blocked format
        Optionally to be subclassed

        :return SliceData object (i.e. a numpy.ndarray) object
        """
        if self.isBuffered:
            self._checkBuffer()
            return self.hdf5buffer.getSliceData(position=position, sliceDim=sliceDim)

        elif self.isBlocked:
            position = self.checkForValidSlice(position=position, sliceDim=sliceDim)
            data = self._readBlockedSlice(sliceDim=sliceDim, position=position)
            # np.nan_to_num(data, copy=False, nan=0.0, posinf=0.0, neginf=0.0)  # NOTE:ED - do we need this here?
            data *= self.dataScale
            return data

        else:
            raise NotImplementedError('Not implemented')

    def setSliceData(self, data, position: Sequence = None, sliceDim: int = 1):
        """Set data as slice defined by sliceDim and position (all 1-based)
        Can be subclassed
        """
        if self.isBuffered:
            self._checkBuffer()
            self.hdf5buffer.setSliceData(data=data, position=position, sliceDim=sliceDim)
        else:
            raise RuntimeError('setSliceData, not buffered and no valid implementation')

    def getSliceDataFromPlane(self, position, xDim: int, yDim: int, sliceDim: int) -> SliceData:
        """Routine to get sliceData using getPlaneData
        :return SliceData object (i.e. a numpy.ndarray) object
        """
        # adapted from earlier Spectrum-class method

        if not (sliceDim == xDim or sliceDim == yDim):
            raise ValueError('sliceDim (%s) not in plane (%s,%s)' % (sliceDim, xDim, yDim))

        position = self.checkForValidPlane(position, xDim, yDim)

        sliceIdx = position[yDim - 1] - 1 if sliceDim == xDim else position[xDim - 1] - 1  # position amd dimensions are 1-based

        # Improve caching,
        position[xDim - 1] = 1
        position[yDim - 1] = 1
        planeData = self.getPlaneData(position, xDim, yDim)

        if sliceDim == xDim:
            data = planeData[sliceIdx, 0:]
        else:
            # sliceDim == yDim:
            data = planeData[0:, sliceIdx]

        return data

    def getPointData(self, position: Sequence = None) -> float:
        """Get value defined by position (1-based, integer values)
        Use getPointValue() for an interpolated value
        """
        if self.isBuffered:
            self._checkBuffer()
            return self.hdf5buffer.getPointData(position=position)

        elif self.isBlocked:
            position = self.checkForValidPosition(position)
            data = self._readBlockedPoint(position)
            data *= self.dataScale
            return data

        else:
            # piggyback on getSliceData
            data = self.getSliceData(position=position, sliceDim=1)
            return float(data[position[0] - 1])

    def setPointData(self, value, position: Sequence = None) -> float:
        """Set point value defined by position (1-based)
        Can be sub-classed
        """
        if self.isBuffered:
            self._checkBuffer()
            return self.hdf5buffer.setPointData(value=value, position=position)
        else:
            raise RuntimeError('setPointData: not buffered or no valid implementation')

    def getPointValue(self, position, aliasingFlags=None):
        """Get interpolated value defined by position (1-based, float values), optionally aliased
        The result is calculated from a weighted average of the two values at the neighbouring
        grid points for each dimension

        aliasingFlags: Optionally allow for aliasing per dimension:
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
            diffs = factor * numpy.diff(data, axis=-1)
            slices = [slice(0, n) for n in diffs.shape]
            result = numpy.add(data[tuple(slices)], diffs)
            result = numpy.squeeze(result, axis=-1)
            # print('result>\n', result,  '\nshape: ', result.shape, '\n')
            return result

        # get the fractions of position; i.e. if position=(324.4, 120.9, 33.7),
        # get ( 0.4, 0.9, 0.7 )
        fractions = [p - float(int(p)) for p in position]
        # get the nD slice data around position; i.e. if position=(324.4, 120.9, 33.7),
        # get ( (324,325), (120,121), (33,34) )
        sliceTuples = [(int(p), int(p) + 1) for p in position]
        pointData = self.getRegionData(sliceTuples=sliceTuples, aliasingFlags=aliasingFlags)

        for f in fractions:
            pointData = interpolate(pointData, factor=f)

        return pointData.item()

    def checkForValidRegion(self, sliceTuples, aliasingFlags):
        """Checks if slicesTuples are valid

        aliasingFlags: Optionally allow for aliasing per dimension:
            0: No aliasing
            1: aliasing with positive sign
           -1: aliasing with negative sign
        """
        if sliceTuples is None or not isIterable(sliceTuples):
            raise ValueError('invalid sliceTuples argument; expect list/tuple, got %s' %
                             sliceTuples)

        if len(sliceTuples) != self.dimensionCount:
            raise ValueError('invalid sliceTuples argument; dimensionality mismatch')

        sliceTuples = list(sliceTuples)

        if aliasingFlags is None:
            raise ValueError('invalid aliasing argument; None value')

        if len(aliasingFlags) != self.dimensionCount:
            raise ValueError('invalid aliasing argument; dimensionality mismatch')

        for idx, sTuple in enumerate(sliceTuples):  # do not call this slice! as it override the python slice object
            if sTuple is None:
                sTuple = (1, self.pointCounts[idx])

            if not isIterable(sTuple) or len(sTuple) != 2:
                raise ValueError('invalid sliceTuple for dimension %s; got %s' %
                                 (idx + 1, sTuple))

            # assure a to be a tuple
            sliceTuples[idx] = tuple(sTuple)
            start, stop = sTuple

            if aliasingFlags[idx] == 0:
                if start < 1:
                    raise ValueError('invalid sliceTuple (start,stop)=%r for dimension %s; start < 1 (%s)' %
                                     (sTuple, idx + 1, start))

                if stop > self.pointCounts[idx]:
                    raise ValueError('invalid sliceTuple (start,stop)=%r for dimension %s; stop > %s (%s)' %
                                     (sTuple, idx + 1, self.pointCounts[idx], stop))

            if start > stop:
                raise ValueError('invalid sliceTuple (start,stop)=%r for dimension %s; start (%s) > stop (%s)' %
                                 (sTuple, idx + 1, start, stop))

        return sliceTuples

    def _getRegionData(self, sliceTuples, aliasingFlags=None):
        """Return an numpy array containing the region data; see getRegionData description
        implementation based upon getSliceData method
        GWV 13/01/2022: new implementation
        """
        sliceDim = 1  # only works for 1, as there is otherwise a np shape mismatch
        sliceIdx = sliceDim - 1

        newPoints = [s[1] - s[0] + 1 for s in sliceTuples]
        slicePoints = newPoints[sliceIdx]

        # first collect all the folded/unfolded/indexed points
        pointDict = {}
        for foldedPosition, aliased in self._selectedPointsIterator(sliceTuples, excludeDimensions=[sliceDim]):

            foldedPosition = tuple(foldedPosition)
            unFoldedPosition = tuple([a * np + p
                                      for p, a, np in zip(foldedPosition, aliased, self.pointCounts)])
            indxPosition = tuple([(p - sliceTuples[idx][0])
                                  for idx, p in zip(self.dimensionIndices, unFoldedPosition)])
            # get aliasing factor determined by dimensions other than sliceDim
            factor = 1.0
            for idx, fac, aliase in zip(self.dimensionIndices, aliasingFlags, aliased):
                if idx != sliceIdx and aliase:
                    factor *= fac

            theList = pointDict.setdefault(foldedPosition, [])
            theList.append((unFoldedPosition, indxPosition, factor))

        # print('pointDict:')
        # for key, val in pointDict.items():
        #     print(key, ':', val)

        # Assemble the data
        # data = numpy.zeros(newPoints[::-1], dtype='float32')  # the final result
        data = RegionData(shape=newPoints[::-1],
                          dataSource=self, dimensions=self.dimensions,
                          position=[st[0] for st in sliceTuples]
                          )

        newSliceData = numpy.zeros(newPoints[sliceIdx], dtype='float32')  # the unaliased slice

        for foldedPosition, _vals in pointDict.items():
            # get the slice for foldedPosition (only once)
            sliceData = self.getSliceData(position=foldedPosition, sliceDim=sliceDim)
            # unaliase the slice
            sliceStart = sliceTuples[sliceIdx][0]
            sliceStop = sliceTuples[sliceIdx][1]
            _fillSlice(sliceData,
                       start=sliceStart, stop=sliceStop, aliasing=aliasingFlags[sliceIdx],
                       resultSlice=newSliceData)
            # print('>>', foldedPosition, newSliceData)

            # put the unaliased slice at all required positions in the data
            for unFoldedPosition, indxPosition, factor in _vals:
                slices = [slice(idx, idx + 1, 1) for idx in indxPosition]
                slices[sliceIdx] = slice(0, slicePoints, 1)
                slices = tuple(slices[::-1])  # x,y,z order is reversed
                data[slices] = factor * newSliceData[:]

        return data

    def getRegionData(self, sliceTuples, aliasingFlags=None) -> RegionData:
        """Return an numpy array containing the points defined by sliceTuples

        :param sliceTuples, list [(start_1,stop_1), (start_2,stop_2), ...],
               sliceTuples are 1-based; sliceTuple stop values are inclusive (
               i.e. different from the python slice object)

        :param aliasingFlags: Optionally allow for aliasing per dimension:
                 0: No aliasing
                 1: aliasing with positive sign
                -1: aliasing with negative sign

        :return RegionData (i.e. numpy.ndarray) object.
        """
        if self.isBuffered:
            self._checkBuffer()
            return self.hdf5buffer.getRegionData(sliceTuples=sliceTuples, aliasingFlags=aliasingFlags)

        if aliasingFlags is None:
            aliasingFlags = [0] * self.dimensionCount

        sliceTuples = self.checkForValidRegion(sliceTuples, aliasingFlags)
        # No need to scale, as _getRegionData relies on getSliceData, which is already scaled
        regionData = self._getRegionData(sliceTuples=sliceTuples, aliasingFlags=aliasingFlags)

        return regionData

    def _estimateInitialContourBase(self, multiplier=1.41):
        """Estimate  the ContourBase based on a quick approximation of the noise level.
        Use mean of abs of dataPlane or dataSlice
        """

        if self.dimensionCount == 1:
            data = self.getSliceData()
            stdFactor = 0.5

        elif self.dimensionCount == 2:
            # 2D: presumably t has data (and potentially water!)
            data = self.getPlaneData()
            data.flatten()
            stdFactor = 0.5

        else:
            # 3D and up: use a yz-plane, about 10 points in; this plane is likely mostly empty
            position = [min(10, self.pointCounts[0])] + [1] * (self.dimensionCount-1)
            data = self.getPlaneData(xDim=specLib.Y_DIM, yDim=specLib.Z_DIM, position=position)
            data = data.flatten()
            stdFactor = 2.0

        absData = numpy.absolute(data)
        absData = absData[numpy.isfinite(absData)]
        median = numpy.median(absData)
        _temp = data[numpy.isfinite(data)].astype(numpy.float64)
        std = numpy.std(data)
        if std != std:
            # std may still be nan because contains HUGE numbers
            std = 0
        noiseLevel = median + stdFactor * std
        positiveContourBase = float(noiseLevel) * multiplier

        return positiveContourBase



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

        :return a (position, aliased) tuple of lists
        """

        if len(sliceTuples) != self.dimensionCount:
            raise ValueError('invalid sliceTuples argument; dimensionality mismatch')

        for dim in excludeDimensions:
            if dim < 1 or dim > self.dimensionCount:
                raise ValueError('invalid dimension "%s" in excludeDimensions' % dim)

        # get dimensions to iterate over
        iterDims = list(set(self.dimensions) - set(excludeDimensions))

        # get relevant iteration parameters
        slices = [sliceTuples[dim - 1] for dim in iterDims]
        indices = [dim - 1 for dim in iterDims]
        iterData = list(zip(iterDims, slices, indices))

        def _nextPosition(currentPosition):
            """Return a (done, position) tuple derived from currentPosition"""
            for _dim, _sliceTuple, _idx in iterData:
                start = _sliceTuple[0]
                stop = _sliceTuple[1]
                if currentPosition[_idx] + 1 <= stop:  # still an increment to make in this dimension
                    currentPosition[_idx] += 1
                    return (False, currentPosition)
                else:  # reset this dimension
                    currentPosition[_idx] = start
            return (True, None)  # reached the end

        # loop over selected slices
        loopPosition = [start for start, stop in sliceTuples]
        done = False
        while not done:
            position = [((p - 1) % np) + 1 for p, np in zip(loopPosition, self.pointCounts)]
            aliased = [(p - 1) // np for p, np in zip(loopPosition, self.pointCounts)]

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
                position[xDim - 1] = 1
                position[yDim - 1] = 1
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
                position[sliceDim - 1] = 1
                sliceData = self.getSliceData(position=position, sliceDim=sliceDim)
                yield (position, sliceData)

    def allPoints(self):
        """An iterator over all points, yielding (position, pointValue) tuples
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

    @property
    def isBuffered(self):
        """ReturnTrue if file is buffered"""
        return self._isBuffered

    def setBuffering(self, isBuffered: bool, bufferIsTemporary: bool = True, bufferPath=None):
        """Define the SpectrumDataSource buffering status
        :param isBuffered (True, False): set the buffering status
        :param bufferIsTemporary (True, False): define buffer as temporary (i.e. disgarded on close)
        :param bufferPath: optional path to store the buffer file
        """
        if self.isBuffered:
            self.closeHdf5Buffer()

        self._isBuffered = isBuffered
        self._bufferFilled = False
        self._bufferIsTemporary = bufferIsTemporary
        self._bufferPath = bufferPath

        # close the current file as all will go from the buffer (once filled)
        if self.hasOpenFile():
            self.closeFile()

    def _checkBuffer(self):
        """Create (if needed) and fill Hdf5 buffer
        """
        if self.hdf5buffer is None:
            # Buffer has not been created
            self.initialiseHdf5Buffer()
        if not self._bufferFilled:
            self.fillHdf5Buffer()

    def initialiseHdf5Buffer(self):
        """Initialise a Hdf5SpectrumBuffer instance.
        :return: Hdf5SpectrumBuffer instance
        """
        from ccpn.core.lib.SpectrumDataSources.Hdf5SpectrumDataSource import Hdf5SpectrumDataSource
        from ccpn.framework.Application import getApplication

        if not self.isBuffered:
            raise RuntimeError('initialiseHdf5Buffer: buffering not active, use setBuffering() method first')

        self.closeHdf5Buffer()

        if self._bufferIsTemporary:
            # Construct a path for temporary buffer using the tempfile methods in _getTemporaryPath
            prefix = 'hdf5buffer_%s_' % self.nameFromPath()
            path = getApplication()._getTemporaryPath(prefix=prefix, suffix=Hdf5SpectrumDataSource.suffixes[0])

        else:
            # take path as defined in _bufferPath, or construct from self.path if None
            path = self._bufferPath
            if self._bufferPath is None:
                path = self.path.withSuffix(Hdf5SpectrumDataSource.suffixes[0]).uniqueVersion()
            # tFile = None

        # create a hdf5 buffer file instance
        hdf5buffer = Hdf5SpectrumDataSource(path=path)
        hdf5buffer.copyParametersFrom(self)
        # do not use openNewFile as it has to remain open to allow for filling the buffer
        hdf5buffer.openFile(mode=Hdf5SpectrumDataSource.defaultOpenWriteMode)
        # backward and forward linkages
        hdf5buffer.parent = self
        self.hdf5buffer = hdf5buffer
        self._isBuffered = True
        self._bufferFilled = False
        # hdf5buffer is ready now; future read/writes will use it to retrieve/store data
        getLogger().debug('initialiseHdf5Buffer: opened %s' % self.hdf5buffer)
        return self.hdf5buffer

    def fillHdf5Buffer(self):
        """Fill hdf5Buffer with data from self;
        this routine will be subclassed in the more problematic cases such as NmrPipe
        """
        if not self.isBuffered or self.hdf5buffer is None:
            raise RuntimeError('fillHdf5Buffer: no hdf5Buffer defined')

        getLogger().debug('fillHdf5Buffer: filling buffer %s' % self.hdf5buffer)
        # To use the non-buffered reading routines for filling the buffer,
        # pretend it is (temporarily) not buffered
        self._isBuffered = False
        self.copyDataTo(self.hdf5buffer)
        self._isBuffered = True
        self._bufferFilled = True

        # close the source, as all data are now in the buffer
        if self.hasOpenFile():
            self.fp.close()
            self.fp = None
            self.mode = None

    def closeHdf5Buffer(self):
        """Close the hdf5Buffer"""
        if not self.isBuffered:
            raise RuntimeError('closeHdf5Buffer: no hdf5Buffer defined')

        if self.hdf5buffer is not None:
            getLogger().debug('Closing buffer %s' % self.hdf5buffer)
            self.hdf5buffer.closeFile()
            if self._bufferIsTemporary:
                self.hdf5buffer.path.removeFile()

        self.hdf5buffer = None
        self._bufferFilled = False

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
        """Print all to path"""
        path.write(str(self) + '\n')
        path.write('%-24s: %s\n' % ('path', self.path))
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
            fName = self.path.name if self.path is not None else str(None)
            return '<%s: _D (), %s>' % (self.__class__.__name__, fName)
        else:
            if self.isBuffered:
                fpStatus = '%r' % 'buffered'
                if self.hdf5buffer is not None:
                    pathName = self.hdf5buffer.path.name
                else:
                    pathName = 'closed'
            else:
                if self.hasOpenFile():
                    fpStatus = '%r' % self.mode
                    pathName = self.path.name
                else:
                    fpStatus = '%r' % 'closed'
                    pathName = self.path.name

            return '<%s: %dD (%s), (%s,%r)>' % (self.__class__.__name__,
                                                self.dimensionCount,
                                                'x'.join([str(p) for p in self.pointCounts]),
                                                fpStatus,
                                                pathName
                                                )


#end class


def _fillSlice(sliceData, start, stop, aliasing, resultSlice=None):
    """Helper function for _getRegionData.
    Fill a slice from sliceData, trimming or extend on either side dependng on start, stop
        :param start,stop: start, stop indices (1-based)
        :param aliasing: the aliasing flag (-1,0,1) to calculate the sliceFactor
        :return the new numpy slice array
    """
    aliasing = float(aliasing)
    sliceFactor = pow(aliasing, 0)

    nPoints = sliceData.shape[0]
    start = start - 1

    if resultSlice is None:
        resultSlice = numpy.zeros((stop - start,), dtype=sliceData.dtype)

    # Simple cases:
    if start >= 0 and stop <= nPoints:
        # within the limits of sliceData
        resultSlice[:] = sliceData[start:stop]
        # print(f' > mid        {start+1}  {stop}    {resultSlice}')
        return resultSlice

    elif -nPoints <= start < 0 and stop <= 0:
        # exclusively in the left extension
        sliceFactor = pow(aliasing, 1)
        resultSlice[:] = sliceData[start + nPoints:stop + nPoints] * sliceFactor  # need to account for zero
        return resultSlice

    elif nPoints <= start < nPoints * 2 and stop <= nPoints * 2:
        # exclusively in the right extension
        sliceFactor = pow(aliasing, 1)
        resultSlice[:] = sliceData[start - nPoints:stop - nPoints] * sliceFactor
        return resultSlice

    elif -nPoints <= start < 0 and stop <= nPoints:
        # at most one extension on left
        sliceFactor = pow(aliasing, 1)
        numpy.concatenate((sliceData[start:] * sliceFactor, sliceData[0:stop]), out=resultSlice)
        return resultSlice

    elif start >= 0 and stop <= nPoints * 2:
        # at most one extension on the right
        sliceFactor = pow(aliasing, 1)
        numpy.concatenate((sliceData[start:], sliceData[0:stop - nPoints] * sliceFactor), out=resultSlice)
        return resultSlice

    elif -nPoints < start < 0 and nPoints <= stop <= nPoints * 2:
        # at most one extension on the left and right;
        # might occur regularly for peak picking of a plane with one-point extension
        sliceFactor = pow(aliasing, 1)
        numpy.concatenate((sliceData[start:] * sliceFactor, sliceData, sliceData[0:stop - nPoints] * sliceFactor), out=resultSlice)
        return resultSlice

    foldedStop = stop // nPoints
    foldedStopIdx = stop % nPoints

    idx = start
    result_idx = 0
    while idx < stop:

        folded = idx // nPoints  # integer division
        sliceFactor = pow(aliasing, abs(folded))

        idx_1 = idx % nPoints
        if folded == foldedStop:
            # This accommodates the stop point
            idx_2 = foldedStopIdx
        else:
            # This accommodates any start value, also < 0; i.e. the initial left part will be
            # truncated to the first multiple of nPoints
            idx_2 = min(idx_1 + nPoints, nPoints)
        increment = idx_2 - idx_1
        # print('>', start, stop, '>>', idx_1, idx_2)

        # copy the data
        resultSlice[result_idx:result_idx + increment] = sliceData[idx_1:idx_2] * sliceFactor
        idx += increment
        result_idx += increment

    return resultSlice


from ccpn.util.traits.CcpNmrTraits import Instance
from ccpn.util.traits.TraitJsonHandlerBase import CcpNmrJsonClassHandlerABC


class DataSourceTrait(Instance):
    """Specific trait for a Datasource instance encoding access to the (binary) spectrum data.
    None indicates no spectrumDataSource has been defined
    """
    klass = SpectrumDataSourceABC

    def __init__(self, **kwds):
        Instance.__init__(self, klass=self.klass, allow_none=True, **kwds)


    class jsonHandler(CcpNmrJsonClassHandlerABC):
        # klass = SpectrumDataSourceABC
        pass


def testMain():
    testSlice = numpy.arange(4, dtype=numpy.int32) + 1
    aliasing = -1

    for ln in (0, 2, 4, 7, 13):
        print(f'\nARRAY   {testSlice * aliasing}{testSlice}{testSlice * aliasing} {testSlice} {testSlice * aliasing}{testSlice}')
        print(f'LEN -> {ln}')
        for start in range(-7, 11 - ln, 1):
            _fillSlice(testSlice, start, start + ln, aliasing=aliasing)


if __name__ == '__main__':
    testMain()
