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

import os

from PyQt4 import QtGui, QtCore

# from ccpn.lib.Experiment import EXPERIMENT_TYPES

from ccpncore.gui.Base import Base
from ccpncore.gui.Button import Button
from ccpncore.gui.ColourDialog import ColourDialog
from ccpncore.util.Colour import spectrumColours
# from ccpncore.lib.spectrum.Util import getSpectrumFileFormat
from ccpncore.gui.ButtonList import ButtonList
from ccpncore.gui.Label import Label
from ccpncore.gui.LineEdit import LineEdit
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.CheckBox import CheckBox
from ccpncore.gui.ScrollArea import ScrollArea
from ccpncore.gui.Spinbox import Spinbox
from ccpncore.gui.DoubleSpinbox import DoubleSpinbox


from functools import partial

import sys

DIMENSIONS = ['X', 'Y', 'Z', 'Z2']
SPECTRA = ['1H', 'STD', 'Relaxation Filtered', 'Water LOGSY']
SAMPLE_STATES = ['liquid', 'solid', 'ordered', 'powder', 'crystal']
VOLUME_UNITS = ['μl', 'ml', 'l']


class SpectrumPropertiesPopup(QtGui.QDialog, Base):
  def __init__(self, spectrum, item, parent=None, **kw):
    super(SpectrumPropertiesPopup, self).__init__(parent)
    Base.__init__(self, **kw)
    tabWidget = QtGui.QTabWidget()
    tabWidget.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
    if spectrum.dimensionCount == 1:
      tabWidget.addTab(GeneralTab(spectrum, item=item), "General")
      tabWidget.addTab(DimensionsTab(spectrum, spectrum.dimensionCount), "Dimensions")
      tabWidget.addTab(PeakListsTab(spectrum), "Peak Lists")
      tabWidget.addTab(AcquisitionTab(spectrum), "Spectrometer")

    else:
      tabWidget.addTab(GeneralTab(spectrum, item=item), "General")
      tabWidget.addTab(DimensionsTab(spectrum, spectrum.dimensionCount), "Dimensions")
      tabWidget.addTab(ContoursTab(spectrum), "Contours")
      tabWidget.addTab(PeakListsTab(spectrum), "Peak Lists")
      tabWidget.addTab(AcquisitionTab(spectrum), "Spectrometer")


    self.setWindowTitle("Spectrum Information")
    buttonBox = ButtonList(self, grid=(3, 1), callbacks=[self.accept, self.reject], texts=['OK', 'Cancel'])


    scrollArea = ScrollArea(self, grid=(0, 0), gridSpan=(2, 2))
    if spectrum.project._appBase.preferences.general.colourScheme == 'dark':
      scrollArea.setStyleSheet("""QScrollArea { background-color:  #2a3358;
                                  }
                                  QTabWidget { background-color:  #2a3358;
                                  }
                                                          """)
    elif spectrum.project._appBase.preferences.general.colourScheme == 'light':
      scrollArea.setStyleSheet("""QScrollArea { background-color:  #FBF4CC;
                                  }
                                  QTabWidget { background-color:  #FBF4CC;
                                  }
                                                          """)
    mainLayout = QtGui.QVBoxLayout()
    scrollArea.setLayout(mainLayout)
    scrollArea.setWidget(tabWidget)
    scrollArea.setWidgetResizable(True)
    # mainLayout.addWidget(tabWidget)
    # self.addWidget(buttonBox)

    # self.setLayout(mainLayout)

  def keyPressEvent(self, event):
    if event.key() == QtCore.Qt.Key_Enter:
      pass



