"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
__author__ = 'simon'

from PyQt4 import QtGui, QtCore
from ccpncore.gui.Base import Base
from ccpncore.gui.Button import Button
from ccpncore.gui.ButtonList import ButtonList
from ccpncore.gui.DoubleSpinbox import DoubleSpinbox
from ccpncore.gui.Label import Label

from ccpncore.gui.PulldownList import PulldownList

LANGUAGES = ['English-UK', 'English-US', 'Nederlands', 'Deutsch', 'Español', 'Français', 'Dansk']
COLOUR_SCHEMES = ['light', 'dark']


class PeakFindPopup(QtGui.QDialog, Base):
  def __init__(self, parent=None, project=None, **kw):
    super(PeakFindPopup, self).__init__(parent)
    Base.__init__(self, **kw)
    self.project = project
    self.peakListLabel =  Label(self, text="PeakList: ", grid=(0, 0))
    self.peakListPulldown = PulldownList(self, grid=(0, 1), gridSpan=(1, 3), hAlign='l', callback=self.selectPeakList)
    # self.peakListPulldown.currentIndexChanged.connect(self.selectPeakList)
    self.peakListPulldown.setData([peakList.pid for peakList in project.peakLists])
    self.peakList = project.getByPid(self.peakListPulldown.currentText())
    self.updateContents()
    # self.excludedRegionsButton = Button(self, grid=(4, 0), text='Exclude Regions')
    # self.excludedRegionsButton.setCheckable(True)
    # self.excludedRegionsButton.toggled.connect(self.toggleExcludedRegionsPopup)




    self.buttonBox = ButtonList(self, grid=(15, 2), gridSpan=(1, 2), texts=['Cancel', 'Find Peaks'],
                           callbacks=[self.reject, self.pickPeaks])


  def selectPeakList(self, item):
    self.peakList = self.project.getByPid(item)
    self.updateContents()

  def pickPeaks(self):
    peakList = self.peakList
    spectralWidths = peakList.spectrum.spectralWidths
    offsets = peakList.spectrum.referenceValues
    apiSpectrumView = peakList.spectrum.spectrumViews[0]._wrappedData
    positions = [[self.dim1MinDoubleSpinBox.value(), self.dim2MinDoubleSpinBox.value()],
                 [self.dim1MaxDoubleSpinBox.value(), self.dim2MaxDoubleSpinBox.value()]]

    if self.peakList.spectrum.dimensionCount > 2:
      positions[0].append(self.dim3MinDoubleSpinBox.value())
      positions[1].append(self.dim3MaxDoubleSpinBox.value())
    apiSpectrumView = peakList.spectrum.spectrumViews[0]._wrappedData

    newPeaks = peakList.pickPeaksNd(positions, apiSpectrumView.spectrumView.orderedDataDims,
                                            doPos=apiSpectrumView.spectrumView.displayPositiveContours,
                                            doNeg=apiSpectrumView.spectrumView.displayNegativeContours)

    for strip in self.project.strips:
      strip.showPeaks(peakList)

    self.accept()

  def updateContents(self):
    try:
      for column in range(4):
        for row in range(1, 4):
          self.layout().itemAtPosition(row, column).widget().deleteLater()
    except AttributeError:
      pass

    self.dim1MinLabel = Label(self, text='F1 '+ self.peakList.spectrum.axisCodes[0]+' min', grid=(1, 0))
    self.dim1MinDoubleSpinBox = DoubleSpinbox(self, grid=(1, 1))
    self.dim1MinDoubleSpinBox.setMinimum(self.peakList.spectrum.spectrumLimits[0][0])
    self.dim1MinDoubleSpinBox.setMaximum(self.peakList.spectrum.spectrumLimits[0][1])
    self.dim1MinDoubleSpinBox.setValue(self.peakList.spectrum.spectrumLimits[0][0])
    self.dim1MaxLabel = Label(self, text='F1 '+ self.peakList.spectrum.axisCodes[0]+' max', grid=(1, 2))
    self.dim1MaxDoubleSpinBox = DoubleSpinbox(self, grid=(1, 3))
    self.dim1MinDoubleSpinBox.setMinimum(self.peakList.spectrum.spectrumLimits[0][0])
    self.dim1MaxDoubleSpinBox.setMaximum(self.peakList.spectrum.spectrumLimits[0][1])
    self.dim1MaxDoubleSpinBox.setValue(self.peakList.spectrum.spectrumLimits[0][1])
    self.dim2MinLabel = Label(self, text='F2 '+ self.peakList.spectrum.axisCodes[1]+' min', grid=(2, 0))
    self.dim2MinDoubleSpinBox = DoubleSpinbox(self, grid=(2, 1))
    self.dim2MinDoubleSpinBox.setMinimum(self.peakList.spectrum.spectrumLimits[1][0])
    self.dim2MinDoubleSpinBox.setMaximum(self.peakList.spectrum.spectrumLimits[1][1])
    self.dim2MinDoubleSpinBox.setValue(self.peakList.spectrum.spectrumLimits[1][0])
    self.dim2MaxLabel = Label(self, text='F2 '+ self.peakList.spectrum.axisCodes[1]+' max', grid=(2, 2))
    self.dim2MaxDoubleSpinBox = DoubleSpinbox(self, grid=(2, 3))
    self.dim2MaxDoubleSpinBox.setMinimum(self.peakList.spectrum.spectrumLimits[1][0])
    self.dim2MaxDoubleSpinBox.setMaximum(self.peakList.spectrum.spectrumLimits[1][1])
    self.dim2MaxDoubleSpinBox.setValue(self.peakList.spectrum.spectrumLimits[1][1])
    if self.peakList.spectrum.dimensionCount > 2:
      self.dim3MinLabel = Label(self, text='F3 '+ self.peakList.spectrum.axisCodes[2]+' min', grid=(3, 0))
      self.dim3MinDoubleSpinBox = DoubleSpinbox(self, grid=(3, 1))
      self.dim3MinDoubleSpinBox.setMinimum(self.peakList.spectrum.spectrumLimits[2][0])
      self.dim3MinDoubleSpinBox.setMaximum(self.peakList.spectrum.spectrumLimits[2][1])
      self.dim3MinDoubleSpinBox.setValue(self.peakList.spectrum.spectrumLimits[2][0])
      self.dim3MaxLabel = Label(self, text='F3 '+ self.peakList.spectrum.axisCodes[2]+' max', grid=(3, 2))
      self.dim3MaxDoubleSpinBox = DoubleSpinbox(self, grid=(3, 3))
      self.dim3MaxDoubleSpinBox.setMinimum(self.peakList.spectrum.spectrumLimits[2][0])
      self.dim3MaxDoubleSpinBox.setMaximum(self.peakList.spectrum.spectrumLimits[2][1])
      self.dim3MaxDoubleSpinBox.setValue(self.peakList.spectrum.spectrumLimits[2][1])


  def toggleExcludedRegionsPopup(self):

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

