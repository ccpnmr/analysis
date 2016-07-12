"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================

__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

import os
import sys
from functools import partial

from PyQt4 import QtGui, QtCore

from ccpn.core.lib import Util as ccpnUtil
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.ColourDialog import ColourDialog
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.FileDialog import FileDialog
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.util.Colour import spectrumColours

SPECTRA = ['1H', 'STD', 'Relaxation Filtered', 'Water LOGSY']

class SpectrumPropertiesPopup(QtGui.QDialog, Base):
  # The values on the 'General' and 'Dimensions' tabs are queued as partial functions when set.
  # The apply button then steps through each tab, and calls each function in the _changes dictionary
  # in order to set the parameters.


  def __init__(self, spectrum, parent=None, **kw):

    super(SpectrumPropertiesPopup, self).__init__(parent)
    layout = QtGui.QGridLayout()
    self.setLayout(layout)
    self.tabWidget = QtGui.QTabWidget()
    # tabWidget.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
    if spectrum.dimensionCount == 1:
      self.tabWidget.addTab(GeneralTab(spectrum), "General")
      self.tabWidget.addTab(DimensionsTab(spectrum, spectrum.dimensionCount), "Dimensions")

    else:
      self.tabWidget.addTab(GeneralTab(spectrum), "General")
      self.tabWidget.addTab(DimensionsTab(spectrum, spectrum.dimensionCount), "Dimensions")
      self.tabWidget.addTab(ContoursTab(spectrum), "Contours")


    self.layout().addWidget(self.tabWidget, 0, 0, 2, 4)
    Button(self, grid=(2, 1), callback=self.reject, text='Cancel',vPolicy='fixed')
    self.applyButton = Button(self, grid=(2, 2), callback=self.apply, text='Apply', vPolicy='fixed')
    # self.applyButton.setEnabled(False)
    Button(self, grid=(2, 3), callback=self.accept, text='Ok', vPolicy='fixed')
    if sys.platform.lower() == 'linux':
      if spectrum.project._appBase.preferences.general.colourScheme == 'dark':
        self.setStyleSheet("QTabWidget > QWidget{ background-color:  #2a3358; color: #f7ffff; padding:4px;}")
      elif spectrum.project._appBase.preferences.general.colourScheme == 'light':
        self.setStyleSheet("QTabWidget > QWidget { background-color: #fbf4cc;} QTabWidget { background-color: #fbf4cc;}")

  def _keyPressEvent(self, event):
    if event.key() == QtCore.Qt.Key_Enter:
      pass

  def accept(self):
    self.apply()
    super().accept()

  def apply(self):
    self.setFocus()  # So editingFinished callbacks fire
    tabs = self.tabWidget.findChildren(QtGui.QStackedWidget)[0].children()
    tabs = [t for t in tabs if not isinstance(t, QtGui.QStackedLayout)]
    for t in tabs:
      try:
        changes = t._changes
        self._applyChanges(changes)
      except AttributeError:
        pass

  def _applyChanges(self, changes):
    for v in changes.values():
      v()


class FilePathValidator(QtGui.QValidator):

  def __init__(self, spectrum, parent=None, validationType='exists'):
    QtGui.QValidator.__init__(self, parent=parent)
    self.spectrum = spectrum
    self.validationType = validationType


  def validate(self, p_str, p_int):
    if self.validationType != 'exists':
      raise NotImplemented('FilePathValidation only checks that the path exists')
    filePath = ccpnUtil.expandDollarFilePath(self.spectrum._project, p_str)

    if os.path.exists(filePath):
      try:
        self.parent().setStyleSheet('background-color: #f7ffff')
      except: pass
      state = QtGui.QValidator.Acceptable
    else:
      try:
        self.parent().setStyleSheet('background-color: #f7ffff')
      except: pass
      self.parent().setStyleSheet('background-color: #f7ffbe') # TODO: use a yellow in our colour scheme
      state = QtGui.QValidator.Intermediate
    return state, p_str, p_int



