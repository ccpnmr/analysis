"""
This file contains the HDF5 data access stuff
it serves as an interface between the V3 Spectrum class and the actual Hdf5 data formats
The Hdf5 format has writing capabilities

Version history:
No-version:     Luca's initial implementation
1.0 (float):    Version info (float) stored as 'version' in parameters;
                spectralWidth definition updated (if need be)
1.0.1 (string): hdf5 metadata; stored in attributes top object (i.e. self.fp)

See SpectrumDataSourceABC for a description of the methods
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2022-02-06 18:36:44 +0000 (Sun, February 06, 2022) $"
__version__ = "$Revision: 3.0.4 $"
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
from ccpn.util.traits.CcpNmrTraits import CString
from ccpn.framework.Version import VersionString

from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import SpectrumDataSourceABC
from ccpn.core._implementation.SpectrumData import SliceData, PlaneData, RegionData


HDF5_VERSION_KEY = 'HDF5_Version'
HDF5_TYPE_KEY = 'HDF5_DataType'
HDF5_DATASET_KEY = 'HDF5_DatasetName'
HDF5_KEYS = (HDF5_VERSION_KEY, HDF5_TYPE_KEY, HDF5_DATASET_KEY)

NONE_STR = '__NONE__'


class String(bytes):
    "Bytes representation of string"

    def __init__(self, value):
        super().__init__(value, encoding='utf8')

    def decode(self):
        return super().decode(encoding='utf8')

    def __str__(self):
        return str(self.decode())


class Hdf5SpectrumDataSource(SpectrumDataSourceABC):
    """
    HDF5 spectral storage
    """
    #=========================================================================================

    dataFormat = 'Hdf5'

    isBlocked = False  # hdf5 format is inherently blocked, but we do not use the implemented
    # routines in the ABC, but rather have hdf5 do the slicing
    hasBlockCached = False  # Flag indicating if block data are cached

    wordSize = 4
    headerSize = 0
    blockHeaderSize = 0
    isFloatData = True
    hasWritingAbility = True  # flag that defines if dataFormat implements writing methods

    suffixes = ['.ndf5', '.hdf5']
    openMethod = h5py.File
    defaultOpenReadMode = 'r+'   # read/write, file must exists
    defaultOpenReadWriteMode = 'r+'
    defaultOpenWriteMode = 'w'  # creates, truncates if exists
    defaultAppendMode = 'a'

    _HDF5version = VersionString('1.0.1')  # Curren HDF5 implementation version
    _HDF5dataType = 'SpectrumData'
    _HDF5dataSetName = 'spectrumData'

    # lzf compression seems not to yield any improvement, but rather a increase in file size;
    # gzip compression about 30% reductions, albeit at a great cost-penalty
    compressionModes = ('lzf', 'gzip')  # 'szip' not in conda distribution
    defaultCompressionMode = None  # hdf5 compression modes

    _NONE = bytes(NONE_STR, 'utf8')

    #=========================================================================================

    @property
    def spectrumData(self):
        if not self.hasOpenFile():
            raise RuntimeError('File "%s" is not open' % self.path)
        data = self.fp[self._HDF5dataSetName]
        return data

    @property
    def spectrumParameters(self):
        dataset = self.spectrumData
        return dataset.attrs

    def _setHdf5Metadata(self):
        """Set the hdf5 metadata attr field to their default values.
        """
        if not self.hasOpenFile():
            getLogger().debug('File not open: hdf5 metadata setting skipped')
            return
        _metadata = self.fp.attrs
        _metadata.clear()
        _metadata[HDF5_TYPE_KEY] = self._HDF5dataType
        _metadata[HDF5_DATASET_KEY] = self._HDF5dataSetName
        _metadata[HDF5_VERSION_KEY] = str(self._HDF5version)

    def _checkHdf5Metadata(self):
        """Check the file metadata for versioning, updates etc
        """
        if not self.hasOpenFile():
            getLogger().debug('File not open: hdf5 metadata check and update skipped')
            return
        try:
            _metadata = self.fp.attrs
            _params = self.spectrumParameters
        except:
            getLogger().debug('Error finding params and hdf5 metadata: check and update skipped')
            return

        if HDF5_VERSION_KEY in _metadata:
            pass  # latest implementation

        elif 'version' in _params:
            del _params['version']
            self._setHdf5Metadata()

        elif HDF5_VERSION_KEY not in self.fp.attrs and 'version' not in _params:
            # Earlier (Luca) hdf5 files, in which spectralWidth (sometimes)
            # denoted the width in Hz
            if 'spectralWidths' in _params:
                sw = _params['spectralWidths']
                _params['spectralWidthsHz'] = sw
                del (_params['spectralWidths'])
            self._setHdf5Metadata()

        else:
            # This should not happen
            getLogger().warning('Undetermined hdf5 version; skipping checks/upgrades')

        # we are now up-to-date to the current hdf5 version
        _metadata[HDF5_VERSION_KEY] = str(self._HDF5version)

    @property
    def _hdf5metadata(self) -> dict:
        """:return the hdf5 metadata as a dict or None if file is not open
        """
        if not self.hasOpenFile():
            getLogger().debug('File not open: hdf5metadata dict is None')
            return None
        _metadata = self.fp.attrs
        return dict((key, _metadata[key]) for key in HDF5_KEYS)

    @property
    def _hdf5version(self)-> VersionString:
        """:return the hdf5 version as stored in the hdf5 metadata
        """
        return VersionString(self._hdf5metadata[HDF5_VERSION_KEY])

    def openFile(self, mode, **kwds):
        """open self.path, set self.fp, return self.fp

        :param mode: open file mode;
                    from hdf5 documentation:
                        r	Readonly, file must exist (default)
                        r+	Read/write, file must exist
                        w	Create file, truncate if exists
                        w- or x	Create file, fail if exists
                        a	Read/write if exists, create otherwise
        :return self.fp
        """

        if mode is None:
            raise ValueError('%s.openFile: Undefined open mode' % self.__class__.__name__)
        newFile = mode.startswith('w')

        if self.hasOpenFile():
            self.closeFile()

        self._checkFilePath(newFile, mode)

        try:
            self.disableCache()  # Hdf has its own caching
            # Adjust hdf chunk caching parameters
            kwds.setdefault('rdcc_nbytes', self.maxCacheSize)
            kwds.setdefault('rdcc_nslots', 9973)  # large 'enough' prime number
            kwds.setdefault('rdcc_w0', 0.25)  # most-often will read

            self.fp = self.openMethod(str(self.path), mode, **kwds)
            self.mode = mode

        except Exception as es:
            self.closeFile()
            text = '%s.openFile(mode=%r): %s' % (self.__class__.__name__, mode, str(es))
            getLogger().warning(text)
            raise es

        if not newFile:
            # old file
            self._checkHdf5Metadata()
            self.readParameters()

        else:
            # New file
            self._setHdf5Metadata()

            # create the spectrum dataset
            dataSetKwds = {}
            dataSetKwds.setdefault('fletcher32', True)
            dataSetKwds.setdefault('fillvalue', 0.0)
            if self.defaultCompressionMode is not None and self.defaultCompressionMode in self.compressionModes:
                dataSetKwds.setdefault('compression', self.defaultCompressionMode)
                dataSetKwds.setdefault('fletcher32', False)

            self.fp.create_dataset(self._HDF5dataSetName,
                                   self.pointCounts[::-1],  # data are organised numpy style z, y, x
                                   dtype=self.dataType,
                                   chunks=True,
                                   track_times=False,  # to assure same hash after opening/storing
                                   **dataSetKwds)
            self.blockSizes = tuple(self.spectrumData.chunks[::-1])

            self.writeParameters()

        getLogger().debug2('openFile: %s; %s blocks with size %s; chunks=%s' %
                          (self, self._totalBlocks, self._totalBlockSize, tuple(self.blockSizes)))

        return self.fp

    # def closeFile(self):
    #     """Close the File"""
    #     if self.hasOpenFile():
    #         self.fp.attrs.clear()
    #         self.fp.attrs.update(self.metadata)
    #     super().closeFile()

    def readParameters(self):
        """Read the parameter values from the hdf5 data structure
        :return self
        """
        def _convertValue(trait, value):
            """Convert a value,  checking for bytes and CString type
            return: converted value
            """
            if value == self._NONE or value == NONE_STR:
                newValue = None
            elif isinstance(trait, CString):
                newValue = trait.fromBytes(value)
            else:
                newValue = value
            return newValue

        def _decode(parName, value):
            """Encode CString traits as bytes, accouting for None values as well
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

            # if VERSION in params:
            #     self.version = params[VERSION]
            # else:
            #     # To discriminate from earlier files, in which spectralWidth (sometimes) denoted the width in Hz
            #     self.version = 0.0
            #     if 'spectralWidths' in params:
            #         sw = params['spectralWidths']
            #         params['spectralWidthsHz'] = sw
            #         del (params['spectralWidths'])

            # loop over all parameters that are defined for the Spectrum class and present in the hdf5 parameters
            for parName, values in [(p, params[p]) for p in self.keys(spectrumAttribute=lambda i: i is not None) if p in params]:
                if values is not None:
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
            logger.error('%s.readParameters: %s' % (self.__class__.__name__, es))
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
                self.openFile(mode=self.defaultOpenReadWriteMode)

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

    def setPointData(self, value, position: Sequence = None) -> float:
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


# Register this format
Hdf5SpectrumDataSource._registerFormat()
