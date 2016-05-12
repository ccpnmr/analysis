__author__ = 'luca'


from application.screen.modules import ScreeningPipeline as sp

from PyQt4 import QtCore, QtGui
from ccpncore.gui.Label import Label
from ccpncore.gui.GroupBox import GroupBox
from ccpncore.gui.LineEdit import LineEdit
from ccpncore.gui.ScrollArea import ScrollArea
from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.CheckBox import CheckBox
from collections import OrderedDict
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.ButtonList import ButtonList
from ccpncore.gui.Button import Button
from ccpncore.gui.Icon import Icon

Qt = QtCore.Qt
Qkeys = QtGui.QKeySequence

class ScreeningSettings(CcpnDock):
  def __init__(self, project, **kw):
    super(ScreeningSettings, self)
    CcpnDock.__init__(self, name='Screening Settings')
    self.project = project
    # self.setFixedHeight(400)
    self.dockArea = self.project._appBase.mainWindow.dockArea
    self.colourScheme = self.project._appBase.preferences.general.colourScheme

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
    self.widget = (PipelineWidgets(self, project))
    self.pipelineMainVLayout.addWidget(self.widget)
    # self.pipelineMainVLayout.addWidget(Display1DWidget(project=project))
    # self.goArea = GoArea(self, project)
    # self.pipelineMainVLayout.addWidget(self.goArea)
    # self.mainLayout.addWidget(self.scrollArea)
    # self.mainLayout.addWidget(self.goArea, 0)




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
    self.lineEdit.editingFinished.connect(self.renamePipeline)
    self.spectrumGroupLabel = Label(self, 'Input Data ', )
    self.spectrumGroupPulldown = PulldownList(self, callback=self.currentSpectrumGroup)
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


  def currentSpectrumGroup(self):
    self.current.spectrumGroup = self.project.getByPid(self.spectrumGroupPulldown.currentText())


  def renamePipeline(self):
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
      ('Match Peaks ', sp.MatchPeaks(self, self.project)),
      ))


    self.moveUpRowIcon = Icon('iconsNew/sort-up')
    self.moveDownRowIcon = Icon('iconsNew/sort-down')
    self.addRowIcon = Icon('iconsNew/plus')
    self.removeRowIcon = Icon('iconsNew/minus')

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
    self.pulldownAction.activated[str].connect(self.addMethod)

    self.checkBox = CheckBox(self, text='active', checked=True)

    self.moveUpDownButtons = ButtonList(self, texts = ['︎','︎︎'], callbacks=[self.moveRowUp, self.moveRowDown], icons=[self.moveUpRowIcon,self.moveDownRowIcon],
                                       tipTexts=['Move row up', 'Move row down'], direction='h', hAlign='r')
    self.moveUpDownButtons.setFixedHeight(40)
    self.moveUpDownButtons.setFixedWidth(40)
    self.moveUpDownButtons.setStyleSheet('font-size: 15pt')

    self.addRemoveButtons = ButtonList(self, texts = ['',''], callbacks=[self.addRow, self.removeRow],icons=[self.addRowIcon,self.removeRowIcon],
                                       tipTexts=['Add new row', 'Remove row '],  direction='H', hAlign='l' )
    self.addRemoveButtons.setStyleSheet('font-size: 15pt')
    self.addRemoveButtons.setFixedHeight(40)
    self.addRemoveButtons.setFixedWidth(40)

    self.mainWidgets_layout.addWidget(self.pulldownAction,)
    self.mainWidgets_layout.addWidget(self.checkBox,)

    self.mainWidgets_layout.addWidget(self.moveUpDownButtons,)
    self.mainWidgets_layout.addWidget(self.addRemoveButtons,)
    self.addRemoveButtons.buttons[0].setEnabled(False)


  def addMethod(self, selected):
    self.updateLayout()
    obj = self.pullDownData[selected]
    if obj is not None:
      self.mainWidgets_layout.insertWidget(2, obj, 1)
      mainVboxLayout = obj.parent().parent().parent().layout()
      items = [mainVboxLayout.itemAt(i) for i in range(mainVboxLayout.count())]
      self.enableAddButton(items)

    if selected == 'Exclude Regions':
      self.mainWidgets.setFixedHeight(200)
    else:
      self.mainWidgets.setFixedHeight(60)


  def updateLayout(self):
    layout = self.mainWidgets_layout
    item = layout.itemAt(2)
    if item.widget() is not self.moveUpDownButtons:
      item.widget().hide()
      layout.removeItem(item)


  def moveRowUp(self):
    '''
    obj => sender = button, parent1= buttonList, parent2= GroupBox1, parent3=PipelineWidgets obj
    objLayout is the main parent layout (VLayout)
    '''
    obj = self.sender().parent().parent().parent()
    objLayout = obj.parent().layout()
    currentPosition = objLayout.indexOf(obj)
    newPosition = max(currentPosition-1, 0)
    objLayout.insertWidget(newPosition, obj)

  def moveRowDown(self):
    '''
    obj as above
    objLayout is the main parent layout (VLayout)
    '''

    obj = self.sender().parent().parent().parent()
    objLayout = obj.parent().layout()
    currentPosition = objLayout.indexOf(obj)
    newPosition = min(currentPosition+1, objLayout.count()-1)
    objLayout.insertWidget(newPosition, obj)

  def addRow(self):
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
    self.disableAddButton(items)


  def disableAddButton(self, items):
    '''
    If there is empty row with no method selected, will disable all the addButtons in each other row
    '''
    for i in items:
      if i.widget().pulldownAction.getText() == '< Select Method >':
        for i in items:
          i.widget().addRemoveButtons.buttons[0].setEnabled(False)


  def enableAddButton(self, items):
    '''
    If a method is selected, will enable all the addButtons in each other row
    '''
    for i in items:
      i.widget().addRemoveButtons.buttons[0].setEnabled(True)


  def removeRow (self):
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
