import sys

from PyQt5 import QtGui, QtWidgets, QtCore

from .Base import Base

class ToolBar(QtWidgets.QToolBar, Base):

  def __init__(self, parent=None, **kw):

    QtWidgets.QToolBar.__init__(self, parent)
    Base.__init__(self, parent, **kw)

if __name__ == '__main__':

  from .Application import Application
  from .BasePopup import BasePopup
  from .Button import Button
  from PySide import QtCore

  def buttonName(text):
    print("Toggled ", text)

  app = Application()
  popup = BasePopup(title='Test Frame')
  popup.resize(400, 400)
  toolBar = ToolBar(parent=popup, sticky = 'n')
  
  actionData = [('Button 1', QtGui.QKeySequence("1")),
		('Button 2', QtGui.QKeySequence("2")),
		('Button 3', QtGui.QKeySequence("3")),
		('Button 4', QtGui.QKeySequence("4")),
		('Button 5', QtGui.QKeySequence("5")),
		]

  signalMapper = QtCore.QSignalMapper(app)
  
  for text, keys in actionData:
    action = QtWidgets.QAction(text, popup, shortcut=keys)
    signalMapper.setMapping(action, text)
    action.triggered.connect(signalMapper.map)
    toolBar.addAction(action)
    
  signalMapper.mapped.connect(buttonName)
  
  

  app.start()

