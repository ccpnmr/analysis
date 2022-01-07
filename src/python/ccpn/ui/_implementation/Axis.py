"""
GUI Axis class
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2022"
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
__dateModified__ = "$dateModified: 2022-01-07 12:25:18 +0000 (Fri, January 07, 2022) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Sequence, Tuple, Optional

from ccpn.core.NmrAtom import NmrAtom
from ccpn.core.Project import Project
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.ui._implementation.Strip import Strip
from ccpn.core.lib import Pid

from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import Axis as ApiAxis
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import StripAxis as ApiStripAxis

from ccpn.util.Constants import AXISUNITS, AXISUNIT_NUMBER


class Axis(AbstractWrapperObject):
    """Display Axis for 1D or nD spectrum"""

    #: Short class name, for PID.
    shortClassName = 'GA'
    # Attribute it necessary as subclasses must use superclass className
    className = 'Axis'

    _parentClass = Strip

    #: Name of plural link to instances of class
    _pluralLinkName = 'axes'

    #: List of child classes.
    _childClasses = []

    _isGuiClass = True

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiStripAxis._metaclass.qualifiedName()

   #-----------------------------------------------------------------------------------------

    def __init__(self, project, wrappedData):
        super().__init__(project, wrappedData)

        # additional attributes set by strip._setAxisPositionAndWidth method
        self._minLimitByType = None
        self._maxLimitByType = None
        self._incrementByType = None
        self._positionByType = None
        self._widthByType = None
        self._planeCount = None

    # @classmethod
    # def _restoreObject(cls, project, apiObj):
    #     """Subclassed to allow for initialisations on restore
    #     """
    #     result = super()._restoreObject(project, apiObj)
    #     return result

    #-----------------------------------------------------------------------------------------
    # Attributes and methods related to the data structure
    #-----------------------------------------------------------------------------------------

    @property
    def _apiStripAxis(self) -> ApiStripAxis:
        """ CCPN Axis matching Axis"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """local id, equal to Axis code"""
        return self._wrappedData.axis.code.translate(Pid.remapSeparators)

    code = _key

    @property
    def _parent(self) -> Strip:
        """Strip containing axis."""
        return self._project._data2Obj.get(self._wrappedData.strip)

    strip = _parent

    @property
    def _index(self):
        """Index of self in the parent strip.axes; i.e. defined by display order
        CCPNINTERNAL: used in GuiStrip
        """
        return list(self.strip.orderedAxes).index(self)

    #=========================================================================================
    # properties
    #=========================================================================================

    @property
    def position(self) -> float:
        """Centre point position for displayed region (in ppm)."""
        return self._wrappedData.axis.position

    @position.setter
    def position(self, value):
        self._wrappedData.axis.position = value

    @property
    def width(self) -> float:
        """Width for displayed region (in ppm)."""
        return self._wrappedData.axis.width

    @width.setter
    def width(self, value):
        self._wrappedData.axis.width = value

    @property
    def region(self) -> tuple:
        """Display region - position +/- width/2.."""
        position = self.position
        halfwidth = self.width * 0.5
        return (position - halfwidth, position + halfwidth)

    @region.setter
    def region(self, value):
        self.position = (value[0] + value[1]) * 0.5
        self.width = abs(value[1] - value[0])

    @property
    def unit(self) -> str:
        """Display unit for axis"""
        return self._wrappedData.axis.unit

    @unit.setter
    def unit(self, value: str):
        options = tuple(list(AXISUNITS) + [AXISUNIT_NUMBER]) # To allow for 1D intensity axis unit
        if value not in options:
            raise ValueError('Axis.unit: invalid value "%s", should be one of %r' %
                             (value, options)
                             )
        self._wrappedData.axis.unit = value

    @property
    def _unitIndex(self) -> int:
        """Return the index of the self.unit relative to the definitions
        CCPNINTERNAL: used in Strp, GL and elsewhere
        """
        options = list(AXISUNITS) + [AXISUNIT_NUMBER]  # To allow for 1D intensity axis unit
        return options.index(self.unit)

    @property
    def nmrAtoms(self) -> Tuple[NmrAtom]:
        """nmrAtoms connected to axis"""
        ff = self._project._data2Obj.get
        return tuple(sorted(ff(x) for x in self._wrappedData.axis.resonances))

    @nmrAtoms.setter
    def nmrAtoms(self, value):
        value = [self.getByPid(x) if isinstance(x, str) else x for x in value]
        self._wrappedData.axis.resonances = tuple(x._wrappedData for x in value)

    #=========================================================================================
    # CCPN Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Strip) -> list:
        """get wrappedData (ccpnmr.gui.Task.Axis) in serial number order"""
        apiStrip = parent._wrappedData
        dd = {x.axis.code: x for x in apiStrip.stripAxes}
        return [dd[x] for x in apiStrip.axisCodes]
        # return [dd[x] if x in dd else None for x in apiStrip.axisCodes]

    def delete(self):
        """Overrides normal delete"""
        raise ValueError("Axes cannot be deleted independently")


#=========================================================================================
# Connections to parents:
#=========================================================================================

# We should NOT have any newAxis functions

# # Strip.orderedAxes property
# def getter(self) -> Tuple[Axis, ...]:
#   apiStrip = self._wrappedData
#   ff = self._project._data2Obj.get
#   return tuple(ff(apiStrip.findFirstStripAxis(axis=x)) for x in apiStrip.orderedAxes)
# def setter(self, value:Sequence):
#   value = [self.getByPid(x) if isinstance(x, str) else x for x in value]
#   #self._wrappedData.orderedAxes = tuple(x._wrappedData.axis for x in value)
#   self._wrappedData.axisOrder = tuple(x.code for x in value)
# Strip.orderedAxes = property(getter, setter, None,
#                              "Axes in display order (X, Y, Z1, Z2, ...) ")
# del getter
# del setter

# Notifiers:
Project._apiNotifiers.append(
        ('_notifyRelatedApiObject', {'pathToObject': 'stripAxes', 'action': 'change'},
         ApiAxis._metaclass.qualifiedName(), '')
        )
