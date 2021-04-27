
"""
Alpha version of a popup for setting up a structure calculation using Xplor-NIH calculations.
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$Author: Luca Mureddu $"
__dateModified__ = "$Date: 2021-04-27 16:04:57 +0100 (Tue, April 27, 2021) $"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2021-04-27 16:04:57 +0100 (Tue, April 27, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtGui, QtWidgets
import ccpn.ui.gui.widgets.CompoundWidgets as cw
from ccpn.ui.gui.widgets.PulldownListsForObjects import PeakListPulldown, ChemicalShiftListPulldown, ChainPulldown
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.ui.gui.widgets.ListWidget import ListWidgetPair
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets import MessageDialog



class SetupXplorStructureCalculationPopup(CcpnDialogMainWidget):
    """

    """
    FIXEDWIDTH = True
    FIXEDHEIGHT = False

    title = 'Setup Xplor-NHI Structure Calculation (Alpha)'
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


        self.plsLabel = Label(self.mainWidget, text='Select PeakLists', grid=(row, 0),  vAlign='l')
        self.plsWidget = ListWidgetPair(self.mainWidget, grid=(row, 1), hAlign='l')

        row += 1
        self.cslWidget = ChemicalShiftListPulldown(parent=self.mainWidget,
                                         mainWindow=self.mainWindow,
                                         grid=(row, 0), gridSpan=(1,2),
                                         showSelectName=True,
                                         minimumWidths=(0, 100),
                                         sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                         callback=None)
        row += 1
        self.mcWidget = ChainPulldown(parent=self.mainWidget,
                                         mainWindow=self.mainWindow,
                                         grid=(row, 0), gridSpan=(1,3),
                                         showSelectName=True,
                                         minimumWidths=(0, 100),
                                         sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                         callback=None)

        self._populateWsFromProjectInfo()

    def _populateWsFromProjectInfo(self):
        if self.project:
            self.cslWidget.selectFirstItem()
            self.mcWidget.selectFirstItem()
            self.plsWidget._populate(self.plsWidget.leftList, self.project.peakLists)


    def _okCallback(self):
        if self.project:
            csl = self.cslWidget.getSelectedObject()
            chain = self.mcWidget.getSelectedObject()
            plsPids = self.plsWidget.rightList.getTexts()
            if not csl:
                MessageDialog.showWarning('', 'Select a ChemicalShift List')
                return
            if not chain:
                MessageDialog.showWarning('', 'Select a ChemicalShift List')
                return
            if not plsPids:
                MessageDialog.showWarning('', 'Include at list a PeakList')
                return
            # run the calculation
            print('Running with peakLists: %s, chain: %s, CSL: %s' %(plsPids, chain.pid, csl.pid))

        self.accept()

if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    # app = TestApplication()
    popup = SetupXplorStructureCalculationPopup(mainWindow=mainWindow)
    popup.show()
    popup.raise_()
    # app.start()