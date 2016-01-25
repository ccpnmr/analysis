__author__ = 'luca'

from PyQt4 import QtCore, QtGui
import sys
from ccpncore.gui.Base import Base
from ccpncore.gui.DoubleSpinbox import DoubleSpinbox
from ccpncore.gui.Button import Button
from ccpncore.gui.CheckBox import CheckBox
from ccpncore.gui.Label import Label
from ccpncore.gui.LineEdit import LineEdit
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.Slider import Slider
from ccpncore.gui.Spinbox import Spinbox
from ccpncore.gui.ScrollArea import ScrollArea
from ccpn.lib.Sample import setupSamples
from application.core.modules.SampleAnalysis import SampleAnalysis

from functools import partial

solvents = {'Acetic Acid-d4': [0,0, 2.14,2.0, 11.75,11.65],
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

class SamplePopup(QtGui.QDialog):


 def __init__(self, parent=None, project=None,  **kw):
  super(SamplePopup, self).__init__(parent)
  Base.__init__(self, **kw)
  self.project = project

  buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Cancel)
  buttonBox.rejected.connect(self.reject)

  self.tabWidget = QtGui.QTabWidget()
  self.setup = GeneralSetup()

  self.tabWidget.addTab(self.setup, 'General Setup')
  self.excludedRegionsTab = ExcludeRegions()
  self.tabWidget.addTab(self.excludedRegionsTab, 'Exclude Regions')
  mainLayout = QtGui.QGridLayout()
  mainLayout.addWidget(self.tabWidget, 0, 0, 1, 3)
  mainLayout.addWidget(buttonBox, 4, 1)
  self.setLayout(mainLayout)
  pickpeakscheckBox = CheckBox(self, grid=(1, 1), checked=True)
  pickpeakscheckBoxLabel =  Label(self, text="Pick peaks automatically:", grid=(1, 0))

  self.distance = DoubleSpinbox(self, grid=(2, 1))
  self.distance.setRange(0.00, 0.20)
  self.distance.setSingleStep(0.01)
  self.distance.setSuffix(" ppm")
  distanceLabel = Label(self, text="Minimal distance between peaks greater than:", grid=(2, 0))

  noiseLabel = Label(self, text="Noise threshold", grid=(3, 0), hAlign='r')
  self.noise = DoubleSpinbox(self, grid=(3, 1), hAlign='l')
  # self.noise.setValue(10000)
  self.noise.setMaximum(10000000)


  self.performButton = Button(self, grid=(4, 2), text='Perform')
  self.performButton.clicked.connect(self.perform)

  self.resize(500, 280)
  self.setWindowTitle("Mixture Generation Setup")


 def perform(self):
    '''
    This function gets all the setting given by the user and runs the mixture generation algorithm ('setupSamples')

    '''

    excludedRegions = []
    noiseThreshold = self.noise.value()
    for comboboxPair in (self.excludedRegionsTab.comboBoxes):

      try:
        if comboboxPair[0].value() is not None:
          firstPair = (sorted([comboboxPair[0].value(), comboboxPair[1].value()],reverse=True))
          excludedRegions.append(firstPair)
        if comboboxPair[2].value() is not None:
          secondPair = (sorted([comboboxPair[2].value(), comboboxPair[3].value()],reverse=True))
          excludedRegions.append(secondPair)
        if comboboxPair[4].value() is not None:
          thirdPair = (sorted([comboboxPair[4].value(), comboboxPair[5].value()],reverse=True))
          excludedRegions.append(thirdPair)
        if comboboxPair[6].value() is not None:
          fourthPair = (sorted([comboboxPair[6].value(), comboboxPair[7].value()],reverse=True))
          excludedRegions.append(fourthPair)
      except:
        pass

    for i in excludedRegions:
      if len(i) == 0:
        excludedRegions.remove(i)


    # sideBar = self.project._appBase.mainWindow.sideBar
    #
    # refData = sideBar.spectrumItem
    # refCount = sideBar.spectrumReference.childCount()
    # spectra = []
    #
    # for i in range(refCount):
    #   print(i)
    #   item = refData.child(i)
    #   itemCount = item.childCount()
    #   for j in range(itemCount):
    #     spectrumPid = item.child(j).text(0)
    #     spectrum = self.project.getByPid(spectrumPid)
    #
    #     spectra.append(spectrum)
    #     spectrum.peakLists[0].pickPeaks1dFiltered(ignoredRegions=excludedRegions, noiseThreshold=noiseThreshold)
    #     sampleTab = sideBar.SamplesItems

    sideBar = self.project._appBase.mainWindow.sideBar

    refData = sideBar.spectrumItem
    refCount = sideBar.spectrumItem.childCount() #  item under sidebar spectra tree

    spectra = []

    for i in range(refCount):
      item = refData.child(i)

      itemCount = item.childCount()
      for j in range(itemCount):
        spectrumPid = item.child(j).text(0)
        peakList = self.project.getByPid(spectrumPid)
        spectrum = peakList.spectrum

        spectra.append(spectrum)
        spectrum.peakLists[0].pickPeaks1dFiltered(ignoredRegions=excludedRegions, noiseThreshold=noiseThreshold)
        sampleTab = sideBar.samplesItem




    minimalDistance = self.distance.value()
    if self.setup.checkBox1.isChecked():
      value = (self.setup.spinBoxSA.value())
      samples = setupSamples(self.project.substances, value , 'nSamples', minimalOverlap=minimalDistance)


    elif self.setup.checkBox2.isChecked():
      value = (int(self.setup.spinBoxcomponent.value()))
      samples = setupSamples(self.project.substances, value, 'nComponentsPerSample', minimalOverlap=minimalDistance)


    for sample in samples:
      newItem = sideBar.addItem(sampleTab, sample)

      for sampleComponent in sample.sampleComponents[0:]:
        sideBar.addItem(newItem, sampleComponent)

        # for peakCollection in sample.peakCollections[0:]:
        #   self.spectrum = self.project.getByPid('SP:'+peakCollection.name)
        #   sideBar.addItem(newItem, self.spectrum)

    # #----- open the analysis table ----#

    sampletable = SampleAnalysis(self.project)
    self.project._appBase.mainWindow.dockArea.addDock(sampletable)
    self.accept()

                                     # ----- tab1 Sample setup -----
