import collections
import json
import time
from collections import OrderedDict
from ccpn.core.lib.Notifiers import Notifier
from ccpn.core.Spectrum import Spectrum
from ccpn.core.SpectrumGroup import SpectrumGroup

import pandas as pd
from PyQt4 import QtCore, QtGui
from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.FileDialog import FileDialog
from ccpn.ui.gui.widgets.GroupBox import GroupBox
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PipelineWidgets import PipelineDropArea
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.ListWidget import ListWidget
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.DropBase import DropBase


Qt = QtCore.Qt
Qkeys = QtGui.QKeySequence

# styleSheets
transparentStyle = "background-color: transparent; border: 0px solid transparent"
selectMethodLabel = '< Select Method >'


class PipelineWorker(QtCore.QObject):
  'Object managing the  auto run pipeline simulation'

  stepIncreased = QtCore.pyqtSignal(int)

  def __init__(self):
    super(PipelineWorker, self).__init__()
    self._step = 0
    self._isRunning = True
    self._maxSteps = 200000

  def task(self):
    if not self._isRunning:
      self._isRunning = True
      self._step = 0

    while self._step < self._maxSteps and self._isRunning == True:
      self._step += 1
      self.stepIncreased.emit(self._step)
      time.sleep(0.1)  # if this time is too small or disabled you won't be able to stop the thread!

  def stop(self):
    self._isRunning = False
    print('Pipeline Thread stopped')


