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
__dateModified__ = "$dateModified: 2021-06-22 09:51:59 +0100 (Tue, June 22, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2021-01-13 10:28:41 +0000 (Wed, Jan 13, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from json import loads
from collections import OrderedDict
from ccpn.util.traits.CcpNmrJson import CcpNmrJson
from ccpn.util.traits.CcpNmrTraits import CFloat, CInt, CBool, CString
from ccpn.util.Logging import getLogger
from ccpn.util.Common import loadModules
from ccpn.framework.PathsAndUrls import peakPickerPath


PEAKPICKERPARAMETERS = '_peakPickerParameters'


#=========================================================================================
# Available peakPicker methods
#=========================================================================================

def getPeakPickerTypes() -> OrderedDict:
    """Get peakPicker types

    :return: a dictionary of (type-identifier-strings, PeakPicker classes) as (key, value) pairs
    """
    # from ccpn.core.lib.PeakPickers.PeakPickerNd import PeakPickerNd
    # from ccpn.core.lib.PeakPickers.Simple1DPeakPicker import Simple1DPeakPicker
    # from ccpn.core.lib.PeakPickers.NmrgluePeakPicker import NmrgluePeakPicker

    # load all from folder
    loadModules([peakPickerPath, ])

    return PeakPickerABC._peakPickers


def getPeakPicker(peakPickerType, spectrum, *args, **kwds):
    """Return instance of class if PeakPicker defined by peakPickerType has been registered

    :param peakPickerType: type str; reference to peakPickerType of peakPicker class
    :return: new instance of class if registered else None
    """
    peakPickerTypes = getPeakPickerTypes()
    cls = peakPickerTypes.get(peakPickerType)
    if cls is None:
        raise ValueError('getPeakPicker: invalid format "%s"; must be one of %s' %
                         (peakPickerType, [k for k in peakPickerTypes.keys()])
                         )

    return cls(spectrum, *args, **kwds)


def isRegistered(peakPickerType):
    """Return True if a PeakPicker class of type peakPickerType is registered

    :param peakPickerType: type str; reference to peakPickerType of peakPicker class
    :return: True if class referenced by peakPickerType has been registered else False
    """
    return getPeakPickerTypes().get(peakPickerType) is not None


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


#=========================================================================================
# Start of class
#=========================================================================================

