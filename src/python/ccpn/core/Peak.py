"""
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
__dateModified__ = "$dateModified: 2020-04-01 14:03:21 +0100 (Wed, April 01, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import itertools
import operator
import numpy as np
from typing import Optional, Tuple, Union, Sequence, TypeVar, Any
from ccpn.util import Common as commonUtil
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.PeakList import PeakList, PARABOLICMETHOD
from ccpn.core.NmrAtom import NmrAtom
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
from ccpn.core.lib.peakUtils import snapToExtremum as peakUtilsSnapToExtremum
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, \
    ccpNmrV3CoreSetter, ccpNmrV3CoreUndoBlock, undoBlock
from ccpn.util.Logging import getLogger
from ccpn.util.Common import makeIterableList


ALIASINGCHANGED = '_aliasingChanged'
DIMENSIONNMRATOMSCHANGED = '_dimensionNmrAtomsChanged'


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

    # the attribute name used by current
    _currentAttributeName = 'peaks'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = Nmr.Peak._metaclass.qualifiedName()

    # _linkedPeak = None
    _linkedPeaksName = 'linkedPeaks'

    # CCPN properties
    @property
    def _apiPeak(self) -> Nmr.Peak:
        """API peaks matching Peak"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """id string - serial number converted to string."""
        return str(self._wrappedData.serial)

    @property
    def serial(self) -> int:
        """serial number of Peak, used in Pid and to identify the Peak."""
        return self._wrappedData.serial

    @property
    def _parent(self) -> Optional[PeakList]:
        """PeakList containing Peak."""
        return self._project._data2Obj[self._wrappedData.peakList] \
            if self._wrappedData.peakList in self._project._data2Obj else None

    peakList = _parent

    @property
    def height(self) -> Optional[float]:
        """height of Peak."""
        return self._wrappedData.height

    @height.setter
    def height(self, value: float):
        self._wrappedData.height = value

    @property
    def heightError(self) -> Optional[float]:
        """height error of Peak."""
        return self._wrappedData.heightError

    @heightError.setter
    def heightError(self, value: float):
        self._wrappedData.heightError = value

    @property
    def volume(self) -> Optional[float]:
        """volume of Peak."""
        return self._wrappedData.volume

    @volume.setter
    def volume(self, value: float):
        self._wrappedData.volume = value

    @property
    def volumeError(self) -> Optional[float]:
        """volume error of Peak."""
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
        """Peak text annotation."""
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
    def axisCodes(self) -> Tuple[str, ...]:
        """Spectrum axis codes in dimension order matching position."""
        return self.peakList.spectrum.axisCodes

    @property
    def position(self) -> Tuple[float, ...]:
        """Peak position in ppm (or other relevant unit) in dimension order."""
        return tuple(x.value for x in self._wrappedData.sortedPeakDims())

    @position.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def position(self, value: Sequence):
        # call api changes
        currentAlias = []
        newAlias = []
        for ii, peakDim in enumerate(self._wrappedData.sortedPeakDims()):
            currentAlias.append(peakDim.numAliasing)
            peakDim.value = value[ii]
            peakDim.realValue = None
            newAlias.append(peakDim.numAliasing)

        # aliasing may have changed here
        if currentAlias != newAlias:
            self._checkAliasing()
            setattr(self, ALIASINGCHANGED, True)

    ppmPositions = position

    # @property
    # def ppmPositions(self) -> Tuple[float, ...]:
    #     """Peak position in ppm (or other relevant unit) in dimension order."""
    #     return tuple(x.value for x in self._wrappedData.sortedPeakDims())
    #
    # @ppmPositions.setter
    # @logCommand(get='self', isProperty=True)
    # @ccpNmrV3CoreSetter()
    # def ppmPositions(self, value: Sequence):
    #     # call api changes
    #     for ii, peakDim in enumerate(self._wrappedData.sortedPeakDims()):
    #         peakDim.value = value[ii]
    #         peakDim.realValue = None

    @property
    def positionError(self) -> Tuple[Optional[float], ...]:
        """Peak position error in ppm (or other relevant unit)."""
        return tuple(x.valueError for x in self._wrappedData.sortedPeakDims())

    @positionError.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def positionError(self, value: Sequence):
        for ii, peakDim in enumerate(self._wrappedData.sortedPeakDims()):
            peakDim.valueError = value[ii]

    @property
    def pointPosition(self) -> Tuple[float, ...]:
        """Peak position in points."""
        return tuple(x.position for x in self._wrappedData.sortedPeakDims())

    @pointPosition.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def pointPosition(self, value: Sequence):
        currentAlias = []
        newAlias = []
        for ii, peakDim in enumerate(self._wrappedData.sortedPeakDims()):
            currentAlias.append(peakDim.numAliasing)
            peakDim.position = value[ii]
            newAlias.append(peakDim.numAliasing)

        # aliasing may have changed here
        if currentAlias != newAlias:
            self._checkAliasing()
            setattr(self, ALIASINGCHANGED, True)

    @property
    def boxWidths(self) -> Tuple[Optional[float], ...]:
        """The full width of the peak footprint in points for each dimension,
        i.e. the width of the area that should be considered for integration, fitting, etc."""
        return tuple(x.boxWidth for x in self._wrappedData.sortedPeakDims())

    @boxWidths.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def boxWidths(self, value: Sequence):
        for ii, peakDim in enumerate(self._wrappedData.sortedPeakDims()):
            peakDim.boxWidth = value[ii]

    @property
    def lineWidths(self) -> Tuple[Optional[float], ...]:
        """Full-width-half-height of peak for each dimension, in Hz."""
        return tuple(x.lineWidth for x in self._wrappedData.sortedPeakDims())

    @lineWidths.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def lineWidths(self, value: Sequence):
        for ii, peakDim in enumerate(self._wrappedData.sortedPeakDims()):
            peakDim.lineWidth = value[ii]

    @property
    def aliasing(self) -> Tuple[Optional[float], ...]:
        """Aliasing for the peak in each dimension.
        Defined as integer number of spectralWidths added or subtracted along each dimension
        """
        return tuple(-1 * x.numAliasing for x in self._wrappedData.sortedPeakDims())

    @aliasing.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def aliasing(self, value: Sequence):
        if len(value) != len(self._wrappedData.sortedPeakDims()):
            raise ValueError("Length of %s does not match number of dimensions." % str(value))
        if not all(isinstance(dimVal, int) for dimVal in value):
            raise ValueError("Aliasing values must be integer.")

        currentAlias = []
        newAlias = []
        for ii, peakDim in enumerate(self._wrappedData.sortedPeakDims()):
            currentAlias.append(peakDim.numAliasing)
            peakDim.numAliasing = -1 * value[ii]
            newAlias.append(peakDim.numAliasing)

        # aliasing may/may not have changed here
        if currentAlias != newAlias:
            self._checkAliasing()
            setattr(self, ALIASINGCHANGED, True)

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

        To (re)set the assignment for a single dimension, use the Peak.assignDimension method."""
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
    @logCommand(get='self', isProperty=True)
    # TODO:ED Check this decorator
    # @ccpNmrV3CoreSetter()
    @ccpNmrV3CoreUndoBlock()
    def dimensionNmrAtoms(self, value: Sequence):

        if not isinstance(value, Sequence):
            raise ValueError("dimensionNmrAtoms must be set to a sequence of list/tuples")

        # store the currently attached nmrAtoms
        assigned = makeIterableList(self.assignedNmrAtoms)

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

        # fixme:ED this creates a new chemicalShift that is not caught by the undo stack
        # caught be the new decorator ccpNmrV3CoreUndoBlock
        # original misses creation of api chemicalShift
        apiPeak.assignByDimensions(dimResonances)

        # insert the new attached nmrAtoms - deleted and new will be included so tables can update with deleted peaks/nmrAtoms
        # hopefully traitlets will solve notifier problems
        changedAssigned = tuple(set(assigned) | set(makeIterableList(self.assignedNmrAtoms)))
        setattr(self, DIMENSIONNMRATOMSCHANGED, changedAssigned)

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

        See also dimensionNmrAtoms, which gives assignments per dimension."""

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

        return tuple(sorted(result))

    @assignedNmrAtoms.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def assignedNmrAtoms(self, value: Sequence):

        if not isinstance(value, Sequence):
            raise ValueError("assignedNmrAtoms must be set to a sequence of list/tuples")

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
                if isinstance(atom, NmrAtom):
                    resonance = atom._wrappedData
                    if isotopeCodes[ii] and resonance.isotopeCode not in (isotopeCodes[ii], '?'):
                        raise ValueError("NmrAtom %s, isotope %s, assigned to dimension %s must have isotope %s or '?'"
                                         % (atom, resonance.isotopeCode, ii + 1, isotopeCodes[ii]))

                    ll[ii] = resonance

                elif atom is not None:
                    raise TypeError('Error assigning NmrAtom %s to dimension %s' % (str(atom), ii + 1))

        # set assignments
        apiPeak.assignByContributions(resonances)

    # alternativeNames
    assignments = assignedNmrAtoms
    assignmentsByDimensions = dimensionNmrAtoms

    @property
    def multiplets(self) -> Optional[Tuple[Any]]:
        """List of multiplets containing the Peak."""
        return tuple([self._project._data2Obj[mt] for mt in self._wrappedData.sortedMultiplets()
                      if mt in self._project._data2Obj])

    @logCommand(get='self')
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

    @logCommand(get='self')
    def assignDimension(self, axisCode: str, value: Union[Union[str, 'NmrAtom'],
                                                          Sequence[Union[str, 'NmrAtom']]] = None):
        """Assign dimension with axisCode to value (NmrAtom, or Pid or sequence of either, or None)."""

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

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: PeakList) -> Tuple[Nmr.Peak, ...]:
        """Get wrappedData (Peaks) for all Peak children of parent PeakList."""
        return parent._wrappedData.sortedPeaks()

    def _finaliseAction(self, action: str):
        """Subclassed to handle associated multiplets
        """
        super()._finaliseAction(action=action)

        # if this peak is changed or deleted then it's multiplets/integral need to CHANGE
        # create required as undo may return peak to a multiplet list
        if action in ['change', 'create', 'delete']:
            for mt in self.multiplets:
                mt._finaliseAction(action='change')
            # NOTE:ED does integral need to be notified? - and reverse notifiers in multiplet/integral

        if action in ['change']:

            # check whether the peak aliasing has changed and notify containing spectrum
            if getattr(self, ALIASINGCHANGED, None):
                self._aliasingChanged = False
                self.peakList.spectrum._finaliseAction(action=action)

            # if the assignedNmrAtoms have changed then notifier the nmrAtoms
            # This contains the pre-post set to handle updating the chemicalShift table
            nmrAtoms = getattr(self, DIMENSIONNMRATOMSCHANGED, None)
            if nmrAtoms:
                for nmrAtom in nmrAtoms:
                    if not (nmrAtom.isDeleted or nmrAtom._flaggedForDelete):
                        nmrAtom._finaliseAction(action=action)

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    def isPartlyAssigned(self):
        """Whether peak is partly assigned."""
        return any(self.dimensionNmrAtoms)

    def isFullyAssigned(self):
        """Whether peak is fully assigned."""
        return all(self.dimensionNmrAtoms)

    @logCommand(get='self')
    def copyTo(self, targetPeakList: PeakList) -> 'Peak':
        """Make (and return) a copy of the Peak in targetPeakList."""

        singleValueTags = ['height', 'volume', 'heightError', 'volumeError', 'figureOfMerit',
                           'annotation', 'comment', 'serial']
        dimensionValueTags = ['ppmPositions', 'positionError', 'boxWidths', 'lineWidths', ]

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

        with undoBlock():
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
        by matching newAxisCodeOrder to spectrum axis code order."""
        return commonUtil.reorder(values, self._parent._parent.axisCodes, newAxisCodeOrder)

    def getInAxisOrder(self, attributeName: str, axisCodes: Sequence[str] = None):
        """Get attributeName in order defined by axisCodes :
           (default order if None)"""
        if not hasattr(self, attributeName):
            raise AttributeError('Peak object does not have attribute "%s"' % attributeName)

        values = getattr(self, attributeName)
        if axisCodes is None:
            return values
        else:
            # change to order defined by axisCodes
            return self.reorderValues(values, axisCodes)

    def setInAxisOrder(self, attributeName: str, values: Sequence[Any], axisCodes: Sequence[str] = None):
        """Set attributeName from values in order defined by axisCodes
           (default order if None)"""
        if not hasattr(self, attributeName):
            raise AttributeError('Peak object does not have attribute "%s"' % attributeName)

        if axisCodes is not None:
            # change values to the order appropriate for spectrum
            values = self.reorderValues(values, axisCodes)
        setattr(self, attributeName, values)

    def snapToExtremum(self, halfBoxSearchWidth: int = 4, halfBoxFitWidth: int = 4,
                       minDropFactor: float = 0.1, fitMethod: str = PARABOLICMETHOD,
                       searchBoxMode=False, searchBoxDoFit=False):
        """Snap the Peak to the closest local extrema, if within range."""
        peakUtilsSnapToExtremum(self, halfBoxSearchWidth=halfBoxSearchWidth, halfBoxFitWidth=halfBoxFitWidth,
                                minDropFactor=minDropFactor, fitMethod=fitMethod,
                                searchBoxMode=searchBoxMode, searchBoxDoFit=searchBoxDoFit)


    # def fitPositionHeightLineWidths(self):
    #     """Set the position, height and lineWidth of the Peak."""
    #     LibPeak.fitPositionHeightLineWidths(self._apiPeak)

    @property
    def integral(self):
        """Return the integral attached to the peak."""
        return self._project._data2Obj[self._wrappedData.integral] if self._wrappedData.integral else None

    @integral.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def integral(self, integral: Union['Integral'] = None):
        """Link an integral to the peak.
        The peak must belong to the spectrum containing the peakList.
        :param integral: single integral."""
        spectrum = self._parent.spectrum
        if integral:
            from ccpn.core.Integral import Integral

            if not isinstance(integral, Integral):
                raise TypeError('%s is not of type Integral' % integral)
            if integral not in spectrum.integrals:
                raise ValueError('%s does not belong to spectrum: %s' % (integral.pid, spectrum.pid))

        self._wrappedData.integral = integral._wrappedData if integral else None

    def _linkPeaks(self, peaks):
        """
        NB: this is needed for screening spectrumHits and peakHits. You might see peakCluster instead.
        Saves the peaks in _ccpnInternalData as pids
        """
        pids = [str(peak.pid) for peak in peaks if peak != self and isinstance(peak, Peak)]
        if isinstance(self._ccpnInternalData, dict):

            # a single write is required to the api to notify that a change has occurred,
            # this will prompt for a save of the v2 data
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

    def _getSNRatio(self, ratio=2.5):
        from ccpn.core.PeakList import estimateSNR_1D

        spectrum = self._parent.spectrum
        noiseLevel = spectrum.noiseLevel
        negativeNoiseLevel = spectrum.negativeNoiseLevel
        if noiseLevel is None:
            m = 'Spectrum noise level not defined for %s' % spectrum.pid
            getLogger().debug1(m)
            return None
        if negativeNoiseLevel is None:
            getLogger().debug1('Spectrum negative noise level not defined %s' % spectrum.pid)
            return None
        if self.height is None:
            # print('Peak height not defined %s' % self.pid)
            return None
        snr = estimateSNR_1D(noiseLevels=[noiseLevel, negativeNoiseLevel], signalPoints=[self.height], ratio=ratio)
        return snr[0]

    @logCommand(get='self')
    def estimateVolume(self, volumeIntegralLimit=2.0):
        """Estimate the volume of the peak from a gaussian distribution.
        The width of the volume integral in each dimension is the lineWidth (FWHM) * volumeIntegralLimit,
        the default is 2.0 * FWHM of the peak.
        :param volumeIntegralLimit: integral width as a multiple of lineWidth (FWHM)
        """

        def sigma2fwhm(sigma):
            """Convert sigma to FWHM for gaussian distribution
            """
            return sigma * np.sqrt(8 * np.log(2))

        def fwhm2sigma(fwhm):
            """Convert FWHM to sigma for gaussian distribution
            """
            return fwhm / np.sqrt(8 * np.log(2))

        def make_gauss(N, sigma, mu, height):
            """Generate a gaussian distribution from given parameters
            """
            k = height  # 1.0 / (sigma * np.sqrt(2 * np.pi)) - to give unit area at infinite bounds
            s = -1.0 / (2 * sigma * sigma)
            return k * np.exp(s * (N - mu) * (N - mu))

        lineWidths = self.lineWidths
        if not lineWidths or None in lineWidths:
            raise ValueError('cannot estimate volume, lineWidths not defined or contain None.')
        if not self.height:
            raise ValueError('cannot estimate volume, height not defined.')

        # parameters for a unit height/sigma gaussian
        sigmaX = 1.0
        mu = 0.0
        height = 1.0
        numPoints = 39  # area estimate area < 1e-8 for this number of points

        # calculate integral limit from FWHM - only need positive half
        FWHM = sigma2fwhm(sigmaX)
        lim = volumeIntegralLimit * FWHM / 2.0
        xxSig = np.linspace(0, lim, numPoints)
        vals = make_gauss(xxSig, sigmaX, mu, height)
        area = 2.0*np.trapz(vals, xxSig)

        # note that negative height will give negative volume
        vol = 1.0
        for lw in lineWidths:
            # multiply the values for the gaussian in each dimension
            vol *= (area * (lw / FWHM))

        self.volume = self.height * abs(vol)

        # do I need to set the volume error?
        # self.volumeError = 1e-8

    def _checkAliasing(self):
        """Recalculate the aliasing range for all peaks in the parent spectrum
        """
        spectrum = self.peakList.spectrum
        alias = spectrum._getAliasingRange()
        if alias is not None:
            spectrum.aliasingRange = alias

    #===========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================


