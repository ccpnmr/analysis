__author__ = 'luca'

from PyQt4 import QtGui, QtCore
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.DateTime import DateTime
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.widgets.CompoundView import CompoundView, Variant, importSmiles

SPECTRA = ['1H', 'STD', 'Relaxation Filtered', 'Water LOGSY']
OTHER_UNIT = ['µ','m', 'n', 'p']
CONCENTRATION_UNIT = ['µM', 'mM', 'nM', 'pM']
VOLUME_UNIT = ['µL', 'mL', 'nL', 'pL']
MASS_UNIT = ['µg','kg','g','mg', 'ng', 'pg']
SAMPLE_STATES = ['Liquid', 'Solid', 'Ordered', 'Powder', 'Crystal', 'Other']
TYPECOMPONENT =  ['Compound', 'Solvent', 'Target', 'inhibitor ', 'Other']
C_COMPONENT_UNIT = ['Molar', 'Mass/Volume',  'mol/Volume', ]

class SamplePropertiesPopup(QtGui.QDialog, Base):
  ''' This popup will allow to view and edit the sample properties '''

  def __init__(self, sample, parent=None, project=None, **kw):
    super(SamplePropertiesPopup, self).__init__(parent)
    Base.__init__(self, **kw)
    self.project = project
    if len(self.project.windows)>0:
      self.mainWindow = self.project.windows[0]
    # if self._appBase.ui.mainWindow is not None:
    #   mainWindow = self._appBase.ui.mainWindow
    # else:
    #   mainWindow = self._appBase._mainWindow
    self.sideBar = self.mainWindow.sideBar
    # self.newSampleSideBar = item

    self.sample = sample
    self.setWindowTitle("Sample Properties")
    self.area = ScrollArea(self)
    self.area.setWidgetResizable(True)
    self.area.setMinimumSize(450, 650)
    self.areaContents = QtGui.QWidget()

    self.area.setStyleSheet(""" background-color:  #2a3358; """)
    self.area.setWidget(self.areaContents)
    self.layout().addWidget(self.area, 0, 0, 1, 0)
    buttonBox = ButtonList(self, grid=(2, 2), callbacks=[self.reject, self.accept], texts=['Cancel', 'Apply'])
    self.setMaximumSize(450, 650)

    # Widgets Properties:
    # SampleName
    sampleNameLabel = Label(self.areaContents, text="Sample name ", grid=(1, 1), hAlign='l')
    self.sampleName = LineEdit(self.areaContents, grid=(1, 2), hAlign='l' )
    self.sampleName.setStyleSheet(""" background-color:  white""")
    self.sampleName.setFixedWidth(203)
    self.sampleName.setFixedHeight(25)
    self.sampleName.setText(sample.name)
    self.sampleName.editingFinished.connect(self._changeSampleName)

#   # Sample Components
    SampleComponents = Label(self.areaContents, text="Sample Components ", grid=(2, 1), hAlign='l')
    self.scpid = []
    sc = [sc.pid for sc in sample.sampleComponents]
    self.scpid.append(sc)
    self.sc = PulldownList(self.areaContents, grid=(2, 2), hAlign='l' )
    self.sc.setStyleSheet(""" background-color:  white""")
    self.sc.setFixedWidth(203)
    self.sc.setFixedHeight(25)
    self.sc.setData(self.scpid[0])
    self.sc.setEditable(True)
    self.sc.activated[str].connect(self._editComponents)

#   # Add component
    self.sampleAddComponents = Button(self.areaContents, text="Add Sample Components ", grid=(13, 1),
                                      hAlign='l', callback=self._addComponents)
    self.sampleAddComponents.setStyleSheet(""" background-color:  white""")
    self.sampleAddComponents.setFixedWidth(195)
    self.sampleAddComponents.setFixedHeight(25)

#   #Sample Spectra
    sampleSpectra = Label(self.areaContents, text="Sample Spectra ", vAlign='t', hAlign='l', grid=(3, 1))
    self.sampleExperimentType = PulldownList(self.areaContents, hAlign='l', grid=(3, 2))#, vAlign='t'
    spPid = [sp.pid for sp in sample.spectra]
    self.sampleExperimentType.addItems(spPid)
    self.sampleExperimentType.setStyleSheet(""" background-color:  white""")
    self.sampleExperimentType.setFixedWidth(203)
    self.sampleExperimentType.setFixedHeight(25)

