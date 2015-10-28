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
from ccpncore.gui.Widget import Widget
from application.core.modules.ScoringMixture import MixtureTable

from ccpn.lib.Mixture import setupMixtures
from ccpn.lib.Mixture import compareWithLevels
from functools import partial

solvents = {'Acetic Acid-d4': [0, 11.65, 2.04], 'Acetone-d6 & Water': [0, 2.05, 2.80],
          'Acetonitrile-d3 & water': [0, 1.94, 2.20], 'Benzene-d6 & water': [0, 0.50, 7.15],
          'Chloroform-d': [0, 1.50, 7.25],'Deuterium Oxide': [0, 4.65],
          'Dichloromethane-d2 & water': [0, 1.50, 5.32],'Dimethyl Sulfoxide-d6': [0, 2.50, 3.30],
          'Dimethylformamide-d7 & water': [0, 8.01, 2.91, 2.73, 3.50],
          'p-Dioxane-d8 & water':[0, 3.53, 2.40], 'Tetrachloromethane-d2 & water': [0, 6.00, 1.60],
          'Ethanol-d6 & water': [0, 5.29, 3.56, 1.11, 5.30], 'Methanol-d4': [0, 4.80, 3.30],
          'Pyridine-d5 & water': [0, 8.74, 7.58, 7.22, 5.00], 'Trifluoroacetic acid-d': [0, 11.50],
          'Tetrahydrofuran-d8 & water': [0, 3.58, 1.73, 2.50], 'Create new regions': [0, 0.1],
          'Toulene-d8 & water': [0, 7.09, 7.00, 6.98, 2.09, 2.40, 5.00],
          'Trifluoroethanol-d3 & water':[0, 5.02, 3.88],'Carbon Tetrachloride & water ': [0, 1.10]}

class MixturePopup(QtGui.QDialog):
 def __init__(self, parent=None, project=None, **kw):
  super(MixturePopup, self).__init__(parent)
  Base.__init__(self, **kw)
  self.project = project

  buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Cancel)
  buttonBox.rejected.connect(self.reject)

  self.tabWidget = QtGui.QTabWidget()
  self.setup = GeneralSetup()
  self.tabWidget.addTab(self.setup, 'General Setup')
  self.tabWidget.addTab(ExcludeRegions(), 'Exclude Regions')
  mainLayout = QtGui.QGridLayout()
  mainLayout.addWidget(self.tabWidget, 0, 0, 1, 3)
  mainLayout.addWidget(buttonBox, 3, 1)
  self.setLayout(mainLayout)
  pickpeakscheckBox = CheckBox(self, grid=(1, 1), checked=True)
  pickpeakscheckBoxLabel =  Label(self, text="Pick peaks automatically:", grid=(1, 0))
  minimalDistanceCombo = PulldownList(self, grid=(2, 1,))

  minimalDistanceCombo.addItems('>0.15ppm >0.10ppm >0.08ppm >0.06ppm >0.04ppm >0.01ppm Any'.split())
  minimalDistanceLabel = Label(self, text="Minimum distance allowed:", grid=(2, 0))

  self.performButton = Button(self, grid=(3, 2), text='Perform')
  self.performButton.clicked.connect(self.perform)

  self.resize(500, 280)
  self.setWindowTitle("Mixture Setup")



 def perform(self):

    sideBar = self.project._appBase.mainWindow.sideBar
    refData = sideBar.spectrumReference
    refCount = sideBar.spectrumReference.childCount()
    spectra = []

    for i in range(refCount):
      item = refData.child(i)
      itemCount = item.childCount()
      for j in range(itemCount):
        spectrumPid = item.child(j).text(0)
        spectrum = self.project.getByPid(spectrumPid)
        spectra.append(spectrum)
        spectrum.peakLists[0].pickPeaks1dFiltered()

        mixtureTab = sideBar.spectrumMixtures

    if self.setup.checkBox1.isChecked():
      value = (self.setup.spinBoxMX.value()+1)
      mixtures = setupMixtures(spectra, value, 'nMixtures')


    elif self.setup.checkBox2.isChecked():
      value = (int(self.setup.spinBoxcompound.value())+1)

      mixtures = setupMixtures(spectra, value, 'nCompoundsPerMixture')


    for mixture in mixtures:
      # print('Mixture pid', mixture.pid)
      # print('mixtures object =', mixtures)


      newItem = sideBar.addItem(mixtureTab, mixture)
      for peakCollection in mixture.peakCollections[1:]:
        spectrum = self.project.getByPid('SP:'+peakCollection.name)
        sideBar.addItem(newItem, spectrum)


    #----- feeds the results table ----#
    from application.core.modules.ScoringMixture import MixtureTable
    mtsm = MixtureTable(mixtureLists=mixtures)
    self.project._appBase.mainWindow.dockArea.addDock(mtsm)


    self.accept()




                                     # ----- tab1 Mixture setup -----
