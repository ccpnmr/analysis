"""
Module documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Joanna Fox, Morgan Hayward, Victoria A Higman, Luca Mureddu",
               "Eliza Płoskoń, Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2024-01-15 18:52:09 +0000 (Mon, January 15, 2024) $"
__version__ = "$Revision: 3.2.2 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
from typing import Optional, Tuple, Sequence, List, Union
from scipy.integrate import trapz

from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import Integral as ApiIntegral
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import PeakDim as ApiPeakDim
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.IntegralList import IntegralList
from ccpn.core.Peak import Peak
from ccpn.core.lib.ContextManagers import newObject, ccpNmrV3CoreSetter
from ccpn.util.decorators import logCommand
from ccpn.util.Logging import getLogger
from ccpn.util.Constants import SCALETOLERANCE


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
    def spectrum(self):
        """Convenience property to get the spectrum, equivalent to integral.peakList.spectrum
        """
        return self.integralList.spectrum

    @property
    def value(self) -> Optional[float]:
        """value of Integral"""

        if self._wrappedData.volume is None:
            return None

        scale = self.integralList.spectrum.scale
        scale = scale if scale is not None else 1.0
        if -SCALETOLERANCE < scale < SCALETOLERANCE:
            getLogger().warning('Scaling {}.value by minimum tolerance (±{})'.format(self, SCALETOLERANCE))

        return self._wrappedData.volume * scale

    @value.setter
    @logCommand(get='self', isProperty=True)
    def value(self, value: Union[float, int, None]):
        if not isinstance(value, (float, int, type(None))):
            raise TypeError('value must be a float, integer or None')
        elif value is not None and (value - value) != 0.0:
            raise TypeError('value cannot be NaN or Infinity')

        if value is None:
            self._wrappedData.volume = None
        else:
            scale = self.integralList.spectrum.scale
            scale = scale if scale is not None else 1.0
            if -SCALETOLERANCE < scale < SCALETOLERANCE:
                getLogger().warning('Scaling {}.value by minimum tolerance (±{})'.format(self, SCALETOLERANCE))
                self._wrappedData.volume = None
            else:
                self._wrappedData.volume = float(value) / scale

    @property
    def valueError(self) -> Optional[float]:
        """value error of Integral"""
        if self._wrappedData.volumeError is None:
            return None

        scale = self.integralList.spectrum.scale
        scale = scale if scale is not None else 1.0
        if -SCALETOLERANCE < scale < SCALETOLERANCE:
            getLogger().warning('Scaling {}.valueError by minimum tolerance (±{})'.format(self, SCALETOLERANCE))

        return self._wrappedData.volumeError * scale

    @valueError.setter
    @logCommand(get='self', isProperty=True)
    def valueError(self, value: Union[float, int, None]):
        if not isinstance(value, (float, int, type(None))):
            raise TypeError('valueError must be a float, integer or None')
        elif value is not None and (value - value) != 0.0:
            raise TypeError('valueError cannot be NaN or Infinity')

        if value is None:
            self._wrappedData.volumeError = None
        else:
            scale = self.integralList.spectrum.scale
            scale = scale if scale is not None else 1.0
            if -SCALETOLERANCE < scale < SCALETOLERANCE:
                getLogger().warning('Scaling {}.valueError by minimum tolerance (±{})'.format(self, SCALETOLERANCE))
                self._wrappedData.volumeError = None
            else:
                self._wrappedData.volumeError = float(value) / scale

    @property
    def bias(self) -> float:
        """Baseplane offset used in calculating integral value"""
        scale = self.integralList.spectrum.scale
        scale = scale if scale is not None else 1.0
        if -SCALETOLERANCE < scale < SCALETOLERANCE:
            getLogger().warning('Scaling {}.bias by minimum tolerance (±{})'.format(self, SCALETOLERANCE))

        return self._wrappedData.offset * scale

    @bias.setter
    @logCommand(get='self', isProperty=True)
    def bias(self, value: Union[float, int]):
        if not isinstance(value, (float, int)):
            raise TypeError('bias must be a float or integer')
        elif (value - value) != 0.0:
            raise TypeError('bias cannot be NaN or Infinity')
        value = float(value)

        scale = self.integralList.spectrum.scale
        scale = scale if scale is not None else 1.0
        if -SCALETOLERANCE < scale < SCALETOLERANCE:
            getLogger().warning('Scaling {}.bias by minimum tolerance (±{})'.format(self, SCALETOLERANCE))
            self._wrappedData.offset = 0.0
        else:
            self._wrappedData.offset = value / scale

    @property
    def figureOfMerit(self) -> Optional[float]:
        """figureOfMerit of Integral, between 0.0 and 1.0 inclusive."""
        return self._wrappedData.figOfMerit

    @figureOfMerit.setter
    @logCommand(get='self', isProperty=True)
    def figureOfMerit(self, value: float):
        self._wrappedData.figOfMerit = value

    @property
    def offset(self) -> float:
        """offset of Integral"""
        scale = self.integralList.spectrum.scale
        scale = scale if scale is not None else 1.0
        if -SCALETOLERANCE < scale < SCALETOLERANCE:
            getLogger().warning('Scaling {}.offset by minimum tolerance (±{})'.format(self, SCALETOLERANCE))

        return self._wrappedData.offset * scale

    @offset.setter
    @logCommand(get='self', isProperty=True)
    def offset(self, value: Union[float, int]):
        if not isinstance(value, (float, int)):
            raise TypeError('offset must be a float or integer')
        elif (value - value) != 0.0:
            raise TypeError('offset cannot be NaN or Infinity')
        value = float(value)

        scale = self.integralList.spectrum.scale
        scale = scale if scale is not None else 1.0
        if -SCALETOLERANCE < scale < SCALETOLERANCE:
            getLogger().warning('Scaling {}.offset by minimum tolerance (±{})'.format(self, SCALETOLERANCE))
            self._wrappedData.offset = 0.0
        else:
            self._wrappedData.offset = value / scale

    # NOTE:ED - check, baseline is currently using offset in the model
    @property
    def baseline(self) -> float:
        """baseline of Integral"""
        baseline = self._wrappedData.offset
        if baseline is None or baseline == 0:
            baseline = self.spectrum.positiveContourBase or 0
        scale = self.integralList.spectrum.scale
        scale = scale if scale is not None else 1.0
        if -SCALETOLERANCE < scale < SCALETOLERANCE:
            getLogger().warning('Scaling {}.baseline by minimum tolerance (±{})'.format(self, SCALETOLERANCE))

        return baseline * scale

    @baseline.setter
    @logCommand(get='self', isProperty=True)
    def baseline(self, value: Union[float, int]):
        if not isinstance(value, (float, int)):
            raise TypeError('baseline must be a float or integer')
        elif (value - value) != 0.0:
            raise TypeError('baseline cannot be NaN or Infinity')
        value = float(value)

        scale = self.integralList.spectrum.scale
        scale = scale if scale is not None else 1.0
        if -SCALETOLERANCE < scale < SCALETOLERANCE:
            getLogger().warning('Scaling {}.baseline by minimum tolerance (±{})'.format(self, SCALETOLERANCE))
            self._wrappedData.offset = 0.0
        else:
            self._wrappedData.offset = value / scale

    @property
    def constraintWeight(self) -> Optional[float]:
        """constraintWeight of Integral"""
        return self._wrappedData.constraintWeight

    @constraintWeight.setter
    @logCommand(get='self', isProperty=True)
    def constraintWeight(self, value: float):
        self._wrappedData.constraintWeight = value

    @property
    def slopes(self) -> Optional[List[float]]:
        """slope (in dimension order) used in calculating integral value

        The slope is defined as the intensity in point i+1 minus the intensity in point i"""
        # return [x.slope for x in self._wrappedData.sortedPeakDims()]
        if self._wrappedData.slopes is None:
            return None

        scale = self.integralList.spectrum.scale
        scale = scale if scale is not None else 1.0
        if -SCALETOLERANCE < scale < SCALETOLERANCE:
            getLogger().warning('Scaling {}.slopes by minimum tolerance (±{})'.format(self, SCALETOLERANCE))

        return [slope * scale for slope in self._wrappedData.slopes]

    @slopes.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def slopes(self, value: Union[List[float], Tuple[float], None] = None):
        if not isinstance(value, (list, tuple, type(None))):
            raise TypeError('slopes must be a None or list/tuple of floats - {}'.format(value))
        if value and not all(isinstance(sl, float) for sl in value):
            raise TypeError('slopes must be a None or list/tuple of floats - {}'.format(value))

        if value is None:
            self._wrappedData.slopes = None
        else:
            scale = self.integralList.spectrum.scale
            scale = scale if scale is not None else 1.0
            if -SCALETOLERANCE < scale < SCALETOLERANCE:
                getLogger().warning('Scaling {}.slopes by minimum tolerance (±{})'.format(self, SCALETOLERANCE))
                self._wrappedData.slopes = None
            else:
                self._wrappedData.slopes = [sl / scale for sl in value]

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
    @logCommand(get='self', isProperty=True)
    def annotation(self, value: str):
        self._wrappedData.annotation = value

    @property
    def axisCodes(self) -> Tuple[str, ...]:
        """Spectrum axis codes in dimension order matching position."""
        return self.integralList.spectrum.axisCodes

    @property
    def limits(self) -> List[Tuple[float, float]]:
        """Integration limits in axis value (ppm), per dimension, with lowest
        ppm value first
        :return list of (low_ppm, high_ppm) tuples
        """
        return self._wrappedData.limits

    @limits.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def limits(self, value):
        self._wrappedData.limits = value

        # automatically calculates Volume given the limits for 1Ds
        spectrum = self.integralList.spectrum
        if spectrum.isEmptySpectrum():
            return

        if spectrum.dimensionCount == 1:
            for ii in range(spectrum.dimensionCount):
                limits = value[ii] if value and len(value) > ii else ()
                if len(limits) == 2:

                    if spectrum.intensities is not None and spectrum.intensities.size != 0:
                        limit1, limit2 = limits
                        x = spectrum.positions
                        index01 = np.where((x <= limit2) & (x >= limit1))
                        values = spectrum.intensities[index01]
                        if len(values) > 0 and all(values):
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

    @property
    def integralViews(self) -> list:
        """STUB: hot-fixed later"""
        return []

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: IntegralList) -> list[ApiIntegral]:
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
        spectrum = self.integralList.spectrum
        if spectrum.isEmptySpectrum():
            return []
        if spectrum.dimensionCount == 1:
            for i in self.limits:
                x = spectrum.positions
                y = spectrum.intensities
                xRegions = np.where((x <= max(i)) & (x >= min(i)))
                for xRegion in xRegions:
                    if baseline is not None:
                        return (baseline, x[xRegion], y[xRegion])
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
    # new<Object> and other methods
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
                 pointLimits: Sequence[Tuple[float, float]] = ()
                 ) -> Integral:
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

    dd = {'volume'    : value, 'volumeError': valueError, 'offset': offset, 'slopes': slopes,
          'figOfMerit': figureOfMerit, 'constraintWeight': constraintWeight,
          'annotation': annotation, 'details': comment,
          'limits'    : limits, 'pointLimits': pointLimits}

    if not constraintWeight: del dd['constraintWeight']
    if not offset: del dd['offset']

    apiParent = self._apiIntegralList
    apiIntegral = apiParent.newIntegral(**dd)
    result = self._project._data2Obj.get(apiIntegral)
    if result is None:
        raise RuntimeError('Unable to generate new Integral item')

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
