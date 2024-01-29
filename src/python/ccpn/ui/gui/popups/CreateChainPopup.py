"""
Module Documentation here

 'Ala Leu Ala Leu Ala Ser Asp Glu Trp Val Leu Ala Leu Ala Leu Leu Ala Ala Trp Glu Arg Thr Leu Ala Ala Trp Glu Arg Thr Tyr Tyr Ala Leu Leu Ala Ala Trp Glu Arg Thr Tyr'
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
__dateModified__ = "$dateModified: 2024-01-29 11:45:33 +0000 (Mon, January 29, 2024) $"
__version__ = "$Revision: 3.2.2 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-07-04 15:21:16 +0000 (Tue, July 04, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import string
import numpy as np
from functools import partial
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.core.lib.MoleculeLib import _nextChainCode
import textwrap
import pandas as pd
from ccpn.core.Chain import Chain
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.Menu import Menu
from ccpn.ui.gui.widgets.Tabs import Tabs
from PyQt5 import QtGui
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.popups.AttributeEditorPopupABC import AttributeEditorPopupABC
from ccpn.util.AttrDict import AttrDict
from ccpn.ui.gui.popups.Dialog import _verifyPopupApply
from ccpn.core.lib.ContextManagers import queueStateChange
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from PyQt5.QtCore import Qt
from ccpn.core.lib.ChainLib import SequenceHandler, CCPCODE, CODE1LETTER, CODE3LETTER
from ccpn.framework.Application import getProject
from bs4 import BeautifulSoup
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QTextCharFormat

DefaultAddAtomGroups = True
DefaultAddPseudoAtoms = False
DefaultAddNonstereoAtoms = True
DefaultSetBoundsForAtomGroups = False
ONELETTERCODE = 'One-Letter Code'
THREELETTERCODE = 'Three-Letter Code'
CCPCODESELECTION = 'Ccp Code'

def divideChunks(l, n):
  for i in range(0, len(l), n):
    yield l[i:i + n]


class _SequenceTextEditorBase(TextEditor):
    textChangedSignal = pyqtSignal()
    _codeType = CODE1LETTER

    demoSequence = 'ABCD'
    extraContextMenuActions = {
        'Copy Selected as 1LetterCodes' : { 'callback':None, 'enabled':True},
        'Copy Selected as 3LetterCodes': {'callback': None, 'enabled': True},
        'Copy Selected as CcpCodes': {'callback': None, 'enabled': True},
        }

    def __init__(self, parent, parentPopup, sequenceStartsAt=1,  maxColumns=10,  **kwargs):
        super().__init__(parent, backgroundText=self.demoSequence,  **kwargs)

        self.parentPopup = parentPopup # needed to get notifications on dynamic value changes.
        self.maxColumns = maxColumns
        self.sequenceStartsAt = sequenceStartsAt
        self._project = getProject()
        self._molType = self._getMolType()
        self._sequenceHandler = SequenceHandler(self._project, moleculeType=self._molType)
        self.sequenceStartsAt = 13# self.parentPopup.startingSequenceCodeWidget.get()
        self.parentPopup.startingSequenceCodeWidget.valueChanged.connect(self._setStartingSequenceCode)
        self.parentPopup.molTypePulldown.currentIndexChanged.connect(self._setMolType)
        self.textChangedSignal.connect(self._textChangedCallback)
        self.setPlaceholderText(str(self.backgroundText))


    def toPlainText(self):
        html_string = self.toHtml()
        soup = BeautifulSoup(html_string, 'html.parser')
        # Find and extract all <span> tags with style attribute for subscript
        subscripts = soup.find_all('span', style=lambda value: value and 'vertical-align:sub' in value)

        # Remove the found <span> tags
        for sub in subscripts:
            sub.decompose()
        # Get the modified HTML content
        textStrip = soup.getText(' ', strip=True)
        return textStrip

    def _textChangedCallback(self):
        text = self.toPlainText()
        with self.blockWidgetSignals():
            self.setSequence(text)

    def setSequence(self, sequence:str):
        df = self._sequenceToDataFrame(sequence)
        sequenceHtml = self._dataFrameToHtml(df, )
        self.setHtml(sequenceHtml)

    def getSequence(self):
        text = self.toPlainText()
        sequenceMap = self._sequenceHandler.parseSequence(text)
        formattedSequence = sequenceMap.get(self._codeType)
        return formattedSequence

    def getSequenceAsCcpCode(self):
        text = self.toPlainText()
        sequenceMap = self._sequenceHandler.parseSequence(text)
        ccpCodeSequence = sequenceMap.get(CCPCODE)
        return ccpCodeSequence

    def _sequenceToDataFrame(self, text):
        if self._codeType in [CODE1LETTER, CODE3LETTER]:
            text = text.upper()

        sequence = self._sequenceHandler.parseSequence(text)
        formattedSequence = sequence.get(self._codeType)
        df = self._listToDataFrame(formattedSequence, maxColumns=self.maxColumns, startAccumulatedCount=1)
        return df

    def isMultipleOfMaxColumnsCount(self, number):
        return number % self.maxColumns == 0

    @staticmethod
    def _listToDataFrame(stringList, maxColumns=10, startAccumulatedCount=1):
        """ Create a dataframe given a list of string. Each item is a code in the sequence.
        Make a maximum of column. Start an accumulated value count from a given starting point.
        Index= the accumulated values"""
        numRows = len(stringList) // maxColumns
        if len(stringList) % maxColumns != 0:
            numRows += 1
        # Pad the string list with None to make it rectangular
        stringList = stringList + [None] * (numRows * maxColumns - len(stringList))
        data = [stringList[i:i + maxColumns] for i in range(0, len(stringList), maxColumns)]
        df = pd.DataFrame(data)
        accumulatedCount = df.apply(lambda row: row.count(), axis=1).cumsum() + startAccumulatedCount - 1
        df.set_index(accumulatedCount, inplace=True)
        return df

    def _dataFrameToHtml(self, dataFrame):
        allowedValues = []
        html = "<table style='border-collapse: collapse; width: 100%;'>"

        for i, (inx, row) in enumerate(dataFrame.iterrows()):
            html += "<tr>"
            for j, (inxRow, value) in enumerate(row.items(), start=0):
                underline_style = ''
                subscript = ''
                if value:
                    cc = self.sequenceStartsAt + j
                    if j == 4:
                        value += f'<sub>{j + 1}</sub>'
                    # underline_style = 'text-decoration: underline;' if self.isMultipleOfMaxColumnsCount(cc) else ''
                cleanedValue = str(value).replace(' ', '').replace(',', '').replace('None', '')
                cellColor = 'red' if cleanedValue not in allowedValues else 'black'
                html += f"<td style='color: {cellColor}; text-align: center; padding: 3px; {subscript} '>{cleanedValue}</td>"
            html += "</tr>"
        html += "</table>"
        return html

    def _update(self):
        self._textChangedCallback()

    def _getMolType(self):
        return self.parentPopup.molTypePulldown.get()

    def _setStartingSequenceCode(self, *args):
        self.sequenceStartsAt = self.parentPopup.startingSequenceCodeWidget.get()
        self._update()

    def _setMolType(self, *args):
        self._molType = self.parentPopup.molTypePulldown.get()
        self._update()

    def context_menu(self):
        self.standardContextMenu = self.createStandardContextMenu()
        # Create a custom context menu
        self.customContextMenu = menu = Menu('Editor', self)
        self.customContextMenu.addActions(self.standardContextMenu.actions())  # Add standard actions
        self.customContextMenu.addSeparator()
        for key, values in self.extraContextMenuActions.items():
            menu.addItem(text=key, callback=values.get('callback'), enabled=values.get('enabled'))
        self.customContextMenu.exec_(QtGui.QCursor.pos())

    def _copySelectedAs1CodeLetter(self):
        pass

    def _copySelectedAs3CodeLetter(self):
        pass

    def _copySelectedAsCcpCode(self):
        pass


class _1LetterCodeSequenceEditor(_SequenceTextEditorBase):

    _codeType = CODE1LETTER
    _name = ONELETTERCODE
    demoSequence = '''Standard residues only: ALSTWYA'''

    extraContextMenuActions = {
        'Copy Selected as 1LetterCodes': {'callback': None, 'enabled': True},
        'Copy Selected as 3LetterCodes': {'callback': None, 'enabled': True},
        'Copy Selected as CcpCodes'    : {'callback': None, 'enabled': True},
        }


    def keyPressEvent(self, event):

        text = event.text()
        alphabet = string.ascii_uppercase

        if event.key() in [
                           Qt.Key_Return,
                            Qt.Key_Enter]:
            self.textChangedSignal.emit()
        elif text in alphabet:
            allowed = self._sequenceHandler.getAvailableCode1Letter(onlyStandard=True)
            notAllowed = set(alphabet) - set(allowed)
            if text.upper() in allowed:
                self.insertPlainText(text.upper())
            elif text.upper in notAllowed:
                showWarning('Not allowed', 'One-Letter code  not recognised. Use standard residues only.')
            else:
                print('event.key()', event.key())
                super().keyPressEvent(event)
        else:
            print('event.key() _codeType:', event.key())
            super().keyPressEvent(event)


class _3LetterCodeSequenceEditor(_SequenceTextEditorBase):
    _codeType = CODE3LETTER
    _name = THREELETTERCODE
    demoSequence = '''Standard residues only: ALA ARG ASN'''

class _CcpCodeSequenceEditor(_SequenceTextEditorBase):
    _codeType = CCPCODE
    _name = CCPCODESELECTION

    demoSequence = '''Any CcpCode: \n Ala Arg Ser or \n Ala Arg Ser Atp or \n MyCcpCode etc '''
    extraContextMenuActions = {
        'Copy Selected as CcpCodes'    : {'callback': None, 'enabled': True},
        }


class _SequenceTabs(Tabs):
    def __init__(self, parent, parentPopup, **kwds):
        super().__init__(parent, **kwds)
        self._tabEditors = {}
        self._parentPopup = parentPopup
        self._editorsClasses = [_1LetterCodeSequenceEditor,  _3LetterCodeSequenceEditor, _CcpCodeSequenceEditor]
        for i, editorCls in enumerate(self._editorsClasses):
            editor = editorCls(self, parentPopup=self._parentPopup)
            self._tabEditors[editor._name] = editor
            self.addTab(editor, editor._name)

    def getSequence(self):
        tabName = self.getSelectedTabText()
        sequenceEditor =  self._tabEditors.get(tabName)
        sequence = sequenceEditor.getSequence()
        return sequence

    def getCcpCodeSequence(self):
        tabName = self.getSelectedTabText()
        sequenceEditor = self._tabEditors.get(tabName)
        sequence = sequenceEditor.getSequenceAsCcpCode()
        return sequence

    def setSequence(self, sequence, editorName=None):
        if editorName is None: #set  the sequence to all tabs
            for k, sequenceEditor in self._tabEditors.items():
                sequenceEditor.setSequence(sequence)
        else:
            sequenceEditor = self._tabEditors.get(editorName)
            if sequenceEditor is not None:
                sequenceEditor.setSequence(sequence)
                self.selectTabText(editorName)


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
        # attach the callbacks for the widgets
        self.moleculeEdit.textChanged.connect(self._queueSetMoleculeName)
        self.commentName.textChanged.connect(self._queueSetComment)
        self.startingSequenceCodeWidget.valueChanged.connect(self._queueSetSequenceStart)
        self.lineEdit2a.textChanged.connect(self._queueSetChainCode)

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
        minimumWidth = 200
        minimumWidthEditors = 400
        minimumHeightEditors = 300

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

        row += 1
        label = Label(self.mainWidget, 'Sequence Start', grid=(row, 0))
        self.startingSequenceCodeWidget = Spinbox(self.mainWidget, grid=(row, 1), value=1, min=-1000000,
                                                  max=1000000, hAlign='left', minimumWidth=minimumWidth)
        row += 1
        label3a = Label(self.mainWidget, text="Sequence", grid=(row, 0))
        self.sequenceTabWidget = _SequenceTabs(self.mainWidget, parentPopup=self,
                                                     setLayout=True, grid=(row, 1), gridSpan=(1, 3),
                                                      minimumWidth=minimumWidthEditors,
                                                      minimumHeight=minimumHeightEditors)
        self.sequenceTabWidget.setSequence('AAWWQAAAAAAAWWQAAAAAAAWWQAAAAAAAWWQAAAAA')

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

                if self.obj.sequenceCcpCodes:
                    sequenceCcpCodes = ','.join(self.obj.sequenceCcpCodes)
                    self.sequenceTabWidget.setSequence(sequenceCcpCodes, editorName=CCPCODESELECTION)
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
        self.obj.sequenceCcpCodes = self.sequenceTabWidget.getCcpCodeSequence()
        self.project.createChain(**self.obj)

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


    def _validateSequence(self, *args):

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
