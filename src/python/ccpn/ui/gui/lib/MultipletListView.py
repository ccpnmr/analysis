"""
Module Documentation here
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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2024-09-20 15:02:11 +0100 (Fri, September 20, 2024) $"
__version__ = "$Revision: 3.2.7 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2018-12-20 15:44:34 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.Project import Project
from ccpn.ui.gui.lib.GuiListView import GuiListViewABC
from ccpn.ui._implementation.MultipletListView import MultipletListView as _CoreClassListView
from ccpn.ui._implementation.MultipletView import MultipletView as KlassView


class GuiMultipletListView(GuiListViewABC):
    """multipletList is the CCPN wrapper object
    """

    def __init__(self, project: Project):
        super().__init__()

        lView = self._wrappedData.multipletListView
        factoryFunc = lView.newMultipletView
        vObjs = {view.multiplet for view in lView.multipletViews}
        # create multipletViews that don't already exist for all multiplets in multipletList
        for apiObj in lView.multipletList.multiplets:
            if apiObj not in vObjs:
                apiView = factoryFunc(multiplet=apiObj, multipletSerial=0)
                if KlassView._newInstanceFromApiData(apiObj=apiView, project=project) is None:
                    raise RuntimeError(f'Unable to generate new {KlassView.__name__}')


class MultipletListView(_CoreClassListView, GuiMultipletListView):
    """Multiplet List View for 1D or nD MultipletList"""

    def __init__(self, project: Project, wrappedData: 'ApiStripMultipletListView'):
        """Local override init for Qt subclass"""
        _CoreClassListView.__init__(self, project, wrappedData)

        # hack for now
        self.application = project.application
        self._init()

        GuiMultipletListView.__init__(self, project)
