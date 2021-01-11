"""
This file contains the NmrView data access class
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

import sys
from typing import Sequence

from ccpn.util.Logging import getLogger

from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import SpectrumDataSourceABC
from ccpn.core.lib.SpectrumDataSources.BinaryHeader import BinaryHeader


class NmrViewSpectrumDataSource(SpectrumDataSourceABC):
    """
    NmrView spectral storage
    """
    dataFormat = 'NMRView'

    isBlocked = True
    wordSize = 4
    headerSize = 512
    blockHeaderSize = 0
    isFloatData = True

    suffixes = ['.nv']
    openMethod = open
    defaultOpenReadMode = 'rb'


    _byteOrderFlags = { ('34','18','AB','CD') : 'big',
                        ('CD','AB','18','34') : 'little'
    }

    def readParameters(self):
        """Read the parameters from the Felix file header
        Returns self
        """
        logger = getLogger()

        self.setDefaultParameters()

        try:
            if not self.hasOpenFile():
                fp = self.openFile(mode=self.defaultOpenReadMode)

            self.header = BinaryHeader(self.headerSize, self.wordSize).read(self.fp)

            # check the 'magic' first 4 bytes
            magicBytes = self.header.bytesAsHexTuple[:4]
            if magicBytes not in self._byteOrderFlags:
                raise RuntimeError('NmrView file "%s" appears to be corrupted: does not start with the expected magic 4 bytes' %
                                  self.path)
            byteorder = self._byteOrderFlags[magicBytes]
            if byteorder != sys.byteorder:
                self.isBigEndian = (byteorder == 'big')
                self.header.swapBytes()

            self.dimensionCount = self.header.intValues[6]

            for dim in range(self.dimensionCount):
                baseIndx = 256 + dim * 32  # 32 dimensional parameters per dimension, starting at idx 256
                self.pointCounts[dim] = self.header.intValues[baseIndx + 0]
                self.blockSizes[dim] = self.header.intValues[baseIndx + 1]
                self.spectrometerFrequencies[dim] = self.header.floatValues[baseIndx + 6]
                self.spectralWidthsHz[dim] = self.header.floatValues[baseIndx + 7]
                self.referencePoints[dim] = self.header.floatValues[baseIndx + 8] + 1  # Analysis points run [1.. pointCounts[dim]]
                self.referenceValues[dim] = self.header.floatValues[baseIndx + 9]

        except Exception as es:
            logger.error('Reading parameters; %s' % es)
            raise es

        return super().readParameters()

# Register this format
NmrViewSpectrumDataSource._registerFormat()
