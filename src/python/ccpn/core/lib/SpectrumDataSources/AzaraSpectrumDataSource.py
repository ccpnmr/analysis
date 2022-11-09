"""
This file contains the Azara data access class
it serves as an interface between the V3 Spectrum class and the actual spectral data

In defining the Azara dataSource it accepts:
- path to binary Azara file (with or without .spc extension); parameter file is binary file + '.par'
  or .spc extension replaced by .par
- parameter file with .par extension: binary file is parameter file without .par extension
  or .par extension replaced by .spc

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
__dateModified__ = "$dateModified: 2022-11-09 13:25:08 +0000 (Wed, November 09, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2020-11-20 10:28:48 +0000 (Fri, November 20, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np

from ccpn.util.Path import aPath
from ccpn.util.Logging import getLogger

from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import SpectrumDataSourceABC
import ccpn.core.lib.SpectrumLib as specLib

from ccpn.framework.constants import NO_SUFFIX, ANY_SUFFIX
from ccpn.util.traits.CcpNmrTraits import CPath

class AzaraSpectrumDataSource(SpectrumDataSourceABC):
    """
    Azara nD (n=1-4) spectral data reading. The Azara data consist of a binary data file
    (required suffix ".spc") and a parameter file (required suffix ".par").
    Azara data are expected (and tested in order) to either:
    - have an identical basename for the binary and parameter files; e.g. myFile.spc, myFile.par
    - have an identical basename for the binary and parameter files with suffix .spc and .spc.par,
      respectively; e.g. myFile.spc, myFile.spc.par
    - have a valid path for the binary file defined in the parameter file (using the "file" keyword)
    """
    dataFormat = 'Azara'

    isBlocked = True
    wordSize = 4
    headerSize = 0
    blockHeaderSize = 0
    isFloatData = True
    MAXDIM = 4          # Explicitly overide as Azara can only handle upto 4 (?) dimensions

    suffixes = ['.spc', '.par']
    openMethod = open
    defaultOpenReadMode = 'rb'

    #
    _parameterFile = CPath(default_value=None, allow_none=True).tag(info =
                                        'an attribute to store the (parsed) path to the azara parameter file'
                                                                    )
    _binaryFile = CPath(default_value=None, allow_none=True).tag(info =
                                        'an attribute to store the path to the azara binary file; used during parsing'
                                                                 )
    _path = CPath(default_value=None, allow_none=True).tag(info =
                                        'an attribute to store the path used to define the azara  file; used during parsing'
                                                           )

    def _findParameterFile(self, binaryFile):
        """Find a parameter file from binaryFile
        :return a path or None if not found
        """
        if binaryFile is None or not binaryFile.exists():
            return None

        if (_p := binaryFile.withSuffix('.par')) and _p.exists():
            return _p

        if (_p := binaryFile + '.par') and _p.exists():
            return _p

        return None

    def _findBinaryFile(self, parameterFile):
        """Find a binary  file from parameter
        :return a path or None if not found
        """
        if parameterFile is None or not parameterFile.exists():
            return None

        # test the path without suffix is the binary
        if (_p := parameterFile.withoutSuffix()) and _p.exists():
            return _p

        # test the path with suffix .spc is the binary
        if (_p := parameterFile.withSuffix('.spc')) and _p.exists():
            return _p

        # we have not yet found a binary file; try parsing the parameter file
        getLogger().debug2(f'AzaraSpectrumDataSource: unable to find binary datafile using {self._path}, trying from "{parameterFile}"')
        # find, open and parse the parameter file
        _p = None
        with parameterFile.open(mode='rU', encoding='utf-8') as fp:
            for line in fp.readlines():
                if (data := line.split()) and len(data) ==2 and data[0] =='file':
                    # Try as relative path
                    _p = parameterFile.parent / data[1]
                    if _p.exists():
                        return _p
                    # try as absolute path
                    _p = aPath(data[1])
                    if _p.exists():
                        return _p

        return None


    def setPath(self, path, substituteSuffix=False):
        """Set the dataFile and parameterFile attributes from path after suitable path manipulation

        :param path: see doc-string above for handling of the argument values
        :param substituteSuffix: argument of the superclass, ignored here

        do some checks by calling the super class

        :return self or None on error
        """
        if path is None:
            self._path = None
            self._parameterFile = None
            self._binaryFile = None
            return super().setPath(path, substituteSuffix=False)

        path = aPath(path)
        self._path = path

        # Testing for binaries
        # .spc suffix, this is (supposingly) the azara binary
        # no suffix, assume this is (maybe) an azara binary
        if path.is_file() and path.suffix == '.spc' or len(path.suffixes) == 0:
            self._binaryFile = path
            self._parameterFile = self._findParameterFile(path)
            self.shouldBeValid = True

        # testing for .par files
        elif path.is_file() and len(path.suffixes) >= 1 and path.suffixes[-1] == '.par':
            # any .par suffix, set the parameterPath to it
            self._parameterFile = path
            self._binaryFile = self._findBinaryFile(path)
            self.shouldBeValid = True

        else:
            self._parameterFile = None
            self._binaryFile = None
            self.shouldBeValid = False
            return None

        return super().setPath(self._binaryFile, substituteSuffix=False)

    def readParameters(self):
        """Read the parameters from the azara parameter file
        :return self
        """
        if self._parameterFile is None or not self._parameterFile.exists():
            raise RuntimeError('Cannot find Azara parameter file "%s"' % self._parameterFile)

        self.setDefaultParameters()

        with open(self._parameterFile, mode='rU', encoding='utf-8') as fp:
            
            dim = 0
            comments = []
            for line in fp.readlines():

                #print('>>>', line)
                line.strip()
                if len(line) == 0: continue
                
                if line.startswith('!'): 
                    comments.append(line)

                if '!' in line:
                    line = line.split('!')[0]

                data = line.split()
                if len(data) == 0: continue

                keyword = data[0]
                if keyword == 'file':
                    #self.dataFile = data[1]
                    pass

                elif keyword == 'int':
                    self.isFloatData = False

                elif keyword == 'swap':
                    self.isBigEndian = not self.isBigEndian

                elif keyword == 'big_endian':
                    self.isBigEndian = True

                elif keyword == 'little_endian':
                    self.isBigEndian = False

                elif keyword == 'ndim':
                    self.dimensionCount = int(data[1])

                elif keyword == 'dim':
                    dim = int(data[1]) - 1

                elif keyword == 'npts':
                    if not self.pointCounts:
                        # strange bug that sometimes the arrays were not defined to the correct size
                        self.pointCounts[:] = [None] * self.dimensionCount
                    self.pointCounts[dim] = int(data[1])

                elif keyword == 'block':
                    if not self.blockSizes:
                        self.blockSizes[:] = [None] * self.dimensionCount
                    self.blockSizes[dim] = int(data[1])

                elif keyword == 'sw':
                    if not self.spectralWidthsHz:
                        self.spectralWidthsHz[:] = [None] * self.dimensionCount
                    self.spectralWidthsHz[dim] = float(data[1])

                elif keyword == 'sf':
                    if not self.spectrometerFrequencies:
                        self.spectrometerFrequencies[:] = [None] * self.dimensionCount
                    self.spectrometerFrequencies[dim] = float(data[1])

                elif keyword == 'refppm':
                    if not self.referenceValues:
                        self.referenceValues[:] = [None] * self.dimensionCount
                    self.referenceValues[dim] = float(data[1])

                elif keyword == 'refpt':
                    if not self.referencePoints:
                        self.referencePoints[:] = [None] * self.dimensionCount
                    self.referencePoints[dim] = float(data[1])

                # elif keyword == 'nuc':
                #     self.isotopes[dim] = str(data[1])

                elif keyword == 'params':
                    if not self.sampledValues:
                        self.sampledValues[:] = [None] * self.dimensionCount
                    self.sampledValues[dim] = [float(x) for x in data[1:]]

                    self.dimensionTypes[dim] = specLib.DIMENSION_TIME

                    if not self.isotopeCodes:
                        self.isotopeCodes[:] = [None] * self.dimensionCount
                    self.isotopeCodes[dim] = None

                elif keyword == 'sigmas':
                    if not self.sampledSigmas:
                        self.sampledSigmas[:] = [None] * self.dimensionCount
                    self.sampledSigmas[dim] = [float(x) for x in data[1:]]

        self.comment = ''.join(comments)

        super().readParameters()

        # we now need a patch to check for endian-ness, as this may vary and is
        # not stored for the Azara format
        # Wrong endiness data are characterised by very large or very small
        # exponents of their values
        slice = self.getSliceData()
        # remove any bad values - zeroes mess up the result and the endian-ness is flipped, also hides numpy warning
        data = np.log10(np.fabs(slice[slice != 0.0]))
        data = data[np.isfinite(data)]
        if len(data) > 0 and (max(data) > 30 or min(data) < -30):
            self.isBigEndian = not self.isBigEndian
            self.clearCache()

        return self

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

        if not self.shouldBeValid:
            errorMsg = f'Path "{self._path}" did not define a valid Azara file'
            return self._returnFalse(errorMsg)

        # checking parameter file
        if self._parameterFile is None:
            errorMsg = f'Azara parameter file is undefined'
            return self._returnFalse(errorMsg)

        if not self._parameterFile.exists():
            errorMsg = f'Azara parameter file "{self._parameterFile}" does not exist'
            return self._returnFalse(errorMsg)

        if not self._parameterFile.is_file():
            errorMsg = f'Azara parameter file "{self._parameterFile}" is not a file'
            return self._returnFalse(errorMsg)

        # checking binary file
        if self._binaryFile is None and self._parameterFile is not None:
            errorMsg = f'Azara binary file is undefined; checked "{self._parameterFile}"'
            return self._returnFalse(errorMsg)

        if self._binaryFile is None:
            errorMsg = f'Azara binary file is undefined'
            return self._returnFalse(errorMsg)

        if not self._binaryFile.exists():
            errorMsg = f'Azara binary file "{self._binaryFile}" does not exist'
            return self._returnFalse(errorMsg)

        if not self._binaryFile.is_file():
            errorMsg = f'Azara binary file "{self._binaryFile}" is not a file'
            return self._returnFalse(errorMsg)

        self.isValid = True
        self.errorString = ''
        return super(AzaraSpectrumDataSource, self).checkValid()

    def getAllFilePaths(self) -> list:
        """
        Get all the files handled by this dataSource: the binary and a parameter file.

        :return: list of Path instances
        """
        result = []
        if self._binaryFile is not None:
            result.append(self._binaryFile)
        if self._parameterFile is not None:
            result.append(self._parameterFile)
        return result

# Register this format
AzaraSpectrumDataSource._registerFormat()