class GeneralTab(QtGui.QWidget, Base):
  def __init__(self, spectrum, parent=None, item=None):
    super(GeneralTab, self).__init__(parent)
    self.item = item
    self.spectrum = spectrum
    self.experimentTypes = spectrum._project._experimentTypeMap
    nameLabel = Label(self, text="Spectrum name ", grid=(0, 0))
    self.nameData = LineEdit(self, vAlign='t', grid=(0, 1))
    self.nameData.setMinimumWidth(200)
    self.nameData.setFixedHeight(25)
    self.nameData.setText(spectrum.name)
    self.nameData.editingFinished.connect(self.changeSpectrumName)
    pathLabel = Label(self, text="Path", vAlign='t', hAlign='l', grid=(1, 0))
    self.pathData = LineEdit(self, vAlign='t', grid=(1, 1))
    self.pathButton = Button(self, '...', grid=(1, 2), callback=self.getSpectrumFile)
    apiDataStore = spectrum._apiDataSource.dataStore
    if apiDataStore.dataLocationStore.name == 'standard':
      dataUrlName = apiDataStore.dataUrl.name
      if dataUrlName == 'insideData':
        self.pathData.setText('$INSIDE/%s' % apiDataStore.path)
      elif dataUrlName == 'alongsideData':
        self.pathData.setText('$ALONGSIDE/%s' % apiDataStore.path)
      elif dataUrlName == 'remoteData':
        self.pathData.setText('$DATA/%s' % apiDataStore.path)
      else:
        self.pathData.setText(apiDataStore.fullPath)
    self.pathData.setMinimumWidth(200)
    self.pathData.setFixedHeight(25)
    self.pathData.editingFinished.connect(self.setSpectrumPath)
    chemicalShiftListLabel = Label(self, text="Chemical Shift List ", vAlign='t', hAlign='l', grid=(3, 0))
    self.chemicalShiftListPulldown = PulldownList(self, vAlign='t', hAlign='l', grid=(3, 1), texts=[csList.pid
                                                for csList in spectrum.project.chemicalShiftLists]
                                                +['<New>'],callback=self.setChemicalShiftList)

    self.chemicalShiftListPulldown.setMinimumWidth(200)
    self.chemicalShiftListPulldown.setFixedHeight(25)

    dateLabel = Label(self, text="Date ", vAlign='t', hAlign='l', grid=(4, 0))
    dateData = LineEdit(self, vAlign='t', hAlign='l', grid=(4, 1))
    dateData.setMinimumWidth(200)
    dateData.setFixedHeight(25)
    pidLabel = Label(self, text="PID ", vAlign='t', hAlign='l', grid=(5, 0))
    pidData = Label(self, text=spectrum.pid, vAlign='t', hAlign='l', grid=(5, 1))
    if spectrum.dimensionCount == 1:
      colourLabel = Label(self, text="Colour", vAlign='t', hAlign='l', grid=(6, 0))
      self.colourBox = PulldownList(self, vAlign='t', hAlign='l', grid=(6, 1))
      for item in spectrumColours.items():
        pix=QtGui.QPixmap(QtCore.QSize(20, 20))
        pix.fill(QtGui.QColor(item[0]))
        self.colourBox.addItem(icon=QtGui.QIcon(pix), text=item[1])
      self.colourBox.setCurrentIndex(list(spectrumColours.keys()).index(spectrum.sliceColour))
      self.colourBox.currentIndexChanged.connect(partial(self.changedColourComboIndex, spectrum))
      colourButton = Button(self, text="More...", vAlign='t', hAlign='l', grid=(6, 2), callback=partial(self.changeSpectrumColour, spectrum))
      spectrumTypeLabel = Label(self, text="Spectrum Type ", vAlign='t', hAlign='l', grid=(7, 0))
      spectrumType = PulldownList(self, vAlign='t', hAlign='l', grid=(7, 1))
      spectrumType.addItems(SPECTRA)
      spectrumType.setCurrentIndex(spectrumType.findText(spectrum.experimentName))
      spectrumScalingLabel = Label(self, text='Spectrum Scaling', vAlign='t', hAlign='l', grid=(8, 0))
      self.spectrumScalingData = LineEdit(self, text=str(self.spectrum.scale), vAlign='t', hAlign='l', grid=(8, 1))
      self.spectrumScalingData.editingFinished.connect(self.setSpectrumScale)
      # pulseProgramLabel = Label(self, text="Pulse Program: ", vAlign='t', hAlign='l', grid=(9, 0))
      # self.pulseProgramData = LineEdit(self, vAlign='t', hAlign='l', grid=(0, 1))
      # self.pulseProgramData.setText(spectrum.name)
      # self.pulseProgramData.editingFinished.connect(self.changeSpectrumName)
      recordingDataLabel = Label(self, text="Date Recorded ", vAlign='t', hAlign='l', grid=(10, 0))
      noiseLevelLabel = Label(self, text="Noise Level ", vAlign='t', hAlign='l', grid=(11, 0))
      noiseLevelData = LineEdit(self)
      if spectrum._apiDataSource.noiseLevel is not None:
        noiseLevelData.setText(str('%.3d' % spectrum._apiDataSource.noiseLevel))
      else:
        noiseLevelData.setText('None')
    else:
      spectrumTypeLabel = Label(self, text="Spectrum Type ", vAlign='t', hAlign='l', grid=(6, 0))
      self.spectrumType = PulldownList(self, vAlign='t', hAlign='l', grid=(6, 1))
      axisCodes = []
      for isotopeCode in spectrum.isotopeCodes:
        axisCodes.append(''.join([code for code in isotopeCode if not code.isdigit()]))

      self.spectrumType.setMinimumWidth(200)
      self.spectrumType.setFixedHeight(25)


      self.atomCodes = tuple(sorted(axisCodes))
      self.spectrumType.addItems(sorted(list(self.experimentTypes[spectrum.dimensionCount].get(self.atomCodes).keys())))


      self.spectrumType.setCurrentIndex(self.spectrumType.findText(spectrum.experimentName))
      self.spectrumType.currentIndexChanged.connect(self.changeSpectrumType)
      # pulseProgramLabel = Label(self, text="Pulse Program: ", vAlign='t', hAlign='l', grid=(7, 0))
      # recordingDataLabel = Label(self, text="Date Recorded", vAlign='t', hAlign='l', grid=(8, 0))
      spectrumScalingLabel = Label(self, text='Spectrum Scaling', vAlign='t', hAlign='l', grid=(8, 0))
      self.spectrumScalingData = LineEdit(self, text=str(self.spectrum.scale), vAlign='t', hAlign='l', grid=(8, 1))
      self.spectrumScalingData.setMinimumWidth(200)
      self.spectrumScalingData.setFixedHeight(25)
      self.spectrumScalingData.editingFinished.connect(self.setSpectrumScale)
      # minimumValueLabel = Label(self, text="Minimum Value: ", vAlign='t', hAlign='l', grid=(9, 0))
      # maximumValueLabel = Label(self, text="Maximum Value: ", vAlign='t', hAlign='l', grid=(10, 0))
      noiseLevelLabel = Label(self, text="Noise Level ", vAlign='t', hAlign='l', grid=(9, 0))
      noiseLevelData = LineEdit(self, vAlign='t', hAlign='l', grid=(9, 1))
      noiseLevelData.setMinimumWidth(200)
      self.spectrumType.setFixedHeight(25)

      if spectrum._apiDataSource.noiseLevel is None:
        noiseLevelData.setText(str('%.3d' % spectrum._apiDataSource.estimateNoise()))
      else:

        noiseLevelData.setText('%.3d' % spectrum._apiDataSource.noiseLevel)

  def changeSpectrumName(self):
    if self.nameData.isModified():
      self.spectrum.rename(self.nameData.text())
      self.item.setText(0, 'SP:'+self.nameData.text())
      for i in range(self.item.childCount()):
        pid = self.item.child(i).text(0).split(':')[0]+':'+self.nameData.text()+"."\
              + self.item.child(i).text(0).split('.')[1]
        self.item.child(i).setText(0, pid)


  def setSpectrumScale(self):
    self.spectrum.scale = float(self.spectrumScalingData.text())

  def setChemicalShiftList(self, item):
    if item == '<New>':
      newChemicalShiftList = self.spectrum.project.newChemicalShiftList()
      insertionIndex = len(self.chemicalShiftListPulldown.texts)-1
      self.chemicalShiftListPulldown.texts.insert(insertionIndex, newChemicalShiftList.pid)
      self.chemicalShiftListPulldown.setData(self.chemicalShiftListPulldown.texts)
      self.chemicalShiftListPulldown.setCurrentIndex(insertionIndex)
      self.spectrum.chemicalShiftList = newChemicalShiftList
    else:
      self.spectrum.chemicalShiftList = self.spectrum.project.getByPid(item)

  def changeSpectrumType(self, value):
    expType = self.experimentTypes[self.spectrum.dimensionCount].get(self.atomCodes).get(self.spectrumType.currentText())
    self.spectrum.experimentType = expType

  def getSpectrumFile(self):
    if os.path.exists('/'.join(self.pathData.text().split('/')[:-1])):
      currentSpectrumDirectory = '/'.join(self.pathData.text().split('/')[:-1])
    else:
      currentSpectrumDirectory = os.path.expanduser('~')
    directory = QtGui.QFileDialog.getOpenFileName(self, 'Select Spectrum File', currentSpectrumDirectory)
    if len(directory) > 0:
      self.pathData.setText(directory)
      self.spectrum.filePath = directory

      apiDataStore = self.spectrum._apiDataSource.dataStore
      if apiDataStore.dataLocationStore.name == 'standard':
        dataUrlName = apiDataStore.dataUrl.name
        if dataUrlName == 'insideData':
          self.pathData.setText('$INSIDE/%s' % apiDataStore.path)
        elif dataUrlName == 'alongsideData':
          self.pathData.setText('$ALONGSIDE/%s' % apiDataStore.path)
        elif dataUrlName == 'remoteData':
          self.pathData.setText('$DATA/%s' % apiDataStore.path)
        else:
          self.pathData.setText(apiDataStore.fullPath)

  def setSpectrumPath(self):
    if self.pathData.isModified():
      self.spectrum.filePath = self.pathData.text()
      apiDataStore = self.spectrum._apiDataSource.dataStore
      if apiDataStore.dataLocationStore.name == 'standard':
        dataUrlName = apiDataStore.dataUrl.name
        if dataUrlName == 'insideData':
          self.pathData.setText('$INSIDE/%s' % apiDataStore.path)
        elif dataUrlName == 'alongsideData':
          self.pathData.setText('$ALONGSIDE/%s' % apiDataStore.path)
        elif dataUrlName == 'remoteData':
          self.pathData.setText('$DATA/%s' % apiDataStore.path)
        else:
          self.pathData.setText(apiDataStore.fullPath)


  def changeSpectrumColour(self, spectrum):
    dialog = ColourDialog()
    newColour = dialog.getColor()
    # palette = QtGui.QPalette(spectrum.guispectrumView.toolBarButton.palette())
    # palette.setColor(QtGui.QPalette.Button,spectrum.spectrumView.colour)
    spectrum._apiDataSource.setSliceColour(newColour.name())
    spectrum.guiSpectrumView.plot.setPen(spectrum._apiDataSource.sliceColour)
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
    #   spectrumView.plot.setPen(QtGui.QColor(spectrum._apiDataSource.sliceColour))
    pix=QtGui.QPixmap(60,10)
    pix.fill(QtGui.QColor(spectrum.sliceColour))
    newIcon = QtGui.QIcon(pix)
    # spectrum.guiSpectrumView.newAction.setIcon(newIcon)



