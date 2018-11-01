#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:48 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets

from ccpn.core.Chain import Chain
from ccpn.core.lib.AssignmentLib import CCP_CODES, getNmrResiduePrediction
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.FilteringPulldownList import FilteringPulldownList
from ccpn.ui.gui.widgets.CompoundWidgets import EntryCompoundWidget, PulldownListCompoundWidget
from ccpn.ui.gui.widgets.PulldownListsForObjects import NmrChainPulldown

from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.util.Logging import getLogger

import sys


class NmrResiduePopup(CcpnDialog):
    def __init__(self, parent=None, mainWindow=None, nmrResidue=None, nmrAtom=None, title='NmrResidue', **kw):
        """
        Initialise the widget
        """
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kw)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current

        self.parent = parent
        self.nmrAtom = nmrAtom

        row = 0
        hspan = 3
        hWidth = 100

        row += 1
        self.chainPulldown = NmrChainPulldown(self, project=self.project,
                                              minimumWidths=(hWidth, hWidth), maximumWidths=(hWidth, hWidth),
                                              grid=(row, 0), gridSpan=(1, hspan))
        row += 1
        self.sequenceCode = EntryCompoundWidget(self, labelText="Sequence Code", grid=(row, 0), gridSpan=(1, hspan))

        row += 1
        self.residueType = PulldownListCompoundWidget(self, labelText="Residue Type", editable=True,
                                                      minimumWidths=(hWidth, hWidth), maximumWidths=(hWidth, hWidth),
                                                      grid=(row, 0), gridSpan=(1, hspan))
        row += 1
        self.comment = EntryCompoundWidget(self, labelText="Comment",
                                           minimumWidths=(hWidth, hWidth), maximumWidths=(hWidth, hWidth),
                                           grid=(row, 0), gridSpan=(1, hspan))
        row += 1
        self.buttons = ButtonList(self, texts=('Close', 'Apply', 'Ok'),
                                  callbacks=(self.reject, self._applyChanges, self._okButton),
                                  grid=(row, 0), gridSpan=(1, hspan))

        self._updatePopup(nmrResidue)

    def _updatePopup(self, nmrResidue):
        if nmrResidue is not None:
            self.setWindowTitle(nmrResidue.pid)
            self.nmrResidue = nmrResidue

            chain = nmrResidue.nmrChain
            self.chainPulldown.select(chain.pid)
            self.sequenceCode.setText(nmrResidue.sequenceCode)
            self._getResidueTypeProb(nmrResidue)
            self.residueType.select(nmrResidue.residueType)
            self.comment.setText(nmrResidue.comment)

    def _getResidueTypeProb(self, currentNmrResidue):

        if self.project.chemicalShiftLists and len(self.project.chemicalShiftLists) > 0:
            predictions = getNmrResiduePrediction(currentNmrResidue, self.project.chemicalShiftLists[0])
            preds1 = [' '.join([x[0], x[1]]) for x in predictions if not currentNmrResidue.residueType]
            predictedTypes = [x[0] for x in predictions]
            remainingResidues = [x for x in CCP_CODES if x not in predictedTypes and not currentNmrResidue.residueType]
            possibilities = [currentNmrResidue.residueType] + preds1 + remainingResidues
        else:
            possibilities = ('',) + CCP_CODES,
        self.residueType.modifyTextList(possibilities)

    def _applyChanges(self):
        """
        The apply button has been clicked
        Define an undo block for setting the properties of the object
        If there is an error setting any values then generate an error message
          If anything has been added to the undo queue then remove it with application.undo()
          repopulate the popup widgets
        """
        self.project._startCommandEchoBlock('_applyChanges', quiet=True)
        try:
            nmrChain = self.nmrResidue.nmrChain
            newNmrchain = self.project.getByPid(self.chainPulldown.getText())
            if newNmrchain != nmrChain:
                self.nmrResidue.moveToNmrChain(newNmrchain)

            sequenceCode = self.sequenceCode.getText()
            residueType = self.residueType.getText()
            if self.nmrResidue.sequenceCode != sequenceCode or self.nmrResidue.residueType != residueType:
                newSeqCode = '.'.join((sequenceCode, residueType))
                self.nmrResidue.rename(newSeqCode)

        except Exception as es:
            showWarning(str(self.windowTitle()), str(es))
            self.application.undo()

        finally:
            self.project._endCommandEchoBlock()
            self._updatePopup(self.nmrResidue)  # Repopulate

    def _okButton(self):
        self._applyChanges()
        self.accept()
