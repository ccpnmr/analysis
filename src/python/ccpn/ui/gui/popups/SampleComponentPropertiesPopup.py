__author__ = 'luca'

from PyQt4 import QtGui, QtCore
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.MessageDialog import showInfo

TYPECOMPONENT =  ['Select', 'Compound', 'Solvent', 'Buffer', 'Target', 'Inhibitor ', 'Other']
C_COMPONENT_UNIT = ['Select', 'Molar', 'g/L', 'L/L', 'mol/mol', 'g/g']



class EditSampleComponentPopup(QtGui.QDialog):

  def __init__(self, parent=None, project=None, sample=None, sampleComponent=None, newSampleComponent=False, **kw):
    super(EditSampleComponentPopup, self).__init__(parent)
    self.project = project
    self.sample = sample
    self.newSampleComponentToCreate = newSampleComponent

    self.sampleComponent = sampleComponent
    self._setMainLayout()
    self._setWidgets()
    self._addWidgetsToLayout(widgets=self._getAllWidgets(), layout=self.mainLayout)
    if self.newSampleComponentToCreate:
      self._updateButtons()

  def _setMainLayout(self):
    self.mainLayout = QtGui.QGridLayout()
    self.setLayout(self.mainLayout)
    self.setWindowTitle("Sample Component Properties")
    self.mainLayout.setContentsMargins(15, 20, 25, 10) #L,T,R,B
    self.setFixedWidth(400)
    self.setFixedHeight(250)

  def _getWidgetsToSet(self):

    return  (
            self.componentNameEditWidget,
            self.componentNameWidget,
            self.setLabelingWidget,
            self.currentLabelingWidget,
            self.componentRoleWidget,
            self.concentrationUnitWidget,
            self.concentrationWidget,
            self._commentWidget,
            self._setPerformButtonWidgets
            )

  def _setWidgets(self):
    for setWidget in self._getWidgetsToSet():
      setWidget()

  def _addWidgetsToLayout(self, widgets, layout):
    count = int(len(widgets) / 2)
    self.positions = [[i + 1, j] for i in range(count) for j in range(2)]
    for position, widget in zip(self.positions, widgets):
      i, j = position
      layout.addWidget(widget, i, j)
    layout.addWidget(self.buttons, count+1, 1)
    self.nameLabelingOptions()

  def nameLabelingOptions(self):
    if self.newSampleComponentToCreate:
      self.sampleComponentNameLabel.hide()
      self.sampleComponentShowName.hide()
      self.currentLabelingLabel.hide()
      self.showCurrentLabeling.hide()
    else:
      self.sampleComponentNewNameLabel.hide()
      self.nameComponentLineEdit.hide()
      self.sampleComponentLabelingLabel.hide()
      self.labelingLineEdit.hide()

  def _getAllWidgets(self):
    '''
    All widgets are ordered in the way they will be added to the layout EG:
    1)Label1 -> grid 0,0  ---- 2)LineEdit1 --> grid 0,1
    In this list are excluded the 'Cancel, Apply, Ok Buttons' '''
    return (
            self.sampleComponentNewNameLabel, self.nameComponentLineEdit,
            self.sampleComponentNameLabel, self.sampleComponentShowName,
            self.sampleComponentLabelingLabel, self.labelingLineEdit,
            self.currentLabelingLabel, self.showCurrentLabeling,
            self.typeLabel, self.typePulldownList,
            self.concentrationUnitLabel, self.concentrationUnitPulldownList,
            self.concentrationLabel, self.concentrationLineEdit,
            self.labelcomment, self.commentLineEdit
           )

  def componentNameEditWidget(self):
    self.sampleComponentNewNameLabel = Label(self, text="New Name^ ")
    self.nameComponentLineEdit = LineEdit(self)
    self.nameComponentLineEdit.editingFinished.connect(self._updateButtons)

  def componentNameWidget(self):
    self.sampleComponentNameLabel = Label(self, text="Name ")
    self.sampleComponentShowName = Label(self, text="")
    if self.sampleComponent:
      self.sampleComponentShowName.setText(self.sampleComponent.name)

  def setLabelingWidget(self):
    self.sampleComponentLabelingLabel = Label(self, text="Labeling^ ")
    self.labelingLineEdit = LineEdit(self)
    self.labelingLineEdit.editingFinished.connect(self._updateButtons)

  def currentLabelingWidget(self):
    self.currentLabelingLabel = Label(self, text="Labeling ")
    self.showCurrentLabeling = Label(self, text="")
    if self.sampleComponent:
      self.showCurrentLabeling.setText(self.sampleComponent.labeling)

  def componentRoleWidget(self):
    self.typeLabel = Label(self,text="Role ")
    self.typePulldownList = PulldownList(self)
    self.typePulldownList.setFixedWidth(210)
    self.typePulldownList.setData(TYPECOMPONENT)
    if self.sampleComponent:
      self.typePulldownList.set(str(self.sampleComponent.role))

  def concentrationUnitWidget(self):
    self.concentrationUnitLabel = Label(self, text="Concentration Unit ")
    self.concentrationUnitPulldownList = PulldownList(self)
    self.concentrationUnitPulldownList.setFixedWidth(210)
    self.concentrationUnitPulldownList.setData(C_COMPONENT_UNIT)
    if self.sampleComponent:
      self.concentrationUnitPulldownList.set(str(self.sampleComponent.concentrationUnit))

  def concentrationWidget(self):
    self.concentrationLabel = Label(self, text="Concentration ")
    self.concentrationLineEdit = LineEdit(self)
    self.concentrationLineEdit.editingFinished.connect(self._getConcentrationValue)
    if self.sampleComponent:
      self.concentrationLineEdit.setText(str(self.sampleComponent.concentration))

  def _commentWidget(self):
    self.labelcomment = Label(self,text="Comment")
    self.commentLineEdit = LineEdit(self)
    if self.sampleComponent:
      self.commentLineEdit.setText(self.sampleComponent.comment)

  def _setPerformButtonWidgets(self):
    self.buttons = ButtonList(self, callbacks=[self.reject, self._applyChanges, self._okButton], texts=['Cancel', 'Apply', 'Ok'])

  ######### Widget Callbacks #########

  def _getCallBacksDict(self):
    return {
            self._typeComponent: str(self.typePulldownList.get()),
            self._concentrationChanged: self._getConcentrationValue(),
            self._concentrationUnitChanged: str(self.concentrationUnitPulldownList.get()),
            self._commentChanged: str(self.commentLineEdit.text())
            }

  def _getConcentrationValue(self):

    try:
      value = float(self.concentrationLineEdit.text())
      return value
    except:
      print('Concentration error: \n Value must be flot or int.')
      # info = showInfo('Concentration error', 'Value must be a flot or int')


  def _typeComponent(self, value):
    if value:
      self.sampleComponent.role = value

  def _concentrationUnitChanged(self, value):
    if value:
      self.sampleComponent.concentrationUnit = value

  def _concentrationChanged(self, value):
    if value:
      self.sampleComponent.concentration = float(value)

  def _commentChanged(self, value):
    if value:
      self.sampleComponent.comment = str(value)

  def _createNewComponent(self):
    if not self.sampleComponent:
      self.sampleComponent =  self.sample.newSampleComponent(
        name=str(self.nameComponentLineEdit.text()), labeling=self.labelingLineEdit.text())

  def _updateButtons(self):
    checkMissingValues = [self.nameComponentLineEdit.text(),  self.labelingLineEdit.text()]
    for isNotMissingValue in checkMissingValues:
      if isNotMissingValue:
        self.buttons.buttons[1].setEnabled(True)
        self.buttons.buttons[2].setEnabled(True)
      else:
        self.buttons.buttons[1].setEnabled(False)
        self.buttons.buttons[2].setEnabled(False)

  def _applyChanges(self):
    if self.newSampleComponentToCreate :
      self._createNewComponent()
    for property, value in self._getCallBacksDict().items():
      property(value)

  def _okButton(self):
    self._applyChanges()
    self.accept()

  def keyPressEvent(self, event):
    if event.key() == QtCore.Qt.Key_Enter:
      self._okButton()
    if event.key() == QtCore.Qt.Key_Escape:
      self.reject()
