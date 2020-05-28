"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-05-28 16:10:26 +0100 (Thu, May 28, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-07-04 15:21:16 +0000 (Tue, July 04, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import string
from ccpn.core.Chain import Chain
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget, handleDialogApply
from ccpn.ui.gui.lib.ChangeStateHandler import changeState
from ccpn.ui.gui.popups.AttributeEditorPopupABC import AttributeEditorPopupABC
from ccpn.util.AttrDict import AttrDict
from ccpn.ui.gui.widgets.CompoundWidgets import EntryCompoundWidget, PulldownListCompoundWidget


def _nextChainCode(project):
    """This gives a "next" available chain code.
       First does A-Z, then A1-Z1, then A2-Z2, etc.
    """

    possibleChainCodes = list(string.ascii_uppercase)
    existingChainCodes = set([chain.shortName for chain in project.chains])

    n = 0
    code = possibleChainCodes[n]
    while code in existingChainCodes and n < len(possibleChainCodes) - 1:
        n += 1
        code = possibleChainCodes[n]

    r = 0
    while code in existingChainCodes:
        r += 1
        n = 0
        code = '%s%d' % (possibleChainCodes[n], r)
        while code in existingChainCodes and n < len(possibleChainCodes) - 1:
            n += 1
            code = '%s%d' % (possibleChainCodes[n], r)

    return code


