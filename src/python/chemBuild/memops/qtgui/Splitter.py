import sys

from PyQt5 import QtCore, QtGui, QtWidgets

from .Base import Base

class Splitter(QtGui.QSplitter, Base):

  def __init__(self, parent=None, splitterDirection=QtCore.Qt.Horizontal, **kw):

    QtGui.QSplitter.__init__(self, splitterDirection, parent)
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

if __name__ == '__main__':

  from .Application import Application
  from .BasePopup import BasePopup
  from .Table import Column, ObjectTable

  class TestObj:
  
    def __init__(self, i, name, greek):
      self.i = i
      self.name = name
      self.greek = greek
  
  objects = (TestObj(1, 'One', '\u03B1'),
             TestObj(2, 'Two', '\u03B2'),
             TestObj(3, 'Three','\u03B3'),
             TestObj(4, 'Four', '\u03B4'),
             TestObj(5, 'Five', '\u03B5'),
             TestObj(6, 'Six', '\u03B6'),
             TestObj(7, 'Seven', '\u03B7'),
             TestObj(8, 'Eight', '\u03B8'),
             TestObj(9, 'Nine', '\u03B9'),
             TestObj(10,'Ten', '\u03BA'))

  
  app = Application()
  popup = BasePopup(title='Splitter test')
  popup.resize(400, 400)
  splitter = Splitter(popup, QtCore.Qt.Horizontal)
  
  objectCols = [Column('x', 'i', tipText='Tip C', alignment='C'),
                Column('Name', 'name',
                       tipText='Tip A'),
                Column('Greek', 'greek', tipText='Tip B',
                       alignment='center')]

  objTable1 = ObjectTable(splitter, objectCols, objects,
                          multiSelect=True)
  objTable2 = ObjectTable(splitter, objectCols, objects,
                          multiSelect=True)
                          
  app.start()

