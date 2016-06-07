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



class SamplePropertiesPopup(QtGui.QDialog):

  def __init__(self, sample, parent=None, project=None, **kw):
    super(SamplePropertiesPopup, self).__init__(parent)
    self.project = project
    self.sample = sample
    self._getInfoFromProject()
    self._setMainLayout()
    self._setWidgets()

  def _getInfoFromProject(self):

    if len(self.project.windows) > 0:
      self.mainWindow = self.project.windows[0]
    self.framework = self.mainWindow.framework
    self.generalPreferences = self.framework.preferences.general
    self.colourScheme = self.generalPreferences.colourScheme

  def _setMainLayout(self):
    self.mainLayout = QtGui.QGridLayout()
    self.setLayout(self.mainLayout)
    self.setWindowTitle("Sample Properties")
    self.resize(350, 350)

  def _setWidgets(self):
    setWidgets = (self._setSampleNameWidgets,
                  self._setSampleComponentsWidgets,
                  self._setSampleSpectraWidgets,
                  self._setsampleStateWidgets,
                  self._setsampleAmountUnitWidgets,
                  self._setsampleAmountWidgets,
                  self._setSample_pHWidgets,
                  self._setSampleDateWidgets,
                  self._setPlateIdentifierWidgets,
                  self._setSampleRowNumberWidgets,
                  self._setSampleColumnNumberWidgets,
                  self._setSampleCommentWidgets,
                  self._setPerformButtonWidgets
                  )
    for setWidget in setWidgets:
      setWidget()


  def _setSampleNameWidgets(self):
    self.sampleNameLabel = Label(self, text="Sample name ")
    self.sampleName = LineEdit(self)
    self.sampleName.setFixedWidth(203)
    self.sampleName.setFixedHeight(25)
    self.sampleName.setText(self.sample.name)
    self.sampleName.editingFinished.connect(self._changeSampleName)
    self.mainLayout.addWidget(self.sampleNameLabel, 0, 0)
    self.mainLayout.addWidget(self.sampleName, 0, 1)



  def _setSampleComponentsWidgets(self):
    SampleComponents = Label(self, text="Sample Components ")
    self.scpid = [['New'],]
    sc = [sc.pid for sc in self.sample.sampleComponents]
    self.scpid.append(sc)


    self.scPulldownList = PulldownList(self)
    self.scPulldownList.setFixedWidth(203)
    self.scPulldownList.setFixedHeight(25)
    self.scPulldownList.setData(self.scpid[0])
    self.scPulldownList.setEditable(True)
    self.scPulldownList.activated[str].connect(self._editComponents)
    self.mainLayout.addWidget(SampleComponents, 1, 0)
    self.mainLayout.addWidget(self.scPulldownList, 1, 1)

  def _setSampleSpectraWidgets(self):
    sampleSpectra = Label(self, text="Sample Spectra ")
    self.sampleExperimentType = PulldownList(self)
    spPid = [sp.pid for sp in self.sample.spectra]
    self.sampleExperimentType.addItems(spPid)
    self.sampleExperimentType.setFixedWidth(203)
    self.sampleExperimentType.setFixedHeight(25)
    self.mainLayout.addWidget(sampleSpectra, 2, 0)
    self.mainLayout.addWidget(self.sampleExperimentType, 2, 1)

  def _setsampleStateWidgets(self):
    sampleState = Label(self, text="Sample State ")
    self.sampleState = PulldownList(self)
    self.sampleState.addItems(SAMPLE_STATES)
    self.sampleState.setFixedWidth(203)
    self.sampleState.setFixedHeight(25)
    self.sampleState.activated[str].connect(self._sampleStateChanged)
    self.mainLayout.addWidget(sampleState, 3, 0)
    self.mainLayout.addWidget(self.sampleState, 3, 1)

  def _setsampleAmountUnitWidgets(self):
    sampleAmountUnitLabel = Label(self, text="Sample Amount ")
    self.sampleAmountUnit = PulldownList(self)
    self.sampleAmountUnit.setData(CONCENTRATION_UNIT)
    self.sampleAmountUnit.setFixedWidth(203)
    self.sampleAmountUnit.setFixedHeight(25)
    self.sampleAmountUnit.activated[str].connect(self._sampleAmountUnitChanged)
    self.mainLayout.addWidget(sampleAmountUnitLabel, 4, 0)
    self.mainLayout.addWidget(self.sampleAmountUnit, 4, 1)

  def _setsampleAmountWidgets(self):
    self.sampleAmount = DoubleSpinbox(self)
    self.sampleAmount.setRange(0.00, 1000.00)
    self.sampleAmount.setSingleStep(0.01)
    self.sampleAmount.setFixedWidth(203)
    self.sampleAmount.setFixedHeight(25)
    if self.sample.amount is not None:
      self.sampleAmount.setValue(self.sample.amount)
    self.sampleAmount.valueChanged.connect(self._sampleAmountChanged)
    self.mainLayout.addWidget(self.sampleAmount, 5, 1)

  def _setSample_pHWidgets(self):
    samplepHLabel = Label(self, text="Sample pH ")
    self.samplepH = DoubleSpinbox(self)
    self.samplepH.setRange(0.00, 14.00)
    self.samplepH.setSingleStep(0.01)
    self.samplepH.valueChanged.connect(self._samplepHchanged)
    self.samplepH.setFixedWidth(203)
    self.samplepH.setFixedHeight(25)
    if self.sample.pH is not None:
      self.samplepH.setValue(self.sample.pH)
    self.mainLayout.addWidget(samplepHLabel, 6, 0)
    self.mainLayout.addWidget(self.samplepH, 6, 1)

  def _setSampleDateWidgets(self):
    sampleDate = Label(self, text="Sample Creation Date ")
    self.sampleDate = DateTime(self)
    # self.sampleDate.setStyleSheet(""" background-color:  white""")
    self.sampleDate.setFixedWidth(203)
    self.sampleDate.setFixedHeight(25)
    if self.sample.creationDate is None:
      setToday = QtCore.QDate.currentDate()
      self.sampleDate.setDate(setToday)
      self.sampleDate.dateChanged.connect(self._sampleDateChanged)
    self.mainLayout.addWidget(sampleDate, 7, 0)
    self.mainLayout.addWidget(self.sampleDate, 7, 1)

  def _setPlateIdentifierWidgets(self):
    samplePlateIdentifierLabel = Label(self, text="Sample Plate Identifier ")
    self.plateIdentifier = LineEdit(self)
    self.plateIdentifier.setFixedWidth(203)
    self.plateIdentifier.setFixedHeight(25)
    self.plateIdentifier.setText(str(self.sample.plateIdentifier))
    self.plateIdentifier.editingFinished.connect(self._plateIdentifierChanged)
    self.mainLayout.addWidget(samplePlateIdentifierLabel, 8, 0)
    self.mainLayout.addWidget(self.plateIdentifier, 8, 1)

  def _setSampleRowNumberWidgets(self):
    samplerowNumberLabel = Label(self, text="Sample Row Number ")
    self.rowNumber = LineEdit(self)
    self.rowNumber.setFixedWidth(203)
    self.rowNumber.setFixedHeight(25)
    if self.sample.rowNumber is not None:
      self.rowNumber.setText(str(self.sample.rowNumber))
    self.rowNumber.editingFinished.connect(self._rowNumberChanged)
    self.mainLayout.addWidget(samplerowNumberLabel, 9, 0)
    self.mainLayout.addWidget(self.rowNumber, 9, 1)

  def _setSampleColumnNumberWidgets(self):
    sampleColumnNumberLabel = Label(self, text="Sample Column Number ")
    self.columnNumber = LineEdit(self)
    self.columnNumber.setFixedWidth(203)
    self.columnNumber.setFixedHeight(25)
    if self.sample.columnNumber is not None:
      self.columnNumber.setText(str(self.sample.columnNumber))
    self.columnNumber.editingFinished.connect(self._columnNumberChanged)
    self.mainLayout.addWidget(sampleColumnNumberLabel, 10, 0)
    self.mainLayout.addWidget(self.columnNumber, 10, 1)

  def _setSampleCommentWidgets(self):
    sampleCommentLabel = Label(self, text="Comment ")
    self.comment = TextEditor(self)
    # self.comment.setStyleSheet(""" background-color: white""")
    self.comment.setFixedWidth(205)
    self.comment.setFixedHeight(50)
    self.comment.setText(self.sample.comment)
    self.comment.textChanged.connect(self._commentChanged)
    self.mainLayout.addWidget(sampleCommentLabel, 11, 0)
    self.mainLayout.addWidget(self.comment, 11, 1)


  def _setPerformButtonWidgets(self):
    self.buttonBox = ButtonList(self, callbacks=[self.reject, self.accept], texts=['Cancel', 'Apply'])
    self.mainLayout.addWidget(self.buttonBox, 12, 1, 12,1)

  ######### Callbacks

  def _changeSampleName(self):

    if self.sampleName.isModified():
      self.sample.rename(self.sampleName.text())
      self.item.setText(0, 'SA:' + self.sampleName.text())
      for i in range(self.item.childCount()):
        pid = self.item.child(i).text(0).split(':')[0] + ':' + self.sampleName.text() + "." \
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

  def _editComponents(self, pressed):
    ''' This opens the sample component editor '''
    if pressed == 'New':
      EditSampleComponentPopup(project=self.project, sample=self.sample).exec()
    else:
      sampleComponent = self.project.getByPid(pressed)
      EditSampleComponentPopup(project=self.project, sample=self.sample, sampleComponent=sampleComponent).exec()


