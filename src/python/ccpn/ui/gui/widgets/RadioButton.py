
from PyQt5 import QtGui, QtWidgets, QtCore

from ccpn.ui.gui.widgets.Base import Base
from ccpn.framework.Translation import translator



class RadioButton(QtWidgets.QRadioButton, Base):

  def __init__(self, parent, text='', textColor=None, textSize=None, callback=None, **kwds):

    super().__init__(parent)
    Base._init(self,  **kwds)

    text = translator.translate(text)
    self.setText(text)

    if textColor:
      self.setStyleSheet('QRadioButton {color: %s; font-size: 12pt;}' % textColor)
    if textSize :
      self.setStyleSheet('QRadioButton {font-size: %s;}' % textSize)
    if callback:
      self.setCallback(callback)
    if not self.objectName():
      self.setObjectName(text)

    self.setStyleSheet('''
    RadioButton::disabled {
                            color: #7f88ac;
                            }
                            ''')

  def get(self):
    return self.text()

  def set(self, text=''):
    if len(text) > 0:
      text = translator.translate(text)
    self.setText(text)


  def getText(self):
    "Get the text of the button"
    return self.get()


  def setCallback(self, callback):
    #
    # if self.callback:
    #   self.disconnect(self, QtCore.SIGNAL('clicked()'), self.callback)

    if callback:
      # self.connect(self, QtCore.SIGNAL('clicked()'), callback)
      self.clicked.connect(callback)