class GeneralSetup(QtGui.QWidget):
  def __init__(self, parent=None):
    super(GeneralSetup, self).__init__(parent)

    # --- Select number of Mixtures ---
    self.checkBox1 = CheckBox(self, grid=(0, 0), hAlign='c', checked= False)
    nMixtureLabel = Label(self, text="Select number of Mixtures", grid=(0, 1))
    self.checkBox1.toggled.connect(self.show_nMixtures)
    self.sliderMX = Slider(self, startVal = 2, endVal = 100, value=None,
               direction='h', step=1, bigStep=None, grid =(1, 1))
    self.spinBoxMX = Spinbox(self, grid=(1, 0))
    self.spinBoxMX.setRange(2, 100)
    self.sliderMX.valueChanged.connect(self.spinBoxMX.setValue)
    self.spinBoxMX.valueChanged.connect(self.sliderMX.setValue)
    self.spinBoxMX.hide()
    self.sliderMX.hide()

    # --- Select number of Compounds per Mixture ---
    self.checkBox2 = CheckBox(self, grid=(3, 0), hAlign='c', checked= False)
    nCompoundLabel = Label(self, text="Select number of Compounds", grid=(3, 1))
    self.checkBox2.toggled.connect(self.show_nCompounds)
    self.sliderCompound  = Slider(self, startVal = 2, endVal = 20, value=None,
                                  direction='h', step=1, bigStep=None, grid =(5, 1))
    self.spinBoxcompound = Spinbox(self, grid=(5, 0))
    self.spinBoxcompound.setRange(2, 20)
    self.sliderCompound.valueChanged.connect(self.spinBoxcompound.setValue)
    self.spinBoxcompound.valueChanged.connect(self.sliderCompound .setValue)
    self.spinBoxcompound.hide()
    self.sliderCompound.hide()



  def show_nMixtures(self):
    if self.checkBox1.isChecked():
     self.checkBox2.setChecked(False)
     self.sliderMX.show()
     self.spinBoxMX.show()
    else:
     self.sliderMX.hide()
     self.spinBoxMX.hide()

  def show_nCompounds(self):
    if self.checkBox2.isChecked():
     self.checkBox1.setChecked(False)
     self.sliderCompound.show()
     self.spinBoxcompound.show()
    else:
     self.sliderCompound.hide()
     self.spinBoxcompound.hide()

                                   # ----- tab2 Exclude Regions from Spectrum -----
class ExcludeRegions(QtGui.QWidget):
  def __init__(self, parent=None):
    super(ExcludeRegions, self).__init__(parent)
    self.pulldownSolvents = PulldownList(self, grid=(1, 0))
    self.pulldownSolvents.activated[str].connect(self.addRegions)
    for solvent in sorted(solvents):
      self.pulldownSolvents.addItem(solvent)
    self.SolventsLabel = Label(self, "Select solvents to exclude : ", grid=(0, 0))
    self.scrollArea = ScrollArea(self, grid=(2, 0))
    self.scrollArea.setWidgetResizable(True)
    self.scrollAreaWidgetContents = QtGui.QWidget()
    self.scrollArea.setWidget(self.scrollAreaWidgetContents)
    self.regioncount = 0



  def addRegions(self, pressed):
    for solvent in sorted(solvents):
      if pressed == ('%s' %solvent):
        self.solventType = Label(self.scrollAreaWidgetContents, text=solvent, grid=(self.regioncount,0))
        self.closebutton = Button(self.scrollAreaWidgetContents,'Remove from selection', grid=(self.regioncount,1))
        values = (solvents[solvent])*2
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
          self.spin.setPrefix('ppm ')
          self.spin.setValue(values)

    self.closebutton.clicked.connect(partial(self.deleteRegions, self.positions))

  def deleteRegions(self, positions):
    for position in positions:
      widget1 = self.scrollAreaWidgetContents.layout().itemAtPosition(*position).widget()
      if widget1 is self.solventType:
        widget1.hide()
      else:
        widget1.deleteLater()
