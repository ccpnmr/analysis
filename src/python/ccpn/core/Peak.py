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
__dateModified__ = "$dateModified: 2021-09-03 12:18:43 +0100 (Fri, September 03, 2021) $"
__version__ = "$Revision: 3.0.4 $"
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
from functools import partial
from typing import Optional, Tuple, Union, Sequence, TypeVar, Any

from ccpn.core.lib.AxisCodeLib import _axisCodeMapIndices
from ccpn.util import Common as commonUtil
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.PeakList import PeakList, PARABOLICMETHOD
from ccpn.core.NmrAtom import NmrAtom
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
from ccpn.core.lib.peakUtils import _getPeakSNRatio, snapToExtremum as peakUtilsSnapToExtremum
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, deleteObject, \
    ccpNmrV3CoreSetter, undoBlock, undoBlockWithoutSideBar, undoStackBlocking, ccpNmrV3CoreUndoBlock
from ccpn.util.Logging import getLogger
from ccpn.util.Common import makeIterableList, isIterable
from ccpn.util.Constants import SCALETOLERANCE


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
    def spectrum(self):
        """Convenience property to get the spectrum, equivalent to peak.peakList.spectrum"""
        return self.peakList.spectrum

    @property
    def height(self) -> Optional[float]:
        """height of Peak."""
        if self._wrappedData.height is None:
            return None

        scale = self.peakList.spectrum.scale
        scale = scale if scale is not None else 1.0
        if -SCALETOLERANCE < scale < SCALETOLERANCE:
            getLogger().warning('Scaling {}.height by minimum tolerance (±{})'.format(self, SCALETOLERANCE))

        return self._wrappedData.height * scale

    @height.setter
    @logCommand(get='self', isProperty=True)
    def height(self, value: Union[float, int, None]):
        if not isinstance(value, (float, int, type(None))):
            raise TypeError('height must be a float, integer or None')
        elif value is not None and (value - value) != 0.0:
            raise TypeError('height cannot be NaN or Infinity')

        if value is None:
            self._wrappedData.height = None
        else:
            scale = self.peakList.spectrum.scale
            scale = scale if scale is not None else 1.0
            if -SCALETOLERANCE < scale < SCALETOLERANCE:
                getLogger().warning('Scaling {}.height by minimum tolerance (±{})'.format(self, SCALETOLERANCE))
                self._wrappedData.height = None
            else:
                self._wrappedData.height = float(value) / scale

    @property
    def heightError(self) -> Optional[float]:
        """height error of Peak."""
        if self._wrappedData.heightError is None:
            return None

        scale = self.peakList.spectrum.scale
        scale = scale if scale is not None else 1.0
        if -SCALETOLERANCE < scale < SCALETOLERANCE:
            getLogger().warning('Scaling {}.heightError by minimum tolerance (±{})'.format(self, SCALETOLERANCE))

        return self._wrappedData.heightError * scale

    @heightError.setter
    @logCommand(get='self', isProperty=True)
    def heightError(self, value: Union[float, int, None]):
        if not isinstance(value, (float, int, type(None))):
            raise TypeError('heightError must be a float, integer or None')
        elif value is not None and (value - value) != 0.0:
            raise TypeError('heightError cannot be NaN or Infinity')

        if value is None:
            self._wrappedData.heightError = None
        else:
            scale = self.peakList.spectrum.scale
            scale = scale if scale is not None else 1.0
            if -SCALETOLERANCE < scale < SCALETOLERANCE:
                getLogger().warning('Scaling {}.heightError by minimum tolerance (±{})'.format(self, SCALETOLERANCE))
                self._wrappedData.heightError = None
            else:
                self._wrappedData.heightError = float(value) / scale

    @property
    def volume(self) -> Optional[float]:
        """volume of Peak."""
        if self._wrappedData.volume is None:
            return None

        scale = self.peakList.spectrum.scale
        scale = scale if scale is not None else 1.0
        if -SCALETOLERANCE < scale < SCALETOLERANCE:
            getLogger().warning('Scaling {}.volume by minimum tolerance (±{})'.format(self, SCALETOLERANCE))

        return self._wrappedData.volume * scale

    @volume.setter
    @logCommand(get='self', isProperty=True)
    def volume(self, value: Union[float, int, None]):
        if not isinstance(value, (float, int, type(None))):
            raise TypeError('volume must be a float, integer or None')
        elif value is not None and (value - value) != 0.0:
            raise TypeError('volume cannot be NaN or Infinity')

        if value is None:
            self._wrappedData.volume = None
        else:
            scale = self.peakList.spectrum.scale
            scale = scale if scale is not None else 1.0
            if -SCALETOLERANCE < scale < SCALETOLERANCE:
                getLogger().warning('Scaling {}.volume by minimum tolerance (±{})'.format(self, SCALETOLERANCE))
                self._wrappedData.volume = None
            else:
                self._wrappedData.volume = float(value) / scale

    @property
    def volumeError(self) -> Optional[float]:
        """volume error of Peak."""
        if self._wrappedData.volumeError is None:
            return None

        scale = self.peakList.spectrum.scale
        scale = scale if scale is not None else 1.0
        if -SCALETOLERANCE < scale < SCALETOLERANCE:
            getLogger().warning('Scaling {}.volumeError by minimum tolerance (±{})'.format(self, SCALETOLERANCE))

        return self._wrappedData.volumeError * scale

    @volumeError.setter
    @logCommand(get='self', isProperty=True)
    def volumeError(self, value: Union[float, int, None]):
        if not isinstance(value, (float, int, type(None))):
            raise TypeError('volumeError must be a float, integer or None')
        elif value is not None and (value - value) != 0.0:
            raise TypeError('volumeError cannot be NaN or Infinity')

        if value is None:
            self._wrappedData.volumeError = None
        else:
            scale = self.peakList.spectrum.scale
            scale = scale if scale is not None else 1.0
            if -SCALETOLERANCE < scale < SCALETOLERANCE:
                getLogger().warning('Scaling {}.volumeError by minimum tolerance (±{})'.format(self, SCALETOLERANCE))
                self._wrappedData.volumeError = None
            else:
                self._wrappedData.volumeError = float(value) / scale

    @property
    def figureOfMerit(self) -> Optional[float]:
        """figureOfMerit of Peak, between 0.0 and 1.0 inclusive."""
        return self._wrappedData.figOfMerit

    @figureOfMerit.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def figureOfMerit(self, value: float):
        if self._wrappedData.figOfMerit == value:
            return
        self._wrappedData.figOfMerit = value

        # recalculate the shifts
        assigned = set(makeIterableList(self.assignments))
        shifts = set(cs for nmrAt in assigned for cs in nmrAt.chemShifts if cs and not cs.isDeleted)

        self._childActions.extend(sh._recalculateShiftValue for sh in shifts)
        self._finaliseChildren.extend((sh, 'change') for sh in shifts)

    @property
    def annotation(self) -> Optional[str]:
        """Peak text annotation."""
        return self._wrappedData.annotation

    @annotation.setter
    @logCommand(get='self', isProperty=True)
    def annotation(self, value: Optional[str]):
        if not isinstance(value, (str, type(None))):
            raise ValueError("annotation must be a string or None")
        else:
            self._wrappedData.annotation = value

    @property
    def axisCodes(self) -> Tuple[str, ...]:
        """Spectrum axis codes in dimension order matching position."""
        return self.spectrum.axisCodes

    @property
    def position(self) -> Tuple[float, ...]:
        """Peak position in ppm (or other relevant unit) in dimension order."""
        return tuple(x.value for x in self._wrappedData.sortedPeakDims())

    @position.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def position(self, value: Sequence):
        # call api changes
        shifts = set()
        ff = self._project._data2Obj.get

        for ii, peakDim in enumerate(self._wrappedData.sortedPeakDims()):
            _old = peakDim.position  # the current pointPosition, quick to get
            peakDim.value = value[ii]
            peakDim.realValue = None

            # log any peak assignments that have moved in this axis
            if peakDim.position != _old:
                assigned = set([ff(pdc.resonance) for pdc in peakDim.mainPeakDimContribs if hasattr(pdc, 'resonance')])
                shifts |= set(sh for nmrAt in assigned for sh in nmrAt.chemShifts)

        self._childActions.extend(sh._recalculateShiftValue for sh in shifts)
        self._finaliseChildren.extend((sh, 'change') for sh in shifts)

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
    def pointPositions(self) -> Tuple[float, ...]:
        """Peak position in points."""
        return tuple(x.position for x in self._wrappedData.sortedPeakDims())

    @pointPositions.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def pointPositions(self, value: Sequence):
        shifts = set()
        ff = self._project._data2Obj.get

        for ii, peakDim in enumerate(self._wrappedData.sortedPeakDims()):
            _old = peakDim.position  # the current pointPositions
            peakDim.position = value[ii]

            # log any peak assignments that have moved in this axis
            if peakDim.position != _old:
                assigned = set([ff(pdc.resonance) for pdc in peakDim.mainPeakDimContribs if hasattr(pdc, 'resonance')])
                shifts |= set(sh for nmrAt in assigned for sh in nmrAt.chemShifts)

        self._childActions.extend(sh._recalculateShiftValue for sh in shifts)
        self._finaliseChildren.extend((sh, 'change') for sh in shifts)

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
        """Full-width-half-height of peak for each dimension, in Hz/ppm."""
        return tuple(x.lineWidth for x in self._wrappedData.sortedPeakDims())

    @lineWidths.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def lineWidths(self, value: Sequence):
        for ii, peakDim in enumerate(self._wrappedData.sortedPeakDims()):
            peakDim.lineWidth = value[ii]

    # @property
    # def ppmLineWidths(self) -> Tuple[Optional[float], ...]:
    #     """Full-width-half-height of peak for each dimension, in ppm."""
    #     return tuple(peakDim.lineWidth * peakDim.dataDim.valuePerPoint if peakDim.lineWidth is not None else None
    #                  for peakDim in self._wrappedData.sortedPeakDims())
    #
    # @ppmLineWidths.setter
    # @logCommand(get='self', isProperty=True)
    # @ccpNmrV3CoreSetter()
    # def ppmLineWidths(self, value: Sequence):
    #     for ii, peakDim in enumerate(self._wrappedData.sortedPeakDims()):
    #         peakDim.lineWidth = value[ii] / peakDim.dataDim.valuePerPoint if value[ii] is not None else None

    ppmLineWidths = lineWidths

    @property
    def pointLineWidths(self) -> Tuple[Optional[float], ...]:
        """Full-width-half-height of peak for each dimension, in points."""
        # currently assumes that internal storage is in ppms
        return tuple(peakDim.lineWidth / peakDim.dataDim.valuePerPoint if peakDim.lineWidth is not None else None
                     for peakDim in self._wrappedData.sortedPeakDims())

    @pointLineWidths.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def pointLineWidths(self, value: Sequence):
        for ii, peakDim in enumerate(self._wrappedData.sortedPeakDims()):
            peakDim.lineWidth = value[ii] * peakDim.dataDim.valuePerPoint if value[ii] is not None else None

    @property
    def aliasing(self) -> Tuple[Optional[float], ...]:
        """Aliasing for the peak in each dimension.
        Defined as integer number of spectralWidths added or subtracted along each dimension
        """
        aliasing = []
        for peakDim in self._wrappedData.sortedPeakDims():
            axisReversed = -1
            expDimRef = peakDim.dataDim.expDim.findFirstExpDimRef(serial=1)
            if expDimRef:
                axisReversed = -1 if expDimRef.isAxisReversed else 1
            aliasing.append(axisReversed * peakDim.numAliasing)
        return tuple(aliasing)

    @aliasing.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def aliasing(self, value: Sequence):
        if len(value) != len(self._wrappedData.sortedPeakDims()):
            raise ValueError("Length of %s does not match number of dimensions." % str(value))
        if not all(isinstance(dimVal, int) for dimVal in value):
            raise ValueError("Aliasing values must be integer.")

        # call api changes
        shifts = set()
        ff = self._project._data2Obj.get
        for ii, peakDim in enumerate(self._wrappedData.sortedPeakDims()):
            # log any peak assignments that have moved in this axis
            if peakDim.numAliasing != -1 * value[ii]:
                assigned = set([ff(pdc.resonance) for pdc in peakDim.mainPeakDimContribs if hasattr(pdc, 'resonance')])
                peakDim.numAliasing = -1 * value[ii]

                shifts |= set(sh for nmrAt in assigned for sh in nmrAt.chemShifts)

        self._childActions.extend(sh._recalculateShiftValue for sh in shifts)
        self._finaliseChildren.extend((sh, 'change') for sh in shifts)

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

    @property
    def _dimensionNmrAtoms(self) -> Tuple[Tuple['NmrAtom', ...], ...]:
        """Transparent method to control notifiers"""
        return self.dimensionNmrAtoms

    @_dimensionNmrAtoms.setter
    @ccpNmrV3CoreSetter()
    def _dimensionNmrAtoms(self, value: Sequence):
        """Assign by Dimensions
        Ccpn Internal:used by assignDimension/dimensionNmrAtoms - not to be called elsewhere
        Doesn't need undoBlock/CoreSetter as this is taken care of by calling method
        """

        if not isinstance(value, Sequence):
            raise ValueError("dimensionNmrAtoms must be sequence of list/tuples")

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
                    raise ValueError("dimensionNmrAtoms must be sequence of list/tuples")

                atoms = tuple(self.getByPid(x) if isinstance(x, str) else x for x in atoms)
                resonances = tuple(x._wrappedData for x in atoms if x is not None)
                if isotopeCode and isotopeCode != '?':
                    # check for isotope match
                    for x in resonances:
                        if x.isotopeCode not in (isotopeCode, '?'):
                            msg = "IsotopeCodes mismatch between NmrAtom %s and Spectrum. " \
                                  "Consider changing NmrAtom isotopeCode from %s to %s, None, or '?'" \
                                  " to avoid future warnings." % (x.name, x.isotopeCode, isotopeCode)
                            getLogger().warning(msg)  # don't raise errors. NmrAtoms are just labels and can be assigned to anything if user wants so.

                dimResonances.append(resonances)

        apiPeak.assignByDimensions(dimResonances)

    # def _tempFunc(self, nmrResidues, shifts):
    #     # update the assigned nmrAtom chemical shift values - notify the nmrResidues and chemShifts
    #     self._childActions.extend(sh._recalculateShiftValue for sh in shifts)
    #     self._finaliseChildren.extend((nmr, 'change') for nmr in nmrResidues)
    #     self._finaliseChildren.extend((sh, 'change') for sh in shifts)

    def _recalculatePeakShifts(self, nmrResidues, shifts):
        # update the assigned nmrAtom chemical shift values - notify the nmrResidues and chemShifts
        for sh in shifts:
            sh._recalculateShiftValue()
        for nmr in nmrResidues:
            nmr._finaliseAction('change')
        for sh in shifts:
            sh._finaliseAction('change')

    @dimensionNmrAtoms.setter
    @logCommand(get='self', isProperty=True)
    # @ccpNmrV3CoreSetter()
    def dimensionNmrAtoms(self, value: Sequence):

        _pre = set(makeIterableList(self.assignedNmrAtoms))
        _post = set(makeIterableList(value))
        nmrResidues = set(nmr.nmrResidue for nmr in (_pre | _post))
        shifts = list(set(cs for nmrAt in (_pre | _post) for cs in nmrAt.chemShifts))
        _thisNmr = self.spectrum.chemicalShiftList._getNmrAtoms()

        # # NOTE:ED - need this check as nmrAtoms must be unique in chemicalShiftList
        # for nmrAtom in (_post - _pre - _thisNmr):
        #     if self.spectrum.chemicalShiftList._getChemicalShift(nmrAtom=nmrAtom):
        #         raise RuntimeError(f'Peak.dimensionNmrAtoms: {nmrAtom} already in list')

        with undoBlock():
            with undoStackBlocking() as addUndoItem:
                addUndoItem(undo=partial(self._recalculatePeakShifts, nmrResidues, shifts))

            # set the value
            self._dimensionNmrAtoms = value

            # add those that are not already in the list - otherwise recalculate
            for nmrAtom in (_post - _pre - _thisNmr):
                self.spectrum.chemicalShiftList._newChemicalShift(nmrAtom=nmrAtom)

            self._recalculatePeakShifts(nmrResidues, shifts)
            with undoStackBlocking() as addUndoItem:
                addUndoItem(redo=partial(self._recalculatePeakShifts, nmrResidues, shifts))

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

    @property
    def _assignedNmrAtoms(self) -> Tuple[Tuple[Optional['NmrAtom'], ...], ...]:
        """Transparent method to control notifiers"""
        return self.assignedNmrAtoms

    @_assignedNmrAtoms.setter
    @ccpNmrV3CoreSetter()
    def _assignedNmrAtoms(self, value: Sequence):
        """Assign by Contributions
        Ccpn Internal: used by assignedNmrAtoms - not to be called elsewhere
        Doesn't need undoBlock/CoreSetter as this is taken care of by calling method
        """
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

        # store the currently attached nmrAtoms
        _assigned = set(makeIterableList(self.assignedNmrAtoms))

        # set assignments
        apiPeak.assignByContributions(resonances)

    @assignedNmrAtoms.setter
    @logCommand(get='self', isProperty=True)
    # @ccpNmrV3CoreSetter()
    def assignedNmrAtoms(self, value: Sequence):

        _pre = set(makeIterableList(self.assignedNmrAtoms))
        _post = set(makeIterableList(value))
        nmrResidues = set(nmr.nmrResidue for nmr in (_pre | _post))
        shifts = list(set(cs for nmrAt in (_pre | _post) for cs in nmrAt.chemShifts))
        _thisNmr = self.spectrum.chemicalShiftList._getNmrAtoms()

        # # NOTE:ED - need this check as nmrAtoms must be unique in chemicalShiftList
        # for nmrAtom in (_post - _pre - _thisNmr):
        #     if self.spectrum.chemicalShiftList._getChemicalShift(nmrAtom=nmrAtom):
        #         raise RuntimeError(f'Peak.assignedNmrAtoms: {nmrAtom} already in list')

        with undoBlock():
            with undoStackBlocking() as addUndoItem:
                addUndoItem(undo=partial(self._recalculatePeakShifts, nmrResidues, shifts))

            # set the value
            self._assignedNmrAtoms = value

            # add those that are not already in the list - otherwise recalculate
            for nmrAtom in (_post - _pre - _thisNmr):
                self.spectrum.chemicalShiftList._newChemicalShift(nmrAtom=nmrAtom)

            self._recalculatePeakShifts(nmrResidues, shifts)
            with undoStackBlocking() as addUndoItem:
                addUndoItem(redo=partial(self._recalculatePeakShifts, nmrResidues, shifts))

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

        axisCodes = self.spectrum.axisCodes
        try:
            axis = axisCodes.index(axisCode)
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

        dimensionNmrAtoms[axis] = value
        self.dimensionNmrAtoms = dimensionNmrAtoms

    def getByAxisCodes(self, attributeName: str, axisCodes: Sequence[str] = None, exactMatch: bool = False):
        """Return values defined by attributeName in order defined by axisCodes:
        (default order if None).

        Perform a mapping if exactMatch=False (eg. 'H' to 'Hn')

        NB: Use getByDimensions for dimensions (1..dimensionCount) based access
        """
        if not hasattr(self, attributeName):
            raise AttributeError('Object %s does not have attribute "%s"' %
                                 (self, attributeName)
                                 )

        if not isIterable(axisCodes):
            raise ValueError('axisCodes is not iterable "%s"; expected list or tuple' %
                             axisCodes
                             )

        if axisCodes is not None and not exactMatch:
            axisCodes = self.spectrum._mapAxisCodes(axisCodes)

        try:
            values = getattr(self, attributeName)
        except AttributeError:
            raise AttributeError('Error getting attribute "%s" from object %s' %
                                 (attributeName, self)
                                 )
        if not isIterable(values):
            raise ValueError('Attribute "%s" of object %s is not iterable; "%s"' %
                             (attributeName, self, values)
                             )
        if axisCodes is not None:
            # change to order defined by axisCodes
            values = self.spectrum._reorderValues(values, axisCodes)
        return values

    def setByAxisCodes(self, attributeName: str, values: Sequence, axisCodes: Sequence[str] = None, exactMatch: bool = False):
        """Set attributeName to values in order defined by axisCodes:
        (default order if None)

        Perform a mapping if exactMatch=False (eg. 'H' to 'Hn')

        NB: Use setByDimensions for dimensions (1..dimensionCount) based access
        """
        if not hasattr(self, attributeName):
            raise AttributeError('Object %s does not have attribute "%s"' %
                                 (self, attributeName)
                                 )

        if not isIterable(values):
            raise ValueError('Values "%s" is not iterable' % (values)
                             )

        if not isIterable(axisCodes):
            raise ValueError('axisCodes is not iterable "%s"; expected list or tuple' %
                             axisCodes
                             )

        if axisCodes is not None and not exactMatch:
            axisCodes = self.spectrum._mapAxisCodes(axisCodes)

        if axisCodes is not None:
            # change values to the order appropriate for spectrum
            values = self.spectrum._reorderValues(values, axisCodes)
        try:
            setattr(self, attributeName, values)
        except AttributeError:
            raise AttributeError('Unable to set attribute "%s" of object %s to "%s"' %
                                 (attributeName, self, values)
                                 )

    def getByDimensions(self, attributeName: str, dimensions: Sequence[int] = None):
        """Return values defined by attributeName in order defined by dimensions (1..dimensionCount).
           (default order if None)
           NB: Use getByAxisCodes for axisCode based access
        """
        if not hasattr(self, attributeName):
            raise AttributeError('Object %s does not have attribute "%s"' %
                                 (self, attributeName)
                                 )
        values = getattr(self, attributeName)

        if dimensions is None:
            return values

        newValues = []
        for dim in dimensions:
            if not (1 <= dim <= self.spectrum.dimensionCount):
                raise ValueError('Invalid dimension "%d"; should be one of %s' % (dim, self.spectrum.dimensions))
            else:
                newValues.append(values[dim - 1])
        return newValues

    def setByDimensions(self, attributeName: str, values: Sequence, dimensions: Sequence[int] = None):
        """Set attributeName to values in order defined by dimensions (1..dimensionCount).
           (default order if None)
           NB: Use setByAxisCodes for axisCode based access
        """
        if not hasattr(self, attributeName):
            raise AttributeError('Object %s does not have attribute "%s"' %
                                 (self, attributeName)
                                 )

        if dimensions is None:
            setattr(self, attributeName, values)
            return

        newValues = []
        for dim in dimensions:
            if not (1 <= dim <= self.spectrum.dimensionCount):
                raise ValueError('Invalid dimension "%d"; should be one of %s' % (dim, self.spectrum.dimensions))
            else:
                newValues.append(values[dim - 1])
        setattr(self, attributeName, newValues)

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
        if not super()._finaliseAction(action):
            return

        # if this peak is changed or deleted then it's multiplets/integral need to CHANGE
        # create required as undo may return peak to a multiplet list
        if action in ['change', 'create', 'delete']:
            for mt in self.multiplets:
                mt._finaliseAction('change')
            # NOTE:ED does integral need to be notified? - and reverse notifiers in multiplet/integral

    def delete(self):
        """Delete a peak."""
        assigned = tuple(() for _ in range(self.peakList.spectrum.dimensionCount))

        with undoBlockWithoutSideBar():

            self.dimensionNmrAtoms = assigned
            self._delete()

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
                           'annotation', 'comment', ]
        dimensionValueTags = ['ppmPositions', 'positionError', 'boxWidths', 'lineWidths', ]

        peakList = self._parent
        dimensionCount = peakList.spectrum.dimensionCount

        if dimensionCount != targetPeakList.spectrum.dimensionCount:
            raise ValueError("Cannot copy %sD %s to %sD %s"
                             % (dimensionCount, self.longPid,
                                targetPeakList.spectrum.dimensionCount, targetPeakList.longPid))

        dimensionMapping = _axisCodeMapIndices(peakList.spectrum.axisCodes,
                                                                         targetPeakList.spectrum.axisCodes)
        if dimensionMapping is None:
            raise ValueError("%s axisCodes %s not compatible with target axisCodes %s"
                             % (self, peakList.spectrum.axisCodes, targetPeakList.spectrum.axisCodes))

        with undoBlockWithoutSideBar():
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

    # def _linkPeaks(self, peaks):
    #     """
    #     NB: this is needed for screening spectrumHits and peakHits. You might see peakCluster instead.
    #     Saves the peaks in _ccpnInternalData as pids
    #     """
    #     pids = [str(peak.pid) for peak in peaks if peak != self and isinstance(peak, Peak)]
    #     if isinstance(self._ccpnInternalData, dict):
    #
    #         # a single write is required to the api to notify that a change has occurred,
    #         # this will prompt for a save of the v2 data
    #         tempCcpn = self._ccpnInternalData.copy()
    #         tempCcpn[self._linkedPeaksName] = pids
    #         self._ccpnInternalData = tempCcpn
    #     else:
    #         raise ValueError("Peak.linkPeaks: CCPN internal must be a dictionary")
    #
    # @property
    # def _linkedPeaks(self):
    #     """
    #     NB: this is needed for screening spectrumHits and peakHits. You might see peakCluster instead.
    #     It returns a list of peaks belonging to other peakLists or spectra which are required to be linked to this particular peak.
    #     This functionality is not implemented in the model. Saves the Peak pids in _ccpnInternalData.
    #     :return: a list of peaks
    #     """
    #     pids = self._ccpnInternalData.get(self._linkedPeaksName) or []
    #     peaks = [self.project.getByPid(pid) for pid in pids if pid is not None]
    #     return peaks

    @property
    def signalToNoiseRatio(self):
        """
        :return: float. Estimated  Signal to Noise ratio based on the spectrum noiseLevel values.
        SNratio = |factor*(height/DeltaNoise)|
                height: peak height
                DeltaNoise: spectrum noise levels
                factor: multiplication factor. Default: 2.5
        """
        return _getPeakSNRatio(self)

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
        area = 2.0 * np.trapz(vals, xxSig)

        # note that negative height will give negative volume
        vol = 1.0
        for lw in lineWidths:
            # multiply the values for the gaussian in each dimension
            vol *= (area * (lw / FWHM))

        self.volume = self.height * abs(vol)

        # do I need to set the volume error?
        # self.volumeError = 1e-8

    def fit(self, fitMethod=None, halfBoxSearchWidth=2, keepPosition=False, iterations=10):
        """
        Fit the peak to recalculate position and lineWidths.
        Use peak.estimateVolume to recalculate the volume.

        :param fitMethod: str, one of ['gaussian', 'lorentzian', 'parabolic']
               Default: the fitting method defined in the general preferences.
               If not given or not included in the available options, it uses the default.
        :param halfBoxSearchWidth: int. Default: 2.
               Used to increase the searching area limits from the initial position.
        :param keepPosition: bool. Default: False.
               if True, reset to the original position after applying the fitting method.
               Height is calculated using spectrum.getHeight()
        :param iterations: int. Default: 3.
               How many times the fitting method will run before it converges.
        :return: None.
        """
        from ccpn.core.PeakList import PICKINGMETHODS
        from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar, notificationEchoBlocking

        if not fitMethod in PICKINGMETHODS:
            fitMethod = self._project.application.preferences.general.peakFittingMethod
        peak = self
        peakList = peak.peakList
        originalPosition = peak.position
        lastLWsFound = []
        consecutiveSameLWsCount = 0
        maxSameLWsCount = 3  # if the same values are found in the last x iterations, then it breaks the loop.
        with undoBlockWithoutSideBar():
            with notificationEchoBlocking():
                while iterations > 0 and consecutiveSameLWsCount <= maxSameLWsCount:
                    peakList.fitExistingPeaks([peak], fitMethod=fitMethod,
                                              halfBoxSearchWidth=halfBoxSearchWidth, singularMode=True)
                    if keepPosition:
                        peak.position = originalPosition
                        peak.height = peakList.spectrum.getHeight(peak.ppmPositions)
                    if np.array_equal(lastLWsFound, peak.lineWidths):
                        consecutiveSameLWsCount += 1
                    else:
                        consecutiveSameLWsCount = 0
                    lastLWsFound = peak.lineWidths
                    iterations -= 1
        getLogger().info('Peak fit completed for %s' % peak)
        return

    # def _checkAliasing(self):
    #     """Recalculate the aliasing range for all peaks in the parent spectrum
    #     """
    #     spectrum = self.peakList.spectrum
    #     alias = spectrum._getAliasingRange()
    #     if alias is not None:
    #         spectrum.aliasingRange = alias

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
             pointPositions: Sequence[float] = (), boxWidths: Sequence[float] = (),
             lineWidths: Sequence[float] = (), ppmLineWidths: Sequence[float] = (), pointLineWidths: Sequence[float] = (),
             ) -> Peak:
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
    :param ppmPositions: peak position in ppm for each dimension (related attributes: positionError, pointPositions)
    :param position: OLD: peak position in ppm for each dimension (related attributes: positionError, pointPositions)
    :param positionError:
    :param pointPositions:
    :param boxWidths:
    :param lineWidths:
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

    apiPeakDims = apiPeak.sortedPeakDims()
    if ppmPositions:
        for ii, peakDim in enumerate(apiPeakDims):
            peakDim.value = ppmPositions[ii]
    elif pointPositions:

        pointCounts = result.spectrum.pointCounts
        for ii, peakDim in enumerate(apiPeakDims):
            # move the peak to the correct aliased position
            alias = int((pointPositions[ii] - 1) // pointCounts[ii])
            pos = float((pointPositions[ii] - 1) % pointCounts[ii]) + 1.0  # API position starts at 1
            peakDim.numAliasing = alias
            peakDim.position = pos

    if positionError:
        for ii, peakDim in enumerate(apiPeakDims):
            peakDim.valueError = positionError[ii]
    if boxWidths:
        for ii, peakDim in enumerate(apiPeakDims):
            peakDim.boxWidth = boxWidths[ii]

    # currently lineWidths/ppmLineWidths are both in Hz/ppm
    if lineWidths:
        for ii, peakDim in enumerate(apiPeakDims):
            peakDim.lineWidth = lineWidths[ii]
    elif ppmLineWidths:
        for ii, peakDim in enumerate(apiPeakDims):
            peakDim.lineWidth = ppmLineWidths[ii]
    elif pointLineWidths:
        for peakDim, pointLineWidth in zip(apiPeakDims, pointLineWidths):
            peakDim.lineWidth = (pointLineWidth * peakDim.dataDim.valuePerPoint) if pointLineWidth else None

    result.height = height  # use the method to store the unit-scaled value
    result.volume = volume
    result.heightError = heightError
    result.volumeError = volumeError

    return result


@newObject(Peak)
def _newPickedPeak(self: PeakList, pointPositions: Sequence[float] = None, height: float = None,
                   lineWidths: Sequence[float] = (), fitMethod: str = 'gaussian') -> Peak:
    """Create a new Peak within a peakList from a picked peak

    See the Peak class for details.

    :param height: height of the peak (related attributes: volume, volumeError, lineWidths)
    :param pointPositions: peak position in points for each dimension (related attributes: positionError, pointPositions)
    :param fitMethod: type of curve fitting
    :param lineWidths:
    :return: a new Peak instance.
    """

    apiPeakList = self._apiPeakList
    apiPeak = apiPeakList.newPeak()
    result = self._project._data2Obj.get(apiPeak)
    if result is None:
        raise RuntimeError('Unable to generate new Peak item')

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

    # apiPeak.height = apiDataSource.scale * height
    # store the unit scaled value
    apiPeak.height = height

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
