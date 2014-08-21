from PySide import QtGui, QtCore

# from ccpncore.gui.Base import Base
from ccpncore.gui.Button import Button
from ccpncore.gui.ColourDialog import ColourDialog
from ccpnmrcore.modules.SpectrumPane import SPECTRUM_COLOURS
from ccpncore.lib.spectrum.Util import getSpectrumFileFormat

from functools import partial

import sys

DIMENSIONS = ['X', 'Y', 'Z', 'A']
SPECTRA = ['1H', 'STD', 'Relaxation Filtered', 'Water LOGSY']
SAMPLE_STATES = ['liquid', 'solid', 'ordered', 'powder', 'crystal']
VOLUME_UNITS = ['μl', 'ml', 'l']

class SpectrumPropertiesPopup(QtGui.QDialog):
  def __init__(self, spectrum=None, parent=None):
    super(SpectrumPropertiesPopup, self).__init__(parent)

    tabWidget = QtGui.QTabWidget()
    if spectrum.dimensionCount == 1:
      tabWidget.addTab(GeneralTab(spectrum), "General")
      tabWidget.addTab(DimensionsTab(spectrum, spectrum.dimensionCount), "Dimensions")
      tabWidget.addTab(PeakListsTab(spectrum), "Peak Lists")
      # tabWidget.addTab(AcquisitionTab(spectrum), "Spectrometer")

    else:
      tabWidget.addTab(GeneralTab(spectrum), "General")
      tabWidget.addTab(DimensionsTab(spectrum, spectrum.dimensionCount), "Dimensions")
      tabWidget.addTab(ContoursTab(spectrum), "Contours")
      tabWidget.addTab(PeakListsTab(spectrum), "Peak Lists")
      # tabWidget.addTab(AcquisitionTab(spectrum), "Spectrometer")

    self.setWindowTitle("Spectrum Information")
    buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)

    buttonBox.accepted.connect(self.accept)
    buttonBox.rejected.connect(self.reject)

    mainLayout = QtGui.QVBoxLayout()
    mainLayout.addWidget(tabWidget)
    mainLayout.addWidget(buttonBox)
    self.setLayout(mainLayout)



