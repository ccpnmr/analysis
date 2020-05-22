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
__dateModified__ = "$dateModified: 2020-05-22 21:20:39 +0100 (Fri, May 22, 2020) $"
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
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget, handleDialogApply


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


class CreateChainPopup(CcpnDialogMainWidget):
    FIXEDWIDTH = False
    FIXEDHEIGHT = False

    def __init__(self, parent=None, mainWindow=None, project=None, **kwds):
        """
        Initialise the widget
        """
        super().__init__(parent, setLayout=True, windowTitle='Create Chain', size=(500, 250), **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = project if project is not None else mainWindow.application.project
        self.current = mainWindow.application.current

        row = 2
        label2a = Label(self.mainWidget, text="name", grid=(row, 0))
        moleculeName = LineEdit(self.mainWidget, text="", grid=(row, 1), gridSpan=(1, 1), textAlignment='l', backgroundText='> Enter name <')
        label2b = Label(self.mainWidget, text="Molecule Type", grid=(row, 2))
        self.molTypePulldown = PulldownList(self.mainWidget, grid=(row, 3))
        row += 1

        comment = Label(self.mainWidget, text="comment", grid=(row, 0))
        self.commentName = LineEdit(self.mainWidget, text="", grid=(row, 1), gridSpan=(1, 1), textAlignment='l', backgroundText='> Optional <')
        row += 1

        molTypes = ['protein', 'DNA', 'RNA']
        self.molTypePulldown.setData(molTypes)
        label3a = Label(self.mainWidget, text="sequence", grid=(row, 0))
        tipText = """Sequence may be entered a set of one letter codes without
                 spaces or a set of three letter codes with spaces inbetween"""
        self.sequenceEditor = TextEditor(self.mainWidget, grid=(row, 1), gridSpan=(1, 3), tipText=tipText)
        row += 1

        label4a = Label(self.mainWidget, 'Sequence Start', grid=(row, 0))
        lineEdit1a = Spinbox(self.mainWidget, grid=(row, 1), value=1, min=-1000000, max=1000000)
        label5a = Label(self.mainWidget, 'Chain code', grid=(row, 2))
        code = _nextChainCode(self.project)
        lineEdit2a = LineEdit(self.mainWidget, grid=(row, 3), text=code)

        # self.residueList = ListWidgetSelector(self, setLayout=True, grid=(5,0), gridSpan=(1,4), title='Residue Types')

        # buttonBox = ButtonList(self.mainWidget, grid=(6, 3), texts=['Cancel', 'Ok'],
        #                        callbacks=[self.reject, self._okButton])

        self.setOkButton(callback=self._okClicked)
        self.setCancelButton(callback=self.reject)

        self.sequenceStart = 1
        self.chainCode = code
        self.sequence = self.sequenceEditor.toPlainText()
        self.moleculeName = None
        self.comment = None
        moleculeName.textChanged.connect(self._setMoleculeName)
        self.commentName.textChanged.connect(self._setComment)

        lineEdit1a.valueChanged.connect(self._setSequenceStart)
        lineEdit2a.textChanged.connect(self._setChainCode)
        self.sequenceEditor.textChanged.connect(self._setSequence)

        # complete initialising the widget
        self.setDefaultButton(CcpnDialogMainWidget.CANCELBUTTON)
        self.__postInit__()
        self._okButton = self.getButton(self.OKBUTTON)
        self._cancelButton = self.getButton(self.CANCELBUTTON)

    def _createSequence(self):
        """Creates a sequence using the values specified in the text widget.
        Single-letter codes must be entered with no spacing
        Three-letter codes can be entered as space or <return> separated
        """
        # check the sequence for consistency, sequence widget does most of the work
        seq = self.sequence

        # split and remove white spaces
        if isinstance(seq, str):
            seq = seq.split()

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

        self.project.createChain(sequence=seq, compoundName=self.moleculeName,
                                 startNumber=self.sequenceStart, shortName=self.chainCode,
                                 molType=self.molTypePulldown.currentText(),
                                 comment=self.comment)

    def _setSequenceStart(self, value: int):
        """
        Sets sequence start for sequence being created
        """
        self.sequenceStart = int(value)

    def _setChainCode(self, value: str):
        """
        Sets chain code for sequence being created.
        """
        self.chainCode = value

    def _setSequence(self):

        sequence = self.sequenceEditor.toPlainText()
        if not ' ' in sequence:
            self.sequence = self.sequenceEditor.toPlainText()
        else:
            self.sequence = tuple(sequence.split())

    def _setMoleculeName(self, value: str):
        """
        Sets name of molecule being created.
        """
        self.moleculeName = value

    def _setComment(self, value: str):
        """
        Sets comment of molecule being created.
        """
        self.comment = value or None

    def _repopulate(self):
        #TODO:ED make sure that this popup is repopulated correctly
        pass

    def _applyChanges(self):
        """
        The apply button has been clicked
        Define an undo block for setting the properties of the object
        If there is an error setting any values then generate an error message
          If anything has been added to the undo queue then remove it with application.undo()
          repopulate the popup widgets
        """
        with handleDialogApply(self) as error:
            self._createSequence()

        if error.errorValue:
            # repopulate popup
            self._repopulate()
            return False

        return True

    def _okButton(self):
        if self._applyChanges() is True:
            self.accept()
