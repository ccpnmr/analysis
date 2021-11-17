"""
This file contains the Azara data access class
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
__dateModified__ = "$dateModified: 2021-11-17 21:07:35 +0000 (Wed, November 17, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2020-11-20 10:28:48 +0000 (Fri, November 20, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.Path import aPath

from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import SpectrumDataSourceABC


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

    suffixes = ['.spc', '.par']
    openMethod = open
    defaultOpenReadMode = 'rb'

    @property
    def parameterPath(self):
        """Path of the parameter file"""
        return self.path +'.par'

    def setPath(self, path, substituteSuffix=False):
        """Set the path, optionally change .par in .spc suffix and do some checks by calling
        the super class
        """
        if path is not None:
            path = aPath(path)
            if len(path.suffixes) == 2 and \
                    path.suffixes[-1] == '.par' and path.suffixes[-2] == '.spc':
                path = path.withoutSuffix()
            path = str(path)
        return super().setPath(path, substituteSuffix=substituteSuffix)

    def readParameters(self):
        """Read the parameters from the azara parameter file
        Returns self
        """
        params = self.parameterPath
        if not params.exists():
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

        return super().readParameters()

# Register this format
AzaraSpectrumDataSource._registerFormat()
