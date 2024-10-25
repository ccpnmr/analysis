"""
Get the regions between two peak Limits and fill the area under the curve.

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2024-10-25 11:34:14 +0100 (Fri, October 25, 2024) $"
__version__ = "$Revision: 3.2.7.GWV $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.Project import Project
from ccpn.ui.gui.lib.GuiListView import GuiListViewABC
from ccpn.ui._implementation.IntegralListView import IntegralListView as _IntegralListViewCoreClass
from ccpn.ui._implementation.IntegralView import IntegralView as KlassView

from ccpn.ui.gui.guiSettings import _styleBlue
from ccpn.util.Logging import getLogger


# GWV 24/10/24: Implementation change
def _factoryFunction(project, wrappedData):
    """The factory function used to create the GUI-augmented
    IntegralListView object.
    Used in core.__init__ to define the proper instantiation
    """
    return IntegralListView(project=project, wrappedData=wrappedData)


class _IntegralListViewGuiClass(GuiListViewABC):
    """integralList is the CCPN wrapper object
    """

    def __init__(self, project: Project):
        super().__init__()

        lView = self._wrappedData.integralListView
        factoryFunc = lView.newIntegralView
        vObjs = {view.integral for view in lView.integralViews}
        # create integralViews that don't already exist for all integrals in integralList
        for apiObj in lView.integralList.integrals:
            if apiObj not in vObjs:
                apiView = factoryFunc(integral=apiObj, integralSerial=0)
                if KlassView._newInstanceFromApiData(apiObj=apiView, project=project) is None:
                    raise RuntimeError(f'Unable to generate new {KlassView.__name__}')


class IntegralListView(_IntegralListViewCoreClass, _IntegralListViewGuiClass):
    """Core data part and Gui Integral List View for 1D or nD IntegralList
    """

    def __init__(self, project: Project, wrappedData: 'ApiStripIntegralListView'):
        """Local override init for Qt subclass
        """
        _IntegralListViewCoreClass.__init__(self, project, wrappedData)
        _IntegralListViewGuiClass.__init__(self, project)
        getLogger().debug(_styleBlue(f'IntegralListView.__init__>> initialised {self}  {self.integralList=}'))
