"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:29 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import itertools
import collections
import operator

from ccpn.util import Undo
from ccpn.util import Common as commonUtil
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.SpectrumReference import SpectrumReference
from ccpn.core.Peak import Peak
# from ccpn.core.Spectrum import Spectrum
from ccpn.core.MultipletList import MultipletList
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
#from ccpnmodel.ccpncore.lib import Util as modelUtil
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import Multiplet as apiMultiplet
# from ccpn.core.MultipletList import MultipletList
from typing import Optional, Tuple, Any, Union, Sequence, List
from ccpn.util.Common import makeIterableList


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
        for d in range(dim):
            peakPositions = [peak.position[d] for peak in multiplet.peaks]
            peakIntensities = [peak.height or 1 for peak in multiplet.peaks]
            numerator = []
            for p, i in zip(peakPositions, peakIntensities):
                numerator.append(p * i)
            centerOfMass = sum(numerator) / sum(peakIntensities)
            position += (centerOfMass,)
        return position


def _getMultipletHeight(multiplet):
    'return the heighest peak intensity across the multiplet peaks'
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

    # CCPN properties
    @property
    def _apiMultiplet(self) -> apiMultiplet:
        """ API multiplets matching Multiplet"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """id string - serial number converted to string"""
        return str(self._wrappedData.serial)

    @property
    def serial(self) -> int:
        """serial number of Multiplet, used in Pid and to identify the Multiplet. """
        return self._wrappedData.serial

    @property
    def _parent(self) -> Optional[MultipletList]:
        """parent containing multiplet."""
        return self._project._data2Obj[self._wrappedData.multipletList]

    multipletList = _parent

    @property
    def height(self) -> Optional[float]:
        """height of Multiplet"""
        height = _getMultipletHeight(self)
        return height

    @height.setter
    def height(self, value: float):
        self._wrappedData.height = value

    @property
    def heightError(self) -> Optional[float]:
        """height error of Multiplet"""
        return self._wrappedData.heightError

    @heightError.setter
    def heightError(self, value: float):
        self._wrappedData.heightError = value

    @property
    def volume(self) -> Optional[float]:
        """volume of Multiplet"""
        return self._wrappedData.volume

    @volume.setter
    def volume(self, value: float):
        self._wrappedData.volume = value

    @property
    def offset(self) -> Optional[float]:
        """offset of Multiplet"""
        return self._wrappedData.offset

    @offset.setter
    def offset(self, value: float):
        self._wrappedData.offset = value

    @property
    def constraintWeight(self) -> Optional[float]:
        """constraintWeight of Multiplet"""
        return self._wrappedData.constraintWeight

    @constraintWeight.setter
    def constraintWeight(self, value: float):
        self._wrappedData.constraintWeight = value

    @property
    def volumeError(self) -> Optional[float]:
        """volume error of Multiplet"""
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
        """Multiplet text annotation"""
        return self._wrappedData.annotation

    @annotation.setter
    def annotation(self, value: str):
        self._wrappedData.annotation = value

    @property
    def comment(self) -> Optional[str]:
        """Free-form text comment"""
        return self._wrappedData.details

    @comment.setter
    def comment(self, value: str):
        self._wrappedData.details = value

    @property
    def slopes(self) -> List[float]:
        """slope (in dimension order) used in calculating integral value"""
        return self._wrappedData.slopes

    @slopes.setter
    def slopes(self, value):
        self._wrappedData.slopes = value

    @property
    def limits(self) -> List[Tuple[float, float]]:
        return self._wrappedData.limits

    @limits.setter
    def limits(self, value):
        self._wrappedData.limits = value

    @property
    def pointlimits(self) -> List[Tuple[float, float]]:
        return self._wrappedData.pointLimits

    @pointlimits.setter
    def pointlimits(self, value):
        self._wrappedData.pointLimits = value

    @property
    def axisCodes(self) -> Tuple[str, ...]:
        """Spectrum axis codes in dimension order matching position."""
        if self.peaks:
            return self.peaks[0].peakList.spectrum.axisCodes

    @property
    def peaks(self) -> Optional[Tuple[Any]]:
        """List of peaks attached to the multiplet"""
        try:
            return tuple([self._project._data2Obj[pk] for pk in self._wrappedData.sortedPeaks()])
        except:
            return None

    @peaks.setter
    def peaks(self, ll: list):

        if ll:
            toRemove = [pk for pk in self.peaks if pk not in ll]
            toAdd = [pk for pk in ll if pk not in self.peaks]
            self.removePeaks(toRemove)
            self.addPeaks(toAdd)

    @property
    def numPeaks(self) -> int:
        """return number of peaks in the multiplet"""
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
    def lineWidths(self, value):
        self._wrappedData.lineWidths = value

    # Implementation functions
    @classmethod
    def _getAllWrappedData(cls, parent: MultipletList) -> Tuple[apiMultiplet, ...]:
        """get wrappedData (Multiplets) for all Multiplet children of parent MultipletList"""
        return parent._wrappedData.sortedMultiplets()

    def addPeaks(self, peaks: ['Peak'] = None):
        """
        Add a peak or list of peaks to the Multiplet
        The peaks must belong to the spectrum containing the multipletList.

        :param peaks - single peak or list of peaks:
        """
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb
        # throw more understandable errors for the python console
        spectrum = self._parent.spectrum
        pks = makeIterableList(peaks)
        for pp in pks:
            if not isinstance(pp, Peak):
                raise TypeError('%s is not of type Peak' % pp)
            if pp not in spectrum.peaks:
                raise ValueError('%s does not belong to spectrum: %s' % (pp.pid, spectrum.pid))
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb

        defaults = collections.OrderedDict(
                (('peaks', None),
                 )
                )
        undo = self._project._undo
        self._startCommandEchoBlock('addPeaks', values=locals(), defaults=defaults,
                                    parName='addPeaks')
        try:
            for pk in pks:
                self._wrappedData.addPeak(pk._wrappedData)
        finally:
            self._endCommandEchoBlock()

    def removePeaks(self, peaks: ['Peak'] = None):
        """
        Remove a peak or list of peaks from the Multiplet
        The peaks must belong to the multiplet.

        :param peaks - single peak or list of peaks:
        """
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb
        # throw more understandable errors for the python console
        spectrum = self._parent.spectrum
        pks = makeIterableList(peaks)
        for pp in pks:
            if not isinstance(pp, Peak):
                raise TypeError('%s is not of type Peak' % pp)
            if pp not in self.peaks:
                raise ValueError('%s does not belong to multiplet: %s' % (pp.pid, self.pid))
            if pp not in spectrum.peaks:
                raise ValueError('%s does not belong to spectrum: %s' % (pp.pid, spectrum.pid))
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb

        defaults = collections.OrderedDict(
                (('peaks', None),
                 )
                )
        undo = self._project._undo
        self._startCommandEchoBlock('removePeaks', values=locals(), defaults=defaults,
                                    parName='removePeaks')
        try:
            for pk in pks:
                self._wrappedData.removePeak(pk._wrappedData)
        finally:
            self._endCommandEchoBlock()


# Connections to parents:
def _newMultiplet(self: MultipletList,
                  height: float = 0.0, heightError: float = 0.0,
                  volume: float = 0.0, volumeError: float = 0.0,
                  offset: float = 0.0, constraintWeight: float = 0.0,
                  figureOfMerit: float = 1.0, annotation: str = None, comment: str = None,
                  position: List[float] = (), positionError: List[float] = (),
                  limits: Sequence[Tuple[float, float]] = (), slopes: List[float] = (),
                  pointLimits: Sequence[Tuple[float, float]] = (),
                  peaks: ['Peak'] = ()) -> Multiplet:
    """Create new Multiplet within multipletList"""

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb
    # throw more understandable errors for the python console
    spectrum = self.spectrum
    pks = makeIterableList(peaks)
    for pp in pks:
        if not isinstance(pp, Peak):
            raise TypeError('%s is not of type Peak' % pp)
        if pp not in spectrum.peaks:
            raise ValueError('%s does not belong to spectrum: %s' % (pp.pid, spectrum.pid))
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb

    defaults = collections.OrderedDict((('annotation', None),
                                        ('height', 0.0), ('heightError', 0.0),
                                        ('volume', 0.0), ('volumeError', 0.0),
                                        ('offset', 0.0),
                                        ('figureOfMerit', 1.0),
                                        ('constraintWeight', 0.0),
                                        ('comment', None),
                                        ('position', ()), ('positionError', ()),
                                        ('limits', ()), ('slopes', ()), ('pointLimits', ()),
                                        ('peaks', [])))
    dd = {'height': height, 'heightError': heightError,
          'volume': volume, 'volumeError': volumeError, 'offset': offset, 'slopes': slopes,
          'figOfMerit': figureOfMerit, 'constraintWeight': constraintWeight,
          'annotation': annotation, 'details': comment,
          # 'position': position, 'positionError': positionError,   # these can't be set
          'limits': limits, 'pointLimits': pointLimits}
    if peaks:
        dd['peaks'] = [p._wrappedData for p in peaks]

    undo = self._project._undo
    self._startCommandEchoBlock('newMultiplet', values=locals(), defaults=defaults,
                                parName='newMultiplet')
    try:
        apiParent = self._apiMultipletList
        # if pks:
        #   apiMultiplet = apiParent.newMultiplet(multipletType='multiplet',
        #                                           peaks=[p._wrappedData for p in pks])
        # else:
        #   apiMultiplet = apiParent.newMultiplet(multipletType='multiplet')

        apiMultiplet = apiParent.newMultiplet(multipletType='multiplet', **dd)

        result = self._project._data2Obj.get(apiMultiplet)
    finally:
        self._endCommandEchoBlock()

    return result


Multiplet._parentClass.newMultiplet = _newMultiplet
del _newMultiplet

# Notify Multiplets when the contents of peaks have changed
# i.e PeakDim references
Project._apiNotifiers.append(
        ('_notifyRelatedApiObject', {'pathToObject': 'peak.multiplets', 'action': 'change'},
         Nmr.PeakDim._metaclass.qualifiedName(), '')
        )
