__author__ = 'luca'

from PyQt4 import QtGui
from ccpn.Screen.modules.MixtureAnalysis import MixtureAnalysis
from ccpn.Screen.modules.ScreeningPipeline import ExcludeRegions

from ccpn.Screen.lib.MixtureGeneration import setupSamples
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.Slider import Slider
from ccpn.ui.gui.widgets.Spinbox import Spinbox


class MixtureGenerationPopup(QtGui.QDialog):

  def __init__(self, parent=None, project=None,  **kw):
    super(MixtureGenerationPopup, self).__init__(parent)

    self.project = project
    # if self.parent is not None:
    #   self.mainWindow = self._appBase.ui.mainWindow
    # else:
    #   self.mainWindow = self._appBase._mainWindow
    # parent=Framework
    # self.mainWindow = mainWindow
    # self.moduleArea = moduleArea
    self.mainWindow = parent
    self.moduleArea = self.mainWindow.moduleArea
    self.framework = self.mainWindow.framework
    self.generalPreferences = self.framework.preferences.general
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
                                              callback=self._pickPeakCallBack,
                                              tipTexts=None)
    self.noiseLevelRadioButtons = RadioButtons(self,
                                               texts=['Estimated','Manual'],
                                               selectedInd=0,
                                               callback=self._noiseLevelCallBack,
                                               tipTexts=None)

    self.replaceRadioButtons = RadioButtons(self,
                                               texts=['Yes','No'],
                                               selectedInd=0,
                                               callback=None,
                                               tipTexts=None)

    ######## ========  Set ApplyButtons  ====== ########
    self.calculateButtons = ButtonList(self,
                                       texts = ['Cancel','Perform'],
                                       callbacks=[self.reject, self.genereteMixture],
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

    self._populatePullDownSelection()
    self._createWidgetsGeneralTab()
    self._setPerformButtonStatus()


  def _createWidgetsGeneralTab(self):
    '''   '''
    self.modeRadioButtons = RadioButtons(self, texts=['Select number of Mixtures',
                                                    'Select number of Components',
                                                    'Best match'],
                                         selectedInd=2,
                                         callback=self._modeSelection,
                                         direction='v',
                                         tipTexts=None)
    self.spacerLabel = Label(self, text="")
    self.spinBoxSA = Spinbox(self)
    self.sliderSA = Slider(self,startVal= 2,endVal=100,direction='h',step=1,)

    self.spinBoxcomponent = Spinbox(self)
    self.sliderComponent  = Slider(self, startVal = 2, endVal = 20,direction='h', step=1, )

    self.ppmDistance = DoubleSpinbox(self)
    self.distanceLabel = Label(self, text="Minimal distance between peaks")

    self._addWidgetsToGeneralTab()
    self._setWidgetsGeneralTab()


  def _addWidgetsToGeneralTab(self):
    '''   '''
    widgetsToAdd = (self.modeRadioButtons, self.spacerLabel, self.spinBoxSA,self.sliderSA,
                    self.spinBoxcomponent, self.sliderComponent, self.ppmDistance, self.distanceLabel)
    count = int(len(widgetsToAdd)/2)
    self.positions = [[i+1, j] for i in range(count) for j in range(2)]
    for position, widget in zip(self.positions, widgetsToAdd):
      i,j = position
      self.tabGeneralSetupLayout.addWidget(widget, i,j)

  def _setWidgetsGeneralTab(self):
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
    self._hideWidgets(self.widgetsToHide)

    self.buttonsToStyle = [self.spacerLabel,self.noiseLevelRadioButtons,self.pickPeaksRadioButtons,
                           self.modeRadioButtons, self.distanceLabel]
    for button in self.buttonsToStyle:
      if self.colourScheme == 'dark':
        button.setStyleSheet("background-color:transparent; color: #EFFBFB")
      else:
        button.setStyleSheet("background-color:transparent; color: #122043")

  def _modeSelection(self):
    '''   '''
    selected = self.modeRadioButtons.get()
    callbacks = (self._show_nSamples, self._showNComponents, self._showBestMatch)
    for selection, callback in zip(self.modeRadioButtons.texts, callbacks):
      if selected == str(selection):
        callback()


  def _pickPeakCallBack(self, ):
    '''   '''
    selected = self.pickPeaksRadioButtons.get()
    if selected == 'Automatic':
      self._showWidgets([self.noiseLevelRadioButtons, self.noiseLabel])
      self.noiseLevelRadioButtons.radioButtons[0].setChecked(True)
    else:
      self.noiseLevelRadioButtons.radioButtons[1].setChecked(True)
      self._hideWidgets([self.noiseLevelRadioButtons, self.noiseLabel, self.noiseLevelSpinbox])

  def _noiseLevelCallBack(self):
    '''   '''
    selected = self.noiseLevelRadioButtons.get()
    if selected == 'Estimated':
      self._hideWidgets([self.noiseLevelSpinbox])
    else:
      self._showWidgets([self.noiseLevelSpinbox])


  def _show_nSamples(self):
    '''   '''
    widgetsToHide = [self.sliderComponent,self.spinBoxcomponent,self.ppmDistance,self.distanceLabel]
    widgetsToShow = [self.sliderSA,self.spinBoxSA]
    self._showWidgets(widgetsToShow)
    self._hideWidgets(widgetsToHide)


  def _showNComponents(self):
    '''   '''
    widgetsToHide = [self.sliderSA,self.spinBoxSA,self.ppmDistance,self.distanceLabel]
    widgetsToShow = [self.sliderComponent,self.spinBoxcomponent]
    self._showWidgets(widgetsToShow)
    self._hideWidgets(widgetsToHide)


  def _showBestMatch(self):
    '''   '''
    widgetsToHide = [self.sliderComponent,self.spinBoxcomponent,self.sliderSA,self.spinBoxSA]
    widgetsToShow = [self.ppmDistance,self.distanceLabel]
    self._showWidgets(widgetsToShow)
    self._hideWidgets(widgetsToHide)


  def _hideWidgets(self, widgets:[]):
    for widget in widgets:
      widget.hide()


  def _showWidgets(self, widgets:[]):
    for widget in widgets:
      widget.show()


  def _populatePullDownSelection(self):
    '''   '''
    self.dataPullDown = ['Select An Option']
    if len(self.project.spectrumGroups)>0:
      self.dataPullDown.append('All')
      for spectrumGroup in self.project.spectrumGroups:
         self.dataPullDown.append(spectrumGroup.pid)
    self.selectSpectraPullDown.setData(self.dataPullDown)
    if 'SG:H' in self.dataPullDown:
      self.selectSpectraPullDown.select('SG:H')

    self.selectSpectraPullDown.activated[str].connect(self._setPerformButtonStatus)

  def _getPullDownSelectionSpectra(self):
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

  def _deleteMixtures(self):
    mixtures = MixtureAnalysis._getMixture(self)
    if len(mixtures)>0:
      for mixture in mixtures:
        mixture.delete()
    if 'MIXTURE ANALYSIS' in self.moduleArea.findAll()[1]:
      self.moduleArea.modules['MIXTURE ANALYSIS'].close()


  def genereteMixture(self):
    '''This function gets all the setting given by the user and runs the mixture generation algorithm ('setupSamples')'''
    mode, n, minOverlap, mixtureName = self._getSelectedSettings()
    spectra = self._getPullDownSelectionSpectra()

    if self.replaceRadioButtons.get() == 'Yes':
      self._deleteMixtures()

    if self.pickPeaksRadioButtons.get() == 'Already picked':
      setupSamples(spectra, mode, n, minOverlap, mixtureName)
    else:
      self._pickPeaks()
      setupSamples(spectra, mode, n, minOverlap, mixtureName)

    self._openMixtureAnalysisModule()
    self.accept()

  def _pickPeaks(self):
    '''   '''
    spectra = self._getPullDownSelectionSpectra()
    regions = self.excludedRegionsTab._getExcludedRegions()

    if self.pickPeaksRadioButtons.radioButtons[0].isChecked:
      selected = self.noiseLevelRadioButtons.get()
      values = (0, self.noiseLevelSpinbox.value())
      for selection, value in zip(self.noiseLevelRadioButtons.texts, values):
        if selected == str(selection):
          for spectrum in spectra:
            spectrum.peakLists[0].pickPeaks1dFiltered(size=10, ignoredRegions=regions, noiseThreshold=value)


  def _setPerformButtonStatus(self):
    '''   '''
    selected = self.selectSpectraPullDown.getText()
    if selected == 'Select An Option':
      self.calculateButtons.buttons[1].setEnabled(False)

    else:
      self.calculateButtons.buttons[1].setEnabled(True)

  def _getSelectedSettings(self):
    '''   '''
    settings = {self.modeRadioButtons.radioButtons[0]:['nSamples',self.spinBoxSA.value(),None,None],
                self.modeRadioButtons.radioButtons[1]:['nComponentsPerSample',self.spinBoxcomponent.value(),None,None],
                self.modeRadioButtons.radioButtons[2]:['bestMatch',None, self.ppmDistance.value(),None]}
    for item, value in settings.items():
      if item.isChecked():
        return value


  def _openMixtureAnalysisModule(self):
    '''   '''
    mixtureAnalysis = MixtureAnalysis(parent=self.mainWindow, project=self.project)
    mixtureAnalysisModule = self.moduleArea.addModule(mixtureAnalysis, position='bottom')

    spectrumDisplay = self.mainWindow.createSpectrumDisplay(self.project.spectra[0])
    spectrumDisplay.setWhatsThis('MixtureDisplay')

    self.moduleArea.moveModule(spectrumDisplay.module, position='top', neighbor=mixtureAnalysisModule)
    self.moduleArea.guiWindow.deleteBlankDisplay()
    self.project.strips[0].viewBox.autoRange()

    currentDisplayed = self.project.strips[0]
    for spectrumView in currentDisplayed.spectrumViews:
      if spectrumView is not None:
        spectrumView.delete()
