#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-05-25 19:09:05 +0100 (Tue, May 25, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import re
from ccpn.core.NmrResidue import NmrResidue, _getNmrResidue
from ccpn.core.lib.AssignmentLib import CCP_CODES_SORTED, getNmrResiduePrediction
from ccpn.ui.gui.popups.AttributeEditorPopupABC import AttributeEditorPopupABC, _attribContainer
from ccpn.ui.gui.widgets.CompoundWidgets import EntryCompoundWidget, PulldownListCompoundWidget, CheckBoxCompoundWidget
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.util.OrderedSet import OrderedSet


REMOVEPERCENT = '( ?\d+.?\d* ?%)+'
MERGE = 'merge'
CREATE = 'create'
DEASSIGN = 'deassign'


def _getResidueTypeProb(self, currentNmrResidue):
    """Get the probabilities of the residueTypes
    """
    # ignore if no chemical shifts or a <new> nmrResidue - which chemicalShiftList?
    if self.project.chemicalShiftLists and len(self.project.chemicalShiftLists) > 0 and not isinstance(currentNmrResidue, _attribContainer):
        predictions = getNmrResiduePrediction(currentNmrResidue, self.project.chemicalShiftLists[0])
        preds1 = [' '.join([x[0].upper(), x[1]]) for x in predictions]  # if not currentNmrResidue.residueType]
        preds1 = list(OrderedSet(preds1))
        remainingResidues = list(CCP_CODES_SORTED)
        possibilities = [currentNmrResidue.residueType] + preds1 + remainingResidues
    else:
        possibilities = ('',) + CCP_CODES_SORTED
    self.residueType.modifyTexts(possibilities)


def _checkNmrResidue(self, value=None):
    """Check the new pulldown item and strip bad characters
    """
    # Check the correct characters for residueType - need to remove spaceNumberPercent
    value = re.sub(REMOVEPERCENT, '', value)
    if value not in self.residueType.pulldownList.texts:
        # add modified value if not in the pulldown
        self.residueType.pulldownList.addItem(value)
    self.residueType.pulldownList.set(value)