class GeneralTab(QtGui.QWidget):
  def __init__(self, spectrum, parent=None):
    super(GeneralTab, self).__init__(parent)

    layout = QtGui.QGridLayout()
    pathLabel = QtGui.QLabel("Path:")
    pathData = QtGui.QLineEdit()
    pathData.setText(spectrum.filePath)
    dataTypeLabel = QtGui.QLabel("Data Type: ")
    dataTypeData = QtGui.QLabel(getSpectrumFileFormat(spectrum.filePath))
    templateLabel = QtGui.QLabel("Template: ")
    dateLabel = QtGui.QLabel("Date: ")
    pidLabel = QtGui.QLabel("PID: ")
    pidData = QtGui.QLabel(spectrum.pid)
    spectrumTypeLabel = QtGui.QLabel("Spectrum Type: ")
    colourLabel = QtGui.QLabel("Colour")
    colourBox = QtGui.QComboBox()
    for item in SPECTRUM_COLOURS.items():
      pix=QtGui.QPixmap(QtCore.QSize(20,20))
      pix.fill(QtGui.QColor(item[0]))
      colourBox.addItem(QtGui.QIcon(pix), item[1])
    # colourBox.setCurrentIndex(list(SPECTRUM_COLOURS.keys()).index(spectrum.spectrumItem.colour.name()))
    # colourButton = QtGui.QPushButton(text="More...")
    # colourButton.clicked.connect(partial(self.changeSpectrumColour, spectrum))
    spectrumType = QtGui.QComboBox()
    spectrumType.addItems(SPECTRA)
    spectrumType.addItem(spectrum.experimentName)
    spectrumType.setCurrentIndex(spectrumType.findText(spectrum.experimentName))
    pulseProgramLabel = QtGui.QLabel("Pulse Program: ")
    recordingDataLabel = QtGui.QLabel("Date Recorded")
    minimumValueLabel = QtGui.QLabel("Minimum Value: ")
    maximumValueLabel = QtGui.QLabel("Maximum Value: ")
    noiseLevelLabel = QtGui.QLabel("Noise Level: ")
    noiseLevelData = QtGui.QLineEdit()
    if spectrum.ccpnSpectrum.noiseLevel is not None:
      noiseLevelData.setText(str('%.3d' % spectrum.ccpnSpectrum.noiseLevel))
    else:
      noiseLevelData.setText('None')

    layout.addWidget(pathLabel, 1, 0)
    layout.addWidget(pathData, 1, 1)
    layout.addWidget(dataTypeLabel, 2, 0)
    layout.addWidget(dataTypeData, 2, 1)
    layout.addWidget(templateLabel, 3, 0)
    layout.addWidget(dateLabel, 4, 0)
    layout.addWidget(pidLabel, 5, 0)
    layout.addWidget(pidData, 5, 1)
    if spectrum.dimensionCount == 1:
      layout.addWidget(colourLabel, 6, 0)
      layout.addWidget(colourBox, 6, 1)
      # layout.addWidget(colourButton, 6, 2)
      layout.addWidget(spectrumTypeLabel, 7, 0)
      layout.addWidget(spectrumType, 7, 1)
      layout.addWidget(pulseProgramLabel, 8, 0)
      layout.addWidget(minimumValueLabel, 9, 0)
      layout.addWidget(maximumValueLabel, 10, 0)
      layout.addWidget(noiseLevelLabel, 11, 0)
      layout.addWidget(noiseLevelData, 11, 1)
    else:
      layout.addWidget(spectrumTypeLabel, 6, 0)
      layout.addWidget(spectrumType, 6, 1)
      layout.addWidget(pulseProgramLabel, 7, 0)
      layout.addWidget(minimumValueLabel, 8, 0)
      layout.addWidget(maximumValueLabel, 9, 0)
      layout.addWidget(noiseLevelLabel, 10, 0)
      layout.addWidget(noiseLevelData, 10, 1)

    self.setLayout(layout)

  def changeSpectrumColour(self, spectrum):
    dialog = ColourDialog()
    spectrum.spectrumItem.colour = dialog.getColor()
    palette = QtGui.QPalette(spectrum.spectrumItem.toolBarButton.palette())
    palette.setColor(QtGui.QPalette.Button,spectrum.spectrumItem.colour)
    spectrum.spectrumItem.toolBarButton.setPalette(palette)
    spectrum.spectrumItem.plot.setPen(spectrum.spectrumItem.colour)

  def changedColourComboIndex(self, spectrum, value):

    spectrum.spectrumItem.colour = QtGui.QColor(list(SPECTRUM_COLOURS.keys())[value])
    print(QtGui.QColor(list(SPECTRUM_COLOURS.keys())[value]))
    palette = QtGui.QPalette(spectrum.spectrumItem.toolBarButton.palette())
    palette.setColor(QtGui.QPalette.Button,spectrum.spectrumItem.colour)
    spectrum.spectrumItem.toolBarButton.setPalette(palette)
    spectrum.spectrumItem.plot.setPen(spectrum.spectrumItem.colour)

