"""
This file contains the Felix data access class
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

from ccpn.util.Logging import getLogger

from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import SpectrumDataSourceABC
from ccpn.core.lib.SpectrumDataSources.BinaryHeader import BinaryHeader


class FelixSpectrumDataSource(SpectrumDataSourceABC):
    """
    Felix spectral storage
    """
    dataFormat = 'Felix'

    isBlocked = True
    wordSize = 4
    headerSize = 4096
    blockHeaderSize = 0
    isFloatData = True

    suffixes = ['.mat', '.dat']
    openMethod = open
    defaultOpenReadMode = 'rb'

    def readParameters(self):
        """Read the parameters from the Felix file header
        Returns self
        """
        logger = getLogger()

        self.setDefaultParameters()

        try:
            if not self.hasOpenFile():
                self.openFile(mode=self.defaultOpenReadMode)

            self.header = BinaryHeader(self.headerSize, self.wordSize).read(self.fp)

            # check the 'magic' number at word 1
            if (self.header.intValues[1] != 1):
                self.isBigEndian = not self.isBigEndian
                self.header.swapBytes()

            if self.header.intValues[1] != 1:
                raise RuntimeError('Felix file %s appears to be corrupted' % self.path)

            self.dimensionCount = self.header.intValues[0]
            for i in range(self.dimensionCount):
                self.pointCounts[i] = self.header.intValues[20 + 1 * self.dimensionCount + i]
                self.blockSizes[i] = self.header.intValues[20 + 4 * self.dimensionCount + i]
                self.spectrometerFrequencies[i] = self.header.floatValues[20 + 6 * self.dimensionCount + i]
                self.spectralWidthsHz[i] = self.header.floatValues[20 + 7 * self.dimensionCount + i]
                self.referencePoints[i] = self.header.floatValues[20 + 8 * self.dimensionCount + i]
                self.referenceValues[i] = self.header.floatValues[20 + 9 * self.dimensionCount + i] / self.spectrometerFrequencies[i]
                start = 220 + 8 * i
                self.axisLabels[i] = self.header.wordsToString(start, start+8).strip()

        except Exception as es:
            logger.debug('Reading parameters; %s' % es)
            raise es

        return super().readParameters()

# Register this format
FelixSpectrumDataSource._registerFormat()
