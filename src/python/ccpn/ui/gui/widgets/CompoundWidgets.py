from PyQt4 import QtGui, QtCore

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList


class SelectorWidget(QtGui.QWidget, Base):

  def __init__(self, parent, label, data=None, callback=None, **kw):

    QtGui.QWidget.__init__(self, parent)
    Base.__init__(self, **kw)

    if data:
      data.insert(0, '')
    label1 = Label(self, text=label, grid=(0, 0))
    self.pulldownList = InputPulldown(self, grid=(0, 1), texts=data, callback=callback)


class InputPulldown(PulldownList):

  def __init__(self, parent=None, callback=None, **kw):
    PulldownList.__init__(self, parent, **kw)

    self.setData(['', '<New Item>'])
    if callback:
      self.setCallback(callback)
    else:
      self.setCallback(self.addNewItem)

  def addNewItem(self, item):
    if item == '<New Item>':
      newItemText = LineEditPopup()
      newItemText.exec_()
      newItem = newItemText.inputField.text()
      texts = self.texts
      texts.insert(-2, newItem)
      if '' in texts:
        texts.remove('')
      self.setData(list(set(texts)))
      self.select(newItem)
      return newItem


class LineEditPopup(QtGui.QDialog, Base):

  def __init__(self, parent=None, dataType=None, **kw):

    QtGui.QDialog.__init__(self, parent)
    Base.__init__(self, **kw)

    inputLabel = Label(self, 'Input', grid=(0, 0))
    self.inputField = LineEdit(self, grid=(0, 1))

    ButtonList(self, grid=(1, 1), callbacks=[self.reject, self.returnItem], texts=['Cancel', 'OK'])

    if dataType:
      inputLabel.setText('New %s name' % dataType)

  def returnItem(self):
    self.accept()


