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
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:29 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
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
from ccpn.core.PeakList import PeakList
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
#from ccpnmodel.ccpncore.lib import Util as modelUtil
from ccpnmodel.ccpncore.lib._ccp.nmr.Nmr import Peak as LibPeak
from typing import Optional, Tuple, Union, Sequence, TypeVar, Any


class Peak(AbstractWrapperObject):
    """Peak object, holding position, intensity, and assignment information

    Measurements that require more than one NmrAtom for an individual assignment
    (such as  splittings, J-couplings, MQ dimensions, reduced-dimensionality
    experiments etc.) are not supported (yet). Assignments can be viewed and set
    either as a list of assignments for each dimension (dimensionNmrAtoms) or as a
    list of all possible assignment combinations (assignedNmrAtoms)"""

    #: Short class name, for PID.
    shortClassName = 'PK'
    # Attribute it necessary as subclasses must use superclass className
    className = 'Peak'

    _parentClass = PeakList

    #: Name of plural link to instances of class
    _pluralLinkName = 'peaks'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = Nmr.Peak._metaclass.qualifiedName()

    # _linkedPeak = None
    _linkedPeaksName = 'linkedPeaks'

    # CCPN properties
    @property
    def _apiPeak(self) -> Nmr.Peak:
        """ API peaks matching Peak"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """id string - serial number converted to string"""
        return str(self._wrappedData.serial)

    @property
    def serial(self) -> int:
        """serial number of Peak, used in Pid and to identify the Peak. """
        return self._wrappedData.serial

    @property
    def _parent(self) -> Optional[PeakList]:
        """PeakList containing Peak."""
        #TODO:ED trap that the Peak is no longer attached due to deletion
        try:
            return self._project._data2Obj[self._wrappedData.peakList]
        except:
            return None

    peakList = _parent

    @property
    def height(self) -> Optional[float]:
        """height of Peak"""
        return self._wrappedData.height

    @height.setter
    def height(self, value: float):
        self._wrappedData.height = value

    @property
    def heightError(self) -> Optional[float]:
        """height error of Peak"""
        return self._wrappedData.heightError

    @heightError.setter
    def heightError(self, value: float):
        self._wrappedData.heightError = value

    @property
    def volume(self) -> Optional[float]:
        """volume of Peak"""
        return self._wrappedData.volume

    @volume.setter
    def volume(self, value: float):
        self._wrappedData.volume = value

    @property
    def volumeError(self) -> Optional[float]:
        """volume error of Peak"""
        return self._wrappedData.volumeError

    @volumeError.setter
    def volumeError(self, value: float):
        self._wrappedData.volumeError = value

    @property
    def figureOfMerit(self) -> Optional[float]:
        """figureOfMerit of Peak, between 0.0 and 1.0 inclusive."""
        return self._wrappedData.figOfMerit

    @figureOfMerit.setter
    def figureOfMerit(self, value: float):
        self._wrappedData.figOfMerit = value

    @property
    def annotation(self) -> Optional[str]:
        """Peak text annotation"""
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
    def axisCodes(self) -> Tuple[str, ...]:
        """Spectrum axis codes in dimension order matching position."""
        return self.peakList.spectrum.axisCodes

    @property
    def position(self) -> Tuple[float, ...]:
        """Peak position in ppm (or other relevant unit) in dimension order."""
        return tuple(x.value for x in self._wrappedData.sortedPeakDims())

    @position.setter
    def position(self, value: Sequence):
        """set the position of the peak
        """

        def undo():
            """preredo/postundo function, needed for undo/redo"""
            # self.project.blankNotification()

            if not hasattr(self.project, '_apiBlanking'):
                self.project._apiBlanking = 0
            self.project._apiBlanking += 1

        def redo():
            """preundo/postredo function, needed for undo/redo, and fire single change notifier"""
            # self.project.unblankNotification()
            self.project._apiBlanking = max(0, self.project._apiBlanking-1)

            self._finaliseAction('change')
            for mt in self.multiplets:
                mt._finaliseAction('change')

        self._startCommandEchoBlock('position', value, propertySetter=True)
        _undo = self.project._undo

        _undo.newItem(redo, undo)
        undo()
        try:
            # call api changes
            for ii, peakDim in enumerate(self._wrappedData.sortedPeakDims()):
                peakDim.value = value[ii]
                peakDim.realValue = None
        finally:
            redo()
            _undo.newItem(undo, redo)

            self._endCommandEchoBlock()

    @property
    def positionError(self) -> Tuple[Optional[float], ...]:
        """Peak position error in ppm (or other relevant unit)."""
        return tuple(x.valueError for x in self._wrappedData.sortedPeakDims())

    @positionError.setter
    def positionError(self, value: Sequence):
        self._startCommandEchoBlock('positionError', value, propertySetter=True)
        try:
            for ii, peakDim in enumerate(self._wrappedData.sortedPeakDims()):
                peakDim.valueError = value[ii]
        finally:
            self._endCommandEchoBlock()

    @property
    def pointPosition(self) -> Tuple[float, ...]:
        """Peak position in points."""
        return tuple(x.position for x in self._wrappedData.sortedPeakDims())

    @pointPosition.setter
    def pointPosition(self, value: Sequence):
        self._startCommandEchoBlock('pointPosition', value, propertySetter=True)
        try:
            for ii, peakDim in enumerate(self._wrappedData.sortedPeakDims()):
                peakDim.position = value[ii]
        finally:
            self._endCommandEchoBlock()

    @property
    def boxWidths(self) -> Tuple[Optional[float], ...]:
        """The full width of the peak footprint in points for each dimension,
        i.e. the width of the area that should be considered for integration, fitting, etc. ."""
        return tuple(x.boxWidth for x in self._wrappedData.sortedPeakDims())

    @boxWidths.setter
    def boxWidths(self, value: Sequence):
        self._startCommandEchoBlock('boxWidths', value, propertySetter=True)
        try:
            for ii, peakDim in enumerate(self._wrappedData.sortedPeakDims()):
                peakDim.boxWidth = value[ii]
        finally:
            self._endCommandEchoBlock()

    @property
    def lineWidths(self) -> Tuple[Optional[float], ...]:
        """Full-width-half-height of peak/multiplet for each dimension, in Hz. """
        return tuple(x.lineWidth for x in self._wrappedData.sortedPeakDims())

    @lineWidths.setter
    def lineWidths(self, value: Sequence):
        self._startCommandEchoBlock('lineWidths', value, propertySetter=True)
        try:
            for ii, peakDim in enumerate(self._wrappedData.sortedPeakDims()):
                peakDim.lineWidth = value[ii]
        finally:
            self._endCommandEchoBlock()

    @property
    def dimensionNmrAtoms(self) -> Tuple[Tuple['NmrAtom', ...], ...]:
        """Peak dimension assignment - a tuple of tuples with the assigned NmrAtoms for each dimension.
        One of two alternative views on the Peak assignment.

        Example, for a 13C HSQC:
          ((<NA:A.127.LEU.HA>, <NA:A.127.LEU.HBX>, <NA:A.127.LEU.HBY>, <NA:A.127.LEU.HG>,

           (<NA:A.127.LEU.CA>, <NA:A.127.LEU.CB>)
           )

        Assignments as a list of individual combinations is given in 'assignedNmrAtoms'.
        Note that by setting dimensionAssignments you tel the program that all combinations are
        possible - in the example that all four protons could be bound to either of the carbons

        To (re)set the assignment for a single dimension, use the Peak.assignDimension method. """
        result = []
        for peakDim in self._wrappedData.sortedPeakDims():
            mainPeakDimContribs = peakDim.mainPeakDimContribs
            # Done this way as a quick way of sorting the values
            mainPeakDimContribs = [x for x in peakDim.sortedPeakDimContribs() if x in mainPeakDimContribs]

            data2Obj = self._project._data2Obj
            dimResults = [data2Obj[pdc.resonance] for pdc in mainPeakDimContribs
                          if hasattr(pdc, 'resonance')]
            result.append(tuple(sorted(dimResults)))
        #
        return tuple(result)

    @dimensionNmrAtoms.setter
    def dimensionNmrAtoms(self, value: Sequence):

        self._startCommandEchoBlock('dimensionNmrAtoms', value, propertySetter=True)
        try:
            isotopeCodes = self.peakList.spectrum.isotopeCodes

            apiPeak = self._wrappedData
            dimResonances = []
            for ii, atoms in enumerate(value):
                if atoms is None:
                    dimResonances.append(None)

                else:

                    isotopeCode = isotopeCodes[ii]

                    if isinstance(atoms, str):
                        raise ValueError("dimensionNmrAtoms cannot be set to a sequence of strings")
                    if not isinstance(atoms, Sequence):
                        raise ValueError("dimensionNmrAtoms must be set to a sequence of list/tuples")

                    atoms = tuple(self.getByPid(x) if isinstance(x, str) else x for x in atoms)
                    resonances = tuple(x._wrappedData for x in atoms if x is not None)
                    if isotopeCode and isotopeCode != '?':
                        # check for isotope match
                        if any(x.isotopeCode not in (isotopeCode, '?') for x in resonances):
                            raise ValueError("NmrAtom assigned to dimension %s must have isotope %s or '?'"
                                             % (ii + 1, isotopeCode))
                    dimResonances.append(resonances)

            apiPeak.assignByDimensions(dimResonances)
        finally:
            self._endCommandEchoBlock()

    @property
    def assignedNmrAtoms(self) -> Tuple[Tuple[Optional['NmrAtom'], ...], ...]:
        """Peak assignment - a tuple of tuples of NmrAtom combinations.
        (e.g. a tuple of triplets for a 3D spectrum).
        One of two alternative views on the Peak assignment.
        Missing assignments are entered as None.

        Example, for 13H HSQC::
          ((<NA:A.127.LEU.HA>, <NA:A.127.LEU.CA>),

          (<NA:A.127.LEU.HBX>, <NA:A.127.LEU.CB>),

          (<NA:A.127.LEU.HBY>, <NA:A.127.LEU.CB>),

          (<NA:A.127.LEU.HG>, None),)

        To add a single assignment tuple, use the Peak.addAssignment method

        See also dimensionNmrAtoms, which gives assignments per dimension.

        """
        data2Obj = self._project._data2Obj
        apiPeak = self._wrappedData
        peakDims = apiPeak.sortedPeakDims()
        mainPeakDimContribs = [sorted(x.mainPeakDimContribs, key=operator.attrgetter('serial'))
                               for x in peakDims]
        result = []
        for peakContrib in apiPeak.sortedPeakContribs():
            allAtoms = []
            peakDimContribs = peakContrib.peakDimContribs
            for ii, peakDim in enumerate(peakDims):
                nmrAtoms = [data2Obj.get(x.resonance) for x in mainPeakDimContribs[ii]
                            if x in peakDimContribs and hasattr(x, 'resonance')]
                if not nmrAtoms:
                    nmrAtoms = [None]
                allAtoms.append(nmrAtoms)

            # NB this gives a list of tuples
            # Remove all-None tuples
            result.extend(tt for tt in itertools.product(*allAtoms)
                          if any(x is not None for x in tt))
            # result += itertools.product(*allAtoms)
        #
        return tuple(sorted(result))

    @assignedNmrAtoms.setter
    def assignedNmrAtoms(self, value: Sequence):
        self._startCommandEchoBlock('assignedNmrAtoms', value, propertySetter=True)
        try:
            isotopeCodes = tuple(None if x == '?' else x for x in self.peakList.spectrum.isotopeCodes)

            apiPeak = self._wrappedData
            peakDims = apiPeak.sortedPeakDims()
            dimensionCount = len(peakDims)

            # get resonance, all tuples and per dimension
            resonances = []
            for tt in value:
                ll = dimensionCount * [None]
                resonances.append(ll)
                for ii, atom in enumerate(tt):
                    atom = self.getByPid(atom) if isinstance(atom, str) else atom
                    if atom is not None:
                        resonance = atom._wrappedData
                        if isotopeCodes[ii] and resonance.isotopeCode not in (isotopeCodes[ii], '?'):
                            raise ValueError("NmrAtom %s, isotope %s, assigned to dimension %s must have isotope %s or '?'"
                                             % (atom, resonance.isotopeCode, ii + 1, isotopeCodes[ii]))

                        ll[ii] = resonance

            # set assignments
            apiPeak.assignByContributions(resonances)
        finally:
            self._endCommandEchoBlock()

    # alternativeNames
    assignments = assignedNmrAtoms
    assignmentsByDimensions = dimensionNmrAtoms

    @property
    def multiplets(self) -> Optional[Tuple[Any]]:
        """List of multiplets that the peak belongs to
        """
        try:
            return tuple([self._project._data2Obj[mt] for mt in self._wrappedData.sortedMultiplets()])
        except:
            return None

    def _linkPeaks(self, peaks):
        """
        NB: this is needed for screening spectrumHits and peakHits. You might see peakCluster instead.
        Saves the peaks in _ccpnInternalData as pids
        """
        pids = [str(peak.pid) for peak in peaks if peak != self and isinstance(peak, Peak)]
        if isinstance(self._ccpnInternalData, dict):
            tempCcpn = self._ccpnInternalData.copy()
            tempCcpn[self._linkedPeaksName] = pids
            self._ccpnInternalData = tempCcpn
        else:
            raise ValueError("Peak.linkPeaks: CCPN internal must be a dictionary")

    @property
    def _linkedPeaks(self):
        """
        NB: this is needed for screening spectrumHits and peakHits. You might see peakCluster instead.
        It returns a list of peaks belonging to other peakLists or spectra which are required to be linked to this particular peak.
        This functionality is not implemented in the model. Saves the Peak pids in _ccpnInternalData.
        :return: a list of peaks
        """

        pids = self._ccpnInternalData.get(self._linkedPeaksName) or []
        peaks = [self.project.getByPid(pid) for pid in pids if pid is not None]
        return peaks

    def addAssignment(self, value: Sequence[Union[str, 'NmrAtom']]):
        """Add a peak assignment - a list of one NmrAtom or Pid for each dimension"""

        if len(value) != self.peakList.spectrum.dimensionCount:
            raise ValueError("Length of assignment value %s does not match peak dimensionality %s "
                             % (value, self.peakList.spectrum.dimensionCount))

        # Convert to tuple and check for non-existing pids
        ll = []
        for val in value:
            if isinstance(val, str):
                vv = self.getByPid(val)
                if vv is None:
                    raise ValueError("No NmrAtom matching string pid %s" % val)
                else:
                    ll.append(vv)
            else:
                ll.append(val)
        value = tuple(value)

        assignedNmrAtoms = list(self.assignedNmrAtoms)
        if value in assignedNmrAtoms:
            self._project._logger.warning("Attempt to add already existing Peak Assignment: %s - ignored"
                                          % value)
        else:
            assignedNmrAtoms.append(value)
            self.assignedNmrAtoms = assignedNmrAtoms

    def assignDimension(self, axisCode: str, value: Union[Union[str, 'NmrAtom'],
                                                          Sequence[Union[str, 'NmrAtom']]] = None):
        """Assign dimension with axisCode to value (NmrAtom, or Pid or sequence of either, or None)
        """

        axisCodes = self._parent._parent.axisCodes
        try:
            index = axisCodes.index(axisCode)
        except ValueError:
            raise ValueError("axisCode %s not recognised" % axisCode)

        if value is None:
            value = []
        elif isinstance(value, str):
            value = [self.getByPid(value)]
        elif isinstance(value, Sequence):
            value = [(self.getByPid(x) if isinstance(x, str) else x) for x in value]
        else:
            value = [value]
        dimensionNmrAtoms = list(self.dimensionNmrAtoms)
        dimensionNmrAtoms[index] = value
        self.dimensionNmrAtoms = dimensionNmrAtoms

    # Utility functions

    def isPartlyAssigned(self):
        """Whether peak is partly assigned"""

        return any(self.dimensionNmrAtoms)

    def isFullyAssigned(self):
        """Whether peak is fully assigned"""

        return all(self.dimensionNmrAtoms)

    def copyTo(self, targetPeakList: PeakList) -> 'Peak':
        """Make (and return) a copy of the Peak in targetPeakList"""

        singleValueTags = ['height', 'volume', 'heightError', 'volumeError', 'figureOfMerit',
                           'annotation', 'comment', 'serial']
        dimensionValueTags = ['position', 'positionError', 'boxWidths', 'lineWidths', ]

        peakList = self._parent
        dimensionCount = peakList.spectrum.dimensionCount

        if dimensionCount != targetPeakList.spectrum.dimensionCount:
            raise ValueError("Cannot copy %sD %s to %sD %s"
                             % (dimensionCount, self.longPid,
                                targetPeakList.spectrum.dimensionCount, targetPeakList.longPid))

        dimensionMapping = commonUtil._axisCodeMapIndices(peakList.spectrum.axisCodes,
                                                          targetPeakList.spectrum.axisCodes)
        if dimensionMapping is None:
            raise ValueError("%s axisCodes %s not compatible with target axisCodes %s"
                             % (self, peakList.spectrum.axisCodes, targetPeakList.spectrum.axisCodes))

        params = dict((tag, getattr(self, tag)) for tag in singleValueTags)
        for tag in dimensionValueTags:
            value = getattr(self, tag)
            params[tag] = [value[dimensionMapping[ii]] for ii in range(dimensionCount)]
        newPeak = targetPeakList.newPeak(**params)

        assignments = []
        for assignment in self.assignedNmrAtoms:
            assignments.append([assignment[dimensionMapping[ii]] for ii in range(dimensionCount)])
        if assignments:
            newPeak.assignedNmrAtoms = assignments
        #
        return newPeak

    def reorderValues(self, values, newAxisCodeOrder):
        """Reorder values in spectrum dimension order to newAxisCodeOrder
        by matching newAxisCodeOrder to spectrum axis code order"""
        return commonUtil.reorder(values, self._parent._parent.axisCodes, newAxisCodeOrder)

    def getInAxisOrder(self, attributeName: str, axisCodes: Sequence[str] = None):
        """Get attributeName in order defined by axisCodes :
           (default order if None)
        """
        if not hasattr(self, attributeName):
            raise AttributeError('Peak object does not have attribute "%s"' % attributeName)

        values = getattr(self, attributeName)
        if axisCodes is None:
            return values
        else:
            # change to order defined by axisCodes
            return self.reorderValues(values, axisCodes)

    def setInAxisOrder(self, attributeName: str, values: Sequence, axisCodes: Sequence[str] = None):
        """Set attributeName from values in order defined by axisCodes
           (default order if None)
        """
        if not hasattr(self, attributeName):
            raise AttributeError('Peak object does not have attribute "%s"' % attributeName)

        if axisCodes is not None:
            # change values to the order appropriate for spectrum
            values = self.reorderValues(values, axisCodes)
        setattr(self, attributeName, values)

    def snapToExtremum(self, halfBoxSearchWidth: int = 2, halfBoxFitWidth: int = 2):
        LibPeak.snapToExtremum(self._apiPeak, halfBoxSearchWidth=halfBoxSearchWidth, halfBoxFitWidth=halfBoxFitWidth)

    def fitPositionHeightLineWidths(self):

        LibPeak.fitPositionHeightLineWidths(self._apiPeak)

    # Implementation functions

    @classmethod
    def _getAllWrappedData(cls, parent: PeakList) -> Tuple[Nmr.Peak, ...]:
        """get wrappedData (Peaks) for all Peak children of parent PeakList"""
        return parent._wrappedData.sortedPeaks()

    @property
    def integral(self):
        """The integral attached to the peak"""
        return self._project._data2Obj[self._wrappedData.integral] if self._wrappedData.integral else None

    @integral.setter
    def integral(self, integral: Union['Integral'] = None):
        """
        link an integral to the peak
        The peak must belong to the spectrum containing the peakList.
        :param integral: single integral
        """
        undo = self._project._undo
        integralStr = "project.getByPid('%s')" % integral.pid if integral else 'None'
        self._startCommandEchoBlock('integral = ' + integralStr, propertySetter=True)
        try:
            self._wrappedData.integral = integral._wrappedData if integral else None
        except Exception as es:
            raise TypeError('Error setting integral')
        finally:
            self._endCommandEchoBlock()


# Connections to parents:
def _newPeak(self: PeakList, height: float = None, volume: float = None,
             heightError: float = None, volumeError: float = None,
             figureOfMerit: float = 1.0, annotation: str = None, comment: str = None,
             position: Sequence[float] = (), positionError: Sequence[float] = (),
             pointPosition: Sequence[float] = (), boxWidths: Sequence[float] = (),
             lineWidths: Sequence[float] = (), serial: int = None) -> Peak:
    """Create new Peak within peakList

    NB you must create the peak before you can assign it. The assignment attributes are:

    - assignedNmrAtoms - A tuple of all (e.g.) assignment triplets for a 3D spectrum

    - dimensionNmrAtoms - A tuple of tuples of assignments, one for each dimension

    See the Peak class for details"""

    defaults = collections.OrderedDict(
            (('height', None), ('volume', None), ('heightError', None), ('volumeError', None),
             ('figureOfMerit', 1.0), ('annotation', None), ('comment', None), ('position', ()),
             ('positionError', ()), ('pointPosition', ()), ('boxWidths', ()), ('lineWidths', ()),
             ('serial', None),
             )
            )

    undo = self._project._undo
    self._startCommandEchoBlock('newPeak', values=locals(), defaults=defaults,
                                parName='newPeak')
    self._project.blankNotification()
    undo.increaseBlocking()
    try:
        apiPeakList = self._apiPeakList
        apiPeak = apiPeakList.newPeak(height=height, volume=volume,
                                      heightError=heightError, volumeError=volumeError,
                                      figOfMerit=figureOfMerit, annotation=annotation, details=comment)
        result = self._project._data2Obj.get(apiPeak)
        if serial is not None:
            try:
                result.resetSerial(serial)
                # modelUtil.resetSerial(apiPeak, serial, 'peaks')
            except ValueError:
                self.project._logger.warning("Could not reset serial of %s to %s - keeping original value"
                                             % (result, serial))
        # set peak position
        # NBNB TBD currently unused parameters could be added, and will have to come in here as well
        apiPeakDims = apiPeak.sortedPeakDims()
        if position:
            for ii, peakDim in enumerate(apiPeakDims):
                peakDim.value = position[ii]
        elif pointPosition:
            for ii, peakDim in enumerate(apiPeakDims):
                peakDim.position = pointPosition[ii]
        if positionError:
            for ii, peakDim in enumerate(apiPeakDims):
                peakDim.valueError = positionError[ii]
        if boxWidths:
            for ii, peakDim in enumerate(apiPeakDims):
                peakDim.boxWidth = boxWidths[ii]
        if lineWidths:
            for ii, peakDim in enumerate(apiPeakDims):
                peakDim.lineWidth = lineWidths[ii]

    finally:
        self._endCommandEchoBlock()
        self._project.unblankNotification()
        undo.decreaseBlocking()

    apiObjectsCreated = [apiPeak]
    apiObjectsCreated.extend(apiPeakDims)
    undo.newItem(Undo._deleteAllApiObjects, apiPeak.root._unDelete,
                 undoArgs=(apiObjectsCreated,),
                 redoArgs=(apiObjectsCreated, (apiPeak.topObject,)))

    # DO creation notifications
    if serial is not None:
        result._finaliseAction('rename')
    result._finaliseAction('create')

    return result


PeakList.newPeak = _newPeak
del _newPeak

# Additional Notifiers:
#
# NB These API notifiers will be called for API peaks - which match both Peaks and Integrals
className = Nmr.PeakDim._metaclass.qualifiedName()
Project._apiNotifiers.append(
        ('_notifyRelatedApiObject', {'pathToObject': 'peak', 'action': 'change'}, className, ''),
        )
for clazz in Nmr.AbstractPeakDimContrib._metaclass.getNonAbstractSubtypes():
    className = clazz.qualifiedName()
    # NB - relies on PeakDimContrib.peakDim.peak still working for deleted peak. Should work.
    Project._apiNotifiers.extend((
        ('_notifyRelatedApiObject', {'pathToObject': 'peakDim.peak', 'action': 'change'},
         className, 'postInit'),
        ('_notifyRelatedApiObject', {'pathToObject': 'peakDim.peak', 'action': 'change'},
         className, 'delete'),
        )
            )

# Notify Peaks change when SpectrumReference changes
# (That means DataDimRef referencing information)
SpectrumReference._setupCoreNotifier('change', AbstractWrapperObject._finaliseRelatedObject,
                                     {'pathToObject': 'spectrum.peaks', 'action': 'change'})
