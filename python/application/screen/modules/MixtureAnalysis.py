__author__ = 'luca'

from PyQt4 import QtCore, QtGui
from application.core.widgets.ButtonList import ButtonList
from application.core.widgets.Icon import Icon
from application.core.widgets.Table import ObjectTable, Column
from application.core.widgets.Button import Button
from application.core.widgets.Dock import CcpnDock
from application.core.widgets.PulldownList import PulldownList
from application.core.widgets.ListWidget import ListWidget
from application.core.widgets.Label import Label

from application.core.widgets.LineEdit import LineEdit
from functools import partial
from application.core.widgets.CompoundView import CompoundView, Variant, importSmiles
from application.core.lib.Window import navigateToNmrResidue, navigateToPeakPosition
from application.screen.lib.MixtureGeneration import setupSamples, scoring
from numpy import array, amin, amax, average, empty, nan, nanmin, fabs, subtract, where, argmax, NAN
import math

from application.screen.modules.MixtureOptimisation import MixtureOptimisation

green = QtGui.QColor('Green')
red = QtGui.QColor('Red')
yellow = QtGui.QColor('yellow')

class MixtureAnalysis(CcpnDock):

  '''Creates a module to analyse the mixtures'''

  def __init__(self, project):
    super(MixtureAnalysis, self)
    CcpnDock.__init__(self, name='Mixture Analysis')

    self.project = project
    self.mainWindow = self.project._appBase.mainWindow
    self.dockArea = self.mainWindow.dockArea
    self.generalPreferences = self.project._appBase.preferences.general
    self.colourScheme = self.generalPreferences.colourScheme
    self.listOfSample = []

    ######## ======== Icons ====== ########
    self.settingIcon = Icon('iconsNew/applications-system')
    self.exportIcon = Icon('iconsNew/export')

    ######## ======== Set Main Layout ====== ########
    self.mainFrame = QtGui.QFrame()
    self.mainLayout = QtGui.QVBoxLayout()
    self.mainFrame.setLayout(self.mainLayout)
    self.layout.addWidget(self.mainFrame, 0,0)

    ######## ======== Set Secondary Layout ====== ########
    self.settingFrameLayout = QtGui.QHBoxLayout()
    self.analysisFrameLayout = QtGui.QHBoxLayout()
    self.mainLayout.addLayout(self.settingFrameLayout)
    self.mainLayout.addLayout(self.analysisFrameLayout)

    ######## ======== Create widgets ====== ########
    self.createSettingGroup()
    self.scoringTable()

    ######## ======== Set Tabs  ====== ########
    self.tabWidget = QtGui.QTabWidget()
    self.analysisFrameLayout.addWidget(self.tabWidget)

    ######## ======== Create 1thTab with peak Table and Molecule view  ====== ########
    self.tabPeaksMolecule = QtGui.QFrame()
    self.tabPeaksMoleculeLayout = QtGui.QGridLayout()
    self.tabPeaksMolecule.setLayout(self.tabPeaksMoleculeLayout)
    self.tabWidget.addTab(self.tabPeaksMolecule, 'Components peaks')
    self.toolBarComponents = QtGui.QToolBar()
    self.tabPeaksMoleculeLayout.addWidget(self.toolBarComponents, 0,0,1,0)

    ######## ========  Create 2ndTab with multiple Molecule view ====== ########
    self.tabMoleculeView = QtGui.QFrame()
    self.tabMoleculeViewLayout = QtGui.QHBoxLayout()
    self.tabMoleculeView.setLayout(self.tabMoleculeViewLayout)
    self.tabWidget.addTab(self.tabMoleculeView, 'Components structure')
    self.tableComponentPeaks()

    ######## ========  Create 3thTab with Components Info ====== ########
    self.tabMoleculeInfo = QtGui.QFrame()
    self.tabMoleculeInfoLayout = QtGui.QVBoxLayout()
    self.tabMoleculeInfo.setLayout(self.tabMoleculeInfoLayout)
    self.tabWidget.addTab(self.tabMoleculeInfo, 'Components Info')
    self.widgetsTabComponentsInfo()

    ######## ========  Create 4thTab Mixtures Management ====== ########
    self.tabMixturesManagement = QtGui.QFrame()
    self.tabMixturesManagementLayout = QtGui.QGridLayout()
    self.tabMixturesManagement.setLayout(self.tabMixturesManagementLayout)
    self.tabWidget.addTab(self.tabMixturesManagement, 'Mixtures Management')
    self.mixtureManagementWidgets()

    ######## ========  registerNotify ====== ########
    self.current = project._appBase.current
    self.current.registerNotify(self.findSelectedPeaks, 'peaks')
    self.findSelectedPeaks(peaks=None)



  def getMixture(self):
    ''' Returns spectra mixtures (virtual samples) across all project sample '''
    self.mixtureList= []
    if len(self.project.samples)>0:
      for sample in self.project.samples:
        if hasattr(sample, 'minScore'):
          if len(sample.sampleComponents) and len(sample.spectra) >0:
            self.mixtureList.append(sample)
          else:
            sample.delete()

    return self.mixtureList


  '''######## ======== Scoring and Selection Table ====== ########'''

  def scoringTable(self):
    ''' Fills the first table on the module with the virtual sample information '''

    columns = [Column('Mixture Name', lambda sample:str(sample.pid)),
               Column('N Components', lambda sample: (int(len(sample.spectra)))),
               Column('Min Score', lambda sample: int(sample.minScore)),
               Column('Average Score', lambda sample: int(sample.averageScore))]

    self.scoringTable = ObjectTable(self, columns,  objects=[], selectionCallback=self.tableSelection)
    self.scoringTable.setFixedWidth(400)
    if len(self.getMixture())>0:
      self.scoringTable.setObjects(self.getMixture())
    self.analysisFrameLayout.addWidget(self.scoringTable)

  def tableSelection(self, row:int=None, col:int=None, obj:object=None):
    ''' For each row of the scoring table all the module information are refreshed '''
    objRow = self.scoringTable.getCurrentObject()
    self.createButtons(objRow)
    self.displayMixture(objRow)
    self.displayMolecules(objRow)
    self.displayMixturesInfo(objRow)
    self.populatePullDownSelection()
    self.populateLeftListWidget()
    self.rightListWidget.clear()
    self.selectAnOptionState()


  ''' ######## ======== First Tab properties ====== ########   '''

  def tableComponentPeaks(self,):
    ''' This creates the peak table in the first tab'''
    self.peakListObjects = []

    columns = [Column('#', 'serial'),
               Column('Position', lambda peak: '%.3f' % peak.position[0] ),
               Column('Height', lambda peak: self._getPeakHeight(peak))]

    self.peakTable = ObjectTable(self, columns, objects=[],selectionCallback=self.selectPeak, multiSelect=True)
    self.tabPeaksMoleculeLayout.addWidget(self.peakTable, 1,0)


  def selectPeak(self, row:int=None, col:int=None, obj:object=None):
    ''' this callback  '''
    self.selectedTablePeaks = self.peakTable.getSelectedObjects()
    for peak in self.selectedTablePeaks:
      if peak.isSelected:
        print(self.project._appBase.current.peaks, 'currents')
        # self.project._appBase.current.clearPeaks()
      else:
        peak.isSelected = True
        self.project._appBase.current.peak = peak

  def findSelectedPeaks(self,  peaks:None):
    ''' this callback, registered with a notifier, allows to select a peak either on the table, compoundView or
    guiSpectrum display and highLight the respective peak/s or atom/s on compoundView, table , display '''
    # self.peakTable.clearSelection()
    selectedPeaks = []
    if len(self.project.strips)>0:
      currentDisplayed = self.project.strips[0]
      if len(self.project._appBase.current.peaks):
        self.currentPeaks = self.project._appBase.current.peaks
        if len(self.peakTable.objects)>0:
          for peak in self.currentPeaks:
            if peak in self.peakTable.objects:
              self.peakTable.setCurrentObject(peak)
              selectedPeaks.append(peak)

    if len(selectedPeaks)>0:
      print(selectedPeaks, 'selected peaks')
      self.peakTable.setCurrentObjects(selectedPeaks)

      for atom, atomObject in self.compoundView.atomViews.items():
        if atom.name == 'H1':
          atomObject.select()

  def _getPeakHeight(self, peak):
    if peak.height:
      return peak.height*peak.peakList.spectrum.scale

  def createButtons(self, sample):
    ''' This creates buttons according with how many spectra are inside the mixture. '''
    self.toolBarComponents.clear()
    for spectrum in sample.spectra:
      self.componentButton = Button(self, text=spectrum.id)#,toggle=True)
      self.componentButton.clicked.connect(partial(self.toggleComponentButton, spectrum, sample, self.componentButton))
      # self.componentButton.setChecked(False)
      self.componentButton.setFixedHeight(40)
      self.toolBarComponents.addWidget(self.componentButton)

  def toggleComponentButton(self, spectrum, sample, componentButton):
    '''  Toggling the component button will populate the peak table and display the molecule on compoundViewer '''
    self.project._appBase.mainWindow.clearMarks()
    pressedButton = self.sender()

    buttons = []
    for item in pressedButton.parent().children():
      if hasattr(item, 'callback'):
        if item != componentButton:
          buttons.append(item)

    for item in buttons:
      if self.colourScheme == 'dark':
        item.setStyleSheet("background-color: #2a3358")
        pressedButton.setStyleSheet("background-color: #020F31")
      else:
        item.setStyleSheet("background-color: #fbf4cc; border: 1px solid  #bd8413; color: #122043")
        pressedButton.setStyleSheet("background-color: #bd8413")

    for peakList in spectrum.peakLists:
      self.peakListObjects.append(peakList.peaks)
      self.peakTable.setObjects(self.peakListObjects[-1])

    for sampleComponent in sample.sampleComponents:
      if sampleComponent.substance.referenceSpectra[0] == spectrum:
        smiles = sampleComponent.substance.smiles
        self.compoundView  = CompoundView(self, smiles=smiles, preferences=self.generalPreferences)
        self.tabPeaksMoleculeLayout.addWidget(self.compoundView, 1,1)

        self.compoundView.resetView()


  ''' ######## ======== Second Tab properties (Multiple Compound View ====== ########   '''
  
  def displayMolecules(self, sample):
    '''  displays the molecules on compoundViewers '''
    self.clearTabMoleculeView(sample)

    for component in sample.sampleComponents:
      chemicalName = (''.join(str(x) for x in component.substance.synonyms))
      smiles = component.substance.smiles
      self.compoundViewTab2 = CompoundView(self, smiles=smiles, preferences=self.generalPreferences)
      self.compoundViewTab2.setMaximumWidth(180)
      self.tabMoleculeViewLayout.addWidget(self.compoundViewTab2)

      self.compoundViewTab2.resetView()


  def clearTabMoleculeView(self, sample):
    ''' Delete all the buttons if a different mixture is selected on the scoring table '''
    layout = self.tabMoleculeViewLayout
    items = [layout.itemAt(i) for i in range(layout.count())]
    if len(items)>0:
      for item in items:
        item.widget().deleteLater()

  ''' ######## ======== 3Th Tab properties ====== ########   '''

  def widgetsTabComponentsInfo(self):
    ''' creates a table with the relevant information about the substances/component in the mixture '''
    columns = [Column('Name', lambda substance:str(substance.pid)),
               Column('logP', lambda substance:str(substance.logPartitionCoefficient)),
               Column('psa', lambda substance:str(substance.polarSurfaceArea)),
               Column('H acceptors', lambda substance:str(substance.hBondAcceptorCount)),
               Column('H donors', lambda substance:str(substance.hBondDonorCount)),
               Column('MW', lambda substance:str(substance.molecularMass))]

    self.sampleInfoTable = ObjectTable(self, columns, objects=[])
    self.tabMoleculeInfoLayout.addWidget(self.sampleInfoTable)


  def displayMixturesInfo(self, sample):
    ''' fill the  sampleInfoTable  '''
    self.sampleComponents =  sample.sampleComponents
    substances = [sc.substance for sc in self.sampleComponents]
    self.sampleInfoTable.setObjects(substances)


  ''' ###### ==== Fourth Tab properties (mixtureManagement) === ####
    This tab is made by two widget lists. Each widget list has the spectra present in the respective mixture.
    Left mixture is the selected on the scoring table. A pullDown lets select to create a new empty mixture or pick an other
    from the project.
    Moving spectra across by drag and drop allows the users to recreate manually the mixtures.'''

  def mixtureManagementWidgets(self):
    ''' creates all the widgets present in the mixture Management tab '''
    currentMixture = self.scoringTable.getCurrentObject()
    self.leftListWidget = ListWidget(self, rightMouseCallback=self.rightClickListWidget)
    self.rightListWidget = ListWidget(self,rightMouseCallback=None)
    self.calculateButtons = ButtonList(self, texts = ['Reset','ReFresh'],
                                   callbacks=[self.resetMixtureScore,self.predictScores],
                                   tipTexts=[None,None], direction='h', hAlign='r')

    self.applyButtons = ButtonList(self, texts = ['Cancel','Apply'],
                                   callbacks=[self.resetInitialState,self.createNewMixture],
                                   tipTexts=[None,None], direction='h', hAlign='r')
    self.warningLabel = Label(self,'Cancel or Apply to continue')

    self.pullDownSelection = PulldownList(self,)
    self.leftMixtureLineEdit = LineEdit(self,'')
    self.rightMixtureLineEdit = LineEdit(self,'')

    self.tabMixturesManagementLayout.addWidget(self.pullDownSelection, 0,1)
    self.tabMixturesManagementLayout.addWidget(self.leftMixtureLineEdit, 1,0)
    self.tabMixturesManagementLayout.addWidget(self.rightMixtureLineEdit, 1,1)
    self.tabMixturesManagementLayout.addWidget(self.leftListWidget, 2,0)
    self.tabMixturesManagementLayout.addWidget(self.rightListWidget, 2,1)
    self.tabMixturesManagementLayout.addWidget(self.calculateButtons, 3,1)
    self.tabMixturesManagementLayout.addWidget(self.warningLabel, 3,0)
    self.tabMixturesManagementLayout.addWidget(self.applyButtons, 3,1)

    self.leftMixtureLineEdit.editingFinished.connect(self.changeLeftMixtureName)
    self.rightMixtureLineEdit.editingFinished.connect(self.changeRightMixtureName)

    self.disableRecalculateButtons()
    self.applyButtons.hide()
    self.warningLabel.hide()
    self.leftListWidget.contextMenuItem = 'Not Implemented Yet'

  def rightClickListWidget(self):
      print('Not Implemented Yet')



  def populateLeftListWidget(self):
    ''' fills the left widget with spectra scores from the selected mixture on the scoring table '''
    sample = self.scoringTable.getCurrentObject()
    self.leftListWidget.clear()
    if sample is not None:
      self.leftMixtureLineEdit.setText(str(sample.name))
      color = QtGui.QColor('Red')
      header = QtGui.QListWidgetItem(str(sample.id))
      header.setFlags(QtCore.Qt.NoItemFlags)
      header.setTextColor(color)
      self.leftListWidget.addItem(header)
      for sampleComponent in sample.sampleComponents:
        spectrum = sampleComponent.substance.referenceSpectra[0]
        item = QtGui.QListWidgetItem(str(spectrum.id)+ ' Single Score ' + str(sampleComponent.score[0]))
        self.leftListWidget.addItem(item)

        # if len(sampleComponent.score[2]) > 0:
        #   item = QtGui.QListWidgetItem(str(spectrum.id) + ' Single Score ' + str(sampleComponent.score[0]))
        #                                # + ' Overlapped at Ppm ' + str(sampleComponent.score[2]))
        #   self.leftListWidget.addItem(item)
        # else:
        #   item = QtGui.QListWidgetItem(str(spectrum.id) + ' Single Score ' + str(sampleComponent.score[0]))
        #   self.leftListWidget.addItem(item)

    self.connect(self.rightListWidget, QtCore.SIGNAL("dropped"), self.itemsDropped)
    self.connect(self.leftListWidget, QtCore.SIGNAL("dropped"), self.itemsDropped)
    self.leftListWidget.currentItemChanged.connect(self.itemClicked)

  def populatePullDownSelection(self):
    ''' fills the pulldown with the mixtures on the project (excludes the one already selected on the left listWidget)  '''
    currentMixture = self.scoringTable.getCurrentObject()
    self.dataPullDown = ['Select An Option', 'New empty mixture']
    for mixture in self.getMixture():
      if mixture.name != currentMixture.name:
       self.dataPullDown.append(mixture.name)
    self.pullDownSelection.setData(self.dataPullDown)
    self.pullDownSelection.activated[str].connect(self.pullDownSelectionAction)

  def pullDownSelectionAction(self, selected):
    ''' Each selection gives different behaviour on the right listWidget.
     '''
    if selected == 'New empty mixture':
      self.rightListWidget.clear()
      self.rightListWidget.setAcceptDrops(True)
      self.leftListWidget.setAcceptDrops(True)
      self.rightMixtureLineEdit.setText('NewMixture')

    if selected == 'Select An Option':
      self.selectAnOptionState()
      self.populateLeftListWidget()
      self.rightListWidget.setAcceptDrops(False)
      self.leftListWidget.setAcceptDrops(False)

    else:
      sample = self.project.getByPid('SA:'+selected)
      if sample is not None:
        self.populateRightListWidget(sample)
        self.rightListWidget.setAcceptDrops(True)
        self.leftListWidget.setAcceptDrops(True)

  def populateRightListWidget(self, sample):
    ''' fills the right widget with spectra scores from the selected mixture on the pulldown '''
    if sample is not None:
      self.rightMixtureLineEdit.setText(str(sample.name))
      self.rightListWidget.clear()
      color = QtGui.QColor('Red')
      header = QtGui.QListWidgetItem(str(sample.name))
      header.setFlags(QtCore.Qt.NoItemFlags)
      header.setTextColor(color)
      self.rightListWidget.addItem(header)
      for sampleComponent in sample.sampleComponents:
        spectrum = sampleComponent.substance.referenceSpectra[0]
        item = QtGui.QListWidgetItem(str(spectrum.id) + ' Single Score ' + str(sampleComponent.score[0]))
        self.rightListWidget.addItem(item)
      self.rightListWidget.currentItemChanged.connect(self.getListWidgetItems)

      self.connect(self.rightListWidget, QtCore.SIGNAL("dropped"), self.itemsDropped)
      self.rightListWidget.currentItemChanged.connect(self.itemClicked)


  def getListWidgetItems(self): # to do shorter
    '''Get  Spectra from the right ListWidget '''
    itemsRightWidgetList= []
    rightSpectra = []
    for index in range(self.rightListWidget.count()):
      itemsRightWidgetList.append(self.rightListWidget.item(index))
    for item in itemsRightWidgetList:
      itemText = item.text()
      text, space, value = itemText.partition(' ')
      rightSpectrum = self.project.getByPid('SP:'+text)
      if rightSpectrum is not None:
        rightSpectra.append(rightSpectrum)

    '''Get Spectra from the left ListWidget '''
    itemsLeftWidgetList = []
    leftSpectra = []
    for index in range(self.leftListWidget.count()):
      itemsLeftWidgetList.append(self.leftListWidget.item(index))
    for item in itemsLeftWidgetList:
      itemText = item.text()

      text, space, value = itemText.partition(' ')
      leftSpectrum = self.project.getByPid('SP:'+text)
      if leftSpectrum is not None:
        leftSpectra.append(leftSpectrum)

    return {'leftSpectra':leftSpectra,'rightSpectra':rightSpectra}

  def getListWidgetItemsTest(self, listWidget):
    items= []
    for index in range(listWidget.count()):
      items.append(listWidget.item(index))
    return(items)


  def deleteComponent(self):
    selected = self.leftListWidget.currentRow()
    self.leftListWidget.takeItem(selected)


  def deleteMixture(self):
    ''' delete the mixture from the project '''
    sample = self.scoringTable.getCurrentObject()
    if sample is not None:
      sample.delete()
    self.upDateScoringTable()


  def upDateScoringTable(self):
    ''' refresh the scoring table '''
    self.scoringTable.setObjects(self.getMixture())


  def createNewMixture(self):
    ''' create new mixtures after the items have been moved across the list widgets or a new empty mixture has been selected '''
    getLeftSpectra = self.getListWidgetItems()['leftSpectra']
    getRightSpectra = self.getListWidgetItems()['rightSpectra']

    oldLeftMixture = self.scoringTable.getCurrentObject()
    oldRightMixture = self.getMixtureFromPullDown()

    leftMixtureName = str(self.leftMixtureLineEdit.text())
    rightMixtureName = str(self.rightMixtureLineEdit.text())

    newLeftMixture = setupSamples(getLeftSpectra, 'nSamples', 1, 0.01 , leftMixtureName+'-')
    newRightMixture = setupSamples(getRightSpectra, 'nSamples',1, 0.01 , rightMixtureName+'-')

    oldLeftMixture.delete()
    if self.pullDownSelection.getText() == 'New empty mixture':
      pass
    else:
      oldRightMixture.delete()
    self.confirmNewMixtures()


  def itemsDropped(self):
    ''' Returns the event of dropping data '''
    self.changeButtonStatus()

  def itemClicked(self,  item):
    ''' mouse left click, return the item clicked'''
    pass

  def predictScores(self):  # to do much shorter!!
    ''' Predict scores before to create a different mixture given the left spectra '''

    getLeftSpectra = self.getListWidgetItems()['leftSpectra']
    leftResults = []
    self.leftListWidget.clear()
    for spectrum in getLeftSpectra:
      singleScore = scoring(spectrum,getLeftSpectra)[0]
      itemRight = QtGui.QListWidgetItem(str(spectrum.id)+ ' Single Score ' + str(singleScore))
      self.leftListWidget.addItem(itemRight)
      leftResults.append(singleScore)

    leftMinScore = int(amin(array(leftResults)))
    leftAverageScore = math.floor(average(array(leftResults)))

    itemMinScore = QtGui.QListWidgetItem(str('MinScore ') + str(leftMinScore))
    self.leftListWidget.addItem(itemMinScore)
    itemAverageScore = QtGui.QListWidgetItem(str('AverageScore ') + str(leftAverageScore))
    self.leftListWidget.addItem(itemAverageScore)

    self.oldLeftMixture = getLeftSpectra[0].sample

    if leftMinScore > self.oldLeftMixture.minScore:
      itemMinScore.setTextColor(green)
    if leftMinScore == self.oldLeftMixture.minScore:
      itemMinScore.setTextColor(yellow)
    else:
      itemMinScore.setTextColor(red)

    if leftAverageScore > self.oldLeftMixture.averageScore:
      itemAverageScore.setTextColor(green)
    if leftAverageScore == self.oldLeftMixture.averageScore:
      itemAverageScore.setTextColor(yellow)
    else:
      itemAverageScore.setTextColor(red)

    ''' Predict scores before to create a different mixture given the right spectra '''
    getRightSpectra = self.getListWidgetItems()['rightSpectra']

    rightResults = []
    self.rightListWidget.clear()
    for spectrum in getRightSpectra:
      singleScore = scoring(spectrum,getRightSpectra)[0]
      rightResults.append(singleScore)
      itemRight = QtGui.QListWidgetItem(str(spectrum.id)+ ' Single Score ' + str(singleScore))
      self.rightListWidget.addItem(itemRight)

    rightMinScore = int(amin(array(rightResults)))
    rightAverageScore = math.floor(average(array(rightResults)))

    itemMinScore = QtGui.QListWidgetItem(str('MinScore ') + str(rightMinScore))
    self.rightListWidget.addItem(itemMinScore)
    itemAverageScore = QtGui.QListWidgetItem(str('AverageScore ') + str(rightAverageScore))
    self.rightListWidget.addItem(itemAverageScore)

    self.oldRightMixture = getRightSpectra[0].sample

    if rightMinScore > self.oldRightMixture.minScore:
      itemMinScore.setTextColor(green)
    if rightMinScore == self.oldRightMixture.minScore:
      itemMinScore.setTextColor(yellow)
    else:
      itemMinScore.setTextColor(red)

    if rightAverageScore > self.oldRightMixture.averageScore:
      itemAverageScore.setTextColor(green)
    if rightAverageScore == self.oldRightMixture.averageScore:
      itemAverageScore.setTextColor(yellow)
    else:
      itemAverageScore.setTextColor(red)

    self.temporaryScoringStatus()

  def temporaryScoringStatus(self): # to do shorter
    ''' Disable all the commands so user is forced to take a decision with the new scoring after a mixture has been recalculated '''
    self.pullDownSelection.setEnabled(False)
    for i in range(3):
      self.tabWidget.setTabEnabled(i,False)
    self.calculateButtons.hide()
    self.applyButtons.show()
    self.rightListWidget.setAcceptDrops(False)
    self.leftListWidget.setAcceptDrops(False)
    for item in self.getListWidgetItemsTest(self.leftListWidget):
      item.setFlags(QtCore.Qt.NoItemFlags)
    for item in self.getListWidgetItemsTest(self.rightListWidget):
      item.setFlags(QtCore.Qt.NoItemFlags)
    self.warningLabel.show()
    self.scoringTable.selectionCallback = None
    print('Selection Table Disabled. Cancel or apply the new mixtures scores')

  def confirmNewMixtures(self): # to do shorter
    ''' restore the normal behavior if the buttons and tabs '''
    for i in range(3):
      self.tabWidget.setTabEnabled(i,True)
    self.pullDownSelection.setEnabled(True)
    self.selectAnOptionState()
    self.upDateScoringTable()
    self.calculateButtons.show()
    self.disableRecalculateButtons()
    self.applyButtons.hide()
    self.populateLeftListWidget()
    self.warningLabel.hide()
    self.scoringTable.selectionCallback = self.tableSelection

  def resetMixtureScore(self):
    ''' restore the first scores calculated  '''
    self.resetInitialState()
    # self.populateLeftListWidget()
    # self.populateRightListWidget(self.getMixtureFromPullDown)
    # self.warningLabel.hide()
    # self.scoringTable.selectionCallback = self.tableSelection

  def getMixtureFromPullDown(self):
    ''' Documentation '''
    currentPullDownSelection = self.pullDownSelection.getText()
    mixturePullDown = self.project.getByPid('SA:'+currentPullDownSelection)
    if mixturePullDown is not None:
      return mixturePullDown

  def resetInitialState(self):
    ''' clears up the right listWidget and restores the buttons  '''
    for i in range(3):
      self.tabWidget.setTabEnabled(i,True)
    self.pullDownSelection.setEnabled(True)
    self.selectAnOptionState()
    self.calculateButtons.show()
    self.disableRecalculateButtons()
    self.applyButtons.hide()
    self.warningLabel.hide()
    self.populateLeftListWidget()
    self.scoringTable.selectionCallback = self.tableSelection


  def changeLeftMixtureName(self):
    ''' changes the mixture name '''
    currentMixture = self.scoringTable.getCurrentObject()
    if self.leftMixtureLineEdit.isModified():
      currentMixture.rename(self.leftMixtureLineEdit.text())

  def changeRightMixtureName(self):
    ''' changes the mixture name '''
    currentPullDownSelection = self.pullDownSelection.getText()
    mixturePullDown = self.project.getByPid(currentPullDownSelection)
    if mixturePullDown is not None:
      print(mixturePullDown)
      if self.rightMixtureLineEdit.isModified():
        mixturePullDown.rename(self.rightMixtureLineEdit.text())

  def initialLabelListWidgetRight(self):
    ''' Creates an initial message on the right ListWidget '''
    item = QtGui.QListWidgetItem(' Drag and drop items across to calculate the new scores')
    item.setFlags(QtCore.Qt.NoItemFlags)
    self.rightListWidget.addItem(item)

  def selectAnOptionState(self):
    ''' Creates an initial status on the right ListWidget '''
    self.pullDownSelection.select('Select An Option')
    self.rightListWidget.clear()
    self.rightListWidget.setAcceptDrops(False)
    self.initialLabelListWidgetRight()
    self.disableRecalculateButtons()
    self.rightMixtureLineEdit.setText('')

  def disableRecalculateButtons(self):
    ''' disables the buttons until a change occurs  '''
    for button in self.calculateButtons.buttons:
      button.setEnabled(False)
      button.setStyleSheet("background-color:#868D9D; color: #000000")

  def changeButtonStatus(self):
    ''' enables the buttons when a change occurs '''
    for button in self.calculateButtons.buttons:
      button.setEnabled(True)
      if self.colourScheme == 'dark':
        button.setStyleSheet("background-color:#535a83; color: #bec4f3")
      else:
       button.setStyleSheet("background-color:#bd8413; color: #fdfdfc")


  ''' ######## ==== Gui Spectrum View properties  ====  ########   '''

  def displayMixture(self, sample):
    ''' displays all the spectra present in a mixture '''
    currentDisplay = self.clearDisplayView()
    for spectrum in sample.spectra:
      currentDisplay.displaySpectrum(spectrum)

  def navigateToPosition(self, peaks):
    ''' for a given peak, it navigates to the peak position on the display  '''
    displayed = self.project.strips[0].spectrumDisplay
    self.project._appBase.mainWindow.clearMarks()
    for peak in peaks:
      navigateToPeakPosition(self.project, peak=peak, selectedDisplays=[displayed.pid], markPositions=True)

  def clearDisplayView(self):
    ''' Deletes all the spectra from the display '''
    if len(self.project.strips)>0:
      self.currentDisplayed = self.project.strips[0]
    else:
      self.currentDisplayed=self.openNewDisplay()
      self.closeBlankDisplay()

    for spectrumView in self.currentDisplayed.spectrumViews:
      spectrumView.delete()
    return self.currentDisplayed

  def openNewDisplay(self):
    ''' opens a new spectrum display '''
    spectrumDisplay = self.mainWindow.createSpectrumDisplay(self.project.spectra[0])
    self.dockArea.moveDock(spectrumDisplay.dock, position='top', neighbor=self)
    return spectrumDisplay

  def closeBlankDisplay(self):
    ''' deletes a dock display if present one '''
    if 'BLANK DISPLAY' in self.dockArea.findAll()[1]:
      self.dockArea.guiWindow.deleteBlankDisplay()


  ''' ######## ==== Settings  ====  ########   '''

  def createSettingGroup(self):
    '''GroupBox creates the settingGroup'''
    self.settingButtons = ButtonList(self, texts = ['','',],
                                callbacks=[None,self.openOptimisationModule], icons=[ self.exportIcon, self.settingIcon,],
                                tipTexts=['', ''], direction='H')
    self.settingButtons.setStyleSheet("background-color: transparent")
    self.settingFrameLayout.addStretch(1)
    self.settingFrameLayout.addWidget(self.settingButtons)

  # def exportToXls(self):
    # ''' Export a simple xlxs file from the results '''
    # self.nameAndPath = ''
    # fType = 'XLS (*.xlsx)'
    # dialog = QtGui.QFileDialog
    # filePath = dialog.getSaveFileName(self,filter=fType)
    # self.nameAndPath = filePath
    #
    # sampleColumn = [str(sample.pid) for sample in self.project.samples]
    # sampleComponents = [str(sample.spectra) for sample in self.project.samples]
    # df = DataFrame({'Mixture name': sampleColumn, 'Sample Components': sampleComponents})
    # df.to_excel(self.nameAndPath, sheet_name='sheet1', index=False)
  # def closeDock(self):
  #
  #   for dock in self.dockArea.findAll()[1].values():
  #     if dock.label.isHidden():
  #       dock.close()
  #   self.close()

  def openOptimisationModule(self):
    mixtureOptimisation = MixtureOptimisation(self.project)
    mixtureOptimisationDock = self.dockArea.addDock(mixtureOptimisation, position='bottom')


