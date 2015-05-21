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
from PyQt4 import QtGui, QtCore

from ccpncore.gui.Base import Base
from ccpncore.gui.Button import Button
from ccpncore.gui.ColourDialog import ColourDialog
from ccpncore.util.Colour import spectrumColours
from ccpncore.lib.spectrum.Util import getSpectrumFileFormat
from ccpncore.gui.Label import Label
from ccpncore.gui.LineEdit import LineEdit
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.CheckBox import CheckBox
from ccpncore.gui.Spinbox import Spinbox
from ccpncore.gui.DoubleSpinbox import DoubleSpinbox


from functools import partial

import sys

DIMENSIONS = ['X', 'Y', 'Z', 'Z2']
SPECTRA = ['1H', 'STD', 'Relaxation Filtered', 'Water LOGSY']
SAMPLE_STATES = ['liquid', 'solid', 'ordered', 'powder', 'crystal']
VOLUME_UNITS = ['μl', 'ml', 'l']


class SpectrumPropertiesPopup(QtGui.QDialog):
  def __init__(self, spectrum=None, parent=None, **kw):
    super(SpectrumPropertiesPopup, self).__init__(parent)
    Base.__init__(self, **kw)
    tabWidget = QtGui.QTabWidget()
    if spectrum.dimensionCount == 1:
      tabWidget.addTab(GeneralTab(spectrum), "General")
      tabWidget.addTab(DimensionsTab(spectrum, spectrum.dimensionCount), "Dimensions")
      tabWidget.addTab(PeakListsTab(spectrum), "Peak Lists")
      tabWidget.addTab(AcquisitionTab(spectrum), "Spectrometer")

    else:
      tabWidget.addTab(GeneralTab(spectrum), "General")
      tabWidget.addTab(DimensionsTab(spectrum, spectrum.dimensionCount), "Dimensions")
      tabWidget.addTab(ContoursTab(spectrum), "Contours")
      tabWidget.addTab(PeakListsTab(spectrum), "Peak Lists")
      tabWidget.addTab(AcquisitionTab(spectrum), "Spectrometer")


    self.setWindowTitle("Spectrum Information")
    buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)

    buttonBox.accepted.connect(self.accept)
    buttonBox.rejected.connect(self.reject)

    mainLayout = QtGui.QVBoxLayout()
    mainLayout.addWidget(tabWidget)
    mainLayout.addWidget(buttonBox)
    self.setLayout(mainLayout)

  def keyPressEvent(self, event):
    if event.key() == QtCore.Qt.Key_Enter:
      pass



