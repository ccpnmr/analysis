"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Joanna Fox, Morgan Hayward, Victoria A Higman, Luca Mureddu",
               "Eliza Płoskoń, Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2024-01-25 17:32:14 +0000 (Thu, January 25, 2024) $"
__version__ = "$Revision: 3.2.2 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-07-04 15:21:16 +0000 (Tue, July 04, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
import string
from functools import partial
from PyQt5 import QtWidgets
from ccpn.ui.gui.widgets.MessageDialog import showInfo, showWarning
import textwrap
from ccpn.core.Chain import Chain
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.Menu import Menu
from ccpn.ui.gui.widgets.Frame import Frame
from PyQt5 import QtGui
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.popups.AttributeEditorPopupABC import AttributeEditorPopupABC
from ccpn.util.AttrDict import AttrDict
from ccpn.ui.gui.popups.Dialog import _verifyPopupApply
from ccpn.core.lib.ContextManagers import queueStateChange, catchExceptions
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Widget import Widget
from PyQt5.QtCore import Qt
from itertools import accumulate
from ccpn.core.lib.ChainLib import SequenceHandler, CCPCODE
from ccpn.framework.Application import getApplication, getProject
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QMenu, QAction

DefaultAddAtomGroups = True
DefaultAddPseudoAtoms = False
DefaultAddNonstereoAtoms = True
DefaultSetBoundsForAtomGroups = False
ONELETTERCODE = 'One-Letter Code'
THREELETTERCODE = 'Three-Letter Code'
CCPCODESELECTION = 'Ccp Code (ChemComp)'


def divideChunks(l, n):
  for i in range(0, len(l), n):
    yield l[i:i + n]

def _nextChainCode(project):
    """This gives a "next" available chain code.
       First does A-Z, then A1-Z1, then A2-Z2, etc.
    """

    possibleChainCodes = list(string.ascii_uppercase)
    existingChainCodes = {chain.shortName for chain in project.chains}

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


class _SequenceTextEditor(TextEditor):

    _copyAs1Code = 'Copy Selected as 1LetterCodes'
    _copyAs3Code = 'Copy Selected as 3LetterCodes'
    _copyAsCcpCodes = 'Copy Selected as CcpCodes'

    def __init__(self, parent,  **kwargs):
        super().__init__(parent, **kwargs)

    def context_menu(self):
        self.standardContextMenu = self.createStandardContextMenu()
        # Create a custom context menu
        self.customContextMenu = menu = Menu('Editor', self)
        self.customContextMenu.addActions(self.standardContextMenu.actions())  # Add standard actions
        self.customContextMenu.addSeparator()
        menu.addItem(text=self._copyAs1Code, callback=self._copySelectedAs1CodeLetter, enabled=False)
        menu.addItem(text=self._copyAs3Code, callback=self._copySelectedAs3CodeLetter, enabled=False)
        menu.addItem(text=self._copyAsCcpCodes, callback=self._copySelectedAsCcpCode, enabled=False)
        self.customContextMenu.exec_(QtGui.QCursor.pos())

    def _copySelectedAs1CodeLetter(self):
        pass
    def _copySelectedAs3CodeLetter(self):
        pass
    def _copySelectedAsCcpCode(self):
        pass


class _SequenceEditorBaseWidget(ScrollArea):

    def __init__(self, parent, popup, maxCodesPerLine=10,  demoSequence='ACDFEG', **kwargs):
        super(_SequenceEditorBaseWidget, self).__init__(parent=parent, setLayout=True, **kwargs)

        self._scrollFrame = Frame(self, setLayout=True, showBorder=False,
                                 hPolicy='expanding',
                                 vAlign='top', vPolicy='minimal')
        self.setWidget(self._scrollFrame)
        self._popup = popup
        self.editor = _SequenceTextEditor(self._scrollFrame,  backgroundText=demoSequence, grid=(0, 0))
        self.codeCounter = Label(self._scrollFrame, grid=(0, 1))
        self.editor.textChanged.connect(self._textChangedCallback)
        self.editor.verticalScrollBar().setVisible(False)
        self.editor.horizontalScrollBar().setVisible(False)
        self._maxCodesPerLine = maxCodesPerLine
        self._project = getProject()
        self._molType = self._getMolType()
        self._sequenceHandler = SequenceHandler(self._project, moleculeType=self._molType)
        self._startingCode = self._popup.startingSequenceCodeWidget.get()
        self._popup.startingSequenceCodeWidget.valueChanged.connect(self._setStartingSequenceCode)


    def _getMolType(self):
        return self._popup.molTypePulldown.get()

    def getSequence(self):
        pass

    def setSequence(self, sequence):
        pass

    def _setStartingSequenceCode(self, *args):
        self._startingCode = self._popup.startingSequenceCodeWidget.get()
        self._textChangedCallback()

    def _textChangedCallback(self):
        pass

    def _formatText(self, text):
        pass

    def _updateCodeCounter(self):
       pass

