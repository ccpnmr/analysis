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
__dateModified__ = "$dateModified: 2020-09-29 09:47:39 +0100 (Tue, September 29, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import re
from ccpn.core.lib.AssignmentLib import CCP_CODES_SORTED, getNmrResiduePrediction
from ccpn.ui.gui.widgets.CompoundWidgets import EntryCompoundWidget, PulldownListCompoundWidget, CheckBoxCompoundWidget
from ccpn.ui.gui.popups.AttributeEditorPopupABC import AttributeEditorPopupABC
from ccpn.util.OrderedSet import OrderedSet
from ccpn.core.NmrResidue import NmrResidue, _getNmrResidue


REMOVEPERCENT = '( ?\d+.?\d* ?%)+'
MERGE = '_merge'
CREATE = '_create'


class NmrResiduePopup(AttributeEditorPopupABC):
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

    def _getResidueTypeProb(self, currentNmrResidue):
        """Get the probabilities of the residueTypes
        """
        if self.project.chemicalShiftLists and len(self.project.chemicalShiftLists) > 0:
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

    def _getNmrChainList(self, nmrChain):
        """Populate the nmrChain pulldown
        """
        self.nmrChain.modifyTexts([x.id for x in self.obj.project.nmrChains])
        self.nmrChain.select(self.obj.nmrChain.id)

    klass = NmrResidue
    attributes = [('pid', EntryCompoundWidget, getattr, None, None, None, {}),
                  ('nmrChain', PulldownListCompoundWidget, getattr, setattr, _getNmrChainList, None, {}),
                  ('sequenceCode', EntryCompoundWidget, getattr, setattr, None, None, {}),
                  ('Create New', CheckBoxCompoundWidget, None, None, None, None, {'checked': False}),
                  ('residueType', PulldownListCompoundWidget, getattr, setattr, _getResidueTypeProb, _checkNmrResidue, {}),
                  ('Merge to Existing', CheckBoxCompoundWidget, None, None, None, None, {'checked': False}),
                  ('comment', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <'}),
                  ]

    # hWidth = 120

    def __init__(self, *args, **kwds):
        """Initialise the popup
        """
        super(NmrResiduePopup, self).__init__(*args, **kwds)

        # restore the state of the checkBoxes
        self.MergetoExisting.set(getattr(NmrResiduePopup, MERGE, False))
        self.CreateNew.set(getattr(NmrResiduePopup, CREATE, False))

    def _cancelClicked(self):
        """Close the popup on pressing cancel
        """
        super(NmrResiduePopup, self)._cancelClicked()
        self._setState()

    def _applyAllChanges(self, changes):
        """Apply all changes - move nmrResidue to new chain as required
        """
        merge = self.MergetoExisting.isChecked()
        create = self.CreateNew.isChecked()

        _chainId = self.nmrChain.getText()
        _chainPid = 'NC:{}'.format(self.nmrChain.getText())
        if create:
            # create a new nmrChain as required
            _nmrChain = self.project.fetchNmrChain(_chainId)
        else:
            # find the existing nmrChain
            _nmrChain = self.project.getByPid(_chainPid)

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

        self._setState()

    def _setState(self):
        """Store the state of the checkBoxes between popups
        """
        merge = self.MergetoExisting.isChecked()
        create = self.CreateNew.isChecked()

        setattr(NmrResiduePopup, MERGE, merge)
        setattr(NmrResiduePopup, CREATE, create)

    def _setValue(self, attr, setFunction, value):
        """Not needed here - subclass so does no operation
        """
        pass