class GeneralTab(QtGui.QWidget, Base):
  def __init__(self, spectrum, parent=None):
    super(GeneralTab, self).__init__(parent)

    self.spectrum = spectrum
    # nameLabel = (Label(self, text="Spectrum name: ", grid=(0,0)))
    # nameData = LineEdit(self, grid=(0, 1))
    # nameData.setText(spectrum.spectrumItem.name)
    pathLabel = Label(self, text="Path:", grid=(1, 0))
    self.pathData = LineEdit(self, grid=(1, 1))
    self.pathData.setText(spectrum.filePath)
    self.pathData.editingFinished.connect(self.setSpectrumPath)
    dataTypeLabel = Label(self, text="Data Type: ", grid=(2, 0))
    dataTypeData = Label(self, text=getSpectrumFileFormat(spectrum.filePath), grid=(2, 1))
    templateLabel = Label(self, text="Template: ", grid=(3, 0))
    dateLabel = Label(self, text="Date: ", grid=(4, 0))
    pidLabel = Label(self, text="PID: ", grid=(5, 0))
    pidData = Label(self, text=spectrum.pid, grid=(5, 1))
    if spectrum.dimensionCount == 1:
      colourLabel = Label(self, text="Colour", grid=(6,0))
      self.colourBox = PulldownList(self, grid=(6, 1))
      for item in spectrumColours.items():
        pix=QtGui.QPixmap(QtCore.QSize(20,20))
        pix.fill(QtGui.QColor(item[0]))
        self.colourBox.addItem(icon=QtGui.QIcon(pix), text=item[1])
      self.colourBox.setCurrentIndex(list(spectrumColours.keys()).index(spectrum.sliceColour))
      self.colourBox.currentIndexChanged.connect(partial(self.changedColourComboIndex, spectrum))
      colourButton = Button(self, text="More...", grid=(6, 2), callback=partial(self.changeSpectrumColour, spectrum))
      # colourButton.clicked.connect(partial(self.changeSpectrumColour, spectrum))
      spectrumTypeLabel = Label(self, text="Spectrum Type: ", grid=(7, 0))
      spectrumType = PulldownList(self, grid=(7, 1))
      spectrumType.addItems(SPECTRA)
      spectrumType.addItem(spectrum.experimentName)
      spectrumType.setCurrentIndex(spectrumType.findText(spectrum.experimentName))
      pulseProgramLabel = Label(self, text="Pulse Program: ", grid=(8, 0))
      recordingDataLabel = Label(self, text="Date Recorded", grid=(9, 0))
      minimumValueLabel = Label(self, text="Minimum Value: ", grid=(10, 0))
      maximumValueLabel = Label(self, text="Maximum Value: ", grid=(11, 0))
      noiseLevelLabel = Label(self, text="Noise Level: ", grid=(12, 0))
      noiseLevelData = LineEdit(self, )
      if spectrum.apiDataSource.noiseLevel is not None:
        noiseLevelData.setText(str('%.3d' % spectrum.apiDataSource.noiseLevel))
      else:
        noiseLevelData.setText('None')
    else:
      spectrumTypeLabel = Label(self, text="Spectrum Type: ", grid=(6, 0))
      # spectrumType = PulldownList(self, grid=(6, 1))
      # spectrumType.addItems(SPECTRA)
      # spectrumType.addItem(spectrum.experimentName)
      # spectrumType.setCurrentIndex(spectrumType.findText(spectrum.experimentName))
      pulseProgramLabel = Label(self, text="Pulse Program: ", grid=(7, 0))
      recordingDataLabel = Label(self, text="Date Recorded", grid=(8, 0))
      minimumValueLabel = Label(self, text="Minimum Value: ", grid=(9, 0))
      maximumValueLabel = Label(self, text="Maximum Value: ", grid=(10, 0))
      noiseLevelLabel = Label(self, text="Noise Level: ", grid=(11, 0))
      noiseLevelData = LineEdit(self, grid=(11, 1))
      if spectrum.apiDataSource.noiseLevel is not None:
        noiseLevelData.setText(str('%.3d' % spectrum.apiDataSource.noiseLevel))
      else:
        noiseLevelData.setText('None')



  def setSpectrumPath(self):
    if self.pathData.isModified():
      self.spectrum.filePath = self.pathData.text()
      print(self.spectrum.filePath)


  def changeSpectrumColour(self, spectrum):
    dialog = ColourDialog()
    newColour = dialog.getColor()
    # palette = QtGui.QPalette(spectrum.guispectrumView.toolBarButton.palette())
    # palette.setColor(QtGui.QPalette.Button,spectrum.spectrumView.colour)
    spectrum.apiDataSource.setSliceColour(newColour.name())
    spectrum.guiSpectrumView.plot.setPen(spectrum.apiDataSource.sliceColour)
    pix=QtGui.QPixmap(QtCore.QSize(20,20))
    pix.fill(QtGui.QColor(newColour))
    newIndex = str(len(spectrumColours.items())+1)
    self.colourBox.addItem(icon=QtGui.QIcon(pix), text='Colour %s' % newIndex)
    spectrumColours[newColour.name()] = 'Colour %s' % newIndex
    self.colourBox.setCurrentIndex(int(newIndex)-1)
    pix=QtGui.QPixmap(60,10)
    pix.fill(newColour)
    newIcon = QtGui.QIcon(pix)
    # spectrum.guiSpectrumView.newAction.setIcon(newIcon)

  def changedColourComboIndex(self, spectrum, value):

    spectrum.sliceColour = list(spectrumColours.keys())[value]
    # for spectrumView in spectrum.spectrumViews:
    #   print(dir(spectrumView))
    #   spectrumView.plot.setPen(QtGui.QColor(spectrum.apiDataSource.sliceColour))
    pix=QtGui.QPixmap(60,10)
    pix.fill(QtGui.QColor(spectrum.sliceColour))
    newIcon = QtGui.QIcon(pix)
    # spectrum.guiSpectrumView.newAction.setIcon(newIcon)