class SequenceEditor1Code(_SequenceEditorBaseWidget):

    def __init__(self, parent, popup, maxCodesPerLine=10,  **kwargs):
        super().__init__(parent=parent, popup=popup, maxCodesPerLine=maxCodesPerLine, **kwargs)

    def getSequence(self):
        text = self.editor.toPlainText()
        text = self._sequenceHandler._cleanString(text)
        return text

    def _textChangedCallback(self):

        text = self.editor.toPlainText()
        text = self._sequenceHandler._cleanString(text)
        cursor = self.editor.textCursor()
        cursorAtEnd = cursor.atEnd()
        currentCursorPosition = cursor.position()
        allowed = self._sequenceHandler.getAvailableCode1Letter(onlyStandard=True)
        formattedText = self.formatTextHtml(text, allowed, self._maxCodesPerLine)
        with self.editor.blockWidgetSignals():
            self.editor.setText(formattedText)
            self._updateCodeCounter()

        ## set the cursor in the right position.
        new_cursor = self.editor.textCursor()
        if cursorAtEnd: #we are at the end
            new_cursor.movePosition(cursor.End)
        else:
            # We are in the middle of a block. Preserve the position
            new_cursor.setPosition(currentCursorPosition)
        self.editor.setTextCursor(new_cursor)

        ## we can now set the sequence to the main popup.
        if self._isSequenceValid:
            self._popup._queueSetSequence()
            if self._popup.getButton(self._popup.OKBUTTON):
                self._popup.getButton(self._popup.OKBUTTON).setEnabled(True)
        else:
            # self._popup.
            if self._popup.getButton(self._popup.OKBUTTON):
                self._popup.getButton(self._popup.OKBUTTON).setEnabled(False)

    def formatTextHtml(self, text, allowedChars, maxCodesPerLine):
        # Wrap the text into lines
        wrappedLines = textwrap.wrap(text, maxCodesPerLine)

        # Create a list to store formatted lines
        formattedLines = []

        # Iterate through each line
        isInvalid = False
        for line in wrappedLines:
            formattedLine = ''
            # Iterate through each character in the line
            for char in line:
                # Check if the character is allowed
                if char in allowedChars:
                    formattedLine += f'<span style="color:black">{char}</span>'
                else:
                    formattedLine += f'<span style="color:red">{char}</span>'
                    isInvalid = True

            # Append the formatted line to the list
            formattedLines.append(formattedLine)

        # Join the formatted lines with line breaks
        formattedHtml = '<br>'.join(formattedLines)
        self._isSequenceValid = not isInvalid
        return formattedHtml

    def _getCursorCount(self):
        """ Get how many chars are in the editor including the \n"""
        text = self.editor.toPlainText()
        lines = [len(line) for line in text.split('\n')]
        # print('++++>', lines, 'SUM LINES: ',sum(lines) ,  'LEN LINES:',len(lines))
        count = sum(lines) +(len(lines)-1) #ad the row count excluding the first
        return count

    def _updateCodeCounter(self):
        self.codeCounter.clear()
        text = self.editor.toPlainText()
        lines = [list(line) for line in text.split('\n')]
        labels  = ''
        count = 0
        for i, line in enumerate(lines):
            if i == 0:
                label = list(np.arange(self._startingCode, len(lines[i])+self._startingCode))
                if not label:
                    break
                labels += f'{label.pop()}\n'
                count += len(lines[i])
            else:
                mm = (self._maxCodesPerLine * i)+self._startingCode
                label = list(np.arange(mm, len(lines[i])+mm))
                labels += f'{label.pop()}\n'
            count += (len(lines[i]))*i
        self.codeCounter.setText(labels)
        self.codeCounter.setAlignment(Qt.AlignTop | Qt.AlignRight)
        return count


