"""
Module documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-03-16 17:29:23 +0000 (Mon, March 16, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.IntegralList import IntegralList
from ccpn.core.Peak import Peak
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import Integral as ApiIntegral
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import PeakDim as ApiPeakDim
from typing import Optional, Tuple, Sequence, List
import numpy as np
from scipy.integrate import trapz
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, ccpNmrV3CoreSetter
from ccpn.util.Logging import getLogger


LinkedPeaks = 'linkedPeaks'


class Integral(AbstractWrapperObject):
    """n-dimensional Integral, with integration region and value.

    Includes fields for per-dimension values.
    """

    #: Short class name, for PID.
    shortClassName = 'IT'
    # Attribute it necessary as subclasses must use superclass className
    className = 'Integral'

    _parentClass = IntegralList

    #: Name of plural link to instances of class
    _pluralLinkName = 'integrals'

    # the attribute name used by current
    _currentAttributeName = 'integrals'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class - NB shared with Peak class
    _apiClassQualifiedName = ApiIntegral._metaclass.qualifiedName()

    # _baseline = None
    _linkedPeakNotifier = None
    _linkedPeaks = set()

    # CCPN properties
    @property
    def _apiIntegral(self) -> ApiIntegral:
        """ API integrals matching Integral"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """id string - serial number converted to string"""
        return str(self._wrappedData.serial)

    @property
    def serial(self) -> int:
        """serial number of Integral, used in Pid and to identify the Integral. """
        return self._wrappedData.serial

    @property
    def _parent(self) -> IntegralList:
        """IntegralList containing Integral."""
        return self._project._data2Obj[self._wrappedData.integralList]

    integralList = _parent

    @property
    def value(self) -> Optional[float]:
        """value of Integral"""
        return self._wrappedData.volume

    @value.setter
    def value(self, value: float):
        self._wrappedData.volume = value

    @property
    def valueError(self) -> Optional[float]:
        """value error of Integral"""
        return self._wrappedData.volumeError

    @valueError.setter
    def valueError(self, value: float):
        self._wrappedData.volumeError = value

    @property
    def bias(self) -> float:
        """Baseplane offset used in calculating integral value"""
        return self._wrappedData.offset

    @bias.setter
    def bias(self, value: float):
        self._wrappedData.offset = value

    @property
    def figureOfMerit(self) -> Optional[float]:
        """figureOfMerit of Integral, between 0.0 and 1.0 inclusive."""
        return self._wrappedData.figOfMerit

    @figureOfMerit.setter
    def figureOfMerit(self, value: float):
        self._wrappedData.figOfMerit = value

    @property
    def offset(self) -> Optional[float]:
        """offset of Integral"""
        return self._wrappedData.offset

    @offset.setter
    def offset(self, value: float):
        self._wrappedData.offset = value

    # NOTE:ED - check, baseline is currently using offset in the model
    @property
    def baseline(self) -> Optional[float]:
        """baseline of Integral"""
        return self._wrappedData.offset

    @baseline.setter
    def baseline(self, value: float):
        self._wrappedData.offset = value

    @property
    def constraintWeight(self) -> Optional[float]:
        """constraintWeight of Integral"""
        return self._wrappedData.constraintWeight

    @constraintWeight.setter
    def constraintWeight(self, value: float):
        self._wrappedData.constraintWeight = value

    @property
    def slopes(self) -> List[float]:
        """slope (in dimension order) used in calculating integral value

        The slope is defined as the intensity in point i+1 minus the intensity in point i"""
        # return [x.slope for x in self._wrappedData.sortedPeakDims()]
        return self._wrappedData.slopes

    @slopes.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def slopes(self, value):
        self._wrappedData.slopes = value
        # peakDims = self._wrappedData.sortedPeakDims()
        # if len(value) == len(peakDims):
        #   for tt in zip(peakDims, value):
        #     tt[0].slope = tt[1]
        # else:
        #   raise ValueError("The slopes value %s does not match the dimensionality of the spectrum, %s"
        #                    % value, len(peakDims))

    @property
    def annotation(self) -> Optional[str]:
        """Integral text annotation"""
        return self._wrappedData.annotation

    @annotation.setter
    def annotation(self, value: str):
        self._wrappedData.annotation = value

    # @property
    # def comment(self) -> Optional[str]:
    #     """Free-form text comment"""
    #     return self._wrappedData.details
    #
    # @comment.setter
    # def comment(self, value: str):
    #     self._wrappedData.details = value

    @property
    def axisCodes(self) -> Tuple[str, ...]:
        """Spectrum axis codes in dimension order matching position."""
        return self.integralList.spectrum.axisCodes

    @property
    def limits(self) -> List[Tuple[float, float]]:
        return self._wrappedData.limits
        # """Integration limits in axis value (ppm), per dimension, with lowest value first
        #
        # For Fid or sampled dimensions the individual limit values will be points"""
        # result = []
        # dataDimRefs = self.integralList.spectrum._mainDataDimRefs()
        # for ii,peakDim in enumerate(self._wrappedData.sortedPeakDims()):
        #   dataDimRef = dataDimRefs[ii]
        #   if dataDimRef is None:
        #     value = (peakDim.position or 0)
        #     halfWidth = 0.5 * (peakDim.boxWidth or 0)
        #   else:
        #     value = (peakDim.value or 0)
        #     halfWidth = abs(0.5 * (peakDim.boxWidth or 0) * dataDimRef.valuePerPoint)
        #   result.append((value - halfWidth, value + halfWidth))
        # #
        # return result

    @limits.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def limits(self, value):
        self._wrappedData.limits = value
        # dataDimRefs = self.integralList.spectrum._mainDataDimRefs()
        # for ii,peakDim in enumerate(self._wrappedData.sortedPeakDims()):
        #   dataDimRef = dataDimRefs[ii]
        #   limit1, limit2 = value[ii]
        #   if None in value[ii]:
        #     peakDim.position = None
        #     peakDim.boxWidth = None
        #   elif dataDimRef is None:
        #     peakDim.position = 0.5 * (limit1 + limit2)
        #     peakDim.boxWidth = abs(limit1 - limit2)
        #   else:
        #     peakDim.value = 0.5 * (limit1 + limit2)
        #     peakDim.boxWidth = abs((limit1 - limit2)/ dataDimRef.valuePerPoint)
        #

        # automatically calculates Volume given the limits for 1Ds
        spectrum = self.integralList.spectrum

        if spectrum.dimensionCount == 1:
            for ii in range(spectrum.dimensionCount):
                limits = value[ii] if value and len(value) > ii else ()
                if len(limits) == 2:

                    if spectrum.intensities is not None and spectrum.intensities.size != 0:
                        limit1, limit2 = limits
                        x = spectrum.positions
                        index01 = np.where((x <= limit2) & (x >= limit1))
                        values = spectrum.intensities[index01]
                        self.value = float(trapz(values))

                        # small change, only calculate if there is a peak
                        if self.peak:
                            self.peak.volume = self.value

    @property
    def pointLimits(self) -> List[Tuple[float, float]]:
        return self._wrappedData.pointLimits
        # """Integration limits in points, per dimension, with lowest value first"""
        # result = []
        # for peakDim in self._wrappedData.sortedPeakDims():
        #   position = peakDim.position
        #   halfWidth = 0.5 * (peakDim.boxWidth or 0)
        #   result.append(position - halfWidth, position + halfWidth)
        # #
        # return result

    @pointLimits.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def pointLimits(self, value):
        self._wrappedData.pointLimits = value
        # peakDims = self._wrappedData.sortedPeakDims()
        # if len(value) == len(peakDims):
        #   for ii, peakDim in enumerate(peakDims):
        #     if None in value[ii]:
        #       peakDim.position = None
        #       peakDim.boxWidth = None
        #     else:
        #       limit1, limit2 = value[ii]
        #       peakDim.position = 0.5 * (limit1 + limit2)
        #       peakDim.boxWidth = abs(limit1 - limit2)
        # else:
        #   raise ValueError("The slopes value %s does not match the dimensionality of the spectrum, %s"
        #                    % value, len(peakDims))

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: IntegralList) -> Tuple[ApiIntegral, ...]:
        """get wrappedData (Integrals) for all Integral children of parent IntegralList"""
        return parent._wrappedData.sortedIntegrals()

    @property
    def _1Dregions(self):
        """
        :return:baseline of the integral, x regions and y regions in  separate arrays
        """
        # baseline = self.baseline

        # NOTE:ED - now using offset in the model, slope will determine the angle of the baseline
        #           calculate slope automatically?
        baseline = self.baseline

        for i in self.limits:
            x = self.integralList.spectrum.positions
            y = self.integralList.spectrum.intensities
            xRegions = np.where((x <= max(i)) & (x >= min(i)))
            for xRegion in xRegions:
                if baseline is not None:
                    # try:
                    # baseline = min(y[xRegion])
                    return (baseline, x[xRegion], y[xRegion])
                    # except Exception as es:
                    #     # TODO:Luca check empty list error
                    #     pass
                # should be just one for 1D
        return []

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    @property
    def peak(self):
        """The peak attached to the integral.
        """
        return self._project._data2Obj[self._wrappedData.peak] if self._wrappedData.peak else None

    @peak.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def peak(self, peak: Peak = None):
        """link a peak to the integral
        The peak must belong to the spectrum containing the integralList.
        :param peak: single peak
        """
        spectrum = self._parent.spectrum
        peak = self.project.getByPid(peak) if isinstance(peak, str) else peak

        if peak:
            if not isinstance(peak, Peak):
                raise TypeError('%s is not of type Peak' % peak)
            if peak not in spectrum.peaks:
                raise ValueError('%s does not belong to spectrum: %s' % (peak.pid, spectrum.pid))

        self._wrappedData.peak = peak._wrappedData if peak else None

    #===========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================