class DimensionsTab(QtGui.QWidget):
  def __init__(self, spectrum, dimensions, parent=None):
    super(DimensionsTab, self).__init__(parent)

    layout = QtGui.QGridLayout()
    dimensionalityLabel = Label(self, text="Dimensionality", grid=(0, 0))
    dimensionality = Label(self, text=str(dimensions)+"D", grid=(0, 1))
    j = 2
    for i in range(dimensions):
      axisLabel = Label(self, text=DIMENSIONS[i]+"-Label", grid=(j, 0))
      axisLabelData = Label(self, text=str(spectrum.isotopeCodes[i]), grid=(j, 1))
      pointsLabel = Label(self, text=DIMENSIONS[i]+"-Points", grid=(j+1, 0))
      pointsData = Label(self, text=str(spectrum.pointCounts[i]), grid=(j+1, 1))
      axisTypeLabel = Label(self, text=DIMENSIONS[i]+"-Type", grid=(j+2, 0))
      axisTypeData = Label(self, text=spectrum.dimensionTypes[i], grid=(j+2, 1))
      spectralWidthLabel = Label(self, text=DIMENSIONS[i]+"-Spectral Width (ppm)", grid=(j+3, 0))
      spectralWidthData = Label(self, text=str("%.3f" % spectrum.spectralWidths[i]), grid=(j+3, 1))
      spectralWidthHzLabel = Label(self, text=DIMENSIONS[i]+"-Spectral Width (Hz)", grid=(j+4, 0))
      spectralWidthHzData = Label(self, text=str("%.3f" % spectrum.spectralWidthsHz[i]), grid=(j+4, 1))
      spectralReferencingLabel = Label(self, text=DIMENSIONS[i]+"-Referencing", grid=(j+6, 0))
      spectralReferencingData = LineEdit(self, text=str("%.3f" % spectrum.referenceValues[i]), grid=(j+6, 1))
      spectralAssignmentToleranceLabel = Label(self, text=DIMENSIONS[i]+"-Assignment Tolerance", grid=(j+7, 0))
      spectralAssignmentToleranceData = LineEdit(self, grid=(j+7, 1))
      spectralShiftWeightingLabel = Label(self, text=DIMENSIONS[i]+"-Shift Weighting", grid=(j+8, 0))
      spectralShiftWeightingData = LineEdit(self, grid=(j+8, 1))
      j+=9



    # for i in range(dimensions):

