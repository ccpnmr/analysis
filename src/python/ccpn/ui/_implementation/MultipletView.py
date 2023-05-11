"""Multiplet view in a specific MultipletList View.
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
__dateModified__ = "$dateModified: 2023-05-11 19:16:26 +0100 (Thu, May 11, 2023) $"
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
from ccpn.core.Multiplet import Multiplet
from ccpn.ui._implementation.MultipletListView import MultipletListView
from ccpn.ui._implementation.PMIViewABC import PMIViewABC
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import MultipletView as ApiMultipletView
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr


class MultipletView(PMIViewABC):
    """MultipletView for 1D or nD MultipletList.
    """

    #: Short class name, for PID.
    shortClassName = 'GE'
    # Attribute it necessary as subclasses must use superclass className
    className = 'MultipletView'

    _parentClass = MultipletListView
    _parentClassName = MultipletListView.__class__.__name__

    #: Name of plural link to instances of class
    _pluralLinkName = 'multipletViews'

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiMultipletView._metaclass.qualifiedName()

    #=========================================================================================
    # CCPN properties
    #=========================================================================================

    @property
    def _apiMultipletView(self) -> ApiMultipletView:
        """CCPN MultipletView matching MultipletView"""
        return self._wrappedData

    @property
    def _parent(self) -> MultipletListView:
        """MultipletListView containing MultipletView."""
        return self._project._data2Obj.get(self._wrappedData.multipletListView.sortedStripMultipletListViews()[0])

    multipletListView = _parent

    @property
    def _key(self) -> str:
        """id string - """
        return str(self._wrappedData.multiplet.serial)

    @property
    def _localCcpnSortKey(self) -> typing.Tuple:
        """Local sorting key, in context of parent."""
        return (self._wrappedData.multiplet.serial,)

    @property
    def multiplet(self) -> Multiplet:
        """Multiplet that MultipletView refers to"""
        return self._project._data2Obj.get(self._wrappedData.multiplet)

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: MultipletListView) -> list:
        """get wrappedData (ccpnmr.gui.Task.MultipletView) in serial number order.
        """
        return parent._wrappedData.multipletListView.sortedMultipletViews()

    def _finaliseAction(self, action: str, **actionKwds):
        if super()._finaliseAction(action, **actionKwds):

            if action == 'change':
                self.multiplet._finaliseAction(action)

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    # None


# Multiplet.multipletViews property
def getter(multiplet: Multiplet) -> typing.Tuple[MultipletView, ...]:
    """MultipletViews associated with Multiplet.
    """
    return tuple(multiplet._project._data2Obj[x] for x in multiplet._wrappedData.sortedMultipletViews())


Multiplet.multipletViews = property(getter, None, None, 'MultipletViews associated with Multiplet.')

del getter


def getTextOffset(self: Multiplet, multipletListView: MultipletListView) -> tuple:
    """Get textOffset for the multiplet for the specified multipletListView
    """
    if view := self._wrappedData.findFirstMultipletView(multipletListView=multipletListView._wrappedData.multipletListView):
        tOffset = view.textOffset
        if any(val for val in tOffset):
            return view.textOffset


Multiplet.getTextOffset = getTextOffset

del getTextOffset


def _multipletAddMultipletViews(project: Project, apiMultiplet: Nmr.Multiplet):
    """Add ApiMultipletViews when ApiMultiplet is created.
    """
    if project._apiNotificationBlanking == 0:
        # create new apiObjects if not blocked
        for apiMultipletListView in apiMultiplet.parent.multipletListViews:
            apiMultipletListView.newMultipletView(multiplet=apiMultiplet, multipletSerial=0)


Project._setupApiNotifier(_multipletAddMultipletViews, Nmr.Multiplet, 'postInit')