# class CreateChainPopup(CcpnDialogMainWidget):
#     FIXEDWIDTH = False
#     FIXEDHEIGHT = False
#
#     ENABLEREVERT = True
#
#     def __init__(self, parent=None, mainWindow=None, project=None, **kwds):
#         """
#         Initialise the widget
#         """
#         super().__init__(parent, setLayout=True, windowTitle='Create Chain', size=(500, 250), **kwds)
#
#         self.mainWindow = mainWindow
#         self.application = mainWindow.application
#         self.project = project if project is not None else mainWindow.application.project
#         self.current = mainWindow.application.current
#
#         row = 2
#         label2a = Label(self.mainWidget, text="name", grid=(row, 0))
#         moleculeName = LineEdit(self.mainWidget, text="", grid=(row, 1), gridSpan=(1, 1), textAlignment='l', backgroundText='> Enter name <')
#         label2b = Label(self.mainWidget, text="Molecule Type", grid=(row, 2))
#         self.molTypePulldown = PulldownList(self.mainWidget, grid=(row, 3))
#         row += 1
#
#         comment = Label(self.mainWidget, text="comment", grid=(row, 0))
#         self.commentName = LineEdit(self.mainWidget, text="", grid=(row, 1), gridSpan=(1, 1), textAlignment='l', backgroundText='> Optional <')
#         row += 1
#
#         molTypes = ['protein', 'DNA', 'RNA']
#         self.molTypePulldown.setData(molTypes)
#         label3a = Label(self.mainWidget, text="sequence", grid=(row, 0))
#         tipText = """Sequence may be entered a set of one letter codes without
#                  spaces or a set of three letter codes with spaces inbetween"""
#         self.sequenceEditor = TextEditor(self.mainWidget, grid=(row, 1), gridSpan=(1, 3), tipText=tipText)
#         row += 1
#
#         label4a = Label(self.mainWidget, 'Sequence Start', grid=(row, 0))
#         lineEdit1a = Spinbox(self.mainWidget, grid=(row, 1), value=1, min=-1000000, max=1000000)
#         label5a = Label(self.mainWidget, 'Chain code', grid=(row, 2))
#         code = _nextChainCode(self.project)
#         lineEdit2a = LineEdit(self.mainWidget, grid=(row, 3), text=code)
#
#         # self.residueList = ListWidgetSelector(self, setLayout=True, grid=(5,0), gridSpan=(1,4), title='Residue Types')
#
#         # buttonBox = ButtonList(self.mainWidget, grid=(6, 3), texts=['Cancel', 'Ok'],
#         #                        callbacks=[self.reject, self._okButton])
#
#         self.setOkButton(callback=self._okClicked, enabled=False)
#         self.setCancelButton(callback=self.reject)
#         if self.ENABLEREVERT:
#             self.setRevertButton(callback=self._revertClicked, enabled=False)
#
#         self.sequenceStart = 1
#         self.chainCode = code
#         self.sequence = self.sequenceEditor.toPlainText()
#         self.moleculeName = None
#         self.comment = None
#         moleculeName.textChanged.connect(self._setMoleculeName)
#         self.commentName.textChanged.connect(self._setComment)
#
#         lineEdit1a.valueChanged.connect(self._setSequenceStart)
#         lineEdit2a.textChanged.connect(self._setChainCode)
#         self.sequenceEditor.textChanged.connect(self._setSequence)
#
#         # complete initialising the widget
#         self.setDefaultButton(CcpnDialogMainWidget.CANCELBUTTON)
#
#         self.__postInit__()
#         self._okButton = self.getButton(self.OKBUTTON)
#         self._cancelButton = self.getButton(self.CANCELBUTTON)
#         self._revertButton = self.getButton(self.RESETBUTTON)
#
#     def _createSequence(self):
#         """Creates a sequence using the values specified in the text widget.
#         Single-letter codes must be entered with no spacing
#         Three-letter codes can be entered as space or <return> separated
#         """
#         # check the sequence for consistency, sequence widget does most of the work
#         seq = self.sequence
#
#         # split and remove white spaces
#         if isinstance(seq, str):
#             seq = seq.split()
#
#         # # trap rogue spaces and lower case residues entered by 3-letter code
#         # if seq and len(seq) == 1 and not isinstance(seq, str):
#         #     seq = seq[0]
#         # elif not isinstance(seq, str) and isinstance(seq, Iterable):
#         #     newSeq = []
#         #     for s in seq:
#         #         newSeq.append(s.upper())
#         #     seq = tuple(newSeq)
#         # else:
#         #     seq.strip('\n')
#
#         self.project.createChain(sequence=seq, compoundName=self.moleculeName,
#                                  startNumber=self.sequenceStart, shortName=self.chainCode,
#                                  molType=self.molTypePulldown.currentText(),
#                                  comment=self.comment)
#
#     def _setSequenceStart(self, value: int):
#         """
#         Sets sequence start for sequence being created
#         """
#         self.sequenceStart = int(value)
#
#     def _setChainCode(self, value: str):
#         """
#         Sets chain code for sequence being created.
#         """
#         self.chainCode = value
#
#     def _setSequence(self):
#
#         sequence = self.sequenceEditor.toPlainText()
#         if not ' ' in sequence:
#             self.sequence = self.sequenceEditor.toPlainText()
#         else:
#             self.sequence = tuple(sequence.split())
#
#     def _setMoleculeName(self, value: str):
#         """
#         Sets name of molecule being created.
#         """
#         self.moleculeName = value
#
#     def _setComment(self, value: str):
#         """
#         Sets comment of molecule being created.
#         """
#         self.comment = value or None
#
#     def _repopulate(self):
#         #TODO:ED make sure that this popup is repopulated correctly
#         pass
#
#     def _getChangeState(self):
#         """Get the change state from the _changes dict
#         """
#         applyState = True
#         revertState = False
#         allChanges = True           #if self._changes else False
#
#         return changeState(self, allChanges, applyState, revertState, self._okButton, None, self._revertButton, 0)
#
#     def _applyChanges(self):
#         """
#         The apply button has been clicked
#         Define an undo block for setting the properties of the object
#         If there is an error setting any values then generate an error message
#           If anything has been added to the undo queue then remove it with application.undo()
#           repopulate the popup widgets
#         """
#         with handleDialogApply(self) as error:
#             self._createSequence()
#
#         if error.errorValue:
#             # repopulate popup
#             self._repopulate()
#             return False
#
#         return True
#
#     def _okButton(self):
#         if self._applyChanges() is True:
#             self.accept()