class ExcludeRegions(QtGui.QWidget):
  def __init__(self, parent, peakList):
    super(ExcludeRegions, self).__init__(parent)
    self.label1 = Label(self, text='Dim', grid=(0, 0))
    self.pulldownSolvents = PulldownList(self, grid=(0, 1))
    self.pulldownSolvents.setFixedWidth(100)
    self.peakList = peakList
    axisCodes = peakList.spectrum.axisCodes
    # self.pulldownSolvents.activated[str].connect(self.addRegions)
    self.pulldownSolvents.addItems(axisCodes)
    self.label2 = Label(self, text='min', grid=(0, 2))
    self.label2 = Label(self, text='max', grid=(0, 4))
    self.regionSpinBox1 = DoubleSpinbox(self, grid=(0, 3))
    self.regionSpinBox2 = DoubleSpinbox(self, grid=(0, 5))
    self.regionCount = 1
    self.addRegionButton = Button(self, text='Add Region', callback=self.addRegion, grid=(20, 0), gridSpan=(1, 3))
    self.removeRegionButton = Button(self, text='Remove Region', callback=self.removeRegion, grid=(20, 3), gridSpan=(1, 3))
    # print(self.layout(), self.layout().items())

  def addRegion(self):

    self.label1 = Label(self, text='Dim', grid=(self.regionCount, 0))
    self.pulldownSolvents = PulldownList(self, grid=(self.regionCount, 1))
    self.pulldownSolvents.setFixedWidth(100)
    axisCodes = self.peakList.spectrum.axisCodes
    # self.pulldownSolvents.activated[str].connect(self.addRegions)
    self.pulldownSolvents.addItems(axisCodes)
    self.label2 = Label(self, text='min', grid=(self.regionCount, 2))
    self.label2 = Label(self, text='max', grid=(self.regionCount, 4))
    self.regionSpinBox1 = DoubleSpinbox(self, grid=(self.regionCount, 3))
    self.regionSpinBox2 = DoubleSpinbox(self, grid=(self.regionCount, 5))
    self.regionCount+=1

  def removeRegion(self):
    for i in range(5):
      item = self.layout().itemAtPosition(self.regionCount, i)
      # print(item, i, self.regionCount)
      # self.regionCount-=1

