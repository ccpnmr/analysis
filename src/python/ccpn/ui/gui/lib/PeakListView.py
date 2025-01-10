"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2025"
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
__dateModified__ = "$dateModified: 2025-01-10 16:38:47 +0000 (Fri, January 10, 2025) $"
__version__ = "$Revision: 3.3.0.develop $"
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
from ccpn.ui._implementation.PeakListView import PeakListView as _PeakListViewCoreClass
from ccpn.ui._implementation.PeakListView import _newApiPeakListView
from ccpn.ui._implementation.PeakView import PeakView as _PeakViewCoreClass
from ccpn.ui.gui.guiSettings import _styleBlue

from ccpn.util.Logging import getLogger


# GWV 24/10/24: Implementation change
def _factoryFunction(project, wrappedData):
    """The factory function used to create the GUI-augmented
    PeakListView object.
    Used in core.__init__ to define the proper instantiation
    """
    return PeakListView(project=project, wrappedData=wrappedData)


class _PeakListViewGuiClass(GuiListViewABC):
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
                if _PeakViewCoreClass._newInstanceFromApiData(apiObj=apiView, project=project) is None:
                    raise RuntimeError(f'Unable to generate new {_PeakViewCoreClass.__name__}')


class PeakListView(_PeakListViewCoreClass, _PeakListViewGuiClass):
    """Peak List View for 1D or nD PeakList
    """
    def __init__(self, project: Project, wrappedData: 'ApiStripPeakListView'):
        """Init the CoreClass and Gui-part
        """
        _PeakListViewCoreClass.__init__(self, project, wrappedData)
        _PeakListViewGuiClass.__init__(self, project)
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
