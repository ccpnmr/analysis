"""
This file contains the Jeol data access class
it serves as an interface between the V3 Spectrum class and the actual spectral data

See SpectrumDataSourceABC for a description of the methods
"""
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
__dateModified__ = "$dateModified: 2023-10-06 18:02:25 +0100 (Fri, October 06, 2023) $"
__version__ = "$Revision: 3.2.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2023-09-18 10:28:48 +0000 (Mon, September 18, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
import io
import math
from typing import Sequence

from ccpn.util.Path import Path, aPath, home
from ccpn.util.Common import flatten
from ccpn.util.traits.CcpNmrTraits import CFloat, CInt, CBool, Bool, List, TList, \
    CString, CList, CPath, Any, CTuple

from ccpn.util.Logging import getLogger

import ccpn.core.lib.SpectrumLib as specLib

from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import SpectrumDataSourceABC
from ccpn.core.lib.SpectrumDataSources.lib.BinaryHeader import BinaryHeader
from ccpn.core._implementation.SpectrumData import SliceData, PlaneData, RegionData


WORD_SIZE = 4
MAX_BYTES = 1360
HEADER_SIZE = MAX_BYTES / WORD_SIZE


DATA_FORMAT_1D = 1
DATA_FORMAT_2D = 2
DATA_FORMAT_3D = 3
DATA_FORMAT_4D = 4
DATA_FORMAT_5D = 5
DATA_FORMAT_6D = 6
DATA_FORMAT_7D = 7
DATA_FORMAT_8D = 8
DATA_FORMAT_SMALL_2D = 12
DATA_FORMAT_SMALL_3D = 13
DATA_FORMAT_SMALL_4D = 14

subMatrixSizes = {
    DATA_FORMAT_1D : [8],  # This is silly, why divide a 1D??
    DATA_FORMAT_2D : [32]*2,
    DATA_FORMAT_3D : [8]*3,
    DATA_FORMAT_4D : [8]*4,
    DATA_FORMAT_5D : [4]*5,
    DATA_FORMAT_6D : [4]*6,
    DATA_FORMAT_7D : [2]*7,
    DATA_FORMAT_8D : [2]*8,
    DATA_FORMAT_SMALL_2D : [4]*2,
    DATA_FORMAT_SMALL_3D : [4]*3,
    DATA_FORMAT_SMALL_4D : [4]*4,
}

DATA_AXIS_TYPE_NOTUSED = 0
DATA_AXIS_TYPE_REAL = 1
DATA_AXIS_TYPE_TPPI = 2
DATA_AXIS_TYPE_COMPLEX = 3
DATA_AXIS_TYPE_REAL_COMPLEX = 4

dataTypeMap = {
    DATA_AXIS_TYPE_NOTUSED : specLib.DATA_TYPE_REAL,
    DATA_AXIS_TYPE_REAL : specLib.DATA_TYPE_REAL,
    DATA_AXIS_TYPE_TPPI : specLib.DATA_TYPE_REAL,
    DATA_AXIS_TYPE_COMPLEX : specLib.DATA_TYPE_COMPLEX_nRnI,
    DATA_AXIS_TYPE_REAL_COMPLEX : specLib.DATA_TYPE_REAL,  # A sillt definition: complex for dim=0, real otherwise
}

UNITS_HZ = 13
UNITS_PPM = 26
UNITS_SEC = 28
dimensionUnitsMap = {
    0 : None,
    1 : 'Abundance',
    2 : 'Ampere',
    3 : 'Candela',
    4 : 'Celsius',
    5 : 'Coulomb',
    6 : 'Degree',
    7 : 'Electronvolt',
    8 : 'Farad',
    9 : 'Sievert',
    10 : 'Gram',
    11 : 'Gray',
    12 : 'Henry',
UNITS_HZ: 'Hertz',
    14 : 'Kelvin',
    15 : 'Joule',
    16 : 'Liter',
    17 : 'Lumen',
    18 : 'Lux',
    19 : 'Meter',
    20 : 'Mole',
    21 : 'Newton',
    22 : 'Ohm',
    23 : 'Pascal',
    24 : 'Percent',
    25 : 'Point',
UNITS_PPM : 'Ppm',
    27 : 'Radian',
UNITS_SEC : 'Second',
    29 : 'Siemens',
    30 : 'Steradian',
    31 : 'Tesla',
    32 : 'Volt',
    33 : 'Watt',
    34 : 'Weber',
    35 : 'Decibel',
    36 : 'Dalton',
    37 : 'Thompson',
    38 : 'Ugeneric',
    39 : 'LPercent',
    40 : 'PPT',
    41 : 'PPB',
    42 : 'Index'
}

