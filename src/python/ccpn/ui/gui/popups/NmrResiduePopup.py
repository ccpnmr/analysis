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
__dateModified__ = "$dateModified: 2020-05-27 16:10:33 +0100 (Wed, May 27, 2020) $"
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
from ccpn.ui.gui.widgets.CompoundWidgets import EntryCompoundWidget, PulldownListCompoundWidget
from ccpn.ui.gui.widgets.PulldownListsForObjects import NmrChainPulldown
from ccpn.ui.gui.popups.AttributeEditorPopupABC import AttributeEditorPopupABC
from ccpn.util.OrderedSet import OrderedSet
from ccpn.core.NmrResidue import NmrResidue


REMOVEPERCENT = '( ?\d+.?\d* ?%)+'


class NmrResiduePopup(AttributeEditorPopupABC):
    """
    NmrResidue attributes editor popup
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
        self.nmrChain.modifyTexts([x.pid for x in self.obj.project.nmrChains])
        self.nmrChain.select(self.obj.nmrChain.pid)

    klass = NmrResidue
    attributes = [('pid', EntryCompoundWidget, getattr, None, None, None, {}),
                  ('nmrChain', PulldownListCompoundWidget, getattr, setattr, _getNmrChainList, None, {}),
                  ('sequenceCode', EntryCompoundWidget, getattr, setattr, None, None, {}),
                  ('residueType', PulldownListCompoundWidget, getattr, setattr, _getResidueTypeProb, _checkNmrResidue, {}),
                  ('comment', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <'}),
                  ]

    def _applyAllChanges(self, changes):
        """Apply all changes - move nmrResidue to new chain
        """
        self.obj.moveToNmrChain(self.nmrChain.getText(),
                                self.sequenceCode.getText(),
                                re.sub(REMOVEPERCENT, '', self.residueType.getText())
                                )

    def _setValue(self, attr, setFunction, value):
        """Not needed here - subclass so does no operation
        """
        pass
