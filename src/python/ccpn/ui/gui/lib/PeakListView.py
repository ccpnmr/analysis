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
__dateModified__ = "$dateModified: 2024-10-24 17:29:34 +0100 (Thu, October 24, 2024) $"
__version__ = "$Revision: 3.2.7.GWV $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Wayne Boucher $"
__date__ = "$Date: 2017-03-22 15:13:45 +0000 (Wed, March 22, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.Project import Project
from ccpn.core.PeakList import PeakList

from ccpn.ui.gui.lib.GuiListView import GuiListViewABC
from ccpn.ui._implementation.PeakListView import PeakListView as _CoreClassPeakListView
from ccpn.ui._implementation.PeakListView import _newApiPeakListView
from ccpn.ui._implementation.PeakView import PeakView as KlassView
from ccpn.ui.gui.guiSettings import _styleBlue

from ccpn.util.Logging import getLogger


class GuiPeakListView(GuiListViewABC):
    """peakList is the CCPN wrapper object
    """
    def __init__(self, project: Project):
        super().__init__()

        lView = self._wrappedData.peakListView
        factoryFunc = lView.newPeakView
        vObjs = {view.peak for view in lView.peakViews}
        # create peakViews that don't already exist for all peaks in peakList
        for apiObj in lView.peakList.peaks:
            if apiObj not in vObjs:
                apiView = factoryFunc(peak=apiObj, peakSerial=0)
                if KlassView._newInstanceFromApiData(apiObj=apiView, project=project) is None:
                    raise RuntimeError(f'Unable to generate new {KlassView.__name__}')


class PeakListView(_CoreClassPeakListView, GuiPeakListView):
    """Peak List View for 1D or nD PeakList
    """
    def __init__(self, project: Project, wrappedData: 'ApiStripPeakListView'):
        """Init the CoreClass and Gui-part
        """
        _CoreClassPeakListView.__init__(self, project, wrappedData)
        GuiPeakListView.__init__(self, project)

        getLogger().debug(_styleBlue(f'PeakListView.__init__>> initialised {self}  {self.peakList=}'))


def _newPeakListView(spectrumView, peakList: PeakList) -> PeakListView:
    """Create a new PeakListView object
    :param spectrumView: the (parent) SpectrumView object
    :param peakList: the corresponding PeakList object
    :return PeakListView instance
    """
    apiPeakListView = _newApiPeakListView(spectrumView=spectrumView, peakList=peakList)
    if (result := PeakListView._newInstanceFromApiData(apiObj=apiPeakListView, project=peakList.project)) is None:
        raise RuntimeError('Failed to generate new PeakListView instance')
    return result
