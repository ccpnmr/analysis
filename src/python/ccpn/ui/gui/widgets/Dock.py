#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:42 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: simon1 $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtCore, QtGui

from pyqtgraph.dockarea.Dock import DockLabel, Dock

from ccpn.ui.gui.guiSettings import moduleLabelFont

class CcpnDock(Dock):
  def __init__(self, name, **kw):
    super(CcpnDock, self).__init__(name, self)
    self.label.hide()
    self.label = CcpnDockLabel(name.upper(), self)
    self.label.show()
    self.label.closeButton.clicked.connect(self.closeModule)
    self.label.fixedWidth = True
    self.autoOrientation = False
    self.mainWidget = QtGui.QWidget(self)
    self.settingsWidget = QtGui.QWidget(self)
    self.addWidget(self.mainWidget, 0, 0)
    self.addWidget(self.settingsWidget, 1, 0)

  def resizeEvent(self, event):
    self.setOrientation('vertical', force=True)
    self.resizeOverlay(self.size())

  def closeDock(self):
    self.close()

class CcpnDockLabel(DockLabel):

    def __init__(self, *args):
      super(CcpnDockLabel, self).__init__(showCloseButton=True, *args)
      self.setFont(moduleLabelFont)

    def mousePressEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            self.pressPos = ev.pos()
            self.startedDrag = False
            ev.accept()



