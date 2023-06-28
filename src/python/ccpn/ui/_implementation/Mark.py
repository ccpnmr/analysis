"""Mark class

After creation, there are no attributes that can be modified; i.e. the Mark object is inmutable

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2023-06-28 14:29:32 +0100 (Wed, June 28, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import collections
from typing import Sequence, Tuple, Union
from itertools import zip_longest

from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import Mark as ApiMark
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib.ContextManagers import newObject
from ccpn.core.Project import Project
from ccpn.ui._implementation.SpectrumDisplay import SpectrumDisplay
from ccpn.ui._implementation.Window import Window


RulerData = collections.namedtuple('RulerData', ['position', 'axisCode', 'unit', 'label'])
MARKTOLERANCE = 1e-5


class Mark(AbstractWrapperObject):
    """GUI Mark, a set of axiscode,position rulers or lines"""

    #: Short class name, for PID.
    shortClassName = 'GM'
    # Attribute it necessary as subclasses must use superclass className
    className = 'Mark'

    # attach to project but keep the access through mainWindow/spectrumDisplays
    _parentClass = Project
    _parentClassName = Project.__class__.__name__

    #: Name of plural link to instances of class
    _pluralLinkName = 'marks'

    #: List of child classes.
    _childClasses = []

    _isGuiClass = True

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiMark._metaclass.qualifiedName()

    # CCPN properties
    @property
    def _apiMark(self) -> ApiMark:
        """ CCPN Mark matching Mark"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """id string - serial number converted to string"""
        return str(self._wrappedData.serial)

    @property
    def serial(self) -> int:
        """serial number of Mark, used in Pid and to identify the Mark. """
        return self._wrappedData.serial

    @property
    def _parent(self) -> Project:
        """Task containing Mark."""
        return self._project._data2Obj[self._wrappedData.guiTask.nmrProject]

    project = _parent

    @property
    def colour(self) -> str:
        """Mark colour"""
        return self._wrappedData.colour

    #GWV 20181127: deactivated all the setters
    @colour.setter
    def colour(self, value: Sequence):
        self._wrappedData.colour = value

    @property
    def style(self) -> str:
        """Mark drawing style. Defaults to 'simple'"""
        return self._wrappedData.style

    # @style.setter
    # def style(self, value: str):
    #     self._wrappedData.style = value

    @property
    def positions(self) -> Tuple[float, ...]:
        """Mark position in  float ppm (or other relevant unit) for each ruler making up the mark."""
        return tuple(x.position for x in self._wrappedData.sortedRulers())

    # @positions.setter
    # def positions(self, value: Sequence):
    #     for ii, ruler in enumerate(self._wrappedData.sortedRulers()):
    #         ruler.position = value[ii]

    @property
    def axisCodes(self) -> Tuple[str, ...]:
        """AxisCode (string) for each ruler making up the mark."""
        return tuple(x.axisCode for x in self._wrappedData.sortedRulers())

    # @axisCodes.setter
    # def axisCodes(self, value: Sequence):
    #     for ii, ruler in enumerate(self._wrappedData.sortedRulers()):
    #         ruler.axisCode = value[ii]

    @property
    def units(self) -> Tuple[str, ...]:
        """Unit (string, default is ppm) for each ruler making up the mark."""
        return tuple(x.unit for x in self._wrappedData.sortedRulers())

    # @units.setter
    # def units(self, value: Sequence):
    #     for ii, ruler in enumerate(self._wrappedData.sortedRulers()):
    #         ruler.unit = value[ii]

    @property
    def labels(self) -> Tuple[str, ...]:
        """Optional label (string) for each ruler making up the mark."""
        return tuple(x.label for x in self._wrappedData.sortedRulers())

    # @labels.setter
    # def labels(self, value: Sequence):
    #     for ii, ruler in enumerate(self._wrappedData.sortedRulers()):
    #         ruler.label = value[ii]

    @property
    def rulerData(self) -> tuple:
        """tuple of RulerData ('position', 'axisCode', 'unit', 'label') for the lines in the Mark"""
        return tuple(RulerData(*(getattr(x, tag) for tag in RulerData._fields))
                     for x in self._wrappedData.sortedRulers())

    # GWV 20181127: Not used
    # @logCommand(get='self')
    # def newLine(self, position: float, axisCode: str, unit: str = 'ppm', label: str = None):
    #     """Add an extra line to the mark."""
    #     if unit is None:
    #         raise ValueError('Mark.newLine: unit is None')
    #     self._wrappedData.newRuler(position=position, axisCode=axisCode, unit=unit, label=label)

    @property
    def strips(self) -> tuple:
        """Return the associated strips for the mark.
        """
        # NOTE:ED - these could be place-holders that are generated by the cross-referencing handler
        try:
            refHandler = self._project._crossReferencing
            return refHandler.getValues(self, '_MarkStrip', 0)  # index of 0 for marks

        except Exception:
            return ()

    @strips.setter
    def strips(self, values):
        """Set the associated strips for the mark.
        """
        if not isinstance(values, (tuple, list, type(None))):
            raise TypeError(f'{self.__class__.__name__}.strips must be a list or tuple, or None')
        values = values or []

        try:
            refHandler = self._project._crossReferencing
            refHandler.setValues(self, '_MarkStrip', 0, values)

        except Exception as es:
            raise RuntimeError(f'{self.__class__.__name__}.strips: Error setting strips {es}') from es

    @property
    def spectrumDisplays(self) -> tuple:
        """Return the associated spectrumDisplays for the mark.
        """
        # NOTE:ED - these could be place-holders that are generated by the cross-referencing handler
        try:
            refHandler = self._project._crossReferencing
            return refHandler.getValues(self, '_MarkSpectrumDisplay', 0)  # index of 0 for marks

        except Exception:
            return ()

    @spectrumDisplays.setter
    def spectrumDisplays(self, values):
        """Set the associated spectrumDisplays for the mark.
        """
        if not isinstance(values, (tuple, list, type(None))):
            raise TypeError(f'{self.__class__.__name__}.spectrumDisplays must be a list or tuple, or None')
        values = values or []

        try:
            refHandler = self._project._crossReferencing
            refHandler.setValues(self, '_MarkSpectrumDisplay', 0, values)

        except Exception as es:
            raise RuntimeError(f'{self.__class__.__name__}.spectrumDisplays: Error setting spectrumDisplays {es}') from es

    @property
    def windows(self) -> tuple:
        """Return the associated windows for the mark.
        """
        try:
            refHandler = self._project._crossReferencing
            return refHandler.getValues(self, '_MarkWindow', 0)  # index of 0 for marks

        except Exception:
            return ()

    @windows.setter
    def windows(self, values):
        """Set the associated windows for the mark.
        """
        if not isinstance(values, (tuple, list, type(None))):
            raise TypeError(f'{self.__class__.__name__}.windows must be a list or tuple, or None')
        values = values or []

        try:
            refHandler = self._project._crossReferencing
            refHandler.setValues(self, '_MarkWindow', 0, values)

        except Exception as es:
            raise RuntimeError(f'{self.__class__.__name__}.windows: Error setting windows {es}') from es

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Window) -> list:
        """get wrappedData (ccp.gui.windows) for all Window children of parent NmrProject.windowStore
        """
        # hike from mainWindow to project to find GuiTasks
        apiGuiTask = (parent.project._wrappedData.findFirstGuiTask(nameSpace='user', name='View') or
                      parent.project._wrappedData.root.newGuiTask(nameSpace='user', name='View'))
        return apiGuiTask.sortedMarks()

    def __str__(self):
        if self.isDeleted:
            return super().__str__()

        ll = min(len(self.positions), len(self.axisCodes))

        def roundedValue(value):
            return float('%.2f' % value)

        pstring = str(tuple((self.axisCodes[i], roundedValue(self.positions[i]))
                            for i in range(ll)))

        return f'<{self.shortClassName}:{self.serial} {pstring[1:-1]}>'

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    #===========================================================================================
    # new<Object> and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================


#=========================================================================================
# Connections to parents:
#=========================================================================================

def _removeMarkAxes(parent: Union[Window, 'SpectrumDisplay', 'Strip'],
                    positions: Sequence[float],
                    axisCodes: Sequence[str],
                    labels: Sequence[str] = ()) -> Tuple[Tuple, ...]:
    """Remove existing Mark rulers based on position, axisCode and label.

    :param tuple/list positions: Position in unit (default ppm) of all lines in the mark
    :param tuple/list axisCodes: Axis codes for all lines in the mark
    :param tuple/list labels: Ruler labels for all lines in the mark. Default: None
    :return: tuple of tuples: remaining (positions, axisCodes, labels) that do not currently exist in any mark.
    """
    markList = list(zip_longest(positions, axisCodes, labels))
    if not markList:
        raise TypeError(f'_removeMarkAxes: badly defined parameters {positions}; {axisCodes}; {labels}')

    indices = list(axisCodes)
    for pos, axis, label in markList:
        for mark in parent.marks:
            for mPos, mAxis, mLabel in zip_longest(mark.positions, mark.axisCodes, mark.labels):
                try:
                    posClose = (-MARKTOLERANCE < (mPos - pos) < MARKTOLERANCE)
                    if mAxis == axis and mLabel == label and posClose and axis in indices:
                        # remove this axis from the list
                        indices.remove(axis)
                        ...
                except Exception as es:
                    # mark may not be defined correctly.
                    continue

    return tuple(tuple(mark[ind] for mark in markList if mark[1] in indices) for ind in range(3) if indices)


#=========================================================================================
# Registering
#=========================================================================================
# Mark._registerCoreClass()

#=========================================================================================
# newMark
#=========================================================================================

@newObject(Mark)
def _newMark(self: Window, colour: str, positions: Sequence[float], axisCodes: Sequence,
             style: str = 'simple', units: Sequence[str] = (), labels: Sequence[str] = (),
             ) -> Mark:
    """Create new Mark.

    :param str colour: Mark colour.
    :param tuple/list positions: Position in unit (default ppm) of all lines in the mark.
    :param tuple/list axisCodes: Axis codes for all lines in the mark.
    :param str style: Mark drawing style (dashed line etc.) default: full line ('simple').
    :param tuple/list units: Axis units for all lines in the mark, Default: all ppm.
    :param tuple/list labels: Ruler labels for all lines in the mark. Default: None.
    :return: a new Mark instance.
    """
    project = self.project

    apiGuiTask = (project._wrappedData.findFirstGuiTask(nameSpace='user', name='View') or
                  project._wrappedData.root.newGuiTask(nameSpace='user', name='View'))
    apiMark = apiGuiTask.newMark(colour=colour, style=style)

    for ii, position in enumerate(positions):
        dd = {'position': position, 'axisCode': axisCodes[ii]}
        if units:
            unit = units[ii]
            if unit is not None:
                dd['unit'] = unit
        if labels:
            label = labels[ii]
            if label is not None:
                dd['label'] = label
        _apiRuler = apiMark.newRuler(**dd)

    result = project._data2Obj.get(apiMark)
    if result is None:
        raise RuntimeError('Unable to generate new Mark item')

    return result

    # strips must be added after this catch the create/delete notifier

# Notifiers:
# Mark changes when rulers are created or deleted
# Project._apiNotifiers.extend(
#         (('_notifyRelatedApiObject', {'pathToObject': 'mark', 'action': 'change'},
#           ApiRuler._metaclass.qualifiedName(), 'postInit'),
#          ('_notifyRelatedApiObject', {'pathToObject': 'mark', 'action': 'change'},
#           ApiRuler._metaclass.qualifiedName(), 'preDelete'),
#          )
#         )