class GeneralSetup(QtGui.QWidget):
  '''  This creates the first tab with settings to create virtual samples (Mixtures)
  '''

  def __init__(self, parent=None):
    super(GeneralSetup, self).__init__(parent)

    # --- Select number of Mixtures ---
    self.checkBox1 = CheckBox(self, grid=(0, 0), hAlign='c', checked= False)
    nSampleButton= Button(self, text="Select number of Mixtures", grid=(0, 1))
    nSampleButton.setFlat(True)
    nSampleButton.clicked.connect(self.nSampleIsChecked)

    self.checkBox1.toggled.connect(self.show_nSamples)
    self.sliderSA = Slider(self, startVal = 2, endVal = 100, value=None,
               direction='h', step=1, bigStep=None, grid =(1, 1))
    self.spinBoxSA = Spinbox(self, grid=(1, 0))
    self.spinBoxSA.setRange(2, 100)
    self.sliderSA.valueChanged.connect(self.spinBoxSA.setValue)
    self.spinBoxSA.valueChanged.connect(self.sliderSA.setValue)
    self.spinBoxSA.hide()

    self.sliderSA.hide()

    # --- Select number of Components per Mixtures ---
    self.checkBox2 = CheckBox(self, grid=(3, 0), hAlign='c', checked= False)
    nComponentButton = Button(self, text="Select number of Components", grid=(3, 1))
    nComponentButton.setFlat(True)
    nComponentButton.clicked.connect(self.nComponentsIsChecked)

    self.checkBox2.toggled.connect(self.show_nComponents)
    self.sliderComponent  = Slider(self, startVal = 2, endVal = 20, value=None,
                                  direction='h', step=1, bigStep=None, grid =(5, 1))
    self.spinBoxcomponent = Spinbox(self, grid=(5, 0))
    self.spinBoxcomponent.setRange(2, 20)
    self.sliderComponent.valueChanged.connect(self.spinBoxcomponent.setValue)
    self.spinBoxcomponent.valueChanged.connect(self.sliderComponent.setValue)
    self.spinBoxcomponent.hide()
    self.sliderComponent.hide()

  def nSampleIsChecked(self):
    self.checkBox1.setChecked(True)

  def show_nSamples(self):
    if self.checkBox1.isChecked():
     self.checkBox2.setChecked(False)
     self.sliderSA.show()
     self.spinBoxSA.show()
    else:
     self.sliderSA.hide()
     self.spinBoxSA.hide()

  def nComponentsIsChecked(self):
    self.checkBox2.setChecked(True)

  def show_nComponents(self):
    if self.checkBox2.isChecked():
     self.checkBox1.setChecked(False)
     self.sliderComponent.show()
     self.spinBoxcomponent.show()
    else:
     self.sliderComponent.hide()
     self.spinBoxcomponent.hide()

                                   # ----- -----
class ExcludeRegions(QtGui.QWidget, Base):
  '''This create the second tab to exclude Regions from Spectrum when peak picking '''

  def __init__(self, parent=None,**kw):
    super(ExcludeRegions, self).__init__(parent)
    Base.__init__(self, **kw)

    self.pulldownSolvents = PulldownList(self, grid=(0, 1), hAlign='r')
    self.pulldownSolvents.setFixedWidth(105)
    self.pulldownSolvents.activated[str].connect(self.addRegions)
    for solvent in sorted(solvents):
      self.pulldownSolvents.addItem(solvent)
    self.SolventsLabel = Label(self, "Select Regions or \nsolvents to exclude", grid=(0, 0), hAlign='l')
    self.scrollArea = ScrollArea(self, grid=(2, 0), gridSpan=(2,2))
    self.scrollArea.setWidgetResizable(True)
    self.scrollAreaWidgetContents = QtGui.QWidget()
    self.scrollArea.setWidget(self.scrollAreaWidgetContents)
    self.regioncount = 0
    self.excludedRegions = []
    self.comboBoxes = []

  def addRegions(self, pressed):

    widgetList = []
    for solvent in sorted(solvents):
      if pressed == ('%s' %solvent):
        self.solventType = Label(self.scrollAreaWidgetContents, text=solvent, grid=(self.regioncount,0))
        self.closebutton = Button(self.scrollAreaWidgetContents,'Remove from selection', grid=(self.regioncount,1))
        values = (solvents[solvent])
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
    self.comboBoxes.append(widgetList)
    self.closebutton.clicked.connect(partial(self.deleteRegions, self.positions))

  def deleteRegions(self, positions):

    for position in positions:

      widget1 = self.scrollAreaWidgetContents.layout().itemAtPosition(*position).widget()
      if widget1 is self.solventType:
        widget1.hide()
      else:
        widget1.deleteLater()



