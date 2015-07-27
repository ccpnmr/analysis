__author__ = 'simon1'

from PyQt4 import QtCore, QtGui

from pyqtgraph.dockarea.Dock import DockLabel, Dock

from ccpncore.gui.Font import Font

class CcpnDock(Dock):
  def __init__(self, name, **kw):
    super(CcpnDock, self).__init__(name, self)
    self.label.hide()
    self.label = CcpnDockLabel(name.upper(), self)
    self.label.show()
    self.label.closeButton.clicked.connect(self.closeDock)
    self.label.fixedWidth = True
    self.autoOrientation = False

  def resizeEvent(self, event):
    self.setOrientation('vertical', force=True)
    self.resizeOverlay(self.size())

  def closeDock(self):
    self.close()



class CcpnDockLabel(DockLabel):

    def __init__(self, *args):
      super(CcpnDockLabel, self).__init__(showCloseButton=True, *args)
      self.setFont(Font(size=12, semiBold=True))


    #def minimumSizeHint(self):
        ##sh = QtGui.QWidget.minimumSizeHint(self)
        #return QtCore.QSize(20, 20)



    def updateStyle(self):
        pass

