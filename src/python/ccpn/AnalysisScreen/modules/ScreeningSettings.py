__author__ = 'luca'

from collections import OrderedDict

from PyQt4 import QtCore, QtGui

from ccpn.AnalysisScreen.modules import ScreeningPipeline as sp
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Module import CcpnModule
from ccpn.ui.gui.widgets.GroupBox import GroupBox
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea

Qt = QtCore.Qt
Qkeys = QtGui.QKeySequence

class ScreeningSettings(CcpnModule):
  def __init__(self, parent=None, project=None, **kw):
    super(ScreeningSettings, self)
    CcpnModule.__init__(self, name='Screening Settings')
    self.project = project


    self.mainWindow = parent
    self.moduleArea = self.mainWindow.moduleArea
    self.application = self.mainWindow.application
    self.generalPreferences = self.application.preferences.general
    self.colourScheme = self.generalPreferences.colourScheme

    self.mainFrame = QtGui.QFrame()
    self.mainLayout = QtGui.QVBoxLayout()
    self.mainFrame.setLayout(self.mainLayout)
    self.layout.addWidget(self.mainFrame, 0,0,0,0)

    self.pipelineMainGroupBox = GroupBox()
    self.pipelineMainVLayout = QtGui.QVBoxLayout()
    self.pipelineMainVLayout.setAlignment(QtCore.Qt.AlignTop)
    self.setLayout(self.pipelineMainVLayout)

    self.pipelineMainGroupBox.setLayout(self.pipelineMainVLayout)
    self.scrollArea = ScrollArea(self)
    # self.scrollArea.setFixedHeight(200)
    self.scrollArea.setWidget(self.pipelineMainGroupBox)
    self.scrollArea.setWidgetResizable(True)
    self.widget0 = (PipelineWidgets(self, project))
    self.widget1 = (PipelineWidgets(self, project))
    self.widget2 = (PipelineWidgets(self, project))
    self.pipelineMainVLayout.addWidget(self.widget0)
    self.pipelineMainVLayout.addWidget(self.widget1)
    self.pipelineMainVLayout.addWidget(self.widget2)
    # self.pipelineMainVLayout.addWidget(Display1DWidget(project=project))
    # self.goArea = GoArea(self, project)
    # self.pipelineMainVLayout.addWidget(self.goArea)
    # self.mainLayout.addWidget(self.scrollArea)
    # self.mainLayout.addWidget(self.goArea, 0)

    self.widget0._addMethod('Create std difference spectrum')
    self.widget0.pulldownAction.select('Create std difference spectrum')
    self.widget1._addMethod('Peak Picking')
    self.widget1.pulldownAction.select('Peak Picking')
    self.widget2._addMethod('Match Peaks')
    self.widget2.pulldownAction.select('Match Peaks')


class GoArea(QtGui.QWidget):

  def __init__(self, parent=None, project=None, **kw):
    super(GoArea, self).__init__(parent)

    self.current = project._appBase.current
    self.project = project

    self.goAreaFrame = QtGui.QFrame()
    self.goAreaLayout = QtGui.QHBoxLayout()
    self.goAreaFrame.setLayout(self.goAreaLayout)


    self.label = Label(self, 'Pipeline Name')
    self.current = project._appBase.current
    self.project = project
    self.lineEdit = LineEdit(self,)
    self.lineEdit.setText('ds1')
    self.pipelineName = self.lineEdit.text()
    self.lineEdit.editingFinished.connect(self._renamePipeline)
    self.spectrumGroupLabel = Label(self, 'Input Data ', )
    self.spectrumGroupPulldown = PulldownList(self, callback=self._currentSpectrumGroup)
    spectrumGroups = [spectrumGroup.pid for spectrumGroup in project.spectrumGroups]
    self.spectrumGroupPulldown.setData(spectrumGroups)
    self.current.spectrumGroup = self.project.getByPid(self.spectrumGroupPulldown.currentText())
    self.autoUpdateBox = CheckBox(self, checked=False)
    # self.autoUpdateBox.setChecked(True)
    # self.autoUpdateLabel = Label(self, 'Auto', )
    # self.goButton = Button(self, 'Go')
    # self.goButton.clicked.connect(self.showHitsModule)

    self.goAreaLayout.addWidget(self.lineEdit)
    self.goAreaLayout.addWidget(self.spectrumGroupLabel)
    self.goAreaLayout.addWidget(self.spectrumGroupPulldown)
    self.goAreaLayout.addWidget(self.autoUpdateBox)
    self.goAreaLayout.addWidget(self.goButton)


  def _currentSpectrumGroup(self):
    self.current.spectrumGroup = self.project.getByPid(self.spectrumGroupPulldown.currentText())


  def _renamePipeline(self):
    self.pipelineName = self.lineEdit.text()


