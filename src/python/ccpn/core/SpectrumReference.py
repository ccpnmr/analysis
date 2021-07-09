"""
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
__dateModified__ = "$dateModified: 2021-07-09 11:36:32 +0100 (Fri, July 09, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Optional, Sequence, Tuple

from ccpn.core.lib import Pid
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.Spectrum import Spectrum
import ccpn.core.lib.SpectrumLib as specLib

from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
from ccpn.core.lib.ContextManagers import newObject


class SpectrumReference(AbstractWrapperObject):
    """A SpectrumReference holds detailed information about axes and referencing
    needed for e.g. multple-quantum, projection, and reduced-dimensionality experiments.

    SpectrumRefefences can only exist for frequency dimensions.
    Required for describing experiments with assignable splittings (e.g. J-coupling, RDC),
    reduced dimensionality, more than one nucleus per axis,
    or multi-atom parameters (J-dimensions, MQ dimensions)."""

    #: Short class name, for PID.
    shortClassName = 'SR'
    # Attribute it necessary as subclasses must use superclass className
    className = 'SpectrumReference'

    _parentClass = Spectrum

    # Type of dimension. Always 'Frequency' for frequency (Fourier transformed) dimension
    _dimensionType = specLib.DIMENSION_FREQUENCY  # 'Frequency'

    #: Name of plural link to instances of class
    _pluralLinkName = 'spectrumReferences'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = Nmr.DataDimRef._metaclass.qualifiedName()

    #-----------------------------------------------------------------------------------------

    def __init__(self, project, wrappedData):
        super().__init__(project, wrappedData)

    #-----------------------------------------------------------------------------------------
    # CCPN properties
    #-----------------------------------------------------------------------------------------

    @property
    def _apiSpectrumReference(self) -> Nmr.DataDimRef:
        """ CCPN DataDimRef matching Spectrum"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """object identifier, used for id"""
        dataDimRef = self._wrappedData
        return Pid.createId(dataDimRef.dataDim.dim, dataDimRef.expDimRef.serial)

    @property
    def _localCcpnSortKey(self) -> Tuple:
        """Local sorting key, in context of parent."""
        dataDimRef = self._wrappedData
        return (dataDimRef.dataDim.dim, dataDimRef.expDimRef.serial)

    @property
    def _parent(self) -> Spectrum:
        """Spectrum containing spectrumReference."""
        return self._project._data2Obj[self._wrappedData.dataDim.dataSource]

    @property
    def _dataDim(self):
        """
        :return: dataDim instance
        """
        return self._wrappedData.dataDim

    @property
    def _dataDimRef(self):
        """
        :return: dataDim instance
        """
        return self._wrappedData

    @property
    def _expDim(self):
        """
        :return: expDim instance
        """
        return self._dataDim.expDim

    @property
    def _expDimRef(self):
        """
        :return: expDimRef instance
        """
        return self._wrappedData.expDimRef

    @property
    def _isFrequencyDimension(self) -> bool:
        """True if this is a frequency dimension; mainly used to implement code to upward compatible with v2"""
        return self._dataDim.className == 'FreqDataDim'

    @property
    def _isSampledDimension(self) -> bool:
        """True if this is a sampled dimension; mainly used to implement code to upward compatible with v2"""
        return self._dataDim.className == 'SampledDataDim'

    @property
    def _isFidDimension(self) -> bool:
        """True if this is a Fid dimension; mainly used to implement code to upward compatible with v2"""
        return self._dataDim.className == 'FidDataDim'

    spectrum = _parent

    #-----------------------------------------------------------------------------------------
    # Object properties
    #-----------------------------------------------------------------------------------------

    @property
    def dimension(self) -> int:
        """dimension number"""
        return self._dataDim.dim

    @property
    def isAcquisition(self) -> bool:
        """True if dimension is acquisition"""
        return self._expDim.isAcquisition

    @isAcquisition.setter
    def isAcquisition(self, value):
        self._expDim.isAcquisition = value

    @property
    def pointCount(self):
        """Number of points in this dimension"""
        if self._isFidDimension and hasattr(self._dataDim, 'numPointsValid'):
            # GWV: compatibility with v2?
            result = self._dataDim.numPointsValid
        else:
            result = self._dataDim.numPoints
        return result

    @pointCount.setter
    def pointCount(self, value):
        # To decouple pointCount from spectralWidth
        oldSw = self.spectralWidthHz
        if self._isFidDimension:
            # GWV: compatibility with v2?
            self._dataDim.numPointsValid = value
        else:
            self._dataDim.numPoints = value
        self.spectralWidthHz = oldSw

    @property
    def isComplex(self):
        """Boolean indicating complex data for this dimension"""
        return self._dataDim.isComplex

    @isComplex.setter
    def isComplex(self, value):
        self._dataDim.isComplex = bool(value)

    @property
    def dimensionType(self) -> Optional[str]:
        """Dimension type ('Time' / 'Frequency' / 'Sampled')"""
        if not self._hasInternalParameter('dimensionType'):
            result = specLib.DIMENSION_FREQUENCY
            # self._dimensionType = result
        else:
            result = self._getInternalParameter('dimensionType')
        return result

    @dimensionType.setter
    def dimensionType(self, value):
        if value not in specLib.DIMENSIONTYPES:
            raise ValueError('dimensionType should be one of %r' % specLib.DIMENSIONTYPES)
        self._setInternalParameter('dimensionType', value)

    @property
    def isReversed(self) -> bool:
        """:return True if dimension is reversed
        depricated!
        """
        return self._expDimRef.isAxisReversed

    @property
    def spectrometerFrequency(self) -> float:
        """Absolute frequency at carrier (or at splitting 0.0). In MHz or dimensionless."""
        return self._expDimRef.sf

    @spectrometerFrequency.setter
    def spectrometerFrequency(self, value):
        self._expDimRef.sf = value

    @property
    def measurementType(self) -> Optional[str]:
        """Type of NMR measurement referred to by this reference. Legal values are:
        'Shift','ShiftAnisotropy','JCoupling','Rdc','TROESY','DipolarCoupling',
        'MQShift','T1','T2','T1rho','T1zz' --- defined SpectrumLib.MEASUREMENT_TYPES
        """
        # TODO: Model-change to allow None
        return self._expDimRef.measurementType

    @measurementType.setter
    def measurementType(self, value):
        self._expDimRef.measurementType = value

    # GWV this was carried from the previous Spectrum implementation; no idea why, but it mattered
    # point1 = 1 - dataDim.pointOffset
    # result[ii] = tuple(sorted((ff(point1), ff(point1 + dataDim.numPointsOrig))

    @property
    def maxAliasedFrequency(self) -> float:
        """maximum possible peak frequency (in ppm) for this reference """
        if (result := self._expDimRef.maxAliasedFreq) is None:
            point_1 = 1 - self._dataDim.pointOffset
            point_n = point_1 + self.pointCount
            result = self.pointToValue((point_n))
        return result

    @maxAliasedFrequency.setter
    def maxAliasedFrequency(self, value):
        self._expDimRef.maxAliasedFreq = value

    @property
    def minAliasedFrequency(self) -> float:
        """minimum possible peak frequency (in ppm) for this reference """
        if (result := self._expDimRef.minAliasedFreq) is None:
            point_1 = 1 - self._dataDim.pointOffset
            result = self.pointToValue((point_1))
        return result

    @minAliasedFrequency.setter
    def minAliasedFrequency(self, value):
        self._expDimRef.minAliasedFreq = value

    @property
    def limits(self) -> Tuple[float, float]:
        """Return the limits of this dimension as a tuple of floats"""
        if self.dimensionType == specLib.DIMENSION_FREQUENCY:
            return (self.pointToValue(1), self.pointToValue(self.pointCount + 1))
        elif self.dimensionType == specLib.DIMENSION_TIME:
            return (self.pointToValue(1), self.pointToValue(self.pointCount + 1))
            # return (0.0, self._valuePerPoint * self.pointCount)
        else:
            raise RuntimeError('SpectrumReference.limits not implemented for sampled data')

    @property
    def isotopeCode(self) -> Optional[str]:
        """Isotope identification strings for isotopes.
        """
        if len(self._isotopeCodes) > 0:
            return self._isotopeCodes[0]
        return None

    @isotopeCode.setter
    def isotopeCode(self, value: str):
        self._isotopeCodes = [value]

    # GWV: moved this to a private attributes, as currently we only support one isotopeCode per dimension
    @property
    def _isotopeCodes(self) -> Tuple[str, ...]:
        """Isotope identification strings for isotopes.
        NB there can be several isotopes for e.g. J-coupling or multiple quantum coherence.
        """
        return self._expDimRef.isotopeCodes

    @_isotopeCodes.setter
    def _isotopeCodes(self, value: Sequence):
        self._expDimRef.isotopeCodes = value

    @property
    def foldingMode(self) -> Optional[str]:
        """folding mode matching reference (values: 'circular', 'mirror', None)"""
        if not self._hasInternalParameter('foldingMode'):
            result = None
            self.foldingMode = result
        else:
            result = self._getInternalParameter('foldingMode')
        return result

    @foldingMode.setter
    def foldingMode(self, value):
        if value not in list(specLib.FOLDING_MODES) + [None]:
            raise ValueError('foldingMode should be one of %r or None; got %r' %
                             (specLib.FOLDING_MODES, value))
        self._setInternalParameter('foldingMode', value)

    @property
    def axisCode(self) -> str:
        """Reference axisCode """
        return self._expDimRef.axisCode

    @axisCode.setter
    def axisCode(self, value: str):
        self._expDimRef.axisCode = value

    @property
    def axisUnit(self) -> str:
        """unit for transformed data using their reference (most commonly 'ppm')"""
        return self._expDimRef.unit

    @axisUnit.setter
    def axisUnit(self, value: str):
        self._expDimRef.unit = value

    # Attributes belonging to DataDimRef

    @property
    def referencePoint(self) -> float:
        """point used for axis (chemical shift) referencing."""
        return self._dataDimRef.refPoint

    @referencePoint.setter
    def referencePoint(self, value):
        self._dataDimRef.refPoint = value

    @property
    def referenceValue(self) -> float:
        """ppm-value used for axis (chemical shift) referencing."""
        return self._dataDimRef.refValue

    @referenceValue.setter
    def referenceValue(self, value: float):
        self._dataDimRef.refValue = value

    @property
    def spectralWidthHz(self) -> float:
        """spectral width in Hz"""
        return self._dataDim.spectralWidth

    @spectralWidthHz.setter
    def spectralWidthHz(self, value: float):
        swOld = self.spectralWidthHz
        # self._dataDim.spectralWidth = value # This is not allowed; it needs to go via valuePerPoint
        self._valuePerPoint *= (value / swOld)

    @property
    def spectralWidth(self) -> float:
        """spectral width in ppm"""
        return self._dataDimRef.spectralWidth

    @spectralWidth.setter
    def spectralWidth(self, value: float):
        swOld = self.spectralWidth
        # self._dataDimRef.spectralWidth = value  # This is not allowed; it needs to go via valuePerPoint
        self._valuePerPoint = (value / swOld)

    # This is a crucial property that effectively governs the spectral width (both in Hz and ppm)
    #     # We assume that the number of points is constant, so setting SW changes valuePerPoint
    #     dataDimRef = self._wrappedData
    #     swOld = dataDimRef.spectralWidth
    #     if dataDimRef.localValuePerPoint:
    #         dataDimRef.localValuePerPoint *= (value / swOld)
    #     else:
    #         dataDimRef.dataDim.valuePerPoint *= (value / swOld)
    @property
    def _valuePerPoint(self) -> float:
        """Value per point: in Hz for Frequency domain data, in secs for time/fid domain data"""
        return self._dataDim.valuePerPoint

    @_valuePerPoint.setter
    def _valuePerPoint(self, value: float):
        self._dataDim.valuePerPoint = value

    # @property
    # def numPointsOrig(self) -> bool:
    #     """numPointsOrig"""
    #     return self._wrappedData.dataDim.numPointsOrig

    @property
    def phase0(self) -> Optional[float]:
        """Zero-order phase"""
        return (self._dataDim.phase0 if not self._isSampledDimension else None)

    @phase0.setter
    def phase0(self, value):
        self._dataDim.phase0 = value

    @property
    def phase1(self) -> Optional[float]:
        """First-order phase"""
        return (self._dataDim.phase1 if not self._isSampledDimension else None)

    @phase1.setter
    def phase1(self, value):
        self._dataDim.phase1 = value

    @property
    def windowFunction(self) -> Optional[str]:
        """Window function
        e.g. 'EM', 'GM', 'SINE', 'QSINE', .... (defined in SpectrumLib.WINDOW_FUNCTIONS)
        """
        return (self._dataDim.windowFunction if not self._isSampledDimension else None)

    @windowFunction.setter
    def windowFunction(self, value):
        if not value in list(specLib.WINDOW_FUNCTIONS) + [None]:
            raise ValueError('windowFunction should be one of %r or None; got %r' % (specLib.WINDOW_FUNCTIONS, value))
        self._dataDim.windowFunction = value

    @property
    def lorentzianBroadening(self) -> Optional[float]:
        """Lorenzian broadening (in Hz)"""
        return (self._dataDim.lorentzianBroadening if not self._isSampledDimension else None)

    @lorentzianBroadening.setter
    def lorentzianBroadening(self, value):
        self._dataDim.lorentzianBroadening = value

    @property
    def gaussianBroadening(self) -> Optional[float]:
        """Gaussian broadening"""
        return (self._dataDim.gaussianBroadening if not self._isSampledDimension else None)

    @gaussianBroadening.setter
    def gaussianBroadening(self, value):
        self._dataDim.gaussianBroadening = value

    @property
    def sineWindowShift(self) -> Optional[float]:
        """Shift of sine/sine-square window function (in degrees)"""
        return (self._dataDim.sineWindowShift if not self._isSampledDimension else None)

    @sineWindowShift.setter
    def sineWindowShift(self, value):
        self._dataDim.sineWindowShift = value

    @property
    def assignmentTolerance(self) -> float:
        """Assignment Tolerance"""
        return self._dataDimRef.assignmentTolerance

    @assignmentTolerance.setter
    def assignmentTolerance(self, value):
        self._dataDimRef.assignmentTolerance = value

    #=========================================================================================
    # Implementation properties and functions
    #=========================================================================================

    @property
    def _serial(self) -> int:
        """Spectrum reference serial number"""
        return self._expDimRef.serial

    @classmethod
    def _getAllWrappedData(cls, parent: Spectrum) -> list:
        """get wrappedData (Nmr.DataDimRefs) for all Spectrum children of parent Spectrum"""
        return [y for x in parent._wrappedData.sortedDataDims() if hasattr(x, 'dataDimRefs')
                for y in x.sortedDataDimRefs()]

    def _finaliseAction(self, action: str):
        if not super()._finaliseAction(action):
            return

        #TODO: GWV asks: why do we have this?
        if action == 'change':
            for peak in self.spectrum.peaks:
                peak._finaliseAction('change')

    #=========================================================================================
    # CCPN functions
    #=========================================================================================
    def pointToValue(self, point: float) -> float:
        """:return ppm-value corresponding to point (float)"""
        return self._wrappedData.pointToValue(point)

    def valueToPoint(self, value: float) -> float:
        """:return point (float) corresponding to ppm-value"""
        return self._wrappedData.valueToPoint(value)


#=========================================================================================
# Connections to parents:
#=========================================================================================

@newObject(SpectrumReference)
def _newSpectrumReference(self: Spectrum, dimension: int, dataSource) -> SpectrumReference:
    """Create new SpectrumReference.

    :param dimension:
    :param dataSource: A spectrum dataSource instance

    :return: a new SpectrumReference instance.

    CCPNINTERNAL: called from _newSpectrumFromDataSource
    """

    axis = dimension - 1

    nPoints = dataSource.pointCounts[axis]
    isComplex = dataSource.isComplex[axis]

    dimType = dataSource.dimensionTypes[axis]
    if dimType == specLib.DIMENSION_FREQUENCY:
        # valuePerPoint is digital resolution in Hz
        # TODO: accommodate complex points
        valuePerPoint = dataSource.spectralWidthsHz[axis] / float(nPoints)
        axisUnit = 'ppm'

    elif dimType == specLib.DIMENSION_TIME:
        # valuePerPoint is dwell time
        # valuePerPoint = 1.0 / dataSource.spectralWidthsHz[n] if _isComplex \
        #                  else 0.5 / dataSource.spectralWidthsHz[n]

        # However, for now we leave it as until we have settled the FidDataDim issue (see below)
        valuePerPoint = dataSource.spectralWidthsHz[axis] / float(nPoints)
        axisUnit = 'point'  # model does not allow 'sec'!

    else:
        raise RuntimeError('Invalid dimensionType[%d]: "%s"' % (axis, dimType))

    spectrometerFrequency = dataSource.spectrometerFrequencies[axis]
    isotopeCodes = dataSource.isotopeCodes[axis:axis + 1]
    axisCode = dataSource.axisCodes[axis]

    # generate some api objects
    # Initialise the dimension; This seems a very complicated data structure! (GWV)
    apiDataSource = self._wrappedData
    apiExperiment = apiDataSource.experiment
    apiExpDim = apiExperiment.findFirstExpDim(dim=dimension)

    apiExpDim.isAcquisition = False  # undated later

    # for now, we have to give all dimensions a FreqDataDim, otherwise the code crashes
    # A FidDataDim cannot have a DataDimRef, and that is the object used as _wrappedData!
    if (apiDataDim := apiDataSource.newFreqDataDim(dim=dimension,
                                                   expDim=apiExpDim,
                                                   numPoints=nPoints,
                                                   numPointsOrig=nPoints,
                                                   pointOffset=0,
                                                   isComplex=isComplex,
                                                   valuePerPoint=valuePerPoint
                                                   )
    ) is None:
        raise RuntimeError("Cannot create SpectrumReference for dimension: %s" % dimension)

    if (apiExpDimRef := apiExpDim.newExpDimRef(sf=spectrometerFrequency,
                                               isotopeCodes=isotopeCodes,
                                               measurementType='Shift',
                                               isFolded=False,
                                               axisCode=axisCode,
                                               unit=axisUnit,
                                               minAliasedFreq=None,
                                               maxAliasedFreq=None,
                                               )
    ) is None:
        raise RuntimeError("Cannot create SpectrumReference for dimension: %s" % dimension)

    if (apiDataDimRef := apiDataDim.newDataDimRef(expDimRef=apiExpDimRef,
                                                  refPoint=0.0,
                                                  refValue=0.0
                                                  )
    ) is None:
        raise RuntimeError("Cannot create SpectrumReference for dimension: %s" % dimension)

    if (result := self.project._data2Obj[apiDataDimRef]) is None:
        raise RuntimeError("Cannot create SpectrumReference for dimension: %s" % dimension)

    return result


#EJB 20181205: moved to Spectrum
# Spectrum.newSpectrumReference = _newSpectrumReference
# del _newSpectrumReference


# Notifiers:
# TODO: Do we really need this?
def _isAcquisitionHasChanged(project: Project, apiExpDim: Nmr.ExpDim):
    """Refresh SpectrumReference when ExpDim.isAcquisition has changed"""
    for dataDim in apiExpDim.dataDims:
        for dataDimRef in dataDim.dataDimRefs:
            project._modifiedApiObject(dataDimRef)


Project._setupApiNotifier(_isAcquisitionHasChanged, Nmr.ExpDim, '')
del _isAcquisitionHasChanged

Project._apiNotifiers.extend(
        (('_notifyRelatedApiObject', {'pathToObject': 'dataDimRefs', 'action': 'change'},
          Nmr.ExpDimRef._metaclass.qualifiedName(), ''),
         )
        )
className = Nmr.FreqDataDim._metaclass.qualifiedName()
Project._apiNotifiers.append(
        ('_notifyRelatedApiObject', {'pathToObject': 'dataDimRefs', 'action': 'change'}, className, ''),
        )