class GeneralTab(QtGui.QWidget, Base):
  def __init__(self, spectrum, parent=None, item=None):
    super(GeneralTab, self).__init__(parent)
    self.item = item
    self.spectrum = spectrum
    self._changes = dict()

    self.experimentTypes = spectrum._project._experimentTypeMap
    nameLabel = Label(self, text="Spectrum name ", grid=(1, 0))
    self.nameData = LineEdit(self, vAlign='t', grid=(1, 1))
    self.nameData.setText(spectrum.name)
    self.layout().addItem(QtGui.QSpacerItem(0, 10), 0, 0)
    self.nameData.editingFinished.connect(self._queueSpectrumNameChange)
    pathLabel = Label(self, text="Path", vAlign='t', hAlign='l', grid=(2, 0))
    self.pathData = LineEdit(self, vAlign='t', grid=(2, 1))
    self.pathData.setValidator(FilePathValidator(parent=self.pathData, spectrum=self.spectrum))
    self.pathButton = Button(self, grid=(2, 2), callback=self._getSpectrumFile, icon='icons/applications-system')
    if self.spectrum.project._appBase.ui.mainWindow is not None:
      mainWindow = self.spectrum.project._appBase.ui.mainWindow
    else:
      mainWindow = self.spectrum.project._appBase._mainWindow
    self.pythonConsole = mainWindow.pythonConsole
    self.logger = self.spectrum.project._logger

    self.setWindowTitle("Spectrum Properties")

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
    else:
      self.pathData.setText(apiDataStore.fullPath)
    self.pathData.editingFinished.connect(self._queueSetSpectrumPath)
    chemicalShiftListLabel = Label(self, text="Chemical Shift List ", vAlign='t', hAlign='l', grid=(3, 0))
    self.chemicalShiftListPulldown = PulldownList(self, vAlign='t', grid=(3, 1), texts=[csList.pid
                                                                                        for csList in spectrum.project.chemicalShiftLists]
                                                                                       +['<New>'], callback=self._queueChemicalShiftListChange)
    pidLabel = Label(self, text="PID ", vAlign='t', hAlign='l', grid=(5, 0))
    pidData = Label(self, text=spectrum.pid, vAlign='t', grid=(5, 1))
    if spectrum.dimensionCount == 1:
      colourLabel = Label(self, text="Colour", vAlign='t', hAlign='l', grid=(6, 0))
      self.colourBox = PulldownList(self, vAlign='t', hAlign='l', grid=(6, 1))
      for item in spectrumColours.items():
        pix=QtGui.QPixmap(QtCore.QSize(20, 20))
        pix.fill(QtGui.QColor(item[0]))
        self.colourBox.addItem(icon=QtGui.QIcon(pix), text=item[1])
      self.colourBox.setCurrentIndex(list(spectrumColours.keys()).index(spectrum.sliceColour))
      self.colourBox.currentIndexChanged.connect(partial(self._changedColourComboIndex, spectrum))
      colourButton = Button(self, vAlign='t', hAlign='l', grid=(6, 2), hPolicy='fixed',
                            callback=partial(self._queueSetSpectrumColour, spectrum), icon='icons/colours')
      spectrumTypeLabel = Label(self, text="Experiment Type ", vAlign='t', hAlign='l', grid=(7, 0))
      spectrumType = PulldownList(self, vAlign='t', grid=(7, 1))
      spectrumType.addItems(SPECTRA)

      spectrumType.setCurrentIndex(spectrumType.findText(spectrum.experimentName))
      spectrumScalingLabel = Label(self, text='Spectrum Scaling', vAlign='t', hAlign='l', grid=(8, 0))
      self.spectrumScalingData = LineEdit(self, text=str(self.spectrum.scale), vAlign='t', hAlign='l', grid=(8, 1))
      self.spectrumScalingData.editingFinished.connect(self._queueSpectrumScaleChange)

      recordingDataLabel = Label(self, text="Date Recorded ", vAlign='t', hAlign='l', grid=(10, 0))
      noiseLevelLabel = Label(self, text="Noise Level ", vAlign='t', hAlign='l', grid=(11, 0))
      noiseLevelData = LineEdit(self)
      if spectrum._apiDataSource.noiseLevel is not None:
        noiseLevelData.setText(str('%.3d' % spectrum._apiDataSource.noiseLevel))
      else:
        noiseLevelData.setText('None')
    else:
      spectrumTypeLabel = Label(self, text="Spectrum Type ", vAlign='t', hAlign='l', grid=(6, 0))
      self.spectrumType = PulldownList(self, vAlign='t', grid=(6, 1))
      axisCodes = []
      for isotopeCode in spectrum.isotopeCodes:
        axisCodes.append(''.join([code for code in isotopeCode if not code.isdigit()]))

      self.atomCodes = tuple(sorted(axisCodes))
      self.spectrumType.addItems(list(self.experimentTypes[spectrum.dimensionCount].get(self.atomCodes).keys()))

      # Get the text that was used in the pulldown from the refExperiment
      apiRefExperiment = spectrum._wrappedData.experiment.refExperiment
      text = apiRefExperiment and (apiRefExperiment.synonym or apiRefExperiment.name)
      self.spectrumType.setCurrentIndex(self.spectrumType.findText(text))

      self.spectrumType.currentIndexChanged.connect(self._queueSetSpectrumType)
      self.spectrumType.setMinimumWidth(self.pathData.width()*1.95)
      self.spectrumType.setFixedHeight(25)
      spectrumScalingLabel = Label(self, text='Spectrum Scaling', vAlign='t', grid=(8, 0))
      self.spectrumScalingData = LineEdit(self, text=str(self.spectrum.scale), vAlign='t', grid=(8, 1))
      self.spectrumScalingData.editingFinished.connect(self._queueSpectrumScaleChange)
      noiseLevelLabel = Label(self, text="Noise Level ", vAlign='t', hAlign='l', grid=(9, 0))
      noiseLevelData = LineEdit(self, vAlign='t', grid=(9, 1))


      if spectrum._apiDataSource.noiseLevel is None:
        noiseLevelData.setText(str('%.3d' % spectrum._apiDataSource.estimateNoise()))
      else:

        noiseLevelData.setText('%.3d' % spectrum._apiDataSource.noiseLevel)


  def _writeLoggingMessage(self, command):
    self.logger.info("spectrum = project.getByPid('%s')" % self.spectrum.pid)
    self.logger.info(command)


  def _queueSpectrumNameChange(self):
    if self.nameData.isModified():
      self._changes['spectrumName'] = partial(self._changeSpectrumName, self.nameData.text())

  def _changeSpectrumName(self, name):
    self.spectrum.rename(name)
    self._writeLoggingMessage("spectrum.rename('%s')" % self.nameData.text())


  def _queueSpectrumScaleChange(self):
    self._changes['spectrumScale'] = partial(self._setSpectrumScale, float(self.spectrumScalingData.text()))

  def _setSpectrumScale(self, scale):
    self.spectrum.scale = scale
    self._writeLoggingMessage("spectrum.scale = %s" % self.spectrumScalingData.text())
    self.pythonConsole.writeConsoleCommand("spectrum.scale = %s" % self.spectrumScalingData.text(), spectrum=self.spectrum)


  def _queueChemicalShiftListChange(self, item):
    if item == '<New>':
      listLen = len(self.chemicalShiftListPulldown.texts)
      self._changes['chemicalShiftList'] = partial(self._setNewChemicalShiftList, listLen)
    else:
      self._changes['chemicalShiftList'] = partial(self._setChemicalShiftList, item)

  def _setNewChemicalShiftList(self, listLen):
    newChemicalShiftList = self.spectrum.project.newChemicalShiftList()
    insertionIndex = listLen - 1
    self.chemicalShiftListPulldown.texts.insert(insertionIndex, newChemicalShiftList.pid)
    self.chemicalShiftListPulldown.setData(self.chemicalShiftListPulldown.texts)
    self.chemicalShiftListPulldown.setCurrentIndex(insertionIndex)
    self.spectrum.chemicalShiftList = newChemicalShiftList
    self._writeLoggingMessage("""newChemicalShiftList = project.newChemicalShiftList()\n
                                spectrum.chemicalShiftList = newChemicalShiftList""")
    self.pythonConsole.writeConsoleCommand('spectrum.chemicalShiftList = chemicalShiftList', chemicalShiftList=newChemicalShiftList, spectrum=self.spectrum)
    self.logger.info('spectrum.chemicalShiftList = chemicalShiftList')

  def _setChemicalShiftList(self, item):
    self.spectrum.chemicalShiftList = self.spectrum.project.getByPid(item)
    self.pythonConsole.writeConsoleCommand('spectrum.newChemicalShiftList = chemicalShiftList', chemicalShiftList=self.spectrum.chemicalShiftList, spectrum=self.spectrum)
    self._writeLoggingMessage("""chemicalShiftList = project.getByPid('%s')\n
                                  spectrum.chemicalShiftList = chemicalShiftList""")


  def _queueSetSpectrumType(self, value):
    self._changes['spectrumType'] = partial(self._setSpectrumType, value)

  def _setSpectrumType(self, value):
    expType = self.experimentTypes[self.spectrum.dimensionCount].get(self.atomCodes).get(self.spectrumType.currentText())
    self.spectrum.experimentType = expType
    self.pythonConsole.writeConsoleCommand('spectrum.experimentType = experimentType', experimentType=expType, spectrum=self.spectrum)
    self._writeLoggingMessage("spectrum.experimentType = '%s'" % expType)


  def _getSpectrumFile(self):
    if os.path.exists('/'.join(self.pathData.text().split('/')[:-1])):
      currentSpectrumDirectory = '/'.join(self.pathData.text().split('/')[:-1])
    else:
      currentSpectrumDirectory = os.path.expanduser('~')
    dialog = FileDialog(self, text='Select Spectrum File', directory=currentSpectrumDirectory,
                        fileMode=1, acceptMode=0,
                        preferences=self.spectrum.project._appBase.preferences.general)
    directory = dialog.selectedFiles()
    if len(directory) > 0:
      self.pathData.setText(directory[0])
      self.spectrum.filePath = directory[0]


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


  def _queueSetSpectrumPath(self):
    if self.pathData.isModified():
      filePath = self.pathData.text()

      # Convert from custom repository names to full names
      filePath = ccpnUtil.expandDollarFilePath(self.spectrum._project, filePath)

      if os.path.exists(filePath):
        self._changes['spectrumFilePath'] = partial(self._setSpectrumFilePath, filePath)
      else:
        self.logger.error('Cannot set spectrum path to %s. Path does not exist' % self.pathData.text())

  def _setSpectrumFilePath(self, filePath):
    self.spectrum.filePath = filePath
    self._writeLoggingMessage("spectrum.filePath = '%s'" % filePath)
    self.pythonConsole.writeConsoleCommand("spectrum.filePath('%s')" % filePath,
                                           spectrum=self.spectrum)

    # TODO: Find a way to convert to the shortened path without setting the value in the model,
    #       then move this back to _setSpectrumPath
    apiDataSource = self.spectrum._apiDataSource
    apiDataStore = apiDataSource.dataStore

    if apiDataStore.dataLocationStore.name != 'standard':
      raise NotImplemented('Non-standard API data store locations are invalid.')

    dataUrlName = apiDataStore.dataUrl.name
    apiPathName = apiDataStore.path
    if dataUrlName == 'insideData':
      shortenedPath = '$INSIDE/{}'.format(apiPathName)
    elif dataUrlName == 'alongsideData':
      shortenedPath = '$ALONGSIDE/{}'.format(apiPathName)
    elif dataUrlName == 'remoteData':
      shortenedPath = '$DATA/{}'.format(apiPathName)
    else:
      shortenedPath = apiDataStore.fullPath
    self.pathData.setText(shortenedPath)


  def _queueSetSpectrumColour(self, spectrum):
    dialog = ColourDialog()
    newColour = dialog.getColor()
    self._changes['spectrumColour'] = partial(self._setSpectrumColour, spectrum, newColour)

  def _setSpectrumColour(self, spectrum, newColour):
    spectrum._apiDataSource.setSliceColour(newColour.name())
    self._writeLoggingMessage("spectrum.sliceColour = '%s'" % newColour.name())
    self.pythonConsole.writeConsoleCommand("spectrum.sliceColour = '%s'" % newColour.name(), spectrum=self.spectrum)
    spectrum.guiSpectrumView.plot.setPen(spectrum._apiDataSource.sliceColour)
    pix = QtGui.QPixmap(QtCore.QSize(20, 20))
    pix.fill(QtGui.QColor(newColour))
    newIndex = str(len(spectrumColours.items())+1)
    self.colourBox.addItem(icon=QtGui.QIcon(pix), text='Colour %s' % newIndex)
    spectrumColours[newColour.name()] = 'Colour %s' % newIndex
    self.colourBox.setCurrentIndex(int(newIndex)-1)

  # TODO: 1D Only.  Fix this when fixing 1D!
  def _changedColourComboIndex(self, spectrum, value):
    spectrum.sliceColour = list(spectrumColours.keys())[value]
    pix = QtGui.QPixmap(60, 10)
    pix.fill(QtGui.QColor(spectrum.sliceColour))
    self._writeLoggingMessage("spectrum.sliceColour = '%s'" % list(spectrumColours.keys())[value])
    self.pythonConsole.writeConsoleCommand("spectrum.sliceColour '%s'" % list(spectrumColours.keys())[value], spectrum=self.spectrum)