class GuiPipeline(CcpnModule):

  includeSettingsWidget = True
  maxSettingsState = 2
  settingsPosition = 'left'
  className = 'GuiPipeline'

  def __init__(self, mainWindow, name='', pipelineMethods=None, templates=None, appSpecificMethods=True, **kw):
    super(GuiPipeline, self)

    self.project = None
    self.application = None

    if mainWindow is not None:
      self.mainWindow = mainWindow
      self.project = self.mainWindow.project
      self.application = self.mainWindow.application
      self.moduleArea = self.mainWindow.moduleArea
      self.preferences = self.application.preferences
      self.current = self.application.current
      self._spectrumNotifier = Notifier(self.project, [Notifier.CREATE, Notifier.DELETE], 'Spectrum',
                                        self._refreshInputDataList)

      nameCount = 0

      for module in self.mainWindow.moduleArea.findAll()[1].values():
        if hasattr(module, 'runPipeline'):
          nameCount += 1

      name = 'Pipeline-' + str(nameCount)
      self.generalPreferences = self.application.preferences.general
      self.templatePath = self.generalPreferences.auxiliaryFilesPath

    self.currentPipelineBoxNames = []
    self.pipelineSettingsParams = OrderedDict([('name', 'NewPipeline'),
                                               ('rename', 'NewPipeline'),
                                               ('savePath', None), #str(self.generalPreferences.dataPath)),
                                               ('autoRun', False),('addPosit', 'bottom'),
                                               ('autoActive', True),])

    self.templates = self._getPipelineTemplates(templates)
    self.pipelineMethods = self._getPipelineMethods(pipelineMethods)

    CcpnModule.__init__(self, mainWindow=mainWindow, name=name)

    self._setIcons()
    self._setMainLayout()
    self._setPipelineThread()
    self._setSecondaryLayouts()
    if appSpecificMethods:
      self.methodsPreferences = self._setAppSpecificMethods('AnalysisScreen')
    self.pipelineWorker.stepIncreased.connect(self.runPipeline)
    self.currentRunningPipeline = []

    self.interactor = PipelineInteractor(self.application)


  def _setModuleName(self):
    pipelineModules = []
    for module in self.mainWindow.moduleArea.findAll()[1].values():
      if hasattr(module, 'GuiPipeline'):
        print('GuiPipeline')
      if hasattr(module, 'runPipeline'):
        print('runPipeline')
      if isinstance(module, self):
        print('isIST')


  def _getPipelineMethods(self, methods):
    '''
    methods = {name: object}
    name = str will appear in the method pulldown
    obj = any subclass of pipeline Box
    '''
    if methods is not None:
      all = []
      for method in methods:
        i = (method.methodName(method), method)
        all.append(i)
      return dict(all)

    else:
      return {}

  def _getPipelineTemplates(self, templates):
    if templates is not None:
      return templates
    else:
      return {'Empty':'Empty'}

  def _setAppSpecificMethods(self, applicationName):
    '''set data in pull down if selected application specific method '''
    filteredMethod = [selectMethodLabel,]
    for method in self.pipelineMethods.values():
      if hasattr(method, 'applicationsSpecific'):
        applicationsSpecific = method.applicationsSpecific(method)
        if applicationName in applicationsSpecific:
          filteredMethod.append(method.methodName(method))
    self.methodPulldown.setData(sorted(filteredMethod))

  def keyPressEvent(self, KeyEvent):

    if KeyEvent.key() == Qt.Key_Enter:
      self.runPipeline()

  def _setIcons(self):
    self.settingIcon = Icon('icons/applications-system')
    self.saveIcon = Icon('icons/save')
    self.openRecentIcon = Icon('icons/document_open_recent')
    self.goIcon = Icon('icons/play')
    self.stopIcon = Icon('icons/stop')
    self.filterIcon = Icon('icons/edit-find')


  def _setMainLayout(self):
    self.mainFrame = Frame(self.mainWidget, setLayout=False)
    self.mainLayout = QtGui.QVBoxLayout()
    self.mainFrame.setLayout(self.mainLayout)
    self.mainWidget.getLayout().addWidget(self.mainFrame, 0, 0, 0 ,0)

  def _setSecondaryLayouts(self):
    self.settingFrameLayout = QtGui.QHBoxLayout()
    self.goAreaLayout = QtGui.QHBoxLayout()
    self.pipelineAreaLayout = QtGui.QHBoxLayout()
    self.mainLayout.addLayout(self.settingFrameLayout)
    self.mainLayout.addLayout(self.goAreaLayout)
    self.mainLayout.addLayout(self.pipelineAreaLayout)
    self._createSettingButtonGroup()
    self._createPipelineWidgets()
    self._createSettingWidgets()

  def _createSettingButtonGroup(self):
    self.pipelineNameLabel = Label(self, 'NewPipeline')
    self.settingButtons = ButtonList(self, texts=['', ''],
                                     callbacks=[self._openSavedPipeline, self._savePipeline],
                                     icons=[self.openRecentIcon, self.saveIcon],
                                     tipTexts=['', ''], direction='H')
    self.settingFrameLayout.addWidget(self.pipelineNameLabel)

    self._addMenuToOpenButton()
    self.settingButtons.setStyleSheet(transparentStyle)
    self.settingFrameLayout.addStretch(1)
    self.settingFrameLayout.addWidget(self.settingButtons)

  def _setPipelineThread(self):
    self.pipelineThread = QtCore.QThread()
    self.pipelineThread.start()
    self.pipelineWorker = PipelineWorker()
    self.pipelineWorker.moveToThread(self.pipelineThread)

  def openJsonFile(self, path):
    if path is not None:
      with open(str(path), 'r') as jf:
        data = json.load(jf)
      return data

  def _getPathFromDialogBox(self):
    dialog = FileDialog(self, text="Open Pipeline",
                        acceptMode=FileDialog.AcceptOpen)
    return dialog.selectedFile()

  def _getPipelineBoxesFromFile(self, params, boxesNames):
    pipelineBoxes = []
    for i in params:
      for key, value in i.items():
        if value[0].upper() in boxesNames:
          pipelineMethod = self.pipelineMethods[key]
          pipelineBox = pipelineMethod(parent=self, application=self.application, name = value[0], params = value[1])
          pipelineBox.setActive(value[2])
          pipelineBoxes.append(pipelineBox)
    return pipelineBoxes

  def _openSavedPipeline(self):

    path = self._getPathFromDialogBox()
    state, params, boxesNames, pipelineSettings = self.openJsonFile(path)
    pipelineBoxes = self._getPipelineBoxesFromFile(params, boxesNames)
    self._closeExistingPipelineBoxes()
    for pipelineBox in pipelineBoxes:
      self.pipelineArea.addBox(pipelineBox)
    self.pipelineArea.restoreState(state)
    self.pipelineSettingsParams = OrderedDict(pipelineSettings)
    self._setSettingsParams()

  def _addMenuToOpenButton(self):
    openButton = self.settingButtons.buttons[0]
    menu = QtGui.QMenu()
    templatesItem = menu.addAction('Templates')
    subMenu = QtGui.QMenu()
    if self.templates is not None:
      for item in self.templates.keys():
        templatesSubItem = subMenu.addAction(item)
      openItem = menu.addAction('Open...', self._openSavedPipeline)
      templatesItem.setMenu(subMenu)
    openButton.setMenu(menu)

  def _closeExistingPipelineBoxes(self):
    boxes = self.pipelineArea.findAll()[1].values()
    if len(boxes)>0:
      for box in boxes:
        box.closeBox()

  def _savePipeline(self):
    '''jsonData = [{pipelineArea.state}, [boxes widgets params], [currentBoxesNames], pipelineSettingsParams]   '''
    currentBoxesNames = list(self.pipelineArea.findAll()[1].keys())
    if len(currentBoxesNames)>0:
      self.jsonData = []
      self.widgetsParams = self._pipelineBoxesWidgetParams(currentBoxesNames)
      self.jsonData.append(self.pipelineArea.saveState())
      self.jsonData.append(self.widgetsParams)
      self.jsonData.append(currentBoxesNames)
      self.jsonData.append(list(self.pipelineSettingsParams.items()))

      self._saveToJson()

  def _saveToJson(self):
    self.jsonPath = str(self.savePipelineLineEdit.text()) + '/' + str(self.pipelineNameLabel.text()) + '.json'
    with open(self.jsonPath, 'w') as fp:
      json.dump(self.jsonData, fp, indent=2)
      fp.close()
    print('File saved in: ', self.jsonPath)

  def _createPipelineWidgets(self):
    self._addMethodPullDownWidget()
    self._addGoButtonWidget()
    self._addPipelineDropArea()

  def _addMethodPullDownWidget(self):
    self.methodPulldown = PulldownList(self, )
    self.methodPulldown.setMinimumWidth(200)
    self.goAreaLayout.addWidget(self.methodPulldown)
    self.setMethodPullDownData()
    self.methodPulldown.installEventFilter(self)

  def setMethodPullDownData(self):
    self.methodPulldownData = [k for k in sorted(self.pipelineMethods.keys())]
    self.methodPulldownData.insert(0, selectMethodLabel)
    self.methodPulldown.setData(self.methodPulldownData)
    self.methodPulldown.activated[str].connect(self._selectMethod)

  def eventFilter(self, source, event):
    '''Filter to disable the wheel event in the methods pulldown. Otherwise each scroll would add a box!'''
    if event.type() == QtCore.QEvent.Wheel:
      return True
    return False

  def _addGoButtonWidget(self):
    '''
    First Two button are reserved for autoRun mode. They are hidden if the setting autoRun is not checked.
    NB the stop callback needs to be a lambda call

    '''
    self.goButton = ButtonList(self, texts=['','',''],icons=[self.stopIcon, self.goIcon, self.goIcon,],
                               callbacks=[lambda:self.pipelineWorker.stop(), self.pipelineWorker.task, self.runPipeline],
                               hAlign='c')
    self.goButton.buttons[0].hide()
    self.goButton.buttons[1].hide()
    self.goButton.setStyleSheet(transparentStyle)
    self.goAreaLayout.addWidget(self.goButton, )
    self.goAreaLayout.addStretch(1)

  def _addPipelineDropArea(self):
    self.pipelineArea = PipelineDropArea()
    scroll = ScrollArea(self)
    scroll.setWidget(self.pipelineArea)
    scroll.setWidgetResizable(True)
    self.pipelineAreaLayout.addWidget(scroll)



  def runPipeline(self):
    self.currentRunningPipeline = []
    if len(self.pipelineArea.findAll()[1])>0:
      boxes = self.pipelineArea.orderedBoxes(self.pipelineArea.topContainer)
      for box in boxes:
        if box.isActive() and hasattr(box, 'runMethod'):
          result = box.runMethod()
          method = (box, result)
          self.currentRunningPipeline.append(method)


  def _selectMethod(self, selected):

    if str(selected) == selectMethodLabel:
      return

    boxName = self._getSerialName(str(selected))
    self._addMethodBox(boxName, selected)
    self.methodPulldown.setIndex(0)

  def _getSerialName(self, boxName):
    self.currentPipelineBoxNames.append(boxName)
    count = len(self.pipelineArea.findAll()[1])
    if count == 0:
      self.currentPipelineBoxNames = []
    counter = collections.Counter(self.currentPipelineBoxNames)
    return str(boxName) + '-' + str(counter[str(boxName)])


  def _addMethodBox(self, name, selected):

    objMethod = self.pipelineMethods[selected]
    position = self.pipelineSettingsParams['addPosit']

    self.pipelineWidget = objMethod(parent=self, application=None, name=name, params=None, project=self.project)

    self.pipelineArea.addDock(self.pipelineWidget, position=position)
    autoActive = self.pipelineSettingsParams['autoActive']
    self.pipelineWidget.label.checkBox.setChecked(autoActive)


  ''' PIPELINE SETTINGS '''

  def _pipelineBoxesWidgetParams(self, currentBoxesNames):
    self.savePipelineParams = []
    for boxName in currentBoxesNames:
      boxMethod = self.pipelineArea.docks[str(boxName)]
      state = boxMethod.isActive()
      params = boxMethod.getWidgetsParams()
      newDict = {boxMethod.methodName(): (boxName, params, state)}
      self.savePipelineParams.append(newDict)
    return self.savePipelineParams


  def _createSettingWidgets(self):
    self.settingsWidgets = []
    self._createSettingsGroupBox()
    self._createAllSettingWidgets()
    self._addWidgetsToLayout(self.settingsWidgets, self.settingWidgetsLayout)
    # self.settingFrame.hide()
    # self._hideSettingWidget()
    self._setSettingsParams()

  def _createSettingsGroupBox(self):
    self.settingFrame = Frame(self, setLayout=False)
    self.settingFrame.setMaximumWidth(300)
    self.settingWidgetsLayout = QtGui.QGridLayout()
    self.settingFrame.setLayout(self.settingWidgetsLayout)
    self.settingsWidget.getLayout().addWidget(self.settingFrame)

  def _createAllSettingWidgets(self):
    #
    self.pipelineReNameLabel = Label(self, 'Name')
    self.settingsWidgets.append(self.pipelineReNameLabel)
    self.pipelineReNameTextEdit = LineEdit(self, str(self.pipelineNameLabel.text()))
    self.settingsWidgets.append(self.pipelineReNameTextEdit)
    #

    self.inputDataLabel = Label(self, 'Input Data')
    self.settingsWidgets.append(self.inputDataLabel)
    self.inputDataList = ListWidget(self, )
    self.inputDataList.setAcceptDrops(True)

    # self.inputDataList.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
    self.setInputDataList(self.getInputData())
    self.settingsWidgets.append(self.inputDataList)

    #
    self.autoLabel = Label(self, 'Auto Run')
    self.settingsWidgets.append(self.autoLabel)
    self.autoCheckBox = CheckBox(self,)
    self.settingsWidgets.append(self.autoCheckBox)
    #
    self.savePipelineLabel = Label(self, 'Save in')
    self.settingsWidgets.append(self.savePipelineLabel)
    self.savePipelineLineEdit = LineEdit(self, '')
    self.settingsWidgets.append(self.savePipelineLineEdit)
    #
    self.addBoxLabel = Label(self, 'Add Method On')
    self.settingsWidgets.append(self.addBoxLabel)
    self.addBoxPosition = RadioButtons(self,texts=['top', 'bottom'], selectedInd=0,direction='h')
    self.addBoxPosition.setMaximumHeight(20)
    self.settingsWidgets.append(self.addBoxPosition)
    #
    self.autoActiveLabel = Label(self, 'Auto active')
    self.settingsWidgets.append(self.autoActiveLabel)
    self.autoActiveCheckBox = CheckBox(self, )
    self.autoActiveCheckBox.setChecked(True)
    self.settingsWidgets.append(self.autoActiveCheckBox)

    #
    self.filter = Label(self, 'Methods filter')
    self.settingsWidgets.append(self.filter)
    self.filterButton = Button(self, icon = self.filterIcon, callback = self.filterMethodPopup)
    self.filterButton.setStyleSheet(transparentStyle)
    self.settingsWidgets.append(self.filterButton)

    #
    self.spacerLabel = Label(self, '')
    self.spacerLabel.setMaximumHeight(1)
    self.settingsWidgets.append(self.spacerLabel)
    self.applyCancelsettingButtons = ButtonList(self, texts=['Cancel', 'Apply'], callbacks=[self._cancelSettingsCallBack, self._applySettingsCallBack],
                                                direction='H', hAlign='c')
    self.settingsWidgets.append(self.applyCancelsettingButtons)


  def settingsPipelineWidgets(self):
    if self.settingFrame.isHidden():
      self._showSettingWidget()
    else:
      self._cancelSettingsCallBack()

  def _updateSettingsParams(self):
    name = str(self.pipelineReNameTextEdit.text())
    rename = str(self.pipelineReNameTextEdit.text())
    savePath = str(self.savePipelineLineEdit.text())
    autoRun = self.autoCheckBox.get()
    addPosit = self.addBoxPosition.get()
    autoActive = self.autoActiveCheckBox.get()

    params = OrderedDict([
      ('name', name),
      ('rename', rename),
      ('savePath', savePath),
      ('autoRun', autoRun),
      ('addPosit', addPosit),
      ('autoActive', autoActive)
    ])
    self.pipelineSettingsParams = params


  def _setSettingsParams(self):
    widgets = [self.pipelineNameLabel.setText, self.pipelineReNameTextEdit.setText,
               self.savePipelineLineEdit.setText, self.autoCheckBox.setChecked, self.addBoxPosition.set]

    for widget, value in zip(widgets, self.pipelineSettingsParams.values()):
      widget(value)


  def _renamePipeline(self):
    self.pipelineName = self.lineEdit.text()

  def _applySettingsCallBack(self):
    self._displayStopButton()
    self._updateSettingsParams()
    self._setSettingsParams()
    self.setDataSelection()
    # self._hideSettingWidget()

  def _cancelSettingsCallBack(self):
    self._setSettingsParams()
    # self._hideSettingWidget()

  def _hideSettingWidget(self):
    self.settingFrame.hide()
    for widget in self.settingsWidgets:
      widget.hide()

  def _showSettingWidget(self):
    self.settingFrame.show()
    for widget in self.settingsWidgets:
      widget.show()

  def _displayStopButton(self):
    if self.autoCheckBox.isChecked():
      self.goButton.buttons[0].show()
      self.goButton.buttons[1].show()
      self.goButton.buttons[2].hide()
    else:
      self.goButton.buttons[0].hide()
      self.goButton.buttons[1].hide()
      self.goButton.buttons[2].show()

  def filterMethodPopup(self):
    FilterMethods(parent=self).exec()

  def _addWidgetsToLayout(self, widgets, layout):
    count = int(len(widgets) / 2)
    self.positions = [[i + 1, j] for i in range(count) for j in range(2)]
    for position, widget in zip(self.positions, widgets):
      i, j = position
      layout.addWidget(widget, i, j)

  def setDataSelection(self):

    dataTexts = self.inputDataList.getTexts()
    if self.project is not None:
      for text in dataTexts:
        obj  = self.project.getByPid(text)
        if isinstance(obj, Spectrum) or isinstance(obj, SpectrumGroup):
          print(obj)
        else:
          print(obj, 'Not available.')


    # self.interactor.sources = [s.text() for s in self.inputDataList.selectedItems()]



  def getData(self):
    """
    Should this move to the interactors???
    """
    if self.project is not None:
      return [self.project.getByPid('SP:{}'.format(source)) for source in self.interactor.sources]
    else:
      return []

  def setInputDataList(self, inputData=None):
    self.inputDataList.clear()
    if inputData is not None:
      self.inputDataList.setObjects(inputData, name='pid')
      sdo = [s.name for s in inputData]
      self.inputDataList.addItems(sdo)


  def getInputData(self):
    '''Get 1D Spectra from project'''
    sd = []
    if self.project is not None:
      sd += [s for s in self.project.spectra if
             (len(s.axisCodes) == 1) and (s.axisCodes[0].startswith('H'))]
    return sd

  def _refreshInputDataList(self, *args):
    try:
      spectrumGroups = []
      self.setInputDataList(self.getInputData())
    except:
      print('No input data available')