class ContoursTab(QtGui.QWidget):
  def __init__(self, spectrum, parent=None):
    super(ContoursTab, self).__init__(parent)

    self.spectrum = spectrum
    positiveContoursLabel = Label(self, text="Show Positive Contours", grid=(0, 0))
    positiveContoursCheckBox = CheckBox(self, grid=(0, 1), checked=True)
    for spectrumView in self.spectrum.spectrumViews:
      if spectrumView._wrappedData.displayPositiveContours is True:
        positiveContoursCheckBox.setChecked(True)
      else:
        positiveContoursCheckBox.setChecked(False)

    positiveContoursCheckBox.stateChanged.connect(self.changePositiveContourDisplay)
    positiveBaseLevelLabel = Label(self, text="Positive Base Level", grid=(1, 0))
    positiveBaseLevelData = DoubleSpinbox(self, grid=(1, 1))
    positiveBaseLevelData.setMaximum(1e12)
    positiveBaseLevelData.setMinimum(0)
    positiveBaseLevelData.setValue(spectrum.positiveContourBase)
    positiveBaseLevelData.valueChanged.connect(partial(self.lineEditTextChanged1, spectrum))
    positiveMultiplierLabel = Label(self, text="Positive Multiplier", grid=(2, 0))
    positiveMultiplierData = DoubleSpinbox(self, grid=(2, 1))
    positiveMultiplierData.setSingleStep(0.1)
    positiveMultiplierData.setValue(float(spectrum.positiveContourFactor))
    positiveMultiplierData.valueChanged.connect(partial(self.lineEditTextChanged2, spectrum))
    positiveBaseLevelData.setSingleStep(positiveBaseLevelData.value()*(positiveMultiplierData.value()-1))
    positiveContourCountLabel = Label(self, text="Number of positive contours", grid=(3, 0))
    positiveContourCountData = Spinbox(self, grid=(3, 1))
    positiveContourCountData.setValue(int(spectrum.apiDataSource.positiveContourCount))
    positiveContourCountData.valueChanged.connect(partial(self.lineEditTextChanged3, spectrum))
    positiveContourColourLabel = Label(self, text="Positive Contour Colour",grid=(4, 0))
    self.positiveColourBox = PulldownList(self, grid=(4, 1))
    for item in spectrumColours.items():
      pix=QtGui.QPixmap(QtCore.QSize(20,20))
      pix.fill(QtGui.QColor(item[0]))
      self.positiveColourBox.addItem(icon=QtGui.QIcon(pix), text=item[1])
    try:
      self.positiveColourBox.setCurrentIndex(list(spectrumColours.keys()).index(spectrum.positiveContourColour))
      self.positiveColourBox.currentIndexChanged.connect(partial(self.changePosColourComboIndex, spectrum))
    except ValueError:
      pass
    self.positiveColourButton = Button(self, text="More...", grid=(4, 2))
    self.positiveColourButton.clicked.connect(partial(self.changePosSpectrumColour, spectrum))


    negativeContoursLabel = Label(self, text="Show Negative Contours", grid=(6 ,0))
    negativeContoursCheckBox = CheckBox(self, grid=(6, 1), checked=True)
    for spectrumView in self.spectrum.spectrumViews:
      if spectrumView._wrappedData.displayNegativeContours is True:
        negativeContoursCheckBox.setChecked(True)
      else:
        negativeContoursCheckBox.setChecked(False)
    negativeContoursCheckBox.stateChanged.connect(self.displayNegativeContours)
    negativeBaseLevelLabel = Label(self, text="Negative Base Level", grid=(7, 0))
    negativeBaseLevelData = DoubleSpinbox(self, grid=(7, 1))
    negativeBaseLevelData.setMaximum(0)
    negativeBaseLevelData.setMinimum(-1e12)
    negativeBaseLevelData.setValue(spectrum.negativeContourBase)
    negativeBaseLevelData.valueChanged.connect(partial(self.lineEditTextChanged4, spectrum))
    negativeMultiplierLabel = Label(self, text="Multiplier", grid=(8, 0))
    negativeMultiplierData = DoubleSpinbox(self, grid=(8, 1))
    negativeMultiplierData.setValue(spectrum.negativeContourFactor)
    negativeMultiplierData.setSingleStep(0.1)
    negativeMultiplierData.valueChanged.connect(partial(self.lineEditTextChanged5, spectrum))
    negativeContourCountLabel = Label(self, text="Number of contours", grid=(9, 0))
    negativeContourCountData = Spinbox(self, grid=(9, 1))
    negativeContourCountData.setValue(spectrum.negativeContourCount)
    negativeContourCountData.valueChanged.connect(partial(self.lineEditTextChanged6, spectrum))
    negativeContourColourLabel = Label(self, text="Colour",grid=(10, 0))
    self.negativeColourBox = PulldownList(self, grid=(10, 1))
    for item in spectrumColours.items():
      pix=QtGui.QPixmap(QtCore.QSize(20,20))
      pix.fill(QtGui.QColor(item[0]))
      self.negativeColourBox.addItem(icon=QtGui.QIcon(pix), text=item[1])
    try:
      self.negativeColourBox.setCurrentIndex(list(spectrumColours.keys()).index(spectrum.negativeContourColour))
      self.negativeColourBox.currentIndexChanged.connect(partial(self.changeNegColourComboIndex, spectrum))
    except ValueError:
      pass

    self.negativeColourButton = Button(self, text="More...", grid=(10, 2))
    self.negativeColourButton.clicked.connect(partial(self.changeNegSpectrumColour, spectrum))


  def changePositiveContourDisplay(self, state):
    if state == QtCore.Qt.Checked:
      for spectrumView in self.spectrum.spectrumViews:
        spectrumView._wrappedData.displayPositiveContours = True
    else:
      for spectrumView in self.spectrum.spectrumViews:
        spectrumView._wrappedData.displayPositiveContours = False

  def displayNegativeContours(self, state):
    if state == QtCore.Qt.Checked:
      for spectrumView in self.spectrum.spectrumViews:
        spectrumView.displayNegativeContours = True
    else:
      for spectrumView in self.spectrum.spectrumViews:
        spectrumView.displayNegativeContours = False


  def lineEditTextChanged1(self, spectrum, value):
    spectrum.positiveContourBase = float(value)
    # spectrum.spectrumItem.levels = spectrum.spectrumItem.getLevels()

  def lineEditTextChanged2(self, spectrum, value):
    spectrum.positiveContourFactor = float(value)

  def lineEditTextChanged3(self, spectrum, value):
    spectrum.positiveContourCount = int(value)

  def lineEditTextChanged4(self, spectrum, value):
    spectrum.negativeContourBase = float(value)
    # spectrum.spectrumItem.levels = spectrum.spectrumItem.getLevels()

  def lineEditTextChanged5(self, spectrum, value):
    spectrum.negativeContourFactor = float(value)

  def lineEditTextChanged6(self, spectrum, value):
    spectrum.negativeContourCount = int(value)

  def changePosSpectrumColour(self, spectrum):
    dialog = ColourDialog()
    newColour = dialog.getColor()
    spectrum.positiveContourColour = newColour.name()
    pix=QtGui.QPixmap(QtCore.QSize(20,20))
    pix.fill(QtGui.QColor(newColour))
    newIndex = str(len(spectrumColours.items())+1)
    self.positiveColourBox.addItem(icon=QtGui.QIcon(pix), text='Colour %s' % newIndex)
    self.negativeColourBox.addItem(icon=QtGui.QIcon(pix), text='Colour %s' % newIndex)
    spectrumColours[newColour.name()] = 'Colour %s' % newIndex
    self.positiveColourBox.setCurrentIndex(int(newIndex)-1)
    pix=QtGui.QPixmap(60,10)
    pix.fill(newColour)
    newIcon = QtGui.QIcon(pix)
    for spectrumView in spectrum.spectrumViews:
      spectrumView.newAction.setIcon(newIcon)
    

  def changeNegSpectrumColour(self, spectrum):
    dialog = ColourDialog()
    newColour = dialog.getColor()
    spectrum.negativeContourColour = newColour.name()
    pix=QtGui.QPixmap(QtCore.QSize(20,20))
    pix.fill(QtGui.QColor(newColour))
    newIndex = str(len(spectrumColours.items())+1)
    self.negativeColourBox.addItem(icon=QtGui.QIcon(pix), text='Colour %s' %newIndex)
    self.positiveColourBox.addItem(icon=QtGui.QIcon(pix), text='Colour %s' %newIndex)
    spectrumColours[newColour.name()] = 'Colour %s' % newIndex
    self.negativeColourBox.setCurrentIndex(int(newIndex)-1)


  def changePosColourComboIndex(self, spectrum, value):

    newColour = list(spectrumColours.keys())[value]
    spectrum.positiveContourColour = newColour
    pix=QtGui.QPixmap(60,10)
    pix.fill(QtGui.QColor(newColour))
    newIcon = QtGui.QIcon(pix)
    # spectrum.spectrumItem.newAction.setIcon(newIcon)



  def changeNegColourComboIndex(self, spectrum, value):

    newColour = list(spectrumColours.keys())[value]
    spectrum.apiDataSource.negativeContourColour = newColour
    pix=QtGui.QPixmap(60,10)
    pix.fill(QtGui.QColor(newColour))
    newIcon = QtGui.QIcon(pix)
    # spectrum.spectrumItem.newAction.setIcon(newIcon)