class EditSampleComponentPopup(QtGui.QDialog):

  def __init__(self, parent=None, project=None, sample=None, sampleComponent=None, **kw):
    super(EditSampleComponentPopup, self).__init__(parent)
    self.project = project
    self.sample = sample
    if sampleComponent is None:
      self.sampleComponent = self._getSampleComponent()
    else:
      self.sampleComponent = sampleComponent
    self._setMainLayout()
    self._setWidgets()


  def _setMainLayout(self):
    self.mainLayout = QtGui.QGridLayout()
    self.setLayout(self.mainLayout)
    self.setWindowTitle("Sample Components Properties")
    self.resize(350, 500)

  def _setWidgets(self):
    setWidgets = (
                  self.componentTypeWidget,
                  self.componentNameWidget,
                  self.labelingWidget,
                  self.concentrationUnitWidget,
                  self.concentrationUnitWidget1,
                  self.concentrationWidget,
                  self.referenceSpectraWidget,
                  self.chemicalNameWidget,
                  self.smilesWidget,
                  self.empiricalFormulaWidget,
                  self.molecularMassWidget,
                  self.CommentWidget,
                  self.labelUserCodeWidget,
                  self.casNumberWidget,
                  self.atomWidget,
                  self.bondCountWidget,
                  self.ringCountWidget,
                  self.bondDonorCountWidget,
                  self.bondAcceptorCountWidget,
                  self.polarSurfaceAreaWidget,
                  self.LogPWidget,
                  self._showCompoundView,
                  self._setPerformButtonWidgets
                  )
    for setWidget in setWidgets:
      setWidget()

  def componentTypeWidget(self):
    typeLabel = Label(self,text="Type ")
    self.type = PulldownList(self)
    self.type.setData(TYPECOMPONENT)
    # self.type.setFixedWidth(129)
    self.type.activated[str].connect(self._typeComponent)
    self.mainLayout.addWidget(typeLabel, 0, 0)
    self.mainLayout.addWidget(self.type, 0, 1)

  def componentNameWidget(self):
    sampleComponentsLabel = Label(self, text="Component Name ")
    self.nameComponents = LineEdit(self)
    self.nameComponents.setText(self.sampleComponent.name)
    self.nameComponents.editingFinished.connect(self._changeNameComponents)
    self.mainLayout.addWidget(sampleComponentsLabel, 1, 0)
    self.mainLayout.addWidget(self.nameComponents, 1, 1)


  def labelingWidget(self):
    sampleComponentsLabelingLabel = Label(self,text="Labeling ")
    self.labeling = LineEdit(self)
    self.labeling.setText(self.sampleComponent.labeling)
    self.labeling.editingFinished.connect(self._labelingChanged)
    self.mainLayout.addWidget(sampleComponentsLabelingLabel, 2, 0)
    self.mainLayout.addWidget(self.labeling, 2, 1)

  def concentrationUnitWidget(self):
    concentrationUnitLabel = Label(self, text="Value Unit ")
    self.concentrationUnit = PulldownList(self)
    self.concentrationUnit.setData(C_COMPONENT_UNIT)
    # self.concentrationUnit.setFixedWidth(128)
    self.concentrationUnit.activated[str].connect(self._setConcentrationUnit)
    self.mainLayout.addWidget(concentrationUnitLabel, 3, 0)
    self.mainLayout.addWidget(self.concentrationUnit, 3, 1)


  def concentrationUnitWidget1(self):
    concentrationLabel = Label(self, text="Value 1 ")
    self.concentrationUnit1 = PulldownList(self)
    # self.concentrationUnit1.setFixedWidth(128)
    self.concentration = DoubleSpinbox(self)
    self.concentration.setRange(0.00, 1000.00)
    self.concentration.setSingleStep(0.01)
    # self.concentration.setFixedWidth(128)
    self.concentration.setFixedHeight(20)
    self.concentration.valueChanged.connect(self._concentrationChanged)
    self.mainLayout.addWidget(concentrationLabel, 4, 0)
    self.mainLayout.addWidget(self.concentrationUnit1, 4, 1)
    self.mainLayout.addWidget(self.concentration, 5, 1)

  def concentrationWidget(self):
    self.concentrationLabel2 = Label(self, text="Value 2 ")
    self.concentrationUnit2 = PulldownList(self)
    # self.concentrationUnit2.setFixedWidth(128)
    self.concentration2 = DoubleSpinbox(self)
    self.concentration2.setRange(0.00, 1000.00)
    self.concentration2.setSingleStep(0.01)
    # self.concentration2.setFixedWidth(128)
    self.concentration2.setFixedHeight(20)
    self.concentrationUnit2.hide()
    self.concentrationLabel2.hide()
    self.concentration2.hide()
    self.concentration2.valueChanged.connect(self._concentration2Changed)
    self.mainLayout.addWidget(self.concentrationLabel2, 6, 0)
    self.mainLayout.addWidget(self.concentrationUnit2, 6, 1)
    self.mainLayout.addWidget(self.concentration2, 7, 1)

  def referenceSpectraWidget(self):
    referenceSpectraLabel = Label(self, text="Ref Spectra")
    self.referenceSpectra = PulldownList(self)
    for referenceSpectra in self.sampleComponent.substance.referenceSpectra:
      self.referenceSpectra.setData([referenceSpectra.pid])
    # self.referenceSpectra.setFixedWidth(133)
    self.mainLayout.addWidget(referenceSpectraLabel, 8, 0)
    self.mainLayout.addWidget(self.referenceSpectra, 8, 1)

  def chemicalNameWidget(self):
    chemicalNameLabel = Label(self, text="Chemical Name")
    self.chemicalName = LineEdit(self)
    self.chemicalName.editingFinished.connect(self._chemicalNameChanged)
    self.mainLayout.addWidget(chemicalNameLabel, 9, 0)
    self.mainLayout.addWidget(self.chemicalName, 9, 1)


  def smilesWidget(self):
    self.smileLabel = Label(self, text="Smiles")
    self.smilesLineEdit = LineEdit(self)
    self.smilesLineEdit.setText(self.sampleComponent.substance.smiles)
    self.smilesLineEdit.editingFinished.connect(self._smileChanged)
    self.mainLayout.addWidget(self.smileLabel, 10, 0)
    self.mainLayout.addWidget(self.smilesLineEdit, 10, 1)

  def empiricalFormulaWidget(self):
    self.empiricalFormulaLabel = Label(self, text="Empirical Formula")
    self.empiricalFormula = LineEdit(self)
    self.empiricalFormula.setText(str(self.sampleComponent.substance.empiricalFormula))
    self.empiricalFormula.editingFinished.connect(self._empiricalFormulaChanged)
    self.mainLayout.addWidget(self.empiricalFormulaLabel, 11, 0)
    self.mainLayout.addWidget(self.empiricalFormula, 11, 1)

  def molecularMassWidget(self):
    self.molecularMassLabel = Label(self, text="Molecular Mass")
    self.molecularMass = LineEdit(self)
    self.molecularMass.setText(str(self.sampleComponent.substance.molecularMass))
    self.molecularMass.editingFinished.connect(self._molecularMassChanged)
    self.mainLayout.addWidget(self.molecularMassLabel, 12, 0)
    self.mainLayout.addWidget(self.molecularMass, 12, 1)


  def CommentWidget(self):
    self.labelcomment = Label(self,text="Comment")
    self.comment = LineEdit(self)
    self.comment.setText(self.sampleComponent.substance.comment)
    self.comment.editingFinished.connect(self._commentChanged)
    self.mainLayout.addWidget(self.labelcomment, 13, 0)
    self.mainLayout.addWidget(self.comment, 13, 1)
    #
    # self.moreInfo = Button(self, "More... ", hAlign='c', callback=self._moreInfoComponents)
    # self.moreInfo.setFixedHeight(20)
    # self.showSmiles = Button(self, text="Display Compound",
    #                          hAlign='c', callback=self._showCompound)
    # self.hideSmiles = Button(self, text="Hide Compound",
    #                          hAlign='c', callback=None)
    # self.mainLayout.addWidget(self.showSmiles, 21, 0)
    # self.mainLayout.addWidget(self.hideSmiles, 21, 0)
    # self.hideSmiles.hide()
    #   # User Code

  def labelUserCodeWidget(self):
    self.labelUserCode = Label(self, text="User Code")
    self.userCode = LineEdit(self)
    self.userCode.setText(str(self.sampleComponent.substance.userCode))
    self.userCode.editingFinished.connect(self._userCodeChanged)
    # self.labelUserCode.hide()
    # self.userCode.hide()
    self.mainLayout.addWidget(self.labelUserCode, 14, 0)
    self.mainLayout.addWidget(self.userCode, 14, 1)

  def casNumberWidget(self):
    self.labelCasNumber = Label(self, text="Cas Number")
    self.casNumber = LineEdit(self)
    self.casNumber.setText(str(self.sampleComponent.substance.casNumber))
    self.casNumber.editingFinished.connect(self._casNumberChanged)
    # self.labelCasNumber.hide()
    # self.casNumber.hide()
    self.mainLayout.addWidget(self.labelCasNumber, 13, 0)
    self.mainLayout.addWidget(self.casNumber, 13, 1)

  def atomWidget(self):
    self.labelAtomCount = Label(self, text="Atom Count")
    self.atomCount = LineEdit(self)
    self.atomCount.setText(str(self.sampleComponent.substance.atomCount))
    self.atomCount.editingFinished.connect(self._atomCountChanged)
    # self.labelAtomCount.hide()
    # self.atomCount.hide()
    self.mainLayout.addWidget(self.labelAtomCount, 14, 0)
    self.mainLayout.addWidget(self.atomCount, 14, 1)

  def bondCountWidget(self):
    self.labelBondCount = Label(self, text="Bond Count")
    self.bondCount = LineEdit(self)
    self.bondCount.setText(str(self.sampleComponent.substance.bondCount))
    # self.labelBondCount.hide()
    # self.bondCount.hide()
    self.mainLayout.addWidget(self.labelBondCount, 15, 0)
    self.mainLayout.addWidget(self.bondCount, 15, 1)

  def ringCountWidget(self):
    self.labelRingCount = Label(self, text="Ring Count")
    self.ringCount = LineEdit(self)
    self.ringCount.setText(str(self.sampleComponent.substance.ringCount))
    self.ringCount.editingFinished.connect(self._ringCountChanged)
    # self.labelRingCount.hide()
    # self.ringCount.hide()
    self.mainLayout.addWidget(self.labelRingCount, 16, 0)
    self.mainLayout.addWidget(self.ringCount, 16, 1)

  def bondDonorCountWidget(self):
    self.labelHBondDonorCount = Label(self, text="H Bond Donors")
    self.hBondDonorCount = LineEdit(self)
    self.hBondDonorCount.setText(str(self.sampleComponent.substance.hBondDonorCount))
    self.hBondDonorCount.editingFinished.connect(self._hBondDonorCountChanged)
    # self.labelHBondDonorCount.hide()
    # self.hBondDonorCount.hide()
    self.mainLayout.addWidget(self.labelHBondDonorCount, 17, 0)
    self.mainLayout.addWidget(self.hBondDonorCount, 17, 1)

  def bondAcceptorCountWidget(self):
    self.labelHBondAcceptorCount = Label(self, text="H Bond Acceptors")
    self.hBondAcceptorCount = LineEdit(self)
    self.hBondAcceptorCount.setText(str(self.sampleComponent.substance.hBondAcceptorCount))
    self.hBondAcceptorCount.editingFinished.connect(self._hBondAcceptorCountChanged)
    # self.labelHBondAcceptorCount.hide()
    # self.hBondAcceptorCount.hide()
    self.mainLayout.addWidget(self.labelHBondAcceptorCount, 18, 0)
    self.mainLayout.addWidget(self.hBondAcceptorCount, 18, 1)

  def polarSurfaceAreaWidget(self):
    self.labelpolarSurfaceArea = Label(self, text="Polar Surface Area")
    self.polarSurfaceArea = LineEdit(self)
    self.polarSurfaceArea.setText(str(self.sampleComponent.substance.polarSurfaceArea))
    self.polarSurfaceArea.editingFinished.connect(self._polarSurfaceAreaChanged)
    # self.labelpolarSurfaceArea.hide()
    # self.polarSurfaceArea.hide()
    self.mainLayout.addWidget(self.labelpolarSurfaceArea, 19, 0)
    self.mainLayout.addWidget(self.polarSurfaceArea, 19, 1)

  def LogPWidget(self):
    self.labelLogP = Label(self, text="LogP")
    self.logP = LineEdit(self)
    self.logP.setText(str(self.sampleComponent.substance.logPartitionCoefficient))
    self.logP.editingFinished.connect(self._logPChanged)
    # self.labelLogP.hide()
    # self.logP.hide()
    self.mainLayout.addWidget(self.labelLogP, 20, 0)
    self.mainLayout.addWidget(self.logP, 20, 1)

  def _showCompoundView(self):

    self.moleculeViewLabel = Label(self, text="Compound View")
    smiles = self.sampleComponent.substance.smiles
    if smiles is None:
      smiles = 'H'
    else:
      smiles = smiles
    self.compoundView = CompoundView(self, smiles=smiles,
                                     preferences=None)

    self.compoundView.centerView()
    self.compoundView.updateAll()
    self.mainLayout.addWidget(self.moleculeViewLabel, 21, 0)
    self.mainLayout.addWidget(self.compoundView, 21, 1)

  def _setPerformButtonWidgets(self):
    self.buttonBox = ButtonList(self, callbacks=[self.reject, self.accept], texts=['Cancel', 'Apply'])
    self.mainLayout.addWidget(self.buttonBox, 22, 1)

