"""
This file contains the NmrView data access class
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
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2022-03-29 10:03:40 +0100 (Tue, March 29, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2020-11-20 10:28:48 +0000 (Fri, November 20, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys

from ccpn.util.Logging import getLogger

from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import SpectrumDataSourceABC
from ccpn.core.lib.SpectrumDataSources.lib.BinaryHeader import BinaryHeader


class NmrViewSpectrumDataSource(SpectrumDataSourceABC):
    """
    NmrView spectral storage
    """
    dataFormat = 'NMRView'
    alternateDataFormatNames = ['NmrView']

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
