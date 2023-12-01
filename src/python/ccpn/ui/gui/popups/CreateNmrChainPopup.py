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
__dateModified__ = "$dateModified: 2023-12-01 19:07:04 +0000 (Fri, December 01, 2023) $"
__version__ = "$Revision: 3.2.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2018-02-07 15:28:41 +0000 (Wed, February 02, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.RadioButton import RadioButton
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.widgets.PulldownListsForObjects import NmrChainPulldown, ChainPulldown, SELECT, SubstancePulldown, ComplexPulldown
from ccpn.ui.gui.widgets.Font import getFontHeight
from ccpn.core.NmrChain import NmrChain
from ccpn.core.Chain import Chain
from ccpn.core.Substance import Substance
from ccpn.core.Complex import Complex
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar, notificationEchoBlocking


CHAIN = Chain.className
NMRCHAIN = NmrChain.className
SUBSTANCE = Substance.className
COMPLEX = Complex.className

Cancel = 'Cancel'
Create = 'Create'
COPYNMRCHAIN = '-Copy'
CloneOptions = [CHAIN, NMRCHAIN, SUBSTANCE, COMPLEX]

CHAINTipText = 'Clones an NmrChain from a Chain. All the nmrResidues and nmrAtoms will be created.'
NMRCHAINTipText = 'Clones an NmrChain from a NmrChain. All the nmrResidues and nmrAtoms will be created.'
SUBSTANCETipText = 'Creates an NmrChain from a Substance which contains a single nmrResidue. If the SMILES is set, nmrAtoms will be created.'
COMPLEXTipText = 'Clones an nmrChain for each chain present in the complex. All the nmrResidues and nmrAtoms will be created.'

CloneOptionsTipTexts = [CHAINTipText, NMRCHAINTipText, SUBSTANCETipText, COMPLEXTipText]


