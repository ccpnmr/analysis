"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:29 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.Peak import Peak
from ccpn.core.MultipletList import MultipletList
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import Multiplet as apiMultiplet
from typing import Optional, Tuple, Any, Union, Sequence, List
from ccpn.util.Common import makeIterableList
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, ccpNmrV3CoreSetter, undoBlock
from ccpn.util.Logging import getLogger


MULTIPLET_TYPES = ['singlet', 'doublet', 'triplet', 'quartet', 'quintet', 'sextet', 'septet', 'octet', 'nonet',
                   'doublet of doublets', 'doublet of triplets', 'triplet of doublets', 'doublet of doublet of doublets']


def _calculateCenterOfMass(multiplet):
    """

    :param multiplet: multiplet obj containing peaks.
    :return: the center of mass of the multiplet that can be used as peak position
             if you consider the multiplet as a single peak
    """

    if len(multiplet.peaks) > 0:
        position = ()
        dim = multiplet.multipletList.spectrum.dimensionCount
        if dim > 1:
            for d in range(dim):
                peakPositions = [peak.position[d] for peak in multiplet.peaks]
                # peakIntensities = [peak.height or 1 for peak in multiplet.peaks]
                # numerator = []
                # for p, i in zip(peakPositions, peakIntensities):
                #     numerator.append(p * i)
                # centerOfMass = sum(numerator) / sum(peakIntensities)
                # position += (centerOfMass,)

                position += (sum(peakPositions) / len(multiplet.peaks),)
        else:
            position = (sum([peak.position[0] for peak in multiplet.peaks]) / len(multiplet.peaks),
                        sum([peak.height for peak in multiplet.peaks]) / len(multiplet.peaks))
        return position


def _getMultipletHeight(multiplet):
    'return the highest peak intensity across the multiplet peaks'
    if len(multiplet.peaks) > 0:
        return max([peak.height or 1 for peak in multiplet.peaks])


