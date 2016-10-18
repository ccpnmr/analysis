__author__ = 'luca'

from PyQt4 import QtGui, QtCore
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.MessageDialog import showInfo
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons


TYPECOMPONENT =  ['Select', 'Compound', 'Solvent', 'Buffer', 'Target', 'Inhibitor ', 'Other']
C_COMPONENT_UNIT = ['Select', 'Molar', 'g/L', 'L/L', 'mol/mol', 'g/g']
Labelling = ['None','Type_New', '15N', '15N,13C', '15N,13C,2H', 'ILV','ILVA','ILVAT', 'SAIL', '1,3-13C- and 2-13C-Glycerol']


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
    self.setFixedHeight(300)

  def _getWidgetsToSet(self):

    return  (
            self._initialOpitionWidgets,
            self._setSubstanceWidgets,
            self.componentNameEditWidget,
            self.componentNameWidget,
            self.setLabellingWidget,
            self.currentLabellingWidget,
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
    self.nameLabellingOptions()

  def nameLabellingOptions(self):
    if self.newSampleComponentToCreate:
      self.sampleComponentNameLabel.hide()
      self.sampleComponentShowName.hide()
      self.currentLabellingLabel.hide()
      self.showCurrentLabelling.hide()
    else:
      self._editorOptionWidgets()


  def _getAllWidgets(self):
    '''
    All widgets are ordered in the way they will be added to the layout EG:
    1)Label1 -> grid 0,0  ---- 2)LineEdit1 --> grid 0,1
    In this list are excluded the 'Cancel, Apply, Ok Buttons' '''
    return (self.spacerLabel, self.selectInitialRadioButtons,
            self.substanceLabel, self.substancePulldownList,
            self.sampleComponentNewNameLabel, self.nameComponentLineEdit,
            self.sampleComponentNameLabel, self.sampleComponentShowName,
            self.sampleComponentLabellingLabel, self.labellingPulldownList,
            self.currentLabellingLabel, self.showCurrentLabelling,
            self.typeLabel, self.typePulldownList,
            self.concentrationUnitLabel, self.concentrationUnitPulldownList,
            self.concentrationLabel, self.concentrationLineEdit,
            self.labelcomment, self.commentLineEdit
           )
  def _initialOpitionWidgets(self):
    self.spacerLabel = Label(self, text="")
    self.selectInitialRadioButtons = RadioButtons(self, texts=['New', 'From Substances'],
                                                       selectedInd=1,
                                                       callback=self._initialOptionsCallBack,
                                                       direction='h',
                                                       tipTexts=None)

  def _setSubstanceWidgets(self):
    self.substanceLabel = Label(self, text="Current Substances")
    self.substancePulldownList = PulldownList(self)
    self.substancePulldownList.setMinimumWidth(210)
    if self.newSampleComponentToCreate:
      self._fillsubstancePulldownList()
      self.substancePulldownList.activated[str].connect(self._fillInfoFromSubstance)

  def componentNameEditWidget(self):
    self.sampleComponentNewNameLabel = Label(self, text="Name")
    self.nameComponentLineEdit = LineEdit(self)
    # self.nameComponentLineEdit.setMinimumWidth(216)
    self.nameComponentLineEdit.editingFinished.connect(self._updateButtons)
    self.nameComponentLineEdit.setReadOnly(False)
    self.nameComponentLineEdit.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

  def componentNameWidget(self):
    self.sampleComponentNameLabel = Label(self, text="Name")
    self.sampleComponentShowName = Label(self, text="")
    if self.sampleComponent:
      self.sampleComponentShowName.setText(self.sampleComponent.name)

  def setLabellingWidget(self):
    self.sampleComponentLabellingLabel = Label(self, text="Labelling")
    self.labellingPulldownList = PulldownList(self)
    self.labellingPulldownList.setMinimumWidth(210)
    self.labellingPulldownList.setData(Labelling)
    self.labellingPulldownList.setEnabled(False)
    self.labellingPulldownList.activated[str].connect(self._labellingSpecialCases)

  def currentLabellingWidget(self):
    self.currentLabellingLabel = Label(self, text="Labelling")
    self.showCurrentLabelling = Label(self, text="")
    if self.sampleComponent:
      self.showCurrentLabelling.setText(self.sampleComponent.labelling)

  def componentRoleWidget(self):
    self.typeLabel = Label(self,text="Role")
    self.typePulldownList = PulldownList(self)
    self.typePulldownList.setMinimumWidth(210)
    self.typePulldownList.setData(TYPECOMPONENT)
    if self.sampleComponent:
      self.typePulldownList.set(str(self.sampleComponent.role))

  def concentrationUnitWidget(self):
    self.concentrationUnitLabel = Label(self, text="Concentration Unit")
    self.concentrationUnitPulldownList = PulldownList(self)
    self.concentrationUnitPulldownList.setMinimumWidth(210)
    self.concentrationUnitPulldownList.setData(C_COMPONENT_UNIT)
    if self.sampleComponent:
      self.concentrationUnitPulldownList.set(str(self.sampleComponent.concentrationUnit))

  def concentrationWidget(self):
    self.concentrationLabel = Label(self, text="Concentration")
    self.concentrationLineEdit = LineEdit(self)
    self.concentrationLineEdit.editingFinished.connect(self._getConcentrationValue)
    self.concentrationLineEdit.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
    if self.sampleComponent:
      self.concentrationLineEdit.setText(str(self.sampleComponent.concentration))

  def _commentWidget(self):
    self.labelcomment = Label(self,text="Comment")
    self.commentLineEdit = LineEdit(self)
    self.commentLineEdit.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
    if self.sampleComponent:
      self.commentLineEdit.setText(self.sampleComponent.comment)

  def _setPerformButtonWidgets(self):
    tipTexts = ['','Click to apply changes. Name and Labelling cannot be changed once a new sample component is created','Click to apply and close']
    self.buttons = ButtonList(self, callbacks=[self.reject, self._applyChanges, self._okButton], texts=['Cancel', 'Apply', 'Ok'], tipTexts = tipTexts)

  ######### Widget Callbacks #########

  def _getCallBacksDict(self):
    return {
            self._typeComponent: str(self.typePulldownList.get()),
            self._concentrationChanged: self._getConcentrationValue(),
            self._concentrationUnitChanged: str(self.concentrationUnitPulldownList.get()),
            self._commentChanged: str(self.commentLineEdit.text())
            }

  def _initialOptionsCallBack(self):
    selected = self.selectInitialRadioButtons.get()

    if selected == 'From Substances':
      self.substanceLabel.show()
      self.substancePulldownList.show()
    else:
      self.substanceLabel.hide()
      self.substancePulldownList.hide()
      self.nameComponentLineEdit.setText('')
      self.nameComponentLineEdit.setReadOnly(False)
      self.labellingPulldownList.setEnabled(True)
      self.labellingPulldownList.set('None')
      self.substancePulldownList.set('Select an option')

  def _editorOptionWidgets(self):
    self.spacerLabel.hide()
    self.selectInitialRadioButtons.hide()
    self.substanceLabel.hide()
    self.substancePulldownList.hide()
    self.sampleComponentNewNameLabel.hide()
    self.nameComponentLineEdit.hide()
    self.sampleComponentLabellingLabel.hide()
    self.labellingPulldownList.hide()

  def _fillsubstancePulldownList(self):
    if len(self.project.substances)>0:
      substancePulldownData = ['Select an option']
      for substance in self.project.substances:
        substancePulldownData.append(str(substance.id))
      self.substancePulldownList.setData(substancePulldownData)

  def _fillInfoFromSubstance(self, selected):
    if selected != 'Select an option':
      substance = self.project.getByPid('SU:'+selected)
      self.nameComponentLineEdit.setText(str(substance.name))
      self.labellingPulldownList.set(str(substance.labelling))
      self.nameComponentLineEdit.setReadOnly(True)
      self.labellingPulldownList.setEnabled(False)
      self._updateButtons()

  def _labellingSpecialCases(self,selected ):
    if selected == 'Type_New':
      self.labellingPulldownList.setEditable(True)

    else:
      self.labellingPulldownList.setEditable(False)

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
        name=str(self.nameComponentLineEdit.text()), labelling=str(self.labellingPulldownList.currentText()))

  def _updateButtons(self):
    if self.nameComponentLineEdit.text():
      self.buttons.buttons[1].setEnabled(True)
      self.buttons.buttons[2].setEnabled(True)
    else:
      self.buttons.buttons[1].setEnabled(False)
      self.buttons.buttons[2].setEnabled(False)

  def _applyChanges(self):
    if self.newSampleComponentToCreate:
      self._createNewComponent()
    for property, value in self._getCallBacksDict().items():
      property(value)
    self.nameComponentLineEdit.setReadOnly(True)
    self.labellingPulldownList.setEnabled(False)


  def _okButton(self):
    self._applyChanges()
    self.accept()

  def keyPressEvent(self, event):
    if event.key() == QtCore.Qt.Key_Enter:
      self._okButton()
    if event.key() == QtCore.Qt.Key_Escape:
      self.reject()