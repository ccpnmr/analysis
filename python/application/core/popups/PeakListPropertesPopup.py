

from PyQt4 import QtGui

from ccpncore.gui.Base import Base
from ccpncore.gui.Button import Button
from ccpncore.gui.Label import Label
from ccpncore.gui.CheckBox import CheckBox
from ccpncore.gui.PulldownList import PulldownList

class PeakListPropertiesPopup(QtGui.QDialog, Base):
  def __init__(self, parent=None, peakList=None, **kw):
    super(PeakListPropertiesPopup, self).__init__(parent)
    Base.__init__(self, **kw)

    self.peakListLabel = Label(self, "PeakList Name ", grid=(0, 0))
    self.peakListLabel = Label(self, peakList.id, grid=(0, 1))
    self.displayedLabel = Label(self, 'Is displayed', grid=(1, 0))
    self.displayedCheckBox = CheckBox(self, grid=(1, 1), checked=False)
    self.symbolLabel = Label(self, 'Peak Symbol', grid=(2, 0))
    self.symbolPulldown = PulldownList(self, grid=(2, 1))
    self.symbolColourLabel = Label(self, 'Peak Symbol Colour', grid=(3, 0))
    self.symbolColourPulldownList = PulldownList(self, grid=(3, 1))
    self.symbolColourMoreButton = Button(self, 'More...', grid=(3, 2))
    self.minimalAnnotationLabel = Label(self, 'Minimal Annotation', grid=(4, 0))
    self.minimalAnnotationCheckBox = CheckBox(self, grid=(4, 1))

  #   for peakList in spectrum.peakLists:
  #     label = Label(self, grid=(i, 1), text=str(peakList.pid), vAlign='t', hAlign='l')
  #     checkBox = CheckBox(self, grid=(i, 0), checked=True, vAlign='t', hAlign='l')
  #     # self.layout().addWidget(checkBox, i, 0, QtCore.Qt.AlignTop)
  #     for strip in self.spectrum.project.strips:
  #       peakListView = strip.peakListViewDict.get(peakList)
  #       if peakListView is not None:
  #         if peakListView.isVisible():
  #           checkBox.setChecked(True)
  #         else:
  #           checkBox.setChecked(False)
  #       else:
  #         checkBox.setChecked(False)
  #   #   #
  #       checkBox.stateChanged.connect(partial(self.peakListToggle, peakListView))
  #     i+=1
  #
  # def peakListToggle(self, peakListView, state):
  #     if peakListView is not None:
  #       if state == QtCore.Qt.Checked:
  #         peakListView.setVisible(True)
  #       else:
  #         peakListView.setVisible(False)