#=========================================================================================
# Connections to parents:
#=========================================================================================

@newObject(Peak)
def _newPeak(self: PeakList, height: float = None, volume: float = None,
             heightError: float = None, volumeError: float = None,
             figureOfMerit: float = 1.0, annotation: str = None, comment: str = None,
             ppmPositions: Sequence[float] = (), position: Sequence[float] = None, positionError: Sequence[float] = (),
             pointPosition: Sequence[float] = (), boxWidths: Sequence[float] = (),
             lineWidths: Sequence[float] = (), serial: int = None) -> Peak:
    """Create a new Peak within a peakList

    NB you must create the peak before you can assign it. The assignment attributes are:
    - assignedNmrAtoms - A tuple of all (e.g.) assignment triplets for a 3D spectrum
    - dimensionNmrAtoms - A tuple of tuples of assignments, one for each dimension

    See the Peak class for details.

    :param height: height of the peak (related attributes: volume, volumeError, lineWidths)
    :param volume:
    :param heightError:
    :param volumeError:
    :param figureOfMerit:
    :param annotation:
    :param comment: optional comment string
    :param ppmPositions: peak position in ppm for each dimension (related attributes: positionError, pointPosition)
    :param position: OLD: peak position in ppm for each dimension (related attributes: positionError, pointPosition)
    :param positionError:
    :param pointPosition:
    :param boxWidths:
    :param lineWidths:
    :param serial: optional serial number.
    :return: a new Peak instance.
    """

    if position is not None:
        ppmPositions = position  # Backward compatibility

    apiPeakList = self._apiPeakList
    apiPeak = apiPeakList.newPeak(height=height, volume=volume,
                                  heightError=heightError, volumeError=volumeError,
                                  figOfMerit=figureOfMerit, annotation=annotation, details=comment)
    result = self._project._data2Obj.get(apiPeak)
    if result is None:
        raise RuntimeError('Unable to generate new Peak item')

    if serial is not None:
        try:
            result.resetSerial(serial)
        except ValueError:
            getLogger().warning("Could not reset serial of %s to %s - keeping original value"
                                % (result, serial))

    apiPeakDims = apiPeak.sortedPeakDims()
    if ppmPositions:
        for ii, peakDim in enumerate(apiPeakDims):
            peakDim.value = ppmPositions[ii]
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

    return result


