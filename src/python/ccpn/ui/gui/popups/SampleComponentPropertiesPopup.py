"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:49 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import time
from PyQt5 import QtGui, QtWidgets, QtCore
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.MessageDialog import showInfo
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.popups.Dialog import CcpnDialog  # ejb
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.util.Logging import getLogger


TYPECOMPONENT = ['Select', 'Compound', 'Solvent', 'Buffer', 'Target', 'Inhibitor ', 'Other']
C_COMPONENT_UNIT = ['Select', 'Molar', 'g/L', 'L/L', 'mol/mol', 'g/g']
Labelling = ['None', 'Type_New', '15N', '15N,13C', '15N,13C,2H', 'ILV', 'ILVA', 'ILVAT', 'SAIL', '1,3-13C- and 2-13C-Glycerol']


class EditSampleComponentPopup(CcpnDialog):
    def __init__(self, parent=None, mainWindow=None,
                 sample=None, sampleComponent=None, newSampleComponent=False,
                 title='Edit Sample Component', **kwds):
        """
        Initialise the widget
        """
        CcpnDialog.__init__(self, parent, setLayout=False, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current

        self.sample = sample
        self.newSampleComponentToCreate = newSampleComponent

        self.sampleComponent = sampleComponent
        self._setMainLayout()
        self._setWidgets()
        self._addWidgetsToLayout(widgets=self._getAllWidgets(), layout=self.mainLayout)
        if self.newSampleComponentToCreate:
            self._updateButtons()
            self._checkCurrentSubstances()
        else:
            # self._hideSubstanceCreator()
            pass

    def _setMainLayout(self):
        self.mainLayout = QtWidgets.QGridLayout()
        self.setLayout(self.mainLayout)
        self.setWindowTitle("Sample Component Properties")
        self.mainLayout.setContentsMargins(15, 20, 25, 10)  #L,T,R,B
        self.setFixedWidth(400)
        self.setFixedHeight(300)

    def _getWidgetsToSet(self):

        return [
            self._initialOptionWidgets,
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
            ]

    def _setWidgets(self):
        for setWidget in self._getWidgetsToSet():
            setWidget()

    def _addWidgetsToLayout(self, widgets, layout):
        count = int(len(widgets) / 2)
        self.positions = [[i + 1, j] for i in range(count) for j in range(2)]
        for position, widget in zip(self.positions, widgets):
            i, j = position
            layout.addWidget(widget, i, j)
        layout.addWidget(self.buttons, count + 1, 1)
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
                self.labelcomment, self.commentLineEdit)

    def _initialOptionWidgets(self):
        self.spacerLabel = Label(self, text="")
        self.selectInitialRadioButtons = RadioButtons(self, texts=['New', 'From Substances'],
                                                      selectedInd=1,
                                                      callback=self._initialOptionsCallBack,
                                                      direction='h',
                                                      tipTexts=None,
                                                      )

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
        self.labellingPulldownList.setEnabled(True)  # ejb - was False
        self.labellingPulldownList.activated[str].connect(self._labellingSpecialCases)

    def currentLabellingWidget(self):
        self.currentLabellingLabel = Label(self, text="Labelling")
        self.showCurrentLabelling = Label(self, text="")
        if self.sampleComponent:
            self.showCurrentLabelling.setText(self.sampleComponent.labelling)

    def componentRoleWidget(self):
        self.typeLabel = Label(self, text="Role")
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
        self.labelcomment = Label(self, text="Comment")
        self.commentLineEdit = LineEdit(self)
        self.commentLineEdit.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        if self.sampleComponent:
            self.commentLineEdit.setText(self.sampleComponent.comment)

    def _setPerformButtonWidgets(self):
        tipTexts = ['', 'Click to apply changes. Name and Labelling cannot be changed once a new sample component is created', 'Click to apply and close']
        self.buttons = ButtonList(self, callbacks=[self.reject, self._applyChanges, self._okButton], texts=['Cancel', 'Apply', 'Ok'], tipTexts=tipTexts)

    def _checkCurrentSubstances(self):
        if len(self.project.substances) > 0:
            self.selectInitialRadioButtons.radioButtons[0].setChecked(True)
            self.selectInitialRadioButtons.radioButtons[1].setEnabled(True)
            self.substanceLabel.show()
            self.substancePulldownList.show()

        else:
            self.selectInitialRadioButtons.radioButtons[0].setChecked(True)
            self.selectInitialRadioButtons.radioButtons[1].setEnabled(False)
            self.substanceLabel.hide()
            self.substancePulldownList.hide()

    def _hideSubstanceCreator(self):
        if len(self.project.substances) > 0:
            self.substanceLabel.hide()
            self.substancePulldownList.hide()

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
        if len(self.project.substances) > 0:
            substancePulldownData = ['Select an option']
            for substance in self.project.substances:
                substancePulldownData.append(str(substance.id))
            self.substancePulldownList.setData(substancePulldownData)

    def _fillInfoFromSubstance(self, selected):
        if selected != 'Select an option':
            substance = self.project.getByPid('SU:' + selected)
            if substance:
                self.nameComponentLineEdit.setText(str(substance.name))
                self.labellingPulldownList.set(str(substance.labelling))
            self.nameComponentLineEdit.setReadOnly(True)
            self.labellingPulldownList.setEnabled(False)
            self._updateButtons()

    def _labellingSpecialCases(self, selected):
        if selected == 'Type_New':
            self.labellingPulldownList.setEditable(True)

        else:
            self.labellingPulldownList.setEditable(False)

    def _getConcentrationValue(self):

        try:
            value = float(self.concentrationLineEdit.text())
            return value
        except:
            # print('Concentration error: \n Value must be flot or int.')
            # info = showInfo('Concentration error', 'Value must be a flot or int')
            return 0

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
            self.sampleComponent = self.sample.newSampleComponent(
                    name=str(self.nameComponentLineEdit.text()), labelling=str(self.labellingPulldownList.currentText()))

    def _updateButtons(self):
        if self.nameComponentLineEdit.text():
            self.buttons.buttons[1].setEnabled(True)
            self.buttons.buttons[2].setEnabled(True)
        else:
            self.buttons.buttons[1].setEnabled(False)
            self.buttons.buttons[2].setEnabled(False)

    #========================================================================================
    # ejb - new section for repopulating the widgets
    #========================================================================================

    def _setCallBacksDict(self):
        return [
            (self.sampleComponent.role, str, self.typePulldownList.set),
            (self.sampleComponent.concentrationUnit, str, self.concentrationUnitPulldownList.set),
            (self.sampleComponent.concentration, float, self.columnNumberLineEdit.setText),
            (self.sampleComponent.comment, str, self.commentLineEdit.setText)
            ]

    def _repopulate(self):
        if not self.sampleComponent:
            try:
                for attrib, attribType, widget in self._setCallBacksDict():
                    if attrib is not None:  # trap the setting of the widgets
                        widget(attribType(attrib))
            except:
                pass

    def _applyChanges(self):
        """
        The apply button has been clicked
        Define an undo block for setting the properties of the object
        If there is an error setting any values then generate an error message
          If anything has been added to the undo queue then remove it with application.undo()
          repopulate the popup widgets
        """
        applyAccept = False
        oldUndo = self.project._undo.numItems()

        from ccpn.core.lib.ContextManagers import undoBlockManager

        with undoBlockManager():
            try:
                if self.newSampleComponentToCreate:
                    self.sampleComponent = self.sample.newSampleComponent(
                            name=str(self.nameComponentLineEdit.text()),
                            labelling=str(self.labellingPulldownList.currentText()),
                            role=str(self.typePulldownList.get()),
                            concentration=float(self.concentrationLineEdit.text()),
                            concentrationUnit=str(self.concentrationUnitPulldownList.get()),
                            comment=str(self.commentLineEdit.text()))
                else:
                    for property, value in self._getCallBacksDict().items():
                        # if value or type(value) is str and value is not 'None':
                        property(value)

                self.nameComponentLineEdit.setReadOnly(True)
                self.labellingPulldownList.setEnabled(False)

                applyAccept = True
            except Exception as es:
                if 'pre-existing object' in str(es):
                    # this catches api trying to duplicate object
                    applyAccept = True
                else:
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

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Enter:
            self._okButton()
        if event.key() == QtCore.Qt.Key_Escape:
            self.reject()
