"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import List, Tuple, Optional
from ccpn.util.Logging import getLogger
from ccpn.core.Spectrum import Spectrum
from ccpn.core.Peak import Peak
from ccpn.core.Project import Project
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.ListWidget import ListWidget
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.widgets.PulldownListsForObjects import SpectrumPulldown
from ccpn.util.Common import makeIterableList
from ccpn.core.lib.peakUtils import estimateVolumes
from ccpn.core.lib.ContextManagers import undoBlock


class EstimateVolumes(CcpnDialog):

    def __init__(self, parent=None, mainWindow=None, title='Estimate Volumes', **kwds):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        if mainWindow:
            self.mainWindow = mainWindow
            self.application = mainWindow.application
            self.current = self.application.current
            self.project = mainWindow.project
        else:
            self.mainWindow = None
            self.application = None
            self.current = None
            self.project = None

        self._createWidgets()
        self._changePeakLists()
        self.setFixedSize(self.sizeHint())

    def _createWidgets(self):

        row = 0
        self.spectrumPullDown = SpectrumPulldown(self, self.project, grid=(row, 0), gridSpan=(1, 3), callback=self._changePeakLists)

        row += 1
        self._label = Label(self, grid=(row, 0), gridSpan=(1, 3), text='Select peakLists from the table')

        row += 1
        self.peakListWidget = ListWidget(self, multiSelect=True, callback=self._selectPeakLists, tipText='Select PeakLists',
                                         grid=(row, 0), gridSpan=(1, 3))

        row += 1
        self.buttonBox = ButtonList(self, grid=(row, 1), gridSpan=(1, 2), texts=['Close', 'Estimate Volumes'],
                                    callbacks=[self.reject, self._estimateVolumes])

    def _changePeakLists(self, *args):
        obj = self.spectrumPullDown.getSelectedObject()

        if isinstance(obj, Spectrum):
            self.peakListWidget.setObjects(obj.peakLists, name='pid')

    def _selectPeakLists(self, *args):
        pass

    def _estimateVolumes(self):
        """Estimate the volumes for the peaks in the peakLists highlighted in the listWidget
        """
        peakLists = self.peakListWidget.getSelectedObjects()
        peaks = [peak for peakList in peakLists for peak in peakList.peaks]

        # estimate the volumes for the list
        with undoBlock():
            estimateVolumes(peaks)

        self.accept()