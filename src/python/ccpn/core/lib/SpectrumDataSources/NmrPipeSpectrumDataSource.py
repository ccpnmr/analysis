"""
This file contains the NmrPipe data access class
it serves as an interface between the V3 Spectrum class and the actual spectral data

See SpectrumDataSourceABC for a description of the methods

The NmrPipe data access completely relies on the Hdf5buffer option: the NmrPipe file
is fully read into the temporary buffer at the moment of first data access
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
__dateModified__ = "$dateModified: 2023-07-28 17:24:46 +0100 (Fri, July 28, 2023) $"
__version__ = "$Revision: 3.2.0 $"
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

from ccpn.util.traits.CcpNmrTraits import CList, CInt, Int, CString, Bool

from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import SpectrumDataSourceABC
from ccpn.core.lib.SpectrumDataSources.lib.NmrPipeHeader import NmrPipeHeader

import ccpn.core.lib.SpectrumLib as specLib

#============================================================================================================

#define FD_QUAD       0
#define FD_COMPLEX    0
#define FD_SINGLATURE 1
#define FD_REAL       1
#define FD_PSEUDOQUAD 2
#define FD_SE         3
#define FD_GRAD       4
from ccpn.core.lib.SpectrumLib import DATA_TYPE_REAL, DATA_TYPE_COMPLEX_PN, DATA_TYPE_COMPLEX_nRnI, DATA_TYPE_COMPLEX_nRI
dataTypeMap = {0:DATA_TYPE_COMPLEX_nRnI, 1:DATA_TYPE_REAL, 2:DATA_TYPE_REAL, 3:DATA_TYPE_COMPLEX_PN, 4:DATA_TYPE_REAL}

from ccpn.core.lib.SpectrumLib import DIMENSION_FREQUENCY, DIMENSION_TIME
PIPE_TIME_DOMAIN  = 0
PIPE_FREQUENCY_DOMAIN  = 1
# map NmrPipe defs on V3 defs
domainMap = {PIPE_TIME_DOMAIN:DIMENSION_TIME, PIPE_FREQUENCY_DOMAIN:DIMENSION_FREQUENCY}

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
#============================================================================================================

class NmrPipeSpectrumDataSource(SpectrumDataSourceABC):
    """
    NmrPipe nD (n=1-4) binary spectral data reading:
    The NmrPipe files are stored as either:
    - a single file
    - or for 3D/4D as a series of 2D planes defined by a nmrPipeTemplate name; e.g. 'myFile%003d.ft3'

    NmrPipe spectra can be loaded by either:
    - A nD plane file; if required, the nmrPipeTemplate will be reconstructed
    - A folder with a valid NmrPipe suffix and containing a series of numbered 2D planes with a valid
      NmrPipe suffix; e.g. matching *001.dat or *001.pipe or *001.ft3, etc
    """

    #=========================================================================================
    dataFormat = 'NMRPipe'
    # Conveniances; subclassed in the respective classes
    isNmrPipeSpectrum = True

    isBlocked = False
    wordSize = 4
    headerSize = 512
    blockHeaderSize = 0
    isFloatData = True
    MAXDIM = 4          # Explicitly overide as NmrPipe can only handle upto 4 dimensions

    suffixes = ['.pipe', '.fid', '.ft', '.ft1', '.ft2', '.ft3', '.ft4', '.dat']
    allowDirectory = True
    openMethod = open
    defaultOpenReadMode = 'rb'

    # nD multi-file template definitions
    _templates3D = '%04d %03d %02d'.split()
    #  4D digits      3+4       3_4       3+3       3_3     2+4       2_4      2+3       2_3
    _templates4D = '%03d%04d %03d_%04d %03d%03d %03d_%03d %02d%04d %02d_%04d %02d%03d %02d_%03d'.split()

    # File size to show warning (MB); used for loaded/displaying in relation to buffering
    WARNING_FILE_SIZE = 128.0

    #=========================================================================================

    nmrPipeTemplate = CString(allow_none=True, default_value=None).tag(
                                        info='The template to generate the path of the individual files comprising the nD',
                                       )
    nFiles = CInt(default_value=0).tag(
                                        info='The number of files comprising the nD',
                                       )
    baseDimensionality = CInt(default_value=2).tag(
                                        info='Dimensionality of the NmrPipe files comprising the nD',
                                       )
    isTransposed = Bool(default_value=False).tag(
                                        info='Data of underpinning NmrPipe files are transposed',
                                        )
    # _isDirectory = Bool(default_value=False).tag(
    #                                     info='Initiating path was a directory',
    #                                     )

    #=========================================================================================

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

        if self.isValid:
            # NmrPipe files are always buffered
            self.setBuffering(True, temporaryBuffer, bufferPath)

    def readParameters(self):
        """Read the parameters from the NmrPipe file header
        Returns self
        """
        logger = getLogger()

        self.setDefaultParameters()

        try:
            # Create NmrPipeHeader instance and read the data"
            if not self.hasOpenFile():
                self.openFile(mode=self.defaultOpenReadMode)
            self.header = NmrPipeHeader(self.headerSize, self.wordSize).read(self.fp, doSeek=True)
            self.isBigEndian = self.header.isBigEndian

            # First map the easy parameters from the NmrPipeHeader definitions to the DataSource definitions
            for parName, pipeName in [
                ('isTransposed', 'transposed'),
                ('nFiles', 'nFiles'),
                ('dimensionCount', 'dimensionCount'),
                ('dimensionOrder', 'dimensionOrder'),
                ('axisLabels', 'axisLabels'),
                ('spectrometerFrequencies', 'spectrometerFrequencies'),
                ('spectralWidthsHz', 'spectralWidthsHz'),
                ('referencePoints', 'referencePoints'),
                ('referenceValues', 'referenceValues'),
                ('phases0', 'phases0'),
                ('phases1', 'phases1'),
            ]:
                value = self.header.getParameterValue(pipeName)
                setattr(self, parName, value)

            # Now do the more complicated ones

            # map the domain types
            _domain = self.header.getParameterValue('domain')
            self.dimensionTypes = [domainMap.get(k, DIMENSION_FREQUENCY) for k in _domain ]

            # map the quad types
            _quadTypes = self.header.getParameterValue('quadType')
            self.dataTypes = [dataTypeMap.get(v, DATA_TYPE_REAL) for v in _quadTypes]
            self.isComplex = [v != DATA_TYPE_REAL for v in self.dataTypes]

            _pointCounts = self.header.getParameterValue('pointCounts')
            # correction for complex types required here
            if self.isComplex[specLib.X_AXIS]:
                _pointCounts[specLib.X_AXIS] *= 2

            if not self.isComplex[specLib.X_AXIS] and \
               self.dimensionTypes[specLib.X_AXIS] == DIMENSION_FREQUENCY and \
               self.isComplex[specLib.Y_AXIS]:
                    _pointCounts[specLib.Y_AXIS] *= 2

            self.pointCounts = _pointCounts

            # temperature
            if (_temp := self.header.getParameterValue('temperature')) == 0.0:
                self.temperature = None
            else:
                self.temperature = _temp

            # Pipe and NUS dimensions
            map1 = {1:specLib.X_DIM, 2:specLib.Y_DIM, 3:specLib.Z_DIM, 4:specLib.A_DIM, 0:None}
            self.pipeDimension = map1[self.header.getParameterValue('pipeDimension')]
            self.nusDimension = map1[self.header.getParameterValue('nusDimension')]

            # Fix isAcquisition for transposed data
            if self.dimensionCount >= 2 and self.isTransposed:
                _isAcquisition = [False] * self.MAXDIM
                _isAcquisition[1] = True
                self.isAcquisition = _isAcquisition

            self._guessTemplate()
            self._setBaseDimensionality()
            self.blockSizes = [1]*specLib.MAXDIM
            self.blockSizes[0:self.baseDimensionality] = self.pointCounts[0:self.baseDimensionality]

        except Exception as es:
            logger.error('Reading parameters; %s' % es)
            raise es

        # this will set isotopes, axiscodes, assures dimensionality
        super().readParameters()

        # fix possible acquisition axis code
        if self.isTransposed:
            self.acquisitionAxisCode = self.axisCodes[specLib.Y_DIM_INDEX]

        return self

    def _setBaseDimensionality(self):
        """Set the baseDimensionality depending on dimensionCount, nFiles and nmrPipeTemplate
        """
        if self.nFiles == 1:
            # 1D, 2D, nD's stored as a single file
            self.baseDimensionality = self.dimensionCount
        elif self.dimensionCount == 4 and self.nFiles > 1 and \
           self.nmrPipeTemplate is not None and self.nmrPipeTemplate.count('%') == 1:
            # 4D's stored as series of 3D's
            self.baseDimensionality = 3
        elif self.nFiles > 1:
            # The default; Multifile 3D/4D
            self.baseDimensionality = 2
        else:
            raise RuntimeError(f'Unable to establish baseDimensionality for {self}')

    def _checkTemplateOptions(self, templateOptions, fileName) -> list:
        """Using filename, check if any of the templateOptions match
        :return a list with possibilities, where fileName is substituted with template
        """
        # Example from previous code
        # 3D's stored as series of 2D's
        # templates = (re.sub('\d\d\d\d', '%04d', fileName),
        #              re.sub('\d\d\d',   '%03d', fileName),
        #              re.sub('\d\d',     '%02d', fileName),
        # )

        result = []
        for _tmpl in templateOptions:
            # make a subsitution pattern (eg. \d\d\d) for re.sub,
            # using the the 3D template definition (_tmpl) and the value(s) 0
            if _tmpl.count('%') == 1:
                _valueStr = _tmpl % (0,)
            elif _tmpl.count('%') == 2:
                _valueStr = _tmpl % (0,0)
            else:
                raise RuntimeError(f'Invalid template option "{_tmpl}"')
            _pat = ''.join([s if s != '0' else f'\d' for s in _valueStr ])
            # use the pattern and the 3D template definition to create an NmrPipe
            # template from fileName
            template, _nSubs = re.subn(_pat, _tmpl, fileName)
            # check if we made a subsititution; zero: not doen; 1: done; >1: error
            if _nSubs == 0:
                pass
            elif _nSubs == 1:
                result.append(template)
            else:
                getLogger().debug(f'Guessing template from "{fileName}" yielded "{template}"')
        return result

    def _guessTemplate(self):
        """Guess the nmrPipeTemplate based on self.path and dimensionality
        """
        directory, fileName, suffix = self.path.split3()

        self.nmrPipeTemplate = None

        if self.dimensionCount == 2:
            pass

        elif self.dimensionCount in [3,4] and self.nFiles == 1:
            pass

        elif self.dimensionCount == 3 and self.nFiles > 1:

            templates = self._checkTemplateOptions(self._templates3D, fileName)
            if len(templates) == 0:
                raise RuntimeError(f'Unable to guess template from "{fileName}"')

            # Using the templates, check if we can find the last 3D file of the series
            # For the 3D's, the first template should be the correct one
            template = templates[0]
            path = Path(directory) / (template % self.pointCounts[specLib.Z_DIM_INDEX]) + suffix
            if path.exists():
                self.nmrPipeTemplate = str(Path(directory) / (template) + suffix)
            else:
                self.shouldBeValid = True
                self.isValid = False
                self.errorString = f'{self};\nExpected path "{path}" not found'

        elif self.dimensionCount == 4 and self.nFiles > 1:
            # 4D's stored as series of 2D's or
            # 4D's stored as series of 3D's

            templates = self._checkTemplateOptions(self._templates4D, fileName) + \
                        self._checkTemplateOptions(self._templates3D, fileName)
            if len(templates) == 0:
                raise RuntimeError(f'Unable to guess template from "{fileName}"')

            # For the 4D's, there are multiple template that could be the correct one
            _zPoint = self.pointCounts[specLib.Z_DIM_INDEX]
            _aPoint = self.pointCounts[specLib.A_DIM_INDEX]
            found = False
            for template in templates:
                if template.count('%') == 2:
                    path = Path(directory) / (template % (_aPoint, _zPoint)) + suffix
                elif template.count('%') == 1:
                    path = Path(directory) / (template % self.pointCounts[specLib.A_DIM_INDEX]) + suffix
                else:
                    raise RuntimeError(f'Invalid template "{template}"')

                if path.exists():
                    self.nmrPipeTemplate = str(Path(directory) / (template) + suffix)
                    found = True
                    break

            if not found:
                self.shouldBeValid = True
                self.isValid = False
                self.errorString = f'{self};\nFile for Z,A = {(_zPoint, _aPoint)} not found while trying NmrPipe templates {templates}'

        else:
            getLogger().debug(f'NmrPipeSpectrumDataSource._guessTemplate: Unable to guess from "{self.path}", '\
                              f'dimensionCount={self.dimensionCount}; nFiles={self.nFiles}' )

    def _getPathAndOffset(self, position):
        """Construct path of NmrPipe file corresponding to position (1-based) from nmrPipeTemplate
        :return aPath instance of path and offset (in bytes) as a tuple
        """
        if self.dimensionCount <= 2:
            # single file 1D/2D
            path = self.path
            offset = self.headerSize * self.wordSize

        elif self.dimensionCount == 3 and self.nFiles == 1:
            # single-file 3D
            path = self.path
            offset = ( self.headerSize + \
                      (position[specLib.Z_DIM_INDEX]-1) * self.pointCounts[specLib.X_DIM_INDEX] \
                                                        * self.pointCounts[specLib.Y_DIM_INDEX] \
                     ) * self.wordSize

        elif self.dimensionCount == 3 and self.baseDimensionality == 2:
            # regular multi-file 3D
            if self.nmrPipeTemplate is None:
                raise RuntimeError('%s: Undefined nmrPipeTemplate' % self)
            path = self.nmrPipeTemplate % (position[specLib.Z_DIM_INDEX],)
            offset = self.headerSize * self.wordSize

        elif self.dimensionCount == 4 and self.nFiles == 1:
            # Single-file 4D
            path = self.path
            offset = ( self.headerSize + \
                      (position[specLib.Z_DIM_INDEX]-1) * self.pointCounts[specLib.X_DIM_INDEX] \
                                                        * self.pointCounts[specLib.Y_DIM_INDEX] + \
                      (position[specLib.A_DIM_INDEX]-1) * self.pointCounts[specLib.X_DIM_INDEX]  \
                                                        * self.pointCounts[specLib.Y_DIM_INDEX]  \
                                                        * self.pointCounts[specLib.Z_DIM_INDEX]  \
                     ) * self.wordSize

        elif self.dimensionCount == 4 and self.baseDimensionality == 2:
            # regular multi-file 4D
            if self.nmrPipeTemplate is None:
                raise RuntimeError('%s: Undefined nmrPipeTemplate' % self)
            path = self.nmrPipeTemplate % (position[specLib.A_DIM_INDEX], position[specLib.Z_DIM_INDEX])
            offset = self.headerSize * self.wordSize

        elif self.dimensionCount == 4 and self.baseDimensionality == 3:
            # multi-file 4D; 3D base dimensionality
            if self.nmrPipeTemplate is None:
                raise RuntimeError('%s: Undefined nmrPipeTemplate' % self)
            path = self.nmrPipeTemplate % (position[specLib.A_DIM_INDEX],)
            offset = ( self.headerSize + \
                      (position[specLib.X_DIM_INDEX]-1) * self.pointCounts[specLib.X_DIM_INDEX] * self.pointCounts[specLib.Y_DIM_INDEX]
                     ) * self.wordSize
        else:
            # Undefined; raise error
            raise RuntimeError('%s: Unable to construct path for position %s' % (self, position))
        path = aPath(path)

        return path, offset

    def setPath(self, path, checkSuffix=False):
        """define valid path to a (binary) data file, if needed appends or substitutes
        the suffix (if defined).

        :param path: See class doc-string for valid paths
        :param checkSuffix: flag to check the suffix
        :return self or None on error
        """
        if path is None:
            self.dataFile = None  # A reset essentially
            return super().setPath(None)

        _path = aPath(path)
        self._path = _path  # retain the initiating path
        self._isDirectory = _path.is_dir()

        if not self._isDirectory:
            self._binaryFile = _path
            return super().setPath(path=_path, checkSuffix=checkSuffix)

        elif self._isDirectory and _path.suffix in self.suffixes:
            # try to establish if this is a directory with a NmrPipe series of files
            self._binaryFile = None
            for _suffix in self.suffixes:
                pattern = f'*001{_suffix}'
                files = _path.globList(pattern)
                if len(files) > 0:
                    _path = files[0]  # define the first binary
                    self._binaryFile = _path
                    return super().setPath(path=_path, checkSuffix=checkSuffix)

            # Once here: did not find a "001" file
            self.isValid = False
            self.errorString = f'setPath: Failed to find an NmrPipe "001" file in directory {_path}'
            return None

        else:
            self.isValid = False
            self._binaryFile = None
            self .errorString = f'setPath: Invalid path "{_path}"; does not conform to NmrPipe definitions'
            return None

    def getAllFilePaths(self) -> list:
        """
        Get all the files handled by this dataSource: the binary and a parameter file.

        :return: list of Path instances
        """

        if self.nFiles == 0:
            raise RuntimeError(f'DataSource {self.dataFormat}: nFiles = 0')
        elif self.nFiles == 1:
            result = [self.path]
        else:
            # nD's: get all the nmrPipe files
            sliceTuples = [(1, p) for p in self.pointCounts]

            result = []
            # loop over all the xy-planes
            for position, aliased in self._selectedPointsIterator(sliceTuples, excludeDimensions=(specLib.X_DIM, specLib.Y_DIM)):
                path, offset = self._getPathAndOffset(position)
                result.append(path)

            # remove any duplicates
            result = list(set(result))

        return result

    def copyFiles(self, destinationDirectory, overwrite=False) -> list:
        """Copy all data files to a new destination directory
        :param destinationDirectory: a string or Path instance defining the destination directory
        :param overwrite: Overwrite any existing files
        :return A list of files copied
        """
        _destination = aPath(destinationDirectory)
        if not _destination.is_dir():
            raise ValueError(f'"{_destination}" is not a valid directory')

        if self._isDirectory:
            # A directory; create the same in the destination
            # self._path contains the originating path
            _dir, _base, _suffix = self._path.split3()
            _destination = _destination / _base + _suffix
            result = [self._path.copyDir(_destination, overwrite=overwrite)]

        elif self.nFiles > 1:
            # More than one file; i.e. a multi-file 3D or 4D.
            # Put in a single new directory within destinationDirectory with name from path and 'pipe' suffix
            _destination = _destination.fetchDir(self.nameFromPath() + self.suffixes[0])
            super().copyFiles(destinationDirectory=_destination, overwrite=overwrite)
            result = [_destination]

        else:
            # effectively the one-file situation; call super class to handle.
            result = super().copyFiles(destinationDirectory=destinationDirectory, overwrite=overwrite)

        return result

    def nameFromPath(self) -> str:
        """Return a name derived from self._path)
        """
        if self._path is None:
            raise RuntimeError(f'nameFromPath: undefined path')
        name = self._path.parent.stem if self._isDirectory else self._path.stem
        return name

    def checkValid(self) -> bool:
        """check if valid format corresponding to dataFormat by:
        - checking nmrPipeTemplate and binary files are defined

        call super class for:
        - checking suffix and existence of path
        - reading (and checking dimensionCount) parameters

        :return: True if ok, False otherwise
        """
        if not self.isValid:
            # An earlier error occurred
            return False

        if not super().checkValid():
            return False

        self.shouldBeValid = True
        if self.dimensionCount > 2 and self.nFiles > 1 and self.nmrPipeTemplate is None:
            errorMsg = f'No NmrPipe template defined, in spite of {self.nFiles} files comprising the {self.dimensionCount}D data'
            return self._returnFalse(errorMsg)

        # Check if all planes are present
        if self.nFiles > 0:
            sliceTuples = [(1, p) for p in self.pointCounts]
            missing = []
            for position, _tmp in self._selectedPointsIterator(sliceTuples, excludeDimensions=[specLib.X_DIM, specLib.Y_DIM]):
                _path, _tmp = self._getPathAndOffset(position)
                if not _path.exists():
                    missing.append(_path.name)
            if len(missing):
                getLogger().debug(f'Missing NmrPipe files: {missing}')
                return self._returnFalse(f'Missing {len(missing)} NmrPipe files for {self.nmrPipeTemplate}')

        return True

    def _unshuffleComplex(self, position, data):
        """Helper function for fillHdf5Buffer() method to unshuffle the (complex) data,
        obtained reading an XY-plane (data) while filling the buffer.
        :param position: a position tuple (1-based)
        :param data: a PlaneData (2D numpy array) object containing the xy data
        :return (writePosition, writeData) tuple
        """

        # First make a copy of the position tuple and see if changes are requires
        writePosition = [p for p in position]
        writeData = data

        # In a NmrPipe 2D xy plane:
        # - A complex X-axis has n real points followed by n imaginary points (nRnI)
        # - A complex Y-axis has n alternating real, imag points (nRI)
        if self.dimensionCount >= 2 and self.isComplex[specLib.Y_AXIS]:
            # sort the n-RI data point into nRnI data points
            totalSize = self.pointCounts[specLib.Y_AXIS]
            realSize = self.realPointCounts[specLib.Y_AXIS]
            writeData = numpy.empty(shape=data.shape)
            _realData = data[0::2,:]  # The real points
            _imagData = data[1::2,:]  # The imag points
            writeData[0:realSize, :] = _realData
            writeData[realSize:totalSize, :] = _imagData
            self.dataTypes[specLib.Y_AXIS] = specLib.DATA_TYPE_COMPLEX_nRnI

        # For the Z,A dimensions:
        # - the complex Z,A-axes have n alternating real, imag points (nRI)
        if self.dimensionCount >= 3 and self.isComplex[specLib.Z_AXIS]:
            # adjust the Z-position to nRnI ordering
            zP = writePosition[specLib.Z_AXIS] - 1  # convert to zero-based
            if zP % 2:
                # imaginary point
                zP = zP // 2 + self.realPointCounts[specLib.Z_AXIS]
            else:
                # real point
                zP = zP // 2
            writePosition[specLib.Z_AXIS] = zP + 1 # convert to one-based
            self.dataTypes[specLib.Z_AXIS] = specLib.DATA_TYPE_COMPLEX_nRnI

        if self.dimensionCount >= 4 and self.isComplex[specLib.A_AXIS]:
            # adjust the A-position to nRnI ordering
            aP = writePosition[specLib.A_AXIS] - 1  # convert to zero-based
            if aP % 2:
                # imaginary point
                aP = aP // 2 + self.realPointCounts[specLib.A_AXIS]
            else:
                # real point
                aP = aP // 2
            writePosition[specLib.A_AXIS] = aP + 1 # convert to one-based
            self.dataTypes[specLib.A_AXIS] = specLib.DATA_TYPE_COMPLEX_nRnI

        return writePosition, writeData

    def _bufferXYplane(self, position, fp, hdf5buffer):
        """Helper function for fillHdf5Buffer() method.
        Read an XY-plane and store in the hdf5 buffer.
        :param position: a position tuple (1-based)
        :param fp: file pointer
        :param hdf5buffer: Hdf5SpectrumData instance acting as buffer
        :return (writePosition, writeData) tuple
        """
        planeSize = self.pointCounts[specLib.X_DIM_INDEX] * self.pointCounts[specLib.Y_DIM_INDEX]
        _tmp, offset = self._getPathAndOffset(position)
        fp.seek(offset, 0)
        data = numpy.fromfile(file=fp, dtype=self.dtype, count=planeSize)
        data.resize( (self.pointCounts[specLib.Y_DIM_INDEX], self.pointCounts[specLib.X_DIM_INDEX]))

        writePosition, writeData = self._unshuffleComplex(position, data)
        hdf5buffer.setPlaneData(writeData, position=writePosition, xDim=specLib.X_DIM, yDim=specLib.Y_DIM)

        return writePosition, writeData

    def fillHdf5Buffer(self):
        """Fill hdf5buffer with data from self
        """
        if not self.isBuffered:
            raise RuntimeError('fillHdf5Buffer: no hdf5Buffer defined')

        getLogger().debug('fillHdf5Buffer: filling buffer %s' % self.hdf5buffer)

        # just some definitions
        xAxis = specLib.X_DIM_INDEX
        xDim = specLib.X_DIM
        yAxis = specLib.Y_DIM_INDEX
        yDim = specLib.Y_DIM

        if self.dimensionCount == 1:
            # 1D
            position = [1]
            path, offset = self._getPathAndOffset(position)
            with open(path, 'r') as fp:
                fp.seek(offset, 0)
                data = numpy.fromfile(file=fp, dtype=self.dtype, count=self.pointCounts[xAxis])
            self.hdf5buffer.setSliceData(data, position=position, sliceDim=xDim)

        elif self.dimensionCount == 2:
            # 2D
            position = [1,1]
            path, offset = self._getPathAndOffset(position)
            with open(path, 'r') as fp:
                self._bufferXYplane(position, fp, self.hdf5buffer)

        # 3D/4D's: fill the buffer, reading x,y planes from the nmrPipe files into the hdf5 buffer
        elif self.dimensionCount > 2 and self.nFiles == 1:
            # single-file 3D/4D
            # special case the situation to avoid closing/opening same file
            sliceTuples = [(1, p) for p in self.pointCounts]
            with open(self.path, 'r') as fp:
                for position, aliased in self._selectedPointsIterator(sliceTuples, excludeDimensions=(xDim, yDim)):
                    self._bufferXYplane(position, fp, self.hdf5buffer)

        elif self.dimensionCount > 2 and self.nFiles > 1:
            # Multi-file 3D/4D
            sliceTuples = [(1, p) for p in self.pointCounts]
            for position, aliased in self._selectedPointsIterator(sliceTuples, excludeDimensions=(xDim, yDim)):
                path, _tmp = self._getPathAndOffset(position)
                with open(path, 'r') as fp:
                    self._bufferXYplane(position, fp, self.hdf5buffer)

        else:
            raise RuntimeError(f'Error filling Hdf5 buffer for {self}')

        self._bufferFilled = True

    def estimateNoise(self) -> float:
        """Estimate and return a noise level
        Use mean of abs of dataPlane or dataSlice;
        subclassed to prevent buffer loading on first incorpartion into the project
        """

        if self.dimensionCount == 1 or self.dimensionCount == 2 or self.bufferIsFilled:
            # 1D/2D, or if buffer is filled
            return super().estimateNoise()

        else:
            # 3D and up: use a xy-plane, 10 planes in
            position = [1, 1, min(10, self.pointCounts[2]), 1] [0:self.dimensionCount]
            path, offset = self._getPathAndOffset(position)
            with open(path, 'r') as fp:
                fp.seek(offset, 0)
                planeSize = self.pointCounts[specLib.X_DIM_INDEX]*self.pointCounts[specLib.Y_DIM_INDEX]
                data = numpy.fromfile(file=fp, dtype=self.dtype, count=planeSize)

            data = data.flatten()
            stdFactor = 2.0

            absData = numpy.array([v for v in map(abs, data)])
            absData = absData[numpy.isfinite(absData)]
            median = numpy.median(absData)
            _temp = data[numpy.isfinite(data)].astype(numpy.float64)
            std = numpy.std(_temp)
            if std != std:
                # std may still be nan because contains HUGE numbers
                std = 0
            noiseLevel = median + stdFactor * std
            self.noiseLevel = noiseLevel

            return noiseLevel

# Register this format
NmrPipeSpectrumDataSource._registerFormat()


class NmrPipeInputStreamDataSource(NmrPipeSpectrumDataSource):
    """
    NmrPipe spectral storage, reading from an stdinp stream
    """
    def __init__(self, spectrum=None, temporaryBuffer=True, bufferPath=None):
        """Initialise; optionally set path or extract from spectrum

        :param spectrum: associate instance with spectrum and import spectrum's parameters
        :param temporaryBuffer: used temporary file to buffer the data
        :param bufferPath: (optionally) use path to generate buffer file (implies temporaryBuffer=False)
        """
        super().__init__(spectrum=spectrum, temporaryBuffer=temporaryBuffer, bufferPath=bufferPath)
        # sys.stdin.reconfigure(encoding='ISO-8859-1')
        self.fp = sys.stdin.buffer
        self.readParameters()
        self.openHdf5Buffer(bufferIsTemporary=temporaryBuffer, bufferPath=bufferPath)
        self.fillHdf5Buffer()

    def _readHeader(self):
        "Create NmrPipeHeader instance and read the data"
        self.header = NmrPipeHeader(self.headerSize, self.wordSize).read(self.fp, doSeek=False)

    def _guessTemplate(self):
        "Guess nmrPipeTemplate not active/required for input stream"
        return None

    def fillHdf5Buffer(self, hdf5buffer):
        """Fill hdf5 buffer reading all slices from input stream
        """
        if not self.isBuffered:
            raise RuntimeError('fillHdf5Buffer: no hdf5Buffer defined')

        sliceDim = self.pipeDimension
        if sliceDim is None:
            raise RuntimeError('%s.fillHdf5Buffer: undefined dimension of the input stream')

        getLogger().debug('fillHdf5Buffer from sys.stdin reading %d slices along dimension %s' %
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