class DimensionsTab(QtGui.QWidget, Base):
  def __init__(self, spectrum, dimensions, parent=None):
    super(DimensionsTab, self).__init__(parent)
    self.spectrum = spectrum
    self._changes = dict()

    if self.spectrum.project._appBase.ui.mainWindow is not None:
      mainWindow = self.spectrum.project._appBase.ui.mainWindow
    else:
      mainWindow = self.spectrum.project._appBase._mainWindow

    self.pythonConsole = mainWindow.pythonConsole
    self.logger = self.spectrum.project._logger

    Label(self, text="Dimension ", grid=(1, 0), hAlign='l', vAlign='t',)

    self.layout().addItem(QtGui.QSpacerItem(0, 10), 0, 0)
    for i in range(dimensions):
      dimLabel = Label(self, text='%s' % str(i+1), grid =(1, i+1), vAlign='t', hAlign='l')

    for i in range(dimensions):
      Label(self, text="Axis Code ", grid=(2, 0), vAlign='t', hAlign='l')
      Label(self, text=str(spectrum.axisCodes[i]), grid=(2, i+1),  hAlign='l', vAlign='t',)
      Label(self, text="Point Counts ", grid=(3, 0), vAlign='t', hAlign='l')
      Label(self, text=str(spectrum.pointCounts[i]), grid=(3, i+1), vAlign='t', hAlign='l')
      Label(self, text="Dimension Type ", grid=(4, 0), vAlign='t', hAlign='l')
      Label(self, text=spectrum.dimensionTypes[i], grid=(4, i+1), vAlign='t', hAlign='l')
      Label(self, text="Spectrum Width (ppm) ", grid=(5, 0), vAlign='t', hAlign='l')
      Label(self, text=str("%.3f" % spectrum.spectralWidths[i]), grid=(5, i+1), vAlign='t', hAlign='l')
      Label(self, text="Spectral Width (Hz) ", grid=(6, 0), vAlign='t', hAlign='l')
      Label(self, text=str("%.3f" % spectrum.spectralWidthsHz[i]), grid=(6, i+1), vAlign='t', hAlign='l')

      Label(self, text="Referencing (ppm) ", grid=(7, 0), vAlign='t', hAlign='l')
      spectralReferencingData = LineEdit(self, text=str("%.3f" % spectrum.referenceValues[i]), grid=(7, i+1), vAlign='t', hAlign='l')
      spectralReferencingData.editingFinished.connect(partial(self._queueSetDimensionReferencing,
                                                              spectralReferencingData.text, i))

      Label(self, text="Referencing (points)", grid=(8, 0), vAlign='t', hAlign='l')
      spectralReferencingDataPoints = LineEdit(self, text=str("%.3f" % spectrum.referencePoints[i]), grid=(8, i+1), vAlign='t', hAlign='l')
      spectralReferencingDataPoints.editingFinished.connect(partial(self._queueSetPointDimensionReferencing,
                                                                    spectralReferencingDataPoints.text, i))

      Label(self, text="Assignment Tolerance ", grid=(9, 0),  hAlign='l')
      spectralAssignmentToleranceData = LineEdit(self, grid=(9, i+1), hAlign='l')
      spectralAssignmentToleranceData.editingFinished.connect(partial(self._queueSetAssignmentTolerances,
                                                                      spectralAssignmentToleranceData.text, i))
      if spectrum.assignmentTolerances[i] is not None:
        spectralAssignmentToleranceData.setText(str("%.3f" % spectrum.assignmentTolerances[i]))

  def _writeLoggingMessage(self, command):
    self.logger.info("spectrum = project.getByPid('%s')" % self.spectrum.pid)
    self.logger.info(command)


  def _queueSetAssignmentTolerances(self, valueGetter, dim):
    self._changes['assignmentTolerances{}'.format(dim)] = partial(self._setAssignmentTolerances,
                                                                  self.spectrum, dim, valueGetter())

  def _setAssignmentTolerances(self, spectrum, dim, value):
    assignmentTolerances = list(spectrum.assignmentTolerances)
    assignmentTolerances[dim] = float(value)
    spectrum.assignmentTolerances = assignmentTolerances
    self.pythonConsole.writeConsoleCommand("spectrum.assignmentTolerances = {0}".format(assignmentTolerances), spectrum=spectrum)
    self._writeLoggingMessage("spectrum.assignmentTolerances = {0}".format(assignmentTolerances))


  def _queueSetDimensionReferencing(self, valueGetter, dim):
    self._changes['dimensionReferencing{}'.format(dim)] = partial(self._setDimensionReferencing,
                                                                  self.spectrum, dim, valueGetter())

  def _setDimensionReferencing(self, spectrum, dim, value):
    spectrumReferencing = list(spectrum.referenceValues)
    spectrumReferencing[dim] = float(value)
    spectrum.referenceValues = spectrumReferencing
    self.pythonConsole.writeConsoleCommand("spectrum.referenceValues = {0}".format(spectrumReferencing), spectrum=spectrum)
    self._writeLoggingMessage("spectrum.referenceValues = {0}".format(spectrumReferencing))


  def _queueSetPointDimensionReferencing(self, valueGetter, dim):
    self._changes['dimensionReferencingPoint{}'.format(dim)] = partial(self._setPointDimensionReferencing,
                                                                  self.spectrum, dim, valueGetter())

  def _setPointDimensionReferencing(self, spectrum, dim, value):
    spectrumReferencing = list(spectrum.referencePoints)
    spectrumReferencing[dim] = float(value)
    spectrum.referencePoints = spectrumReferencing
    self.pythonConsole.writeConsoleCommand("spectrum.referencePoints = {0}".format(spectrumReferencing), spectrum=spectrum)
    self._writeLoggingMessage("spectrum.referencePoints = {0}".format(spectrumReferencing))



