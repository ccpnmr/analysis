"""
PeakPicker abstract base class
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               )
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y"
                )
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-02-09 16:47:07 +0000 (Tue, February 09, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2021-01-13 10:28:41 +0000 (Wed, Jan 13, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from collections import OrderedDict

from ccpn.core.Spectrum import Spectrum
from ccpn.core.lib.peakUtils import peakParabolicInterpolation
from ccpn.util.traits.CcpNmrJson import CcpNmrJson
from ccpn.util.Logging import getLogger


class SimplePeak(object):
    """A simple class to hold peak data
    """
    currentIndx = 0

    def __init__(self, points, height, lineWidths=None, volume=None, clusterId=None):
        """
        :param points: list/tuple of points (0-based); z,y,x ordered in case of nD (i.e. numpy ordering)
        :param height: height of the peak
        :param lineWidths: list/tuple with lineWidths of the peak for each dimension (in points), optional, None if not defined
        :param volume: volume of the peak; optional, None if not defined
        :param clusterId: id of the peak cluster (i.e. a group of peaks in close proximity); optional, None if not defined
        """
        self.indx = SimplePeak.currentIndx
        SimplePeak.currentIndx += 1

        self.points = tuple(points)
        self.height = height
        self.lineWidths = lineWidths
        self.volume = volume
        self.clusterId = clusterId

    def __str__(self):
        return '<SimplePeak %s: %r, height=%.1e>' % (self.indx, self.points, self.height)


class PeakPickerABC(object):
    """ABC for implementation of a peak picker
    """

    #=========================================================================================
    # to be subclassed
    #=========================================================================================

    peakPickerType = None       # A unique string identifying the peak picker
    defaultPointExtension = 1   # points to extend the region to pick on either side
    onlyFor1D = False

    #=========================================================================================
    # data formats
    #=========================================================================================
    # A dict of registered dataFormat: filled by _registerPeakPicker classmethod, called once after
    # each definition of a new derived class
    _peakPickers = OrderedDict()

    @classmethod
    def register(cls):
        "register cls.peakPickerType"
        if cls.peakPickerType in PeakPickerABC._peakPickers:
            raise RuntimeError('PeakPicker "%s" was already registered' % cls.peakPickerType)
        PeakPickerABC._peakPickers[cls.peakPickerType] = cls

    #=========================================================================================

    def __init__(self, spectrum, autoFit=False):
        """Initialise the instance and associate with spectrum
        """
        if self.peakPickerType is None:
            raise RuntimeError('%s: peakPickerType is undefined' % self.__class__.__name__)

        if spectrum is None:
            raise ValueError('%s: spectrum is None' % self.__class__.__name__)
        if not isinstance(spectrum, Spectrum):
            raise ValueError('%s: spectrum %r is not of Spectrum class' % self.__class__.__name__)

        if spectrum.dimensionCount > 1 and self.onlyFor1D:
            raise ValueError('%s only works for 1D spectra' % self.__class__.__name__)
        self.spectrum = spectrum
        self.dimensionCount = spectrum.dimensionCount
        self.pointExtension = self.defaultPointExtension

        self.autoFit = autoFit

        self.lastPickedPeaks = None
        self.sliceTuples = None

    def setParameters(self, **parameters):
        """
        Set parameters as attributes of self
        :param parameters:
        :return: self
        """
        for key, value in parameters.items():
            setattr(self, key, value)

    def findPeaks(self, data) -> list:
        """find the peaks in data (type numpy-array) and return as a list of SimplePeak instances
        note that SimplePeak.points are ordered z,y,x for nD, in accordance with the numpy nD data array

        called from the pickPeaks() method

        any required parameters that findPeaks method needs should be initialised/set before using the
        setParameters() method; i.e.:
                myPeakPicker = PeakPicker(spectrum=mySpectrum)
                myPeakPicker.setParameters(dropFactor=0.2, positiveThreshold=1e6, negativeThreshold=None)
                corePeaks = myPeakPicker.pickPeaks(axisDict={'H':(6.0,11.5),'N':(102.3,130.0)}, spectrum.peaklists[-1])

        :param data: nD numpy array
        :return list of SimplePeak instances

        To be subclassed
        """
        raise NotImplementedError('%s.findPeaks should be implemented' % self.__class__.__name__)

    def pickPeaks(self, axisDict, peakList) -> list:
        """
        :param axisDict: Axis limits  are passed in as a dict of (axisCode, tupleLimit) key, value
                         pairs with the tupleLimit supplied as (start,stop) axis limits in ppm
                         (lower ppm value first).
        :param peakList: peakList instance to add newly pickedPeaks
        :return: list of core.Peak instances
        """
        if self.spectrum is None:
            raise RuntimeError('%s.spectrum is None' % self.__class__.__name__)

        if not self.spectrum.hasValidPath():
            raise RuntimeError('%s.pickPeaks: spectrum %s, No valid spectral datasource defined' %
                               (self.__class__.__name__, self.spectrum))

        self.sliceTuples = self.spectrum._axisDictToSliceTuples(axisDict)

        if self.defaultPointExtension:
            # add default points to extend pick region
            self.sliceTuples = [(sLeft - self.defaultPointExtension, sRight + self.defaultPointExtension) if sLeft < sRight else
                                (sLeft + self.defaultPointExtension, sRight - self.defaultPointExtension)
                                for sLeft, sRight in self.sliceTuples]

        # TODO: use Spectrum aliasing definitions once defined
        data = self.spectrum.dataSource.getRegionData(self.sliceTuples, aliasingFlags=[1]*self.spectrum.dimensionCount)

        peaks = self.findPeaks(data)
        getLogger().debug('%s.pickPeaks: found %d peaks in spectrum %s; %r' %
                         (self.__class__.__name__, len(peaks), self.spectrum, axisDict))

        corePeaks = []
        if len(peaks) > 0:
            self.lastPickedPeaks = peaks
            corePeaks = self._createCorePeaks(peaks, peakList)

        return corePeaks

    def _createCorePeaks(self, peaks, peakList) -> list:
        """
        Create core.Peak instances
        :param peaks: a list with simplePeaks
        :param peakList: a core.PeakList instance
        :return: a list with core.Peak instances
        """
        corePeaks = []
        for pk in peaks:
            if len(pk.points) != self.dimensionCount:
                raise RuntimeError('%s: invalid dimensionality of points attribute' % pk)
            # correct the peak.points for "offset" (the slice-positions taken) and ordering (i.e. inverse)
            pointPosition = [float(p)+float(self.sliceTuples[idx][0]) for idx,p in enumerate(pk.points[::-1])]
            if pk.height is None:
                # height was not defined; get the interpolated value from the data
                pk.height = self.spectrum.dataSource.getPointValue(pointPosition)
            cPeak = peakList.newPeak(pointPosition=pointPosition, height=pk.height, volume=pk.volume, pointLineWidths=pk.lineWidths)
            if self.autoFit:
                peakParabolicInterpolation(cPeak, update=True)
            corePeaks.append(cPeak)
        return corePeaks

    def _checkParameters(self):
        """
        Check whether the parameters are the correct types
        """
        pass

    def __str__(self):
        return '<%s for %r>' % (self.__class__.__name__, self.spectrum.name)
