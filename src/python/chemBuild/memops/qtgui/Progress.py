from PyQt5 import QtGui, QtWidgets, QtCore

from .Base import Base


class ProgressDialog(QtWidgets.QProgressDialog):

  def __init__(self, parent=None, text='', minimum=0, maximum=99):

    QtWidgets.QProgressDialog.__init__(self, parent=None)
    
    self.setText(text)
    self.setRange(minimum, maximum)
    self.setAutoReset(True)
    self.setAutoClose(True)
    self.setMinimumDuration(1000)
     
  def setText(self, text):
   
    self.setLabel(QtWidgets.QLabel(text, self))
      
  def increment(self, n=1):
  
    self.setValue(self.value()+n)
  
  def getValue(self):
    
    return self.value()
  
  def getProportion(self):
  
    a = self.minimum()
    b = self.maximum()
    return (self.value() - a) / (b-a)
  
  # setRange() inbuilt
  # reset() inbuilt
  # setText() inbuilt
  
  def set(self, value):

    if (value not in (0,1)) and value <=1.0 :
      a = self.minimum()
      b = self.maximum()
      value = float(value) * (b-a)
      value += a
      
    self.setValue(int(value))

class ProgressWidget(QtWidgets.QProgressBar, Base):

  def __init__(self, parent=None, minimum=0,
               maximum=99, total=None, **kw):

    QtWidgets.QProgressBar.__init__(self, parent=None)
    Base.__init__(self, parent, **kw)
    
    self.setRange(minimum, maximum)
    self.show()
      
  def increment(self, n=1):
  
    self.setValue(self.value()+n)
  
  def getValue(self):
    
    return self.value()
  
  def getProportion(self):
  
    a = self.minimum()
    b = self.maximum()
    return (self.value() - a) / (b-a)
  
  def set(self, value):

    if (value not in (0,1)) and value <=1.0 :
      a = self.minimum()
      b = self.maximum()
      value = float(value) * (b-a)
      value += a
      
    self.setValue(int(value))

if __name__ == '__main__':

  import time
  from .Application import Application
  from .BasePopup import BasePopup
  
  app = Application()
  
  window = BasePopup()
  window.setSize(200, 50)
  window.show()
  
  pb1 = ProgressDialog(window, text='Increments')
  pb2 = ProgressWidget(window)
  
  for i in range(100):
    time.sleep(0.1)
    pb1.setValue(i)
    #pb1.increment()
  
  for i in range(100):
    time.sleep(0.1)
    pb2.setValue(100-i)
    
  app.start()
