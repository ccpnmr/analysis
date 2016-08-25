from PyQt4 import QtCore, QtGui

import decimal
from functools import partial
from PyQt4 import QtCore, QtGui
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from collections import OrderedDict

class ExcludeRegions(QtGui.QWidget):

  '''This create a widget group to exclude Regions from the Spectrum when automatically peak picking '''

  def __init__(self, parent=None,**kw):
    super(ExcludeRegions, self).__init__(parent)


    self.solvents = {'Acetic Acid-d4': [0,0, 2.14,2.0, 11.75,11.65],
                     'Acetone-d6 & Water': [0,0, 2.15,2.0, 2.90, 2.80],
                     'Acetonitrile-d3 & water': [0,0, 2.20,1.94],
                     'Benzene-d6 & water': [0,0, 0.60,0.50, 7.25,7.15],
                     'Chloroform-d': [0,0, 1.60,1.50, 7.35,7.25],
                     'Deuterium Oxide': [0,0, 4.75,4.65],
                     'Dichloromethane-d2 & water': [0,0, 1.60,1.50, 5.42,5.32],
                     'Dimethyl Sulfoxide-d6': [0,0, 2.60,2.50, 3.40,3.30],
                     'Dimethylformamide-d7 & water': [0,0, 8.11,8.01, 2.99,2.91, 2.83,2.73, 3.60,3.50],
                     'p-Dioxane-d8 & water':[0,0, 2.60,2.50, 3.63,3.50 ],
                     'Tetrachloromethane-d2 & water': [0,0, 1.70,1.60, 6.10,6.00],
                     'Ethanol-d6 & water': [0,0, 1.21,1.11, 3.66,3.56, 5.40,5.29],
                     'Methanol-d4': [0,0, 3.40,3.30, 4.90,4.80],
                     'Pyridine-d5 & water': [0,0, 8.74,8.84, 7.68,7.58, 7.32,7.22, 5.10,5.00],
                     'Trifluoroacetic acid-d': [0,0, 11.60,11.50],
                     'Tetrahydrofuran-d8 & water': [0,0, 3.68,3.58, 2.60,2.50, 1.83,1.73],
                     'New regions': [0,0, 0.2, 0.1],
                     'Toulene-d8 & water': [0,0, 7.18,6.98, 2.19,2.09, 2.50,2.40, 5.10,5.00],
                     'Trifluoroethanol-d3 & water':[0,0, 5.12,5.02, 3.98,3.88],
                     'Carbon Tetrachloride & water ': [0,0, 1.20, 1.10],
                     'water': [0,0, 5, 4.5]}

    self.pulldownSolvents = PulldownList(self, grid=(0, 1), hAlign='c')
    self.pulldownSolvents.activated[str].connect(self._addRegions)
    for solvent in sorted(self.solvents):
      self.pulldownSolvents.addItem(solvent)
    self.SolventsLabel = Label(self, "Select Regions or \nsolvents to exclude", grid=(0, 0), hAlign='c')
    self.scrollArea = ScrollArea(self, grid=(2, 0), gridSpan=(2,2))
    self.scrollArea.setWidgetResizable(True)
    self.scrollAreaWidgetContents = QtGui.QFrame()
    self.scrollArea.setWidget(self.scrollAreaWidgetContents)
    self.regioncount = 0
    self.excludedRegions = []
    self.excludedSolvents = []
    self.comboBoxes = []


  def _addRegions(self, pressed):
    '''   '''

    widgetList = []
    for solvent in sorted(self.solvents):
      solventValues = [(),()]
      if pressed == ('%s' %solvent):
        solventValues[0] += (solvent,)
        self.solventType = Label(self.scrollAreaWidgetContents, text=solvent, grid=(self.regioncount,0))
        self.closebutton = Button(self.scrollAreaWidgetContents,'Remove from selection', grid=(self.regioncount,1))
        values = (self.solvents[solvent])
        self.selectedSolventValue = sorted(values)
        self.new_list = [values[i:i+2] for i in range(0, len(values), 2)]
        del self.new_list[0:1]  #delete [0,0] used only to set the layout

        self.excludedRegions.append(self.new_list)

        valueCount = len(values)//2
        self.positions = [(i+self.regioncount, j) for i in range(valueCount)
                          for j in range(2)]
        for self.position, values in zip(self.positions, sorted(values)):
          if values == 0:
            continue
          self.regioncount += valueCount
          self.spin = DoubleSpinbox(self.scrollAreaWidgetContents, grid=(self.position))
          self.spin.setSingleStep(0.01)
          self.spin.setMinimum(-20)
          self.spin.setPrefix('ppm')
          self.spin.setValue(values)
          widgetList.append(self.spin)
          solventValues[1]+= (self.spin,)
      self.excludedSolvents.append(solventValues)
    self.comboBoxes.append(widgetList)
    self.closebutton.clicked.connect(partial(self._deleteRegions, self.positions))


  def getSolventsAndValues(self):
    self.excludedSolvents = [x for x in self.excludedSolvents if len(x[0])>0]
    solventsAndValues = []
    for item in self.excludedSolvents:
      try:
        solvent, widgets = item
        values = [round(widget.value(),2) for widget in widgets]
        values.insert(0, 0)
        values.insert(0, 0)
        solventsAndValues.append(((solvent[0]),values))
      except:
        pass
    return OrderedDict(solventsAndValues)

  def _getExcludedRegions(self):
    excludedRegions = []
    self.excludedSolvents = [x for x in self.excludedSolvents if len(x[0]) > 0]
    for item in self.excludedSolvents:
      solvent, widgets = item
      try: # try because widgets can be dinamically deleted
        self.values = [round(widget.value(), 2) for widget in widgets]
        pairedValues = list(self._chunks(self.values, 2))
        excludedRegions.append(pairedValues)
      except:
        pass
    if len(excludedRegions)>0:
      return [item for sublist in excludedRegions for item in sublist]


  def _chunks(self, l, n):
    """Yield successive n-sized chunks from list. Needed this format!"""
    for i in range(0, len(l), n):
      yield sorted(l[i:i + n], key=float, reverse=True)

  def _deleteRegions(self, positions):
    '''   '''
    for position in positions:
      widget1 = self.scrollAreaWidgetContents.layout().itemAtPosition(*position).widget()
      if widget1 is self.solventType:
        widget1.hide()
      else:
        widget1.deleteLater()

