__author__ = 'simon'

from PySide import QtGui

from ccpncore.gui.Base import Base

class Splitter(QtGui.QSplitter, Base):

  def __init__(self, parent=None, **kw):

    QtGui.QSplitter.__init__(self, parent)
    Base.__init__(self, parent, **kw)

    self.doResize = False

  def createHandle(self):

    return SplitterHandle(self, self.orientation())

  def resizeEvent(self, event):

    self.doResize = True
    eventResult = QtGui.QSplitter.resizeEvent(self, event)
    self.doResize = False

    return eventResult

class SplitterHandle(QtGui.QSplitterHandle):

  def __init__(self, parent, orientation):

    QtGui.QSplitterHandle.__init__(self, orientation, parent)

  def mousePressEvent(self, event):

    self.parent().doResize = True
    return QtGui.QSplitter.mousePressEvent(self, event)

  def mouseReleaseEvent(self, event):

    self.parent().doResize = False
    return QtGui.QSplitter.mouseReleaseEvent(self, event)