class DimensionsTab(QtGui.QWidget, Base):
  def __init__(self, spectrum, dimensions, parent=None):
    super(DimensionsTab, self).__init__(parent)
    from ccpncore.gui.Table import ObjectTable, Column
    sampleTables = []
    #


    # sampleTable = ObjectTable(self, columns, callback=None, objects=[spectrum], grid=(0, 0), gridSpan=(2, 8))
    # layout = QtGui.QGridLayout()
    dimensionalityLabel = Label(self, text="Dimension ", grid=(0, 0),hAlign='l', vAlign='t',)
    for i in range(dimensions):
      dimLabel = Label(self, text='%s' % str(i+1), grid =(0, i+1), vAlign='t', hAlign='l')
    j = 2
    for i in range(dimensions):
      axisLabel = Label(self, text="Axis Code ", grid=(1, 0), vAlign='t', hAlign='l')
      axisLabelData = Label(self, text=str(spectrum.axisCodes[i]), grid=(1, i+1),  hAlign='l')
      pointsLabel = Label(self, text="Point Counts ", grid=(2, 0), vAlign='t', hAlign='l')
      pointsData = Label(self, text=str(spectrum.pointCounts[i]), grid=(2, i+1), vAlign='t', hAlign='l')
      axisTypeLabel = Label(self, text="Dimension Type ", grid=(3, 0), vAlign='t', hAlign='l')
      axisTypeData = Label(self, text=spectrum.dimensionTypes[i], grid=(3, i+1), vAlign='t', hAlign='l')
      spectralWidthLabel = Label(self, text="Spectrum Width (ppm) ", grid=(4, 0), vAlign='t', hAlign='l')
      spectralWidthData = Label(self, text=str("%.3f" % spectrum.spectralWidths[i]), grid=(4, i+1), vAlign='t', hAlign='l')
      spectralWidthHzLabel = Label(self, text="Spectral Width (Hz) ", grid=(5, 0), vAlign='t', hAlign='l')
      spectralWidthHzData = Label(self, text=str("%.3f" % spectrum.spectralWidthsHz[i]), grid=(5, i+1), vAlign='t', hAlign='l')
      spectralReferencingLabel = Label(self, text="Referencing ", grid=(6, 0), vAlign='t', hAlign='l')
      spectralReferencingData = LineEdit(self, text=str("%.3f" % spectrum.referenceValues[i]), grid=(6, i+1), vAlign='t', hAlign='l')
      spectralReferencingData.textChanged.connect(partial(self.setDimensionReferencing, spectrum, i))
      spectralReferencingData.setMaximumWidth(100)
      spectralAssignmentToleranceLabel = Label(self, text="Assignment Tolerance ", grid=(7, 0),  hAlign='l')

      spectralAssignmentToleranceData = LineEdit(self, grid=(7, i+1),  hAlign='l')
      spectralAssignmentToleranceData.setMaximumWidth(100)

      if spectrum.assignmentTolerances[i] is not None:
        spectralAssignmentToleranceData.setText(str("%.3f" % spectrum.assignmentTolerances[i]))
      spectralAssignmentToleranceData.textChanged.connect(partial(self.setAssignmentTolerances, spectrum, i))
      # spectralShiftWeightingLabel = Label(self, text=DIMENSIONS[i]+"-Shift Weighting", grid=(j+8, 0))
      # spectralShiftWeightingData = LineEdit(self, grid=(j+8, 1))


  def setAssignmentTolerances(self, spectrum, dim, value):
    assignmentTolerances = list(spectrum.assignmentTolerances)
    assignmentTolerances[dim] = float(value)
    spectrum.assignmentTolerances = assignmentTolerances

  def setDimensionReferencing(self, spectrum, dim, value):
    spectrumReferencing = list(spectrum.referenceValues)
    spectrumReferencing[dim] = float(value)
    spectrum.referenceValues = spectrumReferencing



