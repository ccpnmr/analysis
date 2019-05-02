"""
Module Documentation here
"""
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
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank$"
__date__ = "$Date: 9/05/2017 $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget
from ccpn.ui.gui.popups.Dialog import CcpnDialog, dialogErrorReport
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier
from ccpn.core.lib.ContextManagers import undoBlock, undoStackBlocking


class DeleteItemsPopup(CcpnDialog):
    """
    Open a small popup to allow deletion of selected 'current' items
    Items is a tuple of tuples: indexed by the name of the items, containing a list of the items for deletion
    i.e. (('Peaks', peakList), ('Multiplets',multipletList))
    """

    def __init__(self, parent=None, mainWindow=None, title='Delete Items', items=None, **kwds):
        """
        Initialise the widget
        """
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current

        row = 0
        self.noteLabel = Label(self, "Delete selected items: ", grid=(row, 0))

        self.deleteList = []
        for item in items:
            itemName, values = item

            row += 1
            # add a check box for each item
            newCheckBox = CheckBoxCompoundWidget(self,
                                                 grid=(row, 0), vAlign='top', stretch=(0, 0), hAlign='left',
                                                 orientation='right',
                                                 labelText=itemName,
                                                 checked=True if itemName in ['peaks', 'Peaks'] else False
                                                 )
            self.deleteList.append((itemName, values, newCheckBox))

        row += 1
        # add close buttons at the bottom
        self.buttonList = ButtonList(self, ['Cancel', 'OK'], [self.reject, self._okButton], grid=(row, 1))
        self.buttonList.buttons[1].setFocus()

        self.GLSignals = GLNotifier(parent=self)

    def _refreshGLItems(self):
        # emit a signal to rebuild all peaks and multiplets
        self.GLSignals.emitEvent(triggers=[GLNotifier.GLALLPEAKS, GLNotifier.GLALLINTEGRALS, GLNotifier.GLALLMULTIPLETS])

    def _okButton(self):
        """
        When ok button pressed: delete and exit
        """
        undo = self.project._undo

        try:
            with undoBlock():

                # add item here to redraw items
                with undoStackBlocking() as addUndoItem:
                    addUndoItem(undo=self._refreshGLItems)

                for delItem in self.deleteList:
                    if delItem[2].isChecked():
                        self.project.deleteObjects(*delItem[1])

                # add item here to redraw items
                with undoStackBlocking() as addUndoItem:
                    addUndoItem(redo=self._refreshGLItems)

                # redraw the items
                self._refreshGLItems()

        except Exception as es:
            dialogErrorReport(self, undo, es)

        self.accept()
