"""
This file contains the data access stuff for "Empty" spectra, ie. those without actual data as used for simulated
peaklists
it serves as an interface between the V3 Spectrum class and the non-existent data, yield zero's in all cases

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
__dateModified__ = "$dateModified: 2021-06-25 15:28:15 +0100 (Fri, June 25, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2020-11-20 10:28:48 +0000 (Fri, November 20, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Sequence
from collections import defaultdict
import numpy


from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import SpectrumDataSourceABC
from ccpn.util.isotopes import Nucleus


class EmptySpectrumDataSource(SpectrumDataSourceABC):
    """
    Empty spectral data handling
    """
    #=========================================================================================

    dataFormat = 'Empty'

    isBlocked = False  #
    hasBlockCached = False  # Flag indicating if block data are cached

    wordSize = 4
    headerSize = 0
    blockHeaderSize = 0
    isFloatData = True

    suffixes = [None]
    openMethod = open

    #=========================================================================================
    # some default data
    #=========================================================================================

    isotopeDefaultDataDict = defaultdict(
        lambda: {'spectralRange' : (12.0, -1.0),   'pointCount' : 128},
        [
        ('1H' , {'spectralRange' : (12.0, -1.0),   'pointCount' : 512}),
        ('15N', {'spectralRange' : (130.0, 100.0), 'pointCount' : 128}),
        ('13C', {'spectralRange' : (130.0, 5.0),   'pointCount' : 256}),
        ('19F', {'spectralRange' : (250.0, 40.0),  'pointCount' : 512}),
        ]
    )
    #=========================================================================================


    def openFile(self, mode=None, **kwds):
        """Return None, as there is no actual file
        """
        return None

    @classmethod
    def checkForValidFormat(cls, path):
        """check if valid format corresponding to dataFormat by;
        :return: None
        """
        return None

    def hasValidPath(self):
        """Always True
        """
        return True

    def readParameters(self):
        """Read the parameters from the Spectrum instance
        Returns self
        """
        self.setDefaultParameters()
        if self.spectrum is not None:
            self.importFromSpectrum(self.spectrum, includePath=False)

        return super().readParameters()

    def getPlaneData(self, position:Sequence=None, xDim:int=1, yDim:int=2):
        """Get plane defined by xDim, yDim and position (all 1-based)
        return NumPy data array with zero's
        """
        position = self.checkForValidPlane(position=position, xDim=xDim, yDim=yDim)

        # create the array with zeros
        pointCounts = (self.pointCounts[yDim-1], self.pointCounts[xDim-1])  # y,x ordering
        data = numpy.zeros(pointCounts, dtype=self.dataType)

        return data

    def getSliceData(self, position:Sequence=None, sliceDim:int=1):
        """Get slice defined by sliceDim and position (all 1-based)
        return NumPy data array of zero's
        """
        position = self.checkForValidSlice(position=position, sliceDim=sliceDim)

        # create the array with zeros
        data = numpy.zeros(self.pointCounts[sliceDim-1], dtype=self.dataType)
        return data

    def getPointData(self, position:Sequence=None) -> float:
        """Get value defined by points (1-based)
        returns 0.0
        """
        position = self.checkForValidPosition(position=position)
        return 0.0

    def getPointValue(self, position, aliasingFlags=None):
        """Get interpolated value defined by position (1-based, float values)
        Use getPointData() for a method using an integer-based position argument
        returns 0.0
        """
        return 0.0

    def getRegionData(self, sliceTuples, aliasingFlags=None):
        """Return an numpy array containing the points defined by
                sliceTuples=[(start_1,stop_1), (start_2,stop_2), ...],
        containing only zero's

        sliceTuples are 1-based; sliceTuple stop values are inclusive (i.e. different
        from the python slice object)

        Optionally allow for aliasing per dimension:
            0: No aliasing
            1: aliasing with identical sign
           -1: aliasing with inverted sign
        """
        if aliasingFlags is None:
            aliasingFlags = [0] * self.dimensionCount

        self.checkForValidRegion(sliceTuples, aliasingFlags)

        sizes = [(stop-start+1) for start,stop in sliceTuples]
        # The result being assembled
        regionData = numpy.zeros(sizes[::-1], dtype=self.dataType) # ...,z,y,x numpy ordering
        return regionData

    def _setDefaultIsotopeValues(self, isotopeCode, dimension, field=18.8):
        """ Set the default spectrometerFrequencies, spectralWidth, referencePoints, referenceValues
        and axisCode values derived from isotopeCode and field for dimension (1-based)
        """

        if isotopeCode is not None:

            idx = dimension-1
            nuc = Nucleus(isotopeCode)
            defaultValues = self.isotopeDefaultDataDict[isotopeCode]

            if nuc is not None:
                self.isotopeCodes[idx] = isotopeCode
                self.spectrometerFrequencies[idx] = nuc.frequencyAtField(field)

                high, low = defaultValues['spectralRange']
                self.spectralWidthsHz[idx] = (high-low)*self.spectrometerFrequencies[idx]

                self.referencePoints[idx] = 1.0
                self.referenceValues[idx] = high

                _count = self.axisCodes.count(nuc.axisCode)
                self.axisCodes[idx] = nuc.axisCode + (str(_count) if _count else '')

                self.pointCounts[idx] = defaultValues['pointCount']

    def _setSpectralParametersFromIsotopeCodes(self, field=18.8):
        """Set spectral parameters at field
        """
        for idx, isotopeCode in enumerate(self.isotopeCodes):
            self._setDefaultIsotopeValues(isotopeCode, dimension=idx+1, field=field)

# Register this format
EmptySpectrumDataSource._registerFormat()

