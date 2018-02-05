from PyQt5 import QtGui, QtWidgets, QtCore
Qt = QtCore.Qt

from .Base import Base


class Label(QtWidgets.QLabel, Base):

  def __init__(self, text='', align=None, textColor=None, **kw):

    QtWidgets.QLabel.__init__(self, text)
    Base.__init__(self,  **kw)
    
    if align:
      letter = align.lower()[0]
    
      if letter == 'r':
        alignment = Qt.AlignRight | QtCore.Qt.AlignVCenter
        
      elif letter == 'c':
        alignment = Qt.AlignHCenter | QtCore.Qt.AlignVCenter
        
      else:
        alignment = Qt.AlignLeft | QtCore.Qt.AlignVCenter
        
      self.setAlignment(alignment)
    
    if textColor:
      self.setStyleSheet('QLabel {color: %s;}' % textColor)
    
  def get(self):

    return self.text()

  def set(self, text=''):

    self.setText(text)


if __name__ == '__main__':

  from .Button import Button
  from .Application import Application

  msg = 'Hello world'
  count = 0

  def func():

    global count

    count += 1
    label.set(msg + ' ' + str(count))
    print(label.get())

  import sys
  app = Application()
  
  window = QtWidgets.QWidget()
 
  label = Label(window, text='Hello world', textColor='red', grid=(0,0))
  button = Button(window, text='Click me', command=func, grid=(0,1))

  window.show()

  app.start()
