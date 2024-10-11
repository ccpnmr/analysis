"""
This file contains the ndf5-file data access code
it serves as an interface between the V3 Spectrum class and the actual ndf5 data format
The ndf5 format has writing capabilities

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
__dateModified__ = "$dateModified: 2024-10-11 10:37:01 +0100 (Fri, October 11, 2024) $"
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

from ccpn.util.Logging import getLogger
from ccpn.util.Common import isIterable
from ccpn.util.traits.CcpNmrTraits import CString, TList, CEnum
from ccpn.framework.Version import VersionString

from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import SpectrumDataSourceABC
from ccpn.core._implementation.SpectrumData import SliceData, PlaneData, RegionData

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

            dataset = self._ndf5File.getSpectrumData()
            params = dataset.attrs
            #pDict = [(k, _decode(k, params[k])) for k in params.keys()]

            # loop over all parameters that are defined for the Spectrum class and present in the hdf5 parameters
            for parName, values in [(p, params[p]) for p in self.keys(spectrumAttribute=lambda i: i is not None) if p in params]:
                if values is not None:
                    # if parName == 'dimensionTypes':
                    #     pass  # debug
                    values = _decode(parName, values)
                    self.setTraitValue(parName, values)

            # Get some dataset related parameters
            dataset = self._ndf5File.getSpectrumData()
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
            dataset = self._ndf5File.getSpectrumData()
            params = dataset.attrs
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

        dataset = self._ndf5File.getSpectrumData()
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

        dataset = self._ndf5File.getSpectrumData()
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

        dataset = self._ndf5File.getSpectrumData()
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

        dataset = self._ndf5File.getSpectrumData()
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

        dataset = self._ndf5File.getSpectrumData()
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

        dataset = self._ndf5File.getSpectrumData()
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
            dataset = self._ndf5File.getSpectrumData()
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
            dataset = self._ndf5File.getSpectrumData()
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