#   CallBacks

  def _getSampleComponent(self):
    sampleComponent = self.sample.newSampleComponent(
      name='New-' + str(len(self.sample.sampleComponents) + 1), labeling='None')
    return sampleComponent

  def _moreInfoComponents(self):
    # self.moreInfo.hide()
    # self.showSmiles.hide()
    # self.lessInfo = Button(self.area, text="Less... ", grid=(22, 1),
    #                        hAlign='c', callback=self._hideInfo)
    # self.lessInfo.setFixedHeight(20)
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
    pass
    # if pressed == 'Compound':
    #   # self.moreInfo.show()
    #   self.smileLabel.show()
    #   self.compoundView.show()
    #   self.empiricalFormulaLabel.show()
    #   self.empiricalFormula.show()
    #   self.molecularMassLabel.show()
    #   self.molecularMass.show()
    #   # self.showSmiles.show()
    #
    # else:
    #   self._hideInfo()
      # if hasattr(self, 'moreInfo'):
      #   self.moreInfo.hide()
      # self.showSmiles.hide()

  def _hideInfo(self):
    # self.showSmiles.show()
    # self.moreInfo.show()
    # if hasattr(self, 'lessInfo'):
    #   self.lessInfo.hide()
    self.smileLabel.hide()
    self.compoundView.hide()
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
    print('labeling not Changed', self.sampleComponent.labeling)

  def _concentrationChanged(self, value):
    self.sampleComponent.concentration = float(value)

  def _concentration2Changed(self, value):
    print(value, 'concentration2 Not implemented Yet')

  def _chemicalNameChanged(self):
    print('Not implemented Yet')

  def _smileChanged(self):
    self.sampleComponent.substance.smiles = str(self.smilesLineEdit.text())

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

  # def _showCompound(self):
  #   # self.moreInfo.hide()
  #   # self.showSmiles.hide()
  #   self.hideSmiles.show()
  #
  #   smiles = self.sampleComponent.substance.smiles
  #   if smiles is None:
  #     smiles = 'C'
  #   else:
  #     smiles = smiles
  #   self.compoundView = CompoundView(self, smiles=smiles,
  #                                    preferences=None)
  #
  #   self.compoundView.centerView()
  #   self.compoundView.updateAll()
  #   self.mainLayout.addWidget(self.compoundView,30,0)