class PeakListsTab(QtGui.QWidget):
  def __init__(self, spectrum, parent=None):
    super(PeakListsTab, self).__init__(parent)
    #
    i=0
    for peakList in spectrum.peakLists:
      label = Label(self, text=str(peakList.pid), grid=(i, 1))
      checkBox = CheckBox(self, grid=(i, 0), checked=True)
    #   # if spectrum.spectrumItem.peakListItems[peakList.pid].displayed == True:
    #   #   checkBox.setChecked(True)
    #   # else:
    #   #   checkBox.setChecked(False)
    #   #
    #   # checkBox.stateChanged.connect(lambda: self.peakListToggle(spectrum.spectrumItem, checkBox.checkState(),peakList))
    #   # i+=1


class AcquisitionTab(QtGui.QWidget):
  def __init__(self, spectrum, parent=None):
      super(AcquisitionTab, self).__init__(parent)

      spectrometerLabel = Label(self, text="Acquisition: ", grid=(0, 0))
      spectrometerData = LineEdit(self, grid=(0, 1))
      probeLabel = Label(self, text="Probe: ",grid=(1, 0))
      probeData = LineEdit(self, grid=(1, 1))
      numberScansLabel = Label(self, text="Number of Scans: ", grid=(2, 0))
      numberScansData = LineEdit(self, grid=(2, 1))
      sampleStateLabel = Label(self, text="Sample State: ", grid=(3, 0))
      sampleStateData = PulldownList(self, grid=(3, 1))
      sampleStateData.addItems(SAMPLE_STATES)
      sampleVolumeLabel = Label(self, text="Sample Volume: ", grid=(4, 0))
      sampleVolumeData = LineEdit(self, grid=(4, 1))
      volumeUnitLabel = Label(self, text="Volume Unit")
      volumeUnitData = PulldownList(self)
      volumeUnitData.addItems(VOLUME_UNITS)
      tubeTypeLabel = Label(self, text="NMR Tube Type: ", grid=(5, 0))
      tubeTypeData = LineEdit(self, grid=(5, 1))
      spinningAngleLabel = Label(self, text="Spinning Angle: ", grid=(6, 0))
      spinningAngleData = LineEdit(self, grid=(6, 1))
      spinningRateLabel = Label(self, text="Spinning Rate: ", grid=(7, 0))
      spinningRateData = LineEdit(self, grid=(7, 1))



