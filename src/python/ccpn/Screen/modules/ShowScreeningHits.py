__author__ = 'luca'


from functools import partial
from PyQt4 import QtCore, QtGui
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.GroupBox import GroupBox
from ccpn.ui.gui.widgets.ListWidget import ListWidget

from ccpn.ui.gui.widgets.Module import CcpnModule
from ccpn.ui.gui.widgets.Table import ObjectTable, Column, ObjectTableItemDelegate

from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.CompoundView import CompoundView, Variant, importSmiles
from ccpn.ui.gui.lib.Window import navigateToNmrResidue, navigateToPeakPosition

Qt = QtCore.Qt
Qkeys = QtGui.QKeySequence

class ShowScreeningHits(CcpnModule):
  def __init__(self, parent=None, project=None, **kw):
    super(ShowScreeningHits, self)
    CcpnModule.__init__(self, name='Hit Analysis')
    self.project = project
    self.setFixedHeight(300)
    # self.createDummyHits()
    # if self._appBase.ui.mainWindow is not None:
    #   self.mainWindow = self._appBase.ui.mainWindow
    # else:
    #   self.mainWindow = self._appBase._mainWindow
    self.mainWindow = parent
    self.moduleArea = self.mainWindow.moduleArea
    self.framework = self.mainWindow.framework
    self.generalPreferences = self.framework.preferences.general
    self.colourScheme = self.generalPreferences.colourScheme
    self.moduleArea = self.mainWindow.moduleArea
    self.colourScheme = self.project._appBase.preferences.general.colourScheme

    ######## ======== Set modules on moduleArea ====== ########

    if 'BLANK DISPLAY' in self.moduleArea.findAll()[1]:
      blankDisplay = self.moduleArea.findAll()[1]['BLANK DISPLAY']
      blankDisplay.close()

    ######## ======== Icons ====== ########
    self.acceptIcon = Icon('icons/dialog-apply')
    self.rejectIcon = Icon('icons/reject')
    self.nextAndCommitIcon = Icon('icons/commitNextCopy')
    self.previousAndCommitIcon = Icon('icons/commitPrevCopy')
    self.nextIcon = Icon('icons/next')
    self.previousIcon = Icon('icons/previous')
    self.undoIcon = Icon('icons/edit-undo')
    self.removeIcon = Icon('icons/list-remove')
    self.settingIcon = Icon('icons/applications-system')
    self.exportIcon = Icon('icons/export')

    ######## ======== Set Main Layout ====== ########
    self.mainFrame = QtGui.QFrame()
    self.mainLayout = QtGui.QVBoxLayout()
    self.mainFrame.setLayout(self.mainLayout)
    self.layout.addWidget(self.mainFrame, 0,0)

    ######## ======== Set Secondary Layout ====== ########
    self.settingFrameLayout = QtGui.QHBoxLayout()
    self.hitFrameLayout = QtGui.QHBoxLayout()
    self.mainLayout.addLayout(self.settingFrameLayout)
    self.mainLayout.addLayout(self.hitFrameLayout)

    ######## ======== Create widgets ====== ########
    self._createHitTableGroup()
    self._createHitSelectionGroup()
    self._createHitDetailsGroup() #keep after hitSelectionGroup
    self._createSettingGroup()

  def _createHitTableGroup(self):
    '''GroupBox: creates the hitTableGroup'''

    self.hitTableGroup = GroupBox()
    self.hitTableGroup.setFixedWidth(320)
    self.hitTableGroupVLayout = QtGui.QGridLayout()
    self.hitTableGroupVLayout.setAlignment(QtCore.Qt.AlignTop)
    self.setLayout(self.hitTableGroupVLayout)
    self.hitTableGroup.setLayout(self.hitTableGroupVLayout)
    self.hitFrameLayout.addWidget(self.hitTableGroup, 0)
    self._createHitTable()


  def _createHitSelectionGroup(self):
    '''GroupBox creates the hitSelectionGroup'''

    self.hitSelectionGroup = GroupBox()
    self.hitSelectionGroup.setFixedWidth(250)
    self.hitSelectionGroupLayout = QtGui.QVBoxLayout()
    self.hitSelectionGroupLayout.setAlignment(QtCore.Qt.AlignTop)
    self.setLayout(self.hitSelectionGroupLayout)
    self.hitSelectionGroup.setLayout(self.hitSelectionGroupLayout)
    self.hitFrameLayout.addWidget(self.hitSelectionGroup, 1)
    self._createWidgetsHitSelectionGroup()


  def _createHitDetailsGroup(self):
    '''GroupBox creates the hitDetailsGroup'''

    self.hitDetailsGroup = GroupBox()
    # self.hitDetailsGroup.setFixedWidth(200)
    self.hitDetailsGroupLayout = QtGui.QGridLayout()
    self.hitDetailsGroupLayout.setAlignment(QtCore.Qt.AlignTop)
    self.setLayout(self.hitDetailsGroupLayout)
    self.hitDetailsGroup.setLayout(self.hitDetailsGroupLayout)
    self.hitFrameLayout.addWidget(self.hitDetailsGroup, 2)
    self._createHitDetailsWidgets()

  def _createSettingGroup(self):
    '''GroupBox creates the settingGroup'''

    self.settingButtons = ButtonList(self, texts = ['','',],
                                     callbacks=[self._createExportButton, self._createViewSettingButton, ],
                                     icons=[self.exportIcon,self.settingIcon,],
                                     tipTexts=['', ''], direction='H')
    self.settingButtons.setStyleSheet("background-color: transparent")
    self.settingFrameLayout.addStretch(1)
    self.settingFrameLayout.addWidget(self.settingButtons)


  def _createHitTable(self):
    ''' Documentation '''
    # spacer = QtGui.QSpacerItem(20,40)
    # self.hitTableGroupVLayout.addItem(spacer)

    columns = [Column('Sample', lambda hit:str(hit.sample.name)),
               Column('Hit Name', lambda hit:str(hit.substanceName)),
               Column('Confirmed', lambda hit:str(hit.comment), setEditValue=lambda hit, value: self._testEditor(hit, value)),
               Column('Efficiency', lambda hit:str(hit.meritCode), setEditValue=lambda hit, value: self._scoreEdit(hit, value))]

    self.hitTable = ObjectTable(self, columns, actionCallback=self._hitTableCallback, selectionCallback=self._showAllOnTableSelection, objects=[])
    self.hitTableGroupVLayout.addWidget(self.hitTable)
    self.listOfHits = self.project.spectrumHits
    for hit in self.listOfHits:
      hit.comment = 'No'
    self.hitTable.setObjects(self.listOfHits)


  def _createHitDetailsWidgets(self):
    ''' Documentation '''

    self.listWidgetsHitDetails = QtGui.QListWidget()
    self.listWidgetsHitDetails.setMaximumSize(400,200)
    self.listWidgetsHitDetails.setMinimumSize(200,200)
    self.hitDetailsGroupLayout.addWidget(self.listWidgetsHitDetails, 1,0)


  def _createViewSettingButton(self):
    print('This function has not been implemented yet')

    # menuViewSettingButton = QtGui.QMenu(self)
    # menuViewSettingButton.addAction('Hit table')
    # menuViewSettingButton.addAction('Hit Details')
    # menuViewSettingButton.addAction('')
    # self.settingButtons.buttons[0].setMenu(menuViewSettingButton)

  def _createExportButton(self):
    print('This function has not been implemented yet')

    # menuExportButton = QtGui.QMenu(self)
    # menuExportButton.addAction('Export Hit Table')
    # menuExportButton.addAction('Export Hit Detail')
    # menuExportButton.addAction('Export Hit Structure')
    # menuExportButton.addAction('Export All')
    # self.settingButtons.buttons[1].setMenu(menuExportButton)

  def _createWidgetsHitSelectionGroup(self):
    ''' Documentation '''

    self.pullDownHit = PulldownList(self, hAlign='c' )
    self.hitSelectionGroupLayout.addWidget(self.pullDownHit)

    self.showDeleteHitButtons = ButtonList(self, texts = ['Delete Hit',' Show all'], callbacks=[self._deleteHit, self._showAllSampleComponentsOnPullDownHit], icons=[None, None],
                                           tipTexts=['Delete Hit from project', 'Show all Components '], direction='H', hAlign='c')
    self.hitSelectionGroupLayout.addWidget(self.showDeleteHitButtons)
    self.addHitButton = ButtonList(self, texts=['Cancel',' Add Hit'], callbacks=[self._cancelPullDownSelection, self._addHit], icons=[None, None],
                                   tipTexts=['Delete Hit from project', 'Show all Components '], direction='H', hAlign='c')

    self.hitSelectionGroupLayout.addWidget(self.addHitButton)
    self.addHitButton.hide()
    self.acceptRejectButtons = ButtonList(self, texts = ['',''], callbacks=[self._rejectAssignment, self._acceptAssignment], icons=[self.rejectIcon, self.acceptIcon, ],
                                          tipTexts=['Reject Assignment', 'Accept Assignment'], direction='H', hAlign='c')
    self.acceptRejectButtons.setFixedHeight(80)
    self.hitSelectionGroupLayout.addWidget(self.acceptRejectButtons)
    self.nextPrevCommitButtons = ButtonList(self, texts = ['',''], callbacks=[self._commitMovePreviousRow, self._commitMoveNextRow],
                                            icons=[self.previousAndCommitIcon, self.nextAndCommitIcon],
                                            tipTexts=['Commit Changes and Move previous', 'Commit Changes and Move Next'], direction='h', hAlign='c')

    self.hitSelectionGroupLayout.addWidget(self.nextPrevCommitButtons)

    self.nextPrevButtons = ButtonList(self, texts = ['',''], callbacks=[self._movePreviousRow, self._moveNextRow],
                                      icons=[self.previousIcon, self.nextIcon],
                                      tipTexts=['Move previous', 'Move Next'], direction='h', hAlign='c')
    self.hitSelectionGroupLayout.addWidget(self.nextPrevButtons)


  def _acceptAssignment(self):
    ''' Documentation '''

    hit = self.pullDownHit.getObject()
    hit.comment = 'Yes'
    self._updateHitTable()

  def _addHit(self):
    ''' Documentation '''

    sampleComponent = self.pullDownHit.getObject()
    self._addNewSpectrumHit(sampleComponent)
    self._showDeleteButton()

  def _addNewSpectrumHit(self, sampleComponent):
    ''' Documentation '''

    newHit = sampleComponent.sample.spectra[0].newSpectrumHit(substanceName=str(sampleComponent.substance.name))
    newHit.comment = 'NewUserHit'
    self.listOfHits.append(newHit)
    self.pullDownHit.setEnabled(False)
    self._updateHitTable()
    self._moveNextRow()

  def _cancelPullDownSelection(self):
    ''' Documentation '''

    self._showDeleteButton()
    self._showAllOnTableSelection()


  def _clearDisplayView(self):
    ''' Documentation '''

    # currentDisplayed = self.project.getByPid('GD:user.View.1D:H')
    currentDisplayed = self.project.strips[0]
    for spectrumView in currentDisplayed.spectrumViews:
      spectrumView.delete()
    if self._appBase.ui.mainWindow is not None:
      mainWindow = self._appBase.ui.mainWindow
    else:
      mainWindow = self._appBase._mainWindow
    mainWindow.clearMarks()
    return currentDisplayed

  def _clearListWidget(self):
    ''' Documentation '''

    self.listWidgetsHitDetails.clear()

  def _commitMoveNextRow(self):
    ''' Documentation '''

    self._acceptAssignment()
    self._moveNextRow()

  def _commitMovePreviousRow(self):
    ''' Documentation '''

    self._acceptAssignment()
    self._movePreviousRow()

  def _createDummyHits(self):
    ''' Testing only '''


    self.samples = self.project.samples
    for sample in self.project.samples:
      self.substance = sample.sampleComponents[0].substance
      self.hit = sample.spectra[0].newSpectrumHit(substanceName=str(self.substance.name))
      self.hit.comment = 'No'
    # return self.project.spectrumHits

  def _deleteHit(self):
    ''' Deletes hit from project and from the table. If is last cleans all graphics
    '''
    hitToDelete = self.pullDownHit.getObject()
    hitToDelete.delete()
    if hitToDelete in self.listOfHits:
      self.listOfHits.remove(hitToDelete)
    self._moveNextRow()
    self._updateHitTable()
    if len(self.listOfHits)<=0:
      self._clearDisplayView()
      self.pullDownHit.setData([])

  def _displayAllSampleComponents(self):
    ''' Documentation '''

    sampleComponentSpectra = [sc.substance.referenceSpectra[0] for sc in self.pullDownHit.currentObject().sample.sampleComponents]
    for spectrum in sampleComponentSpectra:
      spectrum.scale = float(0.5)
      # self.project.getByPid('GD:user.View.1D:H').displaySpectrum(spectrum)
      self.project.strips[0].displaySpectrum(spectrum)

  def _displaySampleAndHit(self):
    ''' Documentation '''

    currentDisplay = self._clearDisplayView()
    for spectrum in self._spectraToDisplay():
      currentDisplay.displaySpectrum(spectrum)
      # currentDisplay.showPeaks(spectrum.peakList)
    # self.project.strips[0].viewBox.autoRange()

  def _displaySelectedComponent(self):
    ''' Documentation '''

    currentDisplayed = self.project.strips[0]._parent
    for spectrumView in currentDisplayed.spectrumViews:
      if spectrumView.spectrum in self._spectraToDisplay():
        currentDisplayed.spectrumActionDict[spectrumView.spectrum._apiDataSource].setChecked(True)
      else:
        currentDisplayed.spectrumActionDict[spectrumView.spectrum._apiDataSource].setChecked(False)
    self._showHitInfoOnDisplay()


  def _getPositionOnSpectrum(self):
    ''' Documentation '''
    peaks = self._getPullDownObj().substance.referenceSpectra[0].peakLists[1].peaks
    positions = [peak.position for peak in peaks]
    return set(list(positions))


  def _getPullDownObj(self):
    ''' Documentation '''

    currentObjPulldown = self.pullDownHit.currentObject()
    if hasattr(currentObjPulldown, 'substanceName'):
      substance = self.project.getByPid('SU:'+currentObjPulldown.substanceName+'.H')
      return substance.sampleComponents[0]
    else:
      sampleComponent = currentObjPulldown
      return sampleComponent


  def _getSampleInfoToDisplay(self):
    ''' Documentation '''

    sample = self._getPullDownObj().sample
    sampleInfo = {'Name':sample.name,
                  'Amount':sample.amount,
                  'CreationDate':sample.creationDate,
                  'PlateIdentifier':sample.plateIdentifier,
                  'RowNumber':sample.rowNumber,
                  'ColumnNumber':sample.columnNumber,
                  'Comment':sample.comment,}
    return sampleInfo


  def _getSubstanceInfoToDisplay(self):
    ''' Documentation '''

    sampleComponent = self._getPullDownObj()
    substance = sampleComponent.substance
    substanceInfo = {'name  ':substance.name,
                  # 'synonyms ':substance.synonyms,
                  'userCode ':substance.userCode,
                  'empiricalFormula ':substance.empiricalFormula,
                  'molecularMass  ':substance.molecularMass,
                  'atomCount  ':substance.atomCount,
                  'bondCount  ':substance.bondCount,
                  'ringCount  ':substance.ringCount,
                  'hBondDonorCount  ':substance.hBondDonorCount,
                  'hBondAcceptorCount ':substance.hBondAcceptorCount,
                  'polarSurfaceArea ':substance.polarSurfaceArea,
                  'logPartitionCoefficien ':substance.logPartitionCoefficient,
                  'comment  ':substance.comment}
    return substanceInfo


  def _getSpectrumHitInfoToDisplay(self):
    ''' Documentation '''

    if len(self._getPullDownObj().spectrumHits)>0:
      hit = self._getPullDownObj().spectrumHits[0]
      hitInfo = {'Score  ':hit.figureOfMerit,
                    'Std  ':hit.meritCode,
                    'NormalisedChange ':hit.normalisedChange,
                    'concentration  ':hit.concentration,
                    'concentrationError ':hit.concentrationError,
                    'comment  ':hit.comment,
                    }
      return hitInfo
    else:
      return {'Add new hit to display contents': ''}


  def _getSelectedSample(self):
    ''' Documentation '''

    return self._getPullDownObj().sample


  def _hideDeleteButton(self):
    ''' Documentation '''

    self.showDeleteHitButtons.hide()
    self.addHitButton.show()


  def _hitTableCallback(self, row:int=None, col:int=None, obj:object=None):
    ''' Documentation '''

    peaks = self._getPullDownObj().substance.referenceSpectra[0].peakLists[1].peaks
    # displayed = self.project.getByPid('GD:user.View.1D:H')
    displayed = self.project.strips[0]._parent
    for peak in peaks:
      navigateToPeakPosition(self.project, peak=peak, selectedDisplays=[displayed.pid], markPositions=True)


  def _moveNextRow(self):
    ''' Documentation '''

    self.currentRowPosition = self.hitTable.getSelectedRows()
    newPosition = self.currentRowPosition[0]+1
    self.hitTable.selectRow(newPosition)
    lastRow = len(self.project.spectrumHits)
    if newPosition == lastRow:
     self.hitTable.selectRow(0)


  def _movePreviousRow(self):
    ''' Documentation '''

    self.currentRowPosition = self.hitTable.getSelectedRows()
    newPosition = self.currentRowPosition[0]-1
    lastRow = len(self.project.spectrumHits)-1
    if newPosition == -1:
      self.hitTable.selectRow(lastRow)
    else:
      self.hitTable.selectRow(newPosition)


  def _populateInfoList(self, name, value):
    ''' Documentation '''

    if value is not None:
      item = QtGui.QListWidgetItem(name+str(value))
      item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)# | QtCore.Qt.ItemIsEditable)
      self.listWidgetsHitDetails.addItem(item)
    else:
      value = 'Not Given'
      item = QtGui.QListWidgetItem(name+str(value))
      self.listWidgetsHitDetails.addItem(item)
      item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)# | QtCore.Qt.ItemIsEditable)


  def _rejectAssignment(self):
    ''' Documentation '''

    rejectedHit = self.pullDownHit.getObject()
    rejectedHit.comment = 'No'
    self._updateHitTable()

  def _showAllOnTableSelection(self, row:int=None, col:int=None, obj:object=None):
    ''' Documentation '''

    objRow = self.hitTable.getCurrentObject()
    self._showHitOnPullDown(objRow)
    self._displaySampleAndHit()
    self._showHitInfoOnDisplay()
    self._hidePeakList()

  def _showHitInfoOnDisplay(self):
    ''' Documentation '''
    self._clearListWidget()
    self._showMolecule()
    self._showTextHitDetails()

  def _showAllSampleComponentsOnPullDownHit(self):
    ''' Documentation '''

    self.pullDownHit.setEnabled(True)
    self.sampleComponents = [x for x in self.pullDownHit.getObject().sample.sampleComponents]
    self.substances = [ substance.name for substance in self.sampleComponents]
    self.pullDownHit.setData(self.substances, self.sampleComponents)#Name,Obj
    self.pullDownHit.activated[str].connect(self._displaySelectedComponent)
    self._displayAllSampleComponents()
    self._hideDeleteButton()

  def _showTextHitDetails(self):
    ''' Documentation '''

    color = QtGui.QColor('Red')
    ''' setSpectrum Hit '''
    headerHit =  QtGui.QListWidgetItem('\nSpectrum Hit Details')
    headerHit.setFlags(QtCore.Qt.NoItemFlags)
    headerHit.setTextColor(color)
    self.listWidgetsHitDetails.addItem(headerHit)
    for name, value in self._getSpectrumHitInfoToDisplay().items():
      self._populateInfoList(name, value)

    ''' setHitPositions '''
    headerHitPositions =  QtGui.QListWidgetItem('\nChanged Peak Position At Ppm ')
    headerHitPositions.setFlags(QtCore.Qt.NoItemFlags)
    headerHitPositions.setTextColor(color)
    self.listWidgetsHitDetails.addItem(headerHitPositions)
    for item in self._getPositionOnSpectrum():
      self.listWidgetsHitDetails.addItem(str(item[0]))

    ''' setSubstance '''
    headerSubstance =  QtGui.QListWidgetItem('\nSubstance Details')
    headerSubstance.setFlags(QtCore.Qt.NoItemFlags)
    headerSubstance.setTextColor(color)
    self.listWidgetsHitDetails.addItem(headerSubstance)
    for name, value in self._getSubstanceInfoToDisplay().items():
      self._populateInfoList(name, value)

    ''' setSample '''
    headerSample =  QtGui.QListWidgetItem('\nSample Details')
    headerSample.setFlags(QtCore.Qt.NoItemFlags)
    headerSample.setTextColor(color)
    self.listWidgetsHitDetails.addItem(headerSample)
    for name, value in self._getSampleInfoToDisplay().items():
      self._populateInfoList(name, value)

  def _showMolecule(self):
    ''' Documentation '''
    substance = self._getPullDownObj().substance
    self.smiles = substance.smiles
    if self.smiles is not None:
      self.compoundView  = CompoundView(self, smiles=self.smiles)
      self.hitDetailsGroupLayout.addWidget(self.compoundView, 1,1)
      self.compoundView.centerView()
      self.compoundView.resetView()
      self.compoundView.updateAll()

  def _showDeleteButton(self):
    ''' Documentation '''

    self.showDeleteHitButtons.show()
    self.addHitButton.hide()

  def _showHitOnPullDown(self, hit):
    ''' Documentation '''

    self.pullDownHit.setData([hit.substanceName], [hit])#Name,Obj
    self.pullDownHit.setEnabled(False)

  def _spectraToDisplay(self):
    ''' return sample spectra and spectrum from the hit pulldown'''
    spectraToDisplay = []

    sampleSpectraToDisplay = [x for x in self.pullDownHit.currentObject().sample.spectra]

    sampleSpectraToDisplay[-1].scale =  float(0.03125)

    spectraToDisplay.append(sampleSpectraToDisplay)
    currentObjPulldown = self.pullDownHit.currentObject()
    if hasattr(currentObjPulldown, 'substanceName'):
      substance = self.project.getByPid('SU:'+currentObjPulldown.substanceName+'.H')
      referenceSpectrum = substance.referenceSpectra[0]
      referenceSpectrum.scale = float(0.5)
      spectraToDisplay[0].append(referenceSpectrum)
    else:
      refSpectrum = currentObjPulldown.substance.referenceSpectra[0]
      refSpectrum.scale = float(0.5)
      spectraToDisplay[0].append(refSpectrum)
    spectraToDisplayPL = [spectrum.peakLists[0] for spectrum in spectraToDisplay[0]]

    return spectraToDisplay[0]

  def _testEditor(self, hit, value):
    ''' Documentation '''
    hit.comment = value

  def _scoreEdit(self, hit, value):
    ''' Documentation '''
    hit.meritCode = value

  def _updateHitTable(self):
    ''' Documentation '''
    self.hitTable.setObjects(self.listOfHits)

  def _hidePeakList(self):
    for peakListView in self.project.strips[0].spectrumDisplay.peakListViews:
        # if peakList == peakListView.peakList:
      peakListView.setVisible(False)


#   def exportToXls(self):
#     ''' Export a simple xlxs file from the results '''
#     self.nameAndPath = ''
#     fType = 'XLS (*.xlsx)'
#     dialog = FileDialog(self, fileMode=0, acceptMode=1, preferences=self.preferences, filter=fType)
#     filePath = dialog.selectedFiles()[0]
#     self.nameAndPath = filePath
#
#     sampleColumn = [str(sample.pid) for sample in self.project.samples]
#     sampleHits = [str(sample.spectrumHits) for sample in self.project.samples]
#     df = DataFrame({'Mixture name': sampleColumn, 'Sample Hits': sampleHits})
#     df.to_excel(self.nameAndPath, sheet_name='sheet1', index=False)


#
#     self.strip.viewBox.autoRange()

# project.spectrumDisplays[0].spectrumActionDict[project.spectrumDisplays[0].spectrumViews[0].spectrum._apiDataSource].setChecked(False)
