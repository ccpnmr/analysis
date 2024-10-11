"""
This file contains the ndf5-file data access code
it serves as an interface between the V3 Spectrum class and the actual ndf5 data format
The ndf5 format has writing capabilities

Version history:
No-version:     Luca's initial implementation
1.0 (float):    Version info (float) stored as 'version' in parameters;
                spectralWidth definition updated (if need be)
1.0.1 (string): hdf5 metadata; stored in attributes top object (i.e. self.fp)
1.1.0 (string): hdf5 metadata; implementation change

See SpectrumDataSourceABC for a description of the methods
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
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2024-10-11 10:06:55 +0100 (Fri, October 11, 2024) $"
__version__ = "$Revision: 3.2.5.GWV $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2020-11-20 10:28:48 +0000 (Fri, November 20, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Sequence, Tuple
import h5py

from ccpn.util.Logging import getLogger
from ccpn.util.Common import isIterable
from ccpn.util.traits.CcpNmrTraits import CString, TList, CEnum
from ccpn.framework.Version import VersionString

from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import SpectrumDataSourceABC
from ccpn.core._implementation.SpectrumData import SliceData, PlaneData, RegionData


# #--------------------------------------------------------------------------------------------------
# # hdf5 metadata keys, as stored in the 'top' object and copied into the Hdf5Metadata object
# # NB:
# # this is different from the metadata of the SpectrumDataSourceABC, i.e. CcpNmrJson object
# # from which the Hdf5DataSource class is derived.
# # It is also different from the Traits metadata (as defined by the tag() method)
# #
# NDF5_VERSION_KEY = 'ndf5_version'
# NDF5_VERSION = VersionString('1.1.0')  # Current HDF5 implementation version
#
# NDF5_UID_KEY = 'uid'
# NDF5_USER_KEY = 'user'
# NDF5_DATE_KEY = 'date'
# NDF5_SPECTROMETER_KEY = 'spectrometer'
#
# # the key in the metadata dict defining the dict of all data types contained in the file
# NDF5_DATATYPES_KEY = 'dataTypes'
# # the key in the metadata dict defining datatype used for retrieving the spectrum data
# NDF5_SPECTRUM_DATATYPE_KEY = 'spectrum_dataType'
#
# _defaultNdf5MetadataDict = {
#
#     NDF5_VERSION_KEY : str(NDF5_VERSION),
#     NDF5_UID_KEY : None,
#     NDF5_USER_KEY : None,
#     NDF5_DATE_KEY : None,
#     NDF5_SPECTROMETER_KEY : None,
#
#     # data types
#     NDF5_DATATYPES_KEY : {},
#     NDF5_SPECTRUM_DATATYPE_KEY : None,
#
# }
#
# #--------------------------------------------------------------------------------------------------
# # ndf5 dataTypes
# #--------------------------------------------------------------------------------------------------
#
# NDF5_SPECTRUM = 'spectrum'
# NDF5_NUS = 'nus'
#
# # spectrum: a complete (i.e. all dimensions), np.ndarray-like data matrix
# NDF5_DATATYPE_SPECTRUM_NDARRAY = f'dataType_{NDF5_SPECTRUM}_ndarray'
#
# # pulseprogram:
# NDF5_DATATYPE_PULSEPROGRAM =     f'dataType_pulseprogram'
#
# # NUS:
# NDF5_DATATYPE_NUSLIST =          f'dataType_{NDF5_NUS}_nuslist'
# NDF5_DATATYPE_NUSDATA =          f'dataType_{NDF5_NUS}_nusdata'
#
# # Dict of ndf5 data types and their (default) ndf5-file storage key;
# _ndf5DataTypes = {
#     NDF5_DATATYPE_PULSEPROGRAM : 'pulseprogram',
#     NDF5_DATATYPE_SPECTRUM_NDARRAY : 'spectrumData', # historical; keep for now
#     NDF5_DATATYPE_NUSLIST : 'nus/nuslist',
#     NDF5_DATATYPE_NUSDATA : 'nus/nusdata',
# }
#

# #--------------------------------------------------------------------------------------------------
# # Compression modes
# #
# # GWV 2020 for full files:
# #   lzf compression seems not to yield any improvement, but rather a increase in file size;
# #   gzip compression some (max 30%) reductions, albeit at a speed-penalty
# # GWV 7/10/2024 update:
# #   gzip works well on file writing sparse data and the sparse=True option
#
# NDF5_COMPRESSION_GZIP = 'gzip'
# NDF5_COMPRESSION_LZF = 'lzf'
# # 'szip' not in conda distribution
# # NDF5_COMPRESSION_SZIP = 'szip'
# NDF5_COMPRESSION_MODES = (NDF5_COMPRESSION_GZIP, NDF5_COMPRESSION_LZF)

#--------------------------------------------------------------------------------------------------

from ccpn.core.lib.SpectrumDataSources.lib.Ndf5File import Ndf5File, NDF5_COMPRESSION_MODES

NONE_STR = '__NONE__'

class Hdf5SpectrumDataSource(SpectrumDataSourceABC):
    """
    CcpNmr ndf5-based binary nD (n=1-8) spectral data format. Allows for reading and writing.
    """
    #=========================================================================================

    dataFormat = 'Hdf5'
    # Conveniances; subclassed in the respective classes
    isHdf5Spectrum = True

    isBlocked = False  # ndf5 format is inherently blocked, but we do not use the implemented
    # routines in the ABC, but rather have ndf5 do the slicing
    hasBlockCached = False  # Flag indicating if block data are cached

    wordSize = 4
    headerSize = 0
    blockHeaderSize = 0
    isFloatData = True
    hasWritingAbility = True  # flag that defines if dataFormat implements writing methods

    suffixes = ['.ndf5', '.hdf5']
    openMethod = 'NOT-USED'
    defaultOpenReadMode = 'r'   # read/write, file must exists
    defaultOpenReadWriteMode = 'r+'
    defaultOpenWriteMode = 'w'  # creates, truncates if exists
    defaultAppendMode = 'a'

    compressionMode = CEnum(mapping=NDF5_COMPRESSION_MODES, default_value=None)

    _NONE = bytes(NONE_STR, 'utf8')

    #=========================================================================================

    def __init__(self, path=None, spectrum=None, dimensionCount=None, checkValid=True):
        """initialise instance; optionally set path or associate with and import from
        a Spectrum instance or set dimensionCount

        :param path: optional, path of the (binary) spectral data
        :param spectrum: associate instance with spectrum and import spectrum's parameters
        :param dimensionCount: limit instance to dimensionCount dimensions
        :param checkValid:flag to do validity check (default=False)

        """
        self._ndf5File = Ndf5File(dataSource=self)
        super().__init__(path=path, spectrum=spectrum, dimensionCount=dimensionCount, checkValid=checkValid)

    @property
    def spectrumData(self):
        return self._ndf5File.getSpectrumData()

    @property
    def spectrumParameters(self):
        dataset = self.spectrumData
        return dataset.attrs

    def _createSpectrumDataMatrix(self, sparse=False, compressionMode=None):
        """Create the ndf5 spectrum data ndarray at the location storage in the Ndf5File instance
        :param sparse: flag to set chunking to smaller (i.e. more sparse) blocks
        :param compressionMode: compression mode; defaults to None
        """
        self._ndf5File._createSpectrumData(dimensionCount=self.dimensionCount,
                                           pointCounts=self.pointCounts,
                                           dtype=self.dtype,
                                           sparse=sparse,
                                           compressionMode=compressionMode,
                                           )
        self.blockSizes = tuple(self._ndf5File.getSpectrumData().chunks[::-1])

    def hasOpenFile(self) -> bool:
        """:return True if there is an open file
        """
        return self._ndf5File.fp is not None

    def closeFile(self):
        """Close file if open.
        """
        if self.hasOpenFile():
            self._ndf5File.close()
            self.mode = None
        # call super to do any other admin, like optional closing buffer
        super().closeFile()

    def openFile(self, mode='r', overwrite:bool = False, sparse:bool = False, compressionMode = None, **kwds):
        """open self.path, set self.fp,

        :param mode: open file mode;
            from hdf5 documentation:
                r	    Readonly, file must exist (default)
                r+	    Read/write, file must exist
                w	    Create file, truncate if exists
                x	    Create file, fail if exists
                a	    Read/write if exists, create otherwise
        :param overwrite: overwrite flag (default: False).
                          NB mode=='w' and overwrite==False amounts to mode=='x'
                             mode=='x' sets overwrite==False
        :param sparse: overwrite hdf5 default chunking for sparse matrices (default: False)
        :param compressionMode: set the hdf5 compression; one of HDF5_COMPRESSION_MODES or None; (default: None)
        :param **kwds: optional keyword arguments passed to open-method for this class.

        :return self.fp

        :raises RuntimeError on opening errors

        """

        if mode is None:
            raise ValueError('%s.openFile: Undefined open mode' % self.__class__.__name__)

        if mode[0:1] == 'x':
            overwrite = False

        newFile = not mode.startswith('r')

        if self.hasOpenFile():
            self.closeFile()

        self.disableCache()  # ndf5 has its own caching

        try:
            self._checkFilePath(newFile, mode=mode, overwrite=overwrite)
            self._ndf5File.open(path=self.path, mode=mode,
                                maxCacheSize=self.maxCacheSize
                                )
            self.mode = mode

        except (FileExistsError, FileNotFoundError) as es:
            self.closeFile()
            text = '%s.openFile(mode=%r): %s' % (self.__class__.__name__, mode, str(es))
            getLogger().warning(text)
            raise RuntimeError(text)

        if not newFile:
            # old file
            self.readParameters()
        else:
            # New file;
            # create the spectrum ndarray
            self._ndf5File._createSpectrumData(dimensionCount=self.dimensionCount,
                                               pointCounts=self.pointCounts,
                                               dtype=self.dtype,
                                               sparse=sparse,
                                               compressionMode=compressionMode
                                              )
            self.writeParameters()

        # getLogger().debug2('openFile: %s; %s blocks with size %s; chunks=%s' %
        #                   (self, self._totalBlocks, self._totalBlockSize, tuple(self.blockSizes)))

        return self._ndf5File.fp

    def readParameters(self):
        """Read the parameter values from the hdf5 data structure
        :return self
        """
        def _convertValue(trait, value):
            """Convert a value,  checking for bytes and CString type
            return: optionally converted value
            """
            if value == self._NONE or value == NONE_STR:
                newValue = None
            elif isinstance(trait, (CString,)):
                newValue = trait.fromBytes(value)
            elif isinstance(trait, (CEnum,)) and isinstance(value, bytes):
                newValue = value.decode('utf8')
            else:
                newValue = value
            return newValue

        def _decode(parName, value):
            """Decode CString, CEnum traits from bytes, accounting for None values as well
            """
            if self.isDimensionalParameter(parName):
                # dimensional parameter: optionally decode the items in the list
                if not isIterable(value):
                    raise RuntimeError('Decoding Hdf5 parameters, expected iterable but got "%s"' % value)
                itemTrait = self.getItemTrait(parName)
                newValue = []
                for val in value:
                    _convertedVal = _convertValue(itemTrait, val)
                    newValue.append(_convertedVal)

            else:
                # non-dimensional parameter: optionally decode
                trait = self.getTrait(parName)
                newValue = _convertValue(trait, value)

            return newValue

        logger = getLogger()

        self.setDefaultParameters()

        try:
            if not self.hasOpenFile():
                self.openFile(mode=self.defaultOpenReadMode)

            params = self.spectrumParameters
            #pDict = [(k, _decode(k, params[k])) for k in params.keys()]

            # loop over all parameters that are defined for the Spectrum class and present in the hdf5 parameters
            for parName, values in [(p, params[p]) for p in self.keys(spectrumAttribute=lambda i: i is not None) if p in params]:
                if values is not None:
                    # if parName == 'dimensionTypes':
                    #     pass  # debug
                    values = _decode(parName, values)
                    self.setTraitValue(parName, values)

            # Get some dataset related parameters
            dataset = self.spectrumData
            self.dimensionCount = len(dataset.shape)
            self.isBigEndian = self._bigEndian
            # Get the number of points and blockSizes from the dataset
            self.pointCounts = tuple(dataset.shape[::-1])
            self.blockSizes = tuple(dataset.chunks[::-1])

        except Exception as es:
            logger.error('%s.readParameters(): %s' % (self.__class__.__name__, es))
            raise es

        return super().readParameters()

    def writeParameters(self):
        """write the parameter values into the hdf5 data structure
        :return self
        """
        logger = getLogger()

        def _encode(parName, value):
            """Encode CString traits as bytes, accounting for None values as well
            """
            if self.getMetadata(parName, 'isDimensional'):
                # dimensional parameter: optionally encode the items in the list
                if not isIterable(value):
                    raise RuntimeError('Encoding Hdf5 parameters, expected iterable but got "%s"' % value)
                itemTrait = self.getItemTrait(parName)
                newValue = []
                for val in value:
                    if val is None:
                        newValue.append(self._NONE)
                    elif itemTrait is not None and isinstance(itemTrait, CString):
                        newValue.append(itemTrait.asBytes(val))
                    else:
                        newValue.append(val)
            else:
                # non-dimensional parameter: optionally encode
                trait = self.getTrait(parName)
                if value is None:
                    newValue = self._NONE
                elif isinstance(trait, CString):
                    newValue = trait.asBytes(value)
                else:
                    newValue = value

            return newValue

        try:
            if self.hasOpenFile() and self.mode == 'r':
                # File was opened read-only; close it so it can be re-opened 'r+'
                self.closeFile()
                self.openFile(mode=self.defaultOpenReadWriteMode, check=False)

            if not self.hasOpenFile():
                raise RuntimeError('File %s is not open' % self)

        except Exception as es:
            logger.error('%s.writeParameters: %s' % (self.__class__.__name__, es))
            raise es

        try:
            params = self.spectrumParameters
            # values are stored in the hdf5 under the same attribute name as in the Spectrum class
            for parName, values in self.items(spectrumAttribute=lambda i: i is not None):
                values = _encode(parName, values)
                params[parName] = values

        except Exception as es:
            logger.error('%s.writeParameters: %s' % (self.__class__.__name__, es))
            raise es

        return self

    def _getSlices(self, position: Sequence, dims: Sequence) -> Tuple[slice]:
        """Return a tuple of slice objects (numpy-style) defined by position (one-based)
        and dims (one-based)
        slice objects are (0,pointCounts[dim]) for dims and
                   (p-1,p) for all other dims
        i.e. they can define a single slice, single plane, single cube etc depending on dims
        """
        # convert to zero-based
        dims = [d - 1 for d in dims]

        slices = [slice(p - 1, p) for p in position]
        for dim in dims:
            slices[dim] = slice(0, self.pointCounts[dim])
        return tuple(slices)

    def getPlaneData(self, position: Sequence = None, xDim: int = 1, yDim: int = 2) ->PlaneData:
        """Get plane defined by xDim, yDim and position (all 1-based)
        :return PlaneData (i.e. numpy.ndarray) object.
        """
        if self.isBuffered:
            return super().getPlaneData(position=position, xDim=xDim, yDim=yDim)

        position = self.checkForValidPlane(position=position, xDim=xDim, yDim=yDim)

        if not self.hasOpenFile():
            self.openFile(mode=self.defaultOpenReadMode)

        if xDim < yDim:
            # xDim, yDim in 'regular' order
            firstAxis = xDim - 1
            secondAxis = yDim - 1
        else:
            # xDim, yDim in 'inverted' order; first get a (yDim,xDim) plane and transpose at the end
            firstAxis = yDim - 1
            secondAxis = xDim - 1

        planeData = PlaneData(dataSource=self, dimensions=(xDim, yDim), position=position)

        dataset = self.spectrumData
        slices = self._getSlices(position=position, dims=(firstAxis + 1, secondAxis + 1))  # --> slices are x,y,z ordered
        data = dataset[slices[::-1]]  # data are z,y,x ordered
        data = data.reshape((self.pointCounts[secondAxis], self.pointCounts[firstAxis]))
        if xDim > yDim:
            data = data.transpose()
        data *= self.dataScale

        planeData[:] = data[:]
        return planeData

    def setPlaneData(self, data, position: Sequence = None, xDim: int = 1, yDim: int = 2):
        """Set data as plane defined by xDim, yDim and position (all 1-based)
        """
        if self.isBuffered:
            self.super().setPlaneData(data=data, position=position, xDim=xDim, yDim=yDim)
            return

        position = self.checkForValidPlane(position=position, xDim=xDim, yDim=yDim)

        if len(data.shape) != 2 or \
                data.shape[1] != self.pointCounts[xDim - 1] or \
                data.shape[0] != self.pointCounts[yDim - 1]:
            raise RuntimeError('setPlaneData: data for dimensions (%d,%d) has invalid shape=%r; expected (%d,%d)' %
                               (xDim, yDim, data.shape[::-1], self.pointCounts[xDim - 1], self.pointCounts[yDim - 1])
                               )

        if xDim < yDim:
            # xDim, yDim in 'regular' order
            firstAxis = xDim - 1
            secondAxis = yDim - 1
        else:
            # xDim, yDim in 'inverted' order; first transpose the data plane
            data = data.transpose()  # This creates a new object; so no need to restore the old settings later on
            firstAxis = yDim - 1
            secondAxis = xDim - 1

        if self.hasOpenFile() and self.mode == 'r':
            # File was opened read-only; close it so it can be re-opened 'r+'
            self.closeFile()
            self.openFile(mode=self.defaultOpenReadWriteMode)  # File should exist as it was created before

        if not self.hasOpenFile():
            self.openFile(mode=self.defaultAppendMode)

        dataset = self.spectrumData
        slices = self._getSlices(position=position, dims=(firstAxis + 1, secondAxis + 1))  # slices are x,y,z ordered

        # change 2D data to correct nD shape
        pointCounts = [1] * self.dimensionCount
        pointCounts[firstAxis] = self.pointCounts[firstAxis]
        pointCounts[secondAxis] = self.pointCounts[secondAxis]
        data = data.reshape(tuple(pointCounts[::-1]))  # data are z,y,x ordered, pointCounts is x,y,z ordered

        # copy the data into the dataset
        dataset[slices[::-1]] = data  # dataset and data are z,y,x ordered

    def getSliceData(self, position: Sequence = None, sliceDim: int = 1) -> SliceData:
        """Get slice defined by sliceDim and position (all 1-based)
        :return SliceData object (i.e. a numpy.ndarray) object
        """
        if self.isBuffered:
            return super().getSliceData(position=position, sliceDim=sliceDim)

        position = self.checkForValidSlice(position=position, sliceDim=sliceDim)

        if not self.hasOpenFile():
            self.openFile(mode=self.defaultOpenReadMode)

        sliceData = SliceData(dataSource=self, dimensions=(sliceDim,), position=position)

        dataset = self.spectrumData
        slices = self._getSlices(position=position, dims=(sliceDim,))
        data = dataset[slices[::-1]]  # data are z,y,x ordered
        data = data.reshape((self.pointCounts[sliceDim-1],))
        data *= self.dataScale

        sliceData[:] = data[:]
        return sliceData

    def setSliceData(self, data, position: Sequence = None, sliceDim: int = 1):
        """Set data as slice defined by sliceDim and position (all 1-based)
        """
        if self.isBuffered:
            super().setSliceData(data=data, position=position, sliceDim=sliceDim)
            return

        position = self.checkForValidSlice(position=position, sliceDim=sliceDim)

        if self.hasOpenFile() and self.mode == 'r':
            # File was opened read-only; close it so it can be re-opened 'r+'
            self.closeFile()
            self.openFile(mode=self.defaultOpenReadWriteMode)  # File should exist as it was created before

        if not self.hasOpenFile():
            self.openFile(mode=self.defaultAppendMode)

        dataset = self.spectrumData
        slices = self._getSlices(position=position, dims=(sliceDim,))
        dataset[slices[::-1]] = data  # data are z,y,x ordered

    def getPointData(self, position: Sequence = None) -> float:
        """Get value defined by position (1-based)
        """
        if self.isBuffered:
            return super().getPointData(position=position)

        position = self.checkForValidPosition(position=position)

        if not self.hasOpenFile():
            self.openFile(mode=self.defaultOpenReadMode)

        dataset = self.spectrumData
        slices = self._getSlices(position=position, dims=[])
        data = dataset[slices[::-1]].flatten() # data are z,y,x ordered
        pointValue = float(data[0]) * self.dataScale

        return pointValue

    def setPointData(self, value, position: Sequence = None):
        """Set point value defined by position (1-based)
        """
        if self.isBuffered:
            super().setPointData(value=value, position=position)
            return

        position = self.checkForValidPosition(position=position)

        if self.hasOpenFile() and self.mode == 'r':
            # File was opened read-only; close it so it can be re-opened 'r+'
            self.closeFile()
            self.openFile(mode=self.defaultOpenReadWriteMode)  # File should exist as it was created before

        if not self.hasOpenFile():
            self.openFile(mode=self.defaultAppendMode)

        dataset = self.spectrumData
        slices = self._getSlices(position=position, dims=[])
        dataset[slices[::-1]] = value # data are z,y,x ordered

    def getRegionData(self, sliceTuples, aliasingFlags=None):
        """Return an numpy array containing the points defined by
                sliceTuples=[(start_1,stop_1), (start_2,stop_2), ...],

        sliceTuples are 1-based; sliceTuple stop values are inclusive (i.e. different
        from the python slice object)

        Optionally allow for aliasing per dimension:
            0: No aliasing
            1: aliasing with identical sign
           -1: aliasing with inverted sign
        """
        if self.isBuffered:
            return super().getRegionData(sliceTuples=sliceTuples, aliasingFlags=aliasingFlags)

        if aliasingFlags is None:
            aliasingFlags = [0] * self.dimensionCount

        sliceTuples = self.checkForValidRegion(sliceTuples, aliasingFlags)

        if not self.hasOpenFile():
            self.openFile(mode=self.defaultOpenReadMode)

        withinLimits = [(sliceTuple[0] >= 1 and sliceTuple[1] <= np)
                        for sliceTuple, np in zip(sliceTuples, self.pointCounts)]
        if all(withinLimits):
            # we can use the hdf extraction
            dataset = self.spectrumData
            sizes = [(stop-start+1) for start,stop in sliceTuples]
            regionData = RegionData(shape=sizes[::-1],
                                    dataSource=self, dimensions=self.dimensions,
                                    position = [st[0] for st in sliceTuples]
                                    )
            slices = tuple(slice(start - 1, stop) for start, stop in sliceTuples)
            # data = dataset[slices[::-1]]  # data are ..,z,y,x ordered
            # data *= self.dataScale
            regionData[:] = dataset[slices[::-1]]  # data are ..,z,y,x ordered
            regionData *= self.dataScale
        else:
            # fall back on the slice-based extraction
            regionData = super()._getRegionData(sliceTuples=sliceTuples, aliasingFlags=aliasingFlags)

        return regionData

    def setRegionData(self, data, sliceTuples, aliasingFlags=None):
        """Write an numpy array data containing the points defined by
                sliceTuples=[(start_1,stop_1), (start_2,stop_2), ...],

        sliceTuples are 1-based; sliceTuple stop values are inclusive (i.e. different
        from the python slice object)

        Optionally allow for aliasing per dimension:
            0: No aliasing
            1: aliasing with identical sign
           -1: aliasing with inverted sign
        """
        _ndim = len(data.shape)
        if _ndim != self.dimensionCount:
            raise ValueError(f'Hdf5DataSource.setRegiondata(): incompatible data array (ndim={_ndim})')

        if self.isBuffered:
            return super().setRegionData(data=data, sliceTuples=sliceTuples, aliasingFlags=aliasingFlags)

        if aliasingFlags is None:
            aliasingFlags = [0] * self.dimensionCount

        sliceTuples = self.checkForValidRegion(sliceTuples, aliasingFlags)

        if not self.hasOpenFile():
            self.openFile(mode=self.defaultOpenReadWriteMode)

        withinLimits = [(sliceTuple[0] >= 1 and sliceTuple[1] <= np)
                        for sliceTuple, np in zip(sliceTuples, self.pointCounts)]
        if all(withinLimits):
            # we can use the hdf methods
            dataset = self.spectrumData
            sizes = [(stop-start+1) for start,stop in sliceTuples]
            # regionData = RegionData(shape=sizes[::-1],
            #                         dataSource=self, dimensions=self.dimensions,
            #                         position = [st[0] for st in sliceTuples]
            #                         )
            slices = tuple(slice(start - 1, stop) for start, stop in sliceTuples)
            dataset[slices[::-1]] = data[:] # data are ..,z,y,x ordered

        else:
            # Not yet implemented for now
            raise NotImplementedError(f'Hdf5DataSource.setRegiondata(): folded data not yet implemented')

# Register this format
Hdf5SpectrumDataSource._registerFormat()


# class Hdf5SpectrumDataSource(SpectrumDataSourceABC):
#     """
#     CcpNmr HDF5-based binary nD (n=1-8) spectral data format. Allows for reading and writing.
#     """
#     #=========================================================================================
#
#     dataFormat = 'Hdf5'
#     # Conveniances; subclassed in the respective classes
#     isHdf5Spectrum = True
#
#     isBlocked = False  # hdf5 format is inherently blocked, but we do not use the implemented
#     # routines in the ABC, but rather have hdf5 do the slicing
#     hasBlockCached = False  # Flag indicating if block data are cached
#
#     wordSize = 4
#     headerSize = 0
#     blockHeaderSize = 0
#     isFloatData = True
#     hasWritingAbility = True  # flag that defines if dataFormat implements writing methods
#
#     suffixes = ['.ndf5', '.hdf5']
#     openMethod = h5py.File
#     defaultOpenReadMode = 'r'   # read/write, file must exists
#     defaultOpenReadWriteMode = 'r+'
#     defaultOpenWriteMode = 'w'  # creates, truncates if exists
#     defaultAppendMode = 'a'
#
#     compressionMode = CEnum(mapping=NDF5_COMPRESSION_MODES, default_value=None)
#
#     _NONE = bytes(NONE_STR, 'utf8')
#
#     #=========================================================================================
#
#     def __init__(self, path=None, spectrum=None, dimensionCount=None, checkValid=True):
#         """initialise instance; optionally set path or associate with and import from
#         a Spectrum instance or set dimensionCount
#
#         :param path: optional, path of the (binary) spectral data
#         :param spectrum: associate instance with spectrum and import spectrum's parameters
#         :param dimensionCount: limit instance to dimensionCount dimensions
#         :param checkValid:flag to do validity check (default=False)
#
#         """
#         self._hdf5Metadata = Hdf5Metadata(dataSource=self)
#         super().__init__(path=path, spectrum=spectrum, dimensionCount=dimensionCount, checkValid=checkValid)
#
#     @property
#     def spectrumData(self):
#         if not self.hasOpenFile():
#             raise RuntimeError(f'File {self.path!r} is not open')
#         _dataKey = self._hdf5Metadata.spectrumDataKey
#         data = self.fp[_dataKey]
#         return data
#
#     @property
#     def spectrumParameters(self):
#         dataset = self.spectrumData
#         return dataset.attrs
#
#     def _createSpectrumDataMatrix(self, sparse=False, compressionMode=None):
#         """Create the NDF5 spectrum data matrix at the location storage NDF5_DATATYPE_SPECTRUM_NDARRAY
#         :param sparse: flag to set chunking to smaller (i.e. more sparse) blocks
#         :param compressionMode: compression mode; defaults to None
#         """
#         dataSetKwds = {}
#         dataSetKwds.setdefault('fillvalue', 0.0)
#
#         self.compressionMode = compressionMode
#         if self.compressionMode is not None:
#             dataSetKwds.setdefault('compression', self.compressionMode)
#             dataSetKwds.setdefault('fletcher32', False)
#         else:
#             dataSetKwds.setdefault('fletcher32', True)
#
#         if sparse:
#             # sparse data have smaller, explicitly set chunk's
#             _chunkSizes = {
#                 1 : [64],
#                 2 : [32]*2,
#                 3 : [8]*3,
#                 4 : [8]*4,
#                 5 : [4]*5,
#                 6 : [4]*6,
#                 7 : [4]*7,
#                 8 : [4]*8,
#             }
#             _chunks = tuple(_chunkSizes.get(self.dimensionCount, [4]*self.dimensionCount))
#             dataSetKwds.setdefault('chunks', _chunks)
#         else:
#             dataSetKwds.setdefault('chunks', True)
#
#         # we are storing the data as a spectrum data matrix
#         # method returns the key under which we store spectrum data matrix in the file;
#         _dataKey = self._hdf5Metadata.addDataType(NDF5_DATATYPE_SPECTRUM_NDARRAY)
#
#         self.fp.create_dataset(_dataKey,
#                                shape=self.pointCounts[::-1],  # data are organised numpy style z, y, x
#                                dtype=self._dtype,
#                                track_times=False,  # to assure same hash after opening/storing
#                                **dataSetKwds
#                                )
#         self.blockSizes = tuple(self.spectrumData.chunks[::-1])
#
#     @property
#     def _hdf5version(self) -> VersionString:
#         """:return the hdf5 version as stored in the hdf5 metadata
#         """
#         return VersionString(self._hdf5Metadata[NDF5_VERSION_KEY])
#
#     @property
#     def _hdf5CurrentDataType(self) -> str:
#         """:return the hdf5 current dataType string or None if undefined
#         """
#         return self._hdf5Metadata.get(NDF5_SPECTRUM_DATATYPE_KEY, None)
#
#     def openFile(self, mode='r', overwrite:bool = False, sparse:bool = False, compressionMode = None, **kwds):
#         """open self.path, set self.fp,
#
#         :param mode: open file mode;
#             from hdf5 documentation:
#                 r	    Readonly, file must exist (default)
#                 r+	    Read/write, file must exist
#                 w	    Create file, truncate if exists
#                 x	    Create file, fail if exists
#                 a	    Read/write if exists, create otherwise
#         :param overwrite: overwrite flag (default: False).
#                           NB mode=='w' and overwrite==False amounts to mode=='x'
#                              mode=='x' sets overwrite==False
#         :param sparse: overwrite hdf5 default chunking for sparse matrices (default: False)
#         :param compressionMode: set the hdf5 compression; one of HDF5_COMPRESSION_MODES or None; (default: None)
#         :param **kwds: optional keyword arguments passed to open-method for this class.
#
#         :return self.fp
#
#         :raises RuntimeError on opening errors
#
#         """
#
#         if mode is None:
#             raise ValueError('%s.openFile: Undefined open mode' % self.__class__.__name__)
#
#         if mode[0:1] == 'x':
#             overwrite = False
#
#         newFile = not mode.startswith('r')
#
#         if self.hasOpenFile():
#             self.closeFile()
#
#         self.disableCache()  # Hdf has its own caching
#         # Adjust hdf chunk caching parameters
#         kwds.setdefault('rdcc_nbytes', self.maxCacheSize)
#         kwds.setdefault('rdcc_nslots', 9973)  # large 'enough' prime number
#         kwds.setdefault('rdcc_w0', 0.25)  # most-often will read
#
#         try:
#             self._checkFilePath(newFile, mode=mode, overwrite=overwrite)
#             self.fp = self.openMethod(str(self.path), mode, **kwds)
#             self.mode = mode
#
#         except (FileExistsError, FileNotFoundError) as es:
#             self.closeFile()
#             text = '%s.openFile(mode=%r): %s' % (self.__class__.__name__, mode, str(es))
#             getLogger().warning(text)
#             raise RuntimeError(text)
#
#         if not newFile:
#             # old file
#             self._hdf5Metadata.restoreFromNdf5()
#             self.readParameters()
#
#         else:
#             # New file;
#             self._hdf5Metadata.initDefaultValues()
#
#             # create the spectrum ndarray
#             self._createSpectrumDataMatrix(sparse=sparse, compressionMode=compressionMode)
#             # set the spectrumDataType
#             self._hdf5Metadata.spectrumDataType = NDF5_DATATYPE_SPECTRUM_NDARRAY
#             self._hdf5Metadata.saveToNdf5()
#             self.writeParameters()
#
#         # getLogger().debug2('openFile: %s; %s blocks with size %s; chunks=%s' %
#         #                   (self, self._totalBlocks, self._totalBlockSize, tuple(self.blockSizes)))
#
#         return self.fp
#
#     def readParameters(self):
#         """Read the parameter values from the hdf5 data structure
#         :return self
#         """
#         def _convertValue(trait, value):
#             """Convert a value,  checking for bytes and CString type
#             return: optionally converted value
#             """
#             if value == self._NONE or value == NONE_STR:
#                 newValue = None
#             elif isinstance(trait, (CString,)):
#                 newValue = trait.fromBytes(value)
#             elif isinstance(trait, (CEnum,)) and isinstance(value, bytes):
#                 newValue = value.decode('utf8')
#             else:
#                 newValue = value
#             return newValue
#
#         def _decode(parName, value):
#             """Decode CString, CEnum traits from bytes, accounting for None values as well
#             """
#             if self.isDimensionalParameter(parName):
#                 # dimensional parameter: optionally decode the items in the list
#                 if not isIterable(value):
#                     raise RuntimeError('Decoding Hdf5 parameters, expected iterable but got "%s"' % value)
#                 itemTrait = self.getItemTrait(parName)
#                 newValue = []
#                 for val in value:
#                     _convertedVal = _convertValue(itemTrait, val)
#                     newValue.append(_convertedVal)
#
#             else:
#                 # non-dimensional parameter: optionally decode
#                 trait = self.getTrait(parName)
#                 newValue = _convertValue(trait, value)
#
#             return newValue
#
#         logger = getLogger()
#
#         self.setDefaultParameters()
#
#         try:
#             if not self.hasOpenFile():
#                 self.openFile(mode=self.defaultOpenReadMode)
#
#             params = self.spectrumParameters
#             #pDict = [(k, _decode(k, params[k])) for k in params.keys()]
#
#             # loop over all parameters that are defined for the Spectrum class and present in the hdf5 parameters
#             for parName, values in [(p, params[p]) for p in self.keys(spectrumAttribute=lambda i: i is not None) if p in params]:
#                 if values is not None:
#                     # if parName == 'dimensionTypes':
#                     #     pass  # debug
#                     values = _decode(parName, values)
#                     self.setTraitValue(parName, values)
#
#             # Get some dataset related parameters
#             dataset = self.spectrumData
#             self.dimensionCount = len(dataset.shape)
#             self.isBigEndian = self._bigEndian
#             # Get the number of points and blockSizes from the dataset
#             self.pointCounts = tuple(dataset.shape[::-1])
#             self.blockSizes = tuple(dataset.chunks[::-1])
#
#         except Exception as es:
#             logger.error('%s.readParameters(): %s' % (self.__class__.__name__, es))
#             raise es
#
#         return super().readParameters()
#
#     def writeParameters(self):
#         """write the parameter values into the hdf5 data structure
#         :return self
#         """
#         logger = getLogger()
#
#         def _encode(parName, value):
#             """Encode CString traits as bytes, accounting for None values as well
#             """
#             if self.getMetadata(parName, 'isDimensional'):
#                 # dimensional parameter: optionally encode the items in the list
#                 if not isIterable(value):
#                     raise RuntimeError('Encoding Hdf5 parameters, expected iterable but got "%s"' % value)
#                 itemTrait = self.getItemTrait(parName)
#                 newValue = []
#                 for val in value:
#                     if val is None:
#                         newValue.append(self._NONE)
#                     elif itemTrait is not None and isinstance(itemTrait, CString):
#                         newValue.append(itemTrait.asBytes(val))
#                     else:
#                         newValue.append(val)
#             else:
#                 # non-dimensional parameter: optionally encode
#                 trait = self.getTrait(parName)
#                 if value is None:
#                     newValue = self._NONE
#                 elif isinstance(trait, CString):
#                     newValue = trait.asBytes(value)
#                 else:
#                     newValue = value
#
#             return newValue
#
#         try:
#             if self.hasOpenFile() and self.mode == 'r':
#                 # File was opened read-only; close it so it can be re-opened 'r+'
#                 self.closeFile()
#                 self.openFile(mode=self.defaultOpenReadWriteMode, check=False)
#
#             if not self.hasOpenFile():
#                 raise RuntimeError('File %s is not open' % self)
#
#         except Exception as es:
#             logger.error('%s.writeParameters: %s' % (self.__class__.__name__, es))
#             raise es
#
#         try:
#             params = self.spectrumParameters
#             # values are stored in the hdf5 under the same attribute name as in the Spectrum class
#             for parName, values in self.items(spectrumAttribute=lambda i: i is not None):
#                 values = _encode(parName, values)
#                 params[parName] = values
#
#         except Exception as es:
#             logger.error('%s.writeParameters: %s' % (self.__class__.__name__, es))
#             raise es
#
#         return self
#
#     def _getSlices(self, position: Sequence, dims: Sequence) -> Tuple[slice]:
#         """Return a tuple of slice objects (numpy-style) defined by position (one-based)
#         and dims (one-based)
#         slice objects are (0,pointCounts[dim]) for dims and
#                    (p-1,p) for all other dims
#         i.e. they can define a single slice, single plane, single cube etc depending on dims
#         """
#         # convert to zero-based
#         dims = [d - 1 for d in dims]
#
#         slices = [slice(p - 1, p) for p in position]
#         for dim in dims:
#             slices[dim] = slice(0, self.pointCounts[dim])
#         return tuple(slices)
#
#     def getPlaneData(self, position: Sequence = None, xDim: int = 1, yDim: int = 2) ->PlaneData:
#         """Get plane defined by xDim, yDim and position (all 1-based)
#         :return PlaneData (i.e. numpy.ndarray) object.
#         """
#         if self.isBuffered:
#             return super().getPlaneData(position=position, xDim=xDim, yDim=yDim)
#
#         position = self.checkForValidPlane(position=position, xDim=xDim, yDim=yDim)
#
#         if not self.hasOpenFile():
#             self.openFile(mode=self.defaultOpenReadMode)
#
#         if xDim < yDim:
#             # xDim, yDim in 'regular' order
#             firstAxis = xDim - 1
#             secondAxis = yDim - 1
#         else:
#             # xDim, yDim in 'inverted' order; first get a (yDim,xDim) plane and transpose at the end
#             firstAxis = yDim - 1
#             secondAxis = xDim - 1
#
#         planeData = PlaneData(dataSource=self, dimensions=(xDim, yDim), position=position)
#
#         dataset = self.spectrumData
#         slices = self._getSlices(position=position, dims=(firstAxis + 1, secondAxis + 1))  # --> slices are x,y,z ordered
#         data = dataset[slices[::-1]]  # data are z,y,x ordered
#         data = data.reshape((self.pointCounts[secondAxis], self.pointCounts[firstAxis]))
#         if xDim > yDim:
#             data = data.transpose()
#         data *= self.dataScale
#
#         planeData[:] = data[:]
#         return planeData
#
#     def setPlaneData(self, data, position: Sequence = None, xDim: int = 1, yDim: int = 2):
#         """Set data as plane defined by xDim, yDim and position (all 1-based)
#         """
#         if self.isBuffered:
#             self.super().setPlaneData(data=data, position=position, xDim=xDim, yDim=yDim)
#             return
#
#         position = self.checkForValidPlane(position=position, xDim=xDim, yDim=yDim)
#
#         if len(data.shape) != 2 or \
#                 data.shape[1] != self.pointCounts[xDim - 1] or \
#                 data.shape[0] != self.pointCounts[yDim - 1]:
#             raise RuntimeError('setPlaneData: data for dimensions (%d,%d) has invalid shape=%r; expected (%d,%d)' %
#                                (xDim, yDim, data.shape[::-1], self.pointCounts[xDim - 1], self.pointCounts[yDim - 1])
#                                )
#
#         if xDim < yDim:
#             # xDim, yDim in 'regular' order
#             firstAxis = xDim - 1
#             secondAxis = yDim - 1
#         else:
#             # xDim, yDim in 'inverted' order; first transpose the data plane
#             data = data.transpose()  # This creates a new object; so no need to restore the old settings later on
#             firstAxis = yDim - 1
#             secondAxis = xDim - 1
#
#         if self.hasOpenFile() and self.mode == 'r':
#             # File was opened read-only; close it so it can be re-opened 'r+'
#             self.closeFile()
#             self.openFile(mode=self.defaultOpenReadWriteMode)  # File should exist as it was created before
#
#         if not self.hasOpenFile():
#             self.openFile(mode=self.defaultAppendMode)
#
#         dataset = self.spectrumData
#         slices = self._getSlices(position=position, dims=(firstAxis + 1, secondAxis + 1))  # slices are x,y,z ordered
#
#         # change 2D data to correct nD shape
#         pointCounts = [1] * self.dimensionCount
#         pointCounts[firstAxis] = self.pointCounts[firstAxis]
#         pointCounts[secondAxis] = self.pointCounts[secondAxis]
#         data = data.reshape(tuple(pointCounts[::-1]))  # data are z,y,x ordered, pointCounts is x,y,z ordered
#
#         # copy the data into the dataset
#         dataset[slices[::-1]] = data  # dataset and data are z,y,x ordered
#
#     def getSliceData(self, position: Sequence = None, sliceDim: int = 1) -> SliceData:
#         """Get slice defined by sliceDim and position (all 1-based)
#         :return SliceData object (i.e. a numpy.ndarray) object
#         """
#         if self.isBuffered:
#             return super().getSliceData(position=position, sliceDim=sliceDim)
#
#         position = self.checkForValidSlice(position=position, sliceDim=sliceDim)
#
#         if not self.hasOpenFile():
#             self.openFile(mode=self.defaultOpenReadMode)
#
#         sliceData = SliceData(dataSource=self, dimensions=(sliceDim,), position=position)
#
#         dataset = self.spectrumData
#         slices = self._getSlices(position=position, dims=(sliceDim,))
#         data = dataset[slices[::-1]]  # data are z,y,x ordered
#         data = data.reshape((self.pointCounts[sliceDim-1],))
#         data *= self.dataScale
#
#         sliceData[:] = data[:]
#         return sliceData
#
#     def setSliceData(self, data, position: Sequence = None, sliceDim: int = 1):
#         """Set data as slice defined by sliceDim and position (all 1-based)
#         """
#         if self.isBuffered:
#             super().setSliceData(data=data, position=position, sliceDim=sliceDim)
#             return
#
#         position = self.checkForValidSlice(position=position, sliceDim=sliceDim)
#
#         if self.hasOpenFile() and self.mode == 'r':
#             # File was opened read-only; close it so it can be re-opened 'r+'
#             self.closeFile()
#             self.openFile(mode=self.defaultOpenReadWriteMode)  # File should exist as it was created before
#
#         if not self.hasOpenFile():
#             self.openFile(mode=self.defaultAppendMode)
#
#         dataset = self.spectrumData
#         slices = self._getSlices(position=position, dims=(sliceDim,))
#         dataset[slices[::-1]] = data  # data are z,y,x ordered
#
#     def getPointData(self, position: Sequence = None) -> float:
#         """Get value defined by position (1-based)
#         """
#         if self.isBuffered:
#             return super().getPointData(position=position)
#
#         position = self.checkForValidPosition(position=position)
#
#         if not self.hasOpenFile():
#             self.openFile(mode=self.defaultOpenReadMode)
#
#         dataset = self.spectrumData
#         slices = self._getSlices(position=position, dims=[])
#         data = dataset[slices[::-1]].flatten() # data are z,y,x ordered
#         pointValue = float(data[0]) * self.dataScale
#
#         return pointValue
#
#     def setPointData(self, value, position: Sequence = None):
#         """Set point value defined by position (1-based)
#         """
#         if self.isBuffered:
#             super().setPointData(value=value, position=position)
#             return
#
#         position = self.checkForValidPosition(position=position)
#
#         if self.hasOpenFile() and self.mode == 'r':
#             # File was opened read-only; close it so it can be re-opened 'r+'
#             self.closeFile()
#             self.openFile(mode=self.defaultOpenReadWriteMode)  # File should exist as it was created before
#
#         if not self.hasOpenFile():
#             self.openFile(mode=self.defaultAppendMode)
#
#         dataset = self.spectrumData
#         slices = self._getSlices(position=position, dims=[])
#         dataset[slices[::-1]] = value # data are z,y,x ordered
#
#     def getRegionData(self, sliceTuples, aliasingFlags=None):
#         """Return an numpy array containing the points defined by
#                 sliceTuples=[(start_1,stop_1), (start_2,stop_2), ...],
#
#         sliceTuples are 1-based; sliceTuple stop values are inclusive (i.e. different
#         from the python slice object)
#
#         Optionally allow for aliasing per dimension:
#             0: No aliasing
#             1: aliasing with identical sign
#            -1: aliasing with inverted sign
#         """
#         if self.isBuffered:
#             return super().getRegionData(sliceTuples=sliceTuples, aliasingFlags=aliasingFlags)
#
#         if aliasingFlags is None:
#             aliasingFlags = [0] * self.dimensionCount
#
#         sliceTuples = self.checkForValidRegion(sliceTuples, aliasingFlags)
#
#         if not self.hasOpenFile():
#             self.openFile(mode=self.defaultOpenReadMode)
#
#         withinLimits = [(sliceTuple[0] >= 1 and sliceTuple[1] <= np)
#                         for sliceTuple, np in zip(sliceTuples, self.pointCounts)]
#         if all(withinLimits):
#             # we can use the hdf extraction
#             dataset = self.spectrumData
#             sizes = [(stop-start+1) for start,stop in sliceTuples]
#             regionData = RegionData(shape=sizes[::-1],
#                                     dataSource=self, dimensions=self.dimensions,
#                                     position = [st[0] for st in sliceTuples]
#                                     )
#             slices = tuple(slice(start - 1, stop) for start, stop in sliceTuples)
#             # data = dataset[slices[::-1]]  # data are ..,z,y,x ordered
#             # data *= self.dataScale
#             regionData[:] = dataset[slices[::-1]]  # data are ..,z,y,x ordered
#             regionData *= self.dataScale
#         else:
#             # fall back on the slice-based extraction
#             regionData = super()._getRegionData(sliceTuples=sliceTuples, aliasingFlags=aliasingFlags)
#
#         return regionData
#
#     def setRegionData(self, data, sliceTuples, aliasingFlags=None):
#         """Write an numpy array data containing the points defined by
#                 sliceTuples=[(start_1,stop_1), (start_2,stop_2), ...],
#
#         sliceTuples are 1-based; sliceTuple stop values are inclusive (i.e. different
#         from the python slice object)
#
#         Optionally allow for aliasing per dimension:
#             0: No aliasing
#             1: aliasing with identical sign
#            -1: aliasing with inverted sign
#         """
#         _ndim = len(data.shape)
#         if _ndim != self.dimensionCount:
#             raise ValueError(f'Hdf5DataSource.setRegiondata(): incompatible data array (ndim={_ndim})')
#
#         if self.isBuffered:
#             return super().setRegionData(data=data, sliceTuples=sliceTuples, aliasingFlags=aliasingFlags)
#
#         if aliasingFlags is None:
#             aliasingFlags = [0] * self.dimensionCount
#
#         sliceTuples = self.checkForValidRegion(sliceTuples, aliasingFlags)
#
#         if not self.hasOpenFile():
#             self.openFile(mode=self.defaultOpenReadWriteMode)
#
#         withinLimits = [(sliceTuple[0] >= 1 and sliceTuple[1] <= np)
#                         for sliceTuple, np in zip(sliceTuples, self.pointCounts)]
#         if all(withinLimits):
#             # we can use the hdf methods
#             dataset = self.spectrumData
#             sizes = [(stop-start+1) for start,stop in sliceTuples]
#             # regionData = RegionData(shape=sizes[::-1],
#             #                         dataSource=self, dimensions=self.dimensions,
#             #                         position = [st[0] for st in sliceTuples]
#             #                         )
#             slices = tuple(slice(start - 1, stop) for start, stop in sliceTuples)
#             dataset[slices[::-1]] = data[:] # data are ..,z,y,x ordered
#
#         else:
#             # Not yet implemented for now
#             raise NotImplementedError(f'Hdf5DataSource.setRegiondata(): folded data not yet implemented')
#
# # Register this format
# Hdf5SpectrumDataSource._registerFormat()