# #   #Sample Spectrum  Hit
#     spectrumHit = Label(self.areaContents, text="Spectrum Hits ", vAlign='t', hAlign='l', grid=(4, 1))
#     self.spectrumHit = PulldownList(self.areaContents, hAlign='l', grid=(4, 2))#, vAlign='t'
#     self.spectrumHit.addItems(spPid)
#     self.spectrumHit.setStyleSheet(""" background-color:  white""")
#     self.spectrumHit.setFixedWidth(203)
#     self.spectrumHit.setFixedHeight(25)

#   #Sample  State
    sampleState = Label(self.areaContents, text="Sample State ", vAlign='t', hAlign='l', grid=(5, 1))
    self.sampleState = PulldownList(self.areaContents, hAlign='l', grid=(5, 2))#, vAlign='t'
    self.sampleState.addItems(SAMPLE_STATES)
    self.sampleState.setStyleSheet(""" background-color:  white""")
    self.sampleState.setFixedWidth(203)
    self.sampleState.setFixedHeight(25)
    self.sampleState.activated[str].connect(self._sampleStateChanged)

#   #Sample Amount Unit
    sampleAmountUnitLabel = Label(self.areaContents, text="Sample Amount ", grid=(6, 1), hAlign='l')
    self.sampleAmountUnit = PulldownList(self.areaContents, grid=(6, 2), hAlign='l' )
    self.sampleAmountUnit.setData(CONCENTRATION_UNIT)
    self.sampleAmountUnit.setFixedWidth(75)
    self.sampleAmountUnit.setFixedHeight(25)
    self.sampleAmountUnit.setStyleSheet(""" background-color:  white""")
    self.sampleAmountUnit.activated[str].connect(self._sampleAmountUnitChanged)

#    # Sample Amount
    self.sampleAmount = DoubleSpinbox(self.areaContents, grid=(6, 2), hAlign='r' )
    self.sampleAmount.setRange(0.00, 1000.00)
    self.sampleAmount.setSingleStep(0.01)
    self.sampleAmount.setStyleSheet(""" background-color:  white""")
    self.sampleAmount.setFixedWidth(120)
    self.sampleAmount.setFixedHeight(25)
    if self.sample.amount is not None:
      self.sampleAmount.setValue(self.sample.amount)
    self.sampleAmount.valueChanged.connect(self._sampleAmountChanged)

#    # Sample pH
    samplepHLabel = Label(self.areaContents, text="Sample pH ", grid=(7, 1), hAlign='l')
    self.samplepH = DoubleSpinbox(self.areaContents, grid=(7, 2), hAlign='l' )
    self.samplepH.setRange(0.00, 14.00)
    self.samplepH.setSingleStep(0.01)
    self.samplepH.valueChanged.connect(self._samplepHchanged)
    self.samplepH.setStyleSheet(""" background-color:  white""")
    self.samplepH.setFixedWidth(203)
    self.samplepH.setFixedHeight(25)
    if self.sample.pH is not None:
      self.samplepH.setValue(self.sample.pH)

#    # Sample Date
    sampleDate = Label(self.areaContents, text="Sample Creation Date ", grid=(8, 1), hAlign='l')
    self.sampleDate = DateTime(self.areaContents, grid=(8, 2), hAlign='l')
    self.sampleDate.setStyleSheet(""" background-color:  white""")
    self.sampleDate.setFixedWidth(203)
    self.sampleDate.setFixedHeight(25)
    if sample.creationDate is None:
      setToday = QtCore.QDate.currentDate()
      self.sampleDate.setDate(setToday)
      self.sampleDate.dateChanged.connect(self._sampleDateChanged)