class Multiplet(AbstractWrapperObject):
    """Multiplet object, holding position, intensity, and assignment information

    Measurements that require more than one NmrAtom for an individual assignment
    (such as  splittings, J-couplings, MQ dimensions, reduced-dimensionality
    experiments etc.) are not supported (yet). Assignments can be viewed and set
    either as a list of assignments for each dimension (dimensionNmrAtoms) or as a
    list of all possible assignment combinations (assignedNmrAtoms)"""

    #: Short class name, for PID.
    shortClassName = 'MT'
    # Attribute it necessary as subclasses must use superclass className
    className = 'Multiplet'

    _parentClass = MultipletList

    #: Name of plural link to instances of class
    _pluralLinkName = 'multiplets'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = apiMultiplet._metaclass.qualifiedName()

    # the attribute name used by current
    _currentAttributeName = 'multiplets'

    # CCPN properties
    @property
    def _apiMultiplet(self) -> apiMultiplet:
        """API multiplets matching Multiplet."""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """id string - serial number converted to string."""
        return str(self._wrappedData.serial)

    @property
    def serial(self) -> int:
        """serial number of Multiplet, used in Pid and to identify the Multiplet."""
        return self._wrappedData.serial

    @property
    def _parent(self) -> Optional[MultipletList]:
        """parent containing multiplet."""
        return self._project._data2Obj[self._wrappedData.multipletList]

    multipletList = _parent

    @property
    def height(self) -> Optional[float]:
        """height of Multiplet."""
        height = _getMultipletHeight(self)
        return height

    @height.setter
    def height(self, value: float):
        self._wrappedData.height = value

    @property
    def heightError(self) -> Optional[float]:
        """height error of Multiplet."""
        return self._wrappedData.heightError

    @heightError.setter
    def heightError(self, value: float):
        self._wrappedData.heightError = value

    @property
    def volume(self) -> Optional[float]:
        """volume of Multiplet."""
        return self._wrappedData.volume

    @volume.setter
    def volume(self, value: float):
        self._wrappedData.volume = value

    @property
    def offset(self) -> Optional[float]:
        """offset of Multiplet."""
        return self._wrappedData.offset

    @offset.setter
    def offset(self, value: float):
        self._wrappedData.offset = value

    @property
    def constraintWeight(self) -> Optional[float]:
        """constraintWeight of Multiplet."""
        return self._wrappedData.constraintWeight

    @constraintWeight.setter
    def constraintWeight(self, value: float):
        self._wrappedData.constraintWeight = value

    @property
    def volumeError(self) -> Optional[float]:
        """volume error of Multiplet."""
        return self._wrappedData.volumeError

    @volumeError.setter
    def volumeError(self, value: float):
        self._wrappedData.volumeError = value

    @property
    def figureOfMerit(self) -> Optional[float]:
        """figureOfMerit of Multiplet, between 0.0 and 1.0 inclusive."""
        return self._wrappedData.figOfMerit

    @figureOfMerit.setter
    def figureOfMerit(self, value: float):
        self._wrappedData.figOfMerit = value

    @property
    def annotation(self) -> Optional[str]:
        """Multiplet text annotation."""
        return self._wrappedData.annotation

    @annotation.setter
    def annotation(self, value: str):
        self._wrappedData.annotation = value

    # @property
    # def comment(self) -> Optional[str]:
    #     """Free-form text comment."""
    #     return self._wrappedData.details
    #
    # @comment.setter
    # def comment(self, value: str):
    #     self._wrappedData.details = value

    @property
    def slopes(self) -> List[float]:
        """slope (in dimension order) used in calculating integral value."""
        return self._wrappedData.slopes

    @slopes.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def slopes(self, value):
        self._wrappedData.slopes = value

    @property
    def limits(self) -> List[Tuple[float, float]]:
        """limits (in dimension order) of the multiplet."""
        return self._wrappedData.limits

    @limits.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def limits(self, value):
        self._wrappedData.limits = value

    @property
    def pointLimits(self) -> List[Tuple[float, float]]:
        """pointLimits (in dimension order) of the multiplet."""
        return self._wrappedData.pointLimits

    @pointLimits.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def pointLimits(self, value):
        self._wrappedData.pointLimits = value

    @property
    def axisCodes(self) -> Tuple[str, ...]:
        """Spectrum axis codes in dimension order matching position."""
        return self.multipletList.spectrum.axisCodes

    @property
    def peaks(self) -> Optional[Tuple[Any]]:
        """List of peaks attached to the multiplet."""
        return tuple([self._project._data2Obj[pk] for pk in self._wrappedData.sortedPeaks()
                      if pk in self._project._data2Obj])

    @peaks.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def peaks(self, ll: list):
        if ll:
            pll = makeIterableList(ll)
            pks = [self.project.getByPid(peak) if isinstance(peak, str) else peak for peak in pll]
            for pp in pks:
                if not isinstance(pp, Peak):
                    raise TypeError('%s is not of type Peak' % pp)

            toRemove = [pk for pk in self.peaks if pk not in pks]
            toAdd = [pk for pk in pks if pk not in self.peaks]
            self.removePeaks(toRemove)
            self.addPeaks(toAdd)

    @property
    def numPeaks(self) -> int:
        """return number of peaks in the multiplet."""
        return len(self._wrappedData.sortedPeaks())

    @property
    def position(self) -> Optional[Tuple[float, ...]]:
        """Peak position in ppm (or other relevant unit) in dimension order calculated as Center Of Mass."""
        result = None
        try:
            pks = self.peaks
            # pksPos = [pp.position for pp in pks]
            if pks:
                # self._position = tuple(sum(item) for item in zip(*pksPos))
                self._position = _calculateCenterOfMass(self)
                result = self._position

        finally:
            return result

    ppmPositions = position

    # @property
    # def ppmPositions(self) -> Optional[Tuple[float, ...]]:
    #     """Peak position in ppm (or other relevant unit) in dimension order calculated as Center Of Mass."""
    #     result = None
    #     try:
    #         pks = self.peaks
    #         # pksPos = [pp.position for pp in pks]
    #         if pks:
    #             # self._position = tuple(sum(item) for item in zip(*pksPos))
    #             self._position = _calculateCenterOfMass(self)
    #             result = self._position
    #
    #     finally:
    #         return result

    @property
    def positionError(self) -> Tuple[Optional[float], ...]:
        """Peak position error in ppm (or other relevant unit)."""
        # TODO:LUCA calulate this :)
        return tuple()  # tuple(x.valueError for x in self._wrappedData.sortedPeaks())

    @property
    def boxWidths(self) -> Tuple[Optional[float], ...]:
        """The full width of the peak footprint in points for each dimension,
        i.e. the width of the area that should be considered for integration, fitting, etc. ."""
        return tuple(x.boxWidth for x in self._wrappedData.sortedPeaks())

    @property
    def lineWidths(self) -> Tuple[Optional[float], ...]:
        """Full-width-half-height of peak/multiplet for each dimension. """
        result = tuple()
        pks = self.peaks
        pksWidths = [pp.lineWidths for pp in pks]
        try:
            result = tuple(sum(item) for item in zip(*pksWidths))
        except Exception as es:
            if pks:
                result = list(pksWidths[0])
                for otherPks in pksWidths[1:]:
                    for ii in range(len(result)):
                        result[ii] += otherPks[ii]
            else:
                result = self._wrappedData.lineWidths
        finally:
            return result

    @lineWidths.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def lineWidths(self, value):
        self._wrappedData.lineWidths = value

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    # from ccpnmodel.ccpncore.api.memops import Implementation as ApiImplementation
    #
    # def __init__(self, project: 'Project', wrappedData: ApiImplementation.DataObject):
    #     super().__init__(project, wrappedData)
    #
    #     # attach a notifier to the peaks
    #     from ccpn.core.lib.Notifiers import Notifier
    #
    #     for pp in self.peaks:
    #         Notifier(pp, ['observe'], Notifier.ANY,
    #                  callback=self._propagateAction,
    #                  onceOnly=True, debug=True)

    @classmethod
    def _getAllWrappedData(cls, parent: MultipletList) -> Tuple[apiMultiplet, ...]:
        """get wrappedData (Multiplets) for all Multiplet children of parent MultipletList"""
        return parent._wrappedData.sortedMultiplets()

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    @logCommand(get='self')
    def addPeaks(self, peaks: Sequence[Union['Peak', str]]):
        """
        Add a peak or list of peaks to the Multiplet.
        The peaks must belong to the spectrum containing the multipletList.

        :param peaks: single peak or list of peaks as objects or pids.
        """
        spectrum = self._parent.spectrum
        peakList = makeIterableList(peaks)
        pks = []
        for peak in peakList:
            pks.append(self.project.getByPid(peak) if isinstance(peak, str) else peak)

        for pp in pks:
            if not isinstance(pp, Peak):
                raise TypeError('%s is not of type Peak' % pp)
            if pp not in spectrum.peaks:
                raise ValueError('%s does not belong to spectrum: %s' % (pp.pid, spectrum.pid))

        with undoBlock():
            for pk in pks:
                self._wrappedData.addPeak(pk._wrappedData)

    @logCommand(get='self')
    def removePeaks(self, peaks: Sequence[Union['Peak', str]]):
        """
        Remove a peak or list of peaks from the Multiplet.
        The peaks must belong to the multiplet.

        :param peaks: single peak or list of peaks as objects or pids
        """
        spectrum = self._parent.spectrum
        peakList = makeIterableList(peaks)
        pks = []
        for peak in peakList:
            pks.append(self.project.getByPid(peak) if isinstance(peak, str) else peak)

        for pp in pks:
            if not isinstance(pp, Peak):
                raise TypeError('%s is not of type Peak' % pp)
            if pp not in self.peaks:
                raise ValueError('%s does not belong to multiplet: %s' % (pp.pid, self.pid))
            if pp not in spectrum.peaks:
                raise ValueError('%s does not belong to spectrum: %s' % (pp.pid, spectrum.pid))

        with undoBlock():
            for pk in pks:
                self._wrappedData.removePeak(pk._wrappedData)

    def _propagateAction(self, data):
        from ccpn.core.lib.Notifiers import Notifier

        trigger = data[Notifier.TRIGGER]

        trigger = 'change' if trigger == 'observe' else trigger
        if trigger in ['change']:
            self._finaliseAction(trigger)

    #===========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================