class FilterMethods(CcpnDialog):

  def __init__(self, parent=None, title='Filter Methods', **kw):
    CcpnDialog.__init__(self, parent, setLayout=False, windowTitle=title, **kw)
    # super(FilterMethods, self).__init__(parent)
    self.pipelineModule = parent
    self._setMainLayout()
    self._setWidgets()
    self._addWidgetsToLayout()


  def _setMainLayout(self):
    self.mainLayout = QtGui.QGridLayout()
    self.setLayout(self.mainLayout)
    self.setWindowTitle("Filter Methods")
    self.resize(250, 300)

  def _setWidgets(self):
    self.selectLabel = Label(self, 'Select All')
    self.selectAllCheckBox = CheckBox(self, )
    self._setSelectionScrollArea()
    self._addMethodCheckBoxes()
    self.applyCancelButtons = ButtonList(self, texts=['Cancel', 'Ok'],
                                                callbacks=[self.reject, self._okButtonCallBack],
                                                direction='H')
    self.selectAllCheckBox.stateChanged.connect(self._checkAllMethods)

  def _addMethodCheckBoxes(self):
    self.allMethodCheckBoxes = []
    for i, method in enumerate(self.pipelineModule.methodPulldownData[1:]):
      self.spectrumCheckBox = CheckBox(self.scrollAreaWidgetContents, text=str(method), grid=(i + 1, 0))
      self.allMethodCheckBoxes.append(self.spectrumCheckBox)
    self.updateMethodCheckBoxes()
    self.updateSelectAllCheckBox()

  def updateMethodCheckBoxes(self):

    for method in self.pipelineModule.methodPulldown.texts:
      for cb in self.allMethodCheckBoxes:
        if cb.text() == method:
          cb.setChecked(True)

  def updateSelectAllCheckBox(self):
    for cb in self.allMethodCheckBoxes:
      if not cb.isChecked():
        return
      else:
        self.selectAllCheckBox.setChecked(True)


  def _checkAllMethods(self, state):
    if len(self.allMethodCheckBoxes)>0:
      for cb in self.allMethodCheckBoxes:
        if state == QtCore.Qt.Checked:
          cb.setChecked(True)
        else:
          cb.setChecked(False)

  def _getSelectedMethods(self):
    methods = [selectMethodLabel, ]
    for cb in self.allMethodCheckBoxes:
      if cb.isChecked():
        method = cb.text()
        methods.append(method)
    return sorted(methods)

  def _setSelectionScrollArea(self):
    self.scrollArea = ScrollArea(self)
    self.scrollArea.setWidgetResizable(True)
    self.scrollAreaWidgetContents = Frame(None, setLayout=True)
    self.scrollArea.setWidget(self.scrollAreaWidgetContents)

  def _addWidgetsToLayout(self):
    self.mainLayout.addWidget(self.selectLabel, 0,0)
    self.mainLayout.addWidget(self.selectAllCheckBox, 0, 1)
    self.mainLayout.addWidget(self.scrollArea, 1, 0, 1, 2)
    self.mainLayout.addWidget(self.applyCancelButtons, 2, 1,)

  def _okButtonCallBack(self):
    self.pipelineModule.methodPulldown.setData(self._getSelectedMethods())
    self.accept()

