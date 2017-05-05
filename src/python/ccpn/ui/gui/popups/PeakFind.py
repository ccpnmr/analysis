"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__author__ = "$Author: CCPN $"
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:41 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"

#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: simon $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtGui, QtCore
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.RadioButton import RadioButton
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Widget import Widget

from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.popups.Dialog import CcpnDialog      # ejb


class PeakFindPopup(CcpnDialog):
# class PeakFindPopup(QtGui.QDialog, Base):
  def __init__(self, parent=None, project=None, current=None, **kw):
    CcpnDialog.__init__(self, parent, setLayout=True, windowTitle='', **kw)
    # super(PeakFindPopup, self).__init__(parent)
    # Base.__init__(self, **kw)

    self.project = project
    self.peakListLabel = Label(self, text="PeakList: ", grid=(0, 0))
    self.peakListPulldown = PulldownList(self, grid=(0, 1), gridSpan=(1, 4), hAlign='l', callback=self._selectPeakList)
    self.peakListPulldown.setData([peakList.pid for peakList in project.peakLists])
    if current is not None and current.strip is not None and len(current.strip.spectra)>0:
      self.peakListPulldown.select(current.strip.spectra[0].peakLists[0].pid)
    self.peakList = project.getByPid(self.peakListPulldown.currentText())
    self.checkBoxWidget = QtGui.QWidget()
    layout = QtGui.QGridLayout()
    self.checkBoxWidget.setLayout(layout)
    self.layout().addWidget(self.checkBoxWidget, 1, 0, 1, 4)
    self.checkBox1 = RadioButton(self)
    self.checkBoxWidget.layout().addWidget(self.checkBox1, 0, 0)
    self.checkBox1Label = Label(self, 'Positive only')
    self.checkBoxWidget.layout().addWidget(self.checkBox1Label, 0, 1)
    self.checkBox2 = RadioButton(self)
    self.checkBoxWidget.layout().addWidget(self.checkBox2, 0, 2)
    self.checkBox2Label = Label(self, 'Negative only')
    self.checkBoxWidget.layout().addWidget(self.checkBox2Label, 0, 3)
    self.checkBox3 = RadioButton(self)
    self.checkBoxWidget.layout().addWidget(self.checkBox3, 0, 4)
    self.checkBox3Label = Label(self, 'Both')
    self.checkBoxWidget.layout().addWidget(self.checkBox3Label, 0, 5)
    self.checkBox3.setChecked(True)
    self._updateContents()

    self.buttonBox = ButtonList(self, grid=(7, 2), gridSpan=(1, 4), texts=['Cancel', 'Find Peaks'],
                                callbacks=[self.reject, self._pickPeaks])

  def _selectPeakList(self, item):
    self.peakList = self.project.getByPid(item)
    self._updateContents()

  def _pickPeaks(self):
    peakList = self.peakList
    positions = [[x.value(), y.value()] for x,y in zip(self.minPositionBoxes, self.maxPositionBoxes)]


    doPos=True
    doNeg=True
    if self.checkBox1.isChecked():
      # Positive only
      doNeg=False
    elif self.checkBox2.isChecked():
      # negative only
      doPos=False
    # Checking the third box turns the others off and sets both. Hence default
    peakList.pickPeaksNd(positions, doPos=doPos, doNeg=doNeg, fitMethod='gaussian')

    for strip in self.project.strips:
      strip.showPeaks(peakList)

    self.accept()

  def _updateContents(self):

    rowCount = self.layout().rowCount()
    colCount = self.layout().columnCount()

    for r in range(2, 7):
      for m in range(0, colCount):
        item = self.layout().itemAtPosition(r, m)
        if item:
          if item.widget():
            item.widget().hide()
        self.layout().removeItem(item)

    self.minPositionBoxes = []
    self.maxPositionBoxes = []


    for ii in range(self.peakList.spectrum.dimensionCount):
      dim1MinLabel = Label(self, text='F%s ' % str (ii+1) + self.peakList.spectrum.axisCodes[ii]+' min', grid=(2+ii, 0), vAlign='t')
      dim1MinDoubleSpinBox = DoubleSpinbox(self, grid=(2+ii, 1), vAlign='t')
      dim1MinDoubleSpinBox.setMinimum(self.peakList.spectrum.aliasingLimits[ii][0])
      dim1MinDoubleSpinBox.setMaximum(self.peakList.spectrum.aliasingLimits[ii][1])
      dim1MinDoubleSpinBox.setValue(self.peakList.spectrum.aliasingLimits[ii][0])
      dim1MaxLabel = Label(self, text='F%s ' % str (ii+1) + self.peakList.spectrum.axisCodes[ii]+' max', grid=(2+ii, 2), vAlign='t')
      dim1MaxDoubleSpinBox = DoubleSpinbox(self, grid=(2+ii, 3))
      dim1MaxDoubleSpinBox.setMinimum(self.peakList.spectrum.aliasingLimits[ii][0])
      dim1MaxDoubleSpinBox.setMaximum(self.peakList.spectrum.aliasingLimits[ii][1])
      dim1MaxDoubleSpinBox.setValue(self.peakList.spectrum.aliasingLimits[ii][1])
      self.minPositionBoxes.append(dim1MinDoubleSpinBox)
      self.maxPositionBoxes.append(dim1MaxDoubleSpinBox)
    # self.excludedRegionsButton = Button(self, grid=(self.peakList.spectrum.dimensionCount+3, 0), text='Exclude Regions')
    # self.excludedRegionsButton.setCheckable(True)
    # self.excludedRegionsButton.toggled.connect(self.toggleExcludedRegionsPopup)


  def _toggleExcludedRegionsPopup(self):

    if not hasattr(self, 'excludedRegionsPopup'):
      self.raiseExcludedRegionsPopup()
    else:
      if self.excludedRegionsButton.isChecked():
        self.excludedRegionsPopup.show()
      else:
        self.excludedRegionsPopup.hide()

  def raiseExcludedRegionsPopup(self):
    self.excludedRegionsPopup = ExcludeRegions(self, self.peakList)
    self.layout().addWidget(self.excludedRegionsPopup, 5, 0, 1, 4)