#=========================================================================================
# Connections to parents
#=========================================================================================

@newObject(Multiplet)
def _newMultiplet(self: MultipletList,
                  height: float = 0.0, heightError: float = 0.0,
                  volume: float = 0.0, volumeError: float = 0.0,
                  offset: float = 0.0, constraintWeight: float = 0.0,
                  figureOfMerit: float = 1.0, annotation: str = None, comment: str = None,
                  limits: Sequence[Tuple[float, float]] = (), slopes: List[float] = (),
                  pointLimits: Sequence[Tuple[float, float]] = (), serial: int = None,
                  peaks: Sequence[Union['Peak', str]] = ()) -> Multiplet:
    """Create a new Multiplet within a multipletList

    See the Multiplet class for details.

    :param height:
    :param heightError:
    :param volume:
    :param volumeError:
    :param offset:
    :param constraintWeight:
    :param figureOfMerit:
    :param annotation:
    :param comment:
    :param position:
    :param positionError:
    :param limits:
    :param slopes:
    :param pointLimits:
    :param peaks:
    :return: a new Multiplet instance.
    """

    spectrum = self.spectrum
    peakList = makeIterableList(peaks)
    pks = []
    for peak in peakList:
        pks.append(self.project.getByPid(peak) if isinstance(peak, str) else peak)

    for pp in pks:
        if not isinstance(pp, Peak):
            raise TypeError('%s is not of type Peak' % pp)
        if pp not in spectrum.peaks:
            raise ValueError('%s does not belong to spectrum: %s' % (pp.pid, spectrum.pid))

    dd = {'height': height, 'heightError': heightError,
          'volume': volume, 'volumeError': volumeError, 'offset': offset, 'slopes': slopes,
          'figOfMerit': figureOfMerit, 'constraintWeight': constraintWeight,
          'annotation': annotation, 'details': comment,
          'limits': limits, 'pointLimits': pointLimits}
    if pks:
        dd['peaks'] = [pk._wrappedData for pk in pks]

    # remove items that can't be set to None in the model
    if not offset:
        del dd['offset']
    if not constraintWeight:
        del dd['constraintWeight']

    apiParent = self._apiMultipletList
    apiMultiplet = apiParent.newMultiplet(multipletType='multiplet', **dd)
    result = self._project._data2Obj.get(apiMultiplet)
    if result is None:
        raise RuntimeError('Unable to generate new Multiplet item')

    if serial is not None:
        try:
            result.resetSerial(serial)
        except ValueError:
            getLogger().warning("Could not reset serial of %s to %s - keeping original value"
                                % (result, serial))

    return result

# EJB 20181127: removed
# Multiplet._parentClass.newMultiplet = _newMultiplet
# del _newMultiplet

# EJB 20181128: removed, to be added to multiplet __init__?
# Notify Multiplets when the contents of peaks have changed
# i.e PeakDim references
Project._apiNotifiers.append(
        ('_notifyRelatedApiObject', {'pathToObject': 'peak.multiplets', 'action': 'change'},
         Nmr.PeakDim._metaclass.qualifiedName(), '')
        )
