"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2023-06-12 17:57:05 +0100 (Mon, June 12, 2023) $"
__version__ = "$Revision: 3.1.1 $"
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
from ccpn.core.lib.ContextManagers import queueStateChange, catchExceptions


DefaultAddAtomGroups = True
DefaultAddPseudoAtoms = False
DefaultAddNonstereoAtoms = True
DefaultSetBoundsForAtomGroups = False


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
        self.lineEdit1a.valueChanged.connect(self._queueSetSequenceStart)
        self.lineEdit2a.textChanged.connect(self._queueSetChainCode)
        self.sequenceEditor.textChanged.connect(self._queueSetSequence)
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
        self._code = _nextChainCode(self.project)
        self.lineEdit2a = LineEdit(self.mainWidget, grid=(row, 3), text=self._code)

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
                                           tipText=tipText7a, grid=(row, 1), )
        row += 1
        tipText8a = "E.g., for a VAL residue, the set of HG11, HG12, HG13 (NMR equivalent) atoms\n" \
                    "        will create a new atom HG1% and an extra pseudo-atom MG1;\n" \
                    "        also the set HG1%, HG2% will create a new atom HG% and an extra pseudo-atom QG.\n" \
                    "This option is available only if 'Expand Atoms From AtomSets' is selected and proton groups."
        label8a = Label(self.mainWidget, 'Add extra Pseudo-Atoms', tipText=tipText8a, grid=(row, 0))
        self.addPseudoAtomsW = CheckBox(self.mainWidget, checked=DefaultAddPseudoAtoms,
                                        tipText=tipText8a, grid=(row, 1), )
        self._togglePseudoAtomOptions(self.expandAtomsFromAtomSetW.get())

        row += 1
        tipText9a = "Make a cyclic polymer;\n" \
                    "    H1, H2, H3 and OXT atoms will be removed."
        label8a = Label(self.mainWidget, 'Cyclic Polymer', tipText=tipText9a, grid=(row, 0))
        self.makeCyclicPolymer = CheckBox(self.mainWidget, checked=False,
                                          tipText=tipText9a, grid=(row, 1), )

    def _defineObject(self):
        """Initialise the new object
        """
        # define the blank object to hold the new attributes
        self.obj = AttrDict()
        self.obj.compoundName = None
        self.obj.startNumber = 1
        self.obj.shortName = self._code
        self.obj.sequence = None
        self.obj.comment = None
        self.obj.molType = self.molTypes[0]
        self.obj.expandFromAtomSets = DefaultAddAtomGroups
        self.obj.addPseudoAtoms = DefaultAddPseudoAtoms
        self.obj.addNonstereoAtoms = DefaultAddNonstereoAtoms
        self.obj.isCyclic = False

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
                self.makeCyclicPolymer.set(self.obj.isCyclic)

    def _createSequence(self):
        """Creates a sequence using the values specified in the text widget.
        Single-letter codes must be entered with no spacing
        Three-letter codes can be entered as space or <return> separated
        """
        with catchExceptions(self.application):
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
        value = (
            tuple(value.split())
            if ' ' in value
            else self.sequenceEditor.toPlainText()
        )
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
