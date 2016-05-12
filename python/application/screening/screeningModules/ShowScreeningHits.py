__author__ = 'luca'


from functools import partial
from PyQt4 import QtCore, QtGui
from ccpncore.gui.Base import Base
from ccpncore.gui.GroupBox import GroupBox
from ccpncore.gui.ListWidget import ListWidget

from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.Table import ObjectTable, Column, ObjectTableItemDelegate

from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.ButtonList import ButtonList
from ccpncore.gui.Button import Button
from ccpncore.gui.Icon import Icon
from ccpncore.gui.CompoundView import CompoundView, Variant, importSmiles
from application.core.lib.Window import navigateToNmrResidue, navigateToPeakPosition

Qt = QtCore.Qt
Qkeys = QtGui.QKeySequence

class ShowScreeningHits(CcpnDock, Base):
  def __init__(self, project, **kw):
    super(ShowScreeningHits, self)
    CcpnDock.__init__(self, name='Hit Analysis')
    self.project = project
    self.setFixedHeight(300)
    # self.createDummyHits()
    # self.dockArea = self.project._appBase.mainWindow.dockArea

    self.colourScheme = self.project._appBase.preferences.general.colourScheme

    ######## ======== Icons ====== ########
    self.acceptIcon = Icon('iconsNew/dialog-apply')
    self.rejectIcon = Icon('iconsNew/reject')
    self.nextAndCommitIcon = Icon('iconsNew/commitNextCopy')
    self.previousAndCommitIcon = Icon('iconsNew/commitPrevCopy')
    self.nextIcon = Icon('iconsNew/next')
    self.previousIcon = Icon('iconsNew/previous')
    self.undoIcon = Icon('iconsNew/edit-undo')
    self.removeIcon = Icon('iconsNew/list-remove')
    self.settingIcon = Icon('iconsNew/applications-system')
    self.exportIcon = Icon('iconsNew/export')

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
    self.createHitTableGroup()
    self.createHitSelectionGroup()
    self.createHitDetailsGroup() #keep after hitSelectionGroup
    self.createSettingGroup()

  def createHitTableGroup(self):
    '''GroupBox: creates the hitTableGroup'''

    self.hitTableGroup = GroupBox()
    self.hitTableGroup.setFixedWidth(320)
    self.hitTableGroupVLayout = QtGui.QGridLayout()
    self.hitTableGroupVLayout.setAlignment(QtCore.Qt.AlignTop)
    self.setLayout(self.hitTableGroupVLayout)
    self.hitTableGroup.setLayout(self.hitTableGroupVLayout)
    self.hitFrameLayout.addWidget(self.hitTableGroup, 0)
    self.createHitTable()


  def createHitSelectionGroup(self):
    '''GroupBox creates the hitSelectionGroup'''

    self.hitSelectionGroup = GroupBox()
    self.hitSelectionGroup.setFixedWidth(250)
    self.hitSelectionGroupLayout = QtGui.QVBoxLayout()
    self.hitSelectionGroupLayout.setAlignment(QtCore.Qt.AlignTop)
    self.setLayout(self.hitSelectionGroupLayout)
    self.hitSelectionGroup.setLayout(self.hitSelectionGroupLayout)
    self.hitFrameLayout.addWidget(self.hitSelectionGroup, 1)
    self.createWidgetsHitSelectionGroup()


  def createHitDetailsGroup(self):
    '''GroupBox creates the hitDetailsGroup'''

    self.hitDetailsGroup = GroupBox()
    # self.hitDetailsGroup.setFixedWidth(200)
    self.hitDetailsGroupLayout = QtGui.QGridLayout()
    self.hitDetailsGroupLayout.setAlignment(QtCore.Qt.AlignTop)
    self.setLayout(self.hitDetailsGroupLayout)
    self.hitDetailsGroup.setLayout(self.hitDetailsGroupLayout)
    self.hitFrameLayout.addWidget(self.hitDetailsGroup, 2)
    self.createHitDetailsWidgets()

  def createSettingGroup(self):
    '''GroupBox creates the settingGroup'''

    self.settingButtons = ButtonList(self, texts = ['','',],
                                callbacks=[self.createExportButton,self.createViewSettingButton,],
                                icons=[self.exportIcon,self.settingIcon,],
                                tipTexts=['', ''], direction='H')
    self.settingButtons.setStyleSheet("background-color: transparent")
    self.settingFrameLayout.addStretch(1)
    self.settingFrameLayout.addWidget(self.settingButtons)


  def createHitTable(self):
    ''' Documentation '''
    # spacer = QtGui.QSpacerItem(20,40)
    # self.hitTableGroupVLayout.addItem(spacer)

    columns = [Column('Sample', lambda hit:str(hit.sample.name)),
               Column('Hit Name', lambda hit:str(hit.substanceName)),
               Column('Confirmed', lambda hit:str(hit.comment), setEditValue=lambda hit, value: self.testEditor(hit, value)),
               Column('Efficiency', lambda hit:str(hit.meritCode), setEditValue=lambda hit, value: self.scoreEdit(hit, value))]

    self.hitTable = ObjectTable(self, columns, actionCallback=self.hitTableCallback, selectionCallback=self.showAllOnTableSelection, objects=[])
    self.hitTableGroupVLayout.addWidget(self.hitTable)
    self.listOfHits = self.project.spectrumHits
    for hit in self.listOfHits:
      hit.comment = 'No'
    self.hitTable.setObjects(self.listOfHits)


  def createHitDetailsWidgets(self):
    ''' Documentation '''

    self.listWidgetsHitDetails = QtGui.QListWidget()
    self.listWidgetsHitDetails.setMaximumSize(400,200)
    self.listWidgetsHitDetails.setMinimumSize(200,200)
    self.hitDetailsGroupLayout.addWidget(self.listWidgetsHitDetails, 1,0)


  def createViewSettingButton(self):
    print('This function has not been implemented yet')

    # menuViewSettingButton = QtGui.QMenu(self)
    # menuViewSettingButton.addAction('Hit table')
    # menuViewSettingButton.addAction('Hit Details')
    # menuViewSettingButton.addAction('')
    # self.settingButtons.buttons[0].setMenu(menuViewSettingButton)

  def createExportButton(self):
    print('This function has not been implemented yet')

    # menuExportButton = QtGui.QMenu(self)
    # menuExportButton.addAction('Export Hit Table')
    # menuExportButton.addAction('Export Hit Detail')
    # menuExportButton.addAction('Export Hit Structure')
    # menuExportButton.addAction('Export All')
    # self.settingButtons.buttons[1].setMenu(menuExportButton)

  def createWidgetsHitSelectionGroup(self):
    ''' Documentation '''

    self.pullDownHit = PulldownList(self, hAlign='c' )
    self.hitSelectionGroupLayout.addWidget(self.pullDownHit)

    self.showDeleteHitButtons = ButtonList(self, texts = ['Delete Hit',' Show all'], callbacks=[self.deleteHit, self.showAllSampleComponentsOnPullDownHit], icons=[None, None],
                                       tipTexts=['Delete Hit from project', 'Show all Components '], direction='H', hAlign='c')
    self.hitSelectionGroupLayout.addWidget(self.showDeleteHitButtons)
    self.addHitButton = ButtonList(self, texts=['Cancel',' Add Hit'], callbacks=[self.cancelPullDownSelection, self.addHit], icons=[None, None],
                                       tipTexts=['Delete Hit from project', 'Show all Components '], direction='H', hAlign='c')

    self.hitSelectionGroupLayout.addWidget(self.addHitButton)
    self.addHitButton.hide()
    self.acceptRejectButtons = ButtonList(self, texts = ['',''], callbacks=[self.rejectAssignment, self.acceptAssignment], icons=[self.rejectIcon, self.acceptIcon,],
                                       tipTexts=['Reject Assignment', 'Accept Assignment'], direction='H', hAlign='c')
    self.acceptRejectButtons.setFixedHeight(80)
    self.hitSelectionGroupLayout.addWidget(self.acceptRejectButtons)
    self.nextPrevCommitButtons = ButtonList(self, texts = ['',''], callbacks=[self.commitMovePreviousRow, self.commitMoveNextRow],
                                            icons=[self.previousAndCommitIcon, self.nextAndCommitIcon],
                                       tipTexts=['Commit Changes and Move previous', 'Commit Changes and Move Next'], direction='h', hAlign='c')

    self.hitSelectionGroupLayout.addWidget(self.nextPrevCommitButtons)

    self.nextPrevButtons = ButtonList(self, texts = ['',''], callbacks=[self.movePreviousRow, self.moveNextRow],
                                      icons=[self.previousIcon, self.nextIcon],
                                       tipTexts=['Move previous', 'Move Next'], direction='h', hAlign='c')
    self.hitSelectionGroupLayout.addWidget(self.nextPrevButtons)


  def acceptAssignment(self):
    ''' Documentation '''

    hit = self.pullDownHit.getObject()
    hit.comment = 'Yes'
    self.updateHitTable()

  def addHit(self):
    ''' Documentation '''

    sampleComponent = self.pullDownHit.getObject()
    self.addNewSpectrumHit(sampleComponent)
    self.showDeleteButton()

  def addNewSpectrumHit(self, sampleComponent):
    ''' Documentation '''

    newHit = sampleComponent.sample.spectra[0].newSpectrumHit(substanceName=str(sampleComponent.substance.name))
    newHit.comment = 'NewUserHit'
    self.listOfHits.append(newHit)
    self.pullDownHit.setEnabled(False)
    self.updateHitTable()
    self.moveNextRow()

  def cancelPullDownSelection(self):
    ''' Documentation '''

    self.showDeleteButton()
    self.showAllOnTableSelection()


  def clearDisplayView(self):
    ''' Documentation '''

    # currentDisplayed = self.project.getByPid('GD:user.View.1D:H')
    currentDisplayed = self.project.strips[0]
    for spectrumView in currentDisplayed.spectrumViews:
      spectrumView.delete()
    self.project._appBase.mainWindow.clearMarks()
    return currentDisplayed

  def clearListWidget(self):
    ''' Documentation '''

    self.listWidgetsHitDetails.clear()

  def commitMoveNextRow(self):
    ''' Documentation '''

    self.acceptAssignment()
    self.moveNextRow()

  def commitMovePreviousRow(self):
    ''' Documentation '''

    self.acceptAssignment()
    self.movePreviousRow()

  def createDummyHits(self):
    ''' Testing only '''


    self.samples = self.project.samples
    for sample in self.project.samples:
      self.substance = sample.sampleComponents[0].substance
      self.hit = sample.spectra[0].newSpectrumHit(substanceName=str(self.substance.name))
      self.hit.comment = 'No'
    # return self.project.spectrumHits

  def deleteHit(self):
    ''' Deletes hit from project and from the table. If is last cleans all graphics
    '''
    hitToDelete = self.pullDownHit.getObject()
    hitToDelete.delete()
    if hitToDelete in self.listOfHits:
      self.listOfHits.remove(hitToDelete)
    self.moveNextRow()
    self.updateHitTable()
    if len(self.listOfHits)<=0:
      self.clearDisplayView()
      self.pullDownHit.setData([])

  def displayAllSampleComponents(self):
    ''' Documentation '''

    sampleComponentSpectra = [sc.substance.referenceSpectra[0] for sc in self.pullDownHit.currentObject().sample.sampleComponents]
    for spectrum in sampleComponentSpectra:
      spectrum.scale = float(0.5)
      # self.project.getByPid('GD:user.View.1D:H').displaySpectrum(spectrum)
      self.project.strips[0].displaySpectrum(spectrum)

  def displaySampleAndHit(self):
    ''' Documentation '''

    currentDisplay = self.clearDisplayView()
    for spectrum in self.spectraToDisplay():
      currentDisplay.displaySpectrum(spectrum)
      # currentDisplay.showPeaks(spectrum.peakList)
    # self.project.strips[0].viewBox.autoRange()

  def displaySelectedComponent(self):
    ''' Documentation '''

    currentDisplayed = self.project.strips[0]._parent
    for spectrumView in currentDisplayed.spectrumViews:
      if spectrumView.spectrum in self.spectraToDisplay():
        currentDisplayed.spectrumActionDict[spectrumView.spectrum._apiDataSource].setChecked(True)
      else:
        currentDisplayed.spectrumActionDict[spectrumView.spectrum._apiDataSource].setChecked(False)
    self.showHitInfoOnDisplay()


  def getPositionOnSpectrum(self):
    ''' Documentation '''
    peaks = self.getPullDownObj().substance.referenceSpectra[0].peakLists[1].peaks
    positions = [peak.position for peak in peaks]
    return set(list(positions))


  def getPullDownObj(self):
    ''' Documentation '''

    currentObjPulldown = self.pullDownHit.currentObject()
    if hasattr(currentObjPulldown, 'substanceName'):
      substance = self.project.getByPid('SU:'+currentObjPulldown.substanceName+'.H')
      return substance.sampleComponents[0]
    else:
      sampleComponent = currentObjPulldown
      return sampleComponent


  def getSampleInfoToDisplay(self):
    ''' Documentation '''

    sample = self.getPullDownObj().sample
    sampleInfo = {'Name':sample.name,
                  'Amount':sample.amount,
                  'CreationDate':sample.creationDate,
                  'PlateIdentifier':sample.plateIdentifier,
                  'RowNumber':sample.rowNumber,
                  'ColumnNumber':sample.columnNumber,
                  'Comment':sample.comment,}
    return sampleInfo


  def getSubstanceInfoToDisplay(self):
    ''' Documentation '''

    sampleComponent = self.getPullDownObj()
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


  def getSpectrumHitInfoToDisplay(self):
    ''' Documentation '''

    if len(self.getPullDownObj().spectrumHits)>0:
      hit = self.getPullDownObj().spectrumHits[0]
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


  def getSelectedSample(self):
    ''' Documentation '''

    return self.getPullDownObj().sample


  def hideDeleteButton(self):
    ''' Documentation '''

    self.showDeleteHitButtons.hide()
    self.addHitButton.show()


  def hitTableCallback(self, row:int=None, col:int=None, obj:object=None):
    ''' Documentation '''

    peaks = self.getPullDownObj().substance.referenceSpectra[0].peakLists[1].peaks
    # displayed = self.project.getByPid('GD:user.View.1D:H')
    displayed = self.project.strips[0]._parent
    for peak in peaks:
      navigateToPeakPosition(self.project, peak=peak, selectedDisplays=[displayed.pid], markPositions=True)


  def moveNextRow(self):
    ''' Documentation '''

    self.currentRowPosition = self.hitTable.getSelectedRows()
    newPosition = self.currentRowPosition[0]+1
    self.hitTable.selectRow(newPosition)
    lastRow = len(self.project.spectrumHits)
    if newPosition == lastRow:
     self.hitTable.selectRow(0)


  def movePreviousRow(self):
    ''' Documentation '''

    self.currentRowPosition = self.hitTable.getSelectedRows()
    newPosition = self.currentRowPosition[0]-1
    lastRow = len(self.project.spectrumHits)-1
    if newPosition == -1:
      self.hitTable.selectRow(lastRow)
    else:
      self.hitTable.selectRow(newPosition)


  def populateInfoList(self, name, value):
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


  def rejectAssignment(self):
    ''' Documentation '''

    rejectedHit = self.pullDownHit.getObject()
    rejectedHit.comment = 'No'
    self.updateHitTable()

  def showAllOnTableSelection(self, row:int=None, col:int=None, obj:object=None):
    ''' Documentation '''

    objRow = self.hitTable.getCurrentObject()
    self.showHitOnPullDown(objRow)
    self.displaySampleAndHit()
    self.showHitInfoOnDisplay()
    self.hidePeakList()

  def showHitInfoOnDisplay(self):
    ''' Documentation '''
    self.clearListWidget()
    self.showMolecule()
    self.showTextHitDetails()

  def showAllSampleComponentsOnPullDownHit(self):
    ''' Documentation '''

    self.pullDownHit.setEnabled(True)
    self.sampleComponents = [x for x in self.pullDownHit.getObject().sample.sampleComponents]
    self.substances = [ substance.name for substance in self.sampleComponents]
    self.pullDownHit.setData(self.substances, self.sampleComponents)#Name,Obj
    self.pullDownHit.activated[str].connect(self.displaySelectedComponent)
    self.displayAllSampleComponents()
    self.hideDeleteButton()

  def showTextHitDetails(self):
    ''' Documentation '''

    color = QtGui.QColor('Red')
    ''' setSpectrum Hit '''
    headerHit =  QtGui.QListWidgetItem('\nSpectrum Hit Details')
    headerHit.setFlags(QtCore.Qt.NoItemFlags)
    headerHit.setTextColor(color)
    self.listWidgetsHitDetails.addItem(headerHit)
    for name, value in self.getSpectrumHitInfoToDisplay().items():
      self.populateInfoList( name, value)

    ''' setHitPositions '''
    headerHitPositions =  QtGui.QListWidgetItem('\nChanged Peak Position At Ppm ')
    headerHitPositions.setFlags(QtCore.Qt.NoItemFlags)
    headerHitPositions.setTextColor(color)
    self.listWidgetsHitDetails.addItem(headerHitPositions)
    for item in self.getPositionOnSpectrum():
      self.listWidgetsHitDetails.addItem(str(item[0]))

    ''' setSubstance '''
    headerSubstance =  QtGui.QListWidgetItem('\nSubstance Details')
    headerSubstance.setFlags(QtCore.Qt.NoItemFlags)
    headerSubstance.setTextColor(color)
    self.listWidgetsHitDetails.addItem(headerSubstance)
    for name, value in self.getSubstanceInfoToDisplay().items():
      self.populateInfoList( name, value)

    ''' setSample '''
    headerSample =  QtGui.QListWidgetItem('\nSample Details')
    headerSample.setFlags(QtCore.Qt.NoItemFlags)
    headerSample.setTextColor(color)
    self.listWidgetsHitDetails.addItem(headerSample)
    for name, value in self.getSampleInfoToDisplay().items():
      self.populateInfoList( name, value)

  def showMolecule(self):
    ''' Documentation '''
    substance = self.getPullDownObj().substance
    self.smiles = substance.smiles
    if self.smiles is not None:
      self.compoundView  = CompoundView(self, smiles=self.smiles)
      self.hitDetailsGroupLayout.addWidget(self.compoundView, 1,1)
      self.compoundView.centerView()
      self.compoundView.resetView()
      self.compoundView.updateAll()

  def showDeleteButton(self):
    ''' Documentation '''

    self.showDeleteHitButtons.show()
    self.addHitButton.hide()

  def showHitOnPullDown(self, hit):
    ''' Documentation '''

    self.pullDownHit.setData([hit.substanceName], [hit])#Name,Obj
    self.pullDownHit.setEnabled(False)

  def spectraToDisplay(self):
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

  def testEditor(self,hit, value):
    ''' Documentation '''
    hit.comment = value

  def scoreEdit(self,hit, value):
    ''' Documentation '''
    hit.meritCode = value

  def updateHitTable(self):
    ''' Documentation '''
    self.hitTable.setObjects(self.listOfHits)

  def hidePeakList(self):
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