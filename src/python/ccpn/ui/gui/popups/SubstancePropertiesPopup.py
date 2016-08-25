__author__ = 'luca'


from PyQt4 import QtGui, QtCore
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.widgets.CompoundView import CompoundView, Variant, importSmiles
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons

OTHER_UNIT = ['µ','m', 'n', 'p']
CONCENTRATION_UNIT = ['µM', 'mM', 'nM', 'pM']
VOLUME_UNIT = ['µL', 'mL', 'nL', 'pL']
MASS_UNIT = ['µg','kg','g','mg', 'ng', 'pg']
SAMPLE_STATES = ['Liquid', 'Solid', 'Ordered', 'Powder', 'Crystal', 'Other']
SUBSTANCE_TYPE =  ['Molecule', 'Cell', 'Material', 'Composite ', 'Other']



class SubstancePropertiesPopup(QtGui.QDialog):

  def __init__(self, substance=None, project=None, parent=None, sampleComponent=None, newSubstance=False,  **kw):
    super(SubstancePropertiesPopup, self).__init__(parent)
    self.project = project
    self.sample = parent
    self.sampleComponent = sampleComponent
    self.substance = substance

    self.preferences = self.project._appBase.preferences

    self.createNewSubstance = newSubstance
    self._setMainLayout()
    self._setWidgets()
    self._addWidgetsToLayout(self._allWidgets(), self.mainLayout)

    if self.createNewSubstance:
      self._checkCurrentSubstances()
    else:
      self._hideSubstanceCreator()

  def _setMainLayout(self):
    self.mainLayout = QtGui.QGridLayout()
    self.setLayout(self.mainLayout)
    self.setWindowTitle("Substance Properties")
    # self.setFixedHeight(300)
    self.mainLayout.setContentsMargins(15, 20, 25, 10)  # L,T,R,B

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
    widgetsToSet = (self._initialOpitionWidgets, self._setCurrentSubstanceWidgets,
                    self._substanceNameWidget, self.labelingWidget,
                    self._chemicalNameWidget,
                    self._smilesWidget, self._empiricalFormulaWidget,
                    self._molecularMassWidget, self._commentWidget, self._labelUserCodeWidget,
                    self._casNumberWidget, self._atomWidget, self._bondCountWidget,
                    self._ringCountWidget, self._bondDonorCountWidget, self._bondAcceptorCountWidget,
                    self._polarSurfaceAreaWidget, self._logPWidget, self._showCompoundView,
                    self._setPerformButtonWidgets)
    return widgetsToSet

  def _allWidgets(self):
    return  [
            self.spacerLabel, self.selectInitialRadioButtons,
            self.currentSubstanceLabel, self.substancePulldownList,
            self.substanceLabel,self.nameSubstance,
            self._substanceLabelingLabel, self.labeling,
            self.chemicalNameLabel,self.chemicalName,
            self.smilesLabel,self.smilesLineEdit,
            self.empiricalFormulaLabel,self.empiricalFormula,
            self.molecularMassLabel, self.molecularMass,
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
            self.labelcomment, self.comment,
            self.spacerLabel, self.buttonBox
            ]

  def _initialOpitionWidgets(self):
    self.spacerLabel = Label(self, text="")
    self.selectInitialRadioButtons = RadioButtons(self, texts=['New', 'From Existing'],
                                                  selectedInd=1,
                                                  callback=None,
                                                  direction='h',
                                                  tipTexts=None)

  def _setCurrentSubstanceWidgets(self):
    self.currentSubstanceLabel = Label(self, text="Current Substances")
    self.substancePulldownList = PulldownList(self)
    if self.createNewSubstance:
      self._fillsubstancePulldownList()
      self.substancePulldownList.activated[str].connect(self._fillInfoFromSubstance)

  def _substanceTypeWidget(self):
    self.typeLabel = Label(self, text="Type")
    self.type = Label(self, text="Molecule")


  def _substanceNameWidget(self):
    self.substanceLabel = Label(self, text="Substance Name")
    self.nameSubstance = LineEdit(self, 'New')
    if self.substance:
      self.nameSubstance.setText(self.substance.name)

  def labelingWidget(self):
    self._substanceLabelingLabel = Label(self, text="Labeling")
    self.labeling = LineEdit(self, 'None')
    if self.substance:
      self.labeling.setText(self.substance.labeling)

  def _referenceSpectraWidget(self):
    self.referenceSpectraLabel = Label(self, text="Ref Spectra")
    self.referenceSpectra = PulldownList(self)
    if self.substance:
      for referenceSpectra in self.substance.referenceSpectra:
        self.referenceSpectra.setData([referenceSpectra.pid])



  def _chemicalNameWidget(self):
    self.chemicalNameLabel = Label(self, text="Chemical Names")
    self.chemicalName = LineEdit(self)
    if self.substance:
      self.chemicalName.setText(str(self.substance.synonyms,))


  def _smilesWidget(self):
    self.smilesLabel = Label(self, text="Smiles")
    self.smilesLineEdit = LineEdit(self)
    if self.substance:
      self.smilesLineEdit.setText(self.substance.smiles)

  def _empiricalFormulaWidget(self):
    self.empiricalFormulaLabel = Label(self, text="Empirical Formula")
    self.empiricalFormula = LineEdit(self)
    if self.substance:
      self.empiricalFormula.setText(str(self.substance.empiricalFormula))

  def _molecularMassWidget(self):
    self.molecularMassLabel = Label(self, text="Molecular Mass")
    self.molecularMass = LineEdit(self)
    if self.substance:
      self.molecularMass.setText(str(self.substance.molecularMass))

  def _commentWidget(self):
    self.labelcomment = Label(self, text="Comment")
    self.comment = LineEdit(self)
    if self.substance:
      self.comment.setText(self.substance.comment)

  def _labelUserCodeWidget(self):
    self.labelUserCode = Label(self, text="User Code")
    self.userCode = LineEdit(self)
    if self.substance:
      self.userCode.setText(str(self.substance.userCode))

  def _casNumberWidget(self):
    self.labelCasNumber = Label(self, text="Cas Number")
    self.casNumber = LineEdit(self)
    if self.substance:
      self.casNumber.setText(str(self.substance.casNumber))

  def _atomWidget(self):
    self.labelAtomCount = Label(self, text="Atom Count")
    self.atomCount = LineEdit(self)
    if self.substance:
      self.atomCount.setText(str(self.substance.atomCount))


  def _bondCountWidget(self):
    self.labelBondCount = Label(self, text="Bond Count")
    self.bondCount = LineEdit(self)
    if self.substance:
      self.bondCount.setText(str(self.substance.bondCount))

  def _ringCountWidget(self):
    self.labelRingCount = Label(self, text="Ring Count")
    self.ringCount = LineEdit(self)
    if self.substance:
      self.ringCount.setText(str(self.substance.ringCount))

  def _bondDonorCountWidget(self):
    self.labelHBondDonorCount = Label(self, text="H Bond Donors")
    self.hBondDonorCount = LineEdit(self)
    if self.substance:
      self.hBondDonorCount.setText(str(self.substance.hBondDonorCount))

  def _bondAcceptorCountWidget(self):
    self.labelHBondAcceptorCount = Label(self, text="H Bond Acceptors")
    self.hBondAcceptorCount = LineEdit(self)
    if self.substance:
      self.hBondAcceptorCount.setText(str(self.substance.hBondAcceptorCount))

  def _polarSurfaceAreaWidget(self):
    self.labelpolarSurfaceArea = Label(self, text="Polar Surface Area")
    self.polarSurfaceArea = LineEdit(self)
    if self.substance:
      self.polarSurfaceArea.setText(str(self.substance.polarSurfaceArea))

  def _logPWidget(self):
    self.labelLogP = Label(self, text="LogP")
    self.logP = LineEdit(self)
    if self.substance:
      self.logP.setText(str(self.substance.logPartitionCoefficient))

  def _showCompoundView(self):
    self.moleculeViewLabel = Label(self, text="Compound View")
    if self.substance:
      smiles = self.substance.smiles
      if smiles is None:
        smiles = 'H'
      else:
        smiles = smiles
    else:
      smiles = ''
    self.compoundView = CompoundView(self, smiles=smiles, preferences=self.preferences)

    self.compoundView.centerView()
    self.compoundView.updateAll()

  def _setPerformButtonWidgets(self):
    self.spacerLabel = Label(self, text="")
    self.buttonBox = ButtonList(self, callbacks=[self._hideExtraSettings, self._showMoreSettings,
                                                 self.reject,self._applyChanges, self._okButton],
                                texts=['Less','More','Cancel', 'Apply', 'Ok'])
    self._hideExtraSettings()


  # CallBacks

  def _getCallBacksDict(self):
    return {
      self._changeNameSubstance: str(self.nameSubstance.text()),
      self._labelingChanged:str(self.labeling.text()) ,
      self._chemicalNameChanged: (str(self.chemicalName.text()),),
      self._smilesChanged: str(self.smilesLineEdit.text()),
      self._empiricalFormulaChanged: str(self.empiricalFormula.text()),
      self._molecularMassChanged: self.molecularMass.text(),
      self._userCodeChanged: str(self.userCode.text()),
      self._casNumberChanged: str(self.casNumber.text()),
      self._atomCountChanged: self.atomCount.text(),
      self._ringCountChanged: self.ringCount.text(),
      self._hBondDonorCountChanged: self.hBondDonorCount.text(),
      self._hBondAcceptorCountChanged: self.hBondAcceptorCount.text(),
      self._polarSurfaceAreaChanged: self.polarSurfaceArea.text(),
      self._logPChanged: self.logP.text(),
      self._commentChanged: str(self.comment.text()),

    }
  #
  # def _substanceType(self, value):
  #   if value:
  #     print(value)
  #     # self.substance.substanceType = str(value)

  def _fillsubstancePulldownList(self):
    if len(self.project.substances) > 0:
      substancePulldownData = ['Select an option']
      for substance in self.project.substances:
        substancePulldownData.append(str(substance.id))
      self.substancePulldownList.setData(substancePulldownData)

  def _fillInfoFromSubstance(self, selected):
    if selected != 'Select an option':
      substance = self.project.getByPid('SU:' + selected)
      self.nameSubstance.setText(str(substance.name)+'-Copy')
      self.labeling.setText(str(substance.labeling))

  def _changeNameSubstance(self, value):
    if value:
      if self.substance.name != value:
        self.substance.rename(name=value)

  def _labelingChanged(self, value):
    if value:
      if self.substance.labeling != value:
        self.substance.rename(labeling=value)

  def _chemicalNameChanged(self, value):
    if value:
      if value == 'None':
        return
      else:
        self.substance.synonyms = value

  def _smilesChanged(self, value):
    if value:
      if value == 'None':
        return
      else:
        self.substance.smiles = value

  def _empiricalFormulaChanged(self, value):
    if value:
      if value == 'None':
        return
      else:
        self.substance.empiricalFormula = str(value)

  def _molecularMassChanged(self, value):
    if value:
      if value == 'None':
        return
      else:
        self.substance.molecularMass = float(value)

  def _userCodeChanged(self, value):
    if value:
      if value == 'None':
        return
      else:
        self.substance.userCode = value

  def _casNumberChanged(self, value):
    if value:
      if value == 'None':
        return
      else:
        self.substance.casNumber = value

  def _atomCountChanged(self, value):
    if value:
      if value == 'None':
        return
      else:
        self.substance.atomCount = int(value)

  def _boundCountChanged(self, value):
    if value:
      if value == 'None':
        return
      else:
        self.substance.bondCount = int(value)


  def _ringCountChanged(self, value):
    if value:
      if value == 'None':
        return
      else:
       self.substance.ringCount = int(value)

  def _hBondDonorCountChanged(self, value):
    if value:
      if value == 'None':
        return
      else:
        self.substance.hBondDonorCount = int(value)

  def _hBondAcceptorCountChanged(self, value):
    if value:
      if value == 'None':
        return
      else:
        self.substance.hBondAcceptorCount = int(value)

  def _polarSurfaceAreaChanged(self, value):
    if value:
      if value == 'None':
        return
      else:
        self.substance.polarSurfaceArea = float(value)

  def _logPChanged(self, value):
    if value:
      if value == 'None':
        return
      else:
        self.substance.logPartitionCoefficient = float(value)

  def _commentChanged(self, value):
    if value:
      self.substance.comment = value

  def _getSubstance(self):
    if len(self.project.substances) > 0:
      substance = self.project.newSubstance(name='NewSubstance-' + str(len(self.project.substances)))
      return substance
    else:
      substance = self.project.newSubstance(name='NewSubstance-',)
      return substance

  def _hideExtraSettings(self):
    for w in self._allWidgets()[12:-1]:
      w.hide()
    self.buttonBox.buttons[0].hide()
    self.buttonBox.buttons[1].show()
    self.setMaximumHeight(200)

  def _showMoreSettings(self):
    for w in self._allWidgets()[12:-1]:
      w.show()
    self.buttonBox.buttons[0].show()
    self.buttonBox.buttons[1].hide()
    self.setMaximumHeight(800)

  def _checkCurrentSubstances(self):
    if len(self.project.substances) > 0:
      for w in self._allWidgets()[0:4]:
        w.show()
    else:
      for w in self._allWidgets()[2:4]:
        w.hide()
      self.selectInitialRadioButtons.radioButtons[0].setChecked(True)
      self.selectInitialRadioButtons.radioButtons[1].setEnabled(False)

  def _hideSubstanceCreator(self):
    if len(self.project.substances) > 0:
      for w in self._allWidgets()[0:4]:
        w.hide()

  def _createNewSubstance(self):
    name = str(self.nameSubstance.text())
    labeling = str(self.labeling.text())
    self.substance = self.project.newSubstance(name=name, labeling=labeling)
    self.createNewSubstance = False

  def _setValue(self):
    for property, value in self._getCallBacksDict().items():
      property(value)

  def _applyChanges(self):
    if self.createNewSubstance:
      self._createNewSubstance()
    self._setValue()

  def _okButton(self):

    self._applyChanges()
    self.accept()