#    # Sample Plate Identifier
    samplePlateIdentifierLabel = Label(self.areaContents, text="Sample Plate Identifier ", grid=(9, 1), hAlign='l')
    self.plateIdentifier = LineEdit(self.areaContents, grid=(9, 2), hAlign='l' )
    self.plateIdentifier.setStyleSheet(""" background-color:  white""")
    self.plateIdentifier.setFixedWidth(203)
    self.plateIdentifier.setFixedHeight(25)
    self.plateIdentifier.setText(str(sample.plateIdentifier))
    self.plateIdentifier.editingFinished.connect(self._plateIdentifierChanged)

    # Sample Row Number
    samplerowNumberLabel = Label(self.areaContents, text="Sample Row Number ", grid=(10, 1), hAlign='l')
    self.rowNumber = LineEdit(self.areaContents, grid=(10, 2), hAlign='l' )
    self.rowNumber.setStyleSheet(""" background-color:  white""")
    self.rowNumber.setFixedWidth(203)
    self.rowNumber.setFixedHeight(25)
    if sample.rowNumber is not None:
      self.rowNumber.setText(str(sample.rowNumber))
    self.rowNumber.editingFinished.connect(self._rowNumberChanged)

#    # Sample Column Number
    sampleColumnNumberLabel = Label(self.areaContents, text="Sample Column Number ", grid=(11, 1), hAlign='l')
    self.columnNumber = LineEdit(self.areaContents, grid=(11, 2), hAlign='l' )
    self.columnNumber.setStyleSheet(""" background-color:  white""")
    self.columnNumber.setFixedWidth(203)
    self.columnNumber.setFixedHeight(25)
    if sample.columnNumber is not None:
      self.columnNumber.setText(str(sample.columnNumber))
    self.columnNumber.editingFinished.connect(self._columnNumberChanged)

#    # Sample Comment
    sampleCommentLabel = Label(self.areaContents, text="Comment ", grid=(12, 1), hAlign='l')
    self.comment = TextEditor(self.areaContents, grid=(12, 2), hAlign='c' )
    self.comment.setStyleSheet(""" background-color: white""")
    self.comment.setFixedWidth(207)
    self.comment.setFixedHeight(50)
    self.comment.setText(sample.comment)
    self.comment.textChanged.connect(self._commentChanged)

    # Only to align and center all nicely
    labelAllignLeft = Label(self.areaContents, text="", grid=(1, 0), hAlign='l')
    labelAllignRight = Label(self.areaContents, text="", grid=(1, 3), hAlign='l')

  def _addComponents(self):
    ''' This adds components to the sample, to the sideBar and pulldown '''

    self.sampleComponent = self.sample.newSampleComponent(name=('NewSC'),labeling=str('H'))
    # self.sideBar.addItem(self.newSampleSideBar, self.sampleComponent)
    scPid = self.sampleComponent.pid
    self.scpid[0].append(scPid)
    self.sc.setData(self.scpid[0])
    self._editComponents(self.sampleComponent.pid)


  def _editComponents(self, pressed):
    ''' This opens the sample component editor '''

    sampleComponent = self.project.getByPid(pressed)
    popup = EditSampleComponentPopup(project=self.project, sample=self.sample, sampleComponent=sampleComponent)
    popup.exec_()
    popup.raise_()

  def _changeSampleName(self):

    if self.sampleName.isModified():
      self.sample.rename(self.sampleName.text())
      self.item.setText(0, 'SA:'+self.sampleName.text())
      for i in range(self.item.childCount()):
        pid = self.item.child(i).text(0).split(':')[0]+':'+self.sampleName.text()+"."\
              + self.item.child(i).text(0).split('.')[1]
        self.item.child(i).setText(0, pid)

  def _samplepHchanged(self, value):
    self.sample.pH = value

  def _sampleStateChanged(self, pressed):

    if pressed == 'Liquid':
      self._sampleUnitChangedInVolume()
    elif pressed == 'Other':
      self._sampleUnitChangedInConcentration()
    else:
      self._sampleUnitChangedInMass()

  def _sampleUnitChangedInVolume(self):
    self.sampleAmountUnit.setData(VOLUME_UNIT)

  def _sampleUnitChangedInConcentration(self):
    self.sampleAmountUnit.setData(CONCENTRATION_UNIT)

  def _sampleUnitChangedInMass(self):
    self.sampleAmountUnit.setData(MASS_UNIT)

  def _sampleAmountChanged(self, value):
    self.sample.amount = value

  def _sampleAmountUnitChanged(self, pressed):
    self.sample.amountUnit = str(pressed)

  def _sampleDateChanged(self, pressed):
    print(pressed)

  def _plateIdentifierChanged(self):
    self.sample.plateIdentifier = str(self.plateIdentifier.text())

  def _rowNumberChanged(self):
    self.sample.rowNumber = int(self.rowNumber.text())

  def _columnNumberChanged(self):
    self.sample.columnNumber = int(self.columnNumber.text())

  def _commentChanged(self):
    newText = self.comment.toPlainText()
    self.sample.comment = newText

  def _keyPressEvent(self, event):
    if event.key() == QtCore.Qt.Key_Enter:
      pass



