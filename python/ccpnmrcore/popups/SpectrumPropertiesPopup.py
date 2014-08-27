from PySide import QtGui, QtCore

from ccpncore.gui.Base import Base
from ccpncore.gui.Button import Button
from ccpncore.gui.ColourDialog import ColourDialog
from ccpnmrcore.modules.SpectrumPane import SPECTRUM_COLOURS
from ccpncore.lib.spectrum.Util import getSpectrumFileFormat
from ccpncore.gui.Label import Label
from ccpncore.gui.LineEdit import LineEdit
from ccpncore.gui.PullDownList import PulldownList
from ccpncore.gui.CheckBox import CheckBox
from ccpncore.gui.Spinbox import Spinbox
from ccpncore.gui.DoubleSpinbox import DoubleSpinbox


from functools import partial

import sys

DIMENSIONS = ['X', 'Y', 'Z', 'A']
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

  def keyPressEvent(self, event):
    if event.key() == QtCore.Qt.Key_Enter:
      pass



class GeneralTab(QtGui.QWidget, Base):
  def __init__(self, spectrum, parent=None):
    super(GeneralTab, self).__init__(parent)


    nameLabel = (Label(self, text="Spectrum name: ", grid=(0,0)))
    nameData = LineEdit(self, grid=(0, 1))
    nameData.setText(spectrum.spectrumItem.name)
    pathLabel = Label(self, text="Path:", grid=(1, 0))
    pathData = LineEdit(self, grid=(1, 1))
    pathData.setText(spectrum.filePath)
    dataTypeLabel = Label(self, text="Data Type: ", grid=(2, 0))
    dataTypeData = Label(self, text=getSpectrumFileFormat(spectrum.filePath), grid=(2, 1))
    templateLabel = Label(self, text="Template: ", grid=(3, 0))
    dateLabel = Label(self, text="Date: ", grid=(4, 0))
    pidLabel = Label(self, text="PID: ", grid=(5, 0))
    pidData = Label(self, text=spectrum.pid, grid=(5, 1))
    if spectrum.dimensionCount == 1:
      colourLabel = Label(self, text="Colour", grid=(6,0))
      self.colourBox = PulldownList(self, grid=(6, 1))
      for item in SPECTRUM_COLOURS.items():
        pix=QtGui.QPixmap(QtCore.QSize(20,20))
        pix.fill(QtGui.QColor(item[0]))
        self.colourBox.addItem(icon=QtGui.QIcon(pix), text=item[1])
      self.colourBox.setCurrentIndex(list(SPECTRUM_COLOURS.keys()).index(spectrum.spectrumItem.colour.name()))
      self.colourBox.currentIndexChanged.connect(partial(self.changedColourComboIndex, spectrum))
      colourButton = Button(self, text="More...", grid=(6, 2))
      colourButton.clicked.connect(partial(self.changeSpectrumColour, spectrum))
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
      if spectrum.ccpnSpectrum.noiseLevel is not None:
        noiseLevelData.setText(str('%.3d' % spectrum.ccpnSpectrum.noiseLevel))
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
      if spectrum.ccpnSpectrum.noiseLevel is not None:
        noiseLevelData.setText(str('%.3d' % spectrum.ccpnSpectrum.noiseLevel))
      else:
        noiseLevelData.setText('None')



  def changeSpectrumColour(self, spectrum):
    dialog = ColourDialog()
    newColour = dialog.getColor()
    # palette = QtGui.QPalette(spectrum.spectrumItem.toolBarButton.palette())
    # palette.setColor(QtGui.QPalette.Button,spectrum.spectrumItem.colour)
    spectrum.spectrumItem.plot.setPen(spectrum.spectrumItem.colour)
    pix=QtGui.QPixmap(QtCore.QSize(20,20))
    pix.fill(QtGui.QColor(newColour))
    newIndex = str(len(SPECTRUM_COLOURS.items())+1)
    self.colourBox.addItem(icon=QtGui.QIcon(pix), text='Colour %s' % newIndex)
    SPECTRUM_COLOURS[newColour.name()] = 'Colour %s' % newIndex
    self.colourBox.setCurrentIndex(int(newIndex)-1)
    pix=QtGui.QPixmap(60,10)
    pix.fill(newColour)
    newIcon = QtGui.QIcon(pix)
    spectrum.spectrumItem.newAction.setIcon(newIcon)

  def changedColourComboIndex(self, spectrum, value):

    spectrum.spectrumItem.colour = QtGui.QColor(list(SPECTRUM_COLOURS.keys())[value])
    # palette = QtGui.QPalette(spectrum.spectrumItem.toolBarButton.palette())
    # palette.setColor(QtGui.QPalette.Button,spectrum.spectrumItem.colour)
    # spectrum.spectrumItem.toolBarButton.setPalette(palette)
    spectrum.spectrumItem.plot.setPen(spectrum.spectrumItem.colour)
    pix=QtGui.QPixmap(60,10)
    pix.fill(spectrum.spectrumItem.colour)
    newIcon = QtGui.QIcon(pix)
    spectrum.spectrumItem.newAction.setIcon(newIcon)



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

    positiveContoursLabel = Label(self, text="Show Positive Contours", grid=(0, 0))
    positiveContoursCheckBox = CheckBox(self, grid=(0, 1), checked="True")
    negativeContoursLabel = Label(self, text="Show negative Contours", grid=(1 ,0))
    negativeContoursCheckBox = CheckBox(self, grid=(1, 1), checked="True")
    positiveBaseLevelLabel = Label(self, text="Base Level", grid=(2, 0))
    positiveBaseLevelData = DoubleSpinbox(self, grid=(2, 1))
    positiveBaseLevelData.setMaximum(1e12)
    positiveBaseLevelData.setMinimum(0)
    positiveBaseLevelData.setValue(spectrum.spectrumItem.baseLevel)
    positiveBaseLevelData.valueChanged.connect(partial(self.lineEditTextChanged1, spectrum))
    positiveMultiplierLabel = Label(self, text="Multiplier", grid=(3, 0))
    positiveMultiplierData = DoubleSpinbox(self, grid=(3, 1))
    positiveMultiplierData.setSingleStep(0.1)
    positiveMultiplierData.setValue(float(spectrum.spectrumItem.multiplier))
    positiveMultiplierData.valueChanged.connect(partial(self.lineEditTextChanged2, spectrum))
    positiveBaseLevelData.setSingleStep(positiveBaseLevelData.value()*(positiveMultiplierData.value()-1))
    positiveContourCountLabel = Label(self, text="Number of contours", grid=(4, 0))
    positiveContourCountData = Spinbox(self, grid=(4, 1))
    positiveContourCountData.setValue(int(spectrum.spectrumItem.numberOfLevels))
    positiveContourCountData.valueChanged.connect(partial(self.lineEditTextChanged3, spectrum))
    positiveContourColourLabel = Label(self, text="Colour",grid=(5, 0))
    self.positiveColourBox = PulldownList(self, grid=(5, 1))
    for item in SPECTRUM_COLOURS.items():
      pix=QtGui.QPixmap(QtCore.QSize(20,20))
      pix.fill(QtGui.QColor(item[0]))
      self.positiveColourBox.addItem(icon=QtGui.QIcon(pix), text=item[1])
    try:
      self.positiveColourBox.setCurrentIndex(list(SPECTRUM_COLOURS.keys()).index(spectrum.spectrumItem.posColor))
      self.positiveColourBox.currentIndexChanged.connect(partial(self.changePosColourComboIndex, spectrum))
    except ValueError:
      pass
    self.positiveColourButton = Button(self, text="More...", grid=(5, 2))
    self.positiveColourButton.clicked.connect(partial(self.changePosSpectrumColour, spectrum))
    # spectrum.spectrumItem.levels = self.newLevels(spectrum)
    # print(self.newLevels(spectrum))


    #
    # negativeContoursLabel = Label(self, text="Show negative Levels", grid=(6, 0))
    # negativeContoursCheckBox = CheckBox(self, grid=(6, 1), checked="True")
    # negativeBaseLevelLabel = Label(self, text="Base Level", grid=(7, 0))
    # negativeBaseLevelData = LineEdit(self, text=spectrum.spectrumItem.baseLevel, grid=(7, 1))
    # negativeMultiplierLabel = Label(self, text="Multiplier", grid=(8, 0))
    # negativeMultiplierData = LineEdit(self, grid=(8, 1))
    # negativeContourCountLabel = Label(self, text="Number of contours", grid=(9, 0))
    # negativeContourCountData = LineEdit(self, grid=(9, 1))
    negativeContourColourLabel = Label(self, text="Colour",grid=(6, 0))
    self.negativeColourBox = PulldownList(self, grid=(6, 1))
    for item in SPECTRUM_COLOURS.items():
      pix=QtGui.QPixmap(QtCore.QSize(20,20))
      pix.fill(QtGui.QColor(item[0]))
      self.negativeColourBox.addItem(icon=QtGui.QIcon(pix), text=item[1])
    try:
      self.negativeColourBox.setCurrentIndex(list(SPECTRUM_COLOURS.keys()).index(spectrum.spectrumItem.negColor))
      self.negativeColourBox.currentIndexChanged.connect(partial(self.changeNegColourComboIndex, spectrum))
    except ValueError:
      pass

    self.negativeColourButton = Button(self, text="More...", grid=(6, 2))
    self.negativeColourButton.clicked.connect(partial(self.changeNegSpectrumColour, spectrum))



    spectrum.spectrumItem.levels = spectrum.spectrumItem.getLevels()

  def lineEditTextChanged1(self, spectrum, value):
    spectrum.spectrumItem.baseLevel = float(value)
    spectrum.spectrumItem.levels = spectrum.spectrumItem.getLevels()
  def lineEditTextChanged2(self, spectrum, value):
    spectrum.spectrumItem.multiplier = float(value)
    spectrum.spectrumItem.levels = spectrum.spectrumItem.getLevels()
  def lineEditTextChanged3(self, spectrum, value):
    spectrum.spectrumItem.numberOfLevels = int(value)
    spectrum.spectrumItem.levels = spectrum.spectrumItem.getLevels()

  def changePosSpectrumColour(self, spectrum):
    dialog = ColourDialog()
    newColour = dialog.getColor()
    spectrum.spectrumItem.posColors = (spectrum.spectrumItem.getColorTuple(newColour),)
    pix=QtGui.QPixmap(QtCore.QSize(20,20))
    pix.fill(QtGui.QColor(newColour))
    newIndex = str(len(SPECTRUM_COLOURS.items())+1)
    self.positiveColourBox.addItem(icon=QtGui.QIcon(pix), text='Colour %s' % newIndex)
    self.negativeColourBox.addItem(icon=QtGui.QIcon(pix), text='Colour %s' % newIndex)
    SPECTRUM_COLOURS[newColour.name()] = 'Colour %s' % newIndex
    self.positiveColourBox.setCurrentIndex(int(newIndex)-1)
    pix=QtGui.QPixmap(60,10)
    pix.fill(newColour)
    newIcon = QtGui.QIcon(pix)
    spectrum.spectrumItem.newAction.setIcon(newIcon)
    

  def changeNegSpectrumColour(self, spectrum):
    dialog = ColourDialog()
    newColour = dialog.getColor()
    spectrum.spectrumItem.negColors = (spectrum.spectrumItem.getColorTuple(newColour),)
    pix=QtGui.QPixmap(QtCore.QSize(20,20))
    pix.fill(QtGui.QColor(newColour))
    newIndex = str(len(SPECTRUM_COLOURS.items())+1)
    self.negativeColourBox.addItem(icon=QtGui.QIcon(pix), text='Colour %s' %newIndex)
    self.positiveColourBox.addItem(icon=QtGui.QIcon(pix), text='Colour %s' %newIndex)
    SPECTRUM_COLOURS[newColour.name()] = 'Colour %s' % newIndex
    self.negativeColourBox.setCurrentIndex(int(newIndex)-1)


  def changePosColourComboIndex(self, spectrum, value):

    newColour = list(SPECTRUM_COLOURS.keys())[value]
    spectrum.spectrumItem.posColor = newColour
    spectrum.spectrumItem.posColors = (spectrum.spectrumItem.getColorTuple(newColour),)
    pix=QtGui.QPixmap(60,10)
    pix.fill(newColour)
    newIcon = QtGui.QIcon(pix)
    spectrum.spectrumItem.newAction.setIcon(newIcon)



  def changeNegColourComboIndex(self, spectrum, value):

    newColour = list(SPECTRUM_COLOURS.keys())[value]
    spectrum.spectrumItem.negColor = newColour
    spectrum.spectrumItem.negColors = (spectrum.spectrumItem.getColorTuple(newColour),)


class PeakListsTab(QtGui.QWidget):
  def __init__(self, spectrum, parent=None):
    super(PeakListsTab, self).__init__(parent)
    #
    i=0
    for peakList in spectrum.peakLists:
      label = Label(self, text=str(peakList.pid), grid=(i, 1))
      checkBox = CheckBox(self, grid=(i, 0), checked="True")
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
      # volumeUnitLabel = Label(self, text="Volume Unit")
      volumeUnitData = PulldownList(self)
      volumeUnitData.addItems(VOLUME_UNITS)
      tubeTypeLabel = Label(self, text="NMR Tube Type: ", grid=(5, 0))
      tubeTypeData = LineEdit(self, grid=(5, 1))
      spinningAngleLabel = Label(self, text="Spinning Angle: ", grid=(6, 0))
      spinningAngleData = LineEdit(self, grid=(6, 1))
      spinningRateLabel = Label(self, text="Spinning Rate: ", grid=(7, 0))
      spinningRateData = LineEdit(self, grid=(7, 1))



