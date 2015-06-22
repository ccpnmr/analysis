"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtGui


from ccpncore.gui.DockLabel import DockLabel

from ccpnmrcore.Base import Base as GuiBase

from pyqtgraph.dockarea import Dock

from PyQt4 import QtCore, QtGui

QtCore.qInstallMsgHandler(lambda *args: None)

class GuiModule(QtGui.QWidget, GuiBase):
  # It used to subclass Dock but that doesn't work because that has a function name() and we have an attribute name
  # So instead create a dock

  def __init__(self, position='right'):
    
    QtGui.QWidget.__init__(self)
    self.dockArea = self.window.dockArea
    # self.apiModule = apiModule
    # self.labelStyle = """DockLabel {
    #             background-color : #bec4f3;
    #             color : #122043;
    #             border: 1px 1px 1px 1px solid #00092d;
    #         }"""
    self.dock = Dock(name=self._wrappedData.name, size=(1100,1300))
    self.dock.setStyleSheet("""
    QWidget { background-color: #2a3358;
    }
    """)
    self.dock.label.hide()
    self.dock.label = DockLabel(self._wrappedData.name, self.dock)
    self.dock.label.show()



    # self.dock.label.updateStyle(self.labelStyle)
    self.dockArea.addDock(self.dock, position=position)
    GuiBase.__init__(self, self._project._appBase)

  def hoverEvent(self, event):
    event.accept()
    print(self)