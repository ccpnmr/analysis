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
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2024-10-24 15:59:02 +0100 (Thu, October 24, 2024) $"
__version__ = "$Revision: 3.2.7.GWV $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2023-05-17 11:04:29 +0100 (Wed, May 17, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.Project import Project
from ccpn.ui.gui.lib.GuiView import GuiViewABC
from ccpn.ui._implementation.PeakView import PeakView as _CoreClassPeakView

from ccpn.ui.gui.guiSettings import _styleBlue
from ccpn.util.Logging import getLogger


class GuiPeakView(GuiViewABC):
    """peakView is the CCPN wrapper object
    """
    def __init__(self):
        super().__init__()


class PeakView(_CoreClassPeakView, GuiPeakView):
    """PeakView for 1D or nD Peak.
    """

    def __init__(self, project: Project, wrappedData: 'ApiPeakView'):
        """Local override init for Qt subclass.
        """
        _CoreClassPeakView.__init__(self, project, wrappedData)
        GuiPeakView.__init__(self)
        getLogger().debug(_styleBlue(f'PeakView.__init__>> initialised {self}  {self.peak=}'))
