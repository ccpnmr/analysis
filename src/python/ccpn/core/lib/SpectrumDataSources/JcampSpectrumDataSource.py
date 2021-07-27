"""
This file contains the JCAMP data access class
it serves as an interface between the V3 Spectrum class and the actual spectral data
Some routines rely on code from the Nmrglue package, included in the miniconda distribution

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
__dateModified__ = "$dateModified: 2021-04-20 15:57:57 +0100 (Tue, April 20, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2021-07-23 10:28:48 +0000 (Fri, July 23, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
from typing import Sequence
import numpy as np
from datetime import datetime

from ccpn.util.Path import Path
from ccpn.util.Logging import getLogger
from ccpn.util.Common import flatten, isIterable
import ccpn.core.lib.SpectrumLib as specLib
from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import SpectrumDataSourceABC

from nmrglue.fileio.bruker import read_acqus_file, read_jcamp
from nmrglue.fileio.jcampdx import read as readJcamp


class JcampSpectrumDataSource(SpectrumDataSourceABC):
    """
    JCAMP spectral data reading; 1D only
    """
    dataFormat = 'Jcamp'
    isBlocked = False
    wordSize = 4
    headerSize = 0
    blockHeaderSize = 0
    isFloatData = False

    suffixes = ['.dx', '.DX']
    allowDirectory = False
    openMethod = open
    defaultOpenReadMode = 'r'

    def __init__(self, path=None, spectrum=None, dimensionCount=None):
        super().__init__(path=path, spectrum=spectrum, dimensionCount=dimensionCount)
        self._realData = None  # storage for the real data array
        self._imaginaryData = None  # storage for the imaginary data
        self._params = None  # the nmrGlue parsed parameters dictionary

    def readParameters(self):
        """Read the parameters from the file
        this will also read the data into the two arrays, as it is parsed in one go
        by the nmrglue routine
        """

        logger = getLogger()

        self.setDefaultParameters()

        # Just to use the SpectrumdataSource machinery; open and close the file
        self.openFile(mode=self.defaultOpenReadMode)

        params, data = readJcamp(self.path)

        if (jcampVersion := float(params['JCAMPDX'][0])) < 5.0:
            raise RuntimeError('JcampDataSource.readParameters: invalid Jcamp version (%s)' % jcampVersion)

        # if len(params['$SW']) != 1:
        #     raise RuntimeError(
        #         'JcampDataSource.readParameters: parsing "%s" did not yield viable data, dimensionalty > 1' % self.path)
        self.setDimensionCount(1)

        # Extract the non-dimensional parameters
        _comment = params.get('_comments')
        if _comment is not None and isinstance(_comment, list):
            _comment.extend('---- end comment ----')
            self.comment = '\n'.join(_comment)

        if (_date := params.get('$DATE',None)) is not None:
            _date = int(_date[0])
            _date = datetime.fromtimestamp(_date)
            self.date = str(_date)

        # self.isBigEndian = int(params['$BYTORDP'][0]) == 1

        if 'NC_proc' in params:
            nc_proc = float(params['$NC_proc'][0])
            self.dataScale = pow(2, nc_proc)
        else:
            self.dataScale = 1.0

        self.temperature = float(params['$TE'][0])

        # Extract the dimensional parameters;
        # Written to optionally (later) allow for 2D as well (and to remain in-sinc
        # with the BrukerSpectrumDataSource
        for i in range(self.dimensionCount):

            # create a dict with the parameters for this dimension only, also removing the
            # '$' from the key
            dimDict = dict((key[1:], val[i]) for key, val in params.items() )

            # self.pointCounts[i] = int(dimDict['SI'])
            # self.blockSizes[i] = int(dimDict['XDIM'])
            # if self.blockSizes[i] == 0:
            #     self.blockSizes[i] = self.pointCounts[i]
            # else:
            #     # for 1D data blockSizes can be > numPoints, which is wrongaaaaaaaaa
            #     # (comment from orginal V2-based code)
            #     self.blockSizes[i] = min(self.blockSizes[i], self.pointCounts[i])

            self.isotopeCodes[i] = dimDict.get('AXNUC').strip('<>')
            self.axisLabels[i] = dimDict.get('AXNAME').strip('<>')

            if int(float(dimDict.get('FT_mod', 1))) == 0:
                # point/time axis
                self.dimensionTypes[i] = specLib.DIMENSION_TIME
                self.measurementTypes[i] = specLib.MEASUREMENT_TYPE_TIME
            else:
               # frequency axis
                self.dimensionTypes[i] = specLib.DIMENSION_FREQUENCY
                self.measurementTypes[i] = specLib.MEASUREMENT_TYPE_SHIFT

            self.spectralWidthsHz[i] = float(dimDict.get('SWH', 1.0))  # SW in ppm
            self.spectrometerFrequencies[i] = float(dimDict.get('SFO1', dimDict.get('SF', 1.0)))

            self.referenceValues[i] = float(dimDict.get('OFFSET', 0.0))
            # self.referencePoints[i] = float(dimDict.get('refPoint', 0.0))
            # GWV: No idea!
            self.referencePoints[i] = float(dimDict.get('refPoint', 1.0))

            # origNumPoints[i] = int(dimDict.get('$FTSIZE', 0))
            # pointOffsets[i] = int(dimDict.get('$STSR', 0))

            self.phases0[i] = float(dimDict.get('PHC0', 0.0))
            self.phases1[i] = float(dimDict.get('PHC1', 0.0))
        # end for
        # retain the params dictionary
        self._params = params

        # Set the data arrays and related parameters
        if isIterable(data):
            if len(data) == 2:
                self._realData = np.array(data[0])
                self._imaginaryData = np.array(data[1])
                self.isComplex[self.X_AXIS] = True

            elif len(data) == 1:
                self._realData = np.array(data[0])
                self._imaginaryData = None

            else:
                raise RuntimeError(
                    'JcampDataSource.readParameters: parsing "%s" did not yield viable data' % self.path)

            self.pointCounts[self.X_AXIS] = len(self._realData)

        return super().readParameters()

    def getSliceData(self, position: Sequence = None, sliceDim: int = 1):
        """Return a 1D slice"""

        if self.hdf5buffer is not None:
            return self.hdf5buffer.getSliceData(position=position, sliceDim=sliceDim)

        position = self.checkForValidSlice(position=position, sliceDim=sliceDim)
        if self._realData is None:
            raise RuntimeError('JcampSpectrumDatSource.getSliceData: no data defined; '\
                               'has readParameters been called?')
        return self._realData

JcampSpectrumDataSource._registerFormat()