"""
This file contains the Azara data access class
it serves as an interface between the V3 Spectrum class and the actual spectral data

See SpectrumDataSourceABC for a description of the methods
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:33:14 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2020-11-20 10:28:48 +0000 (Fri, November 20, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Sequence

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
        "Path of the parameter file"
        return self.path +'.par'

    def setPath(self, path, substituteSuffix=False):
        """Set the path, optionally change .par in .spc suffix and do some checks by calling the super class
        """
        if path is not None:
            path = aPath(path)
            if path.suffix == '.par':
                path = path.with_suffix('.spc')
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
                    self.pointCounts[dim] = int(data[1])

                elif keyword == 'block':
                    self.blockSizes[dim] = int(data[1])

                elif keyword == 'sw':
                    self.spectralWidthsHz[dim] = float(data[1])

                elif keyword == 'sf':
                    self.spectrometerFrequencies[dim] = float(data[1])

                elif keyword == 'refppm':
                    self.referenceValues[dim] = float(data[1])

                elif keyword == 'refpt':
                    self.referencePoints[dim] = float(data[1])

                # elif keyword == 'nuc':
                #     self.isotopes[dim] = str(data[1])

                elif keyword == 'params':
                    self.sampledValues[dim] = [float(x) for x in data[1:]]
                    self.isotopeCodes[dim] = None

                elif keyword == 'sigmas':
                    self.sampledSigmas[dim] = [float(x) for x in data[1:]]

        self.comment = ''.join(comments)

        return super().readParameters()

    def getPlaneData(self, position:Sequence=None, xDim:int=1, yDim:int=2):
        """Get plane defined by xDim, yDim and position (all 1-based)
        return NumPy data array
        """
        if position is None:
            position = [1] * self.dimensionCount

        return self._readBlockedPlane(xDim=xDim, yDim=yDim, position=position)

    def getSliceData(self, position:Sequence=None, sliceDim:int=1):
        """Get slice defined by sliceDim and position (all 1-based)
        return NumPy data array
        """
        if position is None:
            position = [1] * self.dimensionCount

        return self._readBlockedSlice(sliceDim=sliceDim, position=position)

# Register this format
AzaraSpectrumDataSource._registerFormat()