class SequenceEditor3Code(_SequenceEditorBaseWidget):

    def __init__(self, parent, popup, maxCodesPerLine=10, **kwargs):
        super().__init__(parent=parent, popup=popup,
                         maxCodesPerLine=maxCodesPerLine,
                         demoSequence='ALA LEU VAL', **kwargs)


class SequenceEditorCcpCode(_SequenceEditorBaseWidget):

    def __init__(self, parent, popup, maxCodesPerLine=10, **kwargs):
        super().__init__(parent=parent, popup=popup,
                         maxCodesPerLine=maxCodesPerLine,
                         demoSequence='Ala Leu Atp', **kwargs)

class CreateChainPopup(AttributeEditorPopupABC):
    """
    Create new chain popup
    """
    FIXEDWIDTH = False
    FIXEDHEIGHT = False

    klass = Chain  # The class whose properties are edited/displayed
    attributes = []  # A list of (attributeName, getFunction, setFunction, kwds) tuples;

    EDITMODE = False
    WINDOWPREFIX = 'New '

    ENABLEREVERT = True
    _code = None

    def __init__(self, parent=None, mainWindow=None, project=None, **kwds):
        """
        Initialise the widget
        """
        # flag required because using attributeDialog which tries to populate
        self._popupReady = False

        super().__init__(parent, mainWindow=mainWindow, size=(500, 300), **kwds)

        # set up the widgets
        self._setWidgets()

        # define the blank object to hold the new attributes
        self._defineObject()
        self._formattingLenght = 5
        # attach the callbacks for the widgets
        self.moleculeEdit.textChanged.connect(self._queueSetMoleculeName)
        self.commentName.textChanged.connect(self._queueSetComment)
        self.startingSequenceCodeWidget.valueChanged.connect(self._queueSetSequenceStart)
        self.lineEdit2a.textChanged.connect(self._queueSetChainCode)
        # self.sequence1CodeEditor.textChanged.connect(self._validate1LetterCodeSequence)
        # self.sequence3CodeEditor.textChanged.connect(self._validate1LetterCodeSequence)
        #
        # self.sequenceCcpCodeEditor.textChanged.connect(self._validateFullLetterCodeSequence)

        self.molTypePulldown.currentIndexChanged.connect(self._queueSetMolType)
        self.expandAtomsFromAtomSetW.clicked.connect(self._queueSetExpandAtomsFromAtomSets)
        self.addNonstereoAtomsW.clicked.connect(self._queueSetAddNonstereoAtomsW)
        self.addPseudoAtomsW.clicked.connect(self._queueSetAddPseudoAtomsW)
        self.makeCyclicPolymer.clicked.connect(self._queueSetMakeCyclic)

        self._popupReady = True
        self._populate()

    def _setWidgets(self):
        """Set up the widgets
        """
        minimumWidth = 180
        minimumWidthEditors = 300
        minimumHeightEditors = 200

        row = 1
        label5a = Label(self.mainWidget, 'Chain Name', grid=(row, 0))
        self._code = _nextChainCode(self.project)
        self.lineEdit2a = LineEdit(self.mainWidget, grid=(row, 1), text=self._code, hAlign='left', minimumWidth=minimumWidth)

        row += 1
        label2a = Label(self.mainWidget, text="Substance Name", grid=(row, 0), )
        self.moleculeEdit = LineEdit(self.mainWidget, text="", grid=(row, 1), textAlignment='l', backgroundText='> Enter name <', hAlign='left', minimumWidth=minimumWidth)
        row += 1
        label2b = Label(self.mainWidget, text="Molecule Type", grid=(row, 0))
        self.molTypePulldown = PulldownList(self.mainWidget, grid=(row, 1), hAlign='left', minimumWidth=minimumWidth)
        row += 1
        comment = Label(self.mainWidget, text="Comment", grid=(row, 0))
        self.commentName = LineEdit(self.mainWidget, text="", grid=(row, 1),  textAlignment='l', backgroundText='> Optional <', hAlign='left', minimumWidth=minimumWidth)

        row += 1
        self.molTypes = ['protein', 'DNA', 'RNA', 'other']
        self.molTypePulldown.setData(self.molTypes)
        label3a = Label(self.mainWidget, text="Sequence mode", grid=(row, 0))
        tipText = ""
        # self.sequenceEditor = TextEditor(self.mainWidget, grid=(row, 1), gridSpan=(1, 3), tipText=tipText)
        self.sequenceEditorCodeOptions = RadioButtons(self.mainWidget,
                                                      texts=[ONELETTERCODE, THREELETTERCODE, CCPCODESELECTION],
                                                      selectedInd=0,
                                                      callback=self._toggleSequenceEditor,
                                                      direction='v',
                                                      grid=(row, 1),  tipText=tipText, hAlign='left', minimumWidth=minimumWidth)
        row += 1
        label = Label(self.mainWidget, 'Sequence Start', grid=(row, 0))
        self.startingSequenceCodeWidget = Spinbox(self.mainWidget, grid=(row, 1), value=1, min=-1000000,
                                                  max=1000000, hAlign='left', minimumWidth=minimumWidth)
        row += 1

        label3a = Label(self.mainWidget, text="Sequence", grid=(row, 0))

        self.sequence1CodeEditor = SequenceEditor1Code(self.mainWidget,
                                                      popup=self,

                                                      grid=(row, 1), gridSpan=(1, 3), tipText=tipText,
                                                      minimumWidth=minimumWidthEditors,
                                                      minimumHeight=minimumHeightEditors)
        row += 1
        demoSequence = '''ALA ARG ASN  or  ALA, ARG, ASN '''
        self.sequence3CodeEditor = SequenceEditor3Code(self.mainWidget,
                                                        popup=self,
                                              backgroundText=demoSequence,
                                              grid=(row, 1), gridSpan=(1, 3),
                                              tipText=tipText,
                                              minimumWidth=minimumWidthEditors,
                                              minimumHeight=minimumHeightEditors)

        demoSequence = '''Ala Arg Aba or Ala, Arg, Aba '''
        self.sequenceCcpCodeEditor = SequenceEditorCcpCode(self.mainWidget,
                                                          popup=self,
                                                backgroundText=demoSequence,

                                                grid=(row, 1), gridSpan=(1, 3), tipText=tipText,
                                                minimumWidth=minimumWidthEditors,
                                                minimumHeight=minimumHeightEditors)

        self._toggleSequenceEditor()



        row += 1
        tipText6a = "E.g., for a VAL residue, the set of HG11, HG12, HG13 (NMR equivalent) atoms will create a new atom HG1%;\n" \
                    "        also the set HG1%, HG2% will create a new atom HG%"
        label6a = Label(self.mainWidget, 'Expand Atoms From AtomSets', tipText=tipText6a, grid=(row, 0))
        self.expandAtomsFromAtomSetW = CheckBox(self.mainWidget, checked=DefaultAddAtomGroups,
                                                tipText=tipText6a, grid=(row, 1), hAlign='left')
        row += 1
        tipText7a = "Add new atoms for Non-stereo Specific Atoms (if any).\n" \
                    "E.g., for a VAL residue, HGx%, HGy% will be added if atoms HG1% and HG2% are present.\n" \
                    "This option is available only if 'Expand Atoms From AtomSets' is selected."
        label7a = Label(self.mainWidget, 'Add Non-Stereo Specific Atoms', tipText=tipText7a, grid=(row, 0))
        self.addNonstereoAtomsW = CheckBox(self.mainWidget, checked=DefaultAddNonstereoAtoms,
                                           tipText=tipText7a, grid=(row, 1), hAlign='left', minimumWidth=minimumWidth)
        row += 1
        tipText8a = "E.g., for a VAL residue, the set of HG11, HG12, HG13 (NMR equivalent) atoms\n" \
                    "        will create a new atom HG1% and an extra pseudo-atom MG1;\n" \
                    "        also the set HG1%, HG2% will create a new atom HG% and an extra pseudo-atom QG.\n" \
                    "This option is available only if 'Expand Atoms From AtomSets' is selected and proton groups."
        label8a = Label(self.mainWidget, 'Add extra Pseudo-Atoms', tipText=tipText8a, grid=(row, 0))
        self.addPseudoAtomsW = CheckBox(self.mainWidget, checked=DefaultAddPseudoAtoms,
                                        tipText=tipText8a, grid=(row, 1), hAlign='left', minimumWidth=minimumWidth)
        self._togglePseudoAtomOptions(self.expandAtomsFromAtomSetW.get())

        row += 1
        tipText9a = "Make a cyclic polymer;\n" \
                    "    H1, H2, H3 and OXT atoms will be removed."
        label8a = Label(self.mainWidget, 'Cyclic Polymer', tipText=tipText9a, grid=(row, 0))
        self.makeCyclicPolymer = CheckBox(self.mainWidget, checked=False,
                                          tipText=tipText9a, grid=(row, 1), hAlign='left', minimumWidth=minimumWidth)

    def _defineObject(self):
        """Initialise the new object
        """
        # define the blank object to hold the new attributes
        self.obj = AttrDict()
        self.obj.compoundName = None
        self.obj.startNumber = 1
        self.obj.shortName = self._code
        self.obj.sequence = None
        self.obj.sequenceCcpCodes = None

        self.obj.comment = None
        self.obj.molType = self.molTypes[0]
        self.obj.expandFromAtomSets = DefaultAddAtomGroups
        self.obj.addPseudoAtoms = DefaultAddPseudoAtoms
        self.obj.addNonstereoAtoms = DefaultAddNonstereoAtoms
        self.obj.isCyclic = False

    def _okClicked(self):

            super()._okClicked()

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
                if self.obj.sequence:
                    self.sequence1CodeEditor.setSequence(self.obj.sequence)
                if self.obj.sequenceCcpCodes:
                    codes = ','.join(self.obj.sequenceCcpCodes)
                    self.sequenceCcpCodeEditor.setSequence(codes)
                self.startingSequenceCodeWidget.set(self.obj.startNumber)
                self.lineEdit2a.setText(self.obj.shortName)
                self.expandAtomsFromAtomSetW.set(self.obj.expandFromAtomSets)
                self.addNonstereoAtomsW.set(self.obj.addNonstereoAtoms)
                self.addPseudoAtomsW.set(self.obj.addPseudoAtoms)
                self.makeCyclicPolymer.set(self.obj.isCyclic)


    def _reformatCcpCode(self):
        valueCcpCode = self.sequenceCcpCodeEditor.toPlainText()
        valueCcpCode = ''.join(valueCcpCode.split())
        valueCcpCode = valueCcpCode.replace('\n', '')
        codes = valueCcpCode.split(',')
        codes = [f'{code}' for code in codes]
        chunks = list(divideChunks(codes, self._formattingLenght))
        if len(chunks) > 0:
            formattedCodes = ','.join(chunks[0]) + ','
            for chunk in chunks[1:]:
                formattedCodes += '\n' + ','.join(chunk) + ','
            formattedCodes = formattedCodes.strip(',')
            self.sequenceCcpCodeEditor.setText(formattedCodes)

    def _reformatSequence(self):

        self._reformatCcpCode()

    def _createSequence(self):
        """Creates a sequence using the values specified in the text widget.

        """
        mode = self.sequenceEditorCodeOptions.getSelectedText()
        if mode == CCPCODESELECTION:
            self.obj.sequence = None
        self.project.createChain(**self.obj)

    def _toggleSequenceEditor(self):
        selected = self.sequenceEditorCodeOptions.getSelectedText()
        if selected == ONELETTERCODE:
            self.sequence1CodeEditor.show()
            self.sequence3CodeEditor.hide()
            self.sequenceCcpCodeEditor.hide()

        elif selected == THREELETTERCODE:
            self.sequence1CodeEditor.hide()
            self.sequence3CodeEditor.show()
            self.sequenceCcpCodeEditor.hide()
        else:
            self.sequence1CodeEditor.hide()
            self.sequence3CodeEditor.hide()
            self.sequenceCcpCodeEditor.show()

    def _togglePseudoAtomOptions(self, value):
        isParentChecked = self.expandAtomsFromAtomSetW.get()
        self.addNonstereoAtomsW.setEnabled(isParentChecked)
        self.addPseudoAtomsW.setEnabled(isParentChecked)

    @queueStateChange(_verifyPopupApply)
    def _queueSetExpandAtomsFromAtomSets(self, value):
        """Queue changes to the expandFromAtomSets
        """
        prefValue = self.obj.expandFromAtomSets
        if value != prefValue:
            return partial(self._setExpandAtomsFromAtomSets, value)

    def _setExpandAtomsFromAtomSets(self, value: str):
        """Sets expandFromAtomSets of molecule being created.
        """
        self.obj.expandFromAtomSets = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetAddNonstereoAtomsW(self, value):
        """Queue changes to the expandFromAtomSets
        """
        prefValue = self.obj.addNonstereoAtoms
        if value != prefValue:
            return partial(self._setSetAddNonstereoAtomsW, value)

    def _setSetAddNonstereoAtomsW(self, value: str):
        """Sets AddNonstereoAtoms of molecule being created.
        """
        self.obj.addNonstereoAtoms = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetAddPseudoAtomsW(self, value):
        """Queue changes to the SetAddPseudoAtomsW
        """
        prefValue = self.obj.addPseudoAtoms
        if value != prefValue:
            return partial(self._setSetAddPseudoAtomsW, value)

    def _setSetAddPseudoAtomsW(self, value: str):
        """Sets addPseudoAtoms of molecule being created.
        """
        self.obj.addPseudoAtoms = value

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
        textFromValue = self.startingSequenceCodeWidget.textFromValue
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

    def _validate1LetterCodeSequence(self, *args):
        value1Code = self.sequence1CodeEditor.toPlainText()
        # valueCcpCode = self.sequenceCcpCodeEditor.toPlainText()
        # if not value1Code:
        #     return
        # msg = None
        # # search empty spaces
        # result = value1Code.split(' ')
        # if len(result)>1:
        #     msg = 'Empty spaces are not allowed. Ensure you are using 1Letter Code only'
        #     showWarning('Sequence Error', msg)
        #     return
        # # search commas
        # result = value1Code.split(',')
        # if len(result) > 1:
        #     msg = 'Commas are not allowed. Ensure you are using 1Letter Code only'
        #     showWarning('Sequence Error', msg)
        #     return

        self._queueSetSequence(*args)

    def _validateFullLetterCodeSequence(self, *args):

        # valueCcpCode = self.sequenceCcpCodeEditor.toPlainText()
        # if not valueCcpCode:
        #     return

        self._queueSetSequenceCcpCode(*args)


    def _isSequenceCcpCodeValid(self):

        molType = self.molTypePulldown.getText()
        availableChemComps = self.project._chemCompsData
        availableChemComps = availableChemComps[availableChemComps.molType == molType]
        availableCcpCodes = availableChemComps.ccpCode.unique()
        valueCcpCodes = self.sequenceCcpCodeEditor.toPlainText().split(',')
        notFound = []
        for code in valueCcpCodes:
            if code not in availableCcpCodes:
                notFound.append(code)
        if len(notFound)>0:
            return False, notFound
        else:
            return True, []

    @queueStateChange(_verifyPopupApply)
    def _queueSetSequence(self, *args, **kwds):
        """Queue changes to sequence
        """
        value = ''
        if self.sequence1CodeEditor.isVisible():
            value = self.sequence1CodeEditor.getSequence()
        elif self.sequence3CodeEditor.isVisible():
            value = self.sequence3CodeEditor.getSequence()

        prefValue = self.obj.sequence
        if value != prefValue:
            return partial(self._setsequence, value)

    @queueStateChange(_verifyPopupApply)
    def _queueSetSequenceCcpCode(self):
        value = self.sequenceCcpCodeEditor.toPlainText()
        codes = value.split(',')
        codes = [f'{code}' for code in codes]
        prefValue = self.obj.sequenceCcpCodes or None
        if codes != prefValue:
            return partial(self._setSequenceCcpCode, codes)

    def _setsequence(self, value: str):
        """Sets the sequence
        """
        value = value.replace(' ', '')
        value = value.replace('\n', '')
        self.obj.sequence = value

    def _setSequenceCcpCode(self, values: str):
        """Sets the sequence
        """
        formattedValues = []
        for value in values:
            value = value.replace(' ', '')
            value = value.replace('\n', '')
            formattedValues.append(value)
        self.obj.sequenceCcpCodes = formattedValues

    @queueStateChange(_verifyPopupApply)
    def _queueSetMolType(self, value):
        """Queue changes to molecule type
        """
        value = self.molTypes[value]
        if value != self.obj.molType:
            return partial(self._setMolType, value)

    def _setMolType(self, value: str):
        """Sets the molecule type
        """
        self.obj.molType = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetMakeCyclic(self, value):
        """Queue changes to the SetV
        """
        prefValue = self.obj.isCyclic
        if value != prefValue:
            return partial(self._setMakeCyclic, value)

    def _setMakeCyclic(self, value: str):
        """Sets cyclic state of molecule being created.
        """
        self.obj.isCyclic = value