class EditSampleComponentPopup(QtGui.QDialog):
  ''' This popup will allow to view and edit the sample Component properties

  '''

  def __init__(self, parent=None, project=None, sample=None, sampleComponent=None, **kw):

    super(EditSampleComponentPopup, self).__init__(parent, **kw)
    self.sample = sample
    self.sampleComponent = sampleComponent
    self.project = project
    self.sampleProperitesPopup =  SamplePropertiesPopup
    self.setWindowTitle("Sample Components Properties")
    self.area = ScrollArea(self)
    self.area.setWidgetResizable(True)
    self.area.setMinimumSize(350, 499)
    self.layout().addWidget(self.area, 0, 0, 1, 0)
    self.smiles = ''
    self.compound = None
    self.variant = None



    buttonBox = ButtonList(self, grid=(2, 2), callbacks=[self.accept, self.reject], texts=['Apply', 'Close'])
    labelAllignLeft = Label(self.area, text="", grid=(1, 0), hAlign='l')
    labelAllignRight = Label(self.area, text="", grid=(1, 3), hAlign='l')
    self.setMaximumSize(350, 700)

#   #Component Type
    typeLabel = Label(self.area, text="Type ", grid=(1, 1), hAlign='l')
    self.type = PulldownList(self.area, grid=(1, 2), hAlign='l' )
    self.type.setData(TYPECOMPONENT)
    self.type.setFixedWidth(129)
    self.type.activated[str].connect(self._typeComponent)

#   #Component Name
    sampleComponentsLabel = Label(self.area, text="Component Name ", grid=(2, 1), hAlign='l')
    self.nameComponents = LineEdit(self.area, grid=(2, 2), hAlign='r' )
    self.nameComponents.setText(sampleComponent.name)
    self.nameComponents.editingFinished.connect(self._changeNameComponents)

#   #Labeling
    sampleComponentsLabelingLabel = Label(self.area, text="Labeling ", grid=(3, 1), hAlign='l')
    self.labeling = LineEdit(self.area, grid=(3, 2), hAlign='r' )
    self.labeling.setText(sampleComponent.labeling)
    self.labeling.editingFinished.connect(self._labelingChanged)

#   #concentration unit
    concentrationUnitLabel = Label(self.area, text="Value Unit ", grid=(4, 1), hAlign='l')
    self.concentrationUnit = PulldownList(self.area, grid=(4, 2), hAlign='l' )
    self.concentrationUnit.setData(C_COMPONENT_UNIT)
    self.concentrationUnit.setFixedWidth(128)
    self.concentrationUnit.activated[str].connect(self._setConcentrationUnit)

#   #concentration Value 1
    concentrationLabel = Label(self.area, text="Value 1 ", grid=(5, 1), hAlign='l')
    self.concentrationUnit1 = PulldownList(self.area, grid=(5, 2), hAlign='l' )
    self.concentrationUnit1.setFixedWidth(65)
    self.concentration = DoubleSpinbox(self.area, grid=(5, 2), hAlign='r' )
    self.concentration.setRange(0.00, 1000.00)
    self.concentration.setSingleStep(0.01)
    self.concentration.setFixedWidth(65)
    self.concentration.setFixedHeight(20)
    self.concentration.valueChanged.connect(self._concentrationChanged)

#   #concentration Value 2
    self.concentrationLabel2 = Label(self.area, text="Value 2 ", grid=(6, 1), hAlign='l')
    self.concentrationUnit2 = PulldownList(self.area, grid=(6, 2), hAlign='l' )
    self.concentrationUnit2.setFixedWidth(65)
    self.concentration2 = DoubleSpinbox(self.area, grid=(6, 2), hAlign='r' )
    self.concentration2.setRange(0.00, 1000.00)
    self.concentration2.setSingleStep(0.01)
    self.concentration2.setFixedWidth(65)
    self.concentration2.setFixedHeight(20)
    self.concentrationUnit2.hide()
    self.concentrationLabel2.hide()
    self.concentration2.hide()
    self.concentration2.valueChanged.connect(self._concentration2Changed)

