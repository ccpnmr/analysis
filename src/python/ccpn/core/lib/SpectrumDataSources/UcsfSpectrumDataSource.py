"""
This file contains the Ucsf data access class
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

from ccpn.util.Logging import getLogger

from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import SpectrumDataSourceABC
from ccpn.core.lib.SpectrumDataSources.lib.BinaryHeader import BinaryHeader


UCSF_FILE_HEADER = int(180/4)    # in words
UCSF_DIM_HEADER = int(128/4)     # in words

class UcsfSpectrumDataSource(SpectrumDataSourceABC):
    """
    Ucsf spectral storage
    """
    dataFormat = 'UCSF'

    isBlocked = True
    wordSize = 4
    headerSize = 0  # dynamic for UCSF format
    blockHeaderSize = 0
    isFloatData = True
    MAXDIM = 7  # Only one byte encodes dimensionCount

    suffixes = ['.ucsf']
    openMethod = open
    defaultOpenReadMode = 'rb'

    @property
    def headerSize(self):
        if self.dimensionCount == 0:
            raise RuntimeError('Undefined dimensionCount')
        return int(UCSF_FILE_HEADER + (UCSF_DIM_HEADER * self.dimensionCount) )

    def readParameters(self):
        """Read the parameters from the Felix file header
        Returns self
        """
        logger = getLogger()

        self.setDefaultParameters()

        try:
            if not self.hasOpenFile():
                self.openFile(mode=self.defaultOpenReadMode)

            self.isBigEndian = True # always for UCSF

            # we need to read some data from the file first, as the headerSize is dependent on the
            # number of dimensions
            header = BinaryHeader(UCSF_FILE_HEADER, self.wordSize).read(self.fp)
            if header.bytesToString(0,8) != 'UCSF NMR':
                raise RuntimeError('File "%s" appears not be a proper UCSF format' % self.path)
            self.dimensionCount = int(header.bytes[10])

            # Now get the full thing
            self.header = BinaryHeader(self.headerSize, self.wordSize).read(self.fp)
            if (sys.byteorder != 'big'):
                self.header.swapBytes()

            self.date = self.header.bytesToString(23,47).strip('\0')

            for dim in range(self.dimensionCount):
                # 32 words per dimension; dimensions in opposite order
                offset = int(UCSF_FILE_HEADER + (self.dimensionCount - dim - 1) * UCSF_DIM_HEADER)

                # 6 bytes for the isotopeCode
                tmp = self.header.bytesToString(offset*self.wordSize, offset*self.wordSize+6).strip('\0')
                if len(tmp) > 0:
                    self.isotopeCodes[dim] = tmp

                self.pointCounts[dim] = self.header.intValues[offset+2]
                self.blockSizes[dim] = self.header.intValues[offset+4]

                self.spectrometerFrequencies[dim] = self.header.floatValues[offset+5]
                self.spectralWidthsHz[dim] = self.header.floatValues[offset+6]

                self.referenceValues[dim] = self.header.floatValues[offset+7]
                self.referencePoints[dim] = self.pointCounts[dim]*0.5 + 1.0

        except Exception as es:
            logger.error('Reading parameters; %s' % es)
            raise es

        return super().readParameters()

# Register this format
UcsfSpectrumDataSource._registerFormat()
