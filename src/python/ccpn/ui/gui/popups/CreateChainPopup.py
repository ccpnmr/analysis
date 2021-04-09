"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2021-04-09 17:22:55 +0100 (Fri, April 09, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-07-04 15:21:16 +0000 (Tue, July 04, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import string
from functools import partial
from ccpn.core.Chain import Chain
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.popups.AttributeEditorPopupABC import AttributeEditorPopupABC
from ccpn.util.AttrDict import AttrDict
from ccpn.ui.gui.popups.Dialog import _verifyPopupApply
from ccpn.core.lib.ContextManagers import queueStateChange
import ccpn.ui.gui.widgets.CompoundWidgets as cw
from ccpn.ui.gui.widgets.MoreLessFrame import MoreLessFrame


DefaultAddAtomGroups = True
DefaultAddPseudoAtoms = False
DefaultAddNonstereoAtoms = True
DefaultSetBoundsForAtomGroups = False

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

    def __init__(self, parent=None, mainWindow=None, project=None, **kwds):
        """
        Initialise the widget
        """
        # flag required because using attributeDialog which tries to populate
        self._popupReady = False

        super().__init__(parent, mainWindow=mainWindow, size=(500, 300), **kwds)

        row = 2
        label2a = Label(self.mainWidget, text="Name", grid=(row, 0))
        self.moleculeEdit = LineEdit(self.mainWidget, text="", grid=(row, 1), gridSpan=(1, 1), textAlignment='l', backgroundText='> Enter name <')
        label2b = Label(self.mainWidget, text="Molecule Type", grid=(row, 2))
        self.molTypePulldown = PulldownList(self.mainWidget, grid=(row, 3))
        row += 1

        comment = Label(self.mainWidget, text="Comment", grid=(row, 0))
        self.commentName = LineEdit(self.mainWidget, text="", grid=(row, 1), gridSpan=(1, 1), textAlignment='l', backgroundText='> Optional <')
        row += 1

        self.molTypes = ['protein', 'DNA', 'RNA', 'other']
        self.molTypePulldown.setData(self.molTypes)
        label3a = Label(self.mainWidget, text="Sequence", grid=(row, 0))
        tipText = "Sequence may be entered a set of one letter codes without\n" \
                  "spaces or a set of three letter codes with spaces inbetween"
        self.sequenceEditor = TextEditor(self.mainWidget, grid=(row, 1), gridSpan=(1, 3), tipText=tipText)
        row += 1

        label4a = Label(self.mainWidget, 'Sequence Start', grid=(row, 0))
        self.lineEdit1a = Spinbox(self.mainWidget, grid=(row, 1), value=1, min=-1000000, max=1000000)
        label5a = Label(self.mainWidget, 'Chain code', grid=(row, 2))
        code = _nextChainCode(self.project)
        self.lineEdit2a = LineEdit(self.mainWidget, grid=(row, 3), text=code)
        row += 1
        tipText6a = "E.g., for a VAL residue, the set of HG11, HG12, HG13 (NMR equivalent) atoms will create a new atom HG1%;\n" \
                    "        also the set HG1%, HG2% will create a new atom HG%"
        label6a = Label(self.mainWidget, 'Expand Atoms From AtomSets', tipText=tipText6a, grid=(row, 0))
        self.expandAtomsFromAtomSetW = CheckBox(self.mainWidget, checked=DefaultAddAtomGroups,
                                                tipText=tipText6a, grid=(row, 1))
        row += 1
        tipText7a = "Add new atoms for Non-stereo Specific Atoms (if any).\n" \
                    "E.g., for a VAL residue, HGx%, HGy% will be added if atoms HG1% and HG2% are present.\n" \
                    "This option is available only if 'Expand Atoms From AtomSets' is selected."
        label7a = Label(self.mainWidget, 'Add Non-Stereo Specific Atoms', tipText=tipText7a, grid=(row, 0))
        self.addNonstereoAtomsW = CheckBox(self.mainWidget, checked=DefaultAddNonstereoAtoms,
                                           tipText=tipText7a, grid=(row, 1),)
        row += 1
        tipText8a = "E.g., for a VAL residue, the set of HG11, HG12, HG13 (NMR equivalent) atoms\n" \
                    "        will create a new atom HG1% and an extra pseudo-atom MG1;\n" \
                    "        also the set HG1%, HG2% will create a new atom HG% and an extra pseudo-atom QG.\n" \
                    "This option is available only if 'Expand Atoms From AtomSets' is selected and proton groups."
        label8a = Label(self.mainWidget, 'Add extra Pseudo-Atoms', tipText=tipText8a, grid=(row, 0))
        self.addPseudoAtomsW = CheckBox(self.mainWidget, checked=DefaultAddPseudoAtoms,
                                        tipText=tipText8a, grid=(row, 1),)
        self._togglePseudoAtomOptions(self.expandAtomsFromAtomSetW.get())


        # define the blank object to hold the new attributes
        self.obj = AttrDict()
        self.obj.startNumber = 1
        self.obj.shortName = code
        self.obj.sequence = None
        self.obj.compoundName = None
        self.obj.comment = None
        self.obj.molType = self.molTypes[0]
        self.obj.expandFromAtomSets = DefaultAddAtomGroups
        self.obj.addPseudoAtoms = DefaultAddPseudoAtoms
        self.obj.addNonstereoAtoms = DefaultAddNonstereoAtoms

        # attach the calbacks for the widgets
        self.moleculeEdit.textChanged.connect(self._queueSetMoleculeName)
        self.commentName.textChanged.connect(self._queueSetComment)
        self.lineEdit1a.valueChanged.connect(self._queueSetSequenceStart)
        self.lineEdit2a.textChanged.connect(self._queueSetChainCode)
        self.sequenceEditor.textChanged.connect(self._queueSetSequence)
        self.molTypePulldown.currentIndexChanged.connect(self._queueSetMolType)
        self.expandAtomsFromAtomSetW.clicked.connect(self._queueSetExpandAtomsFromAtomSets)
        self.addNonstereoAtomsW.clicked.connect(self._queueSetAddNonstereoAtomsW)
        self.addPseudoAtomsW.clicked.connect(self._queueSetAddPseudoAtomsW)

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
                self.expandAtomsFromAtomSetW.set(self.obj.expandFromAtomSets)
                self.addNonstereoAtomsW.set(self.obj.addNonstereoAtoms)
                self.addPseudoAtomsW.set(self.obj.addPseudoAtoms)

    def _createSequence(self):
        """Creates a sequence using the values specified in the text widget.
        Single-letter codes must be entered with no spacing
        Three-letter codes can be entered as space or <return> separated
        """
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
        """Sets the sequence
        """
        self.obj.sequence = value

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
