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
TYPECOMPONENT =  ['Select','Compound', 'Solvent', 'Target', 'inhibitor ', 'Other']
C_COMPONENT_UNIT = ['Select', 'L/L', 'mol/mol', 'g/g', 'g/L', 'M']



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
    self.application = self.mainWindow.application
    self.generalPreferences = self.application.preferences.general
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
                  self.componentRoleWidget,
                  self.componentNameWidget,
                  self.labelingWidget,
                  self.concentrationUnitWidget,
                  self.concentrationWidget,
                  self._commentWidget,
                  self._setPerformButtonWidgets
                  )
    for setWidget in setWidgets:
      setWidget()

  def componentRoleWidget(self):
    typeLabel = Label(self,text="Role ")
    self.type = PulldownList(self)
    self.type.setData(TYPECOMPONENT)
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
    concentrationUnitLabel = Label(self, text="Concentration Unit ")
    self.concentrationUnit = PulldownList(self)
    self.concentrationUnit.setData(C_COMPONENT_UNIT)
    # self.concentrationUnit.setFixedWidth(128)
    self.concentrationUnit.activated[str].connect(self._setConcentrationUnit)
    self.mainLayout.addWidget(concentrationUnitLabel, 3, 0)
    self.mainLayout.addWidget(self.concentrationUnit, 3, 1)


  def concentrationWidget(self):
    self.concentrationLabel2 = Label(self, text="Concentration ")

    self.concentration2 = DoubleSpinbox(self)
    self.concentration2.setRange(0.00, 1000.00)
    self.concentration2.setSingleStep(0.01)


    self.mainLayout.addWidget(self.concentrationLabel2, 6, 0)
    self.mainLayout.addWidget(self.concentration2, 6, 1)



  def _commentWidget(self):
    self.labelcomment = Label(self,text="Comment")
    self.comment = LineEdit(self)
    self.comment.setText(self.sampleComponent.substance.comment)
    self.comment.editingFinished.connect(self._commentChanged)
    self.mainLayout.addWidget(self.labelcomment, 13, 0)
    self.mainLayout.addWidget(self.comment, 13, 1)


  def _setPerformButtonWidgets(self):
    self.buttonBox = ButtonList(self, callbacks=[self.reject, self.accept], texts=['Cancel', 'Apply'])
    self.mainLayout.addWidget(self.buttonBox, 22, 1)


  def _getSampleComponent(self):
    sampleComponent = self.sample.newSampleComponent(
      name='New-' + str(len(self.sample.sampleComponents) + 1), labeling='None')
    return sampleComponent

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

  def _changeNameComponents(self):
    print('Not implemented Yet')

  def _labelingChanged(self):
    # self.sampleComponent.labeling = str(self.labeling.text())
    print('labeling not Changed', self.sampleComponent.labeling)

  def _concentrationChanged(self, value):
    self.sampleComponent.concentration = float(value)

  def _concentration2Changed(self, value):
    print(value, 'concentration2 Not implemented Yet')

  def _commentChanged(self):
    self.sampleComponent.substance.comment = str(self.comment.text())