class PipelineWidgets(QtGui.QWidget):
  '''
  '''
  def __init__(self, parent=None, project=None, **kw):
    super(PipelineWidgets, self).__init__(parent)

    self.project = project
    self.pullDownData = OrderedDict((
      ('< Select Method >', None),
      ('Recent Settings', None),
      ('Select Experiment Type', None),
      ('Create std difference spectrum', sp.StdSpectrumCreator(self, self.project)),
      ('Noise Threshold', sp.ExcludeBaselinePoints(self, self.project)),
      ('Exclude Regions', sp.ExcludeRegions(self)),
      ('Peak Picking',sp.PickPeaksWidget(self, self.project)),
      ('Match Peaks', sp.MatchPeaks(self, self.project)),
      ))


    self.moveUpRowIcon = Icon('icons/sort-up')
    self.moveDownRowIcon = Icon('icons/sort-down')
    self.addRowIcon = Icon('icons/plus')
    self.removeRowIcon = Icon('icons/minus')

    self.mainWidgets = GroupBox(self)
    self.mainWidgets.setFixedHeight(60)

    self.mainWidgets_layout = QtGui.QHBoxLayout(self.mainWidgets)
    # self.mainWidgets_layout.setContentsMargins(0, 0, 0, 0)#(left, top, right, bottom)

    self.pulldownAction = PulldownList(self,)
    self.pulldownAction.setFixedWidth(130)
    self.pulldownAction.setFixedHeight(25)

    pdData = list(self.pullDownData.keys())
    self.selectMethod = '< Select Method >'

    self.pulldownAction.setData(pdData)
    self.pulldownAction.activated[str].connect(self._addMethod)

    self.checkBox = CheckBox(self, text='active', checked=True)

    self.moveUpDownButtons = ButtonList(self, texts = ['︎','︎︎'], callbacks=[self._moveRowUp, self._moveRowDown], icons=[self.moveUpRowIcon, self.moveDownRowIcon],
                                        tipTexts=['Move row up', 'Move row down'], direction='h', hAlign='r')
    self.moveUpDownButtons.setFixedHeight(40)
    self.moveUpDownButtons.setFixedWidth(40)
    self.moveUpDownButtons.setStyleSheet('font-size: 15pt')

    self.addRemoveButtons = ButtonList(self, texts = ['',''], callbacks=[self._addRow, self._removeRow], icons=[self.addRowIcon, self.removeRowIcon],
                                       tipTexts=['Add new row', 'Remove row '], direction='H', hAlign='l')
    self.addRemoveButtons.setStyleSheet('font-size: 15pt')
    self.addRemoveButtons.setFixedHeight(40)
    self.addRemoveButtons.setFixedWidth(40)

    self.mainWidgets_layout.addWidget(self.pulldownAction,)
    self.mainWidgets_layout.addWidget(self.checkBox,)

    self.mainWidgets_layout.addWidget(self.moveUpDownButtons,)
    self.mainWidgets_layout.addWidget(self.addRemoveButtons,)
    self.addRemoveButtons.buttons[0].setEnabled(False)


  def _addMethod(self, selected):
    self._updateLayout()
    obj = self.pullDownData[selected]
    if obj is not None:
      self.mainWidgets_layout.insertWidget(2, obj, 1)
      mainVboxLayout = obj.parent().parent().parent().layout()
      items = [mainVboxLayout.itemAt(i) for i in range(mainVboxLayout.count())]
      self._enableAddButton(items)

    if selected == 'Exclude Regions':
      self.mainWidgets.setFixedHeight(200)
    else:
      self.mainWidgets.setFixedHeight(60)


  def _updateLayout(self):
    layout = self.mainWidgets_layout
    item = layout.itemAt(2)
    if item.widget() is not self.moveUpDownButtons:
      item.widget().hide()
      layout.removeItem(item)


  def _moveRowUp(self):
    '''
    obj => sender = button, parent1= buttonList, parent2= GroupBox1, parent3=PipelineWidgets obj
    objLayout is the main parent layout (VLayout)
    '''
    obj = self.sender().parent().parent().parent()
    objLayout = obj.parent().layout()
    currentPosition = objLayout.indexOf(obj)
    newPosition = max(currentPosition-1, 0)
    objLayout.insertWidget(newPosition, obj)

  def _moveRowDown(self):
    '''
    obj as above
    objLayout is the main parent layout (VLayout)
    '''

    obj = self.sender().parent().parent().parent()
    objLayout = obj.parent().layout()
    currentPosition = objLayout.indexOf(obj)
    newPosition = min(currentPosition+1, objLayout.count()-1)
    objLayout.insertWidget(newPosition, obj)

  def _addRow(self):
    '''
    This function will add a new Pipelinewidgets obj in the next row below the clicked button.
    '''

    newObj = (PipelineWidgets(self, self.project))
    obj = self.sender().parent().parent().parent()
    objLayout = obj.parent().layout()
    currentPosition = objLayout.indexOf(obj)
    newPosition = min(currentPosition+1, objLayout.count())
    objLayout.insertWidget(newPosition, newObj)

    items = [objLayout.itemAt(i) for i in range(objLayout.count())]
    self._disableAddButton(items)


  def _disableAddButton(self, items):
    '''
    If there is empty row with no method selected, will disable all the addButtons in each other row
    '''
    for i in items:
      if i.widget().pulldownAction.getText() == '< Select Method >':
        for i in items:
          i.widget().addRemoveButtons.buttons[0].setEnabled(False)


  def _enableAddButton(self, items):
    '''
    If a method is selected, will enable all the addButtons in each other row
    '''
    for i in items:
      i.widget().addRemoveButtons.buttons[0].setEnabled(True)


  def _removeRow(self):
    '''
    This function will remove the Pipelinewidgets selected from the main parent layout (VLayout)
    '''

    obj = self.sender().parent().parent().parent()
    objLayout = obj.parent().layout()
    currentPosition = objLayout.indexOf(obj)

    if objLayout.count() == 1 and currentPosition == 0:
      pass

    else:
      obj.deleteLater()