class PeakPickerABC(CcpNmrJson):
    """ABC for implementation of a peak picker
    """

    classVersion = 1.0  # For json saving

    #=========================================================================================
    # to be subclassed
    #=========================================================================================

    peakPickerType = None  # A unique string identifying the peak picker
    defaultPointExtension = 1  # points to extend the region to pick on either side
    onlyFor1D = False

    #=========================================================================================
    # data formats
    #=========================================================================================
    # A dict of registered dataFormat: filled by _registerPeakPicker classmethod, called once after
    # each definition of a new derived class
    _peakPickers = OrderedDict()

    @classmethod
    def register(cls):
        """register cls.peakPickerType"""
        if cls.peakPickerType in cls._peakPickers:
            raise RuntimeError(f'PeakPicker "{cls.peakPickerType}" was already registered')
        PeakPickerABC._peakPickers[cls.peakPickerType] = cls
        getLogger().info(f'Registering peakPicker class {cls.peakPickerType}')

    @classmethod
    def _restorePeakPicker(cls, spectrum):
        """Create a new peakPicker instance defined by parameters stored within
        spectrum Ccpn Internal data
        """
        from ccpn.core.Spectrum import Spectrum

        if spectrum is None:
            raise ValueError('%s: spectrum is None' % cls.__class__.__name__)
        if not isinstance(spectrum, Spectrum):
            raise ValueError('%s: spectrum is not of Spectrum class' % cls.__class__.__name__)

        try:
            # read peakPicker from CCPNinternal
            jsonData = spectrum._getInternalParameter(PEAKPICKERPARAMETERS)
            _pickerType = dict(loads(jsonData)).get('_metadata').get('className')
        except Exception as es:
            getLogger().debug(f'peakPicker not restored from {spectrum}')

        else:
            if _pickerType:
                _picker = getPeakPicker(_pickerType, spectrum)
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
    # parameter definitions and mappings onto the Spectrum class
    #=========================================================================================

    keysInOrder = True  # maintain the definition order

    saveAllTraitsToJson = True
    version = 1.0  # for json saving

    # list of core peakPicker attributes that need to be restored when the spectrum is loaded
    dimensionCount = CInt(default_value=0)
    pointExtension = CInt(default_value=0)
    autoFit = CBool(default_value=False)
    dropFactor = CFloat(default_value=0.1)
    fitMethod = CString(allow_none=True, default_value=None)
    positiveThreshold = CFloat(default_value=0.0)
    negativeThreshold = CFloat(default_value=0.0)

    #=========================================================================================
    # start of methods
    #=========================================================================================

    def __init__(self, spectrum, autoFit=False):
        """Initialise the instance and associate with spectrum

        :param spectrum: associate instance with spectrum and import spectrum's parameters
        :param autoFit:
        """
        from ccpn.core.Spectrum import Spectrum

        if self.peakPickerType is None:
            raise RuntimeError('%s: peakPickerType is undefined' % self.__class__.__name__)

        if spectrum is None:
            raise ValueError('%s: spectrum is None' % self.__class__.__name__)
        if not isinstance(spectrum, Spectrum):
            raise ValueError('%s: spectrum is not of Spectrum class' % self.__class__.__name__)

        if spectrum.dimensionCount > 1 and self.onlyFor1D:
            raise ValueError('%s only works for 1D spectra' % self.__class__.__name__)

        super().__init__()

        # default parameters for all peak pickers
        self.setDefaultParameters()

        # initialise from parameters
        self.spectrum = spectrum
        self.dimensionCount = spectrum.dimensionCount
        self.pointExtension = self.defaultPointExtension
        self.autoFit = autoFit

        # attributes not required to be persistent between load/save
        self.lastPickedPeaks = None
        self.sliceTuples = None

    def setDefaultParameters(self):
        """Set default values for all parameters
        """
        for par in self.keys():
            self.setTraitDefaultValue(par)

    def _setParameters(self, **parameters):
        """Set parameters for peakPicker instance
        """
        for par, value in parameters.items():
            if par in self.keys():
                self.setTraitValue(par, value)

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
        """Check whether the parameters are the correct types
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

        jsonData = self.toJson()
        self.spectrum._setInternalParameter(PEAKPICKERPARAMETERS, jsonData)

    def _restoreAttributes(self):
        """Restore important peakPicker attributes when a project is reloaded
        User attributes are listed in self.attributes at the head of the peakPicker class
        """
        if self.spectrum is None:
            raise RuntimeError('%s._restoreAttributes: spectrum not defined' % self.__class__.__name__)

        jsonData = self.spectrum._getInternalParameter(PEAKPICKERPARAMETERS)
        if jsonData is None or len(jsonData) == 0:
            raise RuntimeError('%s._restoreAttributes: json data appear to be corrupted' % self.__class__.__name__)

        self.fromJson(jsonData)

    def _detachFromSpectrum(self):
        """Remove all peakPicker settings from the spectrum
        """
        if self.spectrum is None:
            raise RuntimeError('%s._detachFromSpectrum: spectrum not defined' % self.__class__.__name__)

        # remove all links to spectrum
        self.spectrum._setInternalParameter(PEAKPICKERPARAMETERS, None)
        self.spectrum = None

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
        data = self.spectrum._dataSource.getRegionData(self.sliceTuples, aliasingFlags=[1] * self.spectrum.dimensionCount)

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
        from ccpn.core.lib.peakUtils import peakParabolicInterpolation

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
                    pk.height = self.spectrum._dataSource.getPointValue(pointPositions)

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


#end class

from ccpn.util.traits.CcpNmrTraits import Instance
from ccpn.util.traits.TraitJsonHandlerBase import CcpNmrJsonClassHandlerABC


class PeakPickerTrait(Instance):
    """Specific trait for a PeakPicker instance.
    """
    klass = PeakPickerABC

    def __init__(self, **kwds):
        Instance.__init__(self, klass=self.klass, allow_none=True, **kwds)


    class jsonHandler(CcpNmrJsonClassHandlerABC):
        # klass = PeakPickerABC
        pass
