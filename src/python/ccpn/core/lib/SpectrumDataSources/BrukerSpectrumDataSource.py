"""
This file contains the Bruker data access class
it serves as an interface between the V3 Spectrum class and the actual spectral data
Some routines rely on code from the Nmrglue package, included in the miniconda distribution

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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-11-09 17:40:30 +0000 (Tue, November 09, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2020-11-20 10:28:48 +0000 (Fri, November 20, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
from typing import Sequence

from ccpn.util.Path import Path
from ccpn.util.Logging import getLogger
from ccpn.util.Common import flatten
import ccpn.core.lib.SpectrumLib as specLib
from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import SpectrumDataSourceABC

from nmrglue.fileio.bruker import read_acqus_file, read_jcamp


class BrukerSpectrumDataSource(SpectrumDataSourceABC):
    """
    Bruker spectral data reading
    Intialization can be with:
    - a directory with Bruker data
    - a directory with Bruker processed data (pdata/x)
    - Bruker processed data [1r, 2rr, etc]
    """
    dataFormat = 'Bruker'

    isBlocked = True
    wordSize = 4
    headerSize = 0
    blockHeaderSize = 0
    isFloatData = False

    suffixes = [None]
    allowDirectory = True  # Can supply a Bruker top directory
    openMethod = open
    defaultOpenReadMode = 'rb'

    _processedDataFilesDict = dict([
        (1, '1r 1i'.split()),
        (2, '2rr 2ri 2ir 2ii'.split()),
        (3, '3rrr 3rri 3rir 3rii 3irr 3iri 3iir 3iii'.split()),
        (4, '4rrrr 4rrri 4rrir 4rrii 4rirr 4riri 4riir 4riii 4irrr 4irri 4irir 4irii 4iirr 4iiri 4iiir 4iiii'.split()),
        (5, '5rrrrr'),
        (6, '6rrrrrr'),
        (7, '7rrrrrrr'),
        (8, '8rrrrrrrr'),
    ])
    _processedDataFiles = [f for f in flatten(_processedDataFilesDict.values())]  # all the possible processed data files as a list
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

    def __init__(self, path=None, spectrum=None):
        "Init local attributes"
        self._pdataDir = None
        self._brukerRoot = None
        self.acqus = None
        self.procs = None
        super().__init__(path, spectrum)

    def _isBrukerTopDir(self, path):
        """Return True if path (of type Path) is a Bruker top directory with acqu* files
        and a pdata directory
        """
        hasAcquFiles = len(path.globList('acqu*')) > 0
        pdata = path / self._PDATA
        return path is not None and path.exists() and path.is_dir() and \
               pdata.exists() and pdata.is_dir() and \
               hasAcquFiles

    def _checkBrukerTopDir(self, path):
        """Check if path (of type Path) is a Bruker top directory with acqu* files
        and a pdata directory
        raise RuntimeError on problems
        """
        hasAcquFiles = len(path.globList('acqu*')) > 0
        pdata = path / self._PDATA
        if path is None or not path.exists():
            errorMsg = 'Bruker top directory "%s": does not exist' % path
            getLogger().debug2(errorMsg)
            raise RuntimeError(errorMsg)
        if not path.is_dir():
            errorMsg = 'Bruker top directory "%s": is not a directory' % path
            getLogger().debug2(errorMsg)
            raise RuntimeError(errorMsg)
        if not hasAcquFiles:
            errorMsg = 'Bruker top directory "%s": has no acqu* files' % path
            getLogger().debug2(errorMsg)
            raise RuntimeError(errorMsg)
        if not pdata.exists() or not pdata.is_dir():
            errorMsg = 'Bruker top directory "%s": has no valid pdata directory' % path
            getLogger().debug2(errorMsg)
            raise RuntimeError(errorMsg)

    def _hasBinaryData(self, path=None):
        """Return True if path (defaults to self._pdataDir) contains binary data
        """
        if path is None:
            path = self._pdataDir
        return len(path.globList('[1-8][r,i]*')) > 0

    def _isBrukerPdataDir(self, path):
        """Return True if path (of type Path) is a Bruker pdata directory with
        proc files and binary data
        """
        if path is None:
            return False
        hasProcFiles = len(path.globList('proc*')) > 0
        hasBrukerTopdir = self._isBrukerTopDir(path.parent.parent)
        hasPdata = path.parent.stem == self._PDATA
        return path.exists() and path.is_dir() and \
               hasPdata and hasBrukerTopdir and hasProcFiles

    def _checkBrukerPdataDir(self, path):
        """Check if path (of type Path) is a valid Bruker pdata directory with
        proc* and binary data [r/i]* files;
        raise RuntimeError on problems
        """
        if path is None or not path.exists():
            errorMsg = 'Bruker pdata directory "%s": does not exist' % path
            getLogger().debug2(errorMsg)
            raise RuntimeError(errorMsg)
        if not path.is_dir():
            errorMsg = 'Bruker pdata directory "%s": is not a directory' % path
            getLogger().debug2(errorMsg)
            raise RuntimeError(errorMsg)

        hasProcFiles = len(path.globList('proc*')) > 0
        if not hasProcFiles:
            errorMsg = 'Bruker pdata directory "%s": has no proc* files' % path
            getLogger().debug2(errorMsg)
            raise RuntimeError(errorMsg)

        if not self._hasBinaryData():
            errorMsg = 'Bruker pdata directory "%s": has no valid processed data' % path
            getLogger().debug2(errorMsg)
            raise RuntimeError(errorMsg)

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
        _pdata = self._brukerRoot / self._PDATA
        _procDirs = []
        # add numeric proc dirs only; to sort later
        for p in _pdata.globList('[1-9]*'):
            try:
                _procDirs.append(int(p.basename))
            except:
                pass
        _procDirs.sort(key=int)

        for p in _procDirs:
            _path = _pdata / str(p)
            if self._isBrukerPdataDir(_path) and self._hasBinaryData(_path):
                return _path
        return None

    def nameFromPath(self):
        """Return a name derived from pdataDir
        """
        return '%s_pdata%s' % (self._brukerRoot.stem, self._pdataDir.stem)

    def setPath(self, path, substituteSuffix=False):
        """Parse and set path, assure there is the directory with acqus and pdata dirs
        set the _brukerRoot and _pdata attributes to point to the relevant directories

        Return self or None on error
        """

        logger = getLogger()

        self._pdataDir = None
        self._brukerRoot = None
        self._binaryData = None

        self.acqus = None   # list of the acqu files, parsed as dicts
        self.procs = None   # list of the proc files, parsed as dicts

        if path is None:
            _path = None

        else:
            _path = Path(path)

            if _path.is_file() and _path.stem in self._processedDataFiles:
                # Bruker binary processed data file
                self._pdataDir = _path.parent
                self._brukerRoot = _path.parent.parent.parent
                self._binaryData = _path

            elif _path.is_file() and _path.stem in self._procFiles:
                # Bruker proc file
                self._pdataDir = _path.basename
                self._brukerRoot = _path.parent.parent.parent
                self._binaryData = None

            elif self._isBrukerTopDir(_path):
                # Bruker top directory
                self._brukerRoot = _path
                self._pdataDir = self._findFirstPdataDir()
                self._binaryData = None

            elif _path.is_dir() and _path.stem == self._PDATA and self._isBrukerTopDir(_path.parent):
                # Bruker/pdata directory
                self._brukerRoot = _path.parent
                self._pdataDir = self._findFirstPdataDir()
                self._binaryData = None

            elif self._isBrukerPdataDir(_path):
                # Bruker pdata 'proc'-directory
                self._pdataDir = _path
                self._brukerRoot = _path.parent.parent
                self._binaryData = None

            else:
                logger.debug2('"%s" does not define a valid path with Bruker data' % path)
                return None

            # check the directories; From now on, raise errors when not correct
            self._checkBrukerTopDir(self._brukerRoot)
            self._checkBrukerPdataDir(self._pdataDir)

            dimensionality = self._getDimensionality()
            if dimensionality not in self._processedDataFilesDict:
                raise RuntimeError('Undefined Bruker dimensionality "%s"in "%s"' % (dimensionality, self._pdataDir))

            if self._binaryData is None:
                self._binaryData = self._pdataDir / self._processedDataFilesDict[dimensionality][0]
            if not self._binaryData.exists():
                raise RuntimeError('Unable to find Bruker binary data "%s"' % self._binaryData)

        return super().setPath(self._binaryData, substituteSuffix=False)

    def readParameters(self):
        """Read the parameters from the Bruker directory
        Returns self
        """
        logger = getLogger()

        self.setDefaultParameters()

        try:
            self.dimensionCount = self._getDimensionality()

            # read acqus and procs
            self._readAcqus()
            self._readProcs()

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
            for i in range(self.dimensionCount):
                # collaps the acq and proc dicts into one, so we do not have to
                # remember where the parameter lives
                dimDict = dict()
                dimDict.update(self.acqus[i])
                dimDict.update(self.procs[i])

                self.pointCounts[i] = int(dimDict['SI'])
                self.blockSizes[i] = int(dimDict['XDIM'])
                if self.blockSizes[i] == 0:
                    self.blockSizes[i] = self.pointCounts[i]
                else:
                    # for 1D data blockSizes can be > numPoints, which is wrongaaaaaaaaa
                    # (comment from orginal V2-based code)
                    self.blockSizes[i] = min(self.blockSizes[i], self.pointCounts[i])

                self.isotopeCodes[i] = dimDict.get('AXNUC')
                self.axisLabels[i] = dimDict.get('AXNAME')

                if int(float(dimDict.get('FT_mod', 1))) == 0:
                    # point/time axis
                    self.dimensionTypes[i] = specLib.DIMENSION_TIME
                    self.measurementTypes[i] = specLib.MEASUREMENT_TYPE_TIME
                else:
                   # frequency axis
                    self.dimensionTypes[i] = specLib.DIMENSION_FREQUENCY
                    self.measurementTypes[i] = specLib.MEASUREMENT_TYPE_SHIFT

                self.spectralWidthsHz[i] = float(dimDict.get('SW_p', 1.0))  # SW in Hz processed (from proc file)
                self.spectrometerFrequencies[i] = float(dimDict.get('SFO1', dimDict.get('SF', 1.0)))

                self.referenceValues[i] = float(dimDict.get('OFFSET', 0.0))
                self.referencePoints[i] = float(dimDict.get('refPoint', 0.0))
            # origNumPoints[i] = int(dimDict.get('$FTSIZE', 0))
            # pointOffsets[i] = int(dimDict.get('$STSR', 0))
                self.phases0[i] = float(dimDict.get('PHC0', 0.0))
                self.phases1[i] = float(dimDict.get('PHC1', 0.0))

        except Exception as es:
            logger.error('Reading parameters; %s' % es)
            raise es

        return super().readParameters()

    def _readAcqus(self):
        "Read the acqus files"
        acquFiles = self._acqusFiles[0:self.dimensionCount]
        # acqus = read_acqus_file(str(self._brukerRoot), acuFiles)
        # # acqus is a dict with acqFiles[i] as keys; convert to a list in dimension order
        # self.acqus = [acqus[key] for key in acuFiles]
        self.acqus = []
        for f in acquFiles:
            _params = read_jcamp(self._brukerRoot / f)
            self.acqus.append(_params)

    def _readProcs(self):
        "Read the procs files"
        procFiles = self._procFiles[0:self.dimensionCount]
        self.procs = []
        for f in procFiles:
            _params = read_jcamp(self._pdataDir / f)
            self.procs.append(_params)

# Register this format
BrukerSpectrumDataSource._registerFormat()

#=========================================================================
# Bug fix from NMRglue
#=========================================================================

def read_procs_file(dir='.', procs_files=None):
    """
    Read Bruker processing files from a directory.

    Parameters
    ----------
    dir : str
        Directory to read from.
    procs_files : list, optional
        List of filename(s) of procs parameter files in directory. None uses
        standard files.

    Returns
    -------
    dic : dict
        Dictionary of Bruker parameters.
    """
    if procs_files is None:
        procs_files = []
        for f in ["procs", "proc2s", "proc3s", "proc4s"]:
            if os.path.isfile(os.path.join(dir, f)):
                procs_files.append(f)
        pdata_path = dir

    elif procs_files == []:
        if os.path.isdir(os.path.join(dir, 'pdata')):
            pdata_folders = [folder for folder in
                             os.walk(os.path.join(dir, 'pdata'))][0][1]
            if '1' in pdata_folders:
                pdata_path = os.path.join(dir, 'pdata', '1')
            else:
                pdata_path = os.path.join(dir, 'pdata', pdata_folders[0])

        for f in ["procs", "proc2s", "proc3s", "proc4s"]:
            if os.path.isfile(os.path.join(pdata_path, f)):
                procs_files.append(f)

    else:
        pdata_path = dir

    # create an empty dictionary
    dic = dict()

    # read the acqus_files and add to the dictionary
    for f in procs_files:
        dic[f] = read_jcamp(os.path.join(pdata_path, f))
    return dic
