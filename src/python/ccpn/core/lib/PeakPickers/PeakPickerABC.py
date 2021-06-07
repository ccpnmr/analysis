"""
PeakPicker abstract base class
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
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
__dateModified__ = "$dateModified: 2021-06-07 12:53:53 +0100 (Mon, June 07, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2021-01-13 10:28:41 +0000 (Wed, Jan 13, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from collections import OrderedDict
from copy import deepcopy
from ccpn.core.Spectrum import Spectrum
from ccpn.core.lib.peakUtils import peakParabolicInterpolation
from ccpn.util.traits.CcpNmrJson import CcpNmrJson
from ccpn.util.Logging import getLogger


PEAKPICKERSTORE = 'peakPickerStore'
PEAKPICKER = 'peakPicker'
PEAKPICKERPARAMETERS = 'peakPickerParameters'


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

    peakPickerType = None  # A unique string identifying the peak picker
    defaultPointExtension = 1  # points to extend the region to pick on either side
    onlyFor1D = False

    # list of core peakPicker attributes that need to be restored when the spectrum is loaded
    _attributes = ['dimensionCount',
                   'pointExtension',
                   'autoFit',
                   'dropFactor',
                   'fitMethod',
                   'positiveThreshold',
                   'negativeThreshold',
                   ]

    # list of peakPicker attributes that need to be stored/restored
    # these pertain to a particular peakPicker subclass
    # this cannot contain items that are not JSON serialisable
    # call self._storeAttributes at the end of methods that change any values
    # these are defined in a similar manner to the core attributes above
    attributes = []

    #=========================================================================================
    # data formats
    #=========================================================================================
    # A dict of registered dataFormat: filled by _registerPeakPicker classmethod, called once after
    # each definition of a new derived class
    _peakPickers = OrderedDict()

    @classmethod
    def register(cls):
        """register cls.peakPickerType"""
        if cls.peakPickerType in PeakPickerABC._peakPickers:
            getLogger().debug(f'{cls.peakPickerType} already registered')
            return
            # raise RuntimeError('PeakPicker "%s" was already registered' % cls.peakPickerType)
        PeakPickerABC._peakPickers[cls.peakPickerType] = cls
        getLogger().info(f'Registering peakPicker class {cls.peakPickerType}')

    @classmethod
    def getPeakPickerClass(cls, peakPickerType):
        """Return classtype if PeakPicker defined by peakPickerType has been registered

        :param peakPickerType: type str; reference to peakPickerType of peakPicker class
        :return: class referenced by peakPickerType if it has been registered otherwise None
        """
        if not isinstance(peakPickerType, str):
            raise ValueError(f'{peakPickerType} must be of type str')
        return PeakPickerABC._peakPickers.get(peakPickerType)

    @classmethod
    def isRegistered(cls, peakPickerType):
        """Return True if a PeakPicker class if type peakPickerType is registered

        :param peakPickerType: type str; reference to peakPickerType of peakPicker class
        :return: True if class referenced by peakPickerType if it has been registered
        """
        return cls.getPeakPickerClass(peakPickerType) is not None

    @classmethod
    def createPeakPicker(cls, peakPickerType, spectrum, *args, **kwds):
        """Return instance of class if PeakPicker defined by peakPickerType has been registered

        :param peakPickerType: type str; reference to peakPickerType of peakPicker class
        :return: new instance of class if registered else None
        """
        klass = cls.getPeakPickerClass(peakPickerType)
        if klass:
            return klass(spectrum, *args, **kwds)

    @classmethod
    def _restorePeakPicker(cls, spectrum):
        """Create a new peakPicker instance defined by parameters stored within
        spectrum Ccpn Internal data
        """
        if spectrum is None:
            raise ValueError('%s: spectrum is None' % cls.__class__.__name__)
        if not isinstance(spectrum, Spectrum):
            raise ValueError('%s: spectrum is not of Spectrum class' % cls.__class__.__name__)

        # get peakPickerType from CcpnInternal
        _pickerType = spectrum.getParameter(PEAKPICKERSTORE, PEAKPICKER)

        if _pickerType:
            _picker = cls.createPeakPicker(_pickerType, spectrum)
            if _picker:
                getLogger().debug(f'peakPicker {_picker} instantiated')
                # restore peakPicker with parameters from CcpnInternal
                _picker._restoreAttributes()
                return _picker

            else:
                getLogger().debug(f'peakPicker {_pickerType} not defined')
        else:
            getLogger().debug(f'peakPicker not restored from {spectrum}')

    #=========================================================================================

    def __init__(self, spectrum, autoFit=False):
        """Initialise the instance and associate with spectrum
        """
        if self.peakPickerType is None:
            raise RuntimeError('%s: peakPickerType is undefined' % self.__class__.__name__)

        if spectrum is None:
            raise ValueError('%s: spectrum is None' % self.__class__.__name__)
        if not isinstance(spectrum, Spectrum):
            raise ValueError('%s: spectrum is not of Spectrum class' % self.__class__.__name__)

        if spectrum.dimensionCount > 1 and self.onlyFor1D:
            raise ValueError('%s only works for 1D spectra' % self.__class__.__name__)

        # default parameters for all peak pickers
        self._initParameters()

        # initialise from parameters
        self.spectrum = spectrum
        self.dimensionCount = spectrum.dimensionCount
        self.pointExtension = self.defaultPointExtension
        self.autoFit = autoFit

        # attributes not required to be persistent between load/save
        self.lastPickedPeaks = None
        self.sliceTuples = None

    def _initParameters(self):
        """Initialise the parameters from _attributes and user attributes
        """
        for key in (self._attributes + self.attributes):
            setattr(self, key, None)

    def _setParameters(self, **parameters):
        """Set parameters for peakPicker instance
        """
        for key, value in parameters.items():
            if key in (self._attributes + self.attributes):
                setattr(self, key, value)

    def setParameters(self, **parameters):
        """Set parameters as attributes of self

        Example calling function:

        ::

        >>> peakPicker.setParameters(**parameters)
        >>> peakPicker.setParameters(fitMethod='gaussian', dropFactor=0.1)

        The contents of parameters to be defined by the peakPicker class.
        In the above example, 'fitMethod' and 'dropFactor' are defined in the baseClass, but their
        properties and types are to be defined by the subclass.

        :param parameters: dict of key, value pairs
        """
        self._setParameters(**parameters)
        self._storeAttributes()

    def _checkParameters(self):
        """
        Check whether the parameters are the correct types
        """
        # This can check the common parameters, subclassing can check local
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    def _storeAttributes(self):
        """Store peakPicker attributes that need restoring when a project is reloaded
        User attributes are listed in self.attributes at the head of the peakPicker class
        """
        if self.spectrum is None:
            raise RuntimeError('%s._storeAttributes: spectrum not defined' % self.__class__.__name__)

        values = {k: v
                  for k, v in self.__dict__.items()
                  if k in (self._attributes + self.attributes)}
        values = deepcopy(values)

        self.spectrum.setParameter(PEAKPICKERSTORE, PEAKPICKERPARAMETERS, values)
        self.spectrum.setParameter(PEAKPICKERSTORE, PEAKPICKER, self.peakPickerType)

    def _restoreAttributes(self):
        """Restore important peakPicker attributes when a project is reloaded
        User attributes are listed in self.attributes at the head of the peakPicker class
        """
        if self.spectrum is None:
            raise RuntimeError('%s._storeAttributes: spectrum not defined' % self.__class__.__name__)

        _pickerParams = self.spectrum.getParameter(PEAKPICKERSTORE, PEAKPICKERPARAMETERS)
        if _pickerParams and isinstance(_pickerParams, dict):
            self._setParameters(**_pickerParams)
        else:
            getLogger().debug(f'attributes not restored from {self.spectrum}')

    def _clearAttributes(self):
        """Remove the peak picker settings from the spectrum
        """
        if self.spectrum is None:
            raise RuntimeError('%s._clearAttributes: spectrum not defined' % self.__class__.__name__)

        self.spectrum.setParameter(PEAKPICKERSTORE, PEAKPICKERPARAMETERS, None)
        self.spectrum.setParameter(PEAKPICKERSTORE, PEAKPICKER, None)

    #=========================================================================================

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

    def pickPeaks(self, axisDict, peakList, positiveThreshold=None, negativeThreshold=None) -> list:
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

        # store the threshold values
        self.positiveThreshold = positiveThreshold
        self.negativeThreshold = negativeThreshold

        self.sliceTuples = self.spectrum._axisDictToSliceTuples(axisDict)

        if self.defaultPointExtension:
            # add default points to extend pick region
            self.sliceTuples = [(sLeft - self.defaultPointExtension, sRight + self.defaultPointExtension) if sLeft <= sRight else
                                (sLeft + self.defaultPointExtension, sRight - self.defaultPointExtension)
                                for sLeft, sRight in self.sliceTuples]

        # TODO: use Spectrum aliasing definitions once defined
        data = self.spectrum.dataSource.getRegionData(self.sliceTuples, aliasingFlags=[1] * self.spectrum.dimensionCount)

        peaks = self.findPeaks(data)
        getLogger().debug('%s.pickPeaks: found %d peaks in spectrum %s; %r' %
                          (self.__class__.__name__, len(peaks), self.spectrum, axisDict))

        corePeaks = []
        if len(peaks) > 0:
            self.lastPickedPeaks = peaks
            corePeaks = self._createCorePeaks(peaks, peakList)

        self._storeAttributes()
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
            pointPositions = [float(p) + float(self.sliceTuples[idx][0]) for idx, p in enumerate(pk.points[::-1])]

            # check whether a peak already exists at pointPositions in the peakList
            if self._validatePointPeak(pointPositions, peakList):

                if pk.height is None:
                    # height was not defined; get the interpolated value from the data
                    pk.height = self.spectrum.dataSource.getPointValue(pointPositions)

                if (self.positiveThreshold and pk.height > self.positiveThreshold) or \
                        (self.negativeThreshold and pk.height < self.negativeThreshold):
                    cPeak = peakList.newPeak(pointPositions=pointPositions, height=pk.height, volume=pk.volume, pointLineWidths=pk.lineWidths)
                    if self.autoFit:
                        peakParabolicInterpolation(cPeak, update=True)
                    corePeaks.append(cPeak)

        return corePeaks

    def _validatePointPeak(self, pointPositions, peakList):
        """
        Check whether a peak already exists at this position
        :param pointPositions:
        :param peakList:
        :return: true if pointPositions is valid
        """
        intPositions = [int((pos - 1) % pCount) + 1 for pos, pCount in zip(pointPositions, self.spectrum.pointCounts)]  # API position starts at 1
        existingPositions = [[int(pp) for pp in pk.pointPositions] for pk in peakList.peaks]

        return intPositions not in existingPositions

    def __str__(self):
        return '<%s for %r>' % (self.__class__.__name__, self.spectrum.name)