class NmrResidueEditPopup(AttributeEditorPopupABC):
    """
    NmrResidue attributes editor popup

    New checkBox
    Create New
    if checked
        if the nmrChain doesn't exist, create a new nmrChain
        If the sequenceCode doesn't exist, create a new nmrResidue
    else
        if merge checked
            merge into the existing nmrResidue, if found
        else
            rename the current nmrResidue sequenceCode and residueType
    """

    def _getNmrChainList(self, nmrChain):
        """Populate the nmrChain pulldown
        """
        self.nmrChain.modifyTexts([x.id for x in self.project.nmrChains])
        self.nmrChain.select(self.obj.nmrChain.id)

    klass = NmrResidue
    attributes = [('Pid', EntryCompoundWidget, getattr, None, None, None, {}),
                  ('NmrChain', PulldownListCompoundWidget, getattr, setattr, _getNmrChainList, None, {}),
                  ('Sequence Code', EntryCompoundWidget, getattr, setattr, None, None, {}),
                  # ('Create New', CheckBoxCompoundWidget, None, None, None, None, {'checked': False, 'checkable':True}),
                  ('Residue Type', PulldownListCompoundWidget, getattr, setattr, _getResidueTypeProb, _checkNmrResidue, {}),
                  ('Merge to Existing', CheckBoxCompoundWidget, None, None, None, None, {'checked': False, 'checkable':True}),
                  # ('Deassign', CheckBoxCompoundWidget, None, None, None, None, {'checked': False, 'checkable':True}),
                  ('Comment', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <'}),
                  ]

    # hWidth = 120

    # def __init__(self, *args, **kwds):
    #     super().__init__(*args, **kwds)
    #     self.deassign.checkBox.clicked.connect(self._deassignCallBack)
    #     self.mergetoExisting.checkBox.clicked.connect(self._mergetoExistingCallBack)

    def __postInit__(self):
        """post initialise functions - required as may need to insert more objects into dialog
        """
        # add a new button to deassign/disconnect nmrResidue
        self.setUserButton(callback=self._userCallback, tipText='Deassign the nmrResidue and return to the default nmrChain NC:@-', text='Deassign', enabled=True)

        super().__postInit__()

        self._userButton = self.dialogButtons.button(self.USERBUTTON)
        self._userButton.setEnabled(True)
        self._deassignClicked = False

    # def _deassignCallBack(self, *args):
    #     """Handle clicking the deassign checkBox
    #     - they are mutually exclusive
    #     """
    #     if self.deassign.isChecked():
    #         self.mergetoExisting.set(False)
    #
    # def _mergetoExistingCallBack(self, *args):
    #     """Handle clicking the mergetoExisting checkBox
    #     - they are mutually exclusive
    #     """
    #     if self.mergetoExisting.isChecked():
    #         self.deassign.set(False)

    def _userCallback(self, *args):
        """Handle deassign/disconnect selected nmrResidue
        """
        with self.handleUserClicked() as error:
            # # deassign/disconnect the nmrResidue - nmrChains are split, and nmrResidue is returned to the pool
            # _seqCode = self.sequenceCode.getText()
            # _resType = re.sub(REMOVEPERCENT, '', self.residueType.getText())
            # if _seqCode:
            #     showWarning(str(self.windowTitle()), 'To deassign the nmrResidue, please leave the sequenceCode blank.')
            #     error.errorValue = True
            # else:
            #     self.obj.disconnect()
            #     if _seqCode or _resType:
            #         # reset the sequenceCode/residueType
            #         self.obj.moveToNmrChain(sequenceCode=_seqCode, residueType=_resType)

            self.obj.disconnect()

        # self._deassignClicked = True
        # self._okClicked()
        # self._deassignClicked = False

    def _applyAllChanges(self, changes):
        """Apply all changes - move nmrResidue to new chain as required
        """
        # if self._deassignClicked:
        #     print('   beep')
        #     if self.sequenceCode.getText():
        #         raise RuntimeError('To deassign the nmrResidue, please leave the sequenceCode blank.')
        #     else:
        #         self.obj.disconnect()
        #         return

        merge = self.mergetoExisting.isChecked()
        create = False # self.createNew.isChecked()
        deassign = False # self.deassign.isChecked()

        if deassign:
            pass
            # if self.sequenceCode.getText():
            #     raise RuntimeError('To deassign the nmrResidue, please leave the sequenceCode blank.')
            # else:
            #     self.obj.disconnect()

        else:
            _chainId = self.nmrChain.getText()
            _chainPid = 'NC:{}'.format(self.nmrChain.getText())

            # create a new nmrChain as required
            _nmrChain = self.project.fetchNmrChain(_chainId)

            # find the existing nmrResidue
            destNmrResidue = _getNmrResidue(_nmrChain,
                                            self.sequenceCode.getText(),
                                            re.sub(REMOVEPERCENT, '', self.residueType.getText())) if _nmrChain else None

            if destNmrResidue and (self.obj != destNmrResidue):
                # move to an existing nmrResidue requires a merge
                if not merge:
                    # raise error to notify popup
                    raise ValueError('Cannot move NmrResidue to an existing NmrResidue without merging')

                destNmrResidue.mergeNmrResidues(self.obj)
                destNmrResidue.comment = self.comment.getText()
            else:
                if not create or (self.obj == destNmrResidue):
                    # assign to a new nmrResidue, includes changing just the residueType
                    self.obj.moveToNmrChain(_chainPid,
                                            self.sequenceCode.getText(),
                                            re.sub(REMOVEPERCENT, '', self.residueType.getText())
                                            )
                else:
                    # fetch a new residue, sequenceCode has changed
                    self.obj = _nmrChain.fetchNmrResidue(self.sequenceCode.getText(),
                                                         re.sub(REMOVEPERCENT, '', self.residueType.getText())
                                                         )
                self.obj.comment = self.comment.getText()

    def storeWidgetState(self):
        """Store the state of the checkBoxes between popups
        """
        merge = self.mergetoExisting.isChecked()
        # create = self.createNew.isChecked()
        # deassign = self.deassign.isChecked()

        NmrResidueEditPopup._storedState[MERGE] = merge
        # NmrResidueEditPopup._storedState[CREATE] = create
        # NmrResidueEditPopup._storedState[DEASSIGN] = deassign

    def restoreWidgetState(self):
        """Restore the state of the checkBoxes
        """
        self.mergetoExisting.set(NmrResidueEditPopup._storedState.get(MERGE, False))
        # self.createNew.set(NmrResidueEditPopup._storedState.get(CREATE, False))
        # self.deassign.set(NmrResidueEditPopup._storedState.get(DEASSIGN, False))

    def _setValue(self, attr, setFunction, value):
        """Not needed here - subclass so does no operation
        """
        pass


class NmrResidueNewPopup(AttributeEditorPopupABC):
    """
    NmrResidue attributes new popup
    """

    def _getNmrChainList(self, nmrChain):
        """Populate the nmrChain pulldown
        """
        self.nmrChain.modifyTexts([x.id for x in self.project.nmrChains])
        self.nmrChain.select(self._parentNmrChain.id)

    klass = NmrResidue
    attributes = [('NmrChain', PulldownListCompoundWidget, getattr, setattr, _getNmrChainList, None, {}),
                  ('Sequence Code', EntryCompoundWidget, getattr, setattr, None, None, {}),
                  ('Residue Type', PulldownListCompoundWidget, getattr, setattr, _getResidueTypeProb, _checkNmrResidue, {}),
                  ('Comment', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <'}),
                  ]

    def __init__(self, parent=None, mainWindow=None, obj=None, **kwds):
        self._parentNmrChain = obj
        super().__init__(parent=parent, mainWindow=mainWindow, obj=obj, **kwds)

    def _applyAllChanges(self, changes):
        """Apply all changes - move nmrResidue to new chain as required
        """
        _chainId = self.nmrChain.getText()
        _chainPid = 'NC:{}'.format(self.nmrChain.getText())

        # create a new nmrChain as required
        _nmrChain = self.project.fetchNmrChain(_chainId)

        # find the existing nmrResidue
        destNmrResidue = _getNmrResidue(_nmrChain,
                                        self.sequenceCode.getText(),
                                        re.sub(REMOVEPERCENT, '', self.residueType.getText())) if _nmrChain else None

        if not destNmrResidue:
            self.obj = _nmrChain.fetchNmrResidue(self.sequenceCode.getText(),
                                                 re.sub(REMOVEPERCENT, '', self.residueType.getText())
                                                 )
            self.obj.comment = self.comment.getText()

    def storeWidgetState(self):
        """Store the state of the checkBoxes between popups
        """
        pass

    def restoreWidgetState(self):
        """Restore the state of the checkBoxes
        """
        pass

    def _setValue(self, attr, setFunction, value):
        """Not needed here - subclass so does no operation
        """
        pass

    def _populateInitialValues(self):
        pass