class PipelineInteractor:

  def __init__(self, application):
    self.project = None
    if application is not None:
      self.project = application.project
      self.sources = []

  @property
  def sources(self):
    return self.__sources

  @sources.setter
  def sources(self, value):
    self.__sources = value

  def getData(self):
    if self.project is not None:
      return [self.project.getByPid('SP:{}'.format(source))
              for source in self.sources]
    else:
      return []

  def _getDataFrame(self):
    return pd.DataFrame([x for x in self.getData()])



from collections import OrderedDict

pipelineFilesDirName = '/guiPipeline/'
templates =   OrderedDict((
                          ('Wlogsy', 'WlogsyTemplate'),
                          ('STD', 'STDTemplate'),
                          ('Broadening1H', 'Broadening1HTemplate'),
                          ('t1Rho', 't1RhoTemplate'),
                         ))




if __name__ == '__main__':
  from ccpn.ui.gui.widgets.Application import TestApplication
  from ccpn.ui.gui.widgets.CcpnModuleArea import CcpnModuleArea

  app = TestApplication()

  win = QtGui.QMainWindow()
  from ccpn.AnalysisScreen import guiPipeline as _pm
  pipelineMethods = _pm.__all__
  moduleArea = CcpnModuleArea(mainWindow=None, )
  module = GuiPipeline(mainWindow=None,  pipelineMethods=pipelineMethods, templates=templates)
  moduleArea.addModule(module)

  win.setCentralWidget(moduleArea)
  win.resize(1000, 500)
  win.setWindowTitle('Testing %s' % module.moduleName)
  win.show()

  app.start()