from PyQt5 import QtCore, QtGui, QtWidgets

from .Base import Base
from .CheckButton import CheckButton

class CheckButtons(QtWidgets.QWidget, Base):

  def __init__(self, parent=None, texts=None, states=None, selectedInds=None,
               callback=None, direction='h', tipTexts=None, selected=None, **kw):
    
    # # # # # Note change from exntries to texts compared to Tkinter # # # # # 
    
    QtWidgets.QWidget.__init__(self, parent)
    Base.__init__(self, parent, **kw)

    if selected:
      states = selected
      print("qtGui.CheckButtons.selected is deprecated; use .states instead")

    if texts is None:
      texts = []

    selectedInds = set(selectedInds or [])
    direction = direction.lower()
    buttonGroup = self.buttonGroup = QtGui.QButtonGroup(self)
    buttonGroup.setExclusive(False)

    if not states:
      states = [False] * len(texts)
    
    if not tipTexts:
      tipTexts = [None] * len(texts)
    
    self.checkButtons = []  
    for i, text in enumerate(texts):
      if 'h' in direction:
        grid = (0, i)
      else:
        grid = (i, 0)

      if i in selectedInds:
        states[i] = True
         
      button = CheckButton(self, text, tipText=tipTexts[i], grid=grid)
      button.set(states[i])
      self.checkButtons.append(button)
      
      buttonGroup.addButton(button)
      buttonGroup.setId(button, i)
      
    # buttonGroup.connect(buttonGroup, QtCore.pyqtSignal('buttonClicked(int)'), self._callback)
    buttonGroup.buttonClicked.connect(self._callback)

    self.setCallback(callback)
  
  def getStates(self):
  
    return [cb.isSelected() for cb in self.checkButtons]
  
  def setStates(self, states):
  
    for i, checkButton in enumerate(self.checkButtons):
      checkButton.set(states[i])
  
  def getSelected(self):
  
    states = self.getStates()
    
    return set([t for i, t in enumerate(self.texts) if states[i]])
  
  def setCallback(self, callback):

    self.callback = callback

  def isIndexSelected(self, i):
    
    return self.checkButtons[i].isSelected()

  def setIndexSelected(self, i, state=True):
    
    checkButton = self.checkButtons[i]
    checkButton.set(state)

  def setIndexSelection(self, i, state=True):
    
    print("qtGui.CheckButtons.setIndexSelection is deprecated; use .setIndexSelected instead")
    
    self.setIndexSelected(i, state)
    
  def toggleIndex(self, i):
    
    checkButton = self.checkButtons[i]
    checkButton.set(not checkButton.isSelected())

  def _callback(self, ind):

    if self.callback and ind >= 0:
      button = self.buttonGroup.buttons()[ind]
      self.callback(button.text(), button.isSelected())

if __name__ == '__main__':

  from .Application import Application
  from .BasePopup import BasePopup

  texts = ['Opt 1', 'Opt 2', 'Opt 3']
  tipTexts=['Tip A','Tip B','Tip C']
  
  def callback(text, state):
    print('callback', text, state)

  app = Application()
  popup = BasePopup(title='Test CheckButtons')
  popup.setSize(300,60)
  
  CheckButtons(parent=popup, texts=texts, callback=callback,
               selectedInds=(0,2), tipTexts=tipTexts)
               
  app.start()