class PickPeak1DPopup(QtGui.QDialog):

  def __init__(self, parent=None, project=None,  **kw):
    super(PickPeak1DPopup, self).__init__(parent)
    self.project = project
    self.mainWindow = parent
    self.application = self.mainWindow.application
    self._setMainLayout()
    self._setTabs()
    self._setWidgets()
    self._addWidgetsToLayout()

  def _setMainLayout(self):
    self.mainLayout = QtGui.QGridLayout()
    self.setLayout(self.mainLayout)
    self.setWindowTitle("Pick Peak 1D")
    self.resize(300, 400)

  def _setTabs(self):
    self.tabWidget = QtGui.QTabWidget()
    self.tabGeneralSetup = QtGui.QFrame()
    self.tabGeneralSetupLayout = QtGui.QGridLayout()
    self.tabGeneralSetup.setLayout(self.tabGeneralSetupLayout)
    self.excludedRegionsTab = ExcludeRegions()
    self.tabWidget.addTab(self.tabGeneralSetup, 'General')
    self.tabWidget.addTab(self.excludedRegionsTab, 'Exclude Regions')
    self._setSelectionScrollArea()

  def _setSelectionScrollArea(self):

    self.scrollArea = ScrollArea(self)
    self.scrollArea.setWidgetResizable(True)
    self.scrollAreaWidgetContents = QtGui.QFrame()
    self.scrollArea.setWidget(self.scrollAreaWidgetContents)

  def _setWidgets(self):

    self.selectSpectraOption = RadioButtons(self,
                                              texts=['Spectra', 'Groups'],
                                              selectedInd=0,
                                              callback=self.showSpectraOption,
                                              tipTexts=None)
    self._addSpectrumCheckBoxes()
    self._addSpectrumGroupsCheckBoxes()


    self.noiseLevelLabel = Label(self, text='Noise Level Threshold')
    self.noiseLevelRadioButtons = RadioButtons(self,
                                               texts=['Estimated', 'Manual'],
                                               selectedInd=0,
                                               callback=self._noiseLevelCallBack,
                                               tipTexts=None)
    self.noiseLevelSpinbox = DoubleSpinbox(self)
    self.noiseLevelSpinbox.hide()
    self.noiseLevelSpinbox.setValue(10000)
    self.noiseLevelSpinbox.setMaximum(10000000)

    self.maximumFilterSize = Label(self, text="Select Maximum Filter Size")
    self.maximumFilterSizeSpinbox = Spinbox(self)
    self.maximumFilterSizeSpinbox.setValue(5)
    self.maximumFilterSizeSpinbox.setMaximum(15)

    modes = ['wrap','reflect', 'constant', 'nearest', 'mirror' ]
    self.maximumFilterMode = Label(self, text="Select Maximum Filter Mode")
    self.maximumFilterModePulldownList = PulldownList(self, texts=modes)

    self.pickCancelButtons = ButtonList(self,
                                        texts=['Cancel', 'Find Peaks'],
                                        callbacks=[self.reject, self._pickFromSelectedSpectra],
                                        tipTexts=[None, None],
                                        direction='h', hAlign='r')
    self.pickNegativeLabel = Label(self, text='Pick negative peaks')
    self.pickNegativeCheckBox = CheckBox(self, checked=True)

  def _addWidgetsToLayout(self):
    self.mainLayout.addWidget(self.tabWidget, 0, 0, 1, 2)
    self.tabGeneralSetupLayout.addWidget(self.selectSpectraOption, 0, 0)
    self.tabGeneralSetupLayout.addWidget(self.scrollArea, 1, 0, 1, 2)
    self.tabGeneralSetupLayout.addWidget(self.noiseLevelLabel, 2, 0)
    self.tabGeneralSetupLayout.addWidget(self.noiseLevelRadioButtons, 2, 1)
    self.tabGeneralSetupLayout.addWidget(self.noiseLevelSpinbox, 3, 1)

    self.tabGeneralSetupLayout.addWidget(self.maximumFilterSize, 4, 0)
    self.tabGeneralSetupLayout.addWidget(self.maximumFilterSizeSpinbox, 4, 1)
    self.tabGeneralSetupLayout.addWidget(self.maximumFilterMode, 5, 0)
    self.tabGeneralSetupLayout.addWidget(self.maximumFilterModePulldownList, 5, 1)
    self.tabGeneralSetupLayout.addWidget(self.pickNegativeLabel, 6, 0)
    self.tabGeneralSetupLayout.addWidget(self.pickNegativeCheckBox, 6, 1)
    self.mainLayout.addWidget(self.pickCancelButtons, 10, 1)

  def showSpectraOption(self):
    if self.selectSpectraOption.get() == 'Spectra':
      for cb in self.allCheckBoxes:
        self.spectrumCheckBox.show()
        self.spGroupsCheckBox.hide()
        cb.show()
      for sg in self.allSG_CheckBoxes:
        sg.hide()

    else:
      self.spectrumCheckBox.hide()
      for cb in self.allCheckBoxes:
        cb.hide()
      for sg in self.allSG_CheckBoxes:
        sg.show()
      self.spGroupsCheckBox.show()

  def _noiseLevelCallBack(self):
    selected = self.noiseLevelRadioButtons.get()
    if selected == 'Estimated':
      self.noiseLevelSpinbox.hide()
    else:
      self.noiseLevelSpinbox.show()

  def _addSpectrumCheckBoxes(self):
    self.spectrumCheckBox = CheckBox(self.scrollAreaWidgetContents, text='Select All',grid=(0, 0))
    self.spectrumCheckBox.stateChanged.connect(self._checkAllSpectra)
    self.allCheckBoxes = []
    for i, spectrum in enumerate(self.project.spectra):
      self.spectrumCheckBox = CheckBox(self.scrollAreaWidgetContents, text=str(spectrum.id), grid=(i+1, 0))
      self.allCheckBoxes.append(self.spectrumCheckBox)

  def _addSpectrumGroupsCheckBoxes(self):
    self.spGroupsCheckBox = CheckBox(self.scrollAreaWidgetContents, text='Select All SG', grid=(0, 0))
    self.spGroupsCheckBox.hide()
    self.spGroupsCheckBox.stateChanged.connect(self._checkAllSpectrumGroups)
    self.allSG_CheckBoxes = []
    for i, sg in enumerate(self.project.spectrumGroups):
      self.spectrumGroupCheckBox = CheckBox(self.scrollAreaWidgetContents, text=str(sg.pid), grid=(i + 1, 0))
      self.allSG_CheckBoxes.append(self.spectrumGroupCheckBox)
      self.spectrumGroupCheckBox.hide()


  def _checkAllSpectrumGroups(self, state):
    if len(self.allCheckBoxes) > 0:
      for sg in self.allSG_CheckBoxes:
        if state == QtCore.Qt.Checked:
          sg.setChecked(True)
        else:
          sg.setChecked(False)

  def _checkAllSpectra(self, state):
    if len(self.allCheckBoxes)>0:
        for cb in self.allCheckBoxes:
          if state == QtCore.Qt.Checked:
            cb.setChecked(True)
          else:
            cb.setChecked(False)

  def _getSelectedSpectra(self):
    spectra = []
    for cb in self.allCheckBoxes:
      if cb.isChecked():
        spectrum = self.project.getByPid('SP:'+str(cb.text()))
        spectra.append(spectrum)
    return spectra

  def _getSpectrumGroupsSpectra(self):
    spectra = []
    for sg in self.allSG_CheckBoxes:
      if sg.isChecked():
        spectrumGroup = self.project.getByPid(str(sg.text()))
        spectra.append(spectrumGroup.spectra)
    if len(spectra)>0:
      return list(spectra[0])
    else:
      return spectra


  def _getNoiseThreshold(self):
    selected = self.noiseLevelRadioButtons.get()
    values = (0, self.noiseLevelSpinbox.value())
    for selection, value in zip(self.noiseLevelRadioButtons.texts, values):
      if selected == str(selection):
        return value

  def _pickFromSelectedSpectra(self):

    spectra = list(set(self._getSelectedSpectra()+self._getSpectrumGroupsSpectra()))
    negativePeaks = self.pickNegativeCheckBox.get()
    size = self.maximumFilterSizeSpinbox.value()
    mode = self.maximumFilterModePulldownList.getText()
    ignoredRegions = self.excludedRegionsTab._getExcludedRegions()
    noiseThreshold = self._getNoiseThreshold()
    for spectrum in spectra:
      spectrum.peakLists[0].pickPeaks1dFiltered(size=size, mode=mode, ignoredRegions=ignoredRegions,
                                                noiseThreshold=noiseThreshold, negativePeaks=negativePeaks)
    self.accept()
