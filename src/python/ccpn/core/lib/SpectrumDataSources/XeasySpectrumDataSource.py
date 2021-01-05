"""
This file contains the Xeasy data access class
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
from ccpn.util.Logging import getLogger

from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import SpectrumDataSourceABC


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


class XeasySpectrumDataSource(SpectrumDataSourceABC):
    """
    Xeasy spectral storage
    """
    dataFormat = 'Xeasy'

    isBlocked = True
    wordSize = 2
    headerSize = 0
    blockHeaderSize = 0
    isFloatData = True

    suffixes = ['.param', '.16']
    openMethod = open
    defaultOpenReadMode = 'rb'

    @property
    def parameterPath(self):
        "Path of the parameter file"
        return self.path.with_suffix('.param')

    def setPath(self, path, substituteSuffix=False):
        """Set the path, optionally change .par in .spc suffix and do some checks by calling the super class
        Return self or None on error
        """
        if path is not None:
            path = aPath(path)
            if path.suffix == '.param':
                path = path.with_suffix('.16')
            path = str(path)
        return super().setPath(path, substituteSuffix=substituteSuffix)

    def readParameters(self):
        """Read the parameters from the Xeasy parameter file
        Returns self
        """
        if not self.parameterPath.exists():
            raise RuntimeError('Cannot find Xeasy parameter file "%s"' % self.parameterPath)

        self.setDefaultParameters()

        # Parse the parameter file
        with open(str(self.parameterPath), mode='rU', encoding='utf-8') as fp:
            self._parseDict = {}
            for lineIndx, line in enumerate(fp.readlines()):
                key = line[:32].replace('.', '').strip()
                value = line[32:].strip()
                self._parseDict[key] = value

        version = self._getValue('version', None, int)
        if version != 1:
            raise ValueError('Invalid Xeasy parameter file "%s"' % self.parameterPath)

        self.dimensionCount = self._getValue('ndim', None, int)
        if self.dimensionCount is None:
            raise ValueError('decoding "%s"' % self.parameterPath)

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
            getLogger().debug2('parameterKey "%s" not present in "%s"' % (paramKey, self.parameterPath))
            return None
        return func(self._parseDict[paramKey])

    #TODO: implement Xeasy byte conversion routine
    # def _convertBlockData(self, blockdata):
    #     """Convert the blockdata array
    #     """
    #     if blockdata.dtype != numpy.float32:
    #         blockdata = numpy.array(blockdata, numpy.float32)
    #     return blockdata

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
XeasySpectrumDataSource._registerFormat()
