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
__author__ = "$Author: Wayne Boucher $"
__date__ = "$Date: 2017-03-22 15:13:45 +0000 (Wed, March 22, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.Project import Project
from ccpn.ui.gui.lib.GuiListView import GuiListViewABC
from ccpn.ui._implementation.PeakListView import PeakListView as _CoreClassPeakListView


class GuiPeakListView(GuiListViewABC):
    """peakList is the CCPN wrapper object
    """

    def __init__(self):
        super().__init__()

        vPeaks = {view.peak for view in self._wrappedData.peakListView.peakViews}
        # create peakViews that don't already exist for all peaks in peakList
        for obj in self.peakList.peaks:
            apiPeak = obj._wrappedData
            if apiPeak not in vPeaks:
                self._wrappedData.peakListView.newPeakView(peak=apiPeak, peakSerial=0)


class PeakListView(_CoreClassPeakListView, GuiPeakListView):
    """Peak List View for 1D or nD PeakList"""

    def __init__(self, project: Project, wrappedData: 'ApiStripPeakListView'):
        """Local override init for Qt subclass"""
        _CoreClassPeakListView.__init__(self, project, wrappedData)

        # hack for now
        self.application = project.application
        self._init()

        GuiPeakListView.__init__(self)