@newObject(Peak)
def _newPickedPeak(self: PeakList, pointPositions: Sequence[float] = None, height: float = None,
                   lineWidths: Sequence[float] = (), fitMethod: str = 'gaussian', serial: int = None) -> Peak:
    """Create a new Peak within a peakList from a picked peak

    See the Peak class for details.

    :param height: height of the peak (related attributes: volume, volumeError, lineWidths)
    :param pointPositions: peak position in points for each dimension (related attributes: positionError, pointPosition)
    :param fitMethod: type of curve fitting
    :param lineWidths:
    :param serial: optional serial number.
    :return: a new Peak instance.
    """

    apiPeakList = self._apiPeakList
    apiPeak = apiPeakList.newPeak()
    result = self._project._data2Obj.get(apiPeak)
    if result is None:
        raise RuntimeError('Unable to generate new Peak item')

    if serial is not None:
        try:
            result.resetSerial(serial)
        except ValueError:
            getLogger().warning("Could not reset serial of %s to %s - keeping original value"
                                % (result, serial))

    apiDataSource = self.spectrum._apiDataSource
    apiDataDims = apiDataSource.sortedDataDims()
    apiPeakDims = apiPeak.sortedPeakDims()

    for i, peakDim in enumerate(apiPeakDims):
        dataDim = apiDataDims[i]

        if dataDim.className == 'FreqDataDim':
            dataDimRef = dataDim.primaryDataDimRef
        else:
            dataDimRef = None

        if dataDimRef:
            peakDim.numAliasing = int(divmod(pointPositions[i], dataDim.numPointsOrig)[0])
            peakDim.position = float(pointPositions[i] + 1 - peakDim.numAliasing * dataDim.numPointsOrig)  # API position starts at 1

        else:
            peakDim.position = float(pointPositions[i] + 1)

        if fitMethod and lineWidths and lineWidths[i] is not None:
            peakDim.lineWidth = dataDim.valuePerPoint * lineWidths[i]  # conversion from points to Hz

    apiPeak.height = apiDataSource.scale * height

    return result


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

# EJB 20181122: moved to SpectrumReference
# Notify Peaks change when SpectrumReference changes
# (That means DataDimRef referencing information)
# SpectrumReference._setupCoreNotifier('change', AbstractWrapperObject._finaliseRelatedObject,
#                                      {'pathToObject': 'spectrum.peaks', 'action': 'change'})
