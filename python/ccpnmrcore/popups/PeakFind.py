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
    self.peakList = project.getById(self.peakListPulldown.currentText())
    self.updateContents()



    self.buttonBox = ButtonList(self, grid=(5, 2), gridSpan=(1, 2), texts=['Cancel', 'Find Peaks'],
                           callbacks=[self.reject, self.findPeaks])


  def selectPeakList(self, item):
    print(item)
    self.peakList = self.project.getById(item)
    print('here')
    self.updateContents()

  def findPeaks(self):
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

    newPeaks = peakList.findPeaksNd(positions, apiSpectrumView.spectrumView.orderedDataDims,
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
    self.dim1MinDoubleSpinBox.setMaximum(1000)
    self.dim1MaxLabel = Label(self, text='F1 '+ self.peakList.spectrum.axisCodes[0]+' max', grid=(1, 2))
    self.dim1MaxDoubleSpinBox = DoubleSpinbox(self, grid=(1, 3))
    self.dim1MaxDoubleSpinBox.setMaximum(1000)
    self.dim2MinLabel = Label(self, text='F2 '+ self.peakList.spectrum.axisCodes[1]+' min', grid=(2, 0))
    self.dim2MinDoubleSpinBox = DoubleSpinbox(self, grid=(2, 1))
    self.dim2MinDoubleSpinBox.setMaximum(1000)
    self.dim2MaxLabel = Label(self, text='F2 '+ self.peakList.spectrum.axisCodes[1]+' max', grid=(2, 2))
    self.dim2MaxDoubleSpinBox = DoubleSpinbox(self, grid=(2, 3))
    self.dim2MaxDoubleSpinBox.setMaximum(1000)
    if self.peakList.spectrum.dimensionCount > 2:
      self.dim3MinLabel = Label(self, text='F3 '+ self.peakList.spectrum.axisCodes[2]+' min', grid=(3, 0))
      self.dim3MinDoubleSpinBox = DoubleSpinbox(self, grid=(3, 1))
      self.dim3MinDoubleSpinBox.setMaximum(1000)
      self.dim3MaxLabel = Label(self, text='F3 '+ self.peakList.spectrum.axisCodes[2]+' max', grid=(3, 2))
      self.dim3MaxDoubleSpinBox = DoubleSpinbox(self, grid=(3, 3))
      self.dim3MaxDoubleSpinBox.setMaximum(1000)

