"""
Module Documentation here
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
__dateModified__ = "$dateModified: 2023-05-11 19:16:27 +0100 (Thu, May 11, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2018-12-20 15:44:34 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.lib.GuiListView import GuiListViewABC
from ccpn.core.Project import Project
from ccpn.ui._implementation.MultipletListView import MultipletListView as _CoreClassMultipletListView


class GuiMultipletListView(GuiListViewABC):
    """multipletList is the CCPN wrapper object
    """

    def __init__(self):
        super().__init__()

        vMultiplets = {view.multiplet for view in self._wrappedData.multipletListView.multipletViews}
        # create multipletViews that don't already exist for all multiplets in multipletList
        for obj in self.multipletList.multiplets:
            apiMultiplet = obj._wrappedData
            if apiMultiplet not in vMultiplets:
                self._wrappedData.multipletListView.newMultipletView(multiplet=apiMultiplet, multipletSerial=0)


class MultipletListView(_CoreClassMultipletListView, GuiMultipletListView):
    """Multiplet List View for 1D or nD MultipletList
    """

    def __init__(self, project: Project, wrappedData: 'ApiStripMultipletListView'):
        """Local override init for Qt subclass"""
        _CoreClassMultipletListView.__init__(self, project, wrappedData)

        # hack for now
        self.application = project.application
        self._init()

        GuiMultipletListView.__init__(self)
