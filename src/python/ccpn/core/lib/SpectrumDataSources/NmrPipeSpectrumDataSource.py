"""
This file contains the NmrPipe data access class
it serves as an interface between the V3 Spectrum class and the actual spectral data

See SpectrumDataSourceABC for a description of the methods
"""
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
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2021-12-03 16:05:34 +0000 (Fri, December 03, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2020-11-20 10:28:48 +0000 (Fri, November 20, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys, re
from typing import Sequence
import numpy

from ccpn.util.Path import aPath, Path
from ccpn.util.Logging import getLogger

from ccpn.util.traits.CcpNmrTraits import CInt, CString

from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import SpectrumDataSourceABC
from ccpn.core.lib.SpectrumDataSources.lib.NmrPipeHeader import NmrPipeHeader

#============================================================================================================

DATA_TYPE_REAL    = 0  # real data points
DATA_TYPE_COMPLEX = 1  # size/2 real and size/2 imag points
DATA_TYPE_PN      = 2  # size/2 P and size/2 N points
dataTypeMap = {DATA_TYPE_REAL:"real", DATA_TYPE_COMPLEX:"complex", DATA_TYPE_PN:"PN"}

DOMAIN_TIME       = 0
DOMAIN_FREQUENCY  = 1
domainMap = {DOMAIN_TIME:"time", DOMAIN_FREQUENCY:"frequency"}

# ordering definitions for the NUS types, to be stored in FDUSER6
NUS_TYPE_NONUS    = 0
NUS_TYPE_NUS      = 1
NUS_TYPE_ISTNUS   = 2
nusMap = {NUS_TYPE_NONUS:"regular", NUS_TYPE_NUS:"nus", NUS_TYPE_ISTNUS:"ist-nus"}


#============================================================================================================
# Silly nmrPipe data size definitions!
#
# in all cases: (nAq, n1) total points along acquisition (X) and indirect-1 (Y),
# time domain (T) or frequency domain (F):
#
#     Acq       Ind1             FDSIZE   FDSPECNUM
#  (T) Complex  (T) Complex  ->   nAq/2     n1
#  (T) Complex  (T) Real     ->   nAq/2     n1
#  (T) Real     (T) Complex  ->   nAq       n1
#  (T) Real     (T) Real     ->   nAq       n1
#
#  (F) Complex  (T) Complex  ->   nAq/2     n1
#  (F) Complex  (T) Real     ->   nAq/2     n1
#  (F) Real     (T) Complex  ->   nAq       n1/2
#  (F) Real     (T) Real     ->   nAq       n1
#
#  (F) Complex  (F) Complex  ->   nAq/2     n1
#  (F) Complex  (F) Real     ->   nAq/2     n1
#  (F) Real     (F) Complex  ->   nAq       n1/2
#  (F) Real     (F) Real     ->   nAq       n1
#
#
#============================================================================================================

class NmrPipeSpectrumDataSource(SpectrumDataSourceABC):
    """
    NmrPipe spectral storage
    """

    #=========================================================================================
    dataFormat = 'NMRPipe'

    isBlocked = False
    wordSize = 4
    headerSize = 512
    blockHeaderSize = 0
    isFloatData = True
    MAXDIM = 4          # Explicitly overide as NmrPipe can only handle upto 4 dimensions

    suffixes = ['.dat', '.fid', '.ft1', '.ft2', '.ft3', '.ft4']
    openMethod = open
    defaultOpenReadMode = 'rb'

    #=========================================================================================

    nFiles = CInt(default_value=0).tag(
                                        info='The number of files comprising the nD',
                                        isDimensional=False,
                                        doCopy=True,
                                        spectrumAttribute=None,
                                        hasSetterInSpectrumClass=False
                                       )

    baseDimensionality = CInt(default_value=2).tag(
                                        info='Dimensionality of the NmrPipe files comprising the nD',
                                        isDimensional=False,
                                        doCopy=True,
                                        spectrumAttribute=None,
                                        hasSetterInSpectrumClass=False
                                       )

    template = CString(allow_none=True, default_value=None).tag(
                                        info='The template to generate the path of the individual files comprising the nD',
                                        isDimensional=False,
                                        doCopy=True,
                                        spectrumAttribute=None,
                                        hasSetterInSpectrumClass=False
                                       )


    def __init__(self, path=None, spectrum=None, temporaryBuffer=True, bufferPath=None):
        """Initialise; optionally set path or extract from spectrum

        :param path: optional input path
        :param spectrum: associate instance with spectrum and import spectrum's parameters
        :param temporaryBuffer: used temporary file to buffer the data
        :param bufferPath: (optionally) use path to generate buffer file (implies temporaryBuffer=False)
        """
        super().__init__(path=path, spectrum=spectrum)

        self.header = None  # NmrPipeHeader instance
        self.pipeDimension = None
        self.nusDimension = None

        # NmrPipe files are always buffered
        self.setBuffering(True, temporaryBuffer, bufferPath)

    def _readHeader(self):
        "Create NmrPipeHeader instance and read the data"
        if not self.hasOpenFile():
            self.openFile(mode=self.defaultOpenReadMode)
        self.header = NmrPipeHeader(self.headerSize, self.wordSize).read(self.fp, doSeek=True)

    def readParameters(self):
        """Read the parameters from the NmrPipe file header
        Returns self
        """
        logger = getLogger()

        self.setDefaultParameters()

        try:
            self._readHeader()

            # check the 'magic' bytes
            magicBytes = tuple(self.header.bytes[8:12])
            if magicBytes not in self.header._byteOrderFlags:
                raise RuntimeError('NmrPipe file "%s" appears to be corrupted: does not contain the expected magic 4 bytes' %
                                  self.path)
            byteorder = self.header._byteOrderFlags[magicBytes]
            if  byteorder != sys.byteorder:
                self.header.swapBytes()
                self.isBigEndian = (byteorder == 'big')

            for parName in self.header.parameterNames:
                result = self.header.getParameterValue(parName)
                setattr(self, parName, result)

                # Fixes!
                if self.temperature == 0.0:
                    self.temperature = None

                # Pipe and NUS dimensions??
                map1 = {1:self.X_DIM, 2:self.Y_DIM, 3:self.Z_DIM, 4:self.A_DIM, 0:None}
                if parName == "pipeDimension":
                    self.pipeDimension = map1[self.pipeDimension]
                if parName == "nusDimension":
                    self.nusDimension = map1[self.nusDimension]
                #end if

            if self.template is None and self.dimensionCount > 2:
                self.template = self._guessTemplate()

            self._setBaseDimensionality()
            self.blockSizes = [1]*self.MAXDIM
            self.blockSizes[0:self.baseDimensionality] = self.pointCounts[0:self.baseDimensionality]

        except Exception as es:
            logger.error('Reading parameters; %s' % es)
            raise es

        # this will set isotopes, axiscodes, assures dimensionality
        super().readParameters()

        # fix possible acquisition axis code
        if self.transposed:
            self.acquisitionAxisCode = self.axisCodes[self.Y_AXIS]

        return self

    def _setBaseDimensionality(self):
        """Set the baseDimensionality depending on dimensionCount, nFiles and template
        """
        self.baseDimensionality = 2  # The default
        # nD's stored as a single file
        if self.nFiles == 1:
            self.baseDimensionality = self.dimensionCount
        # 4D's stored as series of 3D's
        if self.dimensionCount == 4 and self.nFiles > 1 and \
           self.template is not None and self.template.count('%') == 1:
            self.baseDimensionality = 3

    def _guessTemplate(self):
        """Guess and return the template based on self.path and dimensionality
        Return None if unsuccessful or not applicable
        """
        logger = getLogger()

        directory, fileName, suffix = self.path.split3()

        if self.dimensionCount == 2:
            pass

        elif self.dimensionCount in [3,4] and self.nFiles == 1:
            pass

        elif self.dimensionCount == 3 and self.nFiles > 1:
            # 3D's stored as series of 2D's
            templates = (re.sub('\d\d\d\d', '%04d', fileName),
                         re.sub('\d\d\d',   '%03d', fileName),
                         re.sub('\d\d',     '%02d', fileName),
            )
            for template in templates:
                # check if we made a subsititution
                if template != fileName:
                    # check if we can find the last 3D file of the series
                    path = Path(directory) / (template % self.pointCounts[self.Z_AXIS]) + suffix
                    if path.exists():
                        return str(Path(directory) / (template) + suffix)

        elif self.dimensionCount == 4 and self.nFiles > 1:
            # 4D's stored as series of 2D's
            templates = (re.sub('\d\d\d\d\d\d\d', '%03d%04d', fileName),
                         re.sub('\d\d\d\d\d\d',   '%03d%03d', fileName),
                         re.sub('\d\d\d\d\d\d',   '%02d%04d', fileName),
                         re.sub('\d\d\d\d\d',     '%02d%03d', fileName),
            )
            for template in templates:
                # check if we made a subsititution
                if template != fileName:
                    # check if we can find the last 4D file of the series
                    path = Path(directory) / (template % (self.pointCounts[self.Z_AXIS], self.pointCounts[self.A_AXIS])) + suffix
                    if path.exists():
                        return str(Path(directory) / (template) + suffix)

            # 4D's stored as series of 3D's
            templates = (re.sub('\d\d\d\d', '%04d', fileName),
                         re.sub('\d\d\d',   '%03d', fileName),
                         re.sub('\d\d',     '%02d', fileName),
            )
            for template in templates:
                # check if we made a subsititution
                if template != fileName:
                    # check if we can find the last 4D file of the series
                    path = Path(directory) / (template % self.pointCounts[self.A_AXIS]) + suffix
                    if path.exists():
                        return str(Path(directory) / (template) + suffix)

        logger.debug('NmrPipeSpectrumDataSource._guessTemplate: Unable to guess from "%s"' % self.path)
        return None

    def _getPathAndOffset(self, position):
        """Construct path of NmrPipe file corresponding to position (1-based) from template
        Check presence of result path
        Return aPath instance of path and offset (in bytes) as a tuple
        """
        if self.dimensionCount <= 2:
            path = self.path
            offset = self.headerSize * self.wordSize

        elif self.dimensionCount == 3 and self.nFiles == 1:
            path = self.path
            offset = ( self.headerSize + \
                      (position[self.Z_AXIS]-1) *self.pointCounts[self.X_AXIS] * self.pointCounts[self.Y_AXIS]
                     ) * self.wordSize

        elif self.dimensionCount == 3 and self.baseDimensionality == 2:
            if self.template is None:
                raise RuntimeError('%s: Undefined template' % self)
            path = self.template % (position[self.Z_AXIS],)
            offset = self.headerSize * self.wordSize

        elif self.dimensionCount == 4 and self.baseDimensionality == 2:
            if self.template is None:
                raise RuntimeError('%s: Undefined template' % self)
            path =  self.template % (position[self.Z_AXIS], position[self.A_AXIS])
            offset = self.headerSize * self.wordSize

        elif self.dimensionCount == 4 and self.baseDimensionality == 3:
            if self.template is None:
                raise RuntimeError('%s: Undefined template' % self)
            path =  self.template % (position[self.A_AXIS],)
            offset = ( self.headerSize + \
                      (position[self.A_AXIS]-1) *self.pointCounts[self.X_AXIS] * self.pointCounts[self.Y_AXIS]
                     ) * self.wordSize
        else:
            raise RuntimeError('%s: Unable to construct path for position %s' % (self, position))

        path = aPath(path)
        if not path.exists():
            raise FileNotFoundError('NmrPipe file "%s" not found' % path)

        return path, offset

    def setPath(self, path, substituteSuffix=False):
        """define valid path to a (binary) data file, if needed appends or substitutes
        the suffix (if defined).


        return self or None on error
        """
        if path is None:
            self.dataFile = None  # A reset essentially
            return self

        _path = aPath(path)
        if _path.is_dir():
            files = [f for f in _path.glob('*001.dat')]
            if len(files) > 0:
                _path = files[0]

        return super().setPath(path=_path, substituteSuffix=substituteSuffix)

    def fillHdf5Buffer(self):
        """Fill hdf5buffer with data from self
        """
        if not self.isBuffered:
            raise RuntimeError('fillHdf5Buffer: no hdf5Buffer defined')

        getLogger().debug('fillHdf5Buffer: filling buffer %s' % self.hdf5buffer)

        xAxis = self.X_AXIS
        xDim = self.X_DIM
        yAxis = self.Y_AXIS
        yDim = self.Y_DIM

        if self.dimensionCount == 1:
            # 1D
            position = [1]
            path, offset = self._getPathAndOffset(position)
            with open(path, 'r') as fp:
                fp.seek(offset, 0)
                data = numpy.fromfile(file=fp, dtype=self.dtype, count=self.pointCounts[xAxis])
            self.hdf5buffer.setSliceData(data, position=position, sliceDim=xDim)

        else:
            # nD's: fill the buffer, reading x,y planes from the nmrPipe files into the hdf5 buffer
            planeSize = self.pointCounts[xAxis] * self.pointCounts[yAxis]
            sliceTuples = [(1, p) for p in self.pointCounts]
            for position, aliased in self._selectedPointsIterator(sliceTuples, excludeDimensions=(xDim, yDim)):
                path, offset = self._getPathAndOffset(position)
                with open(path, 'r') as fp:
                    fp.seek(offset, 0)
                    data = numpy.fromfile(file=fp, dtype=self.dtype, count=planeSize)
                    data.resize( (self.pointCounts[yAxis], self.pointCounts[xAxis]))
                self.hdf5buffer.setPlaneData(data, position=position, xDim=xDim, yDim=yDim)
        self._bufferFilled = True

# Register this format
NmrPipeSpectrumDataSource._registerFormat()


class NmrPipeInputStreamDataSource(NmrPipeSpectrumDataSource):
    """
    NmrPipe spectral storage, reading from an stdinp stream
    """
    def __init__(self, spectrum=None, temporaryBuffer=True, bufferPath=None):
        """Initialise; optionally set path or extract from spectrum

        :param path: optional input path
        :param spectrum: associate instance with spectrum and import spectrum's parameters
        :param temporaryBuffer: used temporary file to buffer the data
        :param bufferPath: (optionally) use path to generate buffer file (implies temporaryBuffer=False)
        """
        super().__init__(spectrum=spectrum, temporaryBuffer=temporaryBuffer, bufferPath=bufferPath)
        # sys.stdin.reconfigure(encoding='ISO-8859-1')
        self.fp = sys.stdin.buffer
        self.readParameters()
        self.setBuffering(True, bufferIsTemporary=temporaryBuffer, bufferPath=bufferPath)
        self.initialiseHdf5Buffer()
        self.fillHdf5Buffer()

    def _readHeader(self):
        "Create NmrPipeHeader instance and read the data"
        self.header = NmrPipeHeader(self.headerSize, self.wordSize).read(self.fp, doSeek=False)

    def _guessTemplate(self):
        "Guess template not active/required for input stream"
        return None

    def fillHdf5Buffer(self, hdf5buffer):
        """Fill hdf5 buffer reading all slices from input stream
        """
        sliceDim = self.pipeDimension
        if sliceDim is None:
            raise RuntimeError('%s.fillHdf5Buffer: undefined dimension of the input stream')
        getLogger().debug('Fill hdf5 buffer from sys.stdin reading %d slices along dimension %s' %
                          (self.sliceCount, sliceDim))

        sliceTuples = [(1, p) for p in self.pointCounts]
        for position, aliased in self._selectedPointsIterator(sliceTuples, excludeDimensions=(sliceDim,)):
            data = numpy.fromfile(file=self.fp, dtype=self.dtype, count=self.pointCounts[sliceDim-1])
            hdf5buffer.setSliceData(data, position=position, sliceDim=sliceDim)
        self._bufferFilled = True

    def closeFile(self):
        """close the file
        """
        self.fp = None  # Do not close sys.stdin --> set self.fp to None here!
        self.mode = None
        super().closeFile()

# NmrPipeInputStreamDataSource._registerFormat()
