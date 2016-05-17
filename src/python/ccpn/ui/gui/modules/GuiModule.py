"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtGui


from ccpn.ui.gui.widgets.Dock import CcpnDock, CcpnDockLabel

from ccpn.ui.gui.Base import Base as GuiBase

from pyqtgraph.dockarea import Dock

from PyQt4 import QtCore, QtGui

QtCore.qInstallMsgHandler(lambda *args: None)

class GuiModule(QtGui.QWidget, GuiBase):
  # It used to subclass Dock but that doesn't work because that has a function name() and we have an attribute name
  # So instead create a dock

  def __init__(self, position='right'):
    
    QtGui.QWidget.__init__(self)
    self.dockArea = self.window.dockArea
    self.dock = CcpnDock(name=self._wrappedData.name, size=(1100,1300), autoOrientation=False)
    # self.dock.label.hide()
    # self.dock.label = DockLabel(self._wrappedData.name, self.dock)
    # self.dock.label.show()
    self.hoverEvent = self._hoverEvent
    self.dockArea.addDock(self.dock, position=position)

    GuiBase.__init__(self, self._project._appBase)


  def _hoverEvent(self, event):
    event.accept()