class DimensionsTab(QtGui.QWidget):
  def __init__(self, spectrum, dimensions, parent=None):
    super(DimensionsTab, self).__init__(parent)

    layout = QtGui.QGridLayout()
    dimensionalityLabel = QtGui.QLabel("Dimensionality")
    dimensionality = QtGui.QLabel(str(dimensions)+"D")
    layout.addWidget(dimensionalityLabel, 0, 0)
    layout.addWidget(dimensionality, 0, 1)
    j = 2
    for i in range(dimensions):
      axisLabel = QtGui.QLabel(DIMENSIONS[i]+"-Label")
      axisLabelData = QtGui.QLabel(str(spectrum.isotopeCodes[i]))
      pointsLabel = QtGui.QLabel(DIMENSIONS[i]+"-Points")
      pointsData = QtGui.QLabel(str(spectrum.pointCounts[i]))
      axisTypeLabel = QtGui.QLabel(DIMENSIONS[i]+"-Type")
      axisTypeData = QtGui.QLabel(spectrum.dimensionTypes[i])
      spectralWidthLabel = QtGui.QLabel(DIMENSIONS[i]+"-Spectral Width (ppm)")
      spectralWidthData = QtGui.QLabel(str("%.3f" % spectrum.spectralWidths[i]))
      spectralWidthHzLabel = QtGui.QLabel(DIMENSIONS[i]+"-Spectral Width (Hz)")
      spectralWidthHzData = QtGui.QLabel(str("%.3f" % spectrum.spectralWidthsHz[i]))
      spectralReferencingLabel = QtGui.QLabel(DIMENSIONS[i]+"-Referencing")
      spectralReferencingData = QtGui.QLineEdit()
      spectralReferencingData.setText(str("%.3f" % spectrum.referenceValues[i]))
      spectralAssignmentToleranceLabel = QtGui.QLabel(DIMENSIONS[i]+"-Assignment Tolerance")
      spectralAssignmentToleranceData = QtGui.QLineEdit()
      spectralShiftWeightingLabel = QtGui.QLabel(DIMENSIONS[i]+"-Shift Weighting")
      spectralShiftWeightingData = QtGui.QLineEdit()

      layout.addWidget(axisLabel, j, 0)
      layout.addWidget(axisLabelData, j, 1)
      layout.addWidget(pointsLabel, j+1, 0)
      layout.addWidget(pointsData, j+1, 1)
      layout.addWidget(axisTypeLabel, j+2, 0)
      layout.addWidget(axisTypeData, j+2, 1)
      layout.addWidget(spectralWidthLabel, j+3, 0)
      layout.addWidget(spectralWidthData, j+3, 1)
      layout.addWidget(spectralWidthHzLabel, j+4, 0)
      layout.addWidget(spectralWidthHzData, j+4, 1)
      layout.addWidget(spectralReferencingLabel, j+5, 0)
      layout.addWidget(spectralReferencingData, j+5, 1)
      layout.addWidget(spectralAssignmentToleranceLabel, j+6, 0)
      layout.addWidget(spectralAssignmentToleranceData, j+6, 1)
      layout.addWidget(spectralShiftWeightingLabel, j+7, 0)
      layout.addWidget(spectralShiftWeightingData, j+7, 1)
      j+=8


    self.setLayout(layout)

    # for i in range(dimensions):

class ContoursTab(QtGui.QWidget):
  def __init__(self, spectrum, parent=None):
    super(ContoursTab, self).__init__(parent)

    layout = QtGui.QGridLayout()
    positiveContoursLabel = QtGui.QLabel("Show Positive Levels")
    positiveContoursCheckBox = QtGui.QCheckBox()
    positiveBaseLevelLabel = QtGui.QLabel("Base Level")
    positiveBaseLevelData = QtGui.QLineEdit()
    positiveMultiplierLabel = QtGui.QLabel("Multiplier")
    positiveMultiplierData = QtGui.QLineEdit()
    positiveContourCountLabel = QtGui.QLabel("Number of contours")
    positiveContourCountData = QtGui.QLineEdit()
    positiveContourColourLabel = QtGui.QLabel("Colour")
    # positiveContoursColourPulldown = QtGui.Q



    negativeContoursLabel = QtGui.QLabel("Show Negative Levels")
    negativeContoursCheckBox = QtGui.QCheckBox()
    negativeBaseLevelLabel = QtGui.QLabel("Base Level")
    negativeBaseLevelData = QtGui.QLineEdit()
    negativeMultiplierLabel = QtGui.QLabel("Multiplier")
    negativeMultiplierData = QtGui.QLineEdit()
    negativeContourCountLabel = QtGui.QLabel("Number of contours")
    negativeContourCountData = QtGui.QLineEdit()

    layout.addWidget(positiveContoursLabel, 0, 0)
    layout.addWidget(positiveContoursCheckBox, 0, 1)
    layout.addWidget(positiveBaseLevelLabel, 1, 0)
    layout.addWidget(positiveBaseLevelData, 1, 1)
    layout.addWidget(positiveMultiplierLabel, 2, 0)
    layout.addWidget(positiveMultiplierData, 2, 1)
    layout.addWidget(positiveContourCountLabel, 3, 0)
    layout.addWidget(positiveContourCountData, 3, 1)
    layout.addWidget(negativeContoursLabel, 4, 0)
    layout.addWidget(negativeContoursCheckBox, 4, 1)
    layout.addWidget(negativeBaseLevelLabel, 5, 0)
    layout.addWidget(negativeBaseLevelData, 5, 1)
    layout.addWidget(negativeMultiplierLabel, 6, 0)
    layout.addWidget(negativeMultiplierData, 6, 1)
    layout.addWidget(negativeContourCountLabel, 7, 0)
    layout.addWidget(negativeContourCountData, 7, 1)

    self.setLayout(layout)


