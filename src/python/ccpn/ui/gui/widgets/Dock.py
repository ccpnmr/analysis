#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-09-22 09:32:50 +0100 (Tue, September 22, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtGui, QtWidgets
from pyqtgraph.dockarea.Dock import DockLabel, Dock
# from ccpn.ui.gui.guiSettings import moduleLabelFont
from ccpn.ui.gui.widgets.Font import setWidgetFont


class CcpnDock(Dock):
    def __init__(self, name):
        super().__init__(name=name, area=self)
        self.label.hide()
        self.label = CcpnDockLabel(name.upper(), self)
        self.label.show()
        self.label.closeButton.clicked.connect(self.closeModule)
        self.label.fixedWidth = True
        self.autoOrientation = False
        self.mainWidget = QtWidgets.QWidget(self)
        self.settingsWidget = QtWidgets.QWidget(self)
        self.addWidget(self.mainWidget, 0, 0)
        self.addWidget(self.settingsWidget, 1, 0)

    def resizeEvent(self, event):
        self.setOrientation('vertical', force=True)
        self.resizeOverlay(self.size())

    def closeDock(self):
        self.close()


class CcpnDockLabel(DockLabel):

    def __init__(self, *args):
        super().__init__(showCloseButton=True, *args)

        # from ccpn.framework.Application import getApplication
        # getApp = getApplication()
        # if getApp and hasattr(getApp, '_fontSettings'):
        #     self.setFont(getApp._fontSettings.moduleLabelFont)
        setWidgetFont(self, )

    def mousePressEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            self.pressPos = ev.pos()
            self.startedDrag = False
            ev.accept()