class ContoursTab(QtGui.QWidget, Base):
  def __init__(self, spectrum, parent=None):
    super(ContoursTab, self).__init__(parent)

    self.spectrum = spectrum
    positiveContoursLabel = Label(self, text="Show Positive Contours", grid=(0, 0), vAlign='t', hAlign='l')
    positiveContoursCheckBox = CheckBox(self, grid=(0, 1), checked=True, vAlign='t', hAlign='l')
    for spectrumView in self.spectrum.spectrumViews:
      if spectrumView._wrappedData.spectrumView.displayPositiveContours is True:
        positiveContoursCheckBox.setChecked(True)
      else:
        positiveContoursCheckBox.setChecked(False)

    positiveContoursCheckBox.stateChanged.connect(self.changePositiveContourDisplay)
    positiveBaseLevelLabel = Label(self, text="Positive Base Level", grid=(1, 0), vAlign='t', hAlign='l')
    positiveBaseLevelData = DoubleSpinbox(self, grid=(1, 1), vAlign='t', hAlign='l')
    positiveBaseLevelData.setMaximum(1e12)
    positiveBaseLevelData.setMinimum(0)
    positiveBaseLevelData.setValue(spectrum.positiveContourBase)
    positiveBaseLevelData.valueChanged.connect(partial(self.lineEditTextChanged1, spectrum))
    positiveMultiplierLabel = Label(self, text="Positive Multiplier", grid=(2, 0), vAlign='t', hAlign='l')
    positiveMultiplierData = DoubleSpinbox(self, grid=(2, 1), vAlign='t', hAlign='l')
    positiveMultiplierData.setSingleStep(0.1)
    positiveMultiplierData.setValue(float(spectrum.positiveContourFactor))
    positiveMultiplierData.valueChanged.connect(partial(self.lineEditTextChanged2, spectrum))
    positiveBaseLevelData.setSingleStep(positiveBaseLevelData.value()*(positiveMultiplierData.value()-1))
    positiveContourCountLabel = Label(self, text="Number of positive contours", grid=(3, 0), vAlign='t', hAlign='l')
    positiveContourCountData = Spinbox(self, grid=(3, 1), vAlign='t', hAlign='l')
    positiveContourCountData.setValue(int(spectrum._apiDataSource.positiveContourCount))
    positiveContourCountData.valueChanged.connect(partial(self.lineEditTextChanged3, spectrum))
    positiveContourColourLabel = Label(self, text="Positive Contour Colour", grid=(4, 0), vAlign='t', hAlign='l')
    self.positiveColourBox = PulldownList(self, grid=(4, 1), vAlign='t', hAlign='l')

    self.positiveColourBox.setMinimumWidth(200)
    self.positiveColourBox.setFixedHeight(25)
    positiveBaseLevelData.setMinimumWidth(200)
    positiveBaseLevelData.setFixedHeight(25)
    positiveMultiplierData.setMinimumWidth(200)
    positiveMultiplierData.setFixedHeight(25)
    positiveContourCountData.setMinimumWidth(200)
    positiveContourCountData.setFixedHeight(25)

    for item in spectrumColours.items():
      pix=QtGui.QPixmap(QtCore.QSize(20,20))
      pix.fill(QtGui.QColor(item[0]))
      self.positiveColourBox.addItem(icon=QtGui.QIcon(pix), text=item[1])
    try:
      self.positiveColourBox.setCurrentIndex(list(spectrumColours.keys()).index(spectrum.positiveContourColour))
      self.positiveColourBox.currentIndexChanged.connect(partial(self.changePosColourComboIndex, spectrum))
    except ValueError:
      pass
    self.positiveColourButton = Button(self, text="More...", grid=(4, 2), vAlign='t', hAlign='l')
    self.positiveColourButton.clicked.connect(partial(self.changePosSpectrumColour, spectrum))


    negativeContoursLabel = Label(self, text="Show Negative Contours", grid=(6 ,0), vAlign='t', hAlign='l')
    negativeContoursCheckBox = CheckBox(self, grid=(6, 1), checked=True, vAlign='t', hAlign='l')
    for spectrumView in self.spectrum.spectrumViews:
      if spectrumView._wrappedData.spectrumView.displayNegativeContours is True:
        negativeContoursCheckBox.setChecked(True)
      else:
        negativeContoursCheckBox.setChecked(False)
    negativeContoursCheckBox.stateChanged.connect(self.displayNegativeContours)
    negativeBaseLevelLabel = Label(self, text="Negative Base Level", grid=(7, 0), vAlign='t', hAlign='l')
    negativeBaseLevelData = DoubleSpinbox(self, grid=(7, 1), vAlign='t', hAlign='l')
    negativeBaseLevelData.setMaximum(0)
    negativeBaseLevelData.setMinimum(-1e12)
    negativeBaseLevelData.setValue(spectrum.negativeContourBase)
    negativeBaseLevelData.valueChanged.connect(partial(self.lineEditTextChanged4, spectrum))
    negativeMultiplierLabel = Label(self, text="Multiplier", grid=(8, 0), vAlign='t', hAlign='l')
    negativeMultiplierData = DoubleSpinbox(self, grid=(8, 1), vAlign='t', hAlign='l')
    negativeMultiplierData.setValue(spectrum.negativeContourFactor)
    negativeMultiplierData.setSingleStep(0.1)
    negativeMultiplierData.valueChanged.connect(partial(self.lineEditTextChanged5, spectrum))
    negativeContourCountLabel = Label(self, text="Number of contours", grid=(9, 0), vAlign='t', hAlign='l')
    negativeContourCountData = Spinbox(self, grid=(9, 1), vAlign='t', hAlign='l')
    negativeContourCountData.setValue(spectrum.negativeContourCount)
    negativeContourCountData.valueChanged.connect(partial(self.lineEditTextChanged6, spectrum))
    negativeContourColourLabel = Label(self, text="Colour",grid=(10, 0), vAlign='t', hAlign='l')
    self.negativeColourBox = PulldownList(self, grid=(10, 1), vAlign='t', hAlign='l')
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


    self.negativeColourBox.setMinimumWidth(200)
    self.negativeColourBox.setFixedHeight(25)
    negativeBaseLevelData.setMinimumWidth(200)
    negativeBaseLevelData.setFixedHeight(25)
    negativeMultiplierData.setMinimumWidth(200)
    negativeMultiplierData.setFixedHeight(25)
    negativeContourCountData.setMinimumWidth(200)
    negativeContourCountData.setFixedHeight(25)

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
    spectrum._apiDataSource.negativeContourColour = newColour
    pix=QtGui.QPixmap(60,10)
    pix.fill(QtGui.QColor(newColour))
    newIcon = QtGui.QIcon(pix)
    # spectrum.spectrumItem.newAction.setIcon(newIcon)


