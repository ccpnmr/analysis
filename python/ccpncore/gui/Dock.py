__author__ = 'simon1'

from PyQt4 import QtCore, QtGui

from pyqtgraph.widgets.VerticalLabel import VerticalLabel

from pyqtgraph.dockarea.Dock import DockLabel, Dock

from ccpncore.gui.Font import Font

class CcpnDock(Dock):
  def __init__(self, name, **kw):
    super(CcpnDock, self).__init__(name, self)
    self.label.hide()
    self.label = CcpnDockLabel(name.upper(), self)
    self.label.show()
    self.autoOrientation = False

  def resizeEvent(self, event):
    self.setOrientation('vertical', force=True)
    self.resizeOverlay(self.size())



class CcpnDockLabel(DockLabel):

    def __init__(self, *args):
      super(CcpnDockLabel, self).__init__(showCloseButton=False, *args)
      self.setFont(QtGui.QFont('Lucida Grande', 10))


    #def minimumSizeHint(self):
        ##sh = QtGui.QWidget.minimumSizeHint(self)
        #return QtCore.QSize(20, 20)


    def updateStyle(self):
        r = '5px'
        if self.dim:
            fg = '#122043'
            bg = '#BEC4F3'
            border = '#00092D'
        else:
            fg = '#122043'
            bg = '#BEC4F3'
            border = '#55B'

        # if self.orientation == 'vertical':
        self.vStyle = """DockLabel {
                background-color : %s;
                color : %s;

            }""" % (bg, fg)
        self.setStyleSheet(self.vStyle)


