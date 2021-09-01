from PyQt5 import QtCore, QtGui, QtWidgets

from .Base import Base
from .RadioButton import RadioButton

CHECKED = QtCore.Qt.Checked
UNCHECKED = QtCore.Qt.Unchecked

class RadioButtons(QtWidgets.QWidget, Base):

  def __init__(self, parent=None, texts=None, selectedInd=None,
               callback=None, direction='h', tipTexts=None,  **kw):
    
    # # # # # Note change from exntries to texts compared to Tkinter # # # # # 
    
    QtWidgets.QWidget.__init__(self, parent)
    Base.__init__(self, parent, **kw)

    if texts is None:
      texts = []
    
    self.texts = texts
    direction = direction.lower()
    buttonGroup = self.buttonGroup = QtWidgets.QButtonGroup(self)
    buttonGroup.setExclusive(True)
    
    if not tipTexts:
      tipTexts = [None] * len(texts)
    
    self.radioButtons = []  
    for i, text in enumerate(texts):
      if 'h' in direction:
        grid = (0, i)
      else:
        grid = (i, 0)
         
      button = RadioButton(self, text, tipText=tipTexts[i], grid=grid)
      
      self.radioButtons.append(button)
      
      buttonGroup.addButton(button)
      buttonGroup.setId(button, i)
    
    if selectedInd is not None:
      self.radioButtons[selectedInd].setChecked(True)

    buttonGroup.buttonClicked.connect(self._callback)

    self.setCallback(callback)

  def get(self):

    return self.texts[self.getIndex()]

  def getIndex(self):

    return self.radioButtons.index(self.buttonGroup.checkedButton())

  def set(self, text):

    i = self.texts.index(text)
    self.setIndex(i)

  def setIndex(self, i):

    self.radioButtons[i].setChecked(True)
  
  def setCallback(self, callback):

    self.callback = callback

  def _callback(self, ind):

    if self.callback and ind >= 0:
      button = self.buttonGroup.buttons()[ind]
      self.callback(button.text())

if __name__ == '__main__':

  from .Application import Application
  from .BasePopup import BasePopup

  texts = ['abc', 'def', 'ghi']

  def callback(text):
    print('callback', text)

  app = Application()
  popup = BasePopup(title='Test RadioButtons')
  popup.setSize(300, 60)
  radios = RadioButtons(parent=popup, texts=texts,
                        callback=callback, selectedInd=1)
  app.start()

