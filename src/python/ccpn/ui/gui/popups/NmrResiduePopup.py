#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:48 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
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
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.CompoundWidgets import EntryCompoundWidget, PulldownListCompoundWidget
from ccpn.ui.gui.widgets.PulldownListsForObjects import NmrChainPulldown
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.util.OrderedSet import OrderedSet


REMOVEPERCENT = '( ?\d+.?\d* ?%)+'


class NmrResiduePopup(CcpnDialog):

    def __init__(self, parent=None, mainWindow=None, nmrResidue=None, **kwds):
        """
        Initialise the widget
        """
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle='Edit NmrResidue', **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current

        self._parent = parent
        self.nmrResidue = nmrResidue  # Also set in updatePopup
        # self.nmrAtom = nmrAtom

        row = 0
        hspan = 2
        hWidth = 140

        self.pid = EntryCompoundWidget(self, labelText="pid",
                                             fixedWidths=(hWidth, hWidth), grid=(row, 0), gridSpan=(1, hspan),
                                             readOnly = True
                                       )
        row += 1

        row += 1
        self.chainPulldown = NmrChainPulldown(self, project=self.project, labelText='nmrChain',
                                              fixedWidths=(hWidth, hWidth),
                                              grid=(row, 0), gridSpan=(1, hspan))
        row += 1
        self.sequenceCode = EntryCompoundWidget(self, labelText="sequenceCode",
                                                fixedWidths=(hWidth, hWidth), grid=(row, 0), gridSpan=(1, hspan))

        row += 1
        self.residueType = PulldownListCompoundWidget(self, labelText="residueType", editable=True,
                                                      fixedWidths=(hWidth, hWidth), grid=(row, 0), gridSpan=(1, hspan),
                                                      callback=self._checkNmrResidue)
        row += 1
        self.comment = EntryCompoundWidget(self, labelText="comment",
                                           fixedWidths=(hWidth, hWidth), grid=(row, 0), gridSpan=(1, hspan))
        row += 1
        self.addSpacer(0, 10, grid=(row, 0))

        row += 1
        self.buttons = ButtonList(self, texts=('Close', 'Apply', 'Ok'),
                                  callbacks=(self.reject, self._applyChanges, self._okButton),
                                  grid=(row, 0), gridSpan=(1, hspan))

        self._updatePopup(nmrResidue)

    def _updatePopup(self, nmrResidue):
        if nmrResidue is not None:
            self.nmrResidue = nmrResidue
            self.pid.setText(self.nmrResidue.pid)
            chain = nmrResidue.nmrChain
            self.chainPulldown.select(chain.pid)
            self.sequenceCode.setText(nmrResidue.sequenceCode)
            self._getResidueTypeProb(nmrResidue)
            self.residueType.select(nmrResidue.residueType)
            self.comment.setText(nmrResidue.comment)

    def _getResidueTypeProb(self, currentNmrResidue):

        if self.project.chemicalShiftLists and len(self.project.chemicalShiftLists) > 0:
            predictions = getNmrResiduePrediction(currentNmrResidue, self.project.chemicalShiftLists[0])
            preds1 = [' '.join([x[0].upper(), x[1]]) for x in predictions]  # if not currentNmrResidue.residueType]
            preds1 = list(OrderedSet(preds1))
            predictedTypes = [x[0].upper() for x in predictions]
            # remainingResidues = [x for x in CCP_CODES_SORTED if x not in predictedTypes and not currentNmrResidue.residueType]
            remainingResidues = list(CCP_CODES_SORTED)
            possibilities = [currentNmrResidue.residueType] + preds1 + remainingResidues
        else:
            possibilities = ('',) + CCP_CODES_SORTED
        self.residueType.modifyTexts(possibilities)

    def _checkNmrResidue(self, value):
        """Check the new pulldown item and strip bad characters
        """
        # Check the correct characters for residueType - need to remove spaceNumberPercent
        # print('>>>check value')
        value = re.sub(REMOVEPERCENT, '', value)
        if value not in self.residueType.pulldownList.texts:
            # add modified value if not in the pulldown
            self.residueType.pulldownList.addItem(value)
        self.residueType.pulldownList.set(value)

    def _applyChanges(self):
        """
        The apply button has been clicked
        If there is an error setting the values then popup an error message
        repopulate the settings
        """
        error = False
        try:
            self.nmrResidue.moveToNmrChain(
                    self.chainPulldown.getText(),
                    self.sequenceCode.getText(),
                    re.sub(REMOVEPERCENT, '', self.residueType.getText())
            )

        except Exception as es:
            showWarning(str(self.windowTitle()), str(es))
            if self.application._isInDebugMode:
                raise es

            error = True

        finally:
            self._updatePopup(self.nmrResidue)  # Repopulate
            return error

    def _okButton(self):
        error = self._applyChanges()
        if not error: self.accept()
