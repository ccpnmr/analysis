"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:50 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtGui, QtWidgets
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.ListWidget import ListWidget
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.popups.Dialog import CcpnDialog  # ejb
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.widgets.PulldownListsForObjects import SpectrumGroupPulldown

from ccpn.util.Logging import getLogger
from ccpn.core.lib.ContextManagers import undoBlockManager

class _LeftListWidget(ListWidget):
    """Subclassed for dropEvent"""
    def dropEvent(self, event):
        data = self.parseEvent(event)
        super().dropEvent(event=event)
        # self.parent()._updateRight()
        self.parent()._removeFromRight()


class _RightListWidget(ListWidget):
    """Subclassed for dropEvent"""
    def dropEvent(self, event):
        data = self.parseEvent(event)
        super().dropEvent(event=event)
        # self.parent()._updateRight()
        self.parent()._removeFromLeft()


class SpectrumGroupEditor(CcpnDialog):
    """
    A popup to create and manage SpectrumGroups
    """
    TITLE = 'SpectrumGroup'
    FIXEDWIDTH = 170

    MODE_NEW = 0
    MODE_EDIT = 1
    MODE_SELECT_EDIT = 2

    BUTTON_NEW = 'New'
    BUTTON_EXISTING = 'From existing:'
    RADIOBUTTONS = [BUTTON_NEW, BUTTON_EXISTING]

    BUTTON_ALL = 'All'
    BUTTON_FILTER = 'Filter by:'
    RADIOBUTTONS2 = [BUTTON_ALL, BUTTON_FILTER]

    def __init__(self, parent=None, mainWindow=None,
                 spectrumGroup=None, addNew=False, editorMode=False, spectra=None or [],
                 **kwds):
        """
        Initialise the widget

        Used in three situations:
        - For creating new SpectrumGroup (mode = 0); optionally uses passed in spectra list
          i.e. New SpectrumGroup of SideBar and Context menu of SideBar
        - For editing existing SpectrumGroup (mode = 1); requires spectrumGroup argument
          i.e. Edit of SpectrumGroup of SideBar
        - For selecting and editing SpectrumGroup (mode = 2)
          i.e. Menu Spectrum->Edit SpectrumGroup...
        """
        CcpnDialog.__init__(self, parent=parent, setLayout=False, margins=(10,10,10,10), **kwds)

        if (spectrumGroup is None or addNew == True) and editorMode == False:
            self.mode = self.MODE_NEW
            self.intialRadioButton = self.BUTTON_NEW
        elif spectrumGroup is not None:
            self.mode = self.MODE_EDIT
            self.intialRadioButton = self.BUTTON_EXISTING  # essentially ignored
        elif editorMode:
            self.mode = self.MODE_SELECT_EDIT
            self.intialRadioButton = self.BUTTON_EXISTING
        else:
            raise RuntimeError('Undefined SpectrumGroupEditor mode')

        # window title
        title = 'New ' + SpectrumGroupEditor.TITLE if self.mode == self.MODE_NEW else 'Edit ' + SpectrumGroupEditor.TITLE
        self.setWindowTitle(title)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current

        # self.addNewSpectrumGroup = addNew
        self.spectrumGroup = spectrumGroup
        # self.editorMode = editorMode
        self._spectra = spectra  #open popup with these spectra already selected. Ready to create the group.

        self._setMainLayout()  # GWV: Passing directly into init constructor does not give the same result??
        self._setLeftWidgets()
        self._setRightWidgets()
        self._setApplyButtons()
        self._addWidgetsToLayout()

        self._updateState()

    def _updateState(self):
        """Update state
        """
        self._updateLeft()
        self._updateRight()

    def _updateLeft(self):
        """Update Left
        """
        if self.mode == self.MODE_NEW or self.mode == self.MODE_SELECT_EDIT:
            self.leftTopLabel.setText('Target')

            # radio buttons and pulldown
            self.leftRadioButtons.show()
            selected = self.leftRadioButtons.get()
            if selected == self.BUTTON_NEW:
                self.leftPullDown.hide()
                self.leftListWidget.clear()
                if self._spectra is not None:
                    self._setSpectra(self._spectra)
                self.nameEdit.setText('')
            else:
                # we are creating a new SG and select from existing
                self.leftPullDown.show()
                # self.leftPullDown.setIndex(0)
                spectrumGroup = self.leftPullDown.getSelectedObject()
                self.leftListWidget.clear()
                if spectrumGroup is not None:
                    self._setSpectra(spectrumGroup.spectra)
                    self.nameEdit.setText(spectrumGroup.name + '_copy')
                else:
                    self.nameEdit.setText('')

        elif self.mode == self.MODE_EDIT:
            self.leftTopLabel.setText('Editing ' + str(self.spectrumGroup))

            self.leftRadioButtons.hide()
            self.leftPullDown.hide()

            self.nameEdit.setText(self.spectrumGroup.name)
            self._setSpectra(self.spectrumGroup.spectra)

        else:
            raise RuntimeError('Invalid SpectrumGroupEditor mode "%s"' % self.mode)

    def _updateRight(self):
        """Update Right
        """
        selected = self.rightRadioButtons.get()
        if selected == self.BUTTON_ALL:
            self.rightPullDown.hide()
            self._setSpectra(self.project.spectra, False)
        else:
            self.rightPullDown.show()
            self.rightListWidget.clear()
            spectrumGroup = self.rightPullDown.getSelectedObject()
            if spectrumGroup is not None:
                self._setSpectra(spectrumGroup.spectra, False)

    def _setMainLayout(self):
        layout = QtWidgets.QGridLayout(self)
        self.setLayout(layout)
        layout.setContentsMargins(10, 20, 10, 20)  # L,T,R,B

    def _setLeftWidgets(self):

        self.leftTopLabel = Label(self, '', bold=True)

        selection = self.RADIOBUTTONS.index(self.intialRadioButton)
        self.leftRadioButtons = RadioButtons(self, texts=self.RADIOBUTTONS,
                                                      selectedInd=selection,
                                                      callback=self._updateState,
                                                      direction='h',
                                                      tipTexts=None, gridSpan=(1, 2))
        self.nameLabel = Label(self, 'Name', )
        self.nameEdit = LineEdit(self, )
        self.nameEdit.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.nameEdit.setFixedWidth(self.FIXEDWIDTH)

        self.leftPullDown = SpectrumGroupPulldown(parent=self.mainWindow,
                                                  project = self.project,
                                                  showSelectName=True,
                                                  default=self.spectrumGroup,
                                                  callback=self._leftPullDownCallback,
                                                  fixedWidths=[0, self.FIXEDWIDTH]
                                                  )

        self.leftListWidget = _LeftListWidget(self, acceptDrops=True)
        self.leftListWidget.setFixedWidth(2*self.FIXEDWIDTH)
        # appears not to work
        # self.leftListWidget.setDropEventCallback(self._removeFromRight) # _dropEventCallBack is already taken by DropBase!

    def _setRightWidgets(self):
        self.rightTopLabel = Label(self, 'Sources', bold=True)

        self.rightRadioButtons = RadioButtons(self, texts=self.RADIOBUTTONS2,
                                                      selectedInd=0,
                                                      callback=self._updateRight,
                                                      direction='h',
                                                      tipTexts=None, gridSpan=(1, 2))
        self.rightPullDown = SpectrumGroupPulldown(parent=self.mainWindow,
                                                   project = self.project,
                                                   showSelectName=True,
                                                   callback=self._rightPullDownCallback,
                                                   fixedWidths=[0, self.FIXEDWIDTH]
                                                   )

        self.rightListWidget = _RightListWidget(self, acceptDrops=True)
        self.rightListWidget.setFixedWidth(2*self.FIXEDWIDTH)

    def _setApplyButtons(self):
        self.applyButtons = ButtonList(self, texts=['Cancel', 'Apply', 'Ok'],
                                             callbacks=[self._cancel, self._applyChanges, self._okButton],
                                             tipTexts=['', '', '', None],
                                             direction='h', hAlign='r')

    def _addWidgetsToLayout(self):
        # Add left Widgets on Main layout
        layout = self.getLayout()
        # layout.setContentsMargins(10, 10, 10, 10)  # L,T,R,B

        layout.addWidget(self.leftTopLabel, 0, 0)
        layout.addWidget(self.leftRadioButtons, 1, 0)
        layout.addWidget(self.leftPullDown, 1, 1)
        layout.addWidget(self.nameLabel, 2, 0)
        layout.addWidget(self.nameEdit, 2, 1)
        layout.addWidget(self.leftListWidget, 3, 0, 1, 2)

        # Add Right Widgets on Main layout
        layout.addWidget(self.rightTopLabel, 0, 2)
        layout.addWidget(self.rightRadioButtons, 2, 2)
        layout.addWidget(self.rightPullDown, 2, 3)
        layout.addWidget(self.rightListWidget, 3, 2, 1, 2)

        # Add Buttons Widgets on Main layout
        layout.addWidget(self.applyButtons, 4, 2, 1, 2)

    def _setSpectra(self, spectra: list, leftWidget = True):
        """Convience to set the spectra in either left or right widget
        """
        # convert to pid's first
        pids = [s.pid for s in spectra]
        if leftWidget:
            widget = self.leftListWidget
        else:
            # right list widget; filter for those id's on the left hand side
            widget = self.rightListWidget
            leftItems = self.leftListWidget.getTexts()
            pids = [s for s in pids if s not in leftItems]

        widget.setTexts(pids, clear=True)

    def _leftPullDownCallback(self, value=None):
        """Callback when selecting the left spectrumGroup pulldown item"""
        self._updateState()

    def _rightPullDownCallback(self, value=None):
        """Callback when selecting the right spectrumGroup pulldown item"""
        self._updateRight()

    def _removeFromLeft(self):
        "Remove item from left list widget"
        leftPids = self.leftListWidget.getTexts()
        rightPids = self.rightListWidget.getTexts()
        pids = [p for p in leftPids if p not in rightPids]
        self.leftListWidget.setTexts(pids, clear=True)

    def _removeFromRight(self):
        "Remove item from left list widget"
        leftPids = self.leftListWidget.getTexts()
        rightPids = self.rightListWidget.getTexts()
        pids = [p for p in rightPids if p not in leftPids]
        self.rightListWidget.setTexts(pids, clear=True)

    # def _populateLeftPullDownList(self):
    #     leftPullDownData = ['Select an Option']
    #     if self.addNewSpectrumGroup:
    #         if len(self.project.spectrumGroups) > 0:
    #             for sg in self.project.spectrumGroups:
    #                 leftPullDownData.append(str(sg.name))
    #             self.leftPullDown.setData(leftPullDownData)
    #         else:
    #             self.leftPullDown.setData(leftPullDownData)
    #         self.leftPullDown.activated[str].connect(self._leftPullDownSelectionAction)
    #     if self.editorMode:
    #         self.leftPullDown.setData([str(sg.name) for sg in self.project.spectrumGroups])
    #         if self.spectrumGroup:
    #             self.leftPullDown.select(str(self.spectrumGroup.name))
    #
    #     else:
    #         if self.spectrumGroup:
    #             # self.leftPullDown.setData([str(self.spectrumGroup.name)])
    #             self.nameEdit.setText(str(self.spectrumGroup.name))
    #             # self.leftRadioButtons.hide()
    #             # self.leftSpectrumGroupsLabel.setText('Current')
    #             # self.leftPullDown.hide()
    #             self.leftTopLabel.setText('Editing ' + str(self.spectrumGroup.pid))
    #             # self.leftTopLabel.show()
    #             self._updateState()

    # def _populateListWidgetLeft(self):
    #     self.leftListWidget.clear()
    #     if self.spectrumGroup:
    #         for spectrum in self.spectrumGroup.spectra:
    #             item = QtWidgets.QListWidgetItem(str(spectrum.id))
    #             self.leftListWidget.addItem(item)
    #     else:
    #         leftPullDownSelection = self.leftPullDown.get()
    #         if leftPullDownSelection != 'Select an Option':
    #             spectrumGroup = self.project.getByPid('SG:' + str(leftPullDownSelection))
    #             for spectrum in spectrumGroup.spectra:
    #                 item = QtWidgets.QListWidgetItem(str(spectrum.id))
    #                 self.leftListWidget.addItem(item)

    # def _populateListWidgetRight(self, spectra=None):
    #     self.rightListWidget.clear()
    #     if spectra is None:
    #         for spectrum in self._getRightPullDownSpectrumGroup().spectra:
    #             item = QtWidgets.QListWidgetItem(str(spectrum.id))
    #             self.rightListWidget.addItem(item)
    #     else:
    #         for spectrum in spectra:
    #             item = QtWidgets.QListWidgetItem(str(spectrum.id))
    #             self.rightListWidget.addItem(item)

    # def _leftPullDownSelectionAction(self, selected):
    #     if selected != 'Select an Option':
    #         self.selected = self.project.getByPid('SG:' + selected)
    #         if self.editorMode:
    #             self.spectrumGroup = self.selected
    #             self.rightPullDown.setData(self._getRightPullDownSelectionData())
    #
    #         if self.selected == self.spectrumGroup:
    #             self.leftListWidget.clear()
    #             self._populateListWidgetLeft()
    #             self.nameEdit.setText(str(selected))
    #             self.rightPullDown.setData(self._getRightPullDownSelectionData())
    #
    #         if self.selected == self.rightPullDown.getText():
    #             self._selectAnOptionState()
    #             print('You cannot have the same SG on the left and right list')
    #
    #         else:
    #             self.spectrumGroup = self.selected
    #             self.leftListWidget.clear()
    #             self.rightListWidget.clear()
    #             self._populateListWidgetLeft()
    #             self.rightPullDown.setData(self._getRightPullDownSelectionData())
    #             self._selectAnOptionState()
    #             self.nameEdit.setText(self.spectrumGroup.name)
    #             if self.addNewSpectrumGroup:
    #                 self._checkForDuplicatedNames()
    #     else:
    #         self.leftListWidget.clear()
    #         self.nameEdit.setText('')

    # def _rightPullDownAction(self, selected):
    #     if selected is not None:
    #
    #         if selected == ' ':
    #             self.rightListWidget.clear()
    #             self.rightListWidget.setAcceptDrops(False)
    #             self._initialLabelListWidgetRight()
    #
    #         elif selected == 'Available Spectra':
    #             self.rightListWidget.clear()
    #             self._populateListWidgetRight(self._getAllSpectra())
    #             self.rightListWidget.setAcceptDrops(True)
    #
    #         else:
    #             self.rightListWidget.clear()
    #             self.rightListWidget.setAcceptDrops(True)
    #             spectrumGroup = self.project.getByPid(selected)
    #             if spectrumGroup != self.spectrumGroup:
    #                 self._populateListWidgetRight(spectrumGroup.spectra)
    #
    # def _initialLabelListWidgetRight(self):
    #     item = QtWidgets.QListWidgetItem('Select an option and drag/drop items across')
    #     item.setFlags(QtCore.Qt.NoItemFlags)
    #     self.rightListWidget.addItem(item)
    #
    # def _getLeftPullDownSelectionData(self):
    #     self.leftPullDownSelectionData = []
    #     for spectrumGroup in self.project.spectrumGroups:
    #         if spectrumGroup != self.spectrumGroup:
    #             self.leftPullDownSelectionData.append(str(spectrumGroup.pid))
    #     return self.leftPullDownSelectionData
    #
    # def _getRightPullDownSelectionData(self):
    #     self.rightPullDownData = [' ', 'Available Spectra']
    #     for spectrumGroup in self.project.spectrumGroups:
    #         if spectrumGroup.pid != self.leftPullDown.getText():  # self.spectrumGroup:
    #             self.rightPullDownData.append(str(spectrumGroup.pid))
    #     if self.spectrumGroup:
    #         if self.spectrumGroup.pid in self.rightPullDownData:  #This to avoid duplicates
    #             self.rightPullDownData.remove(self.spectrumGroup.pid)
    #     return self.rightPullDownData

    # def _addSpectraOnStart(self):
    #     if self._spectra:
    #
    #         # update other widgets
    #         self.leftRadioButtons.radioButtons[0].setChecked(True)
    #         self._radioButtonsCallback()
    #
    #         # add spectra on left list widget ready to create a new Group
    #         for spectrum in self._spectra:
    #             item = QtWidgets.QListWidgetItem(str(spectrum.id))
    #             self.leftListWidget.addItem(item)

    def _getAllSpectra(self):
        if self.spectrumGroup:
            allSpectra = [sp for sp in self.project.spectra]
            spectrumGroupSpectra = self.spectrumGroup.spectra
            for spectrumSG in spectrumGroupSpectra:
                if spectrumSG in allSpectra:
                    allSpectra.remove(spectrumSG)
            return allSpectra
        else:
            leftWidgetSpectra = self._getItemListWidgets()['leftWidgetSpectra']
            availableSpectra = [sp for sp in self.project.spectra if
                                sp not in leftWidgetSpectra]  # make sure to don't have spectra on left and right at the same time
            return availableSpectra

    def _changeLeftSpectrumGroupName(self):
        if self.nameEdit.isModified():
            newName = self.nameEdit.text()
            if self.spectrumGroup.name != newName:
                self.spectrumGroup.rename(newName)

    def _getItemListWidgets(self):
        leftWidgets = []
        leftWidgetSpectra = []

        for index in range(self.leftListWidget.count()):
            leftWidgets.append(self.leftListWidget.item(index))
        for item in leftWidgets:
            spectrum = self.project.getByPid('SP:' + item.text())
            leftWidgetSpectra.append(spectrum)

        rightWidgets = []
        rightWidgetSpectra = []
        for index in range(self.rightListWidget.count()):
            rightWidgets.append(self.rightListWidget.item(index))
        for item in rightWidgets:
            spectrum = self.project.getByPid('SP:' + item.text())
            rightWidgetSpectra.append(spectrum)

        return {'leftWidgetSpectra': leftWidgetSpectra, 'rightWidgetSpectra': rightWidgetSpectra}

    def _checkForDuplicatedNames(self):
        newName = str(self.nameEdit.text())
        for sg in self.project.spectrumGroups:
            if sg.name == newName:
                self.nameEdit.setText(str(sg.name) + '-1')

    # def _setEditorMode(self):
    #
    #     leftPullDownData = ['Select an Option']
    #     if len(self.project.spectrumGroups) > 0:
    #         self.leftRadioButtons.hide()
    #         for sg in self.project.spectrumGroups:
    #             leftPullDownData.append(str(sg.name))
    #         self.leftPullDown.setData(leftPullDownData)
    #         self.leftListWidget.clear()
    #         self.leftPullDown.activated[str].connect(self._leftPullDownSelectionAction)
    #     else:
    #         self.addNewSpectrumGroup = True
    #         self._populateLeftPullDownList()

    def _applyChanges(self):
        """
        The apply button has been clicked
        Define an undo block for setting the properties of the object
        If there is an error setting any values then generate an error message
          If anything has been added to the undo queue then remove it with application.undo()
          repopulate the popup widgets
        """
        leftWidgetSpectra = self._getItemListWidgets()['leftWidgetSpectra']
        rightWidgetSpectra = self._getItemListWidgets()['rightWidgetSpectra']

        applyAccept = False
        oldUndo = self.project._undo.numItems()

        with undoBlockManager():
            try:
                if self.addNewSpectrumGroup:
                    self._applyToNewSG(leftWidgetSpectra)

                if self.editorMode:
                    if self.leftPullDown.text != 'Select an Option':
                        self.spectrumGroup = self.project.getByPid('SG:' + self.leftPullDown.getText())

                if self.spectrumGroup:
                    self._applyToCurrentSG(leftWidgetSpectra)

                if self.rightPullDown.getText() == ' ' or self.rightPullDown.getText() == 'Available Spectra':
                    # return # don't do changes to spectra
                    pass
                else:
                    self._updateRightSGspectra(rightWidgetSpectra)

                applyAccept = True

            except Exception as es:
                showWarning(str(self.windowTitle()), str(es))
                if self.application._isInDebugMode:
                    raise es

        if applyAccept is False:
            # should only undo if something new has been added to the undo deque
            # may cause a problem as some things may be set with the same values
            # and still be added to the change list, so only undo if length has changed
            errorName = str(self.__class__.__name__)
            if oldUndo != self.project._undo.numItems():
                self.project._undo.undo()
                getLogger().debug('>>>Undo.%s._applychanges' % errorName)
            else:
                getLogger().debug('>>>Undo.%s._applychanges nothing to remove' % errorName)

            # repopulate popup
            self._repopulate()
            return False
        else:
            return True

    def _cancel(self):
        self.leftPullDown.unRegister()
        self.rightPullDown.unRegister()
        self.reject()

    def _okButton(self):
        if self._applyChanges() is True:
            self.leftPullDown.unRegister()
            self.rightPullDown.unRegister()
            self.accept()

    def _repopulate(self):
        self._restoreButton()

    def _restoreButton(self):
        if not self.addNewSpectrumGroup:
            self._populateLeftPullDownList()
            self._populateListWidgetLeft()
            self._selectAnOptionState()

    def _applyToNewSG(self, leftWidgetSpectra):
        name = str(self.nameEdit.text())
        if name:
            self.spectrumGroup = self.project.newSpectrumGroup(name, list(leftWidgetSpectra))
            self.addNewSpectrumGroup = False
            self.leftRadioButtons.hide()
            # self.leftSpectrumGroupsLabel.setText('Current')
            self.leftPullDown.setEnabled(False)
            self.leftPullDown.setData([str(self.spectrumGroup.name)])
            self.applyButtons.buttons[1].setEnabled(True)
        else:
            self.nameEdit.setText('Unnamed')
            self._applyToNewSG(leftWidgetSpectra)

    def _applyToCurrentSG(self, leftWidgetSpectra):
        self._changeLeftSpectrumGroupName()
        self.spectrumGroup.spectra = list(set(leftWidgetSpectra))
        self.leftTopLabel.setText(str(self.spectrumGroup.name))
        self.leftTopLabel.show()
        self._populateLeftPullDownList()

    def _updateRightSGspectra(self, rightWidgetSpectra):
        if self._getRightPullDownSpectrumGroup():
            self._getRightPullDownSpectrumGroup().spectra = []
            self._getRightPullDownSpectrumGroup().spectra = list(set(rightWidgetSpectra))
            self._selectAnOptionState()

    def _updateLeftPullDown(self):
        self.leftPullDown.setData([sg.name for sg in self.project.spectrumGroups])

    def _selectAnOptionState(self):
        self.rightPullDown.select(' ')
        self.rightListWidget.clear()
        self.rightListWidget.setAcceptDrops(False)
        self._initialLabelListWidgetRight()

    def _getRightPullDownSpectrumGroup(self):
        pullDownSelection = self.rightPullDown.getText()
        rightSpectrumGroup = self.project.getByPid(pullDownSelection)
        if rightSpectrumGroup is not None:
            return rightSpectrumGroup

    # def _checkCurrentSpectrumGroups(self):
    #     if len(self.project.spectrumGroups) > 0:
    #         self.leftRadioButtons.show()
    #         # self.leftSpectrumGroupsLabel.show()
    #         self.leftPullDown.show()
    #     else:
    #         self.leftRadioButtons.radioButtons[0].setChecked(True)
    #         self.selectInitialRadioButtons.radioButtons[1].setEnabled(False)
    #         # self.leftSpectrumGroupsLabel.hide()
    #         self.leftPullDown.hide()
    #         if len(self.project.spectra) > 0:
    #             self.rightPullDown.select('Available Spectra')
    #             self._populateListWidgetRight(self.project.spectra)

    def _cancelNewSpectrumGroup(self):
        self._populateListWidgetLeft()
        self._selectAnOptionState()
        # self._disableButtons()

    def _disableButtons(self):
        for button in self.applyButtons.buttons[1:]:
            button.setEnabled(False)
        # self.restoreButton.setEnabled(False)

    def _changeButtonStatus(self):
        for button in self.applyButtons.buttons[1:]:
            button.setEnabled(True)
        # self.restoreButton.setEnabled(True)
