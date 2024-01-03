"""
This file contains the Bruker data access class
it serves as an interface between the V3 Spectrum class and the actual spectral data
Some routines rely on code from the Nmrglue package, included in the miniconda distribution

See SpectrumDataSourceABC for a description of the attributes and methods
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Joanna Fox, Morgan Hayward, Victoria A Higman, Luca Mureddu",
               "Eliza Płoskoń, Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2024-01-03 16:37:07 +0000 (Wed, January 03, 2024) $"
__version__ = "$Revision: 3.2.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2020-11-20 10:28:48 +0000 (Fri, November 20, 2020) $"

#=========================================================================================
# Start of code
#=========================================================================================

from difflib import get_close_matches
from itertools import permutations, combinations_with_replacement

from ccpn.util.Path import Path, aPath
from ccpn.util.Logging import getLogger
from ccpn.util.Common import flatten
from ccpn.util.traits.CcpNmrTraits import CPath
from ccpn.util.isotopes import DEFAULT_ISOTOPE_DICT
import ccpn.core.lib.SpectrumLib as specLib
from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import SpectrumDataSourceABC
from ccpn.framework.constants import NO_SUFFIX


def _findClosestMatch(input_string, string_list):
    # Set the number of desired matches (1 in this case, the closest match)
    num_matches = 1

    # Use get_close_matches to find the closest match
    closest_match = get_close_matches(input_string, string_list, n=num_matches, cutoff=0.01)

    # If a match is found, return it; otherwise, return None
    return closest_match[0] if closest_match else None


def _makeBrukerFileNames(dimensionCount) -> tuple:
    """helper function to constucts all possible bruker filenames for dimensionCount
    :return list with the names
    """
    _first = combinations_with_replacement('ri', dimensionCount)

    # we still need to permute the _first expansion
    _second = []
    for _n in _first:
        _second.extend(permutations(_n))

    # remove the duplicates
    _names = list(set(_second))
    _names.sort()

    # create in reverse order so that 'rrr' comes first
    return tuple(f'{dimensionCount}' + ''.join(_n) for _n in _names[::-1])


class BrukerSpectrumDataSource(SpectrumDataSourceABC):
    """
    Bruker binary nD (n=1-8) spectral data reading
    Initialization can be from:
    - a directory with Bruker data (No-suffix)
    - a directory with Bruker processed data (pdata/x)
    - Bruker processed data file, e.g. 1r, 2rr, etc
    """
    dataFormat = 'Bruker'

    isBlocked = True
    wordSize = 4
    headerSize = 0
    blockHeaderSize = 0
    isFloatData = False

    suffixes = [NO_SUFFIX]
    allowDirectory = True  # Can supply a Bruker top directory or pdata directory
    openMethod = open
    defaultOpenReadMode = 'rb'

    #=========================================================================================

    _processedDataFilesDict = dict([
        (1, '1r 1i'.split()),
        (2, '2rr 2ri 2ir 2ii'.split()),
        (3, _makeBrukerFileNames(3)),
        (4, _makeBrukerFileNames(4)),
        (5, _makeBrukerFileNames(5)),
        (6, _makeBrukerFileNames(6)),
        (7, _makeBrukerFileNames(7)),
        (8, _makeBrukerFileNames(8)),
        ])
    _processedDataFiles = [f for f in
                           flatten(_processedDataFilesDict.values())]  # all the possible processed data files as a list
    _acqusFiles = 'acqus acqu2s acqu3s acqu4s acqu5s acqu6s acqu7s acqu8s'.split()
    _procFiles = 'procs proc2s proc3s proc4s proc5s proc6s proc7s proc8s'.split()
    _PDATA = 'pdata'

    termDict = {'AQ'         : 'acquisition time in seconds',
                'AMP'        : 'amplitude of pulses',
                'AQ_mod'     : 'acquisition mode',
                'AQSEQ'      : '3D acquisition order',
                'AUNM'       : 'name of an acquisition AU program',
                'BF(1-8)'    : 'basic frequency for frequency channel f(1-8)',
                'BYTORDP'    : 'Byte order (endianness)',
                'CNST'       : 'constant used in pulse programs',
                'CPDPRG(1-8)': 'names of CPD programs',
                'D'          : 'time delays',
                'DDR'        : 'digital digitizer resolution',
                'DE'         : 'pre-scan delay',
                'DECIM'      : 'decimation factor of the digital filter',
                'DIGMOD'     : 'digitizer mode',
                'DIGTYP'     : 'digitizer type',
                'DQDMODE'    : 'sign of the frequency shift during digital quadrature detection',
                'DR'         : 'digitizer resolution',
                'DS'         : 'number of dummy scans',
                'DSLIST'     : 'dataset list',
                'DSPFIRM'    : 'firmware used for digital filtering',
                'DW'         : 'dwell time',
                'DWOV'       : 'oversampling dwell time',
                'EXP'        : 'experiment performed',
                'FCUCHAN'    : 'routing between logical frequency channels and FCU s',
                'FnMODE'     : 'Acquisition mode of the indirect dimensions (2D and 3D)',
                'FW'         : 'analog filter width',
                'FIDRES'     : 'FID resolution',
                'FQ1LIST'    : 'irradiation frequency lists',
                'GP031'      : 'gradient parameter table',
                'GRDPROG'    : 'gradient program name',
                'HDDUTY'     : 'homodecoupling duty cycle (in percent)',
                'HPMOD'      : 'routing between high power amplifiers and preamplifier modules',
                'HPPRGN'     : 'high power preamplifier gain',
                'INP'        : 'increment for pulse P',
                'IN'         : 'increment for delay D',
                'L'          : 'loop counter',
                'LOCNUC'     : 'lock nucleus',
                'MASR'       : 'MAS spin rate',
                'NBL'        : 'number of blocks (of acquisition memory)',
                'ND0'        : 'number of delays D0',
                'ND10'       : 'number of delays D10',
                'NS'         : 'number of scans',
                'NUC(1-8)'   : 'nucleus for frequency channel f(1-8)',
                'O(1-8)'     : 'irradiation frequency offset for frequency channel f(1-8) in Hz',
                'O(1-8)P'    : 'irradiation frequency offset for frequency channel f(1-8) in ppm',
                'OVERFLW'    : 'data overflow check',
                'P'          : 'pulse length',
                'PARMODE'    : 'dimensionality of the raw data',
                'PHCOR'      : 'correction angle for phase programs',
                'PCPD'       : 'CPD pulse length',
                'PH_ref'     : 'receiver phase correction',
                'PL'         : 'power level',
                'POWMOD'     : 'power mode',
                'PRECHAN'    : 'routing between Switchbox outputs and Preamplifier modules',
                'PROSOL'     : 'copy prosol parameters to corresponding acquisition parameters',
                'PRGAIN'     : 'high power preamplifier gain',
                'PULPROG'    : 'pulse program used for the acquisition',
                'QNP'        : 'QNP nucleus selection',
                'RECCHAN'    : 'receiver channel',
                'RG'         : 'receiver gain',
                'RO'         : 'sample rotation frequency in Hz',
                'RSEL'       : 'routing between FCU s and amplifiers',
                'SEOUT'      : 'SE 451 receiver unit output to be used',
                'SFO(1-8)'   : 'irradiation (carrier) frequencies for channel f(1-8)',
                'SP07'       : 'shaped pulse parameter table',
                'SOLVENT'    : 'the sample solvent',
                'SW'         : 'spectral width in ppm',
                'SW_h'       : 'spectral width in Hz',
                'SWIBOX'     : 'routing between Switchbox inputs and Switchbox outputs',
                'TD'         : 'time domain; number of raw data points',
                'TD0'        : 'loop counter for multidimensional experiments',
                'TE'         : 'demand temperature on the temperature unit',
                'V9'         : 'maximum variation of a delay',
                'VALIST'     : 'variable amplitude (power) list',
                'VCLIST'     : 'variable counter list',
                'VDLIST'     : 'variable delay list',
                'VPLIST'     : 'variable pulse list',
                'VTLIST'     : 'variable temperature list',
                'WBST'       : 'number of wobble steps',
                'WBSW'       : 'wobble sweep width',
                'ZGOPTNS'    : 'acquisition (zg) options',
                }

    #=========================================================================================

    _brukerRoot = CPath(default_value=None, allow_none=True).tag(info=
                                                                 'an attribute to store the path to the Bruker root directory; used during parsing'
                                                                 )
    _pdataDir = CPath(default_value=None, allow_none=True).tag(info=
                                                               'an attribute to store the path to the Bruker pdata directory; used during parsing'
                                                               )

    #=========================================================================================

    def __init__(self, path=None, spectrum=None, dimensionCount=None):
        """Init local attributes
        """

        self.acqus = None  # list of parsed acqus files (per dimension)
        self.procs = None  # list of parsed proc files (per dimension)

        super().__init__(path=path, spectrum=spectrum, dimensionCount=dimensionCount)

    def _isBrukerTopDir(self, path):
        """Return True if path (of type Path) is a Bruker top directory with a pdata directory or acqu* files
        """
        hasAcquFiles = len(path.globList('acqu*')) > 0
        pdata = path / self._PDATA
        return path is not None and path.exists() and path.is_dir() and \
            ((pdata.exists() and pdata.is_dir()) or hasAcquFiles)

    @staticmethod
    def _hasBinaryData(path) -> bool:
        """Return True if path contains  bruker binary data
        """
        if path is None:
            return False
        _binaryData = path.globList('[1-8][r,i]*')
        return len(_binaryData) > 0

    def _getBinaryFile(self):
        """:returns binary-data file in self._pdataDir as a Path instance or None if none present
        """
        if self._pdataDir is None:
            return None

        if len(self._pdataDir.globList('proc*')) == 0:
            return None

        if not self._hasBinaryData(self._pdataDir):
            return None

        dimensionality = self._getDimensionality()
        if dimensionality not in self._processedDataFilesDict:
            return None

        return self._pdataDir / self._processedDataFilesDict[dimensionality][0]

    def _isBrukerPdataDir(self, path):
        """Return True if path (of type Path) is a Bruker pdata directory with
        proc files and/or binary files
        """
        if path is None:
            return False
        hasProcFiles = len(path.globList('proc*')) > 0
        hasBrukerTopdir = self._isBrukerTopDir(path.parent.parent)
        isPdata = path.parent.stem == self._PDATA
        return path.exists() and path.is_dir() and isPdata and hasBrukerTopdir and \
            (hasProcFiles or self._hasBinaryData(path))

    def _getDimensionality(self):
        """Return dimensionality from proc files in self._pdataDir
        """
        dimensionality = 0
        for proc in self._procFiles:
            _p = self._pdataDir / proc
            if not _p.exists():
                break
            dimensionality += 1
        return dimensionality

    def _findFirstPdataDir(self):
        """Find and return first pdata subdir with valid data, starting from Bruker topDir
        :return path of valid pdata 'proc'-directory or None if not found
        """
        if self._brukerRoot is None:
            return None

        _pdata = self._brukerRoot / self._PDATA
        if not _pdata.exists():
            return None

        _procDirs = []
        # add numeric proc dirs only; to sort later
        for p in _pdata.globList('[1-9]*'):
            try:
                _procDirs.append(int(p.basename))
            except:
                pass
        _procDirs.sort(key=int)
        if len(_procDirs) == 0:
            return None

        for p in _procDirs:
            _path = _pdata / str(p)
            if self._hasBinaryData(_path):
                return _path
        return None

    def _findFistProcFile(self):
        """Find the first proc file in self._pDataDir
        :return Path to this file or None if it does not exist
        """
        if self._pdataDir is None or not self._pdataDir.exists():
            return None
        else:
            return self._pdataDir / self._procFiles[0]

    def nameFromPath(self):
        """Return a name derived from _brukerRoot and pdataDir
        Subclassed to accommodate the special Bruker directory structure
        """
        return '%s-%s' % (self._brukerRoot.stem, self._pdataDir.stem)

    @property
    def parentPath(self) -> aPath:
        """Return an absolute path of parent directory, i.e. _BrukerRoot, as a Path instance
        or None when dataFile is not defined.
        Subclassed to accommodate the special Bruker directory structure
        """
        return (None if self.dataFile is None else self._brukerRoot.parent)

    def getAllFilePaths(self) -> list:
        """
        Get all the files handled by this dataSource: the binary and
        acqu* and proc* parameter files.

        :return: list of Path instances
        """
        result = [self.path]

        # acqu files
        for _p in self._acqusFiles[0:self.dimensionCount]:
            result.append(self._brukerRoot / _p)

        # proc files:
        for _p in self._procFiles[0:self.dimensionCount]:
            result.append(self._pdataDir / _p)
        return result

    def copyFiles(self, destinationDirectory, overwrite=False) -> list:
        """Copy all data files to a new destination directory
        :param destinationDirectory: a string or Path instance defining the destination directory
        :param overwrite: Overwrite any existing files
        :return A list of files/directory copied
        """
        _destination = aPath(destinationDirectory)
        if not _destination.is_dir():
            raise ValueError(f'"{_destination}" is not a valid directory')

        _dir, _base, _suffix = self._brukerRoot.split3()
        result = self._brukerRoot.copyDir(_destination / _base, overwrite=overwrite)
        return [result]

    def setPath(self, path, checkSuffix=False):
        """Parse and set path, assure there is the directory with acqus and pdata dirs
        set the _brukerRoot and _pdataDir attributes to point to the relevant directories

        Return self or None on error
        """

        logger = getLogger()

        self._pdataDir = None
        self._brukerRoot = None
        self._binaryFile = None
        self._parameterFile = None
        self._path = None

        if path is None:
            _path = None
            self._path = None

        else:
            _path = Path(path)
            self._path = _path

            if _path.is_file() and _path.stem in self._processedDataFiles:
                # Bruker binary processed data file
                self._brukerRoot = _path.parent.parent.parent
                self._pdataDir = _path.parent
                self._binaryFile = _path
                self._parameterFile = self._findFistProcFile()
                # We should have a valid Bruker file.
                self.shouldBeValid = True

            elif _path.is_file() and _path.stem in self._procFiles and self._isBrukerPdataDir(_path.parent):
                # Bruker proc file
                self._brukerRoot = _path.parent.parent.parent
                self._pdataDir = _path.parent
                self._binaryFile = self._getBinaryFile()
                self._parameterFile = self._findFistProcFile()
                # We should have a valid Bruker file.
                self.shouldBeValid = True

            elif self._isBrukerTopDir(_path):
                # Bruker top directory
                self._brukerRoot = _path
                self._pdataDir = self._findFirstPdataDir()
                self._binaryFile = self._getBinaryFile()
                self._parameterFile = self._findFistProcFile()
                # We should have a valid Bruker file.
                self.shouldBeValid = True

            elif _path.is_dir() and _path.stem == self._PDATA and self._isBrukerTopDir(_path.parent):
                # Bruker/pdata directory
                self._brukerRoot = _path.parent
                self._pdataDir = self._findFirstPdataDir()
                self._binaryFile = self._getBinaryFile()
                self._parameterFile = self._findFistProcFile()
                # We should have a valid Bruker file.
                self.shouldBeValid = True

            elif self._isBrukerPdataDir(_path) and self._isBrukerTopDir(_path.parent.parent):
                # Bruker pdata 'proc'-directory
                self._brukerRoot = _path.parent.parent
                self._pdataDir = _path
                self._binaryFile = self._getBinaryFile()
                self._parameterFile = self._findFistProcFile()
                # We should have a valid Bruker file.
                self.shouldBeValid = True

            else:
                # We do not have a valid Bruker file.
                txt = f'"{path}" does not define a valid path with Bruker data'
                logger.debug2(txt)
                self.errorString = txt
                self.shouldBeValid = False
                return None

        return super().setPath(self._binaryFile, checkSuffix=False)

    def checkValid(self) -> bool:
        """check if valid format corresponding to dataFormat by:
        - checking directories are defined
        - checking bruker Topdir
        - checking pdata dir

        call super class for:
        - checking suffix and existence of path
        - reading (and checking dimensionCount) parameters

        :return: True if ok, False otherwise
        """

        self.isValid = False
        self.errorString = 'Checking validity'

        # if self._path is None or not self._path.exists():
        #     errorMsg = f'Path "{self._path}" does not exist'
        #     return self._returnFalse(errorMsg)

        # checking Bruker topdir
        if self._brukerRoot is None:
            errorMsg = 'Bruker top directory is undefined'
            return self._returnFalse(errorMsg)

        if not self._brukerRoot.exists():
            errorMsg = f'Bruker top directory "{self._brukerRoot}" does not exist'
            return self._returnFalse(errorMsg)

        if not self._brukerRoot.is_dir():
            errorMsg = f'Bruker top directory "{self._brukerRoot}" is not a directory'
            return self._returnFalse(errorMsg)

        pdata = self._brukerRoot / self._PDATA
        if not pdata.exists() or not pdata.is_dir():
            errorMsg = f'Bruker top directory "{self._brukerRoot}" has no valid pdata directory'
            return self._returnFalse(errorMsg)

        hasAcquFiles = len(self._brukerRoot.globList('acqu*')) > 0
        if not hasAcquFiles:
            errorMsg = f'Bruker top directory "{self._brukerRoot}" has no acqu* files'
            return self._returnFalse(errorMsg)

        if self._pdataDir is None or not self._pdataDir.exists():
            errorMsg = 'No valid Bruker pdata/n (n=[1,..]) directory with (binary, proc) data'
            return self._returnFalse(errorMsg)

        if not self._pdataDir.is_dir():
            errorMsg = f'Bruker pdata "{self._pdataDir}" is not a directory'
            return self._returnFalse(errorMsg)

        hasProcFiles = len(self._pdataDir.globList('proc*')) > 0
        if not hasProcFiles:
            errorMsg = f'Bruker pdata "{self._pdataDir}" has no proc* files'
            return self._returnFalse(errorMsg)

        if not self._checkValidExtra():
            return False

        self.isValid = True
        self.errorString = ''
        return super(BrukerSpectrumDataSource, self).checkValid()

    def readParameters(self):
        """Read the parameters from the Bruker directory
        Returns self
        """
        logger = getLogger()

        self.setDefaultParameters()

        _dimensionCount = self._getDimensionality()
        self.setDimensionCount(_dimensionCount)

        try:
            # read acqus and procs
            self._readAcqus()
            self._readProcs()
        except Exception as es:
            errTxt = 'Reading acqu/proc parameters of %s; %s' % (self._brukerRoot, es)
            logger.error(errTxt)
            raise es

        try:
            _comment = self.acqus[0].get('_comments')
            if _comment is not None and isinstance(_comment, list):
                self.comment = '\n'.join(_comment)

            self.isBigEndian = self.procs[0].get('BYTORDP') == 1

            if 'NC_proc' in self.procs[0]:
                self.dataScale = pow(2, float(self.procs[0]['NC_proc']))
            else:
                self.dataScale = 1.0

            self.temperature = self.acqus[0]['TE']

            # Dimensional parameters
            for dimIndx in range(self.dimensionCount):
                # collapse the acq and proc dicts into one, so we do not have to
                # remember where the parameter lives
                dimDict = dict()
                dimDict.update(self.acqus[dimIndx])
                dimDict.update(self.procs[dimIndx])

                # establish dimension type (time/frequency)
                if int(float(dimDict.get('FT_mod', 1))) == 0:
                    # point/time axis
                    self.dimensionTypes[dimIndx] = specLib.DIMENSION_TIME
                    self.measurementTypes[dimIndx] = specLib.MEASUREMENT_TYPE_TIME
                else:
                    # frequency axis
                    self.dimensionTypes[dimIndx] = specLib.DIMENSION_FREQUENCY
                    self.measurementTypes[dimIndx] = specLib.MEASUREMENT_TYPE_SHIFT

                self.pointCounts[dimIndx] = int(dimDict['SI'])
                if self.dimensionTypes[dimIndx] == specLib.DIMENSION_TIME:
                    tdeff = int(dimDict['TDeff'])
                    if 0 < tdeff < self.pointCounts[dimIndx]:
                        self.pointCounts[dimIndx] = tdeff

                self.blockSizes[dimIndx] = int(dimDict['XDIM'])
                if self.blockSizes[dimIndx] == 0:
                    self.blockSizes[dimIndx] = self.pointCounts[dimIndx]
                else:
                    # for 1D data blockSizes can be > numPoints, which is wrong
                    # (comment from original V2-based code)
                    self.blockSizes[dimIndx] = min(self.blockSizes[dimIndx], self.pointCounts[dimIndx])

                # find the closest compatible isotopeCode
                _axNuc = dimDict.get('AXNUC', '').replace(' ', '_')  # remove whitespace
                axNuc = _findClosestMatch(_axNuc, DEFAULT_ISOTOPE_DICT.values()) or _axNuc
                if _axNuc not in DEFAULT_ISOTOPE_DICT.values():
                    getLogger().warning(f'axisCode {_axNuc!r} not found - using closest replacement {axNuc}')
                self.isotopeCodes[dimIndx] = axNuc
                self.axisLabels[dimIndx] = dimDict.get('AXNAME', '').replace(' ', '_')

                # SW_p is in Hz; from the procs file, likely denotes "SW_processed", not "SW_ppm"
                # SW_p can be zero in topspin 4.1.4 for time domain dimensions
                # SW_h is in Hz; from the acqus file
                swHz = float(dimDict.get('SW_p', dimDict.get('SW_h', 1.0)))  # SW in Hz
                if swHz == 0.0:
                    swHz = float(dimDict.get('SW_h', 1.0))
                # check again; swHz cannot be zero as this will (later) violate valuePerPoint in the model
                if swHz == 0.0:
                    swHz = 1.0
                    getLogger().warning(f'Extracting parameters for {self}: spectralWidthHz[{dimIndx}] set to 1.0')
                self.spectralWidthsHz[dimIndx] = swHz

                # SF is in MHz; from the procs file, but generally less digits for dimension 1 (!)
                # SFO1 - SF08: the eight spectrometer RF channels; no direct relation to SF of a dimension
                sf = float(dimDict.get('SF', 1.0))
                # # Correct dimension 1
                # sfo1 = self.acqus[0].get('SFO1')
                # o1 = self.acqus[0].get('O1')
                # if dimIndx == 0 and sfo1 is not None and o1 is not None and \
                #     round(sf,2) - round(sfo1, 2) == 0.0:
                #     sf = sfo1 - o1 * 1e-6
                self.spectrometerFrequencies[dimIndx] = sf

                self.referenceValues[dimIndx] = float(dimDict.get('OFFSET', 0.0))
                self.referencePoints[dimIndx] = float(dimDict.get('refPoint', 1.0))  # CCPN first point is defined as 1
                # origNumPoints[i] = int(dimDict.get('$FTSIZE', 0))
                # pointOffsets[i] = int(dimDict.get('$STSR', 0))
                self.phases0[dimIndx] = float(dimDict.get('PHC0', 0.0))
                self.phases1[dimIndx] = float(dimDict.get('PHC1', 0.0))

        except Exception as es:
            errTxt = 'Parsing parameters for %s; %s' % (self._brukerRoot, es)
            logger.error(errTxt)
            raise RuntimeError(errTxt)

        return super().readParameters()

    def _readAcqus(self):
        """Read the acqus files; fill the self.acqus list with a dict for every dimension
        """
        acquFiles = self._acqusFiles[0:self.dimensionCount]
        self.acqus = []
        for f in acquFiles:
            try:
                _params = read_jcamp(self._brukerRoot / f, encoding='Windows-1252')
            except UnicodeDecodeError:
                # Try again with utf-8
                _params = read_jcamp(self._brukerRoot / f, encoding='utf-8')
            self.acqus.append(_params)

    def _readProcs(self):
        """Read the procs files; fill the self.procs list with a dict for every dimension
        """
        procFiles = self._procFiles[0:self.dimensionCount]
        self.procs = []
        for f in procFiles:
            try:
                _params = read_jcamp(self._pdataDir / f, encoding='Windows-1252')
            except UnicodeDecodeError:
                # Try again with utf-8
                _params = read_jcamp(self._pdataDir / f, encoding='utf-8')

            self.procs.append(_params)


# Register this format
BrukerSpectrumDataSource._registerFormat()

import locale
import io
from nmrglue.fileio.bruker import parse_jcamp_line


def read_jcamp(filename: str, encoding: str = locale.getpreferredencoding()) -> dict:
    """
    Read a Bruker JCAMP-DX file into a dictionary.

    Creates two special dictionary keys _coreheader and _comments Bruker
    parameter "$FOO" are extracted into strings, floats or lists and assigned
    to dic["FOO"]

    Parameters
    ----------
    filename : str
        Filename of Bruker JCAMP-DX file.
    encoding : str
        Encoding of Bruker JCAMP-DX file. Defaults to the system default locale

    Returns
    -------
    dic : dict
        Dictionary of parameters in file.

    See Also
    --------
    write_jcamp : Write a Bruker JCAMP-DX file.

    Notes
    -----
    This is not a fully functional JCAMP-DX reader, it is only intended
    to read Bruker acqus (and similar) files.

    """
    dic = {"_coreheader": [], "_comments": []}  # create empty dictionary

    with io.open(filename, 'r', encoding=encoding, errors='replace') as f:
        endOfFile = False
        lineIndex = 0
        while not endOfFile:  # loop until end of file is found

            lineIndex += 1
            line = f.readline().rstrip()  # read a line
            if line == '':  # end of file found
                endOfFile = True
                continue

            if line[:6] == "##END=":
                # print("End of file")
                endOfFile = True
                continue

            elif line[:2] == "$$":
                dic["_comments"].append(line)
            elif line[:2] == "##" and line[2] != "$":
                dic["_coreheader"].append(line)
            elif line[:3] == "##$":
                try:
                    key, value = parse_jcamp_line(line, f)
                    dic[key] = value
                except:
                    getLogger().warning("%s (line:%d): Unable to correctly parse %r" %
                                        (filename, lineIndex, line))
            else:
                getLogger().warning("%s (line:%d): Extraneous %r" % (filename, lineIndex, line))

    return dic


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# _main - quick check for closest match to an isotope code
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def _main():
    # Example usage:
    word_to_match = "   _1  5  n"
    closest_match = _findClosestMatch(word_to_match, DEFAULT_ISOTOPE_DICT.values())

    if closest_match:
        print(f"The closest match to '{word_to_match}' is: {closest_match}")
    else:
        print(f"No close match found for '{word_to_match}' in the list.")


if __name__ == '__main__':
    _main()