class JeolSpectrumDataSource(SpectrumDataSourceABC):
    """
    Jeol binary nD spectral data reading; limited to 4D for now
    """
    dataFormat = 'Jeol'
    MAXDIM = 8

    isBlocked = True
    wordSize = 4
    headerSize = MAX_BYTES / wordSize
    blockHeaderSize = 0
    isFloatData = True
    suffixes = ['.jdf']
    openMethod = io.open
    defaultOpenReadMode = 'rb'

    _dataIs32Bit = CBool(default_value=False).tag(info='data is stored as 32 bit')
    _dataScaleIsDefined = CBool(default_value=True).tag(info='dataScale has been defined (on basis of noise original data)')

    _dataOffsetBytes = CInt(default_value=None, allow_none=True).tag(info='offset in Bytes for start of data')
    _dataTotalBytes = CInt(default_value=None, allow_none=True).tag(info='Total number of data Bytes')

    _dataValidPoints =  TList(itemTrait=CTuple(allow_none=True), default_value=[None] * MAXDIM, maxlen=MAXDIM).tag(
                              info='Tuples of valid points along each dimension',
                              isDimensional=True,
                              doCopy=False,
                              spectrumAttribute=None,
                              hasSetterInSpectrumClass=False
                             )
    _dimensionUnits =  TList(itemTrait=CString(allow_none=True), default_value=[None] * MAXDIM, maxlen=MAXDIM).tag(
                              info='Units along each dimension',
                              isDimensional=True,
                              doCopy=False,
                              spectrumAttribute=None,
                              hasSetterInSpectrumClass=False
                             )

    _dataRanges =  TList(itemTrait=CTuple(allow_none=True), default_value=[None] * MAXDIM, maxlen=MAXDIM).tag(
                              info='Tuples of data range along each dimension',
                              isDimensional=True,
                              doCopy=False,
                              spectrumAttribute=None,
                              hasSetterInSpectrumClass=False
                             )

    _dataZeroPoints =  TList(itemTrait=CFloat(allow_none=True), default_value=[None] * MAXDIM, maxlen=MAXDIM).tag(
                              info='zero points along each dimension',
                              isDimensional=True,
                              doCopy=False,
                              spectrumAttribute=None,
                              hasSetterInSpectrumClass=False
                             )

    def readParameters(self):
        """Read the parameters from the Jeol file header
        Returns self
        """
        logger = getLogger()

        self.setDefaultParameters()

        try:
            if not self.hasOpenFile():
                self.openFile(mode=self.defaultOpenReadMode)

            header = self.header = JeolHeader(self.headerSize, self.wordSize).read(self.fp)

            # CHeck some crucial values in the header (according to documentation)
            if (jeolStr := header.bytesToString(0, 8)) != 'JEOL.NMR' or \
               (majorVersion := header.bytes[9:10].view(dtype='>B'))[0] != 1 or \
               (minorVersion := header.bytes[10:12].view(dtype='>H')[0]) != 2:
                raise RuntimeError('Jeol file %s appears to be corrupted' % self.path)

            #ndim
            self.dimensionCount =  header.bytes[12:13].view('>B')[0]

            # # dimensions
            # print('dims:        ', bin(header.bytes[13:14].view(dtype='>B')[0]))
            #
            #author
            self.user = header.bytesToString(552, 680, strip=True)
            #
            #comment
            self.comment = 'Comment: ' + header.bytesToString(680, 808, strip=True) + \
                           '; Title: ' + header.bytesToString(48, 48+124, strip=True)

            #-------------------------------------------------------------------------------------------------
            # Data related
            #-------------------------------------------------------------------------------------------------
            # data little endian
            self.isBigEndian = not bool(header.bytes[9].view(dtype='>B'))

            # Reading parameters implies resetting the data scaling and doing this again
            self.dataScale = 1.0
            self._dataScaleIsDefined = False

            # Byte 14: upper 2 bits; 32 bit or 64 bit
            self._dataIs32Bit = bool(header.bytes[14].view(dtype='>B') & 0b11000000)

            # Byte 14: 6 bits; data format that defines submatrices
            data_format = int(header.bytes[14].view(dtype='>B') & 0b00111111)
            try:
                self.blockSizes = subMatrixSizes[data_format]
            except KeyError:
                self.errorString = f'data_format {data_format} does not define a valid Jeol sub-matrix definition'
                self.isValid = False
                raise RuntimeError(f'{self.errorString}; bailing out')

            self._dataOffsetBytes = int(header.bytes[1284:1288].view(dtype='>I'))
            self._dataTotalBytes = int(header.bytes[1288:1296].view(dtype='>Q'))

            #-------------------------------------------------------------------------------------------------
            # dimensions
            #-------------------------------------------------------------------------------------------------
            dimension_map = [int(header.bytes[16+i].view(dtype='>B')) for i in range(self.MAXDIM)]
            # print('dimension_map:', dimension_map)
            self.dimensionOrder = [d-1 for d in dimension_map]

            self.axisLabels = [header.bytesToString(808+dim*32, 808+(dim+1)*32, strip=True) for dim in range(self.MAXDIM)]

            # data axis types
            _data_axis_types = header.bytes[24:32].view(dtype='>B')
            # print('data_axis_types:  ', data_axis_types)
            self.dataTypes = [dataTypeMap.get(t, specLib.DATA_TYPE_REAL) for t in _data_axis_types]
            # correct for silly _REAL_COMPLEX type definition
            if _data_axis_types[0] == DATA_AXIS_TYPE_REAL_COMPLEX:
                self.dataTypes[0] = specLib.DATA_TYPE_COMPLEX_nRnI
            self.isComplex = [specLib.isComplexDataType(dt) for dt in self.dataTypes]

            _points = header.bytes[176:208].view(dtype='>i')
            # print('points:      ',points)
            self.pointCounts = [p*2 if self.isComplex[i] else p for i,p in enumerate(_points)]

            offset_start = [int(val) for val in header.bytes[208:240].view(dtype='>i')]
            # print('offset_start:', offset_start)
            offset_stop = [int(val) for val in header.bytes[240:272].view(dtype='>i')]
            # print('offset_stop: ', offset_stop)
            self._dataValidPoints = [t for t in zip(offset_start, offset_stop)]

            self.spectrometerFrequencies = header.bytes[1064:1128].view(dtype='>d')
            # print('freqs:            ', freqs)

            dimension_units = [val & 0xff for val in header.bytes[32:32+(2*self.MAXDIM)].view(dtype='>H')]
            # print('dimension_units:   ', dimension_units)
            self._dimensionUnits = [dimensionUnitsMap.get(u, None) for u in dimension_units]

            # dimension types
            self.dimensionTypes = [specLib.DIMENSION_TIME if unit == UNITS_SEC else specLib.DIMENSION_FREQUENCY
                                   for unit in dimension_units
                                   ]

            # first 4 and second 4 bits of each Byte
            _dr = [(header.bytes[172+i] & 0xf0, header.bytes[172+i] & 0x0f) for i in range(4)]
            data_ranged = [int(_d) for _d in flatten(_dr)]
            # print('data_ranged:  ', data_ranged
            data_start = [float(val) for val in header.bytes[272:336].view(dtype='>d')]
            # print('data_start:   ', data_start)
            data_stop = [float(val) for val in header.bytes[336:400].view(dtype='>d')]
            # print('data_stop:    ', data_stop)
            self._dataRanges = [t if data_ranged[i]==0 else None for i,t in enumerate(zip(data_start, data_stop))]

            # GWV: This is related to the reference values
            _dataZeroPoints = [float(val)+0.5 for val in header.bytes[1128:1192].view(dtype='>d')]

            # GWV: reconstruct (best guess) spectralwiths
            for i, dRange, dValidPoints, np in zip(range(self.dimensionCount), self._dataRanges, self._dataValidPoints, self.realPointCounts):
                if dRange is None or dValidPoints is None:
                    break
                _drange = dRange[1] - dRange[0]
                _nvp = dValidPoints[1] - dValidPoints[0] + 1  # n valid points; start-stop defined inclusive
                if dimension_units[i] == UNITS_SEC:
                    if specLib.isComplexDataType(self.dataTypes[i]):
                        sw = float(_nvp) / _drange  # dwell = range / nvp; sw = 1 / dwell
                    else:
                        sw = 0.5 * float(_nvp) / _drange  # dwell = range / nvp; sw = 1 / 2*dwell

                elif dimension_units[i] == UNITS_HZ:
                    sw = _drange
                    self.referencePoints[i] = int(_dataZeroPoints[i] * _nvp)
                    self.referenceValues[i] = 0.0

                elif dimension_units[i] == UNITS_PPM:
                    sw = _drange * self.spectrometerFrequencies[i]
                    self.referencePoints[i] = dValidPoints[0] + 1  # one-based
                    self.referenceValues[i] = dRange[0]

                else:
                    getLogger().warning(f'Unable to derive spectral width for dimension {i+1}; (unite={dimension_units[i]}')
                    break

                # Set sw to encompass all points, including also the non-valid ones. So if these are
                # stripped the sw can be adjusted accordingly
                sw *= float(np) / float(_nvp)
                self.spectralWidthsHz[i] = sw


            #-------------------------------------------------------------------------------------------------


        except Exception as es:
            logger.debug('Reading parameters; %s' % es)
            raise es

        return super().readParameters()

    def _pointsToAbsoluteBlockIndex(self, points):
        """
        :param points: an n-dimensional points vector (zero-based)
        :returns absolute block index corresponding to points (zero-based)

        The Jeol files group the submatrices for (hyper)complex files in "sections"
        e.g. for a 2D hypercomplex: RR, RI, IR and II sections are stored
        sequentially in the file; (yes: not in x,y,z,a order!).

        if the data are assumed to be treated nRnI along any complex axis, and we define
            I[x,y,z,a] is the blockIndex along x, y, z, a
            N[x,y,z,a] is number of blocks along x, y, z, a

        if the blockindex I[x,y,z,a] >= N[x,y,z,a] // 2 it is a "complex" block.
        So define:
        - blockComplex[x,y,z,a] as 0/1 (or False/True) for real/imag (also used to define the section)
        - an effective blockIndex Ieff[x,y,z,a] as I[x,y,z,a] % 2
        - the effective number of blocks, Neff[x,y,z,a]. The latter is half along any complex x,y,z,a dimensions,

        absIndex =   Ieff[a] * Neff[z] * Neff[y] * Neff[x]  +
                     Ieff[z]           * Neff[y] * Neff[x]  +
                     Ieff[y]                     * Neff[x]  +
                     Ieff[x]
                     + sectionBlockOffset

                 = ((Ieff[a] * Neff[z] + Ieff[z]) * Neff[y] + Ieff[y]) * Neff[x] + Ieff[x]
                    + sectionBlockOffset

        sectionBlockOffset (0 = Real; 1 = Imaginary);
        1D: {(0,) : 0, (1,) : 1}

        2D: {(0,0) : 0, (0,1) : 1, (1,0) : 2, (1,1) : 3}

        3D: {(0,0,0) : 0, (0,0,1) : 1, (0,1,0) : 2, (0,1,1) : 3,
             (1,0,0) : 4, (1,0,1) : 5, (1,1,0) : 6, (1,1,1) : 7
            }

        4D: {(0,0,0,0) : 0, (0,0,0,1) : 1, (0,0,1,0) : 2, (0,0,1,1) : 3,
             (0,1,0,0) : 4, (0,1,0,1) : 5, (0,1,1,0) : 6, (0,1,1,1) : 7,
             (1,0,0,0) : 8, (1,0,0,1) : 9, (1,0,1,0) : 10, (1,0,1,1) : 11,
             (1,1,0,0) : 12, (1,1,0,1) : 13, (1,1,1,0) : 14, (1,1,1,1) : 15
            }
        etc
        Off course this a binary code with the bits in dimension-reversed order!

        Assuming all dimensions are complex. If a dimension is not complex, it is simply skipped, and the lower
        dimensional definition is used (e.g. a 3D with 2 complex dimensions will use the 2D defs).

        """
        # The "regular" nRnI arrangement of the blocks
        blockIndices = [idx for idx, _t in self._pointsToBlocksPerDimension(points)]
        numBlocks = self._numBlocksPerDimension

        # Now map on the Jeol block arrangement
        # Make blockComplex array; i.e. the array that tells if it is in the real or imag part
        blockComplex = [self.isComplex[i] and blockIndices[i] >= numBlocks[i] // 2 for i in range(self.dimensionCount)]
        # Make effective numBlocks array
        effNumBlocks    = [nb // 2 if self.isComplex[i] else nb for i, nb in enumerate(numBlocks)]
        # Make effective blockIndices array
        effBlockIndices = [bi % effNumBlocks[i] if blockComplex[i] else bi for i, bi in enumerate(blockIndices)]
        # get in which section; e.g. RR or IR, .., we are
        sectionIndex = self._getSectionIndex(blockComplex)
        numBlocksPerSection = math.prod(effNumBlocks)

        # start at the highest dimension
        dim = self.dimensionCount - 1
        absIndex = effBlockIndices[dim]
        dim -= 1
        while dim >= 0:
            absIndex = absIndex * effNumBlocks[dim] + effBlockIndices[dim]
            dim -= 1

        absIndex += sectionIndex * numBlocksPerSection

        return absIndex

    @property
    def dtype(self):
        """return the numpy dtype string of the data based on settings
        """
        _code = 'f' if self._dataIs32Bit else 'd'
        return f"{self.isBigEndian and '>' or '<'}{_code}"

    def _getSectionIndex(self, blockComplex:list) -> int:
        """Calculate the section index
        : blockComplex: a list of 1/0 (False/True) values denoting real/imag blocks in dimension order;
                        treated by the algorithm in reverse order
        : return the section index
        """
        # strip the blockComplex array from any dimension that is not complex itself
        # (as this dimension will not generate additional sections in the file)
        _bits = []
        for i, bc in enumerate(blockComplex):
            if self.isComplex[i]:
                _bits.append(bc)

        result = 0
        # Do a bit-wise addition, setting each "bit" per complex dimension; reverse order
        for i, bit in enumerate(_bits[::-1]):
            result += (bit * 2**i)
        return result

    def _getBlockOffset(self, absoluteBlockIndex):
        """Calculate the block offset
        :param absoluteBlockIndex: index of the block to calculate the offset
        :return offset in Bytes
        """
        wordSize = 4 if self._dataIs32Bit else 8
        offset = self._dataOffsetBytes + \
                 absoluteBlockIndex * self._totalBlockSize * wordSize  # offset in bytes
        return offset

    def _setDataScale(self, data, noiseLevel):
        """Helper function to set the dataScale parameter based on data and noiseLevel
        :return data scaled by new self.dataScale
        """
        self.dataScale = 1.0
        while 0.0 < noiseLevel < 1.0:
            self.dataScale *= 10.0
            noiseLevel *= 10.0
        self._dataScaleIsDefined = True
        self.noiseLevel = noiseLevel
        data *= self.dataScale
        return data

    def getSliceData(self, position: Sequence = None, sliceDim: int = 1) -> SliceData:
        """Get slice defined by sliceDim and position

        Subclassed to check for scaling based on the noise level on first usage,
        as values appear to be very small in the original data.

        :param position: position vector (1-based)
        :param sliceDim: dimension to take the slice (1-based)
        :return: SliceData instance
        """

        data = super().getSliceData(position=position, sliceDim=sliceDim)
        if not self._dataScaleIsDefined:
            noiseLevel, _tmp = specLib.estimateNoiseLevel1D(data)
            data = self._setDataScale(data, noiseLevel)
        return data

    def getPlaneData(self, position: Sequence = None, xDim: int = 1, yDim: int = 2) -> PlaneData:
        """Get plane defined by xDim, yDim and position
        Check for hdf5buffer first, then blocked format

        Subclassed to check for scaling based on the noise level on first usage,
        as values appear to be very small in the original data.

        :param position: position vector (1-based)
        :param xDim: first dimension of the plane (1-based)
        :param yDim: second dimension of the plane (1-based)
        :return PlaneData instance (i.e. numpy.ndarray).
        """

        data = super().getPlaneData(position=position, xDim=xDim, yDim=yDim)
        if not self._dataScaleIsDefined:
            noiseLevel, _tmp = specLib.estimateNoiseLevelnD(data, stdFactor=0.5)
            data = self._setDataScale(data, noiseLevel)
        return data


# Register the format
JeolSpectrumDataSource._registerFormat()


class JeolHeader(BinaryHeader):
    """Class to read the binary Jeol header using numpy
    """

    def read(self, fp, doSeek=True):
        """Read and initialise the header from binary file pointed to by fp
        :param doSeek: seek to start of file if True
        :return self
        """

        if doSeek:
            fp.seek(0,0)  # rewind the file as header should be at the start

        self.bytes = np.fromfile(fp, dtype='B', count=MAX_BYTES)
        return self










