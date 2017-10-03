from PyQt5 import QtCore, QtGui, QtWidgets

from .Base import Base

PEN = QtCore.Qt.black
QPainter = QtGui.QPainter
Antialiasing = QPainter.Antialiasing

class Divider(QtWidgets.QFrame, Base):

  def __init__(self, parent, text=None, direction='h', minSize=8, **kw):
  
    QtWidgets.QFrame.__init__(self, parent)
    Base.__init__(self, parent, **kw)
    
    self.text = text
    self.minSize = minSize
    self.fontMetric = QtGui.QFontMetricsF(self.font())
    
    if text:
      direction = 'h' 
      self.bbox = self.fontMetric.tightBoundingRect(text)
      indent = self.bbox.width() + minSize
      textHeight = self.bbox.height()
      
    else:
      indent = indent = 0
      textHeight = 0
    
    rect = self.rect()
    x = rect.x()
    y = rect.y()
    w = rect.width()
    h = rect.height()   
    
    if 'h' in direction.lower():
      self.setFrameShape(QtWidgets.QFrame.HLine)
      self.setFrameRect(QtCore.QRect(x+minSize/2+indent,y,w-minSize-indent,h))
    else:
      self.setFrameShape(QtWidgets.QFrame.VLine)
      self.setFrameRect(QtCore.QRect(x,y+minSize/2,w,h-minSize))
      
    self.setMinimumSize(minSize, max(minSize, textHeight))
    self.setFrameShadow(QtWidgets.QFrame.Raised)
    self.setMidLineWidth(3)
    self.setLineWidth(0)
  
  def setText(self, text):
  
    self.text = text

    rect = self.rect()
    x = rect.x()
    y = rect.y()
    w = rect.width()
    h = rect.height()   
    
    self.bbox = self.fontMetric.tightBoundingRect(text)
    indent = self.bbox.width() + self.minSize
    self.setFrameShape(QtWidgets.QFrame.HLine)
    self.setFrameRect(QtCore.QRect(x+self.minSize/2+indent,y,w-self.minSize-indent,h))
  
  def paintEvent(self, event):   
    

    if self.text:
      painter = QPainter()
      painter.begin(self);
      painter.setRenderHint(Antialiasing);
      
      h = self.bbox.height()
      y = self.height() / 2.0 +  h / 2.0
      x = self.minSize
      
      painter.setPen(PEN)
      painter.drawText(x, y, self.text)
 
      painter.end()
      
    QtWidgets.QFrame.paintEvent(self, event)

if __name__ == '__main__':

  from .Application import Application
  from .BasePopup import BasePopup
  from .Button import Button
  
  app = Application()
  popup = BasePopup(title='Test Frame')
  popup.resize(400, 150)
  
  Button(popup, 'Button 1')
  
  Divider(popup)
  
  Button(popup, 'Button 2')

  div = Divider(popup, 'A Label')
  
  def changeText():
    div.setText('A new text label')
  
  Button(popup, 'Ckick to change label', changeText)
  
  app.start()

