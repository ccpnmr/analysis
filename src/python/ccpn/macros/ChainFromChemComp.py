"""
This macro opens a popup for creating a chain from a ChemComp saved as xml file.
A new chain containing only one residue corresponding to the small molecule and its atoms.
Atoms are named as defined in the ChemComp file.
Residue name is set from the chemComp ccpCode.
Note. Also a substance will be added in the project.

ChemComps are available from
    - https://github.com/VuisterLab/CcpNmr-ChemComps/tree/master/data/pdbe/chemComp/archive/ChemComp
    or
    - build your own using ChemBuild:
        - open chembuild
        - new compound
        - export CCPN ChemComp XML File

Run the macro and select the Xml file.

Alpha released in Version 3.0.3
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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-04-09 10:45:12 +0100 (Fri, April 09, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2021-03-05 11:01:32 +0000 (Fri, March 05, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================


from ccpn.core.Chain import _fetchChemCompFromFile, _newChainFromChemComp
from ccpn.ui.gui.widgets.FileDialog import ChemCompFileDialog
from ccpn.util.Logging import getLogger


from PyQt5 import QtCore, QtGui, QtWidgets
import ccpn.ui.gui.widgets.CompoundWidgets as cw
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.ui.gui.widgets.MoreLessFrame import MoreLessFrame
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.lib.GuiPath import PathEdit
from ccpn.ui.gui.widgets import MessageDialog
import traceback

A = str(u"\u212B")

AddAtomGroups = 'expandFromAtomSets'
AddPseudoAtoms = 'addPseudoAtoms'
RemoveDuplicateEquivalentAtoms = 'removeDuplicateEquivalentAtoms'
AddNonstereoAtoms = 'addNonstereoAtoms'
SetBoundsForAtomGroups = 'setBoundsForAtomGroups'
AtomNamingSystem = 'atomNamingSystem'
PseudoNamingSystem = 'pseudoNamingSystem'
ChainCode = 'chainCode'

DefaultAddAtomGroups = True
DefaultAddPseudoAtoms = False
DefaultRemoveDuplicateEquivalentAtoms = False
DefaultAddNonstereoAtoms = False
DefaultSetBoundsForAtomGroups = False
DefaultAtomNamingSystem = 'PDB_REMED'
DefaultPseudoNamingSystem = 'AQUA'
DefaultChainCode = 'Lig'

DefaultOptions = {
                ChainCode: DefaultChainCode,
                AddAtomGroups: DefaultAddAtomGroups,
                AddPseudoAtoms: DefaultAddPseudoAtoms,
                RemoveDuplicateEquivalentAtoms: DefaultRemoveDuplicateEquivalentAtoms,
                AddNonstereoAtoms: DefaultAddNonstereoAtoms,
                SetBoundsForAtomGroups: DefaultSetBoundsForAtomGroups,
                AtomNamingSystem: DefaultAtomNamingSystem,
                PseudoNamingSystem: DefaultPseudoNamingSystem,
                }


class NewChainFromChemComp(CcpnDialogMainWidget):
    """

    """
    FIXEDWIDTH = True
    FIXEDHEIGHT = False

    title = 'New Chain From ChemComp'
    def __init__(self, parent=None, mainWindow=None, title=title,  **kwds):
        super().__init__(parent, setLayout=True, windowTitle=title,
                         size=(400, 200), minimumSize=None, **kwds)

        if mainWindow:
            self.mainWindow = mainWindow
            self.application = mainWindow.application
            self.current = self.application.current
            self.project = mainWindow.project

        else:
            self.mainWindow = None
            self.application = None
            self.current = None
            self.project = None

        self._createWidgets()

        # enable the buttons
        self.tipText = 'Create a new Chain from a selected ChemComp'
        self.setOkButton(callback=self._okCallback, tipText =self.tipText, text='Ok', enabled=True)
        self.setCloseButton(callback=self.reject, tipText='Close')
        self.setDefaultButton(CcpnDialogMainWidget.CLOSEBUTTON)
        self.__postInit__()
        self._okButton = self.dialogButtons.button(self.OKBUTTON)

    def _createWidgets(self):

        row = 0

        self.filePathW = Widget(self.mainWidget, setLayout=True, grid=(row, 0), gridSpan=(1, 1))
        self.filePathLabel = Label(self.filePathW, text="ChemComp Path", grid=(0, 0), )
        self.filePathEdit = PathEdit(self.filePathW, grid=(0, 1), vAlign='t', tipText='')
        # self.filePathEdit.setMinimumWidth(100)
        self.filePathButton = Button(self.filePathW, grid=(0, 2), callback=self._getUserPipesPath,
                                          icon='icons/directory', hPolicy='fixed')
        # self.userPipesPath.textChanged.connect(None)

        row += 1
        self.chainCodeW = cw.EntryCompoundWidget(self.mainWidget, labelText='Chain Code',
                                                 entryText=DefaultOptions.get(DefaultChainCode),
                                                 grid=(row, 0), gridSpan=(1, 1))


        row += 1
        self.addAtomGroupsW = cw.CheckBoxCompoundWidget(self.mainWidget,
                                                         labelText='Expand Atoms from Atom Groups',
                                                         checked=DefaultOptions.get(AddAtomGroups, True),
                                                         grid=(row, 0), gridSpan=(1, 1))

        row += 1


        _frame = MoreLessFrame(self.mainWidget, name='Advanced', showMore=False, grid=(row, 0), gridSpan=(1, 2))
        advContentsFrame = _frame.contentsFrame

        advRow = 0


        self.addNonstereoAtomsW = cw.CheckBoxCompoundWidget(advContentsFrame,
                                                            labelText='Add Non Stereo-Specific Atom',
                                                            checked=DefaultOptions.get(AddNonstereoAtoms),
                                                            grid=(advRow, 0), gridSpan=(1, 1))

        # advRow += 1
        # self.addPseudoAtomsW = cw.CheckBoxCompoundWidget(advContentsFrame,
        #                                                  labelText='Add Pseudo-Atom Groups',
        #                                                  checked=DefaultOptions.get(AddPseudoAtoms, False),
        #                                                  grid=(advRow, 0), gridSpan=(1, 1))
        # advRow += 1
        # self.pseudoNamingSystemsW = cw.PulldownListCompoundWidget(advContentsFrame,
        #                                                           labelText='Pseudo-Atoms Naming Systems',
        #                                                           texts=NamingSystems,
        #                                                           default=DefaultOptions.get(PseudoNamingSystem),
        #                                                           grid=(advRow, 0), gridSpan=(1, 1))
        #
        # advRow += 1
        # self.renamePseudoAtomsW = cw.CheckBoxCompoundWidget(advContentsFrame,
        #                                                  labelText='Rename Pseudo-Atoms with the selected Naming System',
        #                                                  checked=DefaultOptions.get(RemoveDuplicateEquivalentAtoms),
        #                                                  grid=(advRow, 0), gridSpan=(1, 1))
        #
        #
        # advRow += 1
        # self.setBoundsForAtomGroupsW = cw.CheckBoxCompoundWidget(advContentsFrame,
        #                                                                   labelText='Set Bounds for Pseudo-Atom Groups',
        #                                                                   checked=DefaultOptions.get(SetBoundsForAtomGroups),
        #                                                                   grid=(advRow, 0), gridSpan=(1, 1))
        #
        # advRow += 1

        self.mainWidget.getLayout().setAlignment(QtCore.Qt.AlignRight)
        self._populateWsFromProjectInfo()

    def _populateWsFromProjectInfo(self):
        from ccpn.ui.gui.popups.CreateChainPopup import _nextChainCode
        if self.project:
            chainCode = _nextChainCode(self.project)
            self.chainCodeW.setText(chainCode)

    def _getUserPipesPath(self):
        if self.project:
            dial = ChemCompFileDialog(self.mainWindow, acceptMode='select')
            dial._show()
            filePath = dial.selectedFile()
            if filePath:
                self.filePathEdit.setText(filePath)

    @property
    def params(self):
        return self._params

    @params.getter
    def params(self):
        _params = DefaultOptions
        _params.update({ChainCode: self.chainCodeW.getText() or _params[ChainCode]})
        _params.update({AddAtomGroups: self.addAtomGroupsW.get() or _params[AddAtomGroups]})
        _params.update({AddNonstereoAtoms: self.addNonstereoAtomsW.get() or _params[AddNonstereoAtoms] })
        _params.update({AddPseudoAtoms: self.addPseudoAtomsW.get() or _params[AddPseudoAtoms]})
        # _params.update({PseudoNamingSystem: self.pseudoNamingSystemsW.getText() or _params[PseudoNamingSystem]})
        # _params.update({RemoveDuplicateEquivalentAtoms: self.renamePseudoAtomsW.get() or _params[RemoveDuplicateEquivalentAtoms]})
        # _params.update({SetBoundsForAtomGroups: self.setBoundsForAtomGroupsW.get() or _params[SetBoundsForAtomGroups]})
        return _params

    def _okCallback(self):
        if self.project:
            filePath = self.filePathEdit.get()
            if filePath:
                expandFromAtomSets =  self.addAtomGroupsW.get() or DefaultOptions[AddAtomGroups]
                addNonstereoAtoms = self.addNonstereoAtomsW.get() or DefaultOptions[AddNonstereoAtoms]

                try:
                    chemComp = _fetchChemCompFromFile(self.project, filePath)

                    chain = _newChainFromChemComp(self.project, chemComp,
                                                  chainCode = self.chainCodeW.getText(),
                                                  expandFromAtomSets = expandFromAtomSets,
                                                  addNonstereoAtoms = addNonstereoAtoms
                                                  )
                    getLogger().info("New Chain available from SideBar")
                except Exception as err:

                    MessageDialog.showError('Error creating Chain from File', str(err))

            else:
                getLogger().warning('No selected file. Chain from ChemComp Aborted')

        self.accept()

if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    # app = TestApplication()
    popup = NewChainFromChemComp(mainWindow=mainWindow)
    popup.show()
    popup.raise_()
    # app.start()