class PeakListsTab(QtGui.QWidget, Base):
  def __init__(self, spectrum, parent=None):
    super(PeakListsTab, self).__init__(parent)
    self.spectrum = spectrum
    i=0
    for peakList in spectrum.peakLists:
      label = Label(self, grid=(i, 1), text=str(peakList.pid), vAlign='t', hAlign='l')
      checkBox = CheckBox(self, grid=(i, 0), checked=True, vAlign='t', hAlign='l')
      # self.layout().addWidget(checkBox, i, 0, QtCore.Qt.AlignTop)
      for strip in self.spectrum.project.strips:
        peakListView = strip.peakListViewDict.get(peakList)
        if peakListView is not None:
          if peakListView.isVisible():
            checkBox.setChecked(True)
          else:
            checkBox.setChecked(False)
        else:
          checkBox.setChecked(False)
    #   #
        checkBox.stateChanged.connect(partial(self.peakListToggle, peakListView))
      i+=1

  def peakListToggle(self, peakListView, state):
      if peakListView is not None:
        if state == QtCore.Qt.Checked:
          peakListView.setVisible(True)
        else:
          peakListView.setVisible(False)




class AcquisitionTab(QtGui.QWidget):
  def __init__(self, spectrum, parent=None):
      super(AcquisitionTab, self).__init__(parent)

      spectrometerLabel = Label(self, text="Acquisition ", grid=(0, 0), vAlign='t', hAlign='l')
      spectrometerData = LineEdit(self, grid=(0, 1), vAlign='t', hAlign='l')
      probeLabel = Label(self, text="Probe ", grid=(1, 0), vAlign='t', hAlign='l')
      probeData = LineEdit(self, grid=(1, 1), vAlign='t', hAlign='l')
      numberScansLabel = Label(self, text="Number of Scans ", grid=(2, 0), vAlign='t', hAlign='l')
      numberScansData = LineEdit(self, grid=(2, 1), vAlign='t', hAlign='l')
      sampleStateLabel = Label(self, text="Sample State ", grid=(3, 0), vAlign='t', hAlign='l')
      sampleStateData = PulldownList(self, grid=(3, 1), vAlign='t', hAlign='l')
      sampleStateData.addItems(SAMPLE_STATES)
      sampleVolumeLabel = Label(self, text="Sample Volume ", grid=(4, 0), vAlign='t', hAlign='l')
      sampleVolumeData = LineEdit(self, grid=(4, 1), vAlign='t', hAlign='l')
      volumeUnitLabel = Label(self, text="Volume Unit ", grid=(5, 0), vAlign='t', hAlign='l')
      volumeUnitData = PulldownList(self, grid=(5, 1), vAlign='t', hAlign='l')
      volumeUnitData.addItems(VOLUME_UNITS)
      tubeTypeLabel = Label(self, text="NMR Tube Type ", grid=(6, 0), vAlign='t', hAlign='l')
      tubeTypeData = LineEdit(self, grid=(6, 1), vAlign='t', hAlign='l')
      spinningAngleLabel = Label(self, text="Spinning Angle ", grid=(7, 0), vAlign='t', hAlign='l')
      spinningAngleData = LineEdit(self, grid=(7, 1), vAlign='t', hAlign='l')
      spinningRateLabel = Label(self, text="Spinning Rate ", grid=(8, 0), vAlign='t', hAlign='l')
      spinningRateData = LineEdit(self, grid=(8, 1), vAlign='t', hAlign='l')
