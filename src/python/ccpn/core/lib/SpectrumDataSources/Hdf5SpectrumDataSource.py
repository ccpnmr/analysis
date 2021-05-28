"""
This file contains the HDF5 data access stuff
it serves as an interface between the V3 Spectrum class and the actual Hdf5 data formats
The Hdf5 format has writing capabilities

See SpectrumDataSourceABC for a description of the methods
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:33:14 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2020-11-20 10:28:48 +0000 (Fri, November 20, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Sequence
import h5py

from ccpn.util.Logging import getLogger
from ccpn.util.Common import isIterable
from ccpn.util.traits.CcpNmrTraits import CString

from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import SpectrumDataSourceABC

SPECTRUM_DATASET_NAME = 'spectrumData'
VERSION = 'version'


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

    suffixes = ['.hdf5']
    openMethod = h5py.File
    defaultOpenReadMode = 'r+'
    defaultOpenWriteMode = 'w'

    HDF_VERSION = 1.0

    # lzf compression seems not to yield any improvement, but rather a increase in file size;
    # gzip compression about 30% reductions, albeit at a great cost-penalty
    compressionModes = ('lzf', 'gzip')  # 'szip' not in conda distribution
    defaultCompressionMode = None  # hdf5 compression modes

    _NONE = bytes('__NONE__','utf8')

    #=========================================================================================

    @property
    def spectrumData(self):
        if not self.hasOpenFile():
            raise RuntimeError('File "%s" is not open' % self.path)
        data = self.fp[SPECTRUM_DATASET_NAME]
        return data

    @property
    def spectrumParameters(self):
        dataset = self.spectrumData
        return dataset.attrs

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

            self.disableCache()  # Hdf has its own caching
            # Adjust hdf chunck caching parameters
            kwds.setdefault('rdcc_nbytes', self.maxCacheSize)
            kwds.setdefault('rdcc_nslots', 9973)  # large 'enough' prime number
            kwds.setdefault('rdcc_w0', 0.25)  # most-often will read

            self.fp = self.openMethod(str(self.path), mode, **kwds)
            self.mode = mode

        except Exception as es:
            self.closeFile()
            text = '%s.openFile(mode=%r): %s' % (self.__class__.__name__, mode, str(es))
            getLogger().error(text)
            raise es

        if mode.startswith('r'):
            self.readParameters()

        else:
            dataSetKwds = {}
            dataSetKwds.setdefault('fletcher32', True)
            dataSetKwds.setdefault('fillvalue', 0.0)
            if self.defaultCompressionMode is not None and self.defaultCompressionMode in self.compressionModes:
                dataSetKwds.setdefault('compression', self.defaultCompressionMode)
                dataSetKwds.setdefault('fletcher32', False)

            self.fp.create_dataset(SPECTRUM_DATASET_NAME, self.pointCounts[::-1],
                                   dtype=self.dataType, chunks=True,
                                   track_times=False,  # to assure same hash after opening/storing
                                   **dataSetKwds)
            self.blockSizes = tuple(self.spectrumData.chunks[::-1])
            self.writeParameters()

        getLogger().debug('opened %s; %s blocks with size %s; chunks=%s' %
                          (self, self._totalBlocks, self._totalBlockSize, tuple(self.blockSizes)))

        return self.fp

    def readParameters(self):
        """Read the parameters from the hdf5 data structure
        Returns self
        """

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
                    if val == self._NONE:
                        newValue.append(None)
                    elif itemTrait is not None and isinstance(itemTrait, CString):
                        newValue.append(itemTrait.fromBytes(val))
                    else:
                        newValue.append(val)
            else:
                # non-dimensional parameter: optionally decode
                trait = self.getTrait(parName)
                if value == self._NONE:
                    newValue = None
                elif isinstance(trait, CString):
                    newValue = trait.fromBytes(value)
                else:
                    newValue = value

            return newValue

        logger = getLogger()

        self.setDefaultParameters()

        try:
            if not self.hasOpenFile():
                self.openFile(mode=self.defaultOpenReadMode)

            params = self.spectrumParameters
            #pDict = [(k, _decode(k, params[k])) for k in params.keys()]

            if VERSION in params:
                self.version = params[VERSION]
            else:
                # To discriminate from earlier files, in which spectralWidth (sometimes) denoted the width in Hz
                self.version = 0.0
                if 'spectralWidths' in params:
                    sw = params['spectralWidths']
                    params['spectralWidthsHz'] = sw
                    del(params['spectralWidths'])

            # loop over all parameters that are defined for the Spectrum class and present in the hdf5 parameters
            for parName, values in [(p, params[p]) for p in self.keys(spectrumAttribute = lambda i: i is not None) if p in params]:
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
        """write the parameters into the hdf5 data structure
        Returns self
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
            if not self.hasOpenFile():
                self.openFile(mode=self.defaultOpenWriteMode)

            params = self.spectrumParameters
            params[VERSION] = self.HDF_VERSION

            # values are stored in the hdf5 under the same attribute name as in the Spectrum class
            for parName, values in self.items(spectrumAttribute = lambda i: i is not None):
                values = _encode(parName, values)
                params[parName] = values

        except Exception as es:
            logger.error('%s.writeParameters: %s' % (self.__class__.__name__, es))
            raise es

        return self

    def _getSlices(self, position:Sequence, dims:Sequence):
        """Return a slices tuple defined by position (one-based) and dims (one-based)
        slices are (0,pointCounts[dim]) for dims and
                   (p-1,p) for all other dims
        i.e. they can define a single slice, single plane, single cube etc depending on dims
        """
        # convert to zero-based
        dims = [d-1 for d in dims]

        slices = [slice(p-1, p) for p in position]
        for dim in dims:
            slices[dim] = slice(0, self.pointCounts[dim])
        return tuple(slices)

    def getPlaneData(self, position:Sequence=None, xDim:int=1, yDim:int=2):
        """Get plane defined by xDim, yDim and position (all 1-based)
        return NumPy data array
        """
        position = self.checkForValidPlane(position=position, xDim=xDim, yDim=yDim)

        if not self.hasOpenFile():
            self.openFile(mode=self.defaultOpenReadMode)

        if xDim < yDim:
            # xDim, yDim in 'regular' order
            firstAxis = xDim-1
            secondAxis = yDim-1
        else:
            # xDim, yDim in 'inverted' order; first get a (yDim,xDim) plane and transpose at the end
            firstAxis = yDim-1
            secondAxis = xDim-1

        dataset = self.spectrumData
        slices = self._getSlices(position=position, dims=(firstAxis+1, secondAxis+1))  # --> slices are x,y,z ordered
        data = dataset[slices[::-1]]  # data are z,y,x ordered
        data = data.reshape((self.pointCounts[secondAxis], self.pointCounts[firstAxis]))
        if xDim > yDim:
            data = data.transpose()
        data *= self.dataScale

        return data

    def setPlaneData(self, data, position:Sequence=None, xDim:int=1, yDim:int=2):
        """Set data as plane defined by xDim, yDim and position (all 1-based)
        """
        position = self.checkForValidPlane(position=position, xDim=xDim, yDim=yDim)

        if len(data.shape) != 2 or \
           data.shape[1] != self.pointCounts[xDim-1] or \
           data.shape[0] != self.pointCounts[yDim-1]:
            raise RuntimeError('setPlaneData: data for dimensions (%d,%d) has invalid shape=%r; expected (%d,%d)' %
                               (xDim, yDim, data.shape[::-1], self.pointCounts[xDim-1], self.pointCounts[yDim-1])
                              )

        if xDim < yDim:
            # xDim, yDim in 'regular' order
            firstAxis = xDim-1
            secondAxis = yDim-1
        else:
             # xDim, yDim in 'inverted' order; first transpose the data plane
            data = data.transpose()  # This creates a new object; so no need to restore the old settings later on
            firstAxis = yDim-1
            secondAxis = xDim-1

        if not self.hasOpenFile():
            self.openFile(mode=self.defaultOpenWriteMode)

        dataset = self.spectrumData
        slices = self._getSlices(position=position, dims=(firstAxis+1, secondAxis+1)) # slices are x,y,z ordered

        # change data to correct nD shape
        pointCounts = [1]*self.dimensionCount
        pointCounts[firstAxis] = self.pointCounts[firstAxis]
        pointCounts[secondAxis] = self.pointCounts[secondAxis]
        data = data.reshape( tuple(pointCounts[::-1]) )  # data are z,y,x ordered, pointCounts is x,y,z ordered

        # copy the data into the dataset
        dataset[slices[::-1]] = data # dataset and data are z,y,x ordered

    def getSliceData(self, position:Sequence=None, sliceDim:int=1):
        """Get slice defined by sliceDim and position (all 1-based)
        return NumPy data array
        """
        position = self.checkForValidSlice(position=position, sliceDim=sliceDim)

        if not self.hasOpenFile():
            self.openFile(mode=self.defaultOpenReadMode)

        dataset = self.spectrumData
        slices = self._getSlices(position=position, dims=(sliceDim,))
        data = dataset[slices[::-1]]  # data are z,y,x ordered
        data = data.reshape((self.pointCounts[sliceDim-1],))
        data *= self.dataScale

        return data

    def setSliceData(self, data, position:Sequence=None, sliceDim:int=1):
        """Set data as slice defined by sliceDim and position (all 1-based)
        """
        position = self.checkForValidSlice(position=position, sliceDim=sliceDim)

        if not self.hasOpenFile():
            self.openFile(mode=self.defaultOpenWriteMode)

        dataset = self.spectrumData
        slices = self._getSlices(position=position, dims=(sliceDim,))
        dataset[slices[::-1]] = data # data are z,y,x ordered

    def getPointData(self, position:Sequence=None) -> float:
        """Get value defined by position (1-based)
        """
        position = self.checkForValidPosition(position=position)

        if not self.hasOpenFile():
            self.openFile(mode=self.defaultOpenReadMode)

        dataset = self.spectrumData
        slices = self._getSlices(position=position, dims=[])
        data = dataset[slices[::-1]].flatten() # data are z,y,x ordered
        pointValue = float(data[0]) * self.dataScale

        return pointValue

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
        if aliasingFlags is None:
            aliasingFlags = [0] * self.dimensionCount

        self.checkForValidRegion(sliceTuples, aliasingFlags)

        if not self.hasOpenFile():
            self.openFile(mode=self.defaultOpenReadMode)

        if 1 in aliasingFlags or -1 in aliasingFlags:
            # fall back on the slice-based extraction
            data = super()._getRegionData(sliceTuples=sliceTuples, aliasingFlags=aliasingFlags)
        else:
            dataset = self.spectrumData
            slices = tuple(slice(start-1, stop) for start,stop in sliceTuples)
            data = dataset[slices[::-1]]  # data are ..,z,y,x ordered
            data *= self.dataScale

        return data

# Register this format
Hdf5SpectrumDataSource._registerFormat()