#=========================================================================================
# Connections to parents:
#=========================================================================================

@newObject(Integral)
def _newIntegral(self: IntegralList,
                 value: List[float] = None, valueError: List[float] = None, bias: float = 0,
                 offset: float = None, constraintWeight: float = None,
                 figureOfMerit: float = 1.0, annotation: str = None, comment: str = None,
                 limits: Sequence[Tuple[float, float]] = (), slopes: List[float] = None,
                 pointLimits: Sequence[Tuple[float, float]] = (), serial: int = None) -> Integral:
    """Create new Integral within IntegralList

    See the Integral class for details.

    :param value:
    :param valueError:
    :param bias:
    :param offset:
    :param constraintWeight:
    :param figureOfMerit:
    :param annotation:
    :param comment:
    :param limits:
    :param slopes:
    :param pointLimits:
    :return a new Integral instance.
    """

    dd = {'volume': value, 'volumeError': valueError, 'offset': offset, 'slopes': slopes,
          'figOfMerit': figureOfMerit, 'constraintWeight': constraintWeight,
          'annotation': annotation, 'details': comment,
          'limits': limits, 'pointLimits': pointLimits}

    if not constraintWeight: del dd['constraintWeight']
    if not offset: del dd['offset']

    apiParent = self._apiIntegralList
    apiIntegral = apiParent.newIntegral(**dd)
    result = self._project._data2Obj.get(apiIntegral)
    if result is None:
        raise RuntimeError('Unable to generate new Integral item')

    if serial is not None:
        try:
            result.resetSerial(serial)
        except ValueError:
            getLogger().warning("Could not reset serial of %s to %s - keeping original value"
                                % (result, serial))

    result.limits = limits  #needs to fire the first time for automatic calculation of the value

    return result


# Integral._parentClass.newIntegral = _newIntegral
# del _newIntegral

# def _factoryFunction(project:Project, wrappedData:ApiIntegral) -> AbstractWrapperObject:
#   """create Peak or Integral from API Peak"""
#   if wrappedData.peakList.dataType == 'Peak':
#     return Peak(project, wrappedData)
#   elif wrappedData.peakList.dataType == 'Integral':
#     return Integral(project, wrappedData)
#   else:
#     raise ValueError("API Peak object has illegal parent dataType: %s. Must be 'Peak' or 'Integral"
#                      % wrappedData.dataType)
#
#
# Integral._factoryFunction = staticmethod(_factoryFunction)
# Peak._factoryFunction = staticmethod(_factoryFunction)

# Additional Notifiers:
# NB API level notifiers are defined in the Peak file for API Peaks
# They will have the same effect for integrals

Project._apiNotifiers.append(
        ('_notifyRelatedApiObject', {'pathToObject': 'peak.integral', 'action': 'change'},
         ApiPeakDim._metaclass.qualifiedName(), '')
        )
