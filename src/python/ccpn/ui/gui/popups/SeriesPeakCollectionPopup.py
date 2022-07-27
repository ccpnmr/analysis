"""
Create Collections of peaks from a SpectrumGroup Series.
Used for ExperimentAnalysis
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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-07-27 10:25:00 +0100 (Wed, July 27, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from collections import OrderedDict as od
from functools import partial
from PyQt5 import QtCore, QtGui, QtWidgets
from ccpn.util.Logging import getLogger
from ccpn.util.OrderedSet import OrderedSet
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar, notificationEchoBlocking
import ccpn.ui.gui.widgets.CompoundWidgets as cw
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.ui.gui.widgets.RadioButton import RadioButton
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons, RadioButtonsWithSubCheckBoxes
from ccpn.ui.gui.widgets.RadioButton import CheckBoxCheckedText, CheckBoxCallbacks, CheckBoxTexts, CheckBoxTipTexts
from ccpn.ui.gui.widgets.MessageDialog import showWarning, _stoppableProgressBar, progressManager
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Menu import Menu
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Icon import Icon, ICON_DIR

INPLACE = 'In Place'
FOLLOW = 'Follow'
LAST = 'Last Created'
NEW = 'Create New'
FINDPEAKS = 'Find Peaks'
USEEXISTINGPEAKS = 'Use Existing Peaks'

_OnlyPositionAndAssignments = 'Copy position and assignments'
_IncludeAllPeakProperties   = 'Copy all existing properties'
_SnapToExtremum             = 'Snap to extremum'
_RefitPeaks                 = 'Refit peaks'
_RefitPeaksAtPosition       = 'Refit peaks at position'
_RecalculateVolume          = 'Recalculate volume'
_tipTextOnlyPos             = f'''Copy Peaks and include only the original position and assignments (if available).\nAdditionally, execute the selected operations'''
_tipTextIncludeAll          = f'''Copy Peaks and include all the original properties: \nPosition, Assignments, Heights, Linewidths, Volumes etc...'''
_tipTextSnapToExtremum      = 'Snap all new peaks to extremum. Default properties set in the General Preferences'
_tipTextRefitPeaks          = 'Refit all new peaks. Default properties set in the General Preferences'
_tipTextRefitPeaksAtPosition= 'Refit peaks and force to maintain the original position. Default properties set in the General Preferences'
_tipTextRecalculateVolume   = 'Recalculate volume for all peaks. Requires a Refit.'

def showWarningPopup():
    showWarning('Under implementation!', 'This popup is not active yet.')

class SeriesPeakCollectionPopup(CcpnDialogMainWidget):
    def __init__(self, parent=None, mainWindow=None, title='Series Peak Collection', **kwds):
        super().__init__(parent, setLayout=True,  size=(200, 300), minimumSize=None, windowTitle=title, **kwds)

        showWarningPopup()

        if mainWindow:
            self.mainWindow = mainWindow
            self.application = self.mainWindow.application
            self.project = self.mainWindow.project
            self.current = self.application.current
        else:
            self.mainWindow = None
            self.application = None
            self.project = None
            self.current = None
        self._sourcePeakList = None
        self._spectrumGroup = None
        self._fixedWidthsCW = [200, 200]
        self.setWidgets()
        self._populate()

        # enable the buttons
        self.setOkButton(callback=self._okClicked, tipText='Create Collections')
        self.setCloseButton(callback=self.reject, tipText='Close popup')
        self.setDefaultButton(CcpnDialogMainWidget.CLOSEBUTTON)
        self.__postInit__()

    def setWidgets(self):
        row = 0
        self.spectrumGroupCW = cw.PulldownListCompoundWidget(self.mainWidget, mainWindow=self.mainWindow,
                                                             labelText='SpectrumGroup', grid=(row, 0),
                                                             gridSpan = (1,2))
                                                             # fixedWidths=self._fixedWidthsCW)
        row += 1
        self.sourcePeakListCW = cw.PulldownListCompoundWidget(self.mainWidget,
                                                              mainWindow=self.mainWindow,
                                                              labelText='Source PeakList',grid=(row, 0),
                                                              gridSpan=(1, 2))
                                                              # fixedWidths=self._fixedWidthsCW)
        row += 1
        self.collectionNameCW = cw.EntryCompoundWidget(self.mainWidget, labelText='Collection Name', grid=(row, 0),
                                                       gridSpan=(1, 2))
        row += 1
        self.coloursLabel = Label(self.mainWidget, text='Colouring', grid=(row, 0))
        self.coloursOption = CheckBox(self.mainWidget, text='Use colour from contours', checked=True,
                                      tipText='Use contour colours for peak symbols and texts',
                                      grid=(row, 1))
        row += 1

        ## InPlace Peak options
        self.inplaceRadioButton = RadioButton(self.mainWidget, text='Copy Peaks In Place',
                                              callback=self._toggleFrames, grid=(row, 0))
        row += 1
        self._inplaceFrame = Frame(self.mainWidget, setLayout=True, grid=(row, 0), gridSpan=(1, 2))
        row += 1
        subRow = 0
        self.targetPeakListLabel = Label(self._inplaceFrame, text='Use peakList', grid=(subRow, 0))
        self.targetPeakListOptions = RadioButtons(self._inplaceFrame, texts=[LAST, NEW], grid=(subRow, 1))
        subRow += 1
        self.refitLabel = Label(self._inplaceFrame, text='Refitting', grid=(subRow, 0))
        self.refitOption = CheckBox(self._inplaceFrame, text='Refit and calculate volume',checked=False, grid=(subRow, 1))

        row += 1
        subRow = 0
        ## follow Peaks options
        self.followRadioButton = RadioButton(self.mainWidget, text='Follow Peaks', callback=self._toggleFrames,grid=(row, 0))
        row += 1
        self._followFrame = Frame(self.mainWidget, setLayout=True, grid=(row, 0), gridSpan=(1, 2))
        self.followPeakOptionstLabel = Label(self._followFrame, text='Select Mode', grid=(subRow, 0))
        self.followPeakOptionsRB = RadioButtons(self._followFrame, texts=[FINDPEAKS, USEEXISTINGPEAKS],
                                                callback=self._togglePeakListOptions, selectedInd=0, grid=(subRow, 1))
        subRow += 1
        self.followPeakLastNewPeakListLabel = Label(self._followFrame, text='Use peakList', grid=(subRow, 0))
        self.followPeakLastNewPeakListRB = RadioButtons(self._followFrame, texts=[LAST, NEW], grid=(subRow, 1))
        subRow += 1

        self.followMethodLabel = Label(self._followFrame, text='Method', grid=(subRow, 0))
        self.followMethodPD = PulldownList(self._followFrame, texts=['Option1'], grid=(subRow, 1))
        subRow += 1


        self.inplaceRadioButton.click()

    @property
    def sourcePeakList(self):
        return self.project.getByPid(self.sourcePeakListCW.pulldownList.getText())

    @property
    def spectrumGroup(self):
        return self.project.getByPid(self.spectrumGroupCW.pulldownList.getText())

    def _toggleFrames(self, *args):
        if self.inplaceRadioButton.isChecked():
            self._inplaceFrame.setVisible(True)
            self._followFrame.setVisible(False)
        else:
            self._followFrame.setVisible(True)
            self._inplaceFrame.setVisible(False)

    def _togglePeakListOptions(self):
        if self.followPeakOptionsRB.getSelectedText() == FINDPEAKS:
            self.followPeakLastNewPeakListRB.setVisible(True)
            self.followPeakLastNewPeakListLabel.setVisible(True)
        else:
            self.followPeakLastNewPeakListLabel.setVisible(False)
            self.followPeakLastNewPeakListRB.setVisible(False)


    def _populate(self):
        self._populateSourcePeakListPullDown()
        self._populateSpectrumGroupPullDown()


    def _okClicked(self):
        # with undoBlockWithoutSideBar():
        #    showWarningPopup()
        self.accept()


    def _populateSourcePeakListPullDown(self):
        """Populate the pulldown with the list of spectra in the project
        """
        if not self.project:
            return
        pass

    def _populateSpectrumGroupPullDown(self, *args):
        """
        """
        if not self.project:
            return
        pass




if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication

    app = TestApplication()
    popup = SeriesPeakCollectionPopup()

    popup.show()
    popup.raise_()
    app.start()

