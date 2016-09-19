from PyQt4 import QtGui

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit

class DataSetPopup(QtGui.QDialog, Base):
  def __init__(self, parent=None, dataSet=None, **kw):
    super(DataSetPopup, self).__init__(parent)
    Base.__init__(self, **kw)

    self.dataSet = dataSet
    self.dataSetLabel = Label(self, "DataSet Name ", grid=(0, 0))
    self.dataSetText = LineEdit(self, dataSet.title, grid=(0, 1))
    ButtonList(self, ['Cancel', 'OK'], [self.reject, self._setDataSetName], grid=(1, 1))

  def _setDataSetName(self):
    newName = self.dataSetText.text()
    self.dataSet.title = newName
    self.accept()


