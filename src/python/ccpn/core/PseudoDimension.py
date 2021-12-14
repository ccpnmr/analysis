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
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2021-12-14 21:34:19 +0000 (Tue, December 14, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Tuple, Sequence, Optional

from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core._implementation.SpectrumDimensionAttributes import SpectrumDimensionAttributes
from ccpn.core.Project import Project
from ccpn.core.Spectrum import Spectrum
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import SampledDataDim as ApiSampledDataDim
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import ExpDimRef as ApiExpDimRef


class PseudoDimension(AbstractWrapperObject, SpectrumDimensionAttributes):
    """A sampled Spectrum axis with non-gridded values. Can be used (V2 legacy) to describe
    sampled-value axes in pseudo-2D and nD experiments, such as the time delay axis for T1
    experiments."""

    #: Short class name, for PID.
    shortClassName = 'PD'
    # Attribute it necessary as subclasses must use superclass className
    className = 'PseudoDimension'

    _parentClass = Spectrum

    # Type of dimension. Always 'Freq' for frequency (Fourier transformed) dimension
    dimensionType = 'Sampled'

    #: Name of plural link to instances of class
    _pluralLinkName = 'pseudoDimensions'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiSampledDataDim._metaclass.qualifiedName()

    #-----------------------------------------------------------------------------------------

    def __init__(self, project, wrappedData):
        super().__init__(project, wrappedData)

    #-----------------------------------------------------------------------------------------
    # CCPN properties
    #-----------------------------------------------------------------------------------------

    # CCPN properties
    @property
    def _apiSampledDataDim(self) -> ApiSampledDataDim:
        """ CCPN DataSource matching Spectrum"""
        return self._wrappedData

    @property
    def _dataDim(self):
        """
        :return: dataDim instance
        """
        return self._wrappedData

    @property
    def _dataDimRef(self):
        """
        :return: dataDim instance; not present for SampledDataDim
        """
        return None

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
        return list(self._expDim.expDimRefs)[0]

    @property
    def _key(self) -> str:
        """object identifier, used for id"""

        return str(self._wrappedData.dim)

    @property
    def _localCcpnSortKey(self) -> Tuple:
        """Local sorting key, in context of parent."""
        return (self._wrappedData.dim,)

    @property
    def _parent(self) -> Spectrum:
        """Spectrum containing PseudoDimension."""
        return self._project._data2Obj[self._wrappedData.dataSource]

    spectrum = _parent

    #-----------------------------------------------------------------------------------------
    # Object properties; specific to PseudoDimension
    #-----------------------------------------------------------------------------------------

    @property
    def axisParameter(self) -> str:
        """Name of the condition or parameter that is varied along the axis.
        Use 'sample' if samples are different for each point on the dimension"""
        return self._wrappedData.conditionVaried

    @axisParameter.setter
    def axisParameter(self, value: str):
        self._wrappedData.conditionVaried = value

    @property
    def pointValues(self) -> Tuple[float, ...]:
        """point values for PseudoDimension)."""
        return tuple(self._wrappedData.pointValues)

    @pointValues.setter
    def pointValues(self, value: Sequence) -> tuple:
        self._wrappedData.pointValues = value

    @property
    def pointErrors(self) -> Tuple[float, ...]:
        """point errors for PseudoDimension)."""
        return tuple(self._wrappedData.pointErrors)

    @pointErrors.setter
    def pointErrors(self, value: Sequence) -> tuple:
        self._wrappedData.pointErrors = value

    @property
    def isAcquisition(self) -> bool:
        """Always False"""
        return False

    @isAcquisition.setter
    def isAcquisition(self, value):
        pass

    @property
    def isReversed(self) -> bool:
        """Always False
        """
        return False

    @isReversed.setter
    def isReversed(self, value):
        """Set whether the axis is reversed - isReversed implies that ppm values decrease as point values increase
        """
        pass

    @property
    def maxAliasedFrequency(self) -> float:
        """maximum possible peak frequency; emulated to be always ppmValue of
        pointCounts +0.5
        """
        return self.pointToValue(float(self.pointCount)+0.5)

    @maxAliasedFrequency.setter
    def maxAliasedFrequency(self, value):
        pass

    @property
    def minAliasedFrequency(self) -> float:
        """minimum possible frequency; emulated to be always ppmValue of
        point 0.5
        """
        result = self.pointToValue(0.5)
        return result

    @minAliasedFrequency.setter
    def minAliasedFrequency(self, value):
        pass

    @property
    def spectrumLimits(self) -> Tuple[float, float]:
        """Return the limits of this spectrum dimension as a tuple of floats"""
        return (self.pointToValue(1.0), self.pointToValue(float(self.pointCount)))

    @property
    def foldingLimits(self) -> Tuple[float, float]:
        """Return the foldingLimits of this dimension as a tuple of floats.
        """
        return (self.pointToValue(0.5), self.pointToValue(float(self.pointCount) + 0.5))

    @property
    def referencePoint(self) -> float:
        """point used for axis (chemical shift) referencing.
        emulated to always be 1.0
        """
        return 1.0

    @referencePoint.setter
    def referencePoint(self, value):
        pass

    @property
    def referenceValue(self) -> float:
        """ppm-value used for axis (chemical shift) referencing.
        emulated to always be pointCount
        """
        return float(self.pointCount)

    @referenceValue.setter
    def referenceValue(self, value: float):
        pass

    @property
    def spectralWidthHz(self) -> float:
        """spectral width in Hz
        emulated to always be 1.0 * spectrometerFrequency
        """
        return self.spectralWidth*self.spectrometerFrequency

    @spectralWidthHz.setter
    def spectralWidthHz(self, value: float):
        pass

    @property
    def spectralWidth(self) -> float:
        """spectral width in ppm
        emulated to always be self.pointCount
        """
        return float(self.pointCount)

    @spectralWidth.setter
    def spectralWidth(self, value: float):
        pass

    @property
    def _valuePerPoint(self) -> float:
        """Value per point in Hz for Frequency domain data, in secs for time/fid domain data"""
        return self.spectralWidthHz / self.pointCount

    @_valuePerPoint.setter
    def _valuePerPoint(self, value: float):
        pass

    @property
    def phase0(self) -> Optional[float]:
        """Zero-order phase; always None"""
        return None

    @phase0.setter
    def phase0(self, value):
        pass

    @property
    def phase1(self) -> Optional[float]:
        """First-order phase; always None"""
        return None

    @phase1.setter
    def phase1(self, value):
        pass

    @property
    def assignmentTolerance(self) -> float:
        """Assignment Tolerance; Always 0.0
        """
        return 0.0

    @assignmentTolerance.setter
    def assignmentTolerance(self, value):
        pass

    @property
    def defaultAssignmentTolerance(self) -> float:
        """Default assignment tolerance (in ppm);
        """
        return 0.0

    #=========================================================================================
    # CCPN functions
    #=========================================================================================
    def pointToValue(self, point: float) -> float:
        """:return ppm-value corresponding to point (float)
        """
        pointOffset = point - self.referencePoint
        ppmPerPoint = self._valuePerPoint / self.spectrometerFrequency
        factor = -1.0 # (axis runs backward) if self.isReversed else 1.0
        value = self.referenceValue + factor * pointOffset *  ppmPerPoint
        return value

    pointToPpm = pointToValue

    def valueToPoint(self, value: float) -> float:
        """:return point (float) corresponding to ppm-value"""
        ppmPerPoint = self._valuePerPoint / self.spectrometerFrequency
        valOffset = value - self.referenceValue
        factor = -1.0 # (axis runs backward) if self.isReversed else 1.0
        point =  self.referencePoint + factor * valOffset / ppmPerPoint
        return point

    ppmToPoint = valueToPoint

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Spectrum) -> list:
        """get wrappedData (Nmr.SampledDataDims) for all DataDim children of parent Spectrum"""

        return [x for x in parent._wrappedData.sortedDataDims() if x.className == 'SampledDataDim']


# No 'new' function - PseudoDimensions are made on spectrum load

#=========================================================================================
# Connections to parents:
#=========================================================================================

# Notifiers:
def _expDimRefHasChanged(project: Project, apiExpDimRef: ApiExpDimRef):
    """Refresh PseudoDimension when ExpDimRef has changed"""
    for dataDim in apiExpDimRef.expDim.dataDims:
        if isinstance(dataDim, ApiSampledDataDim):
            project._modifiedApiObject(dataDim)


Project._setupApiNotifier(_expDimRefHasChanged, ApiExpDimRef, '')
del _expDimRefHasChanged
