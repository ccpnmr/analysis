"""
This file contains the ABC and specfic classes for the numpy.ndarray-based data objects
"""
from __future__ import annotations

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2023-01-10 14:30:44 +0000 (Tue, January 10, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2022-01-14 10:28:48 +0000 (Fri, January 14, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
from typing import Sequence

import ccpn.core.lib.SpectrumLib as specLib
from ccpn.util.Common import isIterable


class SpectrumDataABC(np.ndarray):

    spectrumDataType = None
    spectrumDataLen = None

    _dtype = 'float32'  # numpy data format of the resulting slice, plane, region data

    # Attributes maintained in addition to dimensionCount (ndim), pointCounts (shape)
    _attributes = '_dataSource _position, _dimensions _dataTypes'.split()

    # from https://numpy.org/doc/stable/user/basics.subclassing.html
    def __new__(subtype, shape=None, dtype=None, buffer=None, offset=0,
                strides=None, order=None,
                dataSource=None, dimensions=(), position=None, dataTypes=None
                ):
        # Create the ndarray instance of our type, given the usual
        # ndarray input arguments.
        # GWV added the dataSource, dimensions, position and dataTypes arguments.
        # This will call the standard ndarray constructor, but return an object of our type.
        # It also triggers a call to SpectrumDataABC.__array_finalize__

        # local import to avoid cycles
        from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import SpectrumDataSourceABC

        if dataSource is not None and not isinstance(dataSource, SpectrumDataSourceABC):
            raise ValueError(f'Invalid dataSource; got {dataSource}')

        if dimensions is None or not isIterable(dimensions):
            raise ValueError(f'Invalid dimensions; expected list/tuple, got {dimensions}')
        dimensions = tuple(dimensions)
        maxDimLen =  subtype.spectrumDataLen if subtype.spectrumDataLen is not None else \
                     dataSource.dimensionCount
        if len(dimensions) == 0 or len(dimensions) > maxDimLen:
            raise ValueError(f'Invalid length dimensions; expected at most {maxDimLen}, got {dimensions}')

        if shape is None:
            pointCounts = dataSource.getByDimensions('pointCounts', dimensions=dimensions)
            shape = pointCounts[::-1]

        if dtype is None:
            dtype = subtype._dtype

        if position is None:
            position = [1]*dataSource.dimensionCount

        obj = super().__new__(subtype, shape=shape, dtype=dtype,
                              buffer=buffer, offset=offset, strides=strides, order=order)
        obj.fill(0.0)

        # set the new attributes to the value passed
        obj._dataSource = dataSource
        obj._dimensions = tuple(dimensions)
        obj._position = position

        if dataTypes is not None:
            obj._dataTypes = dataTypes
        elif dataTypes is None and dataSource is not None:
            obj._dataTypes  = [dataSource.dataTypes[dimIdx] for dimIdx in obj.dimensionIndices]
        else:
            obj._dataTypes = [specLib.DATA_TYPE_REAL]*obj.ndim

        # Finally, we must return the newly created object:
        return obj

    def __array_finalize__(self, obj):
        # ``self`` is a new object resulting from
        # ndarray.__new__(SpectrumDataABC, ...), therefore it only has
        # attributes that the ndarray.__new__ constructor gave it -
        # i.e. those of a standard ndarray.
        #
        # We could have got to the ndarray.__new__ call in 3 ways:
        # From an explicit constructor - e.g. SpectrumDataABC():
        #    obj is None
        #    (we're in the middle of the SpectrumDataABC.__new__
        #    constructor, and self.info will be set when we return to
        #    SpectrumDataABC.__new__)
        if obj is None: return

        # From view casting - e.g arr.view(SpectrumDataABC):
        #    obj is arr
        #    (type(obj) can be SpectrumDataABC)
        # From new-from-template - e.g specdata[:3]
        #    type(obj) is SpectrumDataABC
        #
        # Note that it is here, rather than in the __new__ method,
        # that we set the default value for attributes, because this
        # method sees all creation of default objects - with the
        # SpectrumDataABC.__new__ constructor, but also with arr.view(SpectrumDataABC).

        # GWV: This appears not to work??
        # for attr in self._attributes:
        #     val = getattr(obj, attr, None)
        #     setattr(self, attr, val)

        # Whereas this explicit setting does
        self._dataSource = getattr(obj, '_dataSource', None)
        self._dimensions = getattr(obj, '_dimensions', None)
        self._position = getattr(obj, '_position', None)
        self._dataTypes = getattr(obj, '_dataTypes', None)

        # We do not need to return anything
        return

    @property
    def dataSource(self):
        """:return: the originating dataSource object (or None if not defined)
        """
        return self._dataSource

    @property
    def dimensions(self) -> list:
        """The dimensions (1-based) for self in the originating dataSource object
        :return a list of dimensions or [] if not defined
        """
        dims = self._dimensions if self._dimensions is not None else []
        return dims

    @property
    def dimensionIndices(self) -> list:
        """The dimension indices (0-based) for self in the originating dataSource object
        :return a list of dimension indices or [] if not defined
        """
        return [dim-1 for dim in self._dimensions]

    @property
    def dimensionCount(self) -> int:
        """:return number of dimensions of self (i.e. the numpy.ndarray ndim parameter)
        """
        return self.ndim

    @property
    def dimensionsString(self) -> str:
        """Conveniance
        :return a string representation of the dimensions; e.g "XY", "ZXY"
        """
        dimNames = specLib.dimensionNames
        dims = [dimNames[dim][0] for dim in self.dimensions]
        dimStr = ''.join(dims)
        return dimStr.upper()

    @property
    def pointCounts(self) -> tuple:
        """The total number of points of self (i.e. shape).
        This corresponds to the pointCounts of the dataSource object in self.dimension's order
        :return a tuple of the total number of points
        """
        return tuple(list(self.shape)[::-1])

    @property
    def dataTypes(self) -> tuple:
        """The dataTypes of self along the succesive dimensions of self.
        This corresponds to the dataTypes of the dataSource object in self.dimension's order
        :return a tuple of the dataTypes
        """
        if self._dataTypes is None:
            return tuple([specLib.DATA_TYPE_REAL]*self.ndim)
        else:
            return tuple(self._dataTypes)

    @property
    def isComplex(self) -> tuple:
        """Conveniance: A flag indicating a complex dataType along the succesive dimensions of self.
        :return a tuple of isComplex flags
        """
        result  = [(dt != specLib.DATA_TYPE_REAL) for dt in self.dataTypes]
        return tuple(result)

    @property
    def realPointCounts(self) -> tuple:
        """Conveniance: return a tuple with the real number of points along the succesive dimensions of self.
        :return a tuple of real points values
        """
        result = [(np//2 if isC else np) for np, isC in zip(self.pointCounts, self.isComplex)]
        return tuple(result)

    @property
    def position(self) -> (tuple, None):
        """:return: the position (1-based) where the slice was taken in the original dataSource object,
        or None if undefined
        """
        pos = tuple(self._position) if self._position is not None else None
        return pos

    def getSliced(self, *sliceTuples) -> SpectrumDataABC:
        """Conveniance
        Get a part of the data, as defined by slices (1-based) in dimension order;
        updates self.position, so that it points to the actual location in the spectrum
        dataSource, corresponding to the objects data.

        :param sliceTuples: a list/tuple of (start,stop) tuples (1-based) in dimensions order;
                            a None value is expanded to (1,numPoints) for that dimension
        :return: a SpectrumData (e.g. SliceData, PlaneData, RegionData) object
        """
        if len(sliceTuples) != self.dimensionCount:
            raise ValueError('Invalid sliceTuples, expected length %d; got %s' %
                             (self.dimensionCount, sliceTuples)
                             )

        # make a zero-based list, augmenting all None's
        _slices = []
        for idx, sl, np in zip(range(self.dimensionCount), sliceTuples, self.pointCounts):
            if sl is not None:
                start,stop = tuple(sl)
                if start < 1 or stop > np:
                    raise ValueError('Invalid slices[%d], expected in range (1,%d); got %r' %
                                     (idx, np, sl))
                _slices.append((start-1,stop))
            else:
                _slices.append((0, np))

        sliceObjs = [slice(sl[0], sl[1], 1) for sl in _slices]
        result = self[tuple(sliceObjs[::-1])]
        # increments = [sl[0] for sl in _slices]
        # result._updatePosition(increments)

        return result

    def _shapeToDataSource(self):
        """Reshape the data with shape to match dataSource dimensions,
        using size=1, for any dimension of dataSource not in self;
        e.g. this transforms a 2D plane to a 3D with size 1 in one dimension
        CCPNINTERNAL: used in hdf5 extraction
        """
        newShape = [1]*self.dataSource.dimensionCount
        for dimIndx, np in zip(self.dimensionIndices, self.pointCounts):
            newShape[dimIndx] = np
        self.reshape(tuple(newShape[::-1]))

    def _shapeToSelf(self):
        """Reshape the data with shape to match self.dimensions
        CCPNINTERNAL: used in hdf5 extraction
        """
        nPoints = self.dataSource.pointCounts
        newShape = [nPoints[dimIndx] for dimIndx in self.dimensionIndices]
        self.reshape(tuple(newShape[::-1]))

    def _updatePosition(self, increments):
        # update the position (i.e. the place in the spectrum dataSource)
        if self._position is not None:
            pos = list(self._position)
            mapping = dict((idx, dimIdx) for idx, dimIdx in
                           enumerate(self.dimensionIndices))
            for idx, incr in enumerate(increments):
                dimIdx = mapping.get(idx, idx)  # This assures any missing elements
                pos[dimIdx] += incr
            self._position = pos

    def copy(self, order='K') -> SpectrumDataABC:
        """Make a copy of SpectrumDataObject, preserving order('K') as default argument (in contrast to the inherent method
        which uses order='C').
        """
        return super().copy(order=order)

    def __getitem__(self, item):
        """Just subclassed to catch the slice to update the internal position
        parameter
        """
        # print(self, item)

        # item can be many various things:
        # integer, tuple of int's, slice, tuple of slice's
        increments = None
        if isinstance(item, int):
            pass

        elif isinstance(item, slice) and item.start is not None:
            # this denotes a slice of the outermost level, eg. a z
            # in a x,y,z dataset
            increments = [0]*self.dataSource.dimensionCount
            # reversed, first becomes last (relative to self)
            increments[self.dimensionCount-1] = item.start

        elif isinstance(item, (tuple, list)):
            isSlices = [isinstance(obj,slice) for obj in item]
            if all(isSlices):
                increments = []
                for sl in item:
                    val = sl.start if sl.start is not None else 0
                    increments.append(val)
                # reverse the list, as the slices came in reversed order; append with zero
                increments = list(reversed(increments)) + \
                             [0] * (self.dataSource.dimensionCount - len(item))

        result =  super().__getitem__(item)
        if increments is not None:
            result._updatePosition(increments)

        return result

    def _objString(self) -> str:
        """:return a string describing the obj"""
        rcString = {False:'R', True:'C'}
        pos = ','.join(str(p) for p in self._position) \
                    if self._position is not None else None
        sizes =  'x'.join('%s%s' % (p, rcString[isC])
                          for p, isC in zip(self.realPointCounts, self.isComplex))

        return f'<{self.spectrumDataType}: {self.dimensionsString}, @{pos} ({sizes})>'

    def __str__(self):
        return f'{self._objString()}\n{super().__str__()}'


class SliceData(SpectrumDataABC):
    """Class to hold 1D slice data, either as float32 numpy array or optionally as
    a complex64 numpy array in case of complex data
    """
    spectrumDataType = 'SliceData'
    spectrumDataLen = 1

    @property
    def pointCounts(self) -> tuple:
        """The total number of points of self (i.e. shape).
        This corresponds to the pointCounts of the dataSource object in self.dimension's order
        :return a tuple of the total number of points
        """
        if self.dtype == np.complex64:
            _np = self.shape[0] * 2
        else:
            _np = self.shape[0]
        return (_np,)

    @property
    def isShuffled(self) -> bool:
        """:return True if the data are shuffled; i.e. in n(RI) or nPN order
        """
        dataType = self.dataTypes[0]
        return dataType in (specLib.DATA_TYPE_COMPLEX_nRI, specLib.DATA_TYPE_COMPLEX_PN)

    def shuffle(self) -> SpectrumDataABC:
        """For complex data: generate a copy of self with the data shuffled,
        i.e. in n(RI) or nPN order.
        :return data as float32
        """
        if not self.isComplex[0]:
            raise RuntimeError(f'{self._objString()}: not complex data')

        dataType = self.dataTypes[0]
        totalSize = self.pointCounts[0]
        realSize = self.realPointCounts[0]

        _data = self.copy()

        if self.isShuffled or self.dtype == np.complex64:
            pass

        elif dataType == specLib.DATA_TYPE_COMPLEX_nRnI:
            _data[0::2] = self[0:realSize]  # The real part
            _data[1::2] = self[realSize:totalSize]  # The imaginary part
            _data._dataTypes[0] = specLib.DATA_TYPE_COMPLEX_nRI

        else:
            raise RuntimeError(f'{self._objString()}: unable to shuffle dataType "{dataType}"')

        return _data

    def unshuffle(self) -> SpectrumDataABC:
        """For complex data: generate a copy of self with the data un-shuffled,
        i.e. in (nR)(nI) order.
        :return data as float32
        """
        if not self.isComplex[0]:
            raise RuntimeError(f'{self._objString()}: not complex data')

        if self.dtype == np.complex64:
            raise RuntimeError(f'{self._objString()}: data are in numpy.complex64 format; use asFloat() method first')

        dataType = self.dataTypes[0]
        totalSize = self.pointCounts[0]
        realSize = self.realPointCounts[0]

        _data = self.copy()

        if dataType == specLib.DATA_TYPE_COMPLEX_nRI:
            _data[0:realSize] = self[0::2]  # The real part
            _data[realSize:totalSize] = self[1::2]  # The imaginary part
            _data._dataTypes[0] = specLib.DATA_TYPE_COMPLEX_nRnI

        elif dataType == specLib.DATA_TYPE_COMPLEX_nRnI:
            pass

        else:
            raise RuntimeError(f'{self._objString()}: unable to unshuffle dataType "{dataType}"')

        return _data

    def asComplex(self):
        """:return a shuffled self as complex64 view
        """
        if not self.isShuffled:
            raise RuntimeError(f'{self._objString()}: cannot create complex view as data are not shuffled')
        return self.view(np.complex64)

    def asFloat(self):
        """:return a shuffled self as float32 view
        """
        if not self.isShuffled:
            raise RuntimeError(f'{self._objString()}: cannot create complex view as data are not shuffled')
        return self.view(np.float32)

class PlaneData(SpectrumDataABC):
    spectrumDataType = 'PlaneData'
    spectrumDataLen = 2


class CubeData(SpectrumDataABC):
    spectrumDataType = 'CubeData'
    spectrumDataLen = 3


class RegionData(SpectrumDataABC):
    spectrumDataType = 'RegionData'
    spectrumDataLen = None # defined by dimensions