class PeakListsTab(QtGui.QWidget):
  def __init__(self, spectrum, parent=None):
    super(PeakListsTab, self).__init__(parent)

    i=0
    layout = QtGui.QHBoxLayout()
    for peakList in spectrum.peakLists:
      label = QtGui.QLabel()
      label.setText(str(peakList.pid))
      checkBox = QtGui.QCheckBox()
      # if spectrum.spectrumItem.peakListItems[peakList.pid].displayed == True:
      #   checkBox.setChecked(True)
      # else:
      #   checkBox.setChecked(False)
      #
      # checkBox.stateChanged.connect(lambda: self.peakListToggle(spectrum.spectrumItem, checkBox.checkState(),peakList))
      layout.addWidget(checkBox)
      layout.addWidget(label)
      # i+=1

    self.setLayout(layout)

class AcquisitionTab(QtGui.QWidget):
  def __init__(self, spectrum, parent=None):
      super(AcquisitionTab, self).__init__(parent)

      layout = QtGui.QGridLayout()
      spectrometerLabel = QtGui.QLabel("Acquisition: ")
      spectrometerData = QtGui.QLineEdit()
      probeLabel = QtGui.QLabel("Probe: ")
      probeData = QtGui.QLineEdit()
      numberScansLabel = QtGui.QLabel("Number of Scans: ")
      numberScansData = QtGui.QLineEdit()
      sampleStateLabel = QtGui.QLabel("Sample State: ")
      sampleStateData = QtGui.QComboBox()
      sampleStateData.addItems(SAMPLE_STATES)
      sampleVolumeLabel = QtGui.QLabel("Sample Volume: ")
      sampleVolumeData = QtGui.QLineEdit()
      # volumeUnitLabel = QtGui.QLabel("Volume Unit")
      volumeUnitData = QtGui.QComboBox()
      volumeUnitData.addItems(VOLUME_UNITS)
      tubeTypeLabel = QtGui.QLabel("NMR Tube Type: ")
      tubeTypeData = QtGui.QLineEdit()
      spinningAngleLabel = QtGui.QLabel("Spinning Angle: ")
      spinningAngleData = QtGui.QLineEdit()
      spinningRateLabel = QtGui.QLabel("Spinning Rate: ")
      spinningRateData = QtGui.QLineEdit()

      layout.addWidget(spectrometerLabel, 0, 0)
      layout.addWidget(spectrometerData, 0, 1)
      layout.addWidget(probeLabel, 1, 0)
      layout.addWidget(probeData, 1, 1)
      layout.addWidget(numberScansLabel, 2, 0)
      layout.addWidget(numberScansData, 2, 1)
      layout.addWidget(sampleStateLabel, 3, 0)
      layout.addWidget(sampleStateData, 3, 1)
      layout.addWidget(sampleVolumeLabel, 4, 0)
      layout.addWidget(sampleVolumeData, 4, 1)
      layout.addWidget(volumeUnitData, 4, 2)
      layout.addWidget(tubeTypeLabel, 5, 0)
      layout.addWidget(tubeTypeData, 5, 1)
      layout.addWidget(spinningAngleLabel, 6, 0)
      layout.addWidget(spinningAngleData, 6, 1)
      layout.addWidget(spinningRateLabel, 7, 0)
      layout.addWidget(spinningRateData, 7, 1)

      self.setLayout(layout)