#   # referenceSpectra
    referenceSpectraLabel = Label(self.area, text="Ref Spectra", grid=(7, 1), hAlign='l')
    self.referenceSpectra = PulldownList(self.area, grid=(7, 2), hAlign='l' )
    for referenceSpectra in sampleComponent.substance.referenceSpectra:
      self.referenceSpectra.setData([referenceSpectra.pid])
    self.referenceSpectra.setFixedWidth(133)

#   # chemical Name
    chemicalNameLabel = Label(self.area, text="Chemical Name", grid=(8, 1), hAlign='l')
    self.chemicalName = LineEdit(self.area, grid=(8, 2), hAlign='l' )
    self.chemicalName.editingFinished.connect(self._chemicalNameChanged)
    # To clearify on the wrapper first

#   # smiles
    self.smileLabel = Label(self.area, text="Smiles", grid=(9, 1), hAlign='l')
    self.smile = LineEdit(self.area, grid=(9, 2), hAlign='r')
    self.smile.setText(sampleComponent.substance.smiles)
    self.smile.editingFinished.connect(self._smileChanged)

#   # empirical Formula
    self.empiricalFormulaLabel = Label(self.area, text="Empirical Formula", grid=(10, 1), hAlign='l')
    self.empiricalFormula = LineEdit(self.area, grid=(10, 2), hAlign='r' )
    self.empiricalFormula.setText(str(sampleComponent.substance.empiricalFormula))
    self.empiricalFormula.editingFinished.connect(self._empiricalFormulaChanged)

#   # Molecular Mass
    self.molecularMassLabel = Label(self.area, text="Molecular Mass", grid=(11, 1), hAlign='l')
    self.molecularMass = LineEdit(self.area, grid=(11, 2), hAlign='r' )
    self.molecularMass.setText(str(sampleComponent.substance.molecularMass))
    self.molecularMass.editingFinished.connect(self._molecularMassChanged)

#   # Comment
    self.labelcomment = Label(self.area, text="Comment", grid=(12, 1), hAlign='l')
    self.comment = LineEdit(self.area, grid=(12, 2), hAlign='r' )
    self.comment.setText(self.sampleComponent.substance.comment)
    self.comment.editingFinished.connect(self._commentChanged)

    self.moreInfo = Button(self.area, text="More... ", grid=(13, 1),
                           hAlign='c', callback=self._moreInfoComponents)
    self.moreInfo.setFixedHeight(20)
    self.showSmiles = Button(self.area, text="Display Compound", grid=(13, 2),
                             hAlign='c', callback=self._showCompound)
    self.hideSmiles = Button(self.area, text="Hide Compound", grid=(13, 2),
                                      hAlign='c', callback=None)
    self.hideSmiles.hide()
#   # User Code
    self.labelUserCode = Label(self.area, text="User Code", grid=(13, 1), hAlign='l')
    self.userCode = LineEdit(self.area, grid=(13, 2), hAlign='r' )
    self.userCode.setText(str(sampleComponent.substance.userCode))
    self.userCode.editingFinished.connect(self._userCodeChanged)
    self.labelUserCode.hide()
    self.userCode.hide()

#   # Cas Number
    self.labelCasNumber = Label(self.area, text="Cas Number", grid=(14, 1), hAlign='l')
    self.casNumber = LineEdit(self.area, grid=(14, 2), hAlign='r' )
    self.casNumber.setText(str(sampleComponent.substance.casNumber))
    self.casNumber.editingFinished.connect(self._casNumberChanged)
    self.labelCasNumber.hide()
    self.casNumber.hide()

#   # Atom Count
    self.labelAtomCount = Label(self.area, text="Atom Count", grid=(15, 1), hAlign='l')
    self.atomCount = LineEdit(self.area, grid=(15, 2), hAlign='r' )
    self.atomCount.setText(str(sampleComponent.substance.atomCount))
    self.atomCount.editingFinished.connect(self._atomCountChanged)
    self.labelAtomCount.hide()
    self.atomCount.hide()

