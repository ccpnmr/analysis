"""
This file contains the SpectrumView classes (1D and nD versions)
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
__dateModified__ = "$dateModified: 2024-10-25 11:08:17 +0100 (Fri, October 25, 2024) $"
__version__ = "$Revision: 3.2.7.GWV $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2023-01-24 10:28:48 +0000 (Tue, January 24, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui._implementation.SpectrumView import SpectrumView as _SpectrumViewCoreClass
from ccpn.ui.gui.lib.GuiSpectrumView1d import GuiSpectrumView1d as _GuiSpectrumView1d
from ccpn.ui.gui.lib.GuiSpectrumViewNd import GuiSpectrumViewNd as _GuiSpectrumViewNd
from ccpn.ui.gui.guiSettings import _styleBlue

from ccpn.core.Project import Project
from ccpn.core.lib.Notifiers import NotifierABC
from ccpn.util.Logging import getLogger


# GWV 24/10/24: Implementation change
def _factoryFunction(project, wrappedData):
    """The factory function used to create 1d or nD versions of the
    SpectrumView object.
    Used in core.__init__ to define the proper instantiation
    """
    klass = SpectrumView1d if (wrappedData.strip.spectrumDisplay.is1d) else SpectrumViewNd
    return klass(project=project, wrappedData=wrappedData)


# class SpectrumView(_CoreClassSpectrumView):
#
    # GWV reverting
    #     # Set notifiers to create/delete peakList  --> affects PeakListView children
    #     self.setNotifier(self.spectrum,
    #                      triggers=[NotifierABC.CREATE, NotifierABC.DELETE],
    #                      targetName=PeakList.className,
    #                      callback=self._peakListCallback
    #                      )
    #
    # def _peakListCallback(self, callbackDict):
    #     """Callback when peakList is created or deleted
    #     """
    #     from ccpn.ui.gui.lib.PeakListView import _newPeakListView
    #
    #     _trigger = callbackDict.get(NotifierABC.TRIGGER)
    #     _obj = callbackDict.get(NotifierABC.OBJECT)
    #
    #     if _trigger == NotifierABC.CREATE:
    #         _newPeakListView(spectrumView=self, peakList=_obj)
    #
    #     elif _trigger == NotifierABC.DELETE:
    #         pass
    #
    #     else:
    #         raise RuntimeError(f'SpectrumView._peakListCallback(): invalid {_trigger=}')


class SpectrumView1d(_SpectrumViewCoreClass, _GuiSpectrumView1d):
    """Class combining core-class data and 1D Gui Spectrum View
    """

    def __init__(self, project: Project, wrappedData: 'ApiStripSpectrumView'):
        _SpectrumViewCoreClass.__init__(self, project, wrappedData)
        _GuiSpectrumView1d.__init__(self)
        getLogger().debug(_styleBlue(f'SpectrumView1d.__init__>> {self=}, {self.strip=}'))


class SpectrumViewNd(_SpectrumViewCoreClass, _GuiSpectrumViewNd):
    """Class combining core-class data and nD Gui Spectrum View
    """
    def __init__(self, project: Project, wrappedData: 'ApiStripSpectrumView'):
        _SpectrumViewCoreClass.__init__(self, project, wrappedData)
        _GuiSpectrumViewNd.__init__(self)
        getLogger().debug(_styleBlue(f'SpectrumViewNd.__init__>> {self=} {self.strip=}'))
