from PyQt4 import QtCore, QtGui
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.ListWidget import ListWidget
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.ButtonList import ButtonList



class SpectrumGroupEditor(QtGui.QDialog):
  def __init__(self, parent=None, project=None, spectrumGroup=None,   **kw):
    super(SpectrumGroupEditor, self).__init__(parent)

    self.project = project

    if spectrumGroup is not None:
      self.spectrumGroup = spectrumGroup

    self.colourScheme = project._appBase.preferences.general.colourScheme

    ###### Main Layout ######
    self.mainLayout = QtGui.QGridLayout()
    self.setLayout(self.mainLayout)
    self.setWindowTitle("Spectrum Group Setup")

    ###### Left widgets ######
    self.leftSpectrumGroupLabel = Label(self, 'Spectrum GroupName')
    # self.leftSpectrumGroupLabel.setFixedWidth(150)
    self.leftSpectrumGroupsLabel = Label(self, 'Spectrum Groups')
    self.leftSpectrumGroupLineEdit = LineEdit(self, self.spectrumGroup.name)
    self.leftSpectrumGroupLineEdit.editingFinished.connect(self._changeLeftSpectrumGroupName)
    self.leftSpectrumGroupLineEdit.setFixedWidth(160)
    self.leftPullDownSelection = PulldownList(self,)
    self.leftPullDownSelection.setData(self._getLeftPullDownSelectionData())
    self.leftPullDownSelection.activated[str].connect(self._leftPullDownSelectionAction)
    self.leftPullDownSelection.setFixedWidth(160)
    self.spectrumGroupListWidgetLeft = ListWidget(self)
    self.spectrumGroupListWidgetLeft.setAcceptDrops(True)

    ###### Right widgets ######
    self.rightSelectionLabel = Label(self, 'Select an option')
    self.rightPullDownSelection = PulldownList(self,)
    self.rightPullDownSelection.setData(self._getRightPullDownSelectionData())
    self.rightPullDownSelection.activated[str].connect(self._rightPullDownSelectionAction)
    self.rightPullDownSelection.setFixedWidth(160)

    self.rightSpectrumGroupLabel = Label(self, 'SpectrumGroupName')
    self.rightSpectrumGroupLabel.setFixedWidth(160)
    self.rightSpectrumGroupLineEdit = LineEdit(self,'NewSpectrumGroup')
    self.rightSpectrumGroupLineEdit.editingFinished.connect(self._changeRightSpectrumGroupName)
    self.rightSpectrumGroupLineEdit.setFixedWidth(160)

    self.spectrumGroupListWidgetRight = ListWidget(self)
    self.spectrumGroupListWidgetRight.setAcceptDrops(False)
    self.applyButtons = ButtonList(self, texts = ['Close', 'Cancel','Apply'],
                                   callbacks=[self.reject, self._cancelNewSpectrumGroup, self._applyNewSpectrumGroup],
                                   icons=[None,None,None],
                                   tipTexts=['close pop up', 'cancel the last action',None], direction='h', hAlign='r')
    self._disableButtons() #disabled until any change occurs


    ###### Add left Widgets on Main layout ######

    self.mainLayout.addWidget(self.leftSpectrumGroupsLabel, 0,0)
    self.mainLayout.addWidget(self.leftPullDownSelection, 0,1)
    self.mainLayout.addWidget(self.leftSpectrumGroupLabel, 1,0)
    self.mainLayout.addWidget(self.leftSpectrumGroupLineEdit, 1,1)
    self.mainLayout.addWidget(self.spectrumGroupListWidgetLeft, 2,0,2,2)

    ###### Add Right Widgets on Main layout ######

    self.mainLayout.addWidget(self.rightSelectionLabel, 0,2)
    self.mainLayout.addWidget(self.rightPullDownSelection, 0,3)
    self.mainLayout.addWidget(self.rightSpectrumGroupLabel, 1,2)
    self.mainLayout.addWidget(self.rightSpectrumGroupLineEdit, 1,3)
    self.mainLayout.addWidget(self.spectrumGroupListWidgetRight, 2,2,2,2)
    self.mainLayout.addWidget(self.applyButtons, 4,3)
    self.rightSpectrumGroupLabel.hide()
    self.rightSpectrumGroupLineEdit.hide()

    self._populateListWidgetLeft()
    self._initialLabelListWidgetRight()

  def _populateListWidgetLeft(self):
    self.spectrumGroupListWidgetLeft.clear()
    for spectrum in self.spectrumGroup.spectra:
      item = QtGui.QListWidgetItem(str(spectrum.id))
      self.spectrumGroupListWidgetLeft.addItem(item)
    self.connect(self.spectrumGroupListWidgetLeft, QtCore.SIGNAL("dropped"), self._changeButtonStatus)

  def _populateListWidgetRight(self, spectra=None):
    self.spectrumGroupListWidgetRight.clear()
    if spectra is None:
      for spectrum in self._getRightPullDownSpectrumGroup().spectra:
        item = QtGui.QListWidgetItem(str(spectrum.id))
        self.spectrumGroupListWidgetRight.addItem(item)
    else:
      for spectrum in spectra:
        item = QtGui.QListWidgetItem(str(spectrum.id))
        self.spectrumGroupListWidgetRight.addItem(item)

    self.connect(self.spectrumGroupListWidgetRight, QtCore.SIGNAL("dropped"), self._changeButtonStatus)

  def _leftPullDownSelectionAction(self, selected):
    self.selected = self.project.getByPid(selected)
    if self.selected == self.spectrumGroup:
      self.spectrumGroupListWidgetLeft.clear()
      self._populateListWidgetLeft()
      self.rightPullDownSelection.setData(self._getRightPullDownSelectionData())
      self._selectAnOptionState()
      self.leftSpectrumGroupLineEdit.setText(self.spectrumGroup.name)
      self.leftSpectrumGroupLineEdit.editingFinished.connect(self._changeLeftSpectrumGroupName)

    else:
      self.spectrumGroup = self.selected
      self.spectrumGroupListWidgetLeft.clear()
      self.spectrumGroupListWidgetRight.clear()
      self._populateListWidgetLeft()
      self.rightPullDownSelection.setData(self._getRightPullDownSelectionData())
      self._selectAnOptionState()
      self.leftSpectrumGroupLineEdit.setText(self.spectrumGroup.name)
      self.leftSpectrumGroupLineEdit.editingFinished.connect(self._changeLeftSpectrumGroupName)


  def _rightPullDownSelectionAction(self, selected):
    if selected is not None:
      if selected == 'New SpectrumGroup':
        self.spectrumGroupListWidgetRight.clear()
        self.spectrumGroupListWidgetRight.setAcceptDrops(True)
        self.rightSpectrumGroupLabel.show()
        self.rightSpectrumGroupLineEdit.show()

      elif selected == ' ':
        self.spectrumGroupListWidgetRight.clear()
        self.spectrumGroupListWidgetRight.setAcceptDrops(False)
        self._initialLabelListWidgetRight()

      elif selected == 'All Spectra':
        self.spectrumGroupListWidgetRight.clear()
        self._populateListWidgetRight(self._getAllSpectra())
        print(self._getAllSpectra(), 'All Spectra')
        self.spectrumGroupListWidgetRight.setAcceptDrops(True)

      else:
        self.spectrumGroupListWidgetRight.clear()
        self.spectrumGroupListWidgetRight.setAcceptDrops(True)
        spectrumGroup = self.project.getByPid(selected)
        if spectrumGroup != self.spectrumGroup:
          self._populateListWidgetRight(spectrumGroup.spectra)

  def _initialLabelListWidgetRight(self):
    item = QtGui.QListWidgetItem('Select an option and drag/drop items across')
    item.setFlags(QtCore.Qt.NoItemFlags)
    self.spectrumGroupListWidgetRight.addItem(item)

  def _getLeftPullDownSelectionData(self):
    self.leftPullDownSelectionData = [self.spectrumGroup.pid, ]
    for spectrumGroup in self.project.spectrumGroups:
      if spectrumGroup != self.spectrumGroup:
        self.leftPullDownSelectionData.append(str(spectrumGroup.pid))
    return self.leftPullDownSelectionData

  def _getRightPullDownSelectionData(self):
    self.rightPullDownSelectionData = [' ', 'New SpectrumGroup',
                                  'All Spectra']
    for spectrumGroup in self.project.spectrumGroups:
      if spectrumGroup.pid != self.leftPullDownSelection.getText(): # self.spectrumGroup:
        self.rightPullDownSelectionData.append(str(spectrumGroup.pid))

    return self.rightPullDownSelectionData

  def _getAllSpectra(self):
    # spectra = [spectrum for spectrumGroup in self.project.spectrumGroups for spectrum in spectrumGroup.spectra]
    return self.project.spectra

  def _changeLeftSpectrumGroupName(self):
    if self.leftSpectrumGroupLineEdit.isModified():
      self.spectrumGroup.rename(self.leftSpectrumGroupLineEdit.text())

  def _changeRightSpectrumGroupName(self):
    if self.rightSpectrumGroupLineEdit.isModified():
      self.spectrumGroup.rename(self.rightSpectrumGroupLineEdit.text())

  def _getItemListWidgets(self):
    leftWidgets = []
    leftWidgetSpectra = []

    for index in range(self.spectrumGroupListWidgetLeft.count()):
      leftWidgets.append(self.spectrumGroupListWidgetLeft.item(index))
    for item in leftWidgets:
      spectrum = self.project.getByPid('SP:'+item.text())
      leftWidgetSpectra.append(spectrum)

    rightWidgets = []
    rightWidgetSpectra = []
    for index in range(self.spectrumGroupListWidgetRight.count()):
      rightWidgets.append(self.spectrumGroupListWidgetRight.item(index))
    for item in rightWidgets:
      spectrum = self.project.getByPid('SP:'+item.text())
      rightWidgetSpectra.append(spectrum)

    return {'leftWidgetSpectra':leftWidgetSpectra, 'rightWidgetSpectra':rightWidgetSpectra}

  def _applyNewSpectrumGroup(self):

    leftWidgetSpectra = self._getItemListWidgets()['leftWidgetSpectra']
    rightWidgetSpectra = self._getItemListWidgets()['rightWidgetSpectra']

    self.spectrumGroup.spectra = list(set(leftWidgetSpectra))

    if self.rightPullDownSelection.getText() == 'New SpectrumGroup':
      newSpectrumGroup1 = self.project.newSpectrumGroup(str(self.rightSpectrumGroupLineEdit.text()))
      newSpectrumGroup1.spectra = list(set(rightWidgetSpectra))
      self.leftPullDownSelection.setData(self._getLeftPullDownSelectionData())
      self._populateListWidgetLeft()
      self.rightSpectrumGroupLabel.hide()
      self.rightSpectrumGroupLineEdit.hide()
      self._selectAnOptionState()

    if self.rightPullDownSelection.getText() == ' ':
      self._populateListWidgetLeft()
      self._selectAnOptionState()
      return

    if self.rightPullDownSelection.getText() == 'All Spectra':
      self._populateListWidgetLeft()
      self._selectAnOptionState()
      return

    else:
      self._getRightPullDownSpectrumGroup().spectra = []
      self._getRightPullDownSpectrumGroup().spectra = list(set(rightWidgetSpectra))
      self._populateListWidgetLeft()
      self._selectAnOptionState()

  def _selectAnOptionState(self):
    self.rightPullDownSelection.select(' ')
    self.spectrumGroupListWidgetRight.clear()
    self.spectrumGroupListWidgetRight.setAcceptDrops(False)
    self._initialLabelListWidgetRight()
    self._disableButtons()
    self.rightSpectrumGroupLabel.hide()
    self.rightSpectrumGroupLineEdit.hide()

  def _getRightPullDownSpectrumGroup(self):
    pullDownSelection = self.rightPullDownSelection.getText()
    rightSpectrumGroup = self.project.getByPid(pullDownSelection)
    if rightSpectrumGroup is not None:
      return rightSpectrumGroup

  def _cancelNewSpectrumGroup(self):
    self._populateListWidgetLeft()
    self._selectAnOptionState()
    self._disableButtons()

  def _disableButtons(self):
    for button in self.applyButtons.buttons[1:]:
      button.setEnabled(False)
      button.setStyleSheet("background-color:#868D9D; color: #000000")


  def _changeButtonStatus(self):
    for button in self.applyButtons.buttons:
      button.setEnabled(True)
      if self.colourScheme == 'dark':
        button.setStyleSheet("background-color:#535a83; color: #bec4f3")
      else:
       button.setStyleSheet("background-color:#bd8413; color: #fdfdfc")
