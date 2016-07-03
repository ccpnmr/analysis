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

OTHER_UNIT = ['µ','m', 'n', 'p']
CONCENTRATION_UNIT = ['µM', 'mM', 'nM', 'pM']
VOLUME_UNIT = ['µL', 'mL', 'nL', 'pL']
MASS_UNIT = ['µg','kg','g','mg', 'ng', 'pg']
SAMPLE_STATES = ['Liquid', 'Solid', 'Ordered', 'Powder', 'Crystal', 'Other']
SUBSTANCE_TYPE =  ['Molecule', 'Cell', 'Material', 'Composite ', 'Other']



class SubstancePropertiesPopup(QtGui.QDialog):

  def __init__(self, substance=None, project=None, parent=None, sampleComponent=None,   **kw):
    super(SubstancePropertiesPopup, self).__init__(parent)
    self.project = project
    # ?? self.preferences = ??
    self.sample = parent
    self.sampleComponent = sampleComponent
    if substance is not None:
      self.substance = substance
    else:
      self.substance = self._getSubstance()
    self._setMainLayout()
    self._setWidgets()
    self._addWidgetsToLayout(self._allWidgets(), self.mainLayout)

  def _setMainLayout(self):
    self.mainLayout = QtGui.QGridLayout()
    self.setLayout(self.mainLayout)
    self.setWindowTitle("Substance Properties")
    self.resize(350, 350)

  def _setWidgets(self):
    for setWidget in self._getWidgetsToSet():
      setWidget()

  def _addWidgetsToLayout(self, widgets, layout):
    count = int(len(widgets) / 2)
    self.positions = [[i + 1, j] for i in range(count) for j in range(2)]
    for position, widget in zip(self.positions, widgets):
      i, j = position
      layout.addWidget(widget, i, j)

  def _getWidgetsToSet(self):
    widgetsToSet = ( self._substanceTypeWidget, self._substanceNameWidget, self.labelingWidget,

      self._referenceSpectraWidget, self._chemicalNameWidget, self._smilesWidget, self._empiricalFormulaWidget,
      self._molecularMassWidget, self._commentWidget, self._labelUserCodeWidget,
      self._casNumberWidget, self._atomWidget, self._bondCountWidget,
      self._ringCountWidget, self._bondDonorCountWidget, self._bondAcceptorCountWidget,
      self._polarSurfaceAreaWidget, self._logPWidget, self._showCompoundView,
      self._setPerformButtonWidgets)
    return widgetsToSet

  def _allWidgets(self):
    return  (
            self.typeLabel,self.type ,
            self.substanceLabel,self.nameSubstance,
            self._substanceLabelingLabel, self.labeling,
            self.referenceSpectraLabel,self.referenceSpectra,
            self.chemicalNameLabel,self.chemicalName,
            self.smilesLabel,self.smilesLineEdit,
            self.empiricalFormulaLabel,self.empiricalFormula,
            self.molecularMassLabel, self.molecularMass,
            self.labelcomment,self.comment,
            self.labelUserCode,self.userCode,
            self.labelCasNumber,self.casNumber,
            self.labelAtomCount,self.atomCount,
            self.labelBondCount,self.bondCount,
            self.labelRingCount,self.ringCount,
            self.labelHBondDonorCount,self.hBondDonorCount,
            self.labelHBondAcceptorCount,self.hBondAcceptorCount,
            self.labelpolarSurfaceArea,self.polarSurfaceArea,
            self.labelLogP,self.logP,
            self.moleculeViewLabel,self.compoundView,
            self.spacerLabel, self.buttonBox
            )


  def _substanceTypeWidget(self):
    self.typeLabel = Label(self, text="Type ")
    self.type = PulldownList(self)
    self.type.setData(SUBSTANCE_TYPE)
    self.type.activated[str].connect(self._substanceType)

  def _substanceNameWidget(self):
    self.substanceLabel = Label(self, text="Substance Name ")
    self.nameSubstance = LineEdit(self)
    self.nameSubstance.setText(self.substance.name)
    self.nameSubstance.editingFinished.connect(self._changeNameSubstance)

  def labelingWidget(self):
    self._substanceLabelingLabel = Label(self, text="Labeling ")
    self.labeling = LineEdit(self)
    self.labeling.setText(self.substance.labeling)
    self.labeling.editingFinished.connect(self._labelingChanged)

  def _referenceSpectraWidget(self):
    self.referenceSpectraLabel = Label(self, text="Ref Spectra")
    self.referenceSpectra = PulldownList(self)
    for referenceSpectra in self.substance.referenceSpectra:
      self.referenceSpectra.setData([referenceSpectra.pid])

  def _chemicalNameWidget(self):
    self.chemicalNameLabel = Label(self, text="Chemical Name")
    self.chemicalName = LineEdit(self, )
    self.chemicalName.editingFinished.connect(self._chemicalNameChanged)

  def _smilesWidget(self):
    self.smilesLabel = Label(self, text="Smiles")
    self.smilesLineEdit = LineEdit(self)
    self.smilesLineEdit.setText(self.substance.smiles)
    self.smilesLineEdit.editingFinished.connect(self._smileChanged)

  def _empiricalFormulaWidget(self):
    self.empiricalFormulaLabel = Label(self, text="Empirical Formula")
    self.empiricalFormula = LineEdit(self)
    self.empiricalFormula.setText(str(self.substance.empiricalFormula))
    self.empiricalFormula.editingFinished.connect(self._empiricalFormulaChanged)

  def _molecularMassWidget(self):
    self.molecularMassLabel = Label(self, text="Molecular Mass")
    self.molecularMass = LineEdit(self)
    self.molecularMass.setText(str(self.substance.molecularMass))
    self.molecularMass.editingFinished.connect(self._molecularMassChanged)

  def _commentWidget(self):
    self.labelcomment = Label(self, text="Comment")
    self.comment = LineEdit(self)
    self.comment.setText(self.substance.comment)
    self.comment.editingFinished.connect(self._commentChanged)

  def _labelUserCodeWidget(self):
    self.labelUserCode = Label(self, text="User Code")
    self.userCode = LineEdit(self)
    self.userCode.setText(str(self.substance.userCode))
    self.userCode.editingFinished.connect(self._userCodeChanged)

  def _casNumberWidget(self):
    self.labelCasNumber = Label(self, text="Cas Number")
    self.casNumber = LineEdit(self)
    self.casNumber.setText(str(self.substance.casNumber))
    self.casNumber.editingFinished.connect(self._casNumberChanged)

  def _atomWidget(self):
    self.labelAtomCount = Label(self, text="Atom Count")
    self.atomCount = LineEdit(self)
    self.atomCount.setText(str(self.substance.atomCount))
    self.atomCount.editingFinished.connect(self._atomCountChanged)

  def _bondCountWidget(self):
    self.labelBondCount = Label(self, text="Bond Count")
    self.bondCount = LineEdit(self)
    self.bondCount.setText(str(self.substance.bondCount))

  def _ringCountWidget(self):
    self.labelRingCount = Label(self, text="Ring Count")
    self.ringCount = LineEdit(self)
    self.ringCount.setText(str(self.substance.ringCount))
    self.ringCount.editingFinished.connect(self._ringCountChanged)

  def _bondDonorCountWidget(self):
    self.labelHBondDonorCount = Label(self, text="H Bond Donors")
    self.hBondDonorCount = LineEdit(self)
    self.hBondDonorCount.setText(str(self.substance.hBondDonorCount))
    self.hBondDonorCount.editingFinished.connect(self._hBondDonorCountChanged)

  def _bondAcceptorCountWidget(self):
    self.labelHBondAcceptorCount = Label(self, text="H Bond Acceptors")
    self.hBondAcceptorCount = LineEdit(self)
    self.hBondAcceptorCount.setText(str(self.substance.hBondAcceptorCount))
    self.hBondAcceptorCount.editingFinished.connect(self._hBondAcceptorCountChanged)

  def _polarSurfaceAreaWidget(self):
    self.labelpolarSurfaceArea = Label(self, text="Polar Surface Area")
    self.polarSurfaceArea = LineEdit(self)
    self.polarSurfaceArea.setText(str(self.substance.polarSurfaceArea))
    self.polarSurfaceArea.editingFinished.connect(self._polarSurfaceAreaChanged)

  def _logPWidget(self):
    self.labelLogP = Label(self, text="LogP")
    self.logP = LineEdit(self)
    self.logP.setText(str(self.substance.logPartitionCoefficient))
    self.logP.editingFinished.connect(self._logPChanged)

  def _showCompoundView(self):
    self.moleculeViewLabel = Label(self, text="Compound View")
    smiles = self.substance.smiles
    if smiles is None:
      smiles = 'H'
    else:
      smiles = smiles
    self.compoundView = CompoundView(self, smiles=smiles, preferences=None)

    self.compoundView.centerView()
    self.compoundView.updateAll()

  def _setPerformButtonWidgets(self):
    self.spacerLabel = Label(self, text="")
    self.buttonBox = ButtonList(self, callbacks=[self.reject, self.accept], texts=['Cancel', 'Apply'])


  def _substanceType(self, pressed):
    print(self.substance, pressed)
    # self.substance.substanceType = str(pressed)



  def _changeNameSubstance(self):
    self.substance.rename = str(self.nameSubstance.text())

  def _labelingChanged(self):
    # self.sampleComponent.labeling = str(self.labeling.text())
    print('labeling not Changed', self.substance.labeling)

  def _chemicalNameChanged(self):
    self.substance.synonyms = (str(self.chemicalName.text()),)
    # self.chemicalName.setText(self.substance.synonyms)

  def _smileChanged(self):
    self.substance.smiles = str(self.smilesLineEdit.text())

  def _empiricalFormulaChanged(self):
    print(self.empiricalFormula.text())
    self.substance.empiricalFormula = str(self.empiricalFormula.text())

  def _molecularMassChanged(self):
    self.substance.molecularMass = float(self.molecularMass.text())

  def _userCodeChanged(self):
    self.substance.userCode = str(self.userCode.text())

  def _casNumberChanged(self):
    self.substance.casNumber = str(self.casNumber.text())

  def _atomCountChanged(self):
    self.substance.atomCount = int(self.atomCount.text())

  def _ringCountChanged(self):
    self.substance.ringCount = int(self.ringCount.text())

  def _hBondDonorCountChanged(self):
    self.substance.hBondDonorCount = int(self.hBondDonorCount.text())

  def _hBondAcceptorCountChanged(self):
    self.substance.hBondAcceptorCount = int(self.hBondAcceptorCount.text())

  def _polarSurfaceAreaChanged(self):
    self.substance.polarSurfaceArea = float(self.polarSurfaceArea.text())

  def _logPChanged(self):
    self.substance.logPartitionCoefficient = float(self.logP.text())

  def _commentChanged(self):
    self.substance.comment = str(self.comment.text())

  def _getSubstance(self):
    if len(self.project.substances) > 0:
      substance = self.project.newSubstance(name='NewSubstance-' + str(len(self.project.substances)))
      return substance
    else:
      substance = self.project.newSubstance(name='NewSubstance-')
      return substance