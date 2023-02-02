"""
Get the regions between two peak Limits and fill the area under the curve.

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
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2023-02-02 13:48:27 +0000 (Thu, February 02, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.lib.GuiListView import GuiListViewABC
from ccpn.core.Project import Project
from ccpn.ui._implementation.IntegralListView import IntegralListView as _CoreClassIntegralListView


class GuiIntegralListView(GuiListViewABC):
    """integralList is the CCPN wrapper object
    """

    def __init__(self):
        super().__init__()


class IntegralListView(_CoreClassIntegralListView, GuiIntegralListView):
    """Integral List View for 1D or nD IntegralList"""

    def __init__(self, project: Project, wrappedData: 'ApiStripIntegralListView'):
        """Local override init for Qt subclass"""
        _CoreClassIntegralListView.__init__(self, project, wrappedData)

        # hack for now
        self.application = project.application
        GuiIntegralListView.__init__(self)
        self._init()

# #=========================================================================================
# # Registering
# #=========================================================================================
#
# def _factoryFunction(project: Project, wrappedData):
#     """create IntegralListView
#     """
#     return IntegralListView(project, wrappedData)
#
# # _CoreClassIntegralListView._registerCoreClass(factoryFunction=_factoryFunction)