from functools import partial
from ccpn.ui.gui.popups.Dialog import _verifyPopupApply
from ccpn.core.lib.ContextManagers import queueStateChange


class CreateChainPopup(AttributeEditorPopupABC):
    FIXEDWIDTH = False
    FIXEDHEIGHT = False

    klass = Chain  # The class whose properties are edited/displayed
    attributes = []  # A list of (attributeName, getFunction, setFunction, kwds) tuples;

    EDITMODE = False
    WINDOWPREFIX = 'New '

    ENABLEREVERT = True

    def __init__(self, parent=None, mainWindow=None, project=None, **kwds):
        """
        Initialise the widget
        """
        # flag required because using attributeDialog which tries to populate
        self._popupReady = False

        super().__init__(parent, mainWindow=mainWindow, size=(500, 250), **kwds)

        row = 2
        label2a = Label(self.mainWidget, text="name", grid=(row, 0))
        self.moleculeEdit = LineEdit(self.mainWidget, text="", grid=(row, 1), gridSpan=(1, 1), textAlignment='l', backgroundText='> Enter name <')
        label2b = Label(self.mainWidget, text="Molecule Type", grid=(row, 2))
        self.molTypePulldown = PulldownList(self.mainWidget, grid=(row, 3))
        row += 1

        comment = Label(self.mainWidget, text="comment", grid=(row, 0))
        self.commentName = LineEdit(self.mainWidget, text="", grid=(row, 1), gridSpan=(1, 1), textAlignment='l', backgroundText='> Optional <')
        row += 1

        self.molTypes = ['protein', 'DNA', 'RNA']
        self.molTypePulldown.setData(self.molTypes)
        label3a = Label(self.mainWidget, text="sequence", grid=(row, 0))
        tipText = """Sequence may be entered a set of one letter codes without
                 spaces or a set of three letter codes with spaces inbetween"""
        self.sequenceEditor = TextEditor(self.mainWidget, grid=(row, 1), gridSpan=(1, 3), tipText=tipText)
        row += 1

        label4a = Label(self.mainWidget, 'Sequence Start', grid=(row, 0))
        self.lineEdit1a = Spinbox(self.mainWidget, grid=(row, 1), value=1, min=-1000000, max=1000000)
        label5a = Label(self.mainWidget, 'Chain code', grid=(row, 2))
        code = _nextChainCode(self.project)
        self.lineEdit2a = LineEdit(self.mainWidget, grid=(row, 3), text=code)

        self.obj = AttrDict()
        self.obj.startNumber = 1
        self.obj.shortName = code
        self.obj.sequence = None
        self.obj.compoundName = None
        self.obj.comment = None
        self.obj.molType = self.molTypes[0]

        # # self.residueList = ListWidgetSelector(self, setLayout=True, grid=(5,0), gridSpan=(1,4), title='Residue Types')
        #
        # # buttonBox = ButtonList(self.mainWidget, grid=(6, 3), texts=['Cancel', 'Ok'],
        # #                        callbacks=[self.reject, self._okButton])
        #
        # self.setOkButton(callback=self._okClicked, enabled=False)
        # self.setCancelButton(callback=self.reject)
        # if self.ENABLEREVERT:
        #     self.setRevertButton(callback=self._revertClicked, enabled=False)
        #
        # self.sequenceStart = 1
        # self.chainCode = code
        # self.sequence = self.sequenceEditor.toPlainText()
        # self.moleculeName = None
        # self.comment = None

        self.moleculeEdit.textChanged.connect(self._queueSetMoleculeName)
        self.commentName.textChanged.connect(self._queueSetComment)
        self.lineEdit1a.valueChanged.connect(self._queueSetSequenceStart)
        self.lineEdit2a.textChanged.connect(self._queueSetChainCode)
        self.sequenceEditor.textChanged.connect(self._queueSetSequence)
        self.molTypePulldown.currentIndexChanged.connect(self._queueSetMolType)

        # # complete initialising the widget
        # self.setDefaultButton(CcpnDialogMainWidget.CANCELBUTTON)
        #
        # self.__postInit__()
        # self._okButton = self.getButton(self.OKBUTTON)
        # self._cancelButton = self.getButton(self.CANCELBUTTON)
        # self._revertButton = self.getButton(self.RESETBUTTON)

        self._popupReady = True
        self._populate()

    def _applyAllChanges(self, changes):
        """Apply all changes and create sequence from self.obj
        """
        super()._applyAllChanges(changes)

        self._createSequence()

    def _populate(self):
        """Populate the widgets
        """
        if self._popupReady:
            with self._changes.blockChanges():
                self.moleculeEdit.setText(self.obj.compoundName)
                self.commentName.setText(self.obj.comment)
                self.molTypePulldown.setCurrentText(self.obj.molType)
                self.sequenceEditor.setText(self.obj.sequence)
                self.lineEdit1a.set(self.obj.startNumber)
                self.lineEdit2a.setText(self.obj.shortName)

    def _createSequence(self):
        """Creates a sequence using the values specified in the text widget.
        Single-letter codes must be entered with no spacing
        Three-letter codes can be entered as space or <return> separated
        """
        # # check the sequence for consistency, sequence widget does most of the work
        # seq = self.obj.sequence
        #
        # # split and remove white spaces
        # if isinstance(seq, str):
        #     seq = seq.split()

        # # trap rogue spaces and lower case residues entered by 3-letter code
        # if seq and len(seq) == 1 and not isinstance(seq, str):
        #     seq = seq[0]
        # elif not isinstance(seq, str) and isinstance(seq, Iterable):
        #     newSeq = []
        #     for s in seq:
        #         newSeq.append(s.upper())
        #     seq = tuple(newSeq)
        # else:
        #     seq.strip('\n')

        self.project.createChain(**self.obj)

    @queueStateChange(_verifyPopupApply)
    def _queueSetMoleculeName(self, value):
        """Queue changes to the moleculeName
        """
        prefValue = self.obj.compoundName or None
        if value != prefValue:
            return partial(self._setMoleculeName, value)

    def _setMoleculeName(self, value: str):
        """Sets name of molecule being created.
        """
        self.obj.compoundName = value or None

    @queueStateChange(_verifyPopupApply)
    def _queueSetComment(self, value):
        """Queue changes to comment
        """
        prefValue = self.obj.comment or None
        if value != prefValue:
            return partial(self._setComment, value)

    def _setComment(self, value: str):
        """Sets comment of molecule being created.
        """
        self.obj.comment = value or None

    @queueStateChange(_verifyPopupApply)
    def _queueSetSequenceStart(self, value):
        """Queue changes to sequenceStart
        """
        textFromValue = self.lineEdit1a.textFromValue
        prefValue = textFromValue(self.obj.startNumber)
        if textFromValue(value) != prefValue:
            return partial(self._setSequenceStart, value)

    def _setSequenceStart(self, value: int):
        """Sets sequence start for sequence being created
        """
        self.obj.startNumber = int(value)

    @queueStateChange(_verifyPopupApply)
    def _queueSetChainCode(self, value):
        """Queue changes to chainCode
        """
        prefValue = self.obj.shortName or None
        if value != prefValue:
            return partial(self._setChainCode, value)

    def _setChainCode(self, value: str):
        """Sets chain code for sequence being created.
        """
        self.obj.shortName = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetSequence(self, *args, **kwds):
        """Queue changes to sequence
        """
        value = self.sequenceEditor.toPlainText()
        if not ' ' in value:
            value = self.sequenceEditor.toPlainText()
        else:
            value = tuple(value.split())

        prefValue = self.obj.sequence or None
        if value != prefValue:
            return partial(self._setSequence, value)

    def _setSequence(self, value: str):
        """Set the sequence
        """
        self.obj.sequence = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetMolType(self, value):
        value = self.molTypes[value]
        if value != self.obj.molType:
            return partial(self._setMolType, value)

    def _setMolType(self, value: str):
        """Set the molecule type
        """
        self.obj.molType = value
