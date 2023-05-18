"""Integral view in a specific IntegralList View.
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
__dateModified__ = "$dateModified: 2023-05-18 18:49:15 +0100 (Thu, May 18, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import typing

from ccpn.core.Project import Project
from ccpn.core.Integral import Integral
from ccpn.core.lib.ContextManagers import ccpNmrV3CoreSetter  #, undoStackBlocking
from ccpn.util.decorators import logCommand
from ccpn.ui._implementation.IntegralListView import IntegralListView
from ccpn.ui._implementation.PMIViewABC import PMIViewABC
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import IntegralView as ApiIntegralView
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr


class IntegralView(PMIViewABC):
    """IntegralView for 1D or nD IntegralList.
    """

    #: Short class name, for PID.
    shortClassName = 'GN'
    # Attribute it necessary as subclasses must use superclass className
    className = 'IntegralView'

    _parentClass = IntegralListView
    _parentClassName = IntegralListView.__class__.__name__

    #: Name of plural link to instances of class
    _pluralLinkName = 'integralViews'

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiIntegralView._metaclass.qualifiedName()

    #=========================================================================================
    # CCPN properties
    #=========================================================================================

    @property
    def _apiIntegralView(self) -> ApiIntegralView:
        """CCPN IntegralView matching IntegralView"""
        return self._wrappedData

    @property
    def _parent(self) -> IntegralListView:
        """IntegralListView containing IntegralView."""
        return self._project._data2Obj.get(self._wrappedData.integralListView.sortedStripIntegralListViews()[0])

    integralListView = _parent

    @property
    def _key(self) -> str:
        """id string - """
        return str(self._wrappedData.integral.serial)

    @property
    def _localCcpnSortKey(self) -> typing.Tuple:
        """Local sorting key, in context of parent."""
        return (self._wrappedData.integral.serial,)

    @property
    def integral(self) -> Integral:
        """Integral that IntegralView refers to.
        """
        return self._project._data2Obj.get(self._wrappedData.integral)

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: IntegralListView) -> list:
        """get wrappedData (ccpnmr.gui.Task.IntegralView) in serial number order.
        """
        return parent._wrappedData.integralListView.sortedIntegralViews()

    def _finaliseAction(self, action: str, **actionKwds):
        if super()._finaliseAction(action, **actionKwds):

            if action == 'change':
                self.integral._finaliseAction(action)

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    # None


# Integral.integralViews property
def getter(integral: Integral) -> typing.Tuple[IntegralView, ...]:
    """IntegralViews associated with Integral.
    """
    return tuple(integral._project._data2Obj[x] for x in integral._wrappedData.sortedIntegralViews())


Integral.integralViews = property(getter, None, None, 'IntegralViews associated with Integral.')

del getter


def getTextOffset(self: Integral, integralListView: IntegralListView) -> tuple:
    """Get textOffset for the integral for the specified integralListView in ppm.
    """
    if view := self._wrappedData.findFirstIntegralView(integralListView=integralListView._wrappedData.integralListView):
        # bypass the v3-operator in superclass
        tOffset = view.textOffset
        if any(tOffset):
            return view.textOffset


Integral.getTextOffset = getTextOffset

del getTextOffset


def getIntegralView(self: Integral, integralListView: IntegralListView) -> tuple:
    """Get integralView for the integral for the specified integralListView.
    """
    if view := self._wrappedData.findFirstIntegralView(integralListView=integralListView._wrappedData.integralListView):
        return self.project._data2Obj.get(view)


Integral.getIntegralView = getIntegralView

del getIntegralView


def _integralAddIntegralViews(project: Project, apiIntegral: Nmr.Integral):
    """Add ApiIntegralViews when ApiIntegral is created.
    """
    if project._apiNotificationBlanking == 0:
        # create new apiObjects if not blocked
        for apiIntegralListView in apiIntegral.parent.integralListViews:
            apiIntegralListView.newIntegralView(integral=apiIntegral, integralSerial=0)


Project._setupApiNotifier(_integralAddIntegralViews, Nmr.Integral, 'postInit')
