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
from ccpn.util.Logging import getLogger
from ccpn.core.lib.ContextManagers import undoBlockManager


class SpectrumGroupEditor(CcpnDialog):
    def __init__(self, parent=None, mainWindow=None,
                 spectrumGroup=None, addNew=False, editorMode=False, spectra=None or [],
                 title='Spectrum Group Setup', **kwds):
        """
        Initialise the widget
        """
        CcpnDialog.__init__(self, parent, setLayout=False, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current

        self.addNewSpectrumGroup = addNew
        self.spectrumGroup = spectrumGroup
        self.editorMode = editorMode
        self._spectra = spectra  #open popup with already these spectra in. Ready to create the group.

        self._setMainLayout()
        self._setLeftWidgets()
        self._setRightWidgets()
        self._setApplyButtons()
        self._addWidgetsToLayout()

        if self.editorMode:
            self._setEditorMode()

        if self.spectrumGroup:
            self._populateListWidgetLeft()
            self.spectrumGroupLabel.show()

        if self.addNewSpectrumGroup:
            self._checkCurrentSpectrumGroups()

        if self._spectra is not None or len(self._spectra) > 0:
            self._addSpectraOnStart()

    def _setMainLayout(self):
        self.mainLayout = QtWidgets.QGridLayout()
        self.setLayout(self.mainLayout)
        self.setWindowTitle("Spectrum Group Setup")
        self.mainLayout.setContentsMargins(20, 20, 25, 15)  # L,T,R,B
        # self.setFixedWidth(800)

    def _setLeftWidgets(self):
        self.selectInitialRadioButtons = RadioButtons(self, texts=['New', 'From Current SGs'],
                                                      selectedInd=1,
                                                      callback=self._initialOptionsCallBack,
                                                      direction='h',
                                                      tipTexts=None, gridSpan=(1, 2))
        self.leftSpectrumGroupLabel = Label(self, 'Name', )
        self.leftSpectrumGroupsLabel = Label(self, 'Current SGs')
        self.spectrumGroupLabel = Label(self, '')

        self.leftSpectrumGroupLineEdit = LineEdit(self, )
        self.leftSpectrumGroupLineEdit.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.leftSpectrumGroupLineEdit.setFixedWidth(170)

        self.leftPullDownSelection = PulldownList(self)
        self._populateLeftPullDownList()
        self.leftPullDownSelection.setFixedWidth(170)

        self.spectrumGroupListWidgetLeft = ListWidget(self)
        self.spectrumGroupListWidgetLeft.setAcceptDrops(True)

    def _setRightWidgets(self):
        self.rightSelectionLabel = Label(self, 'Select Spectra from')
        self.rightPullDownSelection = PulldownList(self, )
        self.rightPullDownSelection.setData(self._getRightPullDownSelectionData())
        self.rightPullDownSelection.activated[str].connect(self._rightPullDownSelectionAction)
        self.rightPullDownSelection.setFixedWidth(170)

        self.spectrumGroupListWidgetRight = ListWidget(self)
        self.spectrumGroupListWidgetRight.setAcceptDrops(False)
        self._initialLabelListWidgetRight()

    def _setApplyButtons(self):
        self.applyButtons = ButtonList(self, texts=['Cancel', 'Apply', 'Ok'],
                                       callbacks=[self.reject, self._applyChanges, self._okButton],
                                       tipTexts=['', '', '', None], direction='h',
                                       hAlign='r')
        # if self.addNewSpectrumGroup:  # Restore button disabled
        #   self.applyButtons.buttons[1].setEnabled(False)

    def _addWidgetsToLayout(self):
        ###### Add left Widgets on Main layout ######
        self.mainLayout.addWidget(self.selectInitialRadioButtons, 0, 0)
        self.mainLayout.addWidget(self.leftSpectrumGroupsLabel, 1, 0)
        self.mainLayout.addWidget(self.leftPullDownSelection, 1, 1)
        self.mainLayout.addWidget(self.spectrumGroupLabel, 1, 1)
        self.mainLayout.addWidget(self.leftSpectrumGroupLabel, 2, 0)
        self.mainLayout.addWidget(self.leftSpectrumGroupLineEdit, 2, 1)
        self.mainLayout.addWidget(self.spectrumGroupListWidgetLeft, 3, 0, 1, 2)

        ###### Add Right Widgets on Main layout ######
        self.mainLayout.addWidget(self.rightSelectionLabel, 2, 2)
        self.mainLayout.addWidget(self.rightPullDownSelection, 2, 3)
        self.mainLayout.addWidget(self.spectrumGroupListWidgetRight, 3, 2, 1, 2)

        ###### Add Buttons Widgets on Main layout ######
        # self.mainLayout.addWidget(self.restoreButton, 4, 0)
        self.mainLayout.addWidget(self.applyButtons, 4, 3)
        self.spectrumGroupLabel.hide()

    def _initialOptionsCallBack(self):
        selected = self.selectInitialRadioButtons.get()

        if selected == 'New':

            self.spectrumGroupListWidgetLeft.clear()
            self.leftPullDownSelection.setIndex(0)
            self.leftSpectrumGroupLineEdit.setText('')
            self.leftPullDownSelection.setEnabled(False)
            self.leftPullDownSelection.hide()
            self.leftSpectrumGroupsLabel.hide()
            self._selectAnOptionState()

        else:
            self.spectrumGroupListWidgetLeft.clear()
            self.leftPullDownSelection.setEnabled(True)
            self.leftPullDownSelection.show()
            self.leftSpectrumGroupsLabel.show()
            self._selectAnOptionState()

    def _populateLeftPullDownList(self):
        leftPullDownData = ['Select an Option']
        if self.addNewSpectrumGroup:
            if len(self.project.spectrumGroups) > 0:
                for sg in self.project.spectrumGroups:
                    leftPullDownData.append(str(sg.name))
                self.leftPullDownSelection.setData(leftPullDownData)
            else:
                self.leftPullDownSelection.setData(leftPullDownData)
            self.leftPullDownSelection.activated[str].connect(self._leftPullDownSelectionAction)
        if self.editorMode:
            self.leftPullDownSelection.setData([str(sg.name) for sg in self.project.spectrumGroups])
            if self.spectrumGroup:
                self.leftPullDownSelection.select(str(self.spectrumGroup.name))

        else:
            if self.spectrumGroup:
                self.leftPullDownSelection.setData([str(self.spectrumGroup.name)])
                self.leftSpectrumGroupLineEdit.setText(str(self.spectrumGroup.name))
                self.selectInitialRadioButtons.hide()
                self.leftSpectrumGroupsLabel.setText('Current')
                self.leftPullDownSelection.hide()
                self.spectrumGroupLabel.setText(str(self.spectrumGroup.name))
                self.spectrumGroupLabel.show()

    def _populateListWidgetLeft(self):
        self.spectrumGroupListWidgetLeft.clear()
        if self.spectrumGroup:
            for spectrum in self.spectrumGroup.spectra:
                item = QtWidgets.QListWidgetItem(str(spectrum.id))
                self.spectrumGroupListWidgetLeft.addItem(item)
        else:
            leftPullDownSelection = self.leftPullDownSelection.get()
            if leftPullDownSelection != 'Select an Option':
                spectrumGroup = self.project.getByPid('SG:' + str(leftPullDownSelection))
                for spectrum in spectrumGroup.spectra:
                    item = QtWidgets.QListWidgetItem(str(spectrum.id))
                    self.spectrumGroupListWidgetLeft.addItem(item)

    def _populateListWidgetRight(self, spectra=None):
        self.spectrumGroupListWidgetRight.clear()
        if spectra is None:
            for spectrum in self._getRightPullDownSpectrumGroup().spectra:
                item = QtWidgets.QListWidgetItem(str(spectrum.id))
                self.spectrumGroupListWidgetRight.addItem(item)
        else:
            for spectrum in spectra:
                item = QtWidgets.QListWidgetItem(str(spectrum.id))
                self.spectrumGroupListWidgetRight.addItem(item)

    def _leftPullDownSelectionAction(self, selected):
        if selected != 'Select an Option':
            self.selected = self.project.getByPid('SG:' + selected)
            if self.editorMode:
                self.spectrumGroup = self.selected
                self.rightPullDownSelection.setData(self._getRightPullDownSelectionData())

            if self.selected == self.spectrumGroup:
                self.spectrumGroupListWidgetLeft.clear()
                self._populateListWidgetLeft()
                self.leftSpectrumGroupLineEdit.setText(str(selected))
                self.rightPullDownSelection.setData(self._getRightPullDownSelectionData())

            if self.selected == self.rightPullDownSelection.getText():
                self._selectAnOptionState()
                print('You cannot have the same SG on the left and right list')

            else:
                self.spectrumGroup = self.selected
                self.spectrumGroupListWidgetLeft.clear()
                self.spectrumGroupListWidgetRight.clear()
                self._populateListWidgetLeft()
                self.rightPullDownSelection.setData(self._getRightPullDownSelectionData())
                self._selectAnOptionState()
                self.leftSpectrumGroupLineEdit.setText(self.spectrumGroup.name)
                if self.addNewSpectrumGroup:
                    self._checkForDuplicatedNames()
        else:
            self.spectrumGroupListWidgetLeft.clear()
            self.leftSpectrumGroupLineEdit.setText('')

    def _rightPullDownSelectionAction(self, selected):
        if selected is not None:

            if selected == ' ':
                self.spectrumGroupListWidgetRight.clear()
                self.spectrumGroupListWidgetRight.setAcceptDrops(False)
                self._initialLabelListWidgetRight()

            elif selected == 'Available Spectra':
                self.spectrumGroupListWidgetRight.clear()
                self._populateListWidgetRight(self._getAllSpectra())
                self.spectrumGroupListWidgetRight.setAcceptDrops(True)

            else:
                self.spectrumGroupListWidgetRight.clear()
                self.spectrumGroupListWidgetRight.setAcceptDrops(True)
                spectrumGroup = self.project.getByPid(selected)
                if spectrumGroup != self.spectrumGroup:
                    self._populateListWidgetRight(spectrumGroup.spectra)

    def _initialLabelListWidgetRight(self):
        item = QtWidgets.QListWidgetItem('Select an option and drag/drop items across')
        item.setFlags(QtCore.Qt.NoItemFlags)
        self.spectrumGroupListWidgetRight.addItem(item)

    def _getLeftPullDownSelectionData(self):
        self.leftPullDownSelectionData = []
        for spectrumGroup in self.project.spectrumGroups:
            if spectrumGroup != self.spectrumGroup:
                self.leftPullDownSelectionData.append(str(spectrumGroup.pid))
        return self.leftPullDownSelectionData

    def _getRightPullDownSelectionData(self):
        self.rightPullDownSelectionData = [' ', 'Available Spectra']
        for spectrumGroup in self.project.spectrumGroups:
            if spectrumGroup.pid != self.leftPullDownSelection.getText():  # self.spectrumGroup:
                self.rightPullDownSelectionData.append(str(spectrumGroup.pid))
        if self.spectrumGroup:
            if self.spectrumGroup.pid in self.rightPullDownSelectionData:  #This to avoid duplicates
                self.rightPullDownSelectionData.remove(self.spectrumGroup.pid)
        return self.rightPullDownSelectionData

    def _addSpectraOnStart(self):
        if self._spectra:

            # update other widgets
            self.selectInitialRadioButtons.radioButtons[0].setChecked(True)
            self._initialOptionsCallBack()

            # add spectra on left list widget ready to create a new Group
            for spectrum in self._spectra:
                item = QtWidgets.QListWidgetItem(str(spectrum.id))
                self.spectrumGroupListWidgetLeft.addItem(item)

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
        if self.leftSpectrumGroupLineEdit.isModified():
            newName = self.leftSpectrumGroupLineEdit.text()
            if self.spectrumGroup.name != newName:
                self.spectrumGroup.rename(newName)

    def _getItemListWidgets(self):
        leftWidgets = []
        leftWidgetSpectra = []

        for index in range(self.spectrumGroupListWidgetLeft.count()):
            leftWidgets.append(self.spectrumGroupListWidgetLeft.item(index))
        for item in leftWidgets:
            spectrum = self.project.getByPid('SP:' + item.text())
            leftWidgetSpectra.append(spectrum)

        rightWidgets = []
        rightWidgetSpectra = []
        for index in range(self.spectrumGroupListWidgetRight.count()):
            rightWidgets.append(self.spectrumGroupListWidgetRight.item(index))
        for item in rightWidgets:
            spectrum = self.project.getByPid('SP:' + item.text())
            rightWidgetSpectra.append(spectrum)

        return {'leftWidgetSpectra': leftWidgetSpectra, 'rightWidgetSpectra': rightWidgetSpectra}

    def _checkForDuplicatedNames(self):
        newName = str(self.leftSpectrumGroupLineEdit.text())
        for sg in self.project.spectrumGroups:
            if sg.name == newName:
                self.leftSpectrumGroupLineEdit.setText(str(sg.name) + '-1')

    def _setEditorMode(self):

        leftPullDownData = ['Select an Option']
        if len(self.project.spectrumGroups) > 0:
            self.selectInitialRadioButtons.hide()
            for sg in self.project.spectrumGroups:
                leftPullDownData.append(str(sg.name))
            self.leftPullDownSelection.setData(leftPullDownData)
            self.spectrumGroupListWidgetLeft.clear()
            self.leftPullDownSelection.activated[str].connect(self._leftPullDownSelectionAction)
        else:
            self.addNewSpectrumGroup = True
            self._populateLeftPullDownList()

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
                    if self.leftPullDownSelection.text != 'Select an Option':
                        self.spectrumGroup = self.project.getByPid('SG:' + self.leftPullDownSelection.getText())

                if self.spectrumGroup:
                    self._applyToCurrentSG(leftWidgetSpectra)

                if self.rightPullDownSelection.getText() == ' ' or self.rightPullDownSelection.getText() == 'Available Spectra':
                    # return # don't do changes to spectra
                    pass
                else:
                    self._updateRightSGspectra(rightWidgetSpectra)

                applyAccept = True
            except Exception as es:
                showWarning(str(self.windowTitle()), str(es))

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

    def _okButton(self):
        if self._applyChanges() is True:
            self.accept()

    def _repopulate(self):
        self._restoreButton()

    def _restoreButton(self):
        if not self.addNewSpectrumGroup:
            self._populateLeftPullDownList()
            self._populateListWidgetLeft()
            self._selectAnOptionState()

    def _applyToNewSG(self, leftWidgetSpectra):
        name = str(self.leftSpectrumGroupLineEdit.text())
        if name:
            self.spectrumGroup = self.project.newSpectrumGroup(name)
            self.spectrumGroup.spectra = list(set(leftWidgetSpectra))
            self.addNewSpectrumGroup = False
            self.selectInitialRadioButtons.hide()
            self.leftSpectrumGroupsLabel.setText('Current')
            self.leftPullDownSelection.setEnabled(False)
            self.leftPullDownSelection.setData([str(self.spectrumGroup.name)])
            self.applyButtons.buttons[1].setEnabled(True)
        else:
            self.leftSpectrumGroupLineEdit.setText('Unnamed')
            self._applyToNewSG(leftWidgetSpectra)

    def _applyToCurrentSG(self, leftWidgetSpectra):
        self._changeLeftSpectrumGroupName()
        self.spectrumGroup.spectra = list(set(leftWidgetSpectra))
        self.spectrumGroupLabel.setText(str(self.spectrumGroup.name))
        self.spectrumGroupLabel.show()
        self._populateLeftPullDownList()

    def _updateRightSGspectra(self, rightWidgetSpectra):
        if self._getRightPullDownSpectrumGroup():
            self._getRightPullDownSpectrumGroup().spectra = []
            self._getRightPullDownSpectrumGroup().spectra = list(set(rightWidgetSpectra))
            self._selectAnOptionState()

    def _updateLeftPullDown(self):
        self.leftPullDownSelection.setData([sg.name for sg in self.project.spectrumGroups])

    def _selectAnOptionState(self):
        self.rightPullDownSelection.select(' ')
        self.spectrumGroupListWidgetRight.clear()
        self.spectrumGroupListWidgetRight.setAcceptDrops(False)
        self._initialLabelListWidgetRight()

    def _getRightPullDownSpectrumGroup(self):
        pullDownSelection = self.rightPullDownSelection.getText()
        rightSpectrumGroup = self.project.getByPid(pullDownSelection)
        if rightSpectrumGroup is not None:
            return rightSpectrumGroup

    def _checkCurrentSpectrumGroups(self):
        if len(self.project.spectrumGroups) > 0:
            self.selectInitialRadioButtons.show()
            self.leftSpectrumGroupsLabel.show()
            self.leftPullDownSelection.show()
        else:
            self.selectInitialRadioButtons.radioButtons[0].setChecked(True)
            self.selectInitialRadioButtons.radioButtons[1].setEnabled(False)
            self.leftSpectrumGroupsLabel.hide()
            self.leftPullDownSelection.hide()
            if len(self.project.spectra) > 0:
                self.rightPullDownSelection.select('Available Spectra')
                self._populateListWidgetRight(self.project.spectra)

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
