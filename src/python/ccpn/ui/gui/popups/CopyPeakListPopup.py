"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:47 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets, QtCore
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.core.lib.ContextManagers import undoBlockManager


class CopyPeakListPopup(CcpnDialog):
    def __init__(self, parent=None, mainWindow=None, title='Copy PeakList', **kwds):
        CcpnDialog.__init__(self, parent, setLayout=False, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        self.application = self.mainWindow.application
        self.project = self.mainWindow.project

        self._setMainLayout()
        self.setWidgets()
        self.addWidgetsToLayout()

    def _setMainLayout(self):
        self.mainLayout = QtWidgets.QGridLayout()
        self.setLayout(self.mainLayout)
        self.setWindowTitle("Copy PeakList")
        self.mainLayout.setContentsMargins(20, 20, 20, 5)  # L,T,R,B
        self.setFixedWidth(300)
        self.setFixedHeight(130)

    def setWidgets(self):
        self.sourcePeakListLabel = Label(self, 'Source PeakList')
        self.sourcePeakListPullDown = PulldownList(self)
        self._populateSourcePeakListPullDown()

        self.targetSpectraLabel = Label(self, 'Target Spectrum')
        self.targetSpectraPullDown = PulldownList(self)
        self._populateTargetSpectraPullDown()

        self.okCancelButtons = ButtonList(self, texts=['Cancel', ' Ok '],
                                          callbacks=[self.reject, self._okButton],
                                          tipTexts=['Close Popup', 'Copy PeakList'])

    def addWidgetsToLayout(self):
        self.mainLayout.addWidget(self.sourcePeakListLabel, 0, 0)
        self.mainLayout.addWidget(self.sourcePeakListPullDown, 0, 1)
        self.mainLayout.addWidget(self.targetSpectraLabel, 1, 0)
        self.mainLayout.addWidget(self.targetSpectraPullDown, 1, 1)
        self.mainLayout.addWidget(self.okCancelButtons, 2, 1)

    def _okButton(self):
        with undoBlockManager():
            self.sourcePeakList = self.project.getByPid(self.sourcePeakListPullDown.getText())
            self.targetSpectrum = self.project.getByPid(self.targetSpectraPullDown.getText())
            self._copyPeakListToSpectrum()
        self.accept()

    def _copyPeakListToSpectrum(self):
        if self.sourcePeakList is not None:
            try:
                if self.targetSpectrum is not None:
                    self.sourcePeakList.copyTo(self.targetSpectrum)

            except Exception as es:
                getLogger().warning('Error copying peakList: %s' % str(es))
                showWarning(str(self.windowTitle()), str(es))
                if self.application._isInDebugMode:
                    raise es


    def _populateSourcePeakListPullDown(self):
        sourcePullDownData = []
        if len(self.project.peakLists) > 0:
            for pl in self.project.peakLists:
                sourcePullDownData.append(str(pl.pid))
        self.sourcePeakListPullDown.setData(sourcePullDownData)
        self._selectDefaultPeakList()

    def _populateTargetSpectraPullDown(self):
        targetPullDownData = []
        if len(self.project.spectra) > 0:
            for sp in self.project.spectra:
                targetPullDownData.append(str(sp.pid))
        self.targetSpectraPullDown.setData(targetPullDownData)
        self._selectDefaultSpectrum()

    def _selectDefaultPeakList(self):
        if self.application.current.peak is not None:
            defaultPeakList = self.application.current.peak.peakList
            self.sourcePeakListPullDown.select(defaultPeakList.pid)
            # print('Selected defaultPeakList: "current.peak.peakList" ',defaultPeakList) #Testing statement to be deleted
            return
        if self.application.current.strip is not None:
            defaultPeakList = self.application.current.strip.spectra[0].peakLists[-1]
            self.sourcePeakListPullDown.select(defaultPeakList.pid)
            # print('Selected defaultPeakList: "current.strip.spectra[0].peakLists[-1]" ', defaultPeakList)  #Testing statement to be deleted
            return
        else:
            defaultPeakList = self.project.spectra[0].peakLists[-1]
            self.sourcePeakListPullDown.select(defaultPeakList.pid)
            # print('Selected defaultPeakList: "self.project.spectra[0].peakLists[-1]" ', defaultPeakList) #Testing statement to be deleted
            return

    def _selectDefaultSpectrum(self):
        if self.application.current.strip is not None:
            defaultSpectrum = self.application.current.strip.spectra[-1]
            self.targetSpectraPullDown.select(defaultSpectrum.pid)
            # print('Selected defaultSpectrum: "current.strip.spectra[-1]" ', defaultSpectrum) #Testing statement to be deleted
            return
        else:
            defaultSpectrum = self.project.spectra[-1]
            self.targetSpectraPullDown.select(defaultSpectrum.pid)
            # print('Selected defaultSpectrum: "self.project.spectra[-1]" ', defaultSpectrum) #Testing statement to be deleted
            return


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.popups.Dialog import CcpnDialog
    import ccpn.core.testing.WrapperTesting as WT


    app = TestApplication()
    app._ccpnApplication = app
    app.colourScheme = 'dark'

    thisWT = WT.WrapperTesting()
    thisWT.setUp()

    app.project = thisWT.project

    popup = CopyPeakListPopup()  # too many errors for testing here...

    popup.show()
    popup.raise_()

    app.start()

    WT.WrapperTesting.tearDown(thisWT)
