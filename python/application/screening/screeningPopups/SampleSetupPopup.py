__author__ = 'luca'

from PyQt4 import QtCore, QtGui
import sys
from functools import partial

from application.screening.screeningLib.MixtureGeneration import setupSamples, allCombinations
from application.screening.screeningModules.MixtureAnalysis import MixtureAnalysis
from application.screening.screeningModules.ScreeningPipeline import ExcludeRegions

from ccpncore.gui.Base import Base
from ccpncore.gui.DoubleSpinbox import DoubleSpinbox
from ccpncore.gui.Button import Button
from ccpncore.gui.Label import Label
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.Slider import Slider
from ccpncore.gui.Spinbox import Spinbox
from ccpncore.gui.ScrollArea import ScrollArea
from ccpncore.gui.RadioButtons import RadioButtons
from ccpncore.gui.ButtonList import ButtonList


class SamplePopup(QtGui.QDialog):

  def __init__(self, parent=None, project=None,  **kw):
    super(SamplePopup, self).__init__(parent)

    self.project = project
    self.mainWindow = self.project._appBase.mainWindow
    self.dockArea = self.mainWindow.dockArea
    self.generalPreferences = self.project._appBase.preferences.general
    self.colourScheme = self.generalPreferences.colourScheme

    ######## ========  Set Main Layout ====== ########
    self.mainLayout = QtGui.QGridLayout()
    self.setLayout(self.mainLayout)
    self.setWindowTitle("Mixture Generation Setup")
    self.resize(200, 500)

    ######## ========  Set Tabs  ====== ########
    self.tabWidget = QtGui.QTabWidget()
    self.tabGeneralSetup = QtGui.QFrame()
    self.tabGeneralSetupLayout = QtGui.QGridLayout()
    self.tabGeneralSetup.setLayout(self.tabGeneralSetupLayout)
    self.excludedRegionsTab = ExcludeRegions()
    self.tabWidget.addTab(self.tabGeneralSetup, 'General Setup')
    self.tabWidget.addTab(self.excludedRegionsTab, 'Exclude Regions')

    ######## ========  Set extra widgets  ====== ########
    self.selectSpectraLabel = Label(self, text="Select Spectra to mix")
    self.selectSpectraPullDown =  PulldownList(self)
    self.noiseLabel = Label(self, text="Noise level threshold")
    self.pickPeaksLabel = Label(self, text="Peak Picking")
    self.replaceMixtureLabel = Label(self, text="Replace Mixtures")
    self.noiseLevelSpinbox = DoubleSpinbox(self)
    self.noiseLevelSpinbox.hide()
    self.spacer = QtGui.QSpacerItem(0,20)
    self.pickPeaksRadioButtons = RadioButtons(self,
                                               texts=['Automatic','Already picked'],
                                               selectedInd=0,
                                               callback=self.pickPeakCallBack,
                                               tipTexts=None)
    self.noiseLevelRadioButtons = RadioButtons(self,
                                               texts=['Estimated','Manual'],
                                               selectedInd=0,
                                               callback=self.noiseLevelCallBack,
                                               tipTexts=None)

    self.replaceRadioButtons = RadioButtons(self,
                                               texts=['Yes','No'],
                                               selectedInd=0,
                                               callback=None,
                                               tipTexts=None)

    ######## ========  Set ApplyButtons  ====== ########
    self.calculateButtons = ButtonList(self,
                                       texts = ['Cancel','Perform'],
                                       callbacks=[self.reject, self.perform],
                                       tipTexts=[None,None],
                                       direction='h', hAlign='r')

    ######## ======== Add widgets to Layout ====== ########
    self.mainLayout.addWidget(self.tabWidget, 0,0,1,2)
    self.mainLayout.addWidget(self.selectSpectraLabel, 1,0)
    self.mainLayout.addWidget(self.selectSpectraPullDown, 1,1)
    self.mainLayout.addWidget(self.pickPeaksLabel, 2,0)
    self.mainLayout.addWidget(self.pickPeaksRadioButtons, 2,1)
    self.mainLayout.addWidget(self.noiseLabel, 3,0)
    self.mainLayout.addWidget(self.noiseLevelRadioButtons, 3,1)
    self.mainLayout.addWidget(self.noiseLevelSpinbox, 4,1)
    self.mainLayout.addWidget(self.replaceMixtureLabel, 5,0)
    self.mainLayout.addWidget(self.replaceRadioButtons, 5,1)
    self.mainLayout.addItem(self.spacer, 6,0)
    self.mainLayout.addWidget(self.calculateButtons, 7,1)

    self.populatePullDownSelection()
    self.createWidgetsGeneralTab()
    self.setPerformButtonStatus()


  def createWidgetsGeneralTab(self):
    '''   '''
    self.modeRadioButtons = RadioButtons(self,texts=['Select number of Mixtures',
                                                    'Select number of Components',
                                                    'Best match'],
                                             selectedInd=2,
                                             callback=self.modeSelection,
                                             direction='v',
                                             tipTexts=None)
    self.spacerLabel = Label(self, text="")
    self.spinBoxSA = Spinbox(self)
    self.sliderSA = Slider(self,startVal= 2,endVal=100,direction='h',step=1,)

    self.spinBoxcomponent = Spinbox(self)
    self.sliderComponent  = Slider(self, startVal = 2, endVal = 20,direction='h', step=1, )

    self.ppmDistance = DoubleSpinbox(self)
    self.distanceLabel = Label(self, text="Minimal distance between peaks")

    self.addWidgetsToGeneralTab()
    self.setWidgetsGeneralTab()


  def addWidgetsToGeneralTab(self):
    '''   '''
    widgetsToAdd = (self.modeRadioButtons, self.spacerLabel, self.spinBoxSA,self.sliderSA,
                    self.spinBoxcomponent, self.sliderComponent, self.ppmDistance, self.distanceLabel)
    count = int(len(widgetsToAdd)/2)
    self.positions = [[i+1, j] for i in range(count) for j in range(2)]
    for position, widget in zip(self.positions, widgetsToAdd):
      i,j = position
      self.tabGeneralSetupLayout.addWidget(widget, i,j)

  def setWidgetsGeneralTab(self):
    '''   '''
    self.spinBoxSA.setRange(2, 100)
    self.spinBoxcomponent.setRange(2, 20)
    self.ppmDistance.setRange(0.01, 0.20)

    self.spinBoxSA.setMaximumWidth(90)
    self.spinBoxcomponent.setMaximumWidth(90)
    self.ppmDistance.setMaximumWidth(90)

    self.ppmDistance.setValue(0.05)
    self.ppmDistance.setSingleStep(0.01)
    self.ppmDistance.setSuffix(" ppm")
    self.noiseLevelSpinbox.setValue(10000)
    self.noiseLevelSpinbox.setMaximum(10000000)

    self.sliderSA.valueChanged.connect(self.spinBoxSA.setValue)
    self.spinBoxSA.valueChanged.connect(self.sliderSA.setValue)
    self.sliderComponent.valueChanged.connect(self.spinBoxcomponent.setValue)
    self.spinBoxcomponent.valueChanged.connect(self.sliderComponent.setValue)

    self.widgetsToHide =  [self.spinBoxSA, self.sliderSA, self.spinBoxcomponent,
                           self.sliderComponent]
    self.hideWidgets(self.widgetsToHide)

    self.buttonsToStyle = [self.spacerLabel,self.noiseLevelRadioButtons,self.pickPeaksRadioButtons,
                           self.modeRadioButtons, self.distanceLabel]
    for button in self.buttonsToStyle:
      if self.colourScheme == 'dark':
        button.setStyleSheet("background-color:transparent; color: #EFFBFB")
      else:
        button.setStyleSheet("background-color:transparent; color: #122043")

  def modeSelection(self):
    '''   '''
    selected = self.modeRadioButtons.get()
    callbacks = (self.show_nSamples,self.show_nComponents,self.showBestMatch)
    for selection, callback in zip(self.modeRadioButtons.texts, callbacks):
      if selected == str(selection):
        callback()


  def pickPeakCallBack(self,):
    '''   '''
    selected = self.pickPeaksRadioButtons.get()
    if selected == 'Automatic':
      self.showWidgets([self.noiseLevelRadioButtons,self.noiseLabel])
      self.noiseLevelRadioButtons.radioButtons[0].setChecked(True)
    else:
      self.noiseLevelRadioButtons.radioButtons[1].setChecked(True)
      self.hideWidgets([self.noiseLevelRadioButtons,self.noiseLabel,self.noiseLevelSpinbox])

  def noiseLevelCallBack(self):
    '''   '''
    selected = self.noiseLevelRadioButtons.get()
    if selected == 'Estimated':
      self.hideWidgets([self.noiseLevelSpinbox])
    else:
      self.showWidgets([self.noiseLevelSpinbox])


  def show_nSamples(self):
    '''   '''
    widgetsToHide = [self.sliderComponent,self.spinBoxcomponent,self.ppmDistance,self.distanceLabel]
    widgetsToShow = [self.sliderSA,self.spinBoxSA]
    self.showWidgets(widgetsToShow)
    self.hideWidgets(widgetsToHide)


  def show_nComponents(self):
    '''   '''
    widgetsToHide = [self.sliderSA,self.spinBoxSA,self.ppmDistance,self.distanceLabel]
    widgetsToShow = [self.sliderComponent,self.spinBoxcomponent]
    self.showWidgets(widgetsToShow)
    self.hideWidgets(widgetsToHide)


  def showBestMatch(self):
    '''   '''
    widgetsToHide = [self.sliderComponent,self.spinBoxcomponent,self.sliderSA,self.spinBoxSA]
    widgetsToShow = [self.ppmDistance,self.distanceLabel]
    self.showWidgets(widgetsToShow)
    self.hideWidgets(widgetsToHide)


  def hideWidgets(self, widgets:[]):
    for widget in widgets:
      widget.hide()


  def showWidgets(self, widgets:[]):
    for widget in widgets:
      widget.show()


  def populatePullDownSelection(self):
    '''   '''
    self.dataPullDown = ['Select An Option']
    if len(self.project.spectrumGroups)>0:
      self.dataPullDown.append('All')
      for spectrumGroup in self.project.spectrumGroups:
         self.dataPullDown.append(spectrumGroup.pid)
    self.selectSpectraPullDown.setData(self.dataPullDown)
    if 'SG:H' in self.dataPullDown:
      self.selectSpectraPullDown.select('SG:H')

    self.selectSpectraPullDown.activated[str].connect(self.setPerformButtonStatus)

  def getPullDownSelectionSpectra(self):
    '''   '''
    selected = self.selectSpectraPullDown.getText()
    if selected == 'All':
      spectra = self.project.spectra
      return spectra
    if selected == 'Select An Option':
      return []
    else:
     spectra = self.project.getByPid(selected).spectra
     return spectra

  def deleteMixtures(self):
    mixtures = MixtureAnalysis.getMixture(self)
    if len(mixtures)>0:
      for mixture in mixtures:
        mixture.delete()
    if 'MIXTURE ANALYSIS' in self.dockArea.findAll()[1]:
      self.dockArea.docks['MIXTURE ANALYSIS'].close()


  def perform(self):
    '''This function gets all the setting given by the user and runs the mixture generation algorithm ('setupSamples')'''
    mode, n, minOverlap, mixtureName = self.getSelectedSettings()
    spectra = self.getPullDownSelectionSpectra()

    if self.replaceRadioButtons.get() == 'Yes':
      self.deleteMixtures()

    if self.pickPeaksRadioButtons.get() == 'Already picked':
      setupSamples(spectra, mode, n, minOverlap, mixtureName)
    else:
      self.pickPeaks()
      setupSamples(spectra, mode, n, minOverlap, mixtureName)

    self.openTheMixtureAnalysisModule()
    self.accept()

  def pickPeaks(self):
    '''   '''
    spectra = self.getPullDownSelectionSpectra()
    regions = self.excludedRegionsTab.getExcludedRegions()

    if self.pickPeaksRadioButtons.radioButtons[0].isChecked:
      selected = self.noiseLevelRadioButtons.get()
      values = (0, self.noiseLevelSpinbox.value())
      for selection, value in zip(self.noiseLevelRadioButtons.texts, values):
        if selected == str(selection):
          for spectrum in spectra:
            spectrum.peakLists[0].pickPeaks1dFiltered(size=10, ignoredRegions=regions, noiseThreshold=value)


  def setPerformButtonStatus(self):
    '''   '''
    selected = self.selectSpectraPullDown.getText()
    if selected == 'Select An Option':
      self.calculateButtons.buttons[1].setEnabled(False)

    else:
      self.calculateButtons.buttons[1].setEnabled(True)

  def getSelectedSettings(self):
    '''   '''
    settings = {self.modeRadioButtons.radioButtons[0]:['nSamples',self.spinBoxSA.value(),None,None],
                self.modeRadioButtons.radioButtons[1]:['nComponentsPerSample',self.spinBoxcomponent.value(),None,None],
                self.modeRadioButtons.radioButtons[2]:['bestMatch',None, self.ppmDistance.value(),None]}
    for item, value in settings.items():
      if item.isChecked():
        return value


  def openTheMixtureAnalysisModule(self):
    '''   '''
    mixtureAnalysis = MixtureAnalysis(self.project)
    mixtureAnalysisDock = self.dockArea.addDock(mixtureAnalysis, position='bottom')

    spectrumDisplay = self.mainWindow.createSpectrumDisplay(self.project.spectra[0])
    spectrumDisplay.setWhatsThis('MixtureDisplay')

    self.dockArea.moveDock(spectrumDisplay.dock, position='top', neighbor=mixtureAnalysisDock)
    self.dockArea.guiWindow.deleteBlankDisplay()
    self.project.strips[0].viewBox.autoRange()

    currentDisplayed = self.project.strips[0]
    for spectrumView in currentDisplayed.spectrumViews:
      if spectrumView is not None:
        spectrumView.delete()
