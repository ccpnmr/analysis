from PyQt4 import QtGui

from application.core.widgets.Base import Base
from application.core.widgets.ButtonList import ButtonList
from application.core.widgets.Label import Label
from application.core.widgets.PulldownList import PulldownList


restraintTypes = [
  'Distance',
  'Dihedral',
  'Rdc',
  'Csa',
  'ChemicalShift',
  'JCoupling'
]

class RestraintTypePopup(QtGui.QDialog, Base):
  def __init__(self, parent=None, peakList=None, **kw):
    super(RestraintTypePopup, self).__init__(parent)
    Base.__init__(self, **kw)

    self.restraintTypeLabel = Label(self, "Restraint Type ", grid=(0, 0))
    self.restraintTypeList = PulldownList(self, grid=(0, 1))
    self.restraintTypeList.setData(restraintTypes)
    buttonList = ButtonList(self, ['Cancel', 'OK'], [self.reject, self.setRestraintType], grid=(1, 1))

  def setRestraintType(self):
    self.restraintType = self.restraintTypeList.currentText()
    self.accept()