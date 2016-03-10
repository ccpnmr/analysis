__author__ = 'luca'


from PyQt4 import QtCore, QtGui
from ccpncore.gui.ButtonList import ButtonList
from ccpncore.gui.Icon import Icon
from ccpncore.gui.Table import ObjectTable, Column
from ccpncore.gui.Button import Button
from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.PulldownList import PulldownList
from functools import partial
from ccpncore.gui.CompoundView import CompoundView, Variant, importSmiles
from application.core.lib.Window import navigateToNmrResidue, navigateToPeakPosition



class MixtureAnalysis(CcpnDock):

  '''Creates a module of four tabs on the dock to analyse the mixtures.

  '''
  def __init__(self, project, samples=None,):
    super(MixtureAnalysis, self)
    CcpnDock.__init__(self, name='Mixture Analysis')
    self.project = project
    self.settingIcon = Icon('iconsNew/applications-system')
    self.exportIcon = Icon('iconsNew/export')


    self.compound = None
    self.variant = None
    self.smiles = ''
    self.compoundView  = CompoundView(self)


    # self.clearDisplayView()
    ######## ========   Set Layout  ====== ########

    self.mainFrame = QtGui.QFrame()
    self.mainLayout = QtGui.QVBoxLayout()
    self.mainFrame.setLayout(self.mainLayout)
    self.layout.addWidget(self.mainFrame, 0,0)

    self.settingFrameLayout = QtGui.QHBoxLayout()
    self.analysisFrameLayout = QtGui.QHBoxLayout()

    self.mainLayout.addLayout(self.settingFrameLayout)
    self.mainLayout.addLayout(self.analysisFrameLayout)

    self.createSettingGroup()
    self.scoringTable()
    self.colourScheme = self.project._appBase.preferences.general.colourScheme
    self.tabWidget = QtGui.QTabWidget()
    self.analysisFrameLayout.addWidget(self.tabWidget)





    ######## ========   Set Tabs  ====== ########

    self.tabPeaksMolecule = QtGui.QFrame()

    self.tabPeaksMoleculeLayout = QtGui.QGridLayout()
    self.tabPeaksMolecule.setLayout(self.tabPeaksMoleculeLayout)
    self.tabWidget.addTab(self.tabPeaksMolecule, 'Components peaks')

    self.tabMoleculeView = QtGui.QFrame()
    self.tabMoleculeViewLayout = QtGui.QHBoxLayout()
    self.tabMoleculeView.setLayout(self.tabMoleculeViewLayout)
    self.tabWidget.addTab(self.tabMoleculeView, 'Components structure')

    self.tabMoleculeInfo = QtGui.QFrame()
    self.tabMoleculeInfoLayout = QtGui.QVBoxLayout()
    self.tabMoleculeInfo.setLayout(self.tabMoleculeInfoLayout)
    self.tabWidget.addTab(self.tabMoleculeInfo, 'Components Info')

    self.tabMixturesManagement = QtGui.QFrame()
    self.tabMixturesManagementLayout = QtGui.QGridLayout()
    self.tabMixturesManagement.setLayout(self.tabMixturesManagementLayout)
    self.tabWidget.addTab(self.tabMixturesManagement, 'Mixtures Management')

    self.toolBarComponents = QtGui.QToolBar()
    self.tabPeaksMoleculeLayout.addWidget(self.toolBarComponents, 0,0,1,0)


    self.widgetsTabComponentPeak()
    self.widgetsTabComponentsInfo()
    self.mixtureManagementWidgets()

    self.current = project._appBase.current
    self.current.registerNotify(self.findSelectedPeaks, 'peaks')
    self.findSelectedPeaks(peaks=None)

    # self.setColours()

  def createSettingGroup(self):
    '''GroupBox creates the settingGroup'''
    self.settingButtons = ButtonList(self, texts = ['','',],
                                callbacks=[None,None], icons=[self.settingIcon, self.exportIcon],
                                tipTexts=['', ''], direction='H')
    self.settingFrameLayout.addStretch(1)
    self.settingFrameLayout.addWidget(self.settingButtons)


  def scoringTable(self):
    listOfSample = []

    for sample in self.project.samples:
      if hasattr(sample, 'minScore'):
        listOfSample.append(sample)

    columns = [Column('Mixture Name', lambda sample:str(sample.pid)),
               Column('N Components', lambda sample: (int(len(sample.spectra)))),
               Column('Min Score', lambda sample: int(sample.minScore)),
               Column('Average Score', lambda sample: int(sample.averageScore))]

    self.scoringTable = ObjectTable(self, columns,  objects=[], selectionCallback=self.tableSelection)
    self.scoringTable.setFixedWidth(400)


    if len(listOfSample)>0:
      self.scoringTable.setObjects(listOfSample)
    self.analysisFrameLayout.addWidget(self.scoringTable)


  def tableSelection(self, row:int=None, col:int=None, obj:object=None):
    ''' Documentation '''

    objRow = self.scoringTable.getCurrentObject()
    self.createButtons(objRow)
    self.displayMixture(objRow)

    self.displayMolecules(objRow)
    self.displayMixturesInfo(objRow)
    self.populateMixtureManagementWidgets(objRow)



  def displayMixturesInfo(self, sample):
    self.sampleComponents =  sample.sampleComponents
    substances = [sc.substance for sc in self.sampleComponents]
    self.sampleInfoTable.setObjects(substances)

  
  def displayMolecules(self, sample):
    self.clearTabMoleculeView(sample)

    for component in sample.sampleComponents:
      chemicalName = (''.join(str(x) for x in component.substance.synonyms))
      smiles = component.substance.smiles
      self.compoundView2 = CompoundView(self)
      self.tabMoleculeViewLayout.addWidget(self.compoundView2)
      compound = importSmiles(smiles)
      variant = list(compound.variants)[0]
      self.setCompound2(compound, replace = True)
      x, y = self.getAddPoint2()
      variant.snapAtomsToGrid(ignoreHydrogens=False)
      self.compoundView2.centerView()
      self.compoundView.resetView()
      self.compoundView2.updateAll()

  def displayMixture(self, sample):
    currentDisplay = self.clearDisplayView()
    for spectrum in sample.spectra:
      currentDisplay.displaySpectrum(spectrum)

  def createButtons(self, sample):

    self.toolBarComponents.clear()
    for spectrum in sample.spectra:
      self.componentButton = Button(self, text=spectrum.id)#,toggle=True)
      self.componentButton.clicked.connect(partial(self.toggleComponentButton, spectrum, sample, self.componentButton))
      # self.componentButton.setChecked(False)
      self.componentButton.setFixedHeight(40)
      self.toolBarComponents.addWidget(self.componentButton)

  def toggleComponentButton(self, spectrum, sample, componentButton):

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
      # self.navigateToPosition(peakList.peaks)
      self.peakTable.setObjects(self.peakListObjects[-1])

    for sampleComponent in sample.sampleComponents:

      if sampleComponent.substance.referenceSpectra[0] == spectrum:
        smiles = sampleComponent.substance.smiles
        compound = importSmiles(smiles)
        variant = list(compound.variants)[0]
        self.setCompound(compound, replace = True)
        x, y = self.getAddPoint()
        variant.snapAtomsToGrid(ignoreHydrogens=False)
        self.compoundView.centerView()
        self.compoundView.resetView()
        self.compoundView.updateAll()

  def navigateToPosition(self, peaks):
    displayed = self.project.strips[0].spectrumDisplay
    self.project._appBase.mainWindow.clearMarks()
    for peak in peaks:
      navigateToPeakPosition(self.project, peak=peak, selectedDisplays=[displayed.pid], markPositions=True)


  def widgetsTabComponentPeak(self,):
    self.peakListObjects = []

    columns = [Column('#', 'serial'),
               Column('Position', lambda peak: '%.3f' % peak.position[0] ),
               Column('Height', lambda peak: self._getPeakHeight(peak))]

    self.peakTable = ObjectTable(self, columns, objects=[], actionCallback=None, selectionCallback=self.selectPeak,
               multiSelect=True)
    self.tabPeaksMoleculeLayout.addWidget(self.peakTable, 1,0)
    self.tabPeaksMoleculeLayout.addWidget(self.compoundView, 1,1)
    # self.peakTable.setObjects([])


  def selectPeak(self, row:int=None, col:int=None, obj:object=None):

    self.selectedTablePeaks = self.peakTable.getSelectedObjects()
    for peak in self.selectedTablePeaks:
      if peak.isSelected:
        print(self.project._appBase.current.peaks, 'currents')
        # self.project._appBase.current.clearPeaks()

      else:
        peak.isSelected = True
        self.project._appBase.current.peak = peak



  def findSelectedPeaks(self,  peaks:None):
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



  def clearTabMoleculeView(self, sample):

    layout = self.tabMoleculeViewLayout
    items = [layout.itemAt(i) for i in range(layout.count())]
    if len(items)>0:
      for item in items:
        item.widget().deleteLater()

  def widgetsTabComponentsInfo(self):

    columns = [Column('Name', lambda substance:str(substance.pid)),
               Column('logP', lambda substance:str(substance.logPartitionCoefficient)),
               Column('psa', lambda substance:str(substance.polarSurfaceArea)),
               Column('H acceptors', lambda substance:str(substance.hBondAcceptorCount)),
               Column('H donors', lambda substance:str(substance.hBondDonorCount)),
               Column('comment', lambda substance:str(substance.comment))]

    self.sampleInfoTable = ObjectTable(self, columns, objects=[])
    self.tabMoleculeInfoLayout.addWidget(self.sampleInfoTable)


  def mixtureManagementWidgets(self):

    self.mixtureListWidget = ThumbListWidget(self)
    self.tabMixturesManagementLayout.addWidget(self.mixtureListWidget, 1,0)

    self.applyButtons = ButtonList(self, texts = ['Calculate Score', 'Apply'], callbacks=[None,None], icons=[None,None],
                                       tipTexts=[None,None], direction='h', hAlign='r')
    self.tabMixturesManagementLayout.addWidget(self.applyButtons, 2,1)

    self.mixtureListWidget2 = ThumbListWidget(self)
    self.mixtureListWidget2.setFixedWidth(250)
    self.tabMixturesManagementLayout.addWidget(self.mixtureListWidget2, 1,1)

    self.pullDownSelection = PulldownList(self,)
    self.pullDownSelection.setFixedWidth(250)

    self.tabMixturesManagementLayout.addWidget(self.pullDownSelection, 0,1)

  def populateMixtureManagementWidgets(self, sample):
    self.mixtureListWidget.clear()
    if sample is not None:

      color = QtGui.QColor('Red')

      header = QtGui.QListWidgetItem(str(sample.id))

      header.setFlags(QtCore.Qt.NoItemFlags)
      header.setTextColor(color)
      self.mixtureListWidget.addItem(header)

      for sampleComponent in sample.sampleComponents:
        item = QtGui.QListWidgetItem(str(sampleComponent.id)+ ' single score Not implemented')
        # item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)# | QtCore.Qt.ItemIsEditable)
        self.mixtureListWidget.addItem(item)

    self.dataPullDown = []

    selectAnOption = 'Select An Option'
    self.dataPullDown.append(selectAnOption)
    selectNew = 'New empty mixture'
    self.dataPullDown.append(selectNew)

    for sa in self.project.samples:
      self.dataPullDown.append(sa.name)

    self.pullDownSelection.setData(self.dataPullDown)
    self.pullDownSelection.activated[str].connect(self.pullDownSelectionAction)

    self.connect(self.mixtureListWidget, QtCore.SIGNAL("dropped"), self.itemsDropped)
    self.mixtureListWidget.currentItemChanged.connect(self.itemClicked)


  def pullDownSelectionAction(self, selected):

    if selected == 'New empty mixture':
      self.mixtureListWidget2.clear()

    elif selected == 'Select An Option':
      pass
    else:
      sample = self.project.getByPid('SA:'+selected)
      self.populateMixtureManagementWidgets2(sample)

  def populateMixtureManagementWidgets2(self, sample):
    self.mixtureListWidget2.clear()
    color = QtGui.QColor('Red')
    header = QtGui.QListWidgetItem(str(sample.id))
    header.setFlags(QtCore.Qt.NoItemFlags)
    header.setTextColor(color)
    self.mixtureListWidget2.addItem(header)

    for sampleComponent in sample.sampleComponents:
      item = QtGui.QListWidgetItem(str(sampleComponent.id)+ ' single score Not implemented')
      self.mixtureListWidget2.addItem(item)
    self.connect(self.mixtureListWidget2, QtCore.SIGNAL("dropped"), self.itemsDropped)
    self.mixtureListWidget2.currentItemChanged.connect(self.itemClicked)

  def itemsDropped(self, arg):
    print ('items_dropped', arg)

  def itemClicked(self, arg):
    print(arg)







  def _getPeakHeight(self, peak):
    if peak.height:
      return peak.height*peak.peakList.spectrum.scale

  def clearDisplayView(self):
    ''' Documentation '''

    currentDisplayed = self.project.strips[0]
    for spectrumView in currentDisplayed.spectrumViews:
      spectrumView.delete()

    return currentDisplayed


  def setCompound(self, compound, replace=True):
    ''' Set the compound on the graphic scene. '''

    if compound is not self.compound:
      if replace or not self.compound:
        self.compound = compound
        variants = list(compound.variants)
        if variants:
          for variant2 in variants:
            if (variant2.polyLink == 'none') and (variant2.descriptor == 'neutral'):
              variant = variant2
              break
          else:
            for variant2 in variants:
              if variant2.polyLink == 'none':
                variant = variant2
                break
            else:
              variant = variants[0]
        else:
          variant =  Variant(compound)
          print(variant)
        self.variant = variant
        self.compoundView.setVariant(variant)

      else:
        variant = list(compound.variants)[0]
        x, y = self.getAddPoint()
        self.compound.copyVarAtoms(variant.varAtoms, (x,y))
        self.compoundView.centerView()
        self.compoundView.updateAll()

  def getAddPoint(self):
    ''' Set the compound on the specific position on the graphic scene. '''

    compoundView = self.compoundView
    globalPos = QtGui.QCursor.pos()
    pos = compoundView.mapFromGlobal(globalPos)
    widget = compoundView.childAt(pos)
    if widget:
      x = pos.x()
      y = pos.y()
    else:
      x = compoundView.width()/2.0
      y = compoundView.height()/2.0
    point = compoundView.mapToScene(x, y)
    return point.x(), point.y()


  def setCompound2(self, compound, replace=True):
    ''' Set the compound on the graphic scene. '''

    if compound is not self.compound:
      if replace or not self.compound:
        self.compound = compound
        variants = list(compound.variants)
        if variants:
          for variant2 in variants:
            if (variant2.polyLink == 'none') and (variant2.descriptor == 'neutral'):
              variant = variant2
              break
          else:
            for variant2 in variants:
              if variant2.polyLink == 'none':
                variant = variant2
                break
            else:
              variant = variants[0]
        else:
          variant =  Variant(compound)
          print(variant)
        self.variant = variant
        self.compoundView2.setVariant(variant)

      else:
        variant = list(compound.variants)[0]
        x, y = self.getAddPoint()
        self.compound.copyVarAtoms(variant.varAtoms, (x,y))
        self.compoundView2.centerView()
        self.compoundView2.updateAll()

  def getAddPoint2(self):
    ''' Set the compound on the specific position on the graphic scene. '''

    compoundView = self.compoundView2
    globalPos = QtGui.QCursor.pos()
    pos = compoundView.mapFromGlobal(globalPos)
    widget = compoundView.childAt(pos)
    if widget:
      x = pos.x()
      y = pos.y()
    else:
      x = compoundView.width()/2.0
      y = compoundView.height()/2.0
    point = compoundView.mapToScene(x, y)
    return point.x(), point.y()




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


class ThumbListWidget(QtGui.QListWidget):
    def __init__(self, type, parent=None):
        super(ThumbListWidget, self).__init__(parent)
        self.setIconSize(QtCore.QSize(124, 124))
        self.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super(ThumbListWidget, self).dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            super(ThumbListWidget, self).dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
            links = []
            for url in event.mimeData().urls():
                links.append(str(url.toLocalFile()))
            self.emit(QtCore.SIGNAL("dropped"), links)
        else:
            event.setDropAction(QtCore.Qt.MoveAction)
            super(ThumbListWidget, self).dropEvent(event)