#
# import numpy as np
# from ccpn.util.Common import isIterable
#
# _NONE = bytes(NONE_STR, 'utf8')
# # define some tags to denote a dict, xml-style
# DICT = '<__DICT__>'
# DICT_END = '</__DICT__>'
#
# def _encode(value):
#     """Encode value for None; process and recurse into any tuple or list or dicts
#     """
#     if value is None:
#         result = NONE_STR
#
#     elif isinstance(value, dict):
#         # hdf5 attributes do not do dict's;
#         # tried numpy object_: no avail; i.e. result = np.array(value.items())
#         # tried arrays of tuples; no avail
#         # now: Encoded as a list of DICT, n-times key, val, DICT_END
#         result = [DICT]
#         for key, val in value.items():
#             result.append(key)
#             result.append(_encode(val))
#         result.append(DICT_END)
#
#     elif isinstance(value, (tuple, list)):
#         result = [_encode(val) for val in value]
#
#     else:
#         result = value
#
#     return result
#
#
# def _decode(value):
#     """Decode value for None; process and recurse into any tuple, list or dicts
#     """
#
#     # the special case dict need to be first in the checks
#     if isinstance(value, (np.ndarray,)) and len(value)>= 2 \
#             and value[0] == DICT and value[-1] == DICT_END:
#         # Encoded as a list of list of DICT, n-times key, val, DICT_END
#         result = {}
#         ii = 1
#         while ii < len(value) and value[ii] != DICT_END:
#             key = value[ii]
#             val = _decode(value[ii+1])
#             result[key] = val
#             ii += 2
#
#     elif isinstance(value, (np.ndarray,)):
#         result = [_decode(val) for val in value]
#
#     elif value == NONE_STR:
#         result = None
#
#     else:
#         result = value
#
#     return result
#
#
# # Metadata Version 1.0.1 definitions
# HDF5_DATATYPE_KEY = 'HDF5_DataType'
# HDF5_DATASET_KEY = 'HDF5_DatasetName'
# HDF5_VERSION_KEY = 'HDF5_Version'
#
# class Hdf5Metadata(dict):
#     """A class to store/manage the ndf5 metadata
#     """
#     def __init__(self, dataSource:Hdf5SpectrumDataSource):
#         super().__init__()
#         self.dataSource = dataSource
#         self.blockUpdate = 0   # blocking for when updating
#
#     @property
#     def version(self) -> VersionString:
#         """:return current version from self[NDF5_VERSION_KEY] as VersionString instance
#         """
#         return VersionString(self[NDF5_VERSION_KEY])
#
#     @property
#     def uid(self) -> str:
#         """:return current uid from self[NDF5_UID_KEY]
#         """
#         return self[NDF5_UID_KEY]
#
#     @property
#     def dataTypes(self) -> dict:
#         """:return the dict with available (dataType, ndf5-dataKey) as contained in self[NDF5_DATATYPES_KEY]
#         """
#         return self[NDF5_DATATYPES_KEY]
#
#     @property
#     def spectrumDataType(self) -> str:
#         """:return The spectrum dataType, as contained in NDF5_SPECTRUM_DATATYPE_KEY
#         """
#         return self[NDF5_SPECTRUM_DATATYPE_KEY]
#
#     @spectrumDataType.setter
#     def spectrumDataType(self, value: str):
#         """Set spectrumDataType to value
#         """
#         if value not in _ndf5DataTypes:
#             raise ValueError(f'HdfMetadata.spectrumDataType: invalid dataType {value!r}')
#         self[NDF5_SPECTRUM_DATATYPE_KEY] = value
#
#     @property
#     def spectrumDataKey(self) -> str:
#         """:return The spectrum dataKey used for retrieving the spectrum data in the ndf5 file.
#                    Retrieved from self.spectrumDataType and the self.dataTypes dict
#         """
#         return self.dataTypes[self.spectrumDataType]
#
#     def initDefaultValues(self, spectrumDataType=None):
#         """Initialise self with default values, optionally setting the spectrum dataType
#         """
#         import uuid
#
#         self.clear()
#         self.update(_defaultNdf5MetadataDict)
#         self[NDF5_UID_KEY] = str(uuid.uuid4())
#
#         if spectrumDataType:
#             self.addDataType(spectrumDataType)
#             self.spectrumDataType = spectrumDataType
#
#     def addDataType(self, dataType, dataKey=None) -> str:
#         """Add dataType to the dict of available data
#         Use dataKey or set to default value as defined in the _ndf5DataTypes dict
#         :return the dataKey
#         """
#         if dataType not in _ndf5DataTypes:
#             raise ValueError(f'HdfMetadata.addDataType: invalid dataType {dataType!r}')
#         if dataKey is None:
#             dataKey = _ndf5DataTypes[dataType]
#         self.dataTypes[dataType] = dataKey
#         return dataKey
#
#     def _reopenFile(self):
#         """Reopen the file as r+
#         :return the file pointer to the H5py file
#         """
#         self.dataSource.fp.close()
#         _mode = Hdf5SpectrumDataSource.defaultOpenReadWriteMode
#         _path = str(self.dataSource.path)
#         _fp = Hdf5SpectrumDataSource.openMethod(_path, mode=_mode)
#         self.dataSource.fp = _fp
#         return _fp
#
#     def _updateVersion100(self):
#         """Update pre 1.0.1 version to 1.1.0
#         """
#         # pre 1.0.1 version;
#         _oldDataKey = 'spectrumData' # This is historic from the first implementation
#
#         _params = self.dataSource.fp[_oldDataKey].attrs
#         if not 'version' in _params:
#             raise RuntimeError('Hdf5Metadata._updateVersion100(): non-versioned metadata instance')
#
#         _version = VersionString('1.0.0')  # it was a float in this implementation
#         del _params['version']
#
#         # we can now set the 1.1.0 ndf5 version
#         self.initDefaultValues()
#         self[NDF5_VERSION_KEY] = '1.1.0'
#         self[NDF5_DATE_KEY] = self.dataSource.date
#         self[NDF5_USER_KEY] = self.dataSource.user
#
#         self.addDataType(NDF5_DATATYPE_SPECTRUM_NDARRAY, _oldDataKey)
#         self.spectrumDataType = NDF5_DATATYPE_SPECTRUM_NDARRAY
#
#         # We are now upto version 1.1.0, as defined above
#         _version = self.version
#         return _version
#
#     def _updateVersion101(self):
#         """Update 1.0.1 version to 1.1.0
#         """
#         # 1.0.1 -> 1.1.0
#         _version = VersionString(self[HDF5_VERSION_KEY])
#         if not _version == '1.0.1':
#             RuntimeError(f'Hdf5Metadata._updateVeersion101(): unknown version {_version}')
#
#         # remap
#         _oldDataKey = self[HDF5_DATASET_KEY]
#
#         self.initDefaultValues()
#         self[NDF5_VERSION_KEY] = '1.1.0'
#         self[NDF5_DATE_KEY] = self.dataSource.date
#         self[NDF5_USER_KEY] = self.dataSource.user
#
#         # # This works, but don't for now
#         # # reopen the file as we are going to write the update info
#         # _fp = self._reopenFile()
#         # # the spectrum data; move to new location
#         # _fp.create_group(NDF5_SPECTRUM)
#         # _newDataKey = self.addDataType(NDF5_DATATYPE_SPECTRUM_NDARRAY)
#         # _fp.move(_oldDataKey, _newDataKey)
#         # self.spectrumDataType = NDF5_DATATYPE_SPECTRUM_NDARRAY
#         # self.saveToNdf5()
#
#         # instead, just leave it were it is for backward compatibility
#         self.addDataType(NDF5_DATATYPE_SPECTRUM_NDARRAY, _oldDataKey)
#         self.spectrumDataType = NDF5_DATATYPE_SPECTRUM_NDARRAY
#
#         # We are now upto version 1.1.0, as defined above
#         _version = self.version
#         return _version
#
#     def _updateMetadata(self):
#         """Update the self to the latest version
#         """
#         if self.blockUpdate > 0:
#             return
#
#         self.blockUpdate += 1
#         _version = None
#
#         if not self.dataSource.hasOpenFile():
#             raise RuntimeError(f'HdfMetadata._updateMetadata(): File is closed')
#
#         if NDF5_VERSION_KEY in self:
#             # we are already at 1.1.0 or higher
#             _version = self.version
#
#         elif not HDF5_VERSION_KEY in self and not NDF5_VERSION_KEY in self:
#             # # pre 1.0.1 version;
#             _version = self._updateVersion100()
#
#         elif HDF5_VERSION_KEY in self and not NDF5_VERSION_KEY in self:
#             # 1.0.1 -> 1.1.0
#             _version = self._updateVersion101()
#
#         else:
#             raise RuntimeError('Hdf5Metadata._updateMetadata(): non-versioned instance')
#
#         # # Next update would go here
#         # if _version == '1.1.0':
#         #     pass
#
#         if _version != NDF5_VERSION:
#             raise RuntimeError(f'Hdf5Metadata._updateMetadata(): updating failed; stuck at version {_version}')
#
#         self.blockUpdate -= 1
#
#     def restoreFromNdf5(self):
#         """Update self from the ndf5 file toplevel attributes
#         """
#         if not self.dataSource.hasOpenFile():
#             raise RuntimeError(f'HdfMetadata.restoreFromNdf5(): File is closed')
#
#         _metadata = self.dataSource.fp.attrs
#         self.clear()
#
#         # the _metadata object is unfortunately not a real dict;
#         # Decode it from the earlier encoding
#         for key, value in _metadata.items():
#             self[key] = _decode(value)
#         self._updateMetadata()
#
#     def saveToNdf5(self):
#         """Update the ndf5 file toplevel attributes with self
#         """
#         if not self.dataSource.hasOpenFile():
#             raise RuntimeError(f'HdfMetadata.saveToNdf5(): File is closed')
#
#         # the _metadata object is unfortunately not a real dict
#         _metadata = self.dataSource.fp.attrs
#
#         # fist delete current values in the hdf5 file
#         for key in list(_metadata):
#             del _metadata[key]
#
#         _items = list(self.items())
#         # # for backward compatibility, add the old 1.0.1 definition;
#         # _items.append( (HDF5_DATASET_KEY, self.spectrumDataKey) )
#
#         for key, value in _items:
#             # now copy the values from self
#             try:
#                _metadata[key] = _encode(value)
#             except Exception as es:
#                 _txt = f'HdfMetadata.saveToNdf5(): error saving {key = } {value = }; {es}'
#                 getLogger().error(_txt)
#                 raise RuntimeError(_txt)