class CreateNmrChainPopup(CcpnDialogMainWidget):

    def __init__(self, parent=None, mainWindow=None, project=None, **kwds):
        # project is a 'dummy' argument to be compatible with the sideBar callback's

        super().__init__(parent, setLayout=True, margins=(10, 10, 10, 10),
                         windowTitle='Create NmrChain', size=(300, 200), **kwds)

        self._parent = parent
        self.mainWindow = mainWindow
        self.project = project if project is not None else self.mainWindow.project

        # set up the widgets
        self._setWidgets()

        # set the dialog buttons
        self.setOkButton(callback=self._applyChanges, text='Create')
        self.setCloseButton(callback=self.reject)
        self.setDefaultButton(CcpnDialogMainWidget.CLOSEBUTTON)

    def _postInit(self):
        # initialise the buttons and dialog size
        super()._postInit()
        self._createButton = self.dialogButtons.button(self.OKBUTTON)
        self._closeButton = self.dialogButtons.button(self.CLOSEBUTTON)

        self._resetObjectSelections()
        self._setCreateButtonEnabled(True)
        self.createNewWidget.setChecked(True)
        # self._activateCloneOptions()
        self._selectCreateEmpty()

    def _setWidgets(self):
        """Set up the widgets
        """
        _topWidget = self.mainWidget

        # GUI
        vGrid = 0
        self.createNewLabel = Label(_topWidget, text="Create New", grid=(vGrid, 0))
        self.createNewWidget = RadioButton(_topWidget,
                                           callback=self._selectCreateEmpty,
                                           grid=(vGrid, 1),
                                           )
        vGrid += 1
        _topWidget.addSpacer(0, 10, grid=(vGrid, 0))
        vGrid += 1
        self.cloneFromLabel = Label(_topWidget, text="Clone from", grid=(vGrid, 0))
        self.cloneOptionsWidget = RadioButtons(_topWidget, texts=CloneOptions,
                                               callback=self._cloneOptionCallback,
                                               direction='v',
                                               tipTexts=CloneOptionsTipTexts,
                                               grid=(vGrid, 1),
                                               vAlign='c'
                                               )
        vGrid += 1
        _topWidget.addSpacer(5, int(1.2 * getFontHeight()), grid=(vGrid, 0), gridSpan=(5, 1))  # hack :|

        vGrid += 1
        self.availableChainsPD = ChainPulldown(_topWidget, self.mainWindow, showSelectName=True, callback=self._populateWidgets, labelText='', tipText=CHAINTipText,
                                               grid=(vGrid, 1), )
        self.availableChainsPD.label.hide()
        self.availableChainsPD.hide()
        vGrid += 1
        self.availableNmrChainsPD = NmrChainPulldown(_topWidget, self.mainWindow, showSelectName=True, callback=self._populateWidgets, labelText='',
                                                     tipText=NMRCHAINTipText, grid=(vGrid, 1))
        self.availableNmrChainsPD.label.hide()
        self.availableNmrChainsPD.hide()
        vGrid += 1
        self.availableComplexesPD = ComplexPulldown(_topWidget, self.mainWindow, showSelectName=True,
                                                    callback=self._populateWidgets, labelText='', tipText=COMPLEXTipText, grid=(vGrid, 1))
        self.availableComplexesPD.label.hide()
        self.availableComplexesPD.hide()
        vGrid += 1
        tipText = SUBSTANCETipText
        self.availableSubstancesPD = SubstancePulldown(_topWidget, self.mainWindow, showSelectName=True,
                                                       callback=self._populateWidgets, labelText='', tipText=tipText, grid=(vGrid, 1))
        self.availableSubstancesPD.label.hide()
        self.availableSubstancesPD.hide()
        self.pulldownsOptions = {NMRCHAIN : self.availableNmrChainsPD, CHAIN: self.availableChainsPD,
                                 SUBSTANCE: self.availableSubstancesPD, COMPLEX: self.availableComplexesPD}

        vGrid += 1
        _topWidget.addSpacer(0, 10, grid=(vGrid, 0))
        vGrid += 1
        self.labelName = Label(_topWidget, text="Name", grid=(vGrid, 0), )
        self.nameLineEdit = LineEdit(_topWidget, grid=(vGrid, 1), textAlignment='left')
        vGrid += 1
        # self.spacerLabel = Label(_topWidget, text="", grid=(vGrid, 0))
        _topWidget.addSpacer(0, 10, grid=(vGrid, 0))

    def unRegister(self):
        """Un-register notifiers
        """
        if self.availableChainsPD:
            self.availableChainsPD.unRegister()
        if self.availableNmrChainsPD:
            self.availableNmrChainsPD.unRegister()
        if self.availableComplexesPD:
            self.availableComplexesPD.unRegister()
        if self.availableSubstancesPD:
            self.availableSubstancesPD.unRegister()

    def accept(self):
        """Create button has been clicked
        """
        self.unRegister()
        super().accept()

    def reject(self) -> None:
        """Create button has been clicked
        """
        self.unRegister()
        super().reject()

    def _resetObjectSelections(self):
        # used to create a new nmrChain from a selected object.
        self._createEmpty = False
        self._chain = None
        self._nmrChain = None
        self._substance = None
        self._complex = None

    def _selectCreateEmpty(self):
        # Gui bit
        self.cloneOptionsWidget.deselectAll()
        if not self.createNewWidget.isChecked():
            # self.buttonBox.setButtonEnabled(Create, False)
            self._createButton.setEnabled(False)
        else:
            self._setCreateButtonEnabled(False)
        for h in self.pulldownsOptions:
            self.pulldownsOptions[h].hide()

        # if self.nameLineEdit.receivers(self.nameLineEdit.textEdited):     # may be other slots?
        try:
            self.nameLineEdit.textEdited.disconnect(self._cloneChainEdit)
        except Exception:
            pass
        finally:
            self.nameLineEdit.textEdited.connect(self._newChainEdit)

        # FIXME Not an elegant solution
        self._resetObjectSelections()
        self._createEmpty = True

    def _newChainEdit(self):
        self._setCreateButtonEnabled(bool(self.nameLineEdit.text()))

    def _cloneChainEdit(self):
        for cl, pulldown in self.pulldownsOptions.items():
            rButton = self.cloneOptionsWidget.getRadioButton(cl)
            if rButton.isChecked():
                self._setCreateButtonEnabled(bool(self.nameLineEdit.text() and pulldown.getText() != SELECT))

                break

    def _createEmptyNmrChain(self, name):
        if not self.project.getByPid(f'{NmrChain.shortClassName}:{name}'):
            return self.project.newNmrChain(name)

        showWarning('Existing NmrChain name.', 'Change name')

    def _isNmrChainNameExisting(self, name):
        return bool(self.project.getByPid(f'{NmrChain.shortClassName}:{name}'))

    def _setCreateButtonEnabled(self, value: bool = True):
        # self.buttonBox.setButtonEnabled(Create, value)
        self._createButton.setEnabled(value)

    def _cloneFromChain(self, name):
        from ccpn.util.isotopes import DEFAULT_ISOTOPE_DICT

        with undoBlockWithoutSideBar():
            with notificationEchoBlocking():
                if newNmrChain := self._createEmptyNmrChain(name):
                    if len(self._chain.residues) > 0:
                        for residue in self._chain.residues:
                            nmrResidue = newNmrChain.newNmrResidue(sequenceCode=residue.sequenceCode,
                                                                   residueType=residue.residueType)
                            for atom in residue.atoms:
                                isotopeCode = DEFAULT_ISOTOPE_DICT.get(atom.elementSymbol)
                                nmrResidue.newNmrAtom(atom.name, isotopeCode=isotopeCode)  # is not a fetch but new. cannot be already one!
                    return newNmrChain

    def _cloneFromNmrChain(self, name):
        with undoBlockWithoutSideBar():
            with notificationEchoBlocking():
                if newNmrChain := self._createEmptyNmrChain(name):
                    if len(self._nmrChain.nmrResidues) > 0:
                        for nmrResidue in self._nmrChain.nmrResidues:

                            # need to check whether the mainResidue exists before creating the +/- residues
                            if nmrResidue.relativeOffset:
                                mainSequence = nmrResidue.mainNmrResidue.sequenceCode
                                newNmrResidue = newNmrChain.newNmrResidue(sequenceCode=mainSequence,
                                                                          residueType=nmrResidue.residueType)
                            newNmrResidue = newNmrChain.newNmrResidue(sequenceCode=nmrResidue.sequenceCode, residueType=nmrResidue.residueType)
                            for nmrAtom in nmrResidue.nmrAtoms:
                                newNmrResidue.fetchNmrAtom(nmrAtom.name, isotopeCode=nmrAtom.isotopeCode)

                    return newNmrChain

    def _cloneFromSubstance(self, name):
        """Create a new nmr chain from a substance which has a SMILES set."""
        with undoBlockWithoutSideBar():

            if newNmrChain := self._createEmptyNmrChain(name):
                from ccpn.ui.gui.widgets.CompoundView import CompoundView, Variant, importSmiles

                nmrResidue = newNmrChain.newNmrResidue(name)
                if self._substance.smiles:
                    compound = importSmiles(self._substance.smiles, compoundName=name)
                    for atom in compound.atoms:
                        nmrAtom = nmrResidue.fetchNmrAtom(atom.name)

                return newNmrChain

    # def _disableSubstanceWithoutSMILES(self):
    #   'disables from selection substances without SMILES'
    #   if self.project:
    #     for i, text in enumerate(self.availableSubstancesPD.textList):
    #       substance = self.project.getByPid(text)
    #       if isinstance(substance, Substance):
    #         if not substance.smiles:
    #           self.availableSubstancesPD.pulldownList.model().item(i).setEnabled(False)

    def _applyChanges(self):
        """
        The apply button has been clicked
        If there is an error setting the values then popup an error message
        repopulate the settings
        """
        try:
            self._createNmrChain()

        except Exception as es:
            showWarning(str(self.windowTitle()), str(es))
            if self.mainWindow.application._isInDebugMode:
                raise es

    def _createNmrChain(self):
        name = self.nameLineEdit.get()

        if self.project:
            # self.project.blankNotification()
            if self._createEmpty:
                if newNmrChain := self._createEmptyNmrChain(name):
                    self.accept()
                else:
                    return

            if self._chain:
                if newNmrChain := self._cloneFromChain(name):
                    self.accept()
                else:
                    return

            if self._nmrChain:
                if newNmrChain := self._cloneFromNmrChain(name):
                    self.accept()
                else:
                    return

            if self._substance:
                if newNmrChain := self._cloneFromSubstance(name):
                    self.accept()
                else:
                    return

            if self._complex:
                if name:
                    names = name.split(',')
                    for name in names:
                        exsistingNmrChain = self.project.getByPid(NmrChain.shortClassName + ':' + name)
                        if exsistingNmrChain:
                            showWarning('Existing NmrChain %s' % exsistingNmrChain.shortName, 'Change name')
                            return

                    if len(self._complex.chains) == len(names):
                        for chain, name in zip(self._complex.chains, names):
                            self._chain = chain
                            self._cloneFromChain(name)
                        self.accept()
                    else:
                        showWarning('Not enough names', 'Complex %s has %s chains, Please add the missing name/s'
                                    % (self._complex.name, len(self._complex.chains)))
                        return
                else:
                    return

            self.accept()

    def _populateWidgets(self, selected):
        self._resetObjectSelections()
        self.nameLineEdit.clear()
        self._setCreateButtonEnabled(False)
        obj = self.project.getByPid(selected)
        if isinstance(obj, NmrChain):
            self.nameLineEdit.setText(obj.shortName + COPYNMRCHAIN)
            self._nmrChain = obj
            self._setCreateButtonEnabled(True)

        if isinstance(obj, Chain):
            self._chain = obj
            if self._isNmrChainNameExisting(self._chain.shortName):
                self.nameLineEdit.setText(self._chain.shortName + COPYNMRCHAIN)
            else:
                self.nameLineEdit.setText(self._chain.shortName)
            self._setCreateButtonEnabled(True)

        if isinstance(obj, Substance):
            self._substance = obj
            if self._isNmrChainNameExisting(self._substance.name):
                self.nameLineEdit.setText(self._substance.name + COPYNMRCHAIN)
            else:
                self.nameLineEdit.setText(self._substance.name)
            self._setCreateButtonEnabled(True)

        if isinstance(obj, Complex):
            chainsNames = [chain.shortName for chain in obj.chains]
            names = []
            for name in chainsNames:
                if self._isNmrChainNameExisting(name):
                    names.append(name + COPYNMRCHAIN)
                else:
                    names.append(name)
            if names:
                self.nameLineEdit.setText(",".join(names))
                self._complex = obj
                self._setCreateButtonEnabled(True)

    def _activateCloneOptions(self):
        if not self.project:
            return
        if len(self.project.substances) == 0:
            if rb := self.cloneOptionsWidget.getRadioButton(SUBSTANCE):
                rb.setEnabled(False)
        # elif len(self.project.substances) > 0:
        #     noSmiles = [substance.smiles for substance in self.project.substances]
        #     if all(noSmiles):
        #         if rb := self.cloneOptionsWidget.getRadioButton(SUBSTANCE):
        #             rb.setEnabled(False)

        if len(self.project.chains) == 0:
            if rb := self.cloneOptionsWidget.getRadioButton(CHAIN):
                rb.setEnabled(False)

        if len(self.project.complexes) == 0:
            if rb := self.cloneOptionsWidget.getRadioButton(COMPLEX):
                rb.setEnabled(False)

    def _cloneOptionCallback(self):
        self.createNewWidget.setChecked(False)
        self._setCreateButtonEnabled(False)

        selected = self.cloneOptionsWidget.getSelectedText()
        # # needs to clear the previous selection otherwise has an odd behaviour from pulldownNofiers which remember the previous selection
        self._resetObjectSelections()
        for pd in self.pulldownsOptions:
            self.pulldownsOptions[pd].select(SELECT)
        if selected in self.pulldownsOptions:
            self.pulldownsOptions[selected].show()
        hs = [x for x in self.pulldownsOptions if x != selected]
        for h in hs:
            self.pulldownsOptions[h].hide()

        # if self.nameLineEdit.receivers(self.nameLineEdit.textEdited):
        try:
            self.nameLineEdit.textEdited.disconnect()
        except Exception:
            pass
        finally:
            self.nameLineEdit.textEdited.connect(self._cloneChainEdit)


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.popups.Dialog import CcpnDialog
    from ccpn.ui.gui.widgets.Widget import Widget


    app = TestApplication()
    popup = CreateNmrChainPopup()
    widget = Widget(parent=popup, grid=(0, 0))

    popup.show()
    popup.raise_()
    app.start()