#   # Bond Count
    self.labelBondCount = Label(self.area, text="Bond Count", grid=(16, 1), hAlign='l')
    self.bondCount = LineEdit(self.area, grid=(16, 2), hAlign='r' )
    self.bondCount.setText(str(sampleComponent.substance.bondCount))
    self.labelBondCount.hide()
    self.bondCount.hide()

#   # Ring Count
    self.labelRingCount = Label(self.area, text="Ring Count", grid=(17, 1), hAlign='l')
    self.ringCount = LineEdit(self.area, grid=(17, 2), hAlign='r' )
    self.ringCount.setText(str(sampleComponent.substance.ringCount))
    self.ringCount.editingFinished.connect(self._ringCountChanged)
    self.labelRingCount.hide()
    self.ringCount.hide()

#   # H Bond Donor
    self.labelHBondDonorCount = Label(self.area, text="H Bond Donors", grid=(18, 1), hAlign='l')
    self.hBondDonorCount = LineEdit(self.area, grid=(18, 2), hAlign='r' )
    self.hBondDonorCount.setText(str(sampleComponent.substance.hBondDonorCount))
    self.hBondDonorCount.editingFinished.connect(self._hBondDonorCountChanged)
    self.labelHBondDonorCount.hide()
    self.hBondDonorCount.hide()

#   # H Bond Acceptor
    self.labelHBondAcceptorCount = Label(self.area, text="H Bond Acceptors", grid=(19, 1), hAlign='l')
    self.hBondAcceptorCount = LineEdit(self.area, grid=(19, 2), hAlign='r' )
    self.hBondAcceptorCount.setText(str(sampleComponent.substance.hBondAcceptorCount))
    self.hBondAcceptorCount.editingFinished.connect(self._hBondAcceptorCountChanged)
    self.labelHBondAcceptorCount.hide()
    self.hBondAcceptorCount.hide()

#   # Polar Surface Area
    self.labelpolarSurfaceArea = Label(self.area, text="Polar Surface Area", grid=(20, 1), hAlign='l')
    self.polarSurfaceArea = LineEdit(self.area, grid=(20, 2), hAlign='r' )
    self.polarSurfaceArea.setText(str(sampleComponent.substance.polarSurfaceArea))
    self.polarSurfaceArea.editingFinished.connect(self._polarSurfaceAreaChanged)
    self.labelpolarSurfaceArea.hide()
    self.polarSurfaceArea.hide()

