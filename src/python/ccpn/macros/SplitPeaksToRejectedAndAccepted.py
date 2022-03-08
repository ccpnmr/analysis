
"""
Alpha version of a popup for setting up a structure calculation using Xplor-NIH calculations.
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$Author: Eliza $"
__dateModified__ = "$Date: 2021-04-27 16:04:57 +0100 (Tue, April 27, 2021) $"
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2022-03-08 22:20:58 +0000 (Tue, March 08, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2021-04-27 16:04:57 +0100 (Tue, April 27, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtGui, QtWidgets

from ccpn.ui.gui.widgets.PulldownListsForObjects import PeakListPulldown, ChemicalShiftListPulldown, ChainPulldown
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.ui.gui.widgets.ListWidget import ListWidgetPair
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets import MessageDialog

from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar, notificationEchoBlocking, \
    catchExceptions
from ccpn.util.Logging import getLogger


def splitRejectedAccept(peakList):
    """Move rejected peaks, i.e. those without a retraint, to a new peakList
    :return the new PeakList instance
    """

    red = '#FF0000'

    getLogger().info(f'{peakList}: {len(peakList.peaks)}')

    acceptedPeaks = [pk for restraint in peakList.project.restraints for pk in restraint.peaks
                     if pk.peakList == peakList]
    getLogger().info(f'acceptedPeaks: {len(acceptedPeaks)}')

    rejectedPeaks = [pk for pk in peakList.peaks if pk not in acceptedPeaks]
    getLogger().info(f'rejectedPeaks: {len(rejectedPeaks)}')

    with undoBlockWithoutSideBar():
        with notificationEchoBlocking():

            newPl = peakList.spectrum.newPeakList(comment = 'Rejected Peaks',
                                                  textColour = red,
                                                  symbolColour = red)
            for pk in rejectedPeaks:
                pk.copyTo(newPl)
                pk.delete()

    return newPl


class SetupSplitPeakListPopup(CcpnDialogMainWidget):
    """

    """
    FIXEDWIDTH = True
    FIXEDHEIGHT = False

    title = 'Split PeakList to Accepted and Rejected Peaks (Alpha)'
    def __init__(self, parent=None, mainWindow=None, title=title,  **kwds):
        super().__init__(parent, setLayout=True, windowTitle=title,
                         size=(500, 10), minimumSize=None, **kwds)

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

        # enable the buttons
        self.tipText = ''
        self.setOkButton(callback=self._okCallback, tipText =self.tipText, text='Setup', enabled=True)
        self.setCloseButton(callback=self.reject, tipText='Close')
        self.setDefaultButton(CcpnDialogMainWidget.CLOSEBUTTON)
        self.__postInit__()
        self._okButton = self.dialogButtons.button(self.OKBUTTON)

    def _createWidgets(self):

        row = 0
        self.pkWidget = PeakListPulldown(parent=self.mainWidget,
                                                  mainWindow=self.mainWindow,
                                                  grid=(row, 0), gridSpan=(1,2),
                                                  showSelectName=True,
                                                  minimumWidths=(0, 100),
                                                  sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                                  callback=None)

        self._populateWsFromProjectInfo()

    def _populateWsFromProjectInfo(self):
        if self.project:
            self.pkWidget.selectFirstItem()


    def _okCallback(self):
        if self.project:
            peakList = self.pkWidget.getSelectedObject()

            if not peakList:
                MessageDialog.showWarning('', 'Select a PeakList List')
                return

            # run the splitting
            with catchExceptions(errorStringTemplate='Split PeakList\n%s'):
                with MessageDialog.progressManager(parent=self,
                                                   title=f'Splitting PeakList {peakList}'):
                    newPeakList = splitRejectedAccept(peakList)

            if len(newPeakList.peaks) > 0:
                MessageDialog.showInfo('Split PeakList', f'Created {newPeakList} with {len(newPeakList.peaks)} rejected peaks')

        self.accept()

if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    # app = TestApplication()
    popup = SetupSplitPeakListPopup(mainWindow=mainWindow)
    popup.show()
    popup.raise_()
    # app.start()

