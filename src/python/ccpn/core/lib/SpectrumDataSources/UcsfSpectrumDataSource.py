"""
This file contains the Ucsf data access class
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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-04-20 13:29:27 +0100 (Tue, April 20, 2021) $"
__version__ = "$Revision: 3.0.4 $"
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
            header = BinaryHeader(UCSF_FILE_HEADER, self.wordSize).read(self.fp, doSeek=True)
            if header.bytesToString(0,8) != 'UCSF NMR':
                raise RuntimeError('File "%s" does not have the mandatory "UCSF NMR" first eight header bytes' % self.path)

            self.dimensionCount = int(header.bytes[10])
            if self.dimensionCount < 1 or self.dimensionCount > self.MAXDIM:
                raise RuntimeError('File "%s" has an invalid dimensionCount (%d)' %
                                   (self.path, self.dimensionCount))

            # Now get the full thing
            self.header = BinaryHeader(self.headerSize, self.wordSize).read(self.fp, doSeek=True)
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