class ExcludeRegions(QtGui.QWidget, Base):
  def __init__(self, parent, peakList):
    super(ExcludeRegions, self).__init__(parent)
    self.regionCount = 0
    self.peakList = peakList
    self.addRegionButton = Button(self, text='Add Region', callback=self._addRegion, grid=(20, 0), gridSpan=(1, 3))
    self.removeRegionButton = Button(self, text='Remove Region', callback=self._removeRegion, grid=(20, 3), gridSpan=(1, 3))
    self.excludedRegions = []

  def _addRegion(self):
    self.regionCount+=1
    minRegion = []
    maxRegion = []
    for ii in range(self.peakList.spectrum.dimensionCount):
      print(self.peakList.spectrum.dimensionCount)
      dim1MinLabel = Label(self, text='F%s ' % str (1+ii) + self.peakList.spectrum.axisCodes[ii]+' min', grid=(1+ii*self.regionCount, 0), vAlign='t')
      dim1MinDoubleSpinBox = DoubleSpinbox(self, grid=(1+ii*self.regionCount, 1), vAlign='t')
      dim1MinDoubleSpinBox.setMinimum(self.peakList.spectrum.aliasingLimits[ii][0])
      dim1MinDoubleSpinBox.setMaximum(self.peakList.spectrum.aliasingLimits[ii][1])
      dim1MinDoubleSpinBox.setValue(self.peakList.spectrum.aliasingLimits[ii][0])
      minRegion.append(dim1MinDoubleSpinBox)
      dim1MaxLabel = Label(self, text='F%s ' % str (1+ii) + self.peakList.spectrum.axisCodes[ii]+' max', grid=(1+ii*self.regionCount, 2), vAlign='t')
      dim1MaxDoubleSpinBox = DoubleSpinbox(self, grid=(1+ii*self.regionCount, 3))
      dim1MaxDoubleSpinBox.setMinimum(self.peakList.spectrum.aliasingLimits[ii][0])
      dim1MaxDoubleSpinBox.setMaximum(self.peakList.spectrum.aliasingLimits[ii][1])
      dim1MaxDoubleSpinBox.setValue(self.peakList.spectrum.aliasingLimits[ii][1])
      maxRegion.append(dim1MaxDoubleSpinBox)

      # self.minPositionBoxes.append(dim1MinDoubleSpinBox)
      # self.maxPositionBoxes.append(dim1MaxDoubleSpinBox)
    self.excludedRegions.append([minRegion, maxRegion])
    self.regionCount+=1

  def _removeRegion(self):
    for i in range(5):
      item = self.layout().itemAtPosition(self.regionCount, i)
      # print(item, i, self.regionCount)
      # self.regionCount-=1

