"""
This file contains the Xeasy data access class
it serves as an interface between the V3 Spectrum class and the actual spectral data

See SpectrumDataSourceABC for a description of the methods
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
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
__dateModified__ = "$dateModified: 2022-12-07 21:32:04 +0000 (Wed, December 07, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2020-11-20 10:28:48 +0000 (Fri, November 20, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Sequence
import numpy
from numpy.lib import scimath

from ccpn.util.Path import aPath
from ccpn.util.Logging import getLogger

from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import SpectrumDataSourceABC
from ccpn.util.traits.CcpNmrTraits import CPath


XEASY_PARAM_DICT = {
    'version': 'Version',
    'ndim'   : 'Number of dimensions',
    'nbits'  : '16 or 8 bit file type',
    'sf'     : 'Spectrometer frequency in w',
    'sw'     : 'Spectral sweep width in w',
    'maxppm' : 'Maximum chemical shift in w',
    'npts'   : 'Size of spectrum in w',
    'block'  : 'Submatrix size in w',
    'order'  : 'Permutation for w',
    'fold'   : 'Folding in w',  # not used
    'type'   : 'Type of spectrum',  # not used
    'nuc'    : 'Identifier for dimension w',
}
firstLine = 'Version ....................... '

# A lookup dict for sqrt exponents (this is the slow step in decoding the 2-byte xeasy format)
_exponentDict = {}
sqrt2 = scimath.sqrt(2.0)
for i in range(-128,129,1):
    _exponentDict[i] = scimath.power(sqrt2, i)

class XeasySpectrumDataSource(SpectrumDataSourceABC):
    """
    Xeasy nD (n=1-4?) spectral data reading. The Xeasy data consist of a binary data file (required
    suffix ".16" and a parameter file (required suffix ".param").
    Xeasy data are expected to:
    - have an identical basename for the binary and parameter files; e.g. myFile.16, myFile.param
    """
    #=========================================================================================
    dataFormat = 'Xeasy'

    isBlocked = True
    wordSize = 2
    headerSize = 0
    blockHeaderSize = 0
    isFloatData = False
    MAXDIM = 4          # Explicitly overide as Xeasy can only handle upto 4 dimensions(?)

    suffixes = ['.param', '.16']
    openMethod = open
    defaultOpenReadMode = 'rb'

    #=========================================================================================

    _parameterFile = CPath(default_value=None, allow_none=True).tag(info =
                                        'an attribute to store the (parsed) path to the Xeasy parameter file'
                                                                    )
    _binaryFile = CPath(default_value=None, allow_none=True).tag(info =
                                        'an attribute to store the path to the Xeasy binary file; used during parsing'
                                                                 )
    _path = CPath(default_value=None, allow_none=True).tag(info =
                                        'an attribute to store the path used to define the Xeasy file; used during parsing'
                                                           )
    #=========================================================================================

    @property
    def parameterPath(self):
        "Path of the parameter file"
        return self.path.with_suffix('.param')

    def setPath(self, path, checkSuffix=False):
        """Set the path, optionally change suffix and do some checks by calling the super class
        Return self or None on error
        """
        if path is None:
            self._path = None
            _path = None

        else:
            _path = aPath(path)
            self._path = path

            if _path.is_file() and path.suffix == '.param':
                self._parameterFile = _path
                self._binaryFile = _path.with_suffix('.16')
                self.shouldBeValid = True

            elif _path.is_file() and path.suffix == '.16':
                self._binaryFile = _path
                self._parameterFile = _path.with_suffix('.param')
                self.shouldBeValid = True

            else:
                self.shouldBeValid = False
                return None

        return super().setPath(self._binaryFile, checkSuffix=False)

    def readParameters(self):
        """Read the parameters from the Xeasy parameter file
        Returns self
        """
        if not self._parameterFile.exists():
            raise RuntimeError('Cannot find Xeasy parameter file "%s"' % self._parameterFile)

        self.setDefaultParameters()

        # Parse the parameter file
        with open(self._parameterFile, mode='rU', encoding='utf-8') as fp:
            self._parseDict = {}
            for lineIndx, line in enumerate(fp.readlines()):
                key = line[:32].replace('.', '').strip()
                value = line[32:].strip()
                self._parseDict[key] = value

        version = self._getValue('version', None, int)
        if version != 1:
            raise ValueError('Invalid Xeasy parameter file "%s"' % self._parameterFile)

        self.dimensionCount = self._getValue('ndim', None, int)
        if self.dimensionCount is None:
            raise ValueError('decoding "%s"' % self._parameterFile)

        for dim in self.dimensions:
            # There is a mapping defined in the parameter file
            idx = self._getValue('order', dim, int) - 1
            self.dimensionOrder[idx] = dim-1

            self.pointCounts[idx] = self._getValue('npts', dim, int)
            self.blockSizes[idx] = self._getValue('block', dim, int)
            self.spectrometerFrequencies[idx] = self._getValue('sf', dim, float)
            # Spectral widths defined in ppm
            self.spectralWidthsHz[idx] = self._getValue('sw', dim, float) * self.spectrometerFrequencies[idx]
            self.referenceValues[idx] = self._getValue('maxppm', dim, float)
            self.referencePoints[idx] = 1.0
            self.isotopeCodes[idx] = self._getValue('nuc', dim, str)

        return super().readParameters()

    def _getValue(self, key, dim, func):
        "Return value from Xeasy parseDict, using keys defined in XEASY_PARAM_DICT or None on error"
        if key not in XEASY_PARAM_DICT:
            getLogger().debug2('key "%s" not defined in XEASY_PARAM_DICT')
            return None
        if dim is not None:
            paramKey = XEASY_PARAM_DICT[key] + str(dim)
        else:
            paramKey = XEASY_PARAM_DICT[key]
        if paramKey not in self._parseDict:
            getLogger().debug2('parameterKey "%s" not present in "%s"' % (paramKey, self._parameterFile))
            return None
        return func(self._parseDict[paramKey])

    def checkValid(self) -> bool:
        """check if valid format corresponding to dataFormat by:
        - checking parameter and binary files are defined

        call super class for:
        - checking suffix and existence of path
        - reading (and checking dimensionCount) parameters

        :return: True if ok, False otherwise
        """

        self.isValid = False
        self.errorString = 'Checking validity'

        if self._path is None or not self._path.exists():
            errorMsg = f'Path "{self._path}" does not exist'
            return self._returnFalse(errorMsg)

        # checking parameter file
        if self._parameterFile is None and self._binaryFile is not None:
            errorMsg = f'Xeasy parameter file is undefined; did find binary file "{self._binaryFile}"'
            return self._returnFalse(errorMsg)

        if self._parameterFile is None:
            errorMsg = f'Xeasy parameter file is undefined'
            return self._returnFalse(errorMsg)

        if not self._parameterFile.exists():
            errorMsg = f'Xeasy parameter file "{self._parameterFile}" does not exist'
            return self._returnFalse(errorMsg)

        if not self._parameterFile.is_file():
            errorMsg = f'Xeasy parameter file "{self._parameterFile}" is not a file'
            return self._returnFalse(errorMsg)

        # checking binary file
        if self._binaryFile is None and self._parameterFile is not None:
            errorMsg = f'Xeasy binary file is undefined; did find parameter file "{self._parameterFile}"'
            return self._returnFalse(errorMsg)

        if self._binaryFile is None:
            errorMsg = f'Xeasy binary file is undefined'
            return self._returnFalse(errorMsg)

        if not self._binaryFile.exists():
            errorMsg = f'Xeasy binary file "{self._binaryFile}" does not exist'
            return self._returnFalse(errorMsg)

        if not self._binaryFile.is_file():
            errorMsg = f'Xeasy binary file "{self._binaryFile}" is not a file'
            return self._returnFalse(errorMsg)

        if not self.shouldBeValid:
            errorMsg = f'Path "{self._path}" did not define a valid Xeasy file'
            return self._returnFalse(errorMsg)

        self.isValid = True
        self.errorString = ''
        return super().checkValid()

    def getAllFilePaths(self) -> list:
        """
        Get all the files handled by this dataSource: i.e. the binary and a parameter file.

        :return: list of Path instances
        """
        result = []
        if self._binaryFile is not None:
            result.append(self._binaryFile)
        if self._parameterFile is not None:
            result.append(self._parameterFile)
        return result

    @property
    def dtype(self):
        "return the numpy dtype string; usigned 2 byte words"
        return '%s%s%s' % (self.isBigEndian and '>' or '<', 'u', self.wordSize)

    def _convertBlockData(self, blockdata):
        """Convert the blockdata array from  2 byte xeasy format into float32
        closely following the Xeasy manual found at:
        http://triton.iqfr.csic.es/HTML-manuals/xeasy-manual/xeasy_m3.html
        """

        blockDataByteView = blockdata.view(numpy.int8)
        result = numpy.zeros(blockdata.size, numpy.float32)

        idx = 0
        for i in range(0, blockDataByteView.size, 2):
            e_k = int(blockDataByteView[i+1])
            a_k = int(blockDataByteView[i])
            if e_k <= 47:
                sign = 1.0
                ell = e_k - 1
            else:
                sign = -1.0
                ell = -1 * (e_k - 95)

            exponent = 1.0
            if ell != 0:
                exponent = _exponentDict[ell]

            mantissa = 1.0
            if ell != 0:
                mantissa = float(a_k + 615) / 721.0

            result[idx] = sign * mantissa * exponent
            idx += 1

        return result

# Register this format
XeasySpectrumDataSource._registerFormat()
