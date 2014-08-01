from PySide import QtGui, QtCore
Qt = QtCore.Qt

from ccpncore.gui.Base import Base

class Label(QtGui.QLabel, Base):

  def __init__(self, parent, text='', textColor=None, **kw):

    QtGui.QLabel.__init__(self, text, parent)
    Base.__init__(self, **kw)
        
    if textColor:
      self.setStyleSheet('QLabel {color: %s;}' % textColor)
    
  def get(self):

    return self.text()

  def set(self, text=''):

    self.setText(self.translate(text))

if __name__ == '__main__':

  from ccpncore.gui.Application import TestApplication
  from ccpncore.gui.Button import Button

  msg = 'Hello world'
  count = 0

  def func():

    global count

    count += 1
    label.set(msg + ' ' + str(count))
    print(label.get())

  app = TestApplication()
  
  window = QtGui.QWidget()
 
  label = Label(window, text=msg, textColor='red', grid=(0,0))
  button = Button(window, text='Click me', callback=func, grid=(0,1))

  window.show()

  app.start()