#   # LogP
    self.labelLogP = Label(self.area, text="LogP", grid=(21, 1), hAlign='l')
    self.logP = LineEdit(self.area, grid=(21, 2), hAlign='r' )
    self.logP.setText(str(sampleComponent.substance.logPartitionCoefficient))
    self.logP.editingFinished.connect(self._logPChanged)
    self.labelLogP.hide()
    self.logP.hide()

  def _moreInfoComponents(self):
    self.moreInfo.hide()
    self.showSmiles.hide()
    self.lessInfo = Button(self.area, text="Less... ", grid=(22, 1),
                           hAlign='c', callback=self._hideInfo)
    self.lessInfo.setFixedHeight(20)
    self.labelUserCode.show()
    self.userCode.show()
    self.labelCasNumber.show()
    self.casNumber.show()
    self.labelAtomCount.show()
    self.atomCount.show()
    self.labelBondCount.show()
    self.bondCount.show()
    self.labelRingCount.show()
    self.ringCount.show()
    self.labelHBondDonorCount.show()
    self.hBondDonorCount.show()
    self.labelHBondAcceptorCount.show()
    self.hBondAcceptorCount.show()
    self.labelpolarSurfaceArea.show()
    self.polarSurfaceArea.show()
    self.labelLogP.show()
    self.logP.show()

  def _setConcentrationUnit(self, pressed):
    if pressed == 'Molar':
      self.concentrationUnit1.setData(CONCENTRATION_UNIT)
      self.concentrationUnit2.hide()
      self.concentrationLabel2.hide()
      self.concentration2.hide()
    elif pressed == 'Mass/Volume':
      self.concentrationUnit1.setData(MASS_UNIT)
      self.concentrationUnit2.setData(VOLUME_UNIT)
      self.concentrationUnit2.show()
      self.concentrationLabel2.show()
      self.concentration2.show()
    elif pressed == 'mol/Volume':
      self.concentrationUnit1.setData(OTHER_UNIT)
      self.concentrationUnit2.setData(VOLUME_UNIT)
      self.concentrationUnit2.show()
      self.concentrationLabel2.show()
      self.concentration2.show()

  def _typeComponent(self, pressed):

    if pressed == 'Compound':
      self.moreInfo.show()
      self.smileLabel.show()
      self.smile.show()
      self.empiricalFormulaLabel.show()
      self.empiricalFormula.show()
      self.molecularMassLabel.show()
      self.molecularMass.show()
      self.showSmiles.show()

    else:
      self._hideInfo()
      if hasattr(self, 'moreInfo'):
        self.moreInfo.hide()
        self.showSmiles.hide()

  def _hideInfo(self):
      self.showSmiles.show()
      self.moreInfo.show()
      if hasattr(self, 'lessInfo'):
        self.lessInfo.hide()
      self.smileLabel.hide()
      self.smile.hide()
      self.empiricalFormulaLabel.hide()
      self.empiricalFormula.hide()
      self.molecularMassLabel.hide()
      self.molecularMass.hide()
      self.labelUserCode.hide()
      self.userCode.hide()
      self.labelCasNumber.hide()
      self.casNumber.hide()
      self.labelAtomCount.hide()
      self.atomCount.hide()
      self.labelBondCount.hide()
      self.bondCount.hide()
      self.labelRingCount.hide()
      self.ringCount.hide()
      self.labelHBondDonorCount.hide()
      self.hBondDonorCount.hide()
      self.labelHBondAcceptorCount.hide()
      self.hBondAcceptorCount.hide()
      self.labelpolarSurfaceArea.hide()
      self.polarSurfaceArea.hide()
      self.labelLogP.hide()
      self.logP.hide()

  def _changeNameComponents(self):
    print('Not implemented Yet')

  def _labelingChanged(self):
    # self.sampleComponent.labeling = str(self.labeling.text())
    print('labeling not Changed', self.sampleComponent.labeling )

  def _concentrationChanged(self, value):
    self.sampleComponent.concentration = float(value)

  def _concentration2Changed(self, value):
    print(value, 'concentration2 Not implemented Yet')

  def _chemicalNameChanged(self):
    print('Not implemented Yet')

  def _smileChanged(self):
    self.sampleComponent.substance.smiles = str(self.smile.text())

  def _empiricalFormulaChanged(self):
     self.sampleComponent.substance.empiricalFormula = str(self.empiricalFormula.text())

  def _molecularMassChanged(self):
    self.sampleComponent.substance.molecularMass = float(self.molecularMass.text())

  def _userCodeChanged(self):
    self.sampleComponent.substance.userCode = str(self.userCode.text())

  def _casNumberChanged(self):
    self.sampleComponent.substance.casNumber = str(self.casNumber.text())

  def _atomCountChanged(self):
    self.sampleComponent.substance.atomCount = int(self.atomCount.text())

  def _ringCountChanged(self):
    self.sampleComponent.substance.ringCount = int(self.ringCount.text())

  def _hBondDonorCountChanged(self):
    self.sampleComponent.substance.hBondDonorCount = int(self.hBondDonorCount.text())

  def _hBondAcceptorCountChanged(self):
    self.sampleComponent.substance.hBondAcceptorCount = int(self.hBondAcceptorCount.text())

  def _polarSurfaceAreaChanged(self):
    self.sampleComponent.substance.polarSurfaceArea = float(self.polarSurfaceArea.text())

  def _logPChanged(self):
    self.sampleComponent.substance.logPartitionCoefficient = float(self.logP.text())

  def _commentChanged(self):
    self.sampleComponent.substance.comment = str(self.comment.text())


  def _showCompound(self):
    self.moreInfo.hide()
    self.showSmiles.hide()
    self.hideSmiles.show()

    smiles = self.sampleComponent.substance.smiles
    self.compoundView = CompoundView(self.area, smiles=smiles, grid=(14, 1) , gridSpan=(14,2),
                                     preferences=self.project._appBase.preferences.general)


    self.compoundView.centerView()
    # self.compoundView.resetView()
    self.compoundView.updateAll()

