"""
This file contains the Azara data access class
it serves as an interface between the V3 Spectrum class and the actual spectral data

In defining the Azara dataSource it accepts:
- path to binary Azara file (with or without .spc extension); parameter file is binary file + '.par'
  or .spc extension replaced by .par
- parameter file with .par extension: binary file is parameter file without .par extension
  or .par extention replaced by .spc

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
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2022-08-25 17:31:26 +0100 (Thu, August 25, 2022) $"
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
from ccpn.util.traits.CcpNmrTraits import CPath

class AzaraSpectrumDataSource(SpectrumDataSourceABC):
    """
    Azara spectral storage
    """
    dataFormat = 'Azara'

    isBlocked = True
    wordSize = 4
    headerSize = 0
    blockHeaderSize = 0
    isFloatData = True

    suffixes = [None, '.spc', '.par']
    openMethod = open
    defaultOpenReadMode = 'rb'

    # an attibute to store the (parsed) path to the azara parameter file
    parameterFile = CPath(default_value=None, allow_none=True).tag(
                                                                  isDimensional=False,
                                                                  doCopy=False,
                                                                  spectrumAttribute=None,
                                                                  hasSetterInSpectrumClass=False
                                                                  )


    def setPath(self, path, substituteSuffix=False):
        """Set the dataFile and parameterFile attributes from path after suitable path manipulation

        :param path: see doc-string above for hndling of the argument values
        :param substituteSuffix: argument of the superclass, ignored here

        do some checks by calling the super class

        :return self or None on error
        """
        if path is None:
            return super().setPath(path, substituteSuffix=False)

        path = aPath(path)

        # Testing for binaries
        # .spc suffix, this is (supposingly) the azara binary
        # no suffix, assume this is (maybe) an azara binary
        if path.suffix == '.spc' or len(path.suffixes) == 0:
            self.parameterFile = None
            # Find a parameter file
            if (_p := path.withSuffix('.par')) and _p.exists():
                self.parameterFile = _p
            elif (_p := path + '.par') and _p.exists():
                self.parameterFile = _p

        # testing for .par files
        elif len(path.suffixes) >= 1 and path.suffixes[-1] == '.par':
            # any .par suffix, set the parameterPath to it
            self.parameterFile = path
            path = None

            # test the path without suffix is the binary
            if (_p := self.parameterFile.withoutSuffix()) and _p.exists():
                path = _p

            # test the path with suffix .spc is the binary
            elif (_p := self.parameterFile.withSuffix('.spc')) and _p.exists():
                path = _p

        # By now, we expect to have found a valid parameter file
        if self.parameterFile is None or not self.parameterFile.exists():
            getLogger().debug2(f'AzaraSpectrumDataSource: unable to find parameter file from given path "{path}"')

        # By now, we expect to have found a valid binary, if not try to find/define it from the parameter file
        # (i.e. using the 'file' parameter)
        if path is None or not path.exists():
            getLogger().debug2(f'AzaraSpectrumDataSource: unable to find binary datafile "{path}", trying from "{self.parameterFile}"')
            # find, open and parse the parameter file
            if self.parameterFile is not None and self.parameterFile.exists():
                with self.parameterFile.open(mode='rU', encoding='utf-8') as fp:
                    for line in fp.readlines():
                        if (data := line.split()) and len(data) ==2 and data[0] =='file':
                            path = self.parameterFile.parent / data[1]
                            break

        return super().setPath(path, substituteSuffix=False)

    def readParameters(self):
        """Read the parameters from the azara parameter file
        :return self
        """
        params = self.parameterFile
        if params is None or not params.exists():
            raise RuntimeError('Cannot find Azara parameter file "%s"' % params)

        self.setDefaultParameters()

        with open(str(params), mode='rU', encoding='utf-8') as fp:
            
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

# Register this format
AzaraSpectrumDataSource._registerFormat()