class ContoursTab(QtGui.QWidget, Base):
  def __init__(self, spectrum, parent=None):
    super(ContoursTab, self).__init__(parent)

    self.spectrum = spectrum
    if self.spectrum.project._appBase.ui.mainWindow is not None:
      mainWindow = self.spectrum.project._appBase.ui.mainWindow
    else:
      mainWindow = self.spectrum.project._appBase._mainWindow
    self.pythonConsole = mainWindow.pythonConsole
    self.logger = self.spectrum.project._logger
    positiveContoursLabel = Label(self, text="Show Positive Contours", grid=(1, 0), vAlign='t', hAlign='l')
    positiveContoursCheckBox = CheckBox(self, grid=(1, 1), checked=True, vAlign='t', hAlign='l')
    for spectrumView in self.spectrum.spectrumViews:
      if spectrumView._wrappedData.spectrumView.displayPositiveContours is True:
        positiveContoursCheckBox.setChecked(True)
      else:
        positiveContoursCheckBox.setChecked(False)
    self.layout().addItem(QtGui.QSpacerItem(0, 10), 0, 0)
    positiveContoursCheckBox.stateChanged.connect(self._changePositiveContourDisplay)
    positiveBaseLevelLabel = Label(self, text="Positive Base Level", grid=(2, 0), vAlign='c', hAlign='l')
    positiveBaseLevelData = DoubleSpinbox(self, grid=(2, 1), vAlign='t')
    positiveBaseLevelData.setMaximum(1e12)
    positiveBaseLevelData.setMinimum(0.1)
    positiveBaseLevelData.setValue(spectrum.positiveContourBase)
    positiveBaseLevelData.valueChanged.connect(partial(self._lineEditTextChanged1, spectrum))
    positiveMultiplierLabel = Label(self, text="Positive Multiplier", grid=(3, 0), vAlign='c', hAlign='l')
    positiveMultiplierData = DoubleSpinbox(self, grid=(3, 1), vAlign='t')
    positiveMultiplierData.setSingleStep(0.1)
    positiveMultiplierData.setValue(float(spectrum.positiveContourFactor))
    positiveMultiplierData.valueChanged.connect(partial(self._lineEditTextChanged2, spectrum))
    # positiveBaseLevelData.setSingleStep(positiveBaseLevelData.value()*(positiveMultiplierData.value()-1))
    # Changed to get less quickly to zero - but DoubleSpinBox is NOT right for this
    positiveBaseLevelData.setSingleStep(positiveBaseLevelData.value()*0.1)
    positiveContourCountLabel = Label(self, text="Number of positive contours", grid=(4, 0), vAlign='c', hAlign='l')
    positiveContourCountData = Spinbox(self, grid=(4, 1), vAlign='t')
    positiveContourCountData.setValue(int(spectrum._apiDataSource.positiveContourCount))
    positiveContourCountData.valueChanged.connect(partial(self._lineEditTextChanged3, spectrum))
    positiveContourColourLabel = Label(self, text="Positive Contour Colour", grid=(5, 0), vAlign='c', hAlign='l')
    self.positiveColourBox = PulldownList(self, grid=(5, 1), vAlign='t')

    for item in spectrumColours.items():
      pix=QtGui.QPixmap(QtCore.QSize(20,20))
      pix.fill(QtGui.QColor(item[0]))
      self.positiveColourBox.addItem(icon=QtGui.QIcon(pix), text=item[1])
    try:
      self.positiveColourBox.setCurrentIndex(list(spectrumColours.keys()).index(spectrum.positiveContourColour))
      self.positiveColourBox.currentIndexChanged.connect(partial(self._changePosColourComboIndex, spectrum))
    except ValueError:
      pass
    self.positiveColourButton = Button(self, grid=(5, 2), vAlign='t', hAlign='l',
                                       icon='icons/colours', hPolicy='fixed')
    self.positiveColourButton.clicked.connect(partial(self._changePosSpectrumColour, spectrum))


    negativeContoursLabel = Label(self, text="Show Negative Contours", grid=(6 ,0), vAlign='c', hAlign='l')
    negativeContoursCheckBox = CheckBox(self, grid=(6, 1), checked=True, vAlign='t', hAlign='l')
    for spectrumView in self.spectrum.spectrumViews:
      if spectrumView._wrappedData.spectrumView.displayNegativeContours is True:
        negativeContoursCheckBox.setChecked(True)
      else:
        negativeContoursCheckBox.setChecked(False)
    negativeContoursCheckBox.stateChanged.connect(self.displayNegativeContours)
    negativeBaseLevelLabel = Label(self, text="Negative Base Level", grid=(7, 0), vAlign='c', hAlign='l')
    negativeBaseLevelData = DoubleSpinbox(self, grid=(7, 1), vAlign='t')
    negativeBaseLevelData.setMaximum(-0.1)
    negativeBaseLevelData.setMinimum(-1e12)
    negativeBaseLevelData.setValue(spectrum.negativeContourBase)
    negativeBaseLevelData.valueChanged.connect(partial(self._lineEditTextChanged4, spectrum))
    negativeMultiplierLabel = Label(self, text="Negative Multiplier", grid=(8, 0), vAlign='c', hAlign='l')
    negativeMultiplierData = DoubleSpinbox(self, grid=(8, 1), vAlign='t')
    negativeMultiplierData.setValue(spectrum.negativeContourFactor)
    negativeMultiplierData.setSingleStep(0.1)

    negativeMultiplierData.valueChanged.connect(partial(self._lineEditTextChanged5, spectrum))
    # negativeBaseLevelData.setSingleStep((negativeBaseLevelData.value()*-1)*negativeMultiplierData.value()-1)
    # Changed to get less quickly to zero - but DoubleSpinBox is NOT right for this
    negativeBaseLevelData.setSingleStep((negativeBaseLevelData.value()*-1)*0.1)
    negativeContourCountLabel = Label(self, text="Number of negative contours", grid=(9, 0), vAlign='c', hAlign='l')
    negativeContourCountData = Spinbox(self, grid=(9, 1), vAlign='t')
    negativeContourCountData.setValue(spectrum.negativeContourCount)
    negativeContourCountData.valueChanged.connect(partial(self._lineEditTextChanged6, spectrum))
    negativeContourColourLabel = Label(self, text="Colour",grid=(10, 0), vAlign='c', hAlign='l')
    self.negativeColourBox = PulldownList(self, grid=(10, 1), vAlign='t')
    for item in spectrumColours.items():
      pix=QtGui.QPixmap(QtCore.QSize(20,20))
      pix.fill(QtGui.QColor(item[0]))
      self.negativeColourBox.addItem(icon=QtGui.QIcon(pix), text=item[1])
    try:
      self.negativeColourBox.setCurrentIndex(list(spectrumColours.keys()).index(spectrum.negativeContourColour))
      self.negativeColourBox.currentIndexChanged.connect(partial(self._changeNegColourComboIndex, spectrum))
    except ValueError:
      pass

    self.negativeColourButton = Button(self, grid=(10, 2), icon='icons/colours', hPolicy='fixed',
                                       vAlign='t', hAlign='l')
    self.negativeColourButton.clicked.connect(partial(self._changeNegSpectrumColour, spectrum))

    Label(self, text="Note: Changes on this tab are applied immediately.", grid=(11, 0), vAlign='b', hAlign='l')


  def _writeLoggingMessage(self, command):
    self.logger.info("spectrum = project.getByPid('%s')" % self.spectrum.pid)
    self.logger.info(command)

  def _changePositiveContourDisplay(self, state):
    if state == QtCore.Qt.Checked:
      for spectrumView in self.spectrum.spectrumViews:
        spectrumView.displayPositiveContours = True
        self.logger.info("spectrumView = ui.getByGid('%s')" % spectrumView.pid)
        self.logger.info("spectrumView.displayPositiveContours = True")

    else:
      for spectrumView in self.spectrum.spectrumViews:
        spectrumView.displayPositiveContours = False
        self.logger.info("spectrumView = ui.getByGid('%s')" % spectrumView.pid)
        self.logger.info("spectrumView.displayPositiveContours = False")

  def displayNegativeContours(self, state):
    if state == QtCore.Qt.Checked:
      for spectrumView in self.spectrum.spectrumViews:
        spectrumView.displayNegativeContours = True
        self.logger.info("spectrumView = ui.getByGid('%s')" % spectrumView.pid)
        self.logger.info("spectrumView.displayNegativeContours = True")
    else:
      for spectrumView in self.spectrum.spectrumViews:
        spectrumView.displayNegativeContours = False
        self.logger.info("spectrumView = ui.getByGid('%s')" % spectrumView.pid)
        self.logger.info("spectrumView.displayNegativeContours = False")


  def _lineEditTextChanged1(self, spectrum, value):
    spectrum.positiveContourBase = float(value)
    self._writeLoggingMessage("spectrum.positiveContourBase = %f" % float(value))
    self.pythonConsole.writeConsoleCommand("spectrum.positiveContourBase = %f" % float(value), spectrum=spectrum)

  def _lineEditTextChanged2(self, spectrum, value):
    spectrum.positiveContourFactor = float(value)
    self._writeLoggingMessage("spectrum.positiveContourFactor = %f" % float(value))
    self.pythonConsole.writeConsoleCommand("spectrum.positiveContourFactor = %f" % float(value), spectrum=spectrum)

  def _lineEditTextChanged3(self, spectrum, value):
    spectrum.positiveContourCount = int(value)
    self._writeLoggingMessage("spectrum.positiveContourCount = %d" % int(value))
    self.pythonConsole.writeConsoleCommand("spectrum.positiveContourCount = %d" % int(value), spectrum=spectrum)

  def _lineEditTextChanged4(self, spectrum, value):
    spectrum.negativeContourBase = float(value)
    self._writeLoggingMessage("spectrum.negativeContourBase = %f" % float(value))
    self.pythonConsole.writeConsoleCommand("spectrum.negativeContourBase = %f" % float(value), spectrum=spectrum)

  def _lineEditTextChanged5(self, spectrum, value):
    spectrum.negativeContourFactor = float(value)
    self._writeLoggingMessage("spectrum.negativeContourFactor = %f" % float(value))
    self.pythonConsole.writeConsoleCommand("spectrum.negativeContourFactor = %f" % float(value), spectrum=spectrum)

  def _lineEditTextChanged6(self, spectrum, value):
    spectrum.negativeContourCount = int(value)
    self._writeLoggingMessage("spectrum.negativeContourCount = %d" % int(value))
    self.pythonConsole.writeConsoleCommand("spectrum.negativeContourCount = %d" % int(value), spectrum=spectrum)

  def _changePosSpectrumColour(self, spectrum):
    dialog = ColourDialog()
    newColour = dialog.getColor()
    if newColour is not None:
      spectrum.positiveContourColour = newColour.name()
      self._writeLoggingMessage("spectrum.positiveContourColour = '%s'" % newColour.name())
      self.pythonConsole.writeConsoleCommand("spectrum.positiveContourColour = '%s'" % newColour.name(), spectrum=spectrum)
      pix=QtGui.QPixmap(QtCore.QSize(20,20))
      pix.fill(QtGui.QColor(newColour))
      newIndex = str(len(spectrumColours.items())+1)
      self.positiveColourBox.addItem(icon=QtGui.QIcon(pix), text='Colour %s' % newIndex)
      self.negativeColourBox.addItem(icon=QtGui.QIcon(pix), text='Colour %s' % newIndex)
      spectrumColours[newColour.name()] = 'Colour %s' % newIndex
      self.positiveColourBox.setCurrentIndex(int(newIndex)-1)


  def _changeNegSpectrumColour(self, spectrum):
    dialog = ColourDialog()
    newColour = dialog.getColor()
    if newColour is not None:
      spectrum.negativeContourColour = newColour.name()
      self._writeLoggingMessage("spectrum.negativeContourColour = %s" % newColour.name())
      self.pythonConsole.writeConsoleCommand("spectrum.negativeContourColour = '%s'" % newColour.name(), spectrum=spectrum)
      pix=QtGui.QPixmap(QtCore.QSize(20,20))
      pix.fill(QtGui.QColor(newColour))
      newIndex = str(len(spectrumColours.items())+1)
      self.negativeColourBox.addItem(icon=QtGui.QIcon(pix), text='Colour %s' %newIndex)
      self.positiveColourBox.addItem(icon=QtGui.QIcon(pix), text='Colour %s' %newIndex)
      spectrumColours[newColour.name()] = 'Colour %s' % newIndex
      self.negativeColourBox.setCurrentIndex(int(newIndex)-1)


  def _changePosColourComboIndex(self, spectrum, value):

    newColour = list(spectrumColours.keys())[value]
    spectrum.positiveContourColour = newColour
    self._writeLoggingMessage("spectrum.positiveContourColour = '%s'" % newColour)
    self.pythonConsole.writeConsoleCommand("spectrum.positiveContourColour = '%s'" % newColour, spectrum=spectrum)

  def _changeNegColourComboIndex(self, spectrum, value):

    newColour = list(spectrumColours.keys())[value]
    spectrum._apiDataSource.negativeContourColour = newColour
    self._writeLoggingMessage("spectrum.negativeContourColour = %s" % newColour)
    self.pythonConsole.writeConsoleCommand("spectrum.negativeContourColour = '%s'" % newColour, spectrum=spectrum)